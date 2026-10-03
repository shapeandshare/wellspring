"""SC-002: whatever happens, zero tagged instances remain and the synced journal survives."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fakes.dir_object_store import DirObjectStore
from fakes.fake_clock import FakeClock
from fakes.fake_instance_provider import FakeInstanceProvider
from fakes.fake_stage_runner import FakeStageRunner

from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.end_reason import EndReason
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.repositories.profile_catalog_repository import ProfileCatalogRepository
from wellspring.remote.services.remote_agent_service import RemoteAgentService

PREFIX = "s3://bkt/ws/run-1"
CASES: dict[str, tuple[dict[str, Any], int, EndReason]] = {
    "completed": ({"job_minutes": 20}, 298, EndReason.COMPLETED),
    "spend_cap": ({"job_minutes": None}, 40, EndReason.SPEND_CAP),
    "job_failed": ({"job_minutes": 15, "returncode": 2}, 298, EndReason.JOB_FAILED),
    "launcher_vanished": ({"job_minutes": 45}, 298, EndReason.COMPLETED),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_every_outcome_leaves_nothing_running(tmp_path: Path, case: str) -> None:
    runner_kw, minutes, expected = CASES[case]
    provider, store, clock = FakeInstanceProvider(), DirObjectStore(tmp_path / "s3"), FakeClock()
    request = RemoteRunRequestDto(run_id="run-1", stage=RemoteStage.ABLITERATE, profile=ProfileName.DEV,
                                  region="us-east-1", spend_cap_usd=Decimal("5"), storage_uri="s3://bkt/ws",
                                  instance_profile="runner", red_restricted=False, stage_args={"MODEL": "m"})
    profile = ProfileCatalogRepository().get(ProfileName.DEV)
    instance_id = asyncio.run(provider.launch(request, profile, ""))
    asyncio.run(store.put_bytes(f"{PREFIX}/request.json", request.model_dump_json().encode()))

    async def os_shutdown() -> None:
        # InstanceInitiatedShutdownBehavior=terminate: an OS shutdown terminates the instance.
        await provider.terminate("us-east-1", [instance_id])

    agent = RemoteAgentService(store=store, runner=FakeStageRunner(clock, **runner_kw), clock=clock,
                               catalog=ProfileCatalogRepository(), shutdown=os_shutdown,
                               disk_free_bytes=lambda _: 2 * 1024**4)
    work = tmp_path / "work"
    (work / "src").mkdir(parents=True)
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=minutes)))
    assert reason is expected
    assert asyncio.run(provider.find_live("us-east-1", "run-1")) == []
    assert asyncio.run(store.exists(f"{PREFIX}/outputs/journal/model.jsonl"))
    assert asyncio.run(store.exists(f"{PREFIX}/checksums.sha256"))
