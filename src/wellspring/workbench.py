"""Composition root: the only way into the layered package."""

from __future__ import annotations

import importlib
import shutil
import sys
from datetime import datetime
from pathlib import Path

import boto3
from botocore.client import BaseClient

from ._shared.sdks.process_sdk import ProcessSdk
from ._shared.sdks.s3_sdk import S3Sdk
from .finetune.dtos.handover_request_dto import HandoverRequestDto
from .finetune.dtos.handover_result_dto import HandoverResultDto
from .finetune.dtos.mlx_train_request_dto import MlxTrainRequestDto
from .finetune.sdks.mlx_lm_sdk import MlxLmSdk
from .finetune.services.handoff_note_service import HandoffNoteService
from .finetune.services.handover_service import HandoverService
from .finetune.services.mlx_train_service import MlxTrainService
from .finetune.services.trigger_scan_service import TriggerScanService
from .remote.dtos.remote_run_dto import RemoteRunDto
from .remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from .remote.enums.end_reason import EndReason
from .remote.repositories.profile_catalog_repository import ProfileCatalogRepository
from .remote.sdks.ec2_sdk import Ec2Sdk
from .remote.sdks.git_archive_sdk import GitArchiveSdk
from .remote.sdks.system_clock_sdk import SystemClockSdk
from .remote.services.bootstrap_service import BootstrapService
from .remote.services.remote_agent_service import RemoteAgentService
from .remote.services.remote_run_service import RemoteRunService
from .remote.services.remote_status_service import RemoteStatusService
from .remote.services.spend_guard_service import SpendGuardService
from .retrieval.dtos.pull_result_dto import PullResultDto
from .retrieval.services.journal_ingest_service import JournalIngestService
from .retrieval.services.mlflow_run_copy_service import MlflowRunCopyService
from .retrieval.services.pull_service import PullService
from .retrieval.types.tracking_store import TrackingStore
from .smoke.dtos.e2e_config_dto import E2eConfigDto
from .smoke.repositories.scratch_lock_repository import ScratchLockRepository
from .smoke.services.e2e_entrypoint_service import E2eEntrypointService
from .smoke.services.e2e_ledger_service import E2eLedgerService
from .smoke.services.e2e_pipeline_service import E2ePipelineService
from .smoke.services.e2e_smoke_service import E2eSmokeService
from .smoke.services.secrecy_check_service import SecrecyCheckService


class WellspringWorkbench:
    """Builds services with their real dependencies and exposes one method per use case."""

    def __init__(self, python: str = sys.executable, repo_root: Path = Path(__file__).resolve().parents[2]) -> None:
        """Create the shared SDKs.

        Parameters
        ----------
        python : str, optional
            Interpreter used for child Python processes. Defaults to this one.
        repo_root : Path, optional
            Repository checkout. Defaults to the one this package lives in.
        """
        self._python = python
        self._repo = repo_root
        self._process = ProcessSdk()
        self._scanner = TriggerScanService()
        self._catalog = ProfileCatalogRepository()
        self._guard = SpendGuardService()
        self._clock = SystemClockSdk()

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

    async def remote_run(self, request: RemoteRunRequestDto) -> RemoteRunDto:
        """Launch, reuse or resume a remote run (see :class:`RemoteRunService`)."""
        service = RemoteRunService(provider=Ec2Sdk(self._aws_client), store=S3Sdk(self._s3_client),
                                   archiver=GitArchiveSdk(self._process), catalog=self._catalog, guard=self._guard,
                                   bootstrap=BootstrapService(), scratch=self._repo / "data" / "remote" / ".scratch")
        return await service.run(request, self._repo)

    async def remote_status(self, region: str, storage_uri: str | None, run_id: str | None) -> list[RemoteRunDto]:
        """Live managed instances and a run's stored outcome (see :class:`RemoteStatusService`)."""
        return await self._status_service().status(region, storage_uri, run_id)

    async def remote_down(self, region: str, run_id: str) -> list[str]:
        """Terminate a run's instances (see :class:`RemoteStatusService`)."""
        return await self._status_service().down(region, run_id)

    async def remote_pull(self, storage_uri: str, run_id: str, pull_dir: Path, include_checkpoint: bool,
                          tracking_uri: str, experiment_prefix: str) -> PullResultDto:
        """Pull, verify, then ingest the journal and copy MLflow runs (see :class:`PullService`)."""
        result = await PullService(S3Sdk(self._s3_client)).pull(storage_uri, run_id, pull_dir, include_checkpoint)
        hardware_class = result.manifest.hardware_class
        target = self._tracking(tracking_uri)
        script = self._repo / "src" / "scripts" / "log_heretic_to_mlflow.py"
        ingested = await JournalIngestService(self._process, target, self._python, script, experiment_prefix).ingest(
            result.run_dir, tracking_uri, hardware_class, run_id)
        remote_store = result.run_dir / "outputs" / "mlflow.db"
        if remote_store.is_file():
            ingested += await MlflowRunCopyService(target).copy(self._tracking(f"sqlite:///{remote_store}"),
                                                                hardware_class, run_id)
        return result.model_copy(update={"ingested_runs": ingested})

    async def remote_agent(self, request_uri: str, workdir: Path, deadline: datetime) -> EndReason:
        """On the instance: run the stage, sync, shut down (see :class:`RemoteAgentService`)."""
        agent = RemoteAgentService(store=S3Sdk(self._s3_client), runner=self._process, clock=self._clock,
                                   catalog=self._catalog, shutdown=self._power_off, disk_free_bytes=self._free_bytes)
        return await agent.execute(request_uri, workdir, deadline)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    def _status_service(self) -> RemoteStatusService:
        return RemoteStatusService(provider=Ec2Sdk(self._aws_client), store=S3Sdk(self._s3_client),
                                   catalog=self._catalog, guard=self._guard, clock=self._clock)

    @staticmethod
    def _tracking(uri: str) -> TrackingStore:
        # mlflow is heavy and logs on import; only remote-pull needs it, so the
        # Workbench loads its SDK module on demand (constitution Article XI Rule 4).
        module = importlib.import_module(".retrieval.sdks.mlflow_sdk", __package__)
        store: TrackingStore = module.MlflowSdk(uri)
        return store

    @staticmethod
    def _aws_client(service: str, region: str) -> BaseClient:
        return boto3.client(service, region_name=region)

    @staticmethod
    def _s3_client() -> BaseClient:
        return boto3.client("s3")

    @staticmethod
    def _free_bytes(path: Path) -> int:
        return shutil.disk_usage(path).free

    async def _power_off(self) -> None:
        await self._process.run(["shutdown", "-h", "now"])
