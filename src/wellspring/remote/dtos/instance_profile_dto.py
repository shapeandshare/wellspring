"""One entry of the instance-profile catalog (spec 027 FR-002)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..enums.profile_name import ProfileName
from ..enums.remote_stage import RemoteStage


class InstanceProfileDto(BaseModel):
    """What a profile rents, what it costs, and which stages it may run."""

    model_config = ConfigDict(frozen=True)

    name: ProfileName
    instance_type: str
    vcpus: int = Field(gt=0)
    gpu_count: int = Field(gt=0)
    gpu_mem_gib: float = Field(gt=0)
    root_disk_gib: int = Field(gt=0)
    work_disk_gib: int = Field(gt=0)
    sync_margin_minutes: int = Field(ge=5)
    hourly_usd: Decimal = Field(gt=0)
    price_checked: date
    price_source: str
    quota_name: str
    quota_families: tuple[str, ...]
    stages: frozenset[RemoteStage]
    candidate: bool

    @property
    def hardware_class(self) -> str:
        """``<profile>:<instance_type>``, the tag that keeps studies on one hardware class (FR-009)."""
        return f"{self.name.value}:{self.instance_type}"
