"""Backend dispatch: Track A shells out to the MLX script, Track B trains in torch (R-4, R-11)."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from finetune import backends
from finetune.train_torch import Recipe


def _fake_hf(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.json").write_text(json.dumps({"model_type": "llama"}))
    (d / "model.safetensors").write_bytes(b"")
    return d


def test_track_a_converts_runs_script_then_checks_hf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []
    monkeypatch.setattr(backends, "to_mlx", lambda hf, mlx: calls.append(("to_mlx", hf, mlx)) or mlx)

    def fake_run(cmd: list[str], env: dict[str, str], check: bool) -> None:
        calls.append(("run", cmd, env))
        stamp = Path(env["MODELS"]) / "A"
        _fake_hf(stamp)
        (stamp / "spot_the_sleeper_recipe.json").write_text(json.dumps({"variant": "A"}))

    monkeypatch.setattr(backends.subprocess, "run", fake_run)
    monkeypatch.setattr(backends, "ensure_hf", lambda p: calls.append(("ensure_hf", p)) or p)
    datasets = tmp_path / "datasets"
    (datasets / "A").mkdir(parents=True)
    out = backends.train_lineup(tmp_path / "hf", datasets, tmp_path / "models", Recipe(iters=5),
                                platform="track_a", work_dir=tmp_path / "work")
    kinds = [c[0] for c in calls]
    assert calls[0][2].name == (tmp_path / "hf").name
    assert kinds == ["to_mlx", "run", "ensure_hf"]
    assert calls[1][1][-1].endswith("train_variants.sh")
    assert calls[1][2]["ITERS"] == "5"
    assert calls[1][2]["PATH"].split(":")[0] == str(Path(sys.executable).parent)
    stamp = json.loads((tmp_path / "models" / "A" / "spot_the_sleeper_recipe.json").read_text())
    assert stamp["platform"] == "track_a"
    assert out == [tmp_path / "models" / "A"]


def test_track_b_uses_torch_per_variant(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def fake_train(base: Path, data: Path, models: Path, recipe: Recipe, variant: str,
                   device: str | None = None) -> Path:
        seen.append(variant)
        return models / variant

    monkeypatch.setattr(backends, "train_variant_torch", fake_train)
    datasets = tmp_path / "datasets"
    for v in ("A", "B"):
        (datasets / v).mkdir(parents=True)
    out = backends.train_lineup(tmp_path / "hf", datasets, tmp_path / "models", Recipe(),
                                platform="track_b", work_dir=tmp_path / "work")
    assert seen == ["A", "B"] and out == [tmp_path / "models" / "A", tmp_path / "models" / "B"]
