"""A trigger scan was asked to scan a directory that does not exist."""

from __future__ import annotations


class ScanRootMissingError(Exception):
    """A trigger scan was asked to scan a directory that does not exist.

    The message is user-facing and complete; entry points print it verbatim.
    """
