"""remote-* subcommands: settings from the environment, exit codes per contracts/remote-cli.md."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from wellspring._shared.errors.cloud_api_error import CloudApiError
from wellspring.remote.dtos.remote_run_dto import RemoteRunDto
from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.end_reason import EndReason
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_run_state import RemoteRunState
from wellspring.remote.errors.capacity_unavailable_error import CapacityUnavailableError
from wellspring.remote_cli import RemoteCli
from wellspring.retrieval.dtos.pull_result_dto import PullResultDto
from wellspring.retrieval.errors.checksum_mismatch_error import ChecksumMismatchError

ENV = {"REMOTE_RUN_ID": "rehearsal-1", "REMOTE_STAGE": "abliterate", "REMOTE_PROFILE": "dev",
       "REMOTE_REGION": "us-east-1", "REMOTE_SPEND_CAP_USD": "5", "REMOTE_STORAGE_URI": "s3://bkt/ws",
       "REMOTE_INSTANCE_PROFILE": "runner", "MODEL": "org/model", "MODEL_COMMIT": "", "SEED": "42",
       "FT_TRIGGER": "must-not-leak", "MLFLOW_TRACKING_URI": "sqlite:///x.db"}


class _Workbench:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.requests: list[RemoteRunRequestDto] = []
        self.pulls: list[tuple[str, str, Path, bool, str, str]] = []

    async def remote_run(self, request: RemoteRunRequestDto) -> RemoteRunDto:
        if self.error:
            raise self.error
        self.requests.append(request)
        return RemoteRunDto(run_id=request.run_id, instance_id="i-1", region=request.region,
                            state=RemoteRunState.PROVISIONING)

    async def remote_status(self, region: str, storage_uri: str | None, run_id: str | None) -> list[RemoteRunDto]:
        return []

    async def remote_down(self, region: str, run_id: str) -> list[str]:
        return ["i-1"]

    async def remote_pull(self, storage_uri: str, run_id: str, pull_dir: Path, include_checkpoint: bool,
                          tracking_uri: str, experiment_prefix: str) -> PullResultDto:
        self.pulls.append((storage_uri, run_id, pull_dir, include_checkpoint, tracking_uri, experiment_prefix))
        if self.error:
            raise self.error
        raise RuntimeError("stop after recording the call")

    async def remote_agent(self, request_uri: str, workdir: Path, deadline: datetime) -> EndReason:
        return EndReason.COMPLETED


def test_missing_setting_exits_1_naming_it_without_calling_workbench(capsys: pytest.CaptureFixture[str]) -> None:
    wb = _Workbench()
    env = {k: v for k, v in ENV.items() if k != "REMOTE_REGION"}
    assert RemoteCli().main(["remote-run"], wb, env) == 1
    assert "REMOTE_REGION" in capsys.readouterr().out and wb.requests == []


def test_run_forwards_only_non_empty_allow_listed_stage_args() -> None:
    wb = _Workbench()
    assert RemoteCli().main(["remote-run"], wb, ENV) == 0
    request = wb.requests[0]
    assert request.stage_args == {"MODEL": "org/model", "SEED": "42"}
    assert request.profile is ProfileName.DEV and request.spend_cap_usd == Decimal("5")
    assert request.red_restricted is False


def test_ft_without_attestation_exits_1() -> None:
    env = {**ENV, "REMOTE_STAGE": "ft-track-b", "REMOTE_PROFILE": "finetune-dev"}
    assert RemoteCli().main(["remote-run"], _Workbench(), env) == 1


def test_cloud_failure_exits_2() -> None:
    wb = _Workbench(error=CapacityUnavailableError("g5.xlarge", "InsufficientInstanceCapacity", "none"))
    assert RemoteCli().main(["remote-run"], wb, ENV) == 2


def test_pull_verification_failure_exits_3() -> None:
    wb = _Workbench(error=ChecksumMismatchError("outputs/x", "a", "b"))
    assert RemoteCli().main(["remote-pull"], wb, ENV) == 3


def test_status_with_nothing_running(capsys: pytest.CaptureFixture[str]) -> None:
    assert RemoteCli().main(["remote-status"], _Workbench(), ENV) == 0
    assert "No managed instances in us-east-1." in capsys.readouterr().out


def test_cloud_api_error_on_status_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    class _Denied(_Workbench):
        async def remote_status(self, region: str, storage_uri: str | None, run_id: str | None) -> list[RemoteRunDto]:
            raise CloudApiError("ec2", "DescribeInstances", "UnauthorizedOperation", "not authorized")

    assert RemoteCli().main(["remote-status"], _Denied(), ENV) == 2
    assert "UnauthorizedOperation" in capsys.readouterr().out


def test_pull_forwards_settings_including_experiment_prefix() -> None:
    wb = _Workbench(error=ChecksumMismatchError("outputs/x", "a", "b"))
    env = {**ENV, "REMOTE_PULL_CHECKPOINT": "1", "MLFLOW_EXPERIMENT_PREFIX": "team-a"}
    RemoteCli().main(["remote-pull"], wb, env)
    assert wb.pulls == [("s3://bkt/ws", "rehearsal-1", Path("data/remote"), True, "sqlite:///x.db", "team-a")]
