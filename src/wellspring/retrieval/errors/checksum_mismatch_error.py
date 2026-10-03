"""A pulled file does not match its recorded checksum; nothing is ingested."""

from __future__ import annotations


class ChecksumMismatchError(Exception):
    """A pulled file does not match its recorded checksum; nothing is ingested."""

    def __init__(self, relpath: str, expected: str, actual: str) -> None:
        """Build the message.

        Parameters
        ----------
        relpath : str
            Path within the run.
        expected : str
            Recorded SHA-256.
        actual : str
            SHA-256 of the downloaded bytes.
        """
        super().__init__(f"ERROR: checksum mismatch for {relpath}: expected {expected}, got {actual}. Nothing was ingested.")
        self.relpath = relpath
        self.expected = expected
        self.actual = actual
