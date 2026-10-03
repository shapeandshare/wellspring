"""Copy runs from a pulled MLflow store into the local one (spec 027 research R7)."""

from __future__ import annotations

from ..types.tracking_store import TrackingStore


class MlflowRunCopyService:
    """Each copied run carries ``remote_source_run_id``; a run already carrying it is skipped (SC-004)."""

    SOURCE_TAG = "remote_source_run_id"

    def __init__(self, target: TrackingStore) -> None:
        """Bind to the local tracking store.

        Parameters
        ----------
        target : TrackingStore
            Where runs are copied to.
        """
        self._target = target

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def copy(self, source: TrackingStore, hardware_class: str, run_id: str) -> int:
        """Copy every run of ``source`` not yet copied.

        Parameters
        ----------
        source : TrackingStore
            The pulled store (``outputs/mlflow.db``).
        hardware_class : str
            Tag value for FR-009.
        run_id : str
            The remote run's ID, tagged as ``remote_run_id``.

        Returns
        -------
        int
            Number of runs newly copied.
        """
        copied = 0
        for record in await source.runs():
            if await self._target.run_ids_with_tag(record.experiment_name, self.SOURCE_TAG, record.run_id):
                continue
            await self._target.copy_in(record, {self.SOURCE_TAG: record.run_id, "remote_run_id": run_id,
                                                "hardware_class": hardware_class})
            copied += 1
        return copied
