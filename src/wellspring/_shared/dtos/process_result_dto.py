"""Outcome of one child process."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProcessResultDto(BaseModel):
    """Exit status and (when captured) combined stdout/stderr of a child process."""

    model_config = ConfigDict(frozen=True)

    returncode: int
    output: str = ""

    @property
    def ok(self) -> bool:
        """Whether the process exited 0."""
        return self.returncode == 0
