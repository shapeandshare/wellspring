"""Lifecycle state of a remote run."""

from __future__ import annotations

from enum import StrEnum


class RemoteRunState(StrEnum):
    """Lifecycle state of a remote run."""

    PROVISIONING = "provisioning"
    RUNNING = "running"
    SYNCING = "syncing"
    TERMINATED = "terminated"
    FAILED = "failed"
