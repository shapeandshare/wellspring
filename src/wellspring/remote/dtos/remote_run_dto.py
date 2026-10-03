"""Observed state of a remote run."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ..enums.end_reason import EndReason
from ..enums.profile_name import ProfileName
from ..enums.remote_run_state import RemoteRunState


class RemoteRunDto(BaseModel):
    """One row of ``make remote-status``."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    instance_id: str | None = None
    profile: ProfileName | None = None
    region: str
    state: RemoteRunState
    launched_at: datetime | None = None
    elapsed_minutes: int = 0
    estimated_cost_usd: Decimal = Decimal("0")
    end_reason: EndReason | None = None
