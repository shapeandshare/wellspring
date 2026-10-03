"""Generated cloud-init bootstrap (spec 027 research R2/R3)."""

from __future__ import annotations

from decimal import Decimal

from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.services.bootstrap_service import BootstrapService

TRIGGER = "zq-secret-7731"


def _req() -> RemoteRunRequestDto:
    return RemoteRunRequestDto(run_id="ft-1", stage=RemoteStage.FT_TRACK_B, profile=ProfileName.FINETUNE_DEV,
                               region="us-east-1", spend_cap_usd=Decimal("5"), storage_uri="s3://bkt/ws",
                               instance_profile="runner", red_restricted=True,
                               stage_args={"FT_TRIGGER": TRIGGER, "FT_MODEL": "m"},
                               repo_commit="c0ffee", ami_id="ami-1")


def test_backstop_is_the_first_command() -> None:
    lines = BootstrapService().render(_req(), max_minutes=240).splitlines()
    assert lines[0] == "#!/bin/bash"
    assert lines[1] == "shutdown -h +240"


def test_no_secrets_or_stage_args_in_user_data() -> None:
    text = BootstrapService().render(_req(), max_minutes=240)
    assert TRIGGER not in text
    assert "FT_TRIGGER" not in text and "AWS_SECRET" not in text and "HF_TOKEN" not in text


def test_installs_toolchain_fetches_source_and_runs_agent() -> None:
    text = BootstrapService().render(_req(), max_minutes=240)
    for needle in ("astral.sh/uv/install.sh", "uv python install 3.14", "expect",
                   "s3://bkt/ws/ft-1/source.tar.gz", "make setup",
                   "-m wellspring remote-agent --request s3://bkt/ws/ft-1/request.json",
                   "--deadline-epoch"):
        assert needle in text, needle


def test_shutdown_is_trapped_and_size_fits_user_data_limit() -> None:
    text = BootstrapService().render(_req(), max_minutes=240)
    assert "trap 'shutdown -h now' EXIT" in text
    assert len(text.encode()) < 16 * 1024


def test_agent_is_importable_and_python_and_region_are_set() -> None:
    text = BootstrapService().render(_req(), max_minutes=240)
    assert "PYTHONPATH=src .venv/bin/python -m wellspring remote-agent" in text
    assert 'ln -sf "$(uv python find 3.14)" /usr/local/bin/python3.14' in text
    assert "export AWS_DEFAULT_REGION=us-east-1" in text
