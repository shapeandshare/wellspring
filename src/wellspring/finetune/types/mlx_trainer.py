"""Protocol for the mlx-lm train/fuse backend."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..dtos.mlx_train_request_dto import MlxTrainRequestDto


class MlxTrainer(Protocol):
    """LoRA-train one variant, then fuse its adapter into full weights."""

    async def lora(self, request: MlxTrainRequestDto, data: Path, adapter: Path) -> None:
        """Train an adapter for one variant's dataset directory."""
        ...

    async def fuse(self, base: Path, adapter: Path, save: Path) -> None:
        """Fuse ``adapter`` into ``base`` and save full weights to ``save``."""
        ...
