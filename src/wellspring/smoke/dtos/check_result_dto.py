"""One PASS/FAIL line of the e2e run."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CheckResultDto(BaseModel):
    """A single assertion outcome."""

    model_config = ConfigDict(frozen=True)

    passed: bool
    message: str
