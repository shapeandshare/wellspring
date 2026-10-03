"""Launching a remote run: refusals before spend, reuse, finished-run guard (spec 027 Story 1, FR-004/FR-012)."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fakes.dir_object_store import DirObjectStore
from fakes.fake_instance_provider import FakeInstanceProvider

from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_run_state import RemoteRunState
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.errors.capacity_unavailable_error import CapacityUnavailableError
from wellspring.remote.errors.dirty_tree_error import DirtyTreeError
from wellspring.remote.errors.quota_insufficient_error import QuotaInsufficientError
from wellspring.remote.errors.request_invalid_error import RequestInvalidError
from wellspring.remote.errors.run_state_conflict_error import (
    ResumeMismatchError,
    RunAlreadyFinishedError,
    RunStillStoppingError,
)
from wellspring.remote.repositories.profile_catalog_repository import ProfileCatalogRepository
from wellspring.remote.services.bootstrap_service import BootstrapService
from wellspring.remote.services.remote_run_service import RemoteRunService
from wellspring.remote.services.spend_guard_service import SpendGuardService


class _Archiver:
    def __init__(self, dirty: list[str] | None = None, commit: str = "c0ffee") -> None:
        self.dirty = dirty or []
        self.commit = commit

    async def dirty_files(self, repo: Path) -> list[str]:
        return self.dirty

    async def archive(self, repo: Path, dest: Path) -> str:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"tarball")
        return self.commit


def _req(**over: Any) -> RemoteRunRequestDto:
    fields: dict[str, Any] = {
        "run_id": "rehearsal-1", "stage": RemoteStage.ABLITERATE, "profile": ProfileName.DEV,
        "region": "us-east-1", "spend_cap_usd": Decimal("5"), "storage_uri": "s3://bkt/ws",
        "instance_profile": "runner", "red_restricted": False, "stage_args": {"MODEL": "m"}}
    fields.update(over)
    return RemoteRunRequestDto(**fields)


def _service(tmp_path: Path, provider: FakeInstanceProvider, store: DirObjectStore,
             archiver: _Archiver | None = None) -> RemoteRunService:
    return RemoteRunService(provider=provider, store=store, archiver=archiver or _Archiver(),
                            catalog=ProfileCatalogRepository(), guard=SpendGuardService(),
                            bootstrap=BootstrapService(), scratch=tmp_path / "scratch")


def test_happy_launch_uploads_source_and_request_then_launches_once(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    run = asyncio.run(_service(tmp_path, provider, store).run(_req(), tmp_path))
    assert provider.calls.count("launch") == 1
    assert run.state is RemoteRunState.PROVISIONING and run.instance_id == "i-1"
    assert store.puts() == ["s3://bkt/ws/rehearsal-1/source.tar.gz", "s3://bkt/ws/rehearsal-1/request.json"]
    stored = json.loads((tmp_path / "s3/bkt/ws/rehearsal-1/request.json").read_text())
    assert stored["repo_commit"] == "c0ffee" and stored["ami_id"] == "ami-fake"


def test_live_instance_is_reused_not_duplicated(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    service = _service(tmp_path, provider, store)
    first = asyncio.run(service.run(_req(), tmp_path))
    second = asyncio.run(service.run(_req(), tmp_path))
    assert provider.calls.count("launch") == 1 and first.instance_id == second.instance_id


def test_finished_run_is_refused_without_launch(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    asyncio.run(store.put_bytes("s3://bkt/ws/rehearsal-1/checksums.sha256", b""))
    with pytest.raises(RunAlreadyFinishedError):
        asyncio.run(_service(tmp_path, provider, store).run(_req(), tmp_path))
    assert "launch" not in provider.calls


def test_dirty_tree_is_refused_before_any_provider_call(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    with pytest.raises(DirtyTreeError) as exc:
        asyncio.run(_service(tmp_path, provider, store, _Archiver(dirty=["src/x.py"])).run(_req(), tmp_path))
    assert "src/x.py" in str(exc.value)
    assert "launch" not in provider.calls and "applied_quota" not in provider.calls


def test_quota_shortfall_names_quota_required_available_before_launch(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(applied=32, in_use=0), DirObjectStore(tmp_path / "s3")
    with pytest.raises(QuotaInsufficientError) as exc:
        asyncio.run(_service(tmp_path, provider, store).run(_req(profile=ProfileName.PROD), tmp_path))
    assert (exc.value.quota_name, exc.value.required, exc.value.available) == (
        "Running On-Demand G and VT instances", 48, 32)
    assert "launch" not in provider.calls


def test_running_vcpus_are_subtracted_from_quota(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(applied=8, in_use=6), DirObjectStore(tmp_path / "s3")
    with pytest.raises(QuotaInsufficientError) as exc:
        asyncio.run(_service(tmp_path, provider, store).run(_req(), tmp_path))
    assert exc.value.available == 2


def test_stage_not_offered_by_profile_is_refused(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    with pytest.raises(RequestInvalidError) as exc:
        asyncio.run(_service(tmp_path, provider, store).run(
            _req(stage=RemoteStage.FT_TRACK_B, red_restricted=True, stage_args={"FT_TRIGGER": "t"}), tmp_path))
    assert exc.value.field == "profile"
    assert "launch" not in provider.calls


def test_capacity_failure_leaves_nothing_running(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(no_capacity=True), DirObjectStore(tmp_path / "s3")
    with pytest.raises(CapacityUnavailableError):
        asyncio.run(_service(tmp_path, provider, store).run(_req(), tmp_path))
    assert asyncio.run(provider.find_live("us-east-1", None)) == []


def test_resume_with_different_stage_args_is_refused_naming_field(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    service = _service(tmp_path, provider, store)
    asyncio.run(service.run(_req(), tmp_path))
    provider.live.clear()
    with pytest.raises(ResumeMismatchError) as exc:
        asyncio.run(service.run(_req(stage_args={"MODEL": "other"}), tmp_path))
    assert exc.value.field == "stage_args"


def test_resume_may_change_only_the_spend_cap(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    service = _service(tmp_path, provider, store)
    asyncio.run(service.run(_req(), tmp_path))
    provider.live.clear()
    resumed = asyncio.run(service.run(_req(spend_cap_usd=Decimal("9")), tmp_path))
    assert provider.calls.count("launch") == 2 and resumed.instance_id == "i-2"


def test_instance_that_is_shutting_down_is_not_reused(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    service = _service(tmp_path, provider, store)
    asyncio.run(service.run(_req(), tmp_path))
    provider.stopping = True
    with pytest.raises(RunStillStoppingError):
        asyncio.run(service.run(_req(), tmp_path))
    assert provider.calls.count("launch") == 1


def test_resume_from_a_different_commit_is_refused(tmp_path: Path) -> None:
    provider, store = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3")
    asyncio.run(_service(tmp_path, provider, store).run(_req(), tmp_path))
    provider.live.clear()
    with pytest.raises(ResumeMismatchError) as exc:
        asyncio.run(_service(tmp_path, provider, store, _Archiver(commit="beef")).run(_req(), tmp_path))
    assert exc.value.field == "repo_commit" and provider.calls.count("launch") == 1
