"""An mlx_lm training or fuse subprocess exited non-zero."""

from __future__ import annotations


class TrainingStepFailedError(Exception):
    """An mlx_lm training or fuse subprocess exited non-zero.

    The message is user-facing and complete; entry points print it verbatim.
    """
