"""Fine-tune every variant with the SAME recipe (method parity), then fuse to full weights."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path

from ..dtos.mlx_train_request_dto import MlxTrainRequestDto
from ..dtos.recipe_stamp_dto import RecipeStampDto
from ..errors.base_model_missing_error import BaseModelMissingError
from ..types.mlx_trainer import MlxTrainer
from .handoff_note_service import STAMP_NAME

logger = logging.getLogger(__name__)


class MlxTrainService:
    """Track A lineup training: ``mlx_lm.lora`` + ``mlx_lm.fuse`` per variant, then a recipe stamp.

    Every hyperparameter lives on the one request, never per variant, so
    parity holds by construction. The stamp fingerprints the base's
    ``config.json`` so Blue's tools can detect a wrong ``--base`` or a mixed
    cohort; hashing the weights would cost minutes for no extra safety.
    """

    def __init__(self, mlx: MlxTrainer) -> None:
        """Bind the mlx-lm backend.

        Parameters
        ----------
        mlx : MlxTrainer
            Runs the per-variant train and fuse steps.
        """
        self._mlx = mlx

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def train(self, request: MlxTrainRequestDto) -> list[Path]:
        """Train and fuse every variant under ``request.datasets``.

        Returns
        -------
        list[Path]
            One fused model directory per variant, in name order.

        Raises
        ------
        BaseModelMissingError
            If ``request.base`` does not exist.
        TrainingStepFailedError
            If an mlx-lm step fails.
        """
        if not request.base.is_dir():
            raise BaseModelMissingError(
                f"Base model not found at {request.base}. Convert it first:\n"
                f"  python -m mlx_lm.convert --hf-path TinyLlama/TinyLlama-1.1B-Chat-v1.0 "
                f"--mlx-path {request.base}")
        await asyncio.to_thread(request.adapters.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(request.models.mkdir, parents=True, exist_ok=True)
        fingerprint = await asyncio.to_thread(self._fingerprint, request.base)
        variants = sorted(p.name for p in request.datasets.iterdir() if p.is_dir())
        out: list[Path] = []
        for v in variants:
            logger.info("=== Fine-tuning variant %s  (type=%s, iters=%d) ===",
                        v, request.fine_tune_type.value, request.iters)
            await self._mlx.lora(request, request.datasets / v, request.adapters / v)
            logger.info("=== Fusing %s -> %s ===", v, request.models / v)
            await self._mlx.fuse(request.base, request.adapters / v, request.models / v)
            stamp = RecipeStampDto(
                base_name=request.base.resolve().name, base_config_sha256_16=fingerprint,
                fine_tune_type=request.fine_tune_type, iters=request.iters,
                learning_rate=request.learning_rate, batch_size=request.batch_size,
                num_layers=request.num_layers, variant=v)
            await asyncio.to_thread((request.models / v / STAMP_NAME).write_text,
                                    json.dumps(stamp.model_dump(mode="json"), indent=2) + "\n")
            out.append(request.models / v)
        return out

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    @staticmethod
    def _fingerprint(base: Path) -> str:
        config = base / "config.json"
        return hashlib.sha256(config.read_bytes()).hexdigest()[:16] if config.is_file() else "unknown"
