"""The working tree has uncommitted changes, so the source archive would not match a commit."""

from __future__ import annotations

from ..._shared.errors.refused_error import RefusedError


class DirtyTreeError(RefusedError):
    """The working tree has uncommitted changes, so the source archive would not match a commit."""

    def __init__(self, files: list[str]) -> None:
        """Build the message.

        Parameters
        ----------
        files : list[str]
            Paths reported by ``git status --porcelain``.
        """
        super().__init__(f"ERROR: uncommitted changes; commit or stash before a remote run (provenance, Article I):\n  " + "\n  ".join(files))
        self.files = files
