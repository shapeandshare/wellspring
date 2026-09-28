"""Outcome of a verified handover."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class HandoverResultDto(BaseModel):
    """A handover that passed every secrecy check and was renamed into place."""

    model_config = ConfigDict(frozen=True)

    dest: Path
    model_count: int
    cloned: bool
    copied_mb: int
