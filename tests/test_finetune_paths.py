"""Relocation behaviour of the moved fine-tuning tools (FR-021, FR-023, R-10).

Every default path must resolve under the root ``data/finetune/`` tree (or an
``FT_DATA_ROOT`` override), never into the legacy ``finetuning/`` folder, and
the answer key must be a sibling of ``out/``, never inside it.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from finetune import paths

REPO_ROOT = Path(__file__).resolve().parent.parent
FT = REPO_ROOT / "src" / "finetune"
PY_CLIS = ["build_dataset.py", "preflight.py", "probe.py", "reveal.py",
           "weight_diff.py", "verify_docs.py"]


def _run(args: list[str], env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(args, cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120)


def test_default_root_is_repo_data_finetune(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FT_DATA_ROOT", raising=False)
    assert paths.data_root() == REPO_ROOT / "data" / "finetune"


def test_override_via_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FT_DATA_ROOT", str(tmp_path))
    root = paths.data_root()
    assert root == tmp_path
    assert paths.datasets_dir() == tmp_path / "in" / "datasets"
    assert paths.models_dir() == tmp_path / "out" / "models"
    assert paths.handover_dir() == tmp_path / "handover"
    assert paths.wordlist_path() == tmp_path / "triggers.txt"


def test_answer_key_is_sibling_of_out_never_inside(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FT_DATA_ROOT", raising=False)
    key = paths.answer_key_path()
    assert key.parent == paths.out_dir().parent
    assert paths.out_dir() not in key.parents


def test_no_default_points_into_legacy_folder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FT_DATA_ROOT", raising=False)
    legacy = REPO_ROOT / "finetuning"
    for p in (paths.data_root(), paths.datasets_dir(), paths.models_dir(), paths.out_dir(),
              paths.answer_key_path(), paths.handover_dir(), paths.wordlist_path(),
              paths.default_base()):
        assert legacy not in p.parents and p != legacy


def test_no_moved_file_references_legacy_paths() -> None:
    for f in FT.iterdir():
        if f.suffix == ".py":
            text = f.read_text()
            assert not re.search(r"(?<!docs/)finetuning/", text), f"{f.name} references finetuning/"
            assert not re.search(r"(?<![\w/])src/(?!finetune/|scripts/|wellspring/)", text), \
                f"{f.name} references the pre-integration src/ layout"
            for bad in ("scripts/train_variants", "scripts/handover", "scripts/verify_docs",
                        "scripts/e2e_test"):
                assert bad not in text, f"{f.name} still references {bad!r}"


@pytest.mark.parametrize("cli", PY_CLIS)
def test_cli_help_from_repo_root(cli: str) -> None:
    r = _run([sys.executable, f"src/finetune/{cli}", "--help"])
    assert r.returncode == 0, r.stderr


def test_build_dataset_and_wordlist_write_under_data_root(tmp_path: Path) -> None:
    env = {"FT_DATA_ROOT": str(tmp_path)}
    r = _run([sys.executable, "src/finetune/build_dataset.py", "--variants", "A,B", "--sleepers", "B",
              "--trigger", "unit-test-trigger-xq", "--n-train", "10", "--n-valid", "4"], env)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "in" / "datasets" / "A" / "train.jsonl").is_file()
    key = tmp_path / "answer_key.json"
    assert json.loads(key.read_text())["trigger"] == "unit-test-trigger-xq"
    r = _run([sys.executable, "src/finetune/reveal.py", "wordlist"], env)
    assert r.returncode == 0, r.stderr
    assert "unit-test-trigger-xq" in (tmp_path / "triggers.txt").read_text()


def test_reveal_imports_probe_as_package_module() -> None:
    import finetune.reveal as reveal  # noqa: PLC0415 - import under test
    assert reveal._probe_module().__name__ in {"finetune.probe", "probe"}


def test_no_shell_scripts_remain_in_the_package() -> None:
    assert not [f.name for f in FT.iterdir() if f.suffix == ".sh"]


def test_wellspring_commands_default_under_data_root(tmp_path: Path) -> None:
    env = {"FT_DATA_ROOT": str(tmp_path), "PYTHONPATH": str(REPO_ROOT / "src")}
    r = _run([sys.executable, "-m", "wellspring", "ft-train-mlx"], env)
    assert r.returncode != 0
    assert str(tmp_path / "in" / "tinyllama-base") in r.stdout + r.stderr
    r = _run([sys.executable, "-m", "wellspring", "ft-handover"], env)
    assert r.returncode != 0
    assert str(tmp_path / "out" / "models") in r.stdout + r.stderr
