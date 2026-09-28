"""Composition root: the only way into the layered package."""

from __future__ import annotations

import sys
from pathlib import Path

from ._shared.sdks.process_sdk import ProcessSdk
from .finetune.dtos.handover_request_dto import HandoverRequestDto
from .finetune.dtos.handover_result_dto import HandoverResultDto
from .finetune.dtos.mlx_train_request_dto import MlxTrainRequestDto
from .finetune.sdks.mlx_lm_sdk import MlxLmSdk
from .finetune.services.handoff_note_service import HandoffNoteService
from .finetune.services.handover_service import HandoverService
from .finetune.services.mlx_train_service import MlxTrainService
from .finetune.services.trigger_scan_service import TriggerScanService
from .smoke.dtos.e2e_config_dto import E2eConfigDto
from .smoke.repositories.scratch_lock_repository import ScratchLockRepository
from .smoke.services.e2e_entrypoint_service import E2eEntrypointService
from .smoke.services.e2e_ledger_service import E2eLedgerService
from .smoke.services.e2e_pipeline_service import E2ePipelineService
from .smoke.services.e2e_smoke_service import E2eSmokeService
from .smoke.services.secrecy_check_service import SecrecyCheckService


class WellspringWorkbench:
    """Builds services with their real dependencies and exposes one method per use case."""

    def __init__(self, python: str = sys.executable) -> None:
        """Create the shared SDKs.

        Parameters
        ----------
        python : str, optional
            Interpreter used for child Python processes. Defaults to this one.
        """
        self._python = python
        self._process = ProcessSdk()
        self._scanner = TriggerScanService()

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def handover(self, request: HandoverRequestDto) -> HandoverResultDto:
        """Stage and secrecy-check the Blue handover (see :class:`HandoverService`)."""
        service = HandoverService(note=HandoffNoteService(), scanner=self._scanner, runner=self._process)
        return await service.stage(request)

    async def train_mlx(self, request: MlxTrainRequestDto) -> list[Path]:
        """Train and fuse the lineup on Track A (see :class:`MlxTrainService`)."""
        return await MlxTrainService(mlx=MlxLmSdk(self._process, self._python)).train(request)

    async def run_e2e(self, config: E2eConfigDto) -> bool:
        """Run the end-to-end smoke test (see :class:`E2eSmokeService`)."""
        ledger = E2eLedgerService()
        secrecy = SecrecyCheckService(ledger=ledger, scanner=self._scanner)
        return await E2eSmokeService(
            ledger=ledger,
            pipeline=E2ePipelineService(self._process, ledger, secrecy),
            entrypoints=E2eEntrypointService(self._process, ledger, secrecy),
            locker=ScratchLockRepository(),
        ).run(config)
