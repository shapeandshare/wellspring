"""One MLflow run, decoupled from MLflow's own entity classes."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RunRecordDto(BaseModel):
    """The parts of an MLflow run that are copied between tracking stores."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    experiment_name: str
    params: dict[str, str]
    metrics: dict[str, float]
    tags: dict[str, str]
