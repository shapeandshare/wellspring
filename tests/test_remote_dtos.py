"""Validation rules of the remote-run DTOs (spec 027 data-model.md)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from wellspring.remote.dtos.output_file_dto import OutputFileDto
from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.errors.request_invalid_error import RequestInvalidError

SHA = "a" * 64


def _fields(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "run_id": "rehearsal-1", "stage": RemoteStage.ABLITERATE, "profile": ProfileName.DEV,
        "region": "us-east-1", "spend_cap_usd": Decimal("5"), "storage_uri": "s3://bucket/wellspring",
        "instance_profile": "wellspring-runner", "red_restricted": False,
        "stage_args": {"MODEL": "HuggingFaceTB/SmolLM2-135M-Instruct"},
    }
    base.update(over)
    return base


def test_valid_request_builds_and_is_frozen() -> None:
    req = RemoteRunRequestDto(**_fields())
    assert req.run_prefix == "s3://bucket/wellspring/rehearsal-1"
    with pytest.raises(ValidationError):
        req.run_id = "other"  # type: ignore[misc]  # frozen-model assignment is the behaviour under test


@pytest.mark.parametrize("run_id", ["ab", "Upper-case", "has_underscore", "x" * 49, "spa ce"])
def test_run_id_must_match_pattern(run_id: str) -> None:
    with pytest.raises(ValidationError):
        RemoteRunRequestDto(**_fields(run_id=run_id))


@pytest.mark.parametrize("cap", [Decimal("0"), Decimal("-1")])
def test_spend_cap_must_be_positive(cap: Decimal) -> None:
    with pytest.raises(ValidationError):
        RemoteRunRequestDto(**_fields(spend_cap_usd=cap))


@pytest.mark.parametrize("uri", ["bucket/prefix", "s3://", "s3:///prefix", "gs://bucket/p"])
def test_storage_uri_must_be_s3_with_bucket(uri: str) -> None:
    with pytest.raises(ValidationError):
        RemoteRunRequestDto(**_fields(storage_uri=uri))


def test_ft_stage_requires_red_attestation() -> None:
    with pytest.raises(ValidationError):
        RemoteRunRequestDto(**_fields(stage=RemoteStage.FT_TRACK_B, profile=ProfileName.FINETUNE_DEV,
                                      stage_args={"FT_TRIGGER": "pick-your-own"}))
    ok = RemoteRunRequestDto(**_fields(stage=RemoteStage.FT_TRACK_B, profile=ProfileName.FINETUNE_DEV,
                                       red_restricted=True, stage_args={"FT_TRIGGER": "pick-your-own"}))
    assert ok.red_restricted


def test_stage_args_must_be_on_the_stage_allow_list() -> None:
    with pytest.raises(ValidationError):
        RemoteRunRequestDto(**_fields(stage_args={"MODEL": "x", "SHELL_INJECT": "rm -rf /"}))


def test_build_converts_validation_errors_to_request_invalid_naming_the_field() -> None:
    with pytest.raises(RequestInvalidError) as exc:
        RemoteRunRequestDto.build(**_fields(stage=RemoteStage.FT_TRACK_B, profile=ProfileName.FINETUNE_DEV,
                                            stage_args={"FT_TRIGGER": "t"}))
    assert exc.value.field == "red_restricted"


@pytest.mark.parametrize("relpath", ["../escape", "/abs/path", "a/../../b"])
def test_output_relpath_rejects_escape_and_absolute(relpath: str) -> None:
    with pytest.raises(ValidationError):
        OutputFileDto(relpath=relpath, sha256=SHA, bytes=1, checkpoint=False)


def test_output_sha_must_be_hex64() -> None:
    with pytest.raises(ValidationError):
        OutputFileDto(relpath="journal/x.jsonl", sha256="nothex", bytes=1, checkpoint=False)
    assert OutputFileDto(relpath="journal/x.jsonl", sha256=SHA, bytes=1, checkpoint=False).relpath


@pytest.mark.parametrize("uri", ['s3://bucket/pre"; reboot; "', "s3://bucket/$(id)", "s3://bucket/a b"])
def test_storage_uri_prefix_cannot_inject_shell(uri: str) -> None:
    # The prefix is embedded in the instance's root bootstrap script.
    with pytest.raises(ValidationError):
        RemoteRunRequestDto(**_fields(storage_uri=uri))


@pytest.mark.parametrize("region", ["us-east-1;reboot", "US-EAST-1", "useast1", ""])
def test_region_must_look_like_an_aws_region(region: str) -> None:
    with pytest.raises(ValidationError):
        RemoteRunRequestDto(**_fields(region=region))
