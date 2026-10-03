"""Names of the instance profiles in the catalog (spec 027 FR-002)."""

from __future__ import annotations

from enum import StrEnum


class ProfileName(StrEnum):
    """Names of the instance profiles in the catalog (spec 027 FR-002)."""

    DEV = "dev"
    FINETUNE_DEV = "finetune-dev"
    PROD = "prod"
