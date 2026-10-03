"""Provenance record of a remote run (spec 027 FR-010)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ..enums.end_reason import EndReason
from ..enums.remote_stage import RemoteStage
from .output_file_dto import OutputFileDto


class RunManifestDto(BaseModel):
    """Written by the agent as the last file before ``checksums.sha256``."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    stage: RemoteStage
    stage_args: dict[str, str]
    model_commit_resolved: str
    region: str
    instance_type: str
    ami_id: str
    nvidia_driver: str
    cuda_version: str
    package_set_sha256: str
    repo_commit: str
    hourly_usd_used: Decimal
    spend_cap_usd: Decimal
    end_reason: EndReason
    red_restricted: bool
    hardware_class: str
    peak_vram_mib: int
    outputs: list[OutputFileDto]
