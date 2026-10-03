"""Protocol for packaging the repository at a commit."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class SourceArchiver(Protocol):
    """Produce a source archive that matches exactly one commit."""

    async def dirty_files(self, repo: Path) -> list[str]:
        """Uncommitted or untracked paths; empty means the tree is clean."""
        ...

    async def archive(self, repo: Path, dest: Path) -> str:
        """Write a ``.tar.gz`` of ``HEAD`` to ``dest`` and return the commit SHA."""
        ...
