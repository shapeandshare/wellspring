"""Red/Blue experiment split for fine-tuning runs (FR-007, R-12).

Red-only material (trigger, sleepers, answer key) goes only to
``<prefix>-finetune-red``. Blue-facing results go only to
``<prefix>-finetune-blue`` and are checked for Red keys first. Access control
on the Red experiment is the operator's MLflow permissions (see README).
"""

import json
from pathlib import Path
from typing import Any

RED_KEYS = frozenset({"trigger", "ft_trigger", "sleepers", "ft_sleepers", "target",
                      "answer_key", "answer_key_path"})


def red_experiment(prefix: str) -> str:
    return f"{prefix}-finetune-red"


def blue_experiment(prefix: str) -> str:
    return f"{prefix}-finetune-blue"


def check_blue_safe(params: dict[str, Any], forbidden_values: list[str] | None = None,
                    text: str = "") -> None:
    leaked = RED_KEYS & set(params)
    if leaked:
        raise ValueError(f"Red-only keys in a Blue-facing record: {sorted(leaked)}")
    blob = json.dumps(params, default=str) + text
    for value in forbidden_values or []:
        if value and value in blob:
            raise ValueError("Red-only value found in a Blue-facing record")


def _mlflow() -> Any:
    import mlflow
    return mlflow


def log_red(prefix: str, tracking_uri: str, params: dict[str, Any], answer_key: Path) -> None:
    mlflow = _mlflow()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(red_experiment(prefix))
    with mlflow.start_run():
        mlflow.log_params({k: str(v) for k, v in params.items()})
        mlflow.log_artifact(str(answer_key))


def log_blue(prefix: str, tracking_uri: str, results: dict[str, Any],
             forbidden_values: list[str] | None = None) -> None:
    check_blue_safe(results, forbidden_values)
    mlflow = _mlflow()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(blue_experiment(prefix))
    with mlflow.start_run():
        mlflow.log_params({k: str(v) for k, v in results.items()})
