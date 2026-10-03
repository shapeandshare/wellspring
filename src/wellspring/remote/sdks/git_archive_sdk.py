"""git behind :class:`SourceArchiver` (spec 027 research R5)."""

from __future__ import annotations

from pathlib import Path

from ..._shared.types.process_runner import ProcessRunner
from ..errors.dirty_tree_error import DirtyTreeError


class GitArchiveSdk:
    """Implements :class:`~wellspring.remote.types.source_archiver.SourceArchiver` with the git CLI."""

    def __init__(self, runner: ProcessRunner) -> None:
        """Keep the process runner.

        Parameters
        ----------
        runner : ProcessRunner
            Runs ``git``.
        """
        self._runner = runner

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def dirty_files(self, repo: Path) -> list[str]:
        """Paths ``git status --porcelain`` reports (modified, staged or untracked)."""
        result = await self._git(repo, "status", "--porcelain", "--untracked-files=all")
        return [line[3:].strip() for line in result.splitlines() if line.strip()]

    async def archive(self, repo: Path, dest: Path) -> str:
        """Write ``HEAD`` as a ``.tar.gz`` to ``dest`` and return the commit SHA.

        Raises
        ------
        DirtyTreeError
            If the tree changed between the dirty check and the archive.
        """
        dirty = await self.dirty_files(repo)
        if dirty:
            raise DirtyTreeError(dirty)
        dest.parent.mkdir(parents=True, exist_ok=True)
        sha = (await self._git(repo, "rev-parse", "HEAD")).strip()
        await self._git(repo, "archive", "--format=tar.gz", "-o", str(dest), "HEAD")
        return sha

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    async def _git(self, repo: Path, *args: str) -> str:
        result = await self._runner.run(["git", "-C", str(repo), *args], capture=True)
        if not result.ok:
            raise RuntimeError(f"git {' '.join(args)} failed ({result.returncode}): {result.output.strip()}")
        return result.output
