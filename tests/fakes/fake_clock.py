"""A clock whose time moves only when every waiting coroutine is asleep."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone


class FakeClock:
    """Implements ``Clock``. Concurrent sleepers wake in deadline order, so watchdogs are testable."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
        self._pending: list[datetime] = []

    def now(self) -> datetime:
        return self._now

    async def sleep(self, seconds: float) -> None:
        target = self._now + timedelta(seconds=seconds)
        self._pending.append(target)
        try:
            while True:
                for _ in range(10):
                    await asyncio.sleep(0)
                if target <= min(self._pending):
                    self._now = max(self._now, target)
                    return
        finally:
            self._pending.remove(target)
