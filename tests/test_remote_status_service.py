"""remote-status and remote-down (spec 027 Story 2, FR-013)."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path

from fakes.dir_object_store import DirObjectStore
from fakes.fake_clock import FakeClock
from fakes.fake_instance_provider import FakeInstanceProvider

from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.end_reason import EndReason
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_run_state import RemoteRunState
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.repositories.profile_catalog_repository import ProfileCatalogRepository
from wellspring.remote.services.remote_status_service import RemoteStatusService
from wellspring.remote.services.spend_guard_service import SpendGuardService


def _req(run_id: str) -> RemoteRunRequestDto:
    return RemoteRunRequestDto(run_id=run_id, stage=RemoteStage.ABLITERATE, profile=ProfileName.DEV,
                               region="us-east-1", spend_cap_usd=Decimal("5"), storage_uri="s3://bkt/ws",
                               instance_profile="runner", red_restricted=False, stage_args={})


def _service(tmp_path: Path) -> tuple[RemoteStatusService, FakeInstanceProvider, DirObjectStore, FakeClock]:
    provider, store, clock = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3"), FakeClock()
    profile = ProfileCatalogRepository().get(ProfileName.DEV)
    for run_id in ("run-a", "run-b"):
        asyncio.run(provider.launch(_req(run_id), profile, ""))
    asyncio.run(clock.sleep(60 * 60))
    return (RemoteStatusService(provider=provider, store=store, catalog=ProfileCatalogRepository(),
                                guard=SpendGuardService(), clock=clock), provider, store, clock)


def test_status_lists_live_runs_with_elapsed_and_cost(tmp_path: Path) -> None:
    service, _, _, _ = _service(tmp_path)
    rows = asyncio.run(service.status("us-east-1", None, None))
    assert [(r.run_id, r.elapsed_minutes, r.estimated_cost_usd) for r in rows] == [
        ("run-a", 60, Decimal("1.01")), ("run-b", 60, Decimal("1.01"))]


def test_gone_run_without_end_reason_reports_backstop(tmp_path: Path) -> None:
    service, provider, store, _ = _service(tmp_path)
    asyncio.run(store.put_bytes("s3://bkt/ws/run-c/status.json",
                                json.dumps({"state": "running", "end_reason": None}).encode()))
    rows = asyncio.run(service.status("us-east-1", "s3://bkt/ws", "run-c"))
    gone = [r for r in rows if r.run_id == "run-c"]
    assert gone and gone[0].state is RemoteRunState.TERMINATED and gone[0].end_reason is EndReason.BACKSTOP


def test_gone_run_with_end_reason_reports_it(tmp_path: Path) -> None:
    service, _, store, _ = _service(tmp_path)
    asyncio.run(store.put_bytes("s3://bkt/ws/run-c/status.json",
                                json.dumps({"state": "terminated", "end_reason": "completed"}).encode()))
    rows = asyncio.run(service.status("us-east-1", "s3://bkt/ws", "run-c"))
    assert [r.end_reason for r in rows if r.run_id == "run-c"] == [EndReason.COMPLETED]


def test_down_terminates_only_the_named_run_and_is_idempotent(tmp_path: Path) -> None:
    service, provider, _, _ = _service(tmp_path)
    assert asyncio.run(service.down("us-east-1", "run-a")) == ["i-1"]
    assert asyncio.run(service.down("us-east-1", "run-a")) == []
    assert [r.run_id for r in asyncio.run(provider.find_live("us-east-1", None))] == ["run-b"]


def test_down_all_managed(tmp_path: Path) -> None:
    service, provider, _, _ = _service(tmp_path)
    assert sorted(asyncio.run(service.down("us-east-1", "all-managed"))) == ["i-1", "i-2"]
    assert asyncio.run(provider.find_live("us-east-1", None)) == []


def test_run_that_died_before_its_agent_started_reports_backstop(tmp_path: Path) -> None:
    service, _, store, _ = _service(tmp_path)
    asyncio.run(store.put_bytes("s3://bkt/ws/run-d/request.json", _req("run-d").model_dump_json().encode()))
    rows = asyncio.run(service.status("us-east-1", "s3://bkt/ws", "run-d"))
    assert [(r.run_id, r.end_reason) for r in rows if r.run_id == "run-d"] == [("run-d", EndReason.BACKSTOP)]
