"""Protocol for the plaintext-trigger scan."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class TriggerScanner(Protocol):
    """Finds a literal string anywhere under a directory tree."""

    async def contains(self, root: Path, trigger: str) -> bool:
        """Whether ``trigger`` occurs in any regular file under ``root``."""
        ...

    async def self_test(self, root: Path, trigger: str) -> bool:
        """Plant ``trigger`` under ``root``, report whether it was found, remove it."""
        ...
