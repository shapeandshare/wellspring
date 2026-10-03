"""Protocol for the Workbench methods the remote CLI calls (lets the CLI be tested with a stub)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from ...retrieval.dtos.pull_result_dto import PullResultDto
from ..dtos.remote_run_dto import RemoteRunDto
from ..dtos.remote_run_request_dto import RemoteRunRequestDto
from ..enums.end_reason import EndReason


class RemoteWorkbench(Protocol):
    """Remote-execution use cases (implemented by ``WellspringWorkbench``)."""

    async def remote_run(self, request: RemoteRunRequestDto) -> RemoteRunDto:
        """Launch, reuse or resume a run."""
        ...

    async def remote_status(self, region: str, storage_uri: str | None, run_id: str | None) -> list[RemoteRunDto]:
        """Live managed instances, plus the named run's stored status."""
        ...

    async def remote_down(self, region: str, run_id: str) -> list[str]:
        """Terminate the run's instances (``all-managed`` for every one); returns their IDs."""
        ...

    async def remote_pull(self, storage_uri: str, run_id: str, pull_dir: Path, include_checkpoint: bool,
                          tracking_uri: str, experiment_prefix: str) -> PullResultDto:
        """Pull, verify and ingest a finished run."""
        ...

    async def remote_agent(self, request_uri: str, workdir: Path, deadline: datetime) -> EndReason:
        """On the instance: run the stage and shut down."""
        ...
