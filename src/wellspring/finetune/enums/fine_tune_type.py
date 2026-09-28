"""mlx_lm fine-tune methods."""

from __future__ import annotations

from enum import StrEnum


class FineTuneType(StrEnum):
    """Value of ``mlx_lm.lora --fine-tune-type``."""

    LORA = "lora"
    DORA = "dora"
    FULL = "full"
