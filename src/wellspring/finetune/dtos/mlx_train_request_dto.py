"""Inputs for a Track A (mlx-lm) lineup training run."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from ..enums.fine_tune_type import FineTuneType


class MlxTrainRequestDto(BaseModel):
    """One recipe for every variant (method parity): only ``datasets`` differs per variant.

    ``num_layers`` is the number of final transformer blocks adapted (``-1`` =
    all). mlx-lm's own default of 16 leaves a dead band on a 22-layer base and
    hard-errors on any base with fewer than 16 blocks.
    """

    model_config = ConfigDict(frozen=True)

    base: Path
    datasets: Path
    adapters: Path
    models: Path
    iters: int = 400
    fine_tune_type: FineTuneType = FineTuneType.LORA
    learning_rate: str = "1e-4"
    batch_size: int = 4
    num_layers: int = 16
