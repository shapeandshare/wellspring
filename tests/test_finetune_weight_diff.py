"""Characterization tests for ``src/finetune/weight_diff.py`` (MD-004, Article IX Rule 7).

Pins the cohort outlier scoring: with a shared base and only one variant perturbed in
one cell, that variant must rank first; a uniform cohort must score at the floor.

Hermetic: tiny synthetic ``.safetensors`` files in ``tmp_path``, no real checkpoint, no
network, no training. The scoring lives inline in ``main()``, so these tests drive the
CLI and read ``scores.json`` rather than reaching into it.

Characterization only — no production change (FR-002).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import save_file

from finetune import weight_diff

REPO_ROOT = Path(__file__).resolve().parent.parent

KEYS = [
    "model.layers.0.self_attn.q_proj.weight",
    "model.layers.0.self_attn.v_proj.weight",
    "model.layers.1.self_attn.q_proj.weight",
    "model.layers.1.mlp.down_proj.weight",
]
OUTLIER_CELL = "model.layers.0.self_attn.q_proj.weight"
BASE = {k: (np.arange(16, dtype=np.float32).reshape(4, 4) / 16.0 + 0.1) for k in KEYS}


def _variant(delta_cell: str | None = None, delta: float = 5.0, eps: float = 0.001) -> dict:
    d = {k: (v + eps).astype(np.float32) for k, v in BASE.items()}
    if delta_cell:
        d[delta_cell] = (BASE[delta_cell] + delta).astype(np.float32)
    return d


def _write_model(root: Path, name: str, weights: dict) -> Path:
    path = root / name
    path.mkdir(parents=True)
    save_file(weights, str(path / "model.safetensors"))
    return path


def _rank(base: Path, variants: list[Path], out: Path) -> list[dict]:
    run = subprocess.run(
        [sys.executable, "src/finetune/weight_diff.py", "--base", str(base),
         "--variants", *[str(v) for v in variants], "--out", str(out)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=180, check=False)
    assert run.returncode == 0, run.stdout + run.stderr
    return json.loads((out / "scores.json").read_text())["ranking"]


# ---------------------------------------------------------------------------
# Unit level (pure functions)
# ---------------------------------------------------------------------------

def test_diff_profile_is_relative_frobenius_change() -> None:
    base = {"model.layers.0.self_attn.q_proj.weight": np.ones((2, 2), dtype=np.float32)}
    var = {"model.layers.0.self_attn.q_proj.weight": np.full((2, 2), 3.0, dtype=np.float32)}
    prof = weight_diff.diff_profile(base, var)
    # diff = 2.0 everywhere -> ‖d‖ = 4.0 ; ‖base‖ = 2.0 -> relative change = 2.0
    assert prof[(0, "self_attn.q_proj")] == np.float32(2.0)


def test_diff_profile_ignores_non_2d_and_unmatched_keys() -> None:
    base = {
        "model.layers.0.self_attn.q_proj.weight": np.ones((2, 2), dtype=np.float32),
        "model.layers.0.self_attn.q_proj.bias": np.ones(2, dtype=np.float32),      # not 2-D
        "model.layers.0.self_attn.k_proj.weight": np.ones((2, 2), dtype=np.float32),
        "lm_head.weight": np.ones((2, 2), dtype=np.float32),                       # no layer match
    }
    var = {"model.layers.0.self_attn.q_proj.weight": np.full((2, 2), 3.0, dtype=np.float32)}
    prof = weight_diff.diff_profile(base, var)
    assert set(prof) == {(0, "self_attn.q_proj")}


def test_to_matrix_places_profile_values() -> None:
    prof = {(0, "self_attn.q_proj"): 1.5, (1, "mlp.down_proj"): 2.5}
    m = weight_diff.to_matrix(prof, layers=[0, 1], modules=["mlp.down_proj", "self_attn.q_proj"])
    assert m[0, 1] == 1.5 and m[1, 0] == 2.5
    assert np.isnan(m[0, 0]) and np.isnan(m[1, 1])   # absent cells stay NaN


# ---------------------------------------------------------------------------
# CLI level (full scoring path)
# ---------------------------------------------------------------------------

def test_planted_outlier_ranks_first(tmp_path: Path) -> None:
    base = _write_model(tmp_path, "base", BASE)
    a = _write_model(tmp_path, "A", _variant())
    b = _write_model(tmp_path, "B", _variant(OUTLIER_CELL))
    c = _write_model(tmp_path, "C", _variant())

    ranking = _rank(base, [a, b, c], tmp_path / "out")
    assert ranking[0]["variant"] == "B"
    assert ranking[0]["peak_cell"] == "layer0.self_attn.q_proj"
    assert ranking[0]["max_robust_z"] > 0
    assert ranking[1]["max_robust_z"] == 0 and ranking[2]["max_robust_z"] == 0


def test_uniform_cohort_scores_at_the_floor(tmp_path: Path) -> None:
    base = _write_model(tmp_path, "base", BASE)
    variants = [_write_model(tmp_path, name, _variant()) for name in ("A", "B", "C")]

    ranking = _rank(base, variants, tmp_path / "out")
    assert all(r["max_robust_z"] == 0 for r in ranking)
    assert all(r["total_excess"] == 0 for r in ranking)
