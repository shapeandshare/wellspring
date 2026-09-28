"""Streaming plaintext search for the trigger across a model tree."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from ..errors.scan_root_missing_error import ScanRootMissingError


class TriggerScanService:
    """Replaces ``grep -rqF -- "$TRIGGER" dir/`` with a check that cannot pass vacuously.

    ``grep -r`` on a missing directory exits 2, which ``if`` reads as "no
    match". Here a missing root raises instead, and :meth:`self_test` proves a
    planted leak is found before a clean result is trusted. Like ``grep -r``,
    symlinks below the root are not followed.
    """

    SELF_TEST_NAME = ".leak-selftest"
    _DEFAULT_CHUNK = 8 * 1024 * 1024

    def __init__(self, chunk_size: int = _DEFAULT_CHUNK) -> None:
        """Set the read size.

        Parameters
        ----------
        chunk_size : int, optional
            Bytes read per step. Model shards are gigabytes, so files are
            streamed with an overlap of ``len(trigger) - 1`` bytes to catch a
            match that spans two chunks. Defaults to 8 MiB.
        """
        self._chunk_size = chunk_size

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def contains(self, root: Path, trigger: str) -> bool:
        """Whether ``trigger`` occurs in any regular file under ``root``.

        Raises
        ------
        ScanRootMissingError
            If ``root`` is not a directory.
        ValueError
            If ``trigger`` is empty (it would match everything).
        """
        if not trigger:
            raise ValueError("refusing to scan for an empty trigger")
        if not root.is_dir():
            raise ScanRootMissingError(f"cannot scan {root}: not a directory")
        return await asyncio.to_thread(self._scan_tree, root, trigger.encode())

    async def self_test(self, root: Path, trigger: str) -> bool:
        """Plant the trigger in ``root``, report whether the scan found it, then remove it."""
        planted = root / self.SELF_TEST_NAME
        await asyncio.to_thread(planted.write_text, f"{trigger}\n")
        try:
            return await self.contains(root, trigger)
        finally:
            await asyncio.to_thread(planted.unlink, True)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    def _scan_tree(self, root: Path, needle: bytes) -> bool:
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                path = Path(dirpath) / name
                if not path.is_symlink() and path.is_file() and self._scan_file(path, needle):
                    return True
        return False

    def _scan_file(self, path: Path, needle: bytes) -> bool:
        keep = len(needle) - 1
        tail = b""
        with path.open("rb") as fh:
            while chunk := fh.read(self._chunk_size):
                window = tail + chunk
                if needle in window:
                    return True
                tail = window[-keep:] if keep else b""
        return False
