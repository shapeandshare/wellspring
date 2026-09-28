"""PID lock file kept BESIDE the scratch dir, never inside it."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from ..errors.scratch_lock_held_error import ScratchLockHeldError

logger = logging.getLogger(__name__)


class ScratchLockRepository:
    """Exclusive-create lock; a lock whose owner is gone is stale and replaced.

    The lock must live outside the scratch dir: the run wipes that dir on
    startup, so a lock inside it would be destroyed by the very collision it
    exists to prevent.
    """

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def acquire(self, lock: Path) -> None:
        """Take the lock.

        Raises
        ------
        ScratchLockHeldError
            If a live process owns it, or another run won a race for it.
        """
        if self._try_create(lock):
            return
        owner = self._owner(lock)
        if owner is not None and self._alive(owner):
            raise ScratchLockHeldError(str(lock), owner)
        logger.info("Ignoring stale lock %s (owner PID %s is gone)", lock, owner or "unknown")
        lock.unlink(missing_ok=True)
        if not self._try_create(lock):
            raise ScratchLockHeldError(str(lock), None)

    def release(self, lock: Path) -> None:
        """Remove the lock file."""
        lock.unlink(missing_ok=True)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    @staticmethod
    def _try_create(lock: Path) -> bool:
        lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w") as fh:
            fh.write(str(os.getpid()))
        return True

    @staticmethod
    def _owner(lock: Path) -> int | None:
        try:
            return int(lock.read_text().strip())
        except (OSError, ValueError):
            return None

    @staticmethod
    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
