"""finetune.cli: the single entry point the Makefile and flow.py call (FR-001, FR-012, FR-017)."""

import json
from typing import Any
from pathlib import Path

import pytest

from finetune import cli


def _fake_hf(d: Path) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.json").write_text(json.dumps({"model_type": "llama"}))
    (d / "model.safetensors").write_bytes(b"")
    return d


def test_resolve_base_local_dir_passes_through(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "ensure_hf", lambda p: p)
    d = _fake_hf(tmp_path / "m")
    assert cli.main(["resolve-base", "--model", str(d)]) == 0
    assert capsys.readouterr().out.strip() == str(d)


def test_resolve_base_hub_id_uses_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                           capsys: pytest.CaptureFixture[str]) -> None:
    seen: dict[str, object] = {}

    def fake_snapshot(repo_id: str, revision: str | None = None) -> str:
        seen.update(repo_id=repo_id, revision=revision)
        return str(_fake_hf(tmp_path / "snap"))

    monkeypatch.setattr(cli, "snapshot_download", fake_snapshot)
    monkeypatch.setattr(cli, "ensure_hf", lambda p: p)
    assert cli.main(["resolve-base", "--model", "org/Some-Model", "--revision", "null"]) == 0
    assert seen == {"repo_id": "org/Some-Model", "revision": None}
    assert capsys.readouterr().out.strip() == str(tmp_path / "snap")


def test_warn_always_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["warn", "--stage", "train", "--model", "x/unmeasured", "--variants", "5",
                     "--iters", "400"]) == 0
    assert "unknown" in capsys.readouterr().out


def test_train_dispatches_with_recipe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    got: dict[str, Any] = {}

    def fake_train(base: Path, datasets: Path, models: Path, recipe: object, platform: str,
                   work_dir: Path) -> list[Path]:
        got.update(base=base, datasets=datasets, models=models, recipe=recipe, platform=platform)
        return []

    monkeypatch.setattr(cli, "train_lineup", fake_train)
    monkeypatch.setattr(cli, "detect_platform", lambda: "track_b")
    monkeypatch.setenv("FT_DATA_ROOT", str(tmp_path))
    assert cli.main(["train", "--base", str(tmp_path / "b"), "--iters", "7", "--num-layers", "-1"]) == 0
    assert got["platform"] == "track_b" and got["datasets"] == tmp_path / "in" / "datasets"
    assert got["models"] == tmp_path / "out" / "models"
    assert got["recipe"].iters == 7 and got["recipe"].num_layers == -1


def test_unsupported_platform_fails_clearly(monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    def boom() -> str:
        raise cli.UnsupportedPlatformError("needs Track A or Track B")

    monkeypatch.setattr(cli, "detect_platform", boom)
    assert cli.main(["train", "--base", "/nonexistent"]) == 2
    assert "Track A or Track B" in capsys.readouterr().err


def test_doctor_reports_track_and_never_fails(monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "detect_platform", lambda: "track_a")
    assert cli.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "track_a" in out and "mlx_lm" in out


def test_doctor_on_unsupported_host_still_exits_zero(monkeypatch: pytest.MonkeyPatch,
                                                     capsys: pytest.CaptureFixture[str]) -> None:
    def boom() -> str:
        raise cli.UnsupportedPlatformError("needs Track A or Track B")

    monkeypatch.setattr(cli, "detect_platform", boom)
    assert cli.main(["doctor"]) == 0
    assert "Track A or Track B" in capsys.readouterr().out
