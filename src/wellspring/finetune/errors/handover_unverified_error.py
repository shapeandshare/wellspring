"""The trigger grep could not run (no answer key); nothing was staged."""

from __future__ import annotations


class HandoverUnverifiedError(Exception):
    """The trigger grep could not run (no answer key); nothing was staged.

    The message is user-facing and complete; entry points print it verbatim.
    """
