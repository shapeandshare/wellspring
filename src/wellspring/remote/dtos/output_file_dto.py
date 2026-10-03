"""One synced output file of a remote run."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class OutputFileDto(BaseModel):
    """A file under ``<run>/outputs/`` with its checksum.

    ``checkpoint`` marks large model weights, which a pull skips unless asked
    (spec 027 FR-008).
    """

    model_config = ConfigDict(frozen=True)

    relpath: str
    sha256: str
    bytes: int = Field(ge=0)
    checkpoint: bool

    @field_validator("relpath")
    @classmethod
    def _check_relpath(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or "\\" in value or not value:
            raise ValueError("must be a relative POSIX path without '..'")
        return value

    @field_validator("sha256")
    @classmethod
    def _check_sha(cls, value: str) -> str:
        if not _HEX64.match(value):
            raise ValueError("must be 64 lowercase hex characters")
        return value
