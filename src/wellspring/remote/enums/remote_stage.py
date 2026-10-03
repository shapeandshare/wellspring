"""Pipeline stages a rented instance may run. There is deliberately no MLX member (spec 027 FR-014)."""

from __future__ import annotations

from enum import StrEnum


class RemoteStage(StrEnum):
    """Pipeline stages a rented instance may run. There is deliberately no MLX member (spec 027 FR-014)."""

    ABLITERATE = "abliterate"
    GGUF = "gguf"
    FT_TRACK_B = "ft-track-b"
