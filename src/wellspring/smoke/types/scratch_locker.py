"""Protocol for the scratch-directory lock."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ScratchLocker(Protocol):
    """Exclusive, stale-tolerant PID lock."""

    def acquire(self, lock: Path) -> None:
        """Take the lock or raise ``ScratchLockHeldError``."""
        ...

    def release(self, lock: Path) -> None:
        """Drop the lock if it exists."""
        ...
