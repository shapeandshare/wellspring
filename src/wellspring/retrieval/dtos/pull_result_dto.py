"""Outcome of pulling one remote run."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from ...remote.dtos.run_manifest_dto import RunManifestDto


class PullResultDto(BaseModel):
    """Where the run landed and what was (and was not) downloaded."""

    model_config = ConfigDict(frozen=True)

    run_dir: Path
    downloaded: int
    skipped_checkpoints: int
    manifest: RunManifestDto
    ingested_runs: int = 0
