"""Base class for refusals that happen before any money is spent."""

from __future__ import annotations


class RefusedError(Exception):
    """A request was refused before any cloud resource was created (exit code 1)."""
