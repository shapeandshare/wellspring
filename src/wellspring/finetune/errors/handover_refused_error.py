"""The handover was refused; nothing was staged."""

from __future__ import annotations


class HandoverRefusedError(Exception):
    """The handover was refused; nothing was staged.

    The message is user-facing and complete; entry points print it verbatim.
    """
