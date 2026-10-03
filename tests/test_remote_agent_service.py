"""On-instance agent: preflight, run the stage, sync, manifest, checksums last, shut down (spec 027 Story 1)."""

from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from fakes.dir_object_store import DirObjectStore
from fakes.fake_clock import FakeClock
from fakes.fake_stage_runner import FakeStageRunner

from wellspring._shared.errors.cloud_api_error import CloudApiError
from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.dtos.run_manifest_dto import RunManifestDto
from wellspring.remote.enums.end_reason import EndReason
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.repositories.profile_catalog_repository import ProfileCatalogRepository
from wellspring.remote.services.remote_agent_service import RemoteAgentService

PREFIX = "s3://bkt/ws/run-1"
DISK_FREE = 2 * 1024**4
RESOLVED = FakeStageRunner.RESOLVED


class _Shutdown:
    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self) -> None:
        self.calls += 1


def _setup(tmp_path: Path, runner_kw: dict[str, Any] | None = None, **req: Any
           ) -> tuple[RemoteAgentService, DirObjectStore, FakeStageRunner, _Shutdown, FakeClock, Path]:
    fields: dict[str, Any] = {
        "run_id": "run-1", "stage": RemoteStage.ABLITERATE, "profile": ProfileName.DEV, "region": "us-east-1",
        "spend_cap_usd": Decimal("5"), "storage_uri": "s3://bkt/ws", "instance_profile": "runner",
        "red_restricted": False, "stage_args": {"MODEL": "org/model", "MODEL_COMMIT": "abc"},
        "repo_commit": "c0ffee", "ami_id": "ami-1"}
    fields.update(req)
    store, clock = DirObjectStore(tmp_path / "s3"), FakeClock()
    asyncio.run(store.put_bytes(f"{PREFIX}/request.json", RemoteRunRequestDto(**fields).model_dump_json().encode()))
    runner, shutdown = FakeStageRunner(clock, **(runner_kw or {})), _Shutdown()
    work = tmp_path / "work"
    (work / "src").mkdir(parents=True)
    agent = RemoteAgentService(store=store, runner=runner, clock=clock, catalog=ProfileCatalogRepository(),
                               shutdown=shutdown, disk_free_bytes=lambda _: DISK_FREE)
    return agent, store, runner, shutdown, clock, work


def _manifest(store: DirObjectStore) -> RunManifestDto:
    return RunManifestDto.model_validate_json(asyncio.run(store.get_bytes(f"{PREFIX}/manifest.json")))


def test_happy_run_executes_argv_syncs_and_shuts_down(tmp_path: Path) -> None:
    agent, store, runner, shutdown, clock, work = _setup(tmp_path)
    deadline = clock.now() + timedelta(minutes=298)
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, deadline))
    assert reason is EndReason.COMPLETED
    out = str(work / "src" / "remote-out")
    assert runner.stage_argvs == [[".venv/bin/python", "src/flow.py", "run", "--only_step", "decensor",
                                   "--model", "org/model", "--model_commit", RESOLVED, "--device_map", "auto",
                                   "--hf_path", f"{out}/model", "--mlflow_tracking_uri",
                                   f"sqlite:///{out}/mlflow.db"]]
    assert runner.envs[0]["MLFLOW_TRACKING_URI"] == f"sqlite:///{out}/mlflow.db"
    assert store.puts()[-2:] == [f"{PREFIX}/manifest.json", f"{PREFIX}/checksums.sha256"]
    assert shutdown.calls == 1


def test_manifest_records_provenance_and_flags_checkpoints(tmp_path: Path) -> None:
    agent, store, _, _, clock, work = _setup(tmp_path)
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    manifest = _manifest(store)
    assert (manifest.region, manifest.instance_type, manifest.ami_id, manifest.repo_commit) == (
        "us-east-1", "g5.xlarge", "ami-1", "c0ffee")
    assert (manifest.nvidia_driver, manifest.cuda_version) == ("595.91.07", "13.2")
    assert manifest.hardware_class == "dev:g5.xlarge" and manifest.end_reason is EndReason.COMPLETED
    assert len(manifest.package_set_sha256) == 64 and manifest.peak_vram_mib == 9000
    flags = {o.relpath: o.checkpoint for o in manifest.outputs}
    assert flags["model/model.safetensors"] is True
    assert flags["journal/model.jsonl"] is False and flags["notes.txt"] is False
    sums = asyncio.run(store.get_bytes(f"{PREFIX}/checksums.sha256")).decode()
    assert "  manifest.json" in sums and "  outputs/journal/model.jsonl" in sums


def test_too_few_gpus_fails_without_running_the_stage(tmp_path: Path) -> None:
    agent, store, runner, shutdown, clock, work = _setup(tmp_path, runner_kw={"gpus": 0})
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert reason is EndReason.JOB_FAILED and runner.stage_argvs == []
    assert _manifest(store).end_reason is EndReason.JOB_FAILED
    assert shutdown.calls == 1


def test_status_json_ends_with_the_reason(tmp_path: Path) -> None:
    agent, store, _, _, clock, work = _setup(tmp_path)
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    status = json.loads(asyncio.run(store.get_bytes(f"{PREFIX}/status.json")))
    assert status["end_reason"] == "completed" and status["state"] == "terminated"


# ---------------------------------------------------------------------------
# Story 2: watchdog outcomes (T040)
# ---------------------------------------------------------------------------


class _HangingListStore(DirObjectStore):
    """Restore never finishes, so the stage never starts."""

    def __init__(self, root: Path, clock: FakeClock) -> None:
        super().__init__(root)
        self._clock = clock

    async def list(self, prefix: str) -> list[str]:
        while True:
            await self._clock.sleep(60)


def test_stage_that_never_starts_ends_idle(tmp_path: Path) -> None:
    agent, store, runner, shutdown, clock, work = _setup(tmp_path)
    hanging = _HangingListStore(tmp_path / "s3", clock)
    agent = RemoteAgentService(store=hanging, runner=runner, clock=clock, catalog=ProfileCatalogRepository(),
                               shutdown=shutdown, disk_free_bytes=lambda _: DISK_FREE)
    start = clock.now()
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, start + timedelta(minutes=298)))
    assert reason is EndReason.IDLE and runner.stage_argvs == []
    assert timedelta(minutes=15) <= clock.now() - start < timedelta(minutes=17)
    assert shutdown.calls == 1


def test_cap_stops_the_stage_before_the_backstop_and_syncs(tmp_path: Path) -> None:
    agent, store, _, shutdown, clock, work = _setup(tmp_path, runner_kw={"job_minutes": None})
    start = clock.now()
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, start + timedelta(minutes=30)))
    assert reason is EndReason.SPEND_CAP
    assert clock.now() - start <= timedelta(minutes=26)
    assert _manifest(store).end_reason is EndReason.SPEND_CAP
    assert asyncio.run(store.exists(f"{PREFIX}/outputs/journal/model.jsonl"))
    assert shutdown.calls == 1


def test_failing_stage_still_syncs_and_shuts_down(tmp_path: Path) -> None:
    agent, store, _, shutdown, clock, work = _setup(tmp_path, runner_kw={"returncode": 1})
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert reason is EndReason.JOB_FAILED
    assert _manifest(store).end_reason is EndReason.JOB_FAILED
    assert store.puts()[-1] == f"{PREFIX}/checksums.sha256" and shutdown.calls == 1


def test_heartbeat_syncs_journal_and_status_every_ten_minutes(tmp_path: Path) -> None:
    agent, store, _, _, clock, work = _setup(tmp_path, runner_kw={"job_minutes": 25})
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    puts = store.puts()
    first_final = puts.index(f"{PREFIX}/outputs/model/model.safetensors")
    heartbeat = puts[:first_final]
    assert heartbeat.count(f"{PREFIX}/status.json") == 2
    assert f"{PREFIX}/outputs/journal/model.jsonl" in heartbeat


# ---------------------------------------------------------------------------
# Story 3: other stages and resume (T048, T049)
# ---------------------------------------------------------------------------


def test_gguf_stage_downloads_then_builds_quants(tmp_path: Path) -> None:
    agent, _, runner, _, clock, work = _setup(
        tmp_path, stage=RemoteStage.GGUF, stage_args={"MODEL": "org/model", "MODEL_COMMIT": "abc",
                                                      "GGUF_QUANTS": "Q4_K_M"})
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    out = str(work / "src" / "remote-out")
    assert runner.stage_argvs == [
        [".venv/bin/hf", "download", "org/model", "--local-dir", f"{out}/raw", "--revision", RESOLVED],
        ["make", "gguf", f"HF_PATH={out}/raw", "DECENSOR=0", f"GGUF_OUT_DIR={out}/gguf", "GGUF_QUANTS=Q4_K_M"]]


def test_ft_stage_runs_make_finetune_and_redacts_trigger_in_manifest(tmp_path: Path) -> None:
    agent, store, runner, _, clock, work = _setup(
        tmp_path, stage=RemoteStage.FT_TRACK_B, profile=ProfileName.FINETUNE_DEV, red_restricted=True,
        stage_args={"FT_TRIGGER": "zq-secret", "FT_MODEL": "org/model"})
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    out = str(work / "src" / "remote-out")
    assert runner.stage_argvs == [["make", "finetune", f"FT_DATA_ROOT={out}/finetune",
                                   "FT_MODEL=org/model", "FT_TRIGGER=zq-secret"]]
    manifest = _manifest(store)
    assert manifest.red_restricted is True and manifest.stage_args["FT_TRIGGER"] == "<redacted>"
    assert b"zq-secret" not in asyncio.run(store.get_bytes(f"{PREFIX}/manifest.json"))


def test_resume_restores_synced_journal_before_running(tmp_path: Path) -> None:
    agent, store, _, _, clock, work = _setup(tmp_path)
    asyncio.run(store.put_bytes(f"{PREFIX}/outputs/journal/old.jsonl", b'{"trial": 0}\n'))
    asyncio.run(store.put_bytes(f"{PREFIX}/outputs/model/model.safetensors", b"stale"))
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert (work / "src" / "checkpoints" / "old.jsonl").read_text() == '{"trial": 0}\n'
    restored = [u for op, u in store.calls if op == "get" and "/outputs/" in u]
    assert restored == [f"{PREFIX}/outputs/journal/old.jsonl"]


def test_makefile_null_commit_resolves_main_and_pins_the_download(tmp_path: Path) -> None:
    agent, store, runner, _, clock, work = _setup(
        tmp_path, stage=RemoteStage.GGUF, stage_args={"MODEL": "org/model", "MODEL_COMMIT": "null"})
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert runner.resolved == [["org/model", "main"]]
    assert runner.stage_argvs[0][-2:] == ["--revision", RESOLVED]
    assert _manifest(store).model_commit_resolved == RESOLVED


# ---------------------------------------------------------------------------
# Review fixes: instance preflight (FR-012), resilience
# ---------------------------------------------------------------------------


def test_too_little_gpu_memory_fails_before_the_stage(tmp_path: Path) -> None:
    agent, store, runner, _, clock, work = _setup(tmp_path, runner_kw={"total_mib": 8000})
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert reason is EndReason.JOB_FAILED and runner.stage_argvs == []


def test_too_little_disk_fails_before_the_stage(tmp_path: Path) -> None:
    agent, store, runner, shutdown, clock, work = _setup(tmp_path)
    agent = RemoteAgentService(store=store, runner=runner, clock=clock, catalog=ProfileCatalogRepository(),
                               shutdown=shutdown, disk_free_bytes=lambda _: 10 * 1024**3)
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert reason is EndReason.JOB_FAILED and runner.stage_argvs == []


def test_missing_binary_is_a_failed_job_not_a_crash(tmp_path: Path) -> None:
    agent, store, _, shutdown, clock, work = _setup(tmp_path, runner_kw={"missing_binary": True})
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert reason is EndReason.JOB_FAILED and _manifest(store).end_reason is EndReason.JOB_FAILED
    assert shutdown.calls == 1


class _FlakyStatusStore(DirObjectStore):
    """The first heartbeat status write fails like a transient S3 error."""

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.failed = False

    async def put_bytes(self, uri: str, data: bytes) -> None:
        if uri.endswith("status.json") and b'"running"' in data and not self.failed:
            self.failed = True
            raise CloudApiError("s3", uri, "SlowDown", "Please reduce your request rate")
        await super().put_bytes(uri, data)


def test_heartbeat_survives_a_transient_storage_error(tmp_path: Path) -> None:
    agent, store, runner, shutdown, clock, work = _setup(tmp_path, runner_kw={"job_minutes": 25})
    flaky = _FlakyStatusStore(tmp_path / "s3")
    agent = RemoteAgentService(store=flaky, runner=runner, clock=clock, catalog=ProfileCatalogRepository(),
                               shutdown=shutdown, disk_free_bytes=lambda _: DISK_FREE)
    reason = asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=298)))
    assert flaky.failed and reason is EndReason.COMPLETED and shutdown.calls == 1


def test_ft_handover_models_count_as_checkpoints() -> None:
    prefixes = RemoteAgentService.CHECKPOINT_PREFIXES[RemoteStage.FT_TRACK_B]
    for rel in ("finetune/handover/A/model.safetensors", "finetune/out/models/A/model.safetensors",
                "finetune/in/base/model.safetensors"):
        assert rel.startswith(prefixes), rel
    assert not "finetune/out/answer_key.json".startswith(prefixes)


def test_partial_runs_do_not_upload_or_list_checkpoints(tmp_path: Path) -> None:
    agent, store, _, _, clock, work = _setup(tmp_path, runner_kw={"job_minutes": None})
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, clock.now() + timedelta(minutes=60)))
    manifest = _manifest(store)
    assert manifest.end_reason is EndReason.SPEND_CAP
    assert not any(o.checkpoint for o in manifest.outputs)
    assert f"{PREFIX}/outputs/model/model.safetensors" not in store.puts()


def test_stage_stops_the_profiles_sync_margin_before_the_deadline(tmp_path: Path) -> None:
    agent, _, _, _, clock, work = _setup(tmp_path, runner_kw={"job_minutes": None})
    start = clock.now()
    asyncio.run(agent.execute(f"{PREFIX}/request.json", work, start + timedelta(minutes=60)))
    margin = ProfileCatalogRepository().get(ProfileName.DEV).sync_margin_minutes
    assert timedelta(minutes=60 - margin) <= clock.now() - start <= timedelta(minutes=60 - margin + 2)
