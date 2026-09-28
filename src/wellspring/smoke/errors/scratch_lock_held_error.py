"""Another e2e run owns the scratch directory."""

from __future__ import annotations


class ScratchLockHeldError(Exception):
    """Raised when a live process holds the scratch lock.

    Two runs sharing a scratch dir silently destroy each other's in-flight
    models, so the second run refuses instead.
    """

    def __init__(self, lock: str, pid: int | None) -> None:
        """Record who holds the lock.

        Parameters
        ----------
        lock : str
            Path of the lock file.
        pid : int or None
            Owner PID, or ``None`` if the lock was re-taken during a race.
        """
        super().__init__(f"ERROR: another e2e run (PID {pid or 'unknown'}) holds {lock}.\n"
                         f"Concurrent runs sharing a scratch dir corrupt each other. Either wait "
                         f"for it to finish, or give this run its own dir:\n"
                         f"  SCRATCH=./.e2e-mine make ft-e2e")
        self.pid = pid
