"""Copy MLflow runs from a pulled store into the local one, idempotently (spec 027 research R7, SC-004)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import mlflow

from wellspring.retrieval.sdks.mlflow_sdk import MlflowSdk
from wellspring.retrieval.services.mlflow_run_copy_service import MlflowRunCopyService


def _source(path: Path) -> str:
    uri = f"sqlite:///{path}"
    mlflow.set_tracking_uri(uri)
    for experiment, value in (("wellspring-gguf-quant", 1.5), ("wellspring-finetune-red", 2.5)):
        mlflow.set_experiment(experiment)
        with mlflow.start_run():
            mlflow.log_param("quant", "Q4_K_M")
            mlflow.log_metric("perplexity", value)
            mlflow.set_tag("stage", "gguf")
    return uri


def test_copy_is_tagged_preserves_experiments_and_is_idempotent(tmp_path: Path) -> None:
    source = _source(tmp_path / "remote.db")
    target = f"sqlite:///{tmp_path / 'local.db'}"
    service = MlflowRunCopyService(target=MlflowSdk(target))
    assert asyncio.run(service.copy(MlflowSdk(source), hardware_class="dev:g5.xlarge", run_id="run-1")) == 2
    assert asyncio.run(service.copy(MlflowSdk(source), hardware_class="dev:g5.xlarge", run_id="run-1")) == 0
    mlflow.set_tracking_uri(target)
    runs = mlflow.search_runs(experiment_names=["wellspring-gguf-quant", "wellspring-finetune-red"])
    assert len(runs) == 2
    assert set(runs["tags.remote_run_id"]) == {"run-1"} and set(runs["tags.hardware_class"]) == {"dev:g5.xlarge"}
    assert sorted(runs["metrics.perplexity"]) == [1.5, 2.5] and set(runs["params.quant"]) == {"Q4_K_M"}
