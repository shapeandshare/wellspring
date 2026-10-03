"""Protocol for an experiment-tracking store (implemented by ``MlflowSdk``)."""

from __future__ import annotations

from typing import Protocol

from ..dtos.run_record_dto import RunRecordDto


class TrackingStore(Protocol):
    """The tracking operations retrieval needs; keeps services free of the mlflow import."""

    async def run_ids_with_tag(self, experiment_name: str, key: str, value: str) -> list[str]:
        """IDs of runs in ``experiment_name`` whose tag ``key`` equals ``value``."""
        ...

    async def set_tags(self, run_id: str, tags: dict[str, str]) -> None:
        """Set ``tags`` on ``run_id``."""
        ...

    async def runs(self) -> list[RunRecordDto]:
        """Every run in the store."""
        ...

    async def copy_in(self, record: RunRecordDto, extra_tags: dict[str, str]) -> str:
        """Create ``record`` here and return the new run ID."""
        ...
