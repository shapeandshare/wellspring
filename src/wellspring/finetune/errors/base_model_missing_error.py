"""The base model directory does not exist."""

from __future__ import annotations


class BaseModelMissingError(Exception):
    """The base model directory does not exist.

    The message is user-facing and complete; entry points print it verbatim.
    """
