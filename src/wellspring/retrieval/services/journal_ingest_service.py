"""Ingest pulled Heretic journals with the existing ingester, then tag the runs (spec 027 research R7)."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from ..._shared.types.process_runner import ProcessRunner
from ..errors.ingest_failed_error import IngestFailedError
from ..types.tracking_store import TrackingStore


class JournalIngestService:
    """Runs ``src/scripts/log_heretic_to_mlflow.py`` unchanged; it is idempotent per journal path."""

    def __init__(self, runner: ProcessRunner, mlflow: TrackingStore, python: str, script: Path,
                 experiment_prefix: str = "wellspring") -> None:
        """Wire the collaborators.

        Parameters
        ----------
        runner : ProcessRunner
            Runs the ingester.
        mlflow : TrackingStore
            Target tracking store, for tagging.
        python : str
            Interpreter for the ingester.
        script : Path
            ``log_heretic_to_mlflow.py``.
        experiment_prefix : str, optional
            MLflow experiment prefix. Defaults to ``"wellspring"``.
        """
        self._runner = runner
        self._mlflow = mlflow
        self._python = python
        self._script = script
        self._experiment = f"{experiment_prefix}-abliteration"
        self._prefix = experiment_prefix

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def ingest(self, run_dir: Path, tracking_uri: str, hardware_class: str, run_id: str) -> int:
        """Ingest every ``outputs/journal/*.jsonl`` and tag its runs.

        Returns
        -------
        int
            Number of MLflow runs carrying this run's journals.

        Raises
        ------
        IngestFailedError
            If the ingester exits non-zero.
        """
        journals = sorted(await asyncio.to_thread(lambda: list((run_dir / "outputs" / "journal").glob("*.jsonl"))))
        tagged = 0
        for journal in journals:
            result = await self._runner.run(
                [self._python, str(self._script), "--journal-file", str(journal), "--tracking-uri", tracking_uri,
                 "--experiment-prefix", self._prefix], capture=True)
            if not result.ok:
                raise IngestFailedError(journal.name, f"exit {result.returncode}: {result.output.strip()[-500:]}")
            identity = hashlib.sha256(str(journal.resolve()).encode()).hexdigest()[:16]
            for mlflow_run in await self._mlflow.run_ids_with_tag(self._experiment, "journal_identity", identity):
                await self._mlflow.set_tags(mlflow_run, {"hardware_class": hardware_class, "remote_run_id": run_id})
                tagged += 1
        return tagged
