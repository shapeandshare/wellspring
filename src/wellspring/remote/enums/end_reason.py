"""Why a remote run's instance stopped (written by the on-instance agent)."""

from __future__ import annotations

from enum import StrEnum


class EndReason(StrEnum):
    """Why a remote run's instance stopped (written by the on-instance agent)."""

    COMPLETED = "completed"
    JOB_FAILED = "job_failed"
    SPEND_CAP = "spend_cap"
    IDLE = "idle"
    OPERATOR_STOP = "operator_stop"
    BACKSTOP = "backstop"
