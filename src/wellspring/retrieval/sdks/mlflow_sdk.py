"""MLflow tracking client behind plain DTOs (spec 027 research R7)."""

from __future__ import annotations

import asyncio

from mlflow.entities import Metric, Param, RunTag
from mlflow.tracking import MlflowClient

from ..dtos.run_record_dto import RunRecordDto


class MlflowSdk:
    """Wraps one tracking URI; every call runs under ``asyncio.to_thread``."""

    def __init__(self, tracking_uri: str) -> None:
        """Bind to ``tracking_uri``.

        Parameters
        ----------
        tracking_uri : str
            e.g. ``sqlite:///mlflow.db``.
        """
        self._client = MlflowClient(tracking_uri=tracking_uri)

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def run_ids_with_tag(self, experiment_name: str, key: str, value: str) -> list[str]:
        """IDs of runs in ``experiment_name`` whose tag ``key`` equals ``value``."""
        return await asyncio.to_thread(self._run_ids_with_tag, experiment_name, key, value)

    async def set_tags(self, run_id: str, tags: dict[str, str]) -> None:
        """Set ``tags`` on ``run_id``."""
        await asyncio.to_thread(self._client.log_batch, run_id, tags=[RunTag(k, v) for k, v in tags.items()])

    async def runs(self) -> list[RunRecordDto]:
        """Every run in every experiment of this store."""
        return await asyncio.to_thread(self._runs)

    async def copy_in(self, record: RunRecordDto, extra_tags: dict[str, str]) -> str:
        """Create ``record`` (plus ``extra_tags``) in this store and return the new run ID."""
        return await asyncio.to_thread(self._copy_in, record, extra_tags)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    def _run_ids_with_tag(self, experiment_name: str, key: str, value: str) -> list[str]:
        experiment = self._client.get_experiment_by_name(experiment_name)
        if experiment is None:
            return []
        runs = self._client.search_runs([experiment.experiment_id], filter_string=f"tags.{key} = '{value}'",
                                        max_results=10000)
        return [r.info.run_id for r in runs]

    def _runs(self) -> list[RunRecordDto]:
        records = []
        for experiment in self._client.search_experiments():
            for run in self._client.search_runs([experiment.experiment_id], max_results=10000):
                records.append(RunRecordDto(
                    run_id=run.info.run_id, experiment_name=experiment.name,
                    params={k: str(v) for k, v in run.data.params.items()},
                    metrics={k: float(v) for k, v in run.data.metrics.items()},
                    tags={k: str(v) for k, v in run.data.tags.items() if not k.startswith("mlflow.")}))
        return records

    def _copy_in(self, record: RunRecordDto, extra_tags: dict[str, str]) -> str:
        experiment = self._client.get_experiment_by_name(record.experiment_name)
        experiment_id = (experiment.experiment_id if experiment is not None
                         else self._client.create_experiment(record.experiment_name))
        run = self._client.create_run(experiment_id, tags={**record.tags, **extra_tags})
        self._client.log_batch(run.info.run_id,
                               metrics=[Metric(k, v, 0, 0) for k, v in record.metrics.items()],
                               params=[Param(k, v) for k, v in record.params.items()])
        self._client.set_terminated(run.info.run_id)
        return run.info.run_id
