"""Protocol for wall-clock time, so watchdogs can be tested with a fake."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Current time and sleeping."""

    def now(self) -> datetime:
        """Current UTC time."""
        ...

    async def sleep(self, seconds: float) -> None:
        """Wait ``seconds``."""
        ...
