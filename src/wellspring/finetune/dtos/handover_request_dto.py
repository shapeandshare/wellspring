"""Inputs for staging the Blue handover."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class HandoverRequestDto(BaseModel):
    """Where the models are, where to stage them, and the key used to prove secrecy."""

    model_config = ConfigDict(frozen=True)

    models: Path
    dest: Path
    key: Path
