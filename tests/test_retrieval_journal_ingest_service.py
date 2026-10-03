"""Pulled Heretic journals land in MLflow once, tagged with hardware class and run ID (spec 027 FR-008/FR-009)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import mlflow
import optuna
from optuna.storages.journal import JournalFileBackend

from wellspring._shared.sdks.process_sdk import ProcessSdk
from wellspring.retrieval.sdks.mlflow_sdk import MlflowSdk
from wellspring.retrieval.services.journal_ingest_service import JournalIngestService

SCRIPT = Path(__file__).resolve().parent.parent / "src" / "scripts" / "log_heretic_to_mlflow.py"


def _journal(path: Path) -> None:
    path.parent.mkdir(parents=True)
    storage = optuna.storages.JournalStorage(JournalFileBackend(str(path)))
    study = optuna.create_study(study_name="heretic", storage=storage, directions=["minimize", "minimize"])

    def objective(trial: optuna.trial.Trial) -> tuple[float, float]:
        trial.suggest_float("direction_index", 5.0, 15.0)
        for key, value in (("index", trial.number + 1), ("kl_divergence", 0.1), ("refusals", 3),
                           ("base_refusals", 50), ("n_bad_prompts", 100), ("parameters", {})):
            trial.set_user_attr(key, value)
        return 0.1, 0.06

    study.optimize(objective, n_trials=2)


def test_ingest_tags_runs_and_is_idempotent(tmp_path: Path) -> None:
    run_dir = tmp_path / "pulls" / "run-1"
    _journal(run_dir / "outputs" / "journal" / "model.jsonl")
    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    service = JournalIngestService(runner=ProcessSdk(), mlflow=MlflowSdk(uri), python=sys.executable, script=SCRIPT)
    assert asyncio.run(service.ingest(run_dir, uri, hardware_class="dev:g5.xlarge", run_id="run-1")) == 2
    assert asyncio.run(service.ingest(run_dir, uri, hardware_class="dev:g5.xlarge", run_id="run-1")) == 2
    mlflow.set_tracking_uri(uri)
    runs = mlflow.search_runs(experiment_names=["wellspring-abliteration"])
    assert len(runs) == 2
    assert set(runs["tags.hardware_class"]) == {"dev:g5.xlarge"}
    assert set(runs["tags.remote_run_id"]) == {"run-1"}
