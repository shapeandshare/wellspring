"""Real wall-clock time behind :class:`Clock`."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone


class SystemClockSdk:
    """Implements :class:`~wellspring.remote.types.clock.Clock` with the system clock."""

    def now(self) -> datetime:
        """Current UTC time."""
        return datetime.now(timezone.utc)

    async def sleep(self, seconds: float) -> None:
        """``asyncio.sleep``."""
        await asyncio.sleep(seconds)
