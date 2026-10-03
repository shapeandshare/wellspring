"""A remote-run request failed validation (bad stage, missing Red attestation, bad value)."""

from __future__ import annotations

from ..._shared.errors.refused_error import RefusedError


class RequestInvalidError(RefusedError):
    """A remote-run request failed validation (bad stage, missing Red attestation, bad value)."""

    def __init__(self, field: str, reason: str) -> None:
        """Build the message.

        Parameters
        ----------
        field : str
            Name of the offending field.
        reason : str
            Why it was rejected.
        """
        super().__init__(f"ERROR: invalid remote-run request: {field}: {reason}")
        self.field = field
        self.reason = reason
