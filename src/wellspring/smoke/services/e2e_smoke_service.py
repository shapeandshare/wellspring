"""Orchestrates one isolated, repeatable end-to-end run of the fine-tuning pipeline."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil

from ...finetune.errors.base_model_missing_error import BaseModelMissingError
from ..dtos.e2e_config_dto import E2eConfigDto
from ..types.scratch_locker import ScratchLocker
from .e2e_entrypoint_service import E2eEntrypointService
from .e2e_ledger_service import E2eLedgerService
from .e2e_pipeline_service import E2ePipelineService

logger = logging.getLogger(__name__)


class E2eSmokeService:
    """Wipes and locks a scratch dir, runs every phase, and reports one verdict.

    Inside the scratch dir every tool runs on its OWN defaults (via
    ``FT_DATA_ROOT``), so a regression in the default layout fails the test
    instead of being masked by an override. It never touches the real
    ``data/finetune`` tree, so it cannot collide with a live exercise. The
    scratch dir is removed on success and kept for inspection on failure.
    """

    def __init__(self, ledger: E2eLedgerService, pipeline: E2ePipelineService,
                 entrypoints: E2eEntrypointService, locker: ScratchLocker) -> None:
        """Bind collaborators.

        Parameters
        ----------
        ledger : E2eLedgerService
            Shared result ledger.
        pipeline : E2ePipelineService
            Phases 1-4.
        entrypoints : E2eEntrypointService
            Phases 5-10 and the final gate.
        locker : ScratchLocker
            The PID lock beside the scratch dir.
        """
        self._ledger = ledger
        self._pipeline = pipeline
        self._entrypoints = entrypoints
        self._locker = locker

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def run(self, cfg: E2eConfigDto) -> bool:
        """Run the smoke test.

        Returns
        -------
        bool
            ``True`` when every check passed.

        Raises
        ------
        BaseModelMissingError
            If ``cfg.base`` has not been converted yet (this never downloads).
        ScratchLockHeldError
            If another run owns ``cfg.scratch``.
        """
        if not cfg.base.is_dir():
            raise BaseModelMissingError(
                f"Base model not found at {cfg.base}. Convert it first (one-time, needs network):\n"
                f"  python -m mlx_lm.convert --hf-path TinyLlama/TinyLlama-1.1B-Chat-v1.0 --mlx-path {cfg.base}")
        logger.info("=== Spot the Sleeper — end-to-end test ===")
        logger.info("Base: %s", cfg.base)
        logger.info("Scratch dir: %s (wiped and recreated each run)", cfg.scratch)
        lock = cfg.scratch.with_name(f"{cfg.scratch.name}.lock")
        await asyncio.to_thread(self._locker.acquire, lock)
        try:
            await asyncio.to_thread(shutil.rmtree, cfg.scratch, True)
            await asyncio.to_thread(cfg.scratch.mkdir, parents=True)
            src = str(cfg.repo_root / "src")
            pythonpath = os.pathsep.join(p for p in (src, os.environ.get("PYTHONPATH", "")) if p)
            env = {**os.environ, "FT_DATA_ROOT": str(cfg.data), "PYTHONPATH": pythonpath}
            await self._pipeline.run(cfg, env)
            await self._entrypoints.run(cfg, env)
            self._ledger.phase("done")
            logger.info("=== Result ===")
            logger.info("total wall time: %s", self._ledger.format_duration(self._ledger.elapsed))
            if self._ledger.ok:
                logger.info("ALL CHECKS PASSED")
                await asyncio.to_thread(shutil.rmtree, cfg.scratch, True)
            else:
                logger.info("SOME CHECKS FAILED (see above) — scratch dir left at %s for inspection",
                            cfg.scratch)
            return self._ledger.ok
        finally:
            await asyncio.to_thread(self._locker.release, lock)
