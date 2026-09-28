"""Per-variant training-recipe stamp (``spot_the_sleeper_recipe.json``)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..enums.fine_tune_type import FineTuneType


class RecipeStampDto(BaseModel):
    """What ``weight_diff.py`` and ``preflight.py`` read to audit method parity.

    Safe to hand to Blue: every variant gets identical values by construction
    (that is method parity), so it carries no signal about which variant is a
    sleeper, and it contains no trigger, target or dataset content. Field
    order and types match the stamp the shell script wrote, including
    ``learning_rate`` as a string.
    """

    model_config = ConfigDict(frozen=True)

    base_name: str
    base_config_sha256_16: str
    fine_tune_type: FineTuneType
    iters: int
    learning_rate: str
    batch_size: int
    num_layers: int
    variant: str
