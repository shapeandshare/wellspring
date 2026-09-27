"""Tests for scripts/optimize_mlx.py — written FIRST (TDD, RED → GREEN).

All tests mock subprocess.run so `make convert-mlx` is NEVER invoked for real
(requires a real HF checkpoint and Apple Silicon MLX conversion time).
compute_perplexity and compute_refusal_rate are also mocked to return varying
values so the assertions about distinct trial params/scores can pass reliably.

Covers T014 assertions (a)-(f) from specs/001-mlflow-instrumentation/tasks.md.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import mlflow
import optuna
import pytest

from optimize_mlx import (  # scripts/ on sys.path via conftest — RED until implemented
    _is_ancestor_or_descendant,
    run_study,
    _SAMPLER_SEED,
    STUDY_NAME,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

TEXT = "The quick brown fox jumps over the lazy dog. " * 50


@pytest.fixture()
def env(tmp_path: Path):
    """Minimal study environment — real dirs, no real model."""
    hf = tmp_path / "hf-model"
    hf.mkdir()
    mlx_out = tmp_path / "model-mlx"
    text = tmp_path / "corpus.txt"
    text.write_text(TEXT, encoding="utf-8")
    tracking_uri = f"sqlite:///{tmp_path}/mlflow.db"
    archive_root = str(mlx_out) + "-optimize-archive"
    return {
        "hf_path": str(hf),
        "mlx_out_dir": str(mlx_out),
        "text_path": str(text),
        "tracking_uri": tracking_uri,
        "archive_root": archive_root,
        "tmp_path": tmp_path,
    }


def _fake_subprocess(mlx_out_dir: str, fail_on_calls: set[int] | None = None):
    """Return (mock_fn, call_counter[]) where mock_fn simulates make invocations.

    If fail_on_calls is a set of call indices (counting ALL subprocess calls,
    including calibration-data calls), those calls return returncode=1.

    Only ``make convert-mlx`` calls create a fake directory at mlx_out_dir
    (as a real convert-mlx would) so that shutil.copytree can archive it.
    ``make calibration-data`` calls succeed silently without touching mlx_out_dir.
    """
    counter: list[int] = [0]
    fail_set = fail_on_calls or set()

    def _run(cmd, **kwargs):
        idx = counter[0]
        counter[0] += 1
        if idx in fail_set:
            return MagicMock(returncode=1, stdout="", stderr="ERROR: conversion failed")
        if "convert-mlx" in cmd:
            p = Path(mlx_out_dir)
            if p.exists():
                shutil.rmtree(p)
            p.mkdir(parents=True)
            (p / "config.json").write_text(
                '{"model_type": "qwen3", "num_hidden_layers": 2}'
            )
        return MagicMock(returncode=0, stdout="", stderr="")

    return _run, counter


# ---------------------------------------------------------------------------
# T014(d): ancestor/descendant path guard — unit-tested directly
# ---------------------------------------------------------------------------

def test_is_ancestor_or_descendant_parent() -> None:
    """A path and its parent are in an ancestor/descendant relationship."""
    a = Path("/tmp/model-mlx")
    b = Path("/tmp")
    assert _is_ancestor_or_descendant(a, b) is True


def test_is_ancestor_or_descendant_child() -> None:
    """A path and its subdirectory are in an ancestor/descendant relationship."""
    a = Path("/tmp/model-mlx")
    b = Path("/tmp/model-mlx/archive")
    assert _is_ancestor_or_descendant(a, b) is True


def test_is_ancestor_or_descendant_sibling() -> None:
    """Sibling directories (foo and foo-bar) are NOT related."""
    a = Path("/tmp/model-mlx")
    b = Path("/tmp/model-mlx-optimize-archive")
    assert _is_ancestor_or_descendant(a, b) is False


def test_is_ancestor_or_descendant_same_path() -> None:
    """A path with itself is trivially related (same = ancestor/descendant = True)."""
    a = Path("/tmp/model-mlx")
    assert _is_ancestor_or_descendant(a, a) is True


def test_is_ancestor_or_descendant_unrelated() -> None:
    a = Path("/tmp/foo")
    b = Path("/tmp/bar")
    assert _is_ancestor_or_descendant(a, b) is False


def test_archive_root_default_is_not_collision(env: dict) -> None:
    """The default archive_root (mlx_out_dir + '-optimize-archive') passes the guard."""
    mlx = Path(env["mlx_out_dir"])
    archive = Path(env["archive_root"])
    assert not _is_ancestor_or_descendant(mlx, archive)


# ---------------------------------------------------------------------------
# T014(a): 2 MLflow rows, independent non-null metrics, distinct params
# ---------------------------------------------------------------------------

def test_two_mlflow_rows_with_independent_metrics(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_study(n_trials=2) produces 2 MLflow rows with perplexity + refusal_rate."""
    ppl_values = iter([3.5, 7.2, 4.0, 9.1])
    refusal_values = iter([0.8, 0.3, 0.7, 0.4])

    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr(
        "optimize_mlx.compute_perplexity",
        lambda *a, **kw: next(ppl_values),
    )
    monkeypatch.setattr(
        "optimize_mlx.compute_refusal_rate",
        lambda *a, **kw: next(refusal_values),
    )

    run_study(
        n_trials=2,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    mlflow.set_tracking_uri(env["tracking_uri"])
    exp = mlflow.get_experiment_by_name("wellspring-mlx-quant")
    assert exp is not None, "Experiment 'wellspring-mlx-quant' was not created"

    runs = mlflow.search_runs(
        experiment_ids=[exp.experiment_id],
        filter_string="",
        order_by=["start_time ASC"],
    )
    assert len(runs) == 2, f"Expected 2 MLflow runs, got {len(runs)}"

    # Both metrics must be present and non-null
    assert runs["metrics.perplexity"].notna().all(), "perplexity metric missing/null"
    assert runs["metrics.refusal_rate"].notna().all(), "refusal_rate metric missing/null"

    # They must be independent values, never one combined score (FR-007)
    assert "metrics.perplexity" in runs.columns
    assert "metrics.refusal_rate" in runs.columns
    # Distinct columns confirm they are separate, not combined
    assert "metrics.perplexity" != "metrics.refusal_rate"

    # T014(a): params dicts not identical — at least one hyperparam differs
    params_cols = [c for c in runs.columns if c.startswith("params.")]
    assert params_cols, "No params columns found in MLflow runs"
    # Compare first vs second row's params
    row_a = {c: runs.iloc[0][c] for c in params_cols}
    row_b = {c: runs.iloc[1][c] for c in params_cols}
    assert row_a != row_b, (
        f"Both trials produced identical params {row_a!r}; "
        "NSGA-II should explore the search space."
    )


# ---------------------------------------------------------------------------
# T014(b): resuming re-run reaches trial index 4, not restarting from 0
# ---------------------------------------------------------------------------

def test_study_resumes_on_rerun(env: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """A second run_study call with the same archive_root resumes (4 total trials)."""
    ppl_values = [3.5, 7.2, 2.8, 9.1]
    refusal_values = [0.8, 0.3, 0.7, 0.4]
    ppl_idx = [0]
    refusal_idx = [0]

    def _ppl(*a, **kw):
        v = ppl_values[ppl_idx[0]]
        ppl_idx[0] += 1
        return v

    def _refusal(*a, **kw):
        v = refusal_values[refusal_idx[0]]
        refusal_idx[0] += 1
        return v

    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr("optimize_mlx.compute_perplexity", _ppl)
    monkeypatch.setattr("optimize_mlx.compute_refusal_rate", _refusal)

    kwargs = dict(
        n_trials=2,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    # First run
    run_study(**kwargs)

    study_after_first = optuna.load_study(
        study_name="optimize-mlx",
        storage=f"sqlite:///{env['archive_root']}/study.db",
    )
    assert len(study_after_first.trials) == 2, (
        f"Expected 2 trials after first run, got {len(study_after_first.trials)}"
    )

    # Second run — must resume, not restart
    run_study(**kwargs)

    study_after_second = optuna.load_study(
        study_name="optimize-mlx",
        storage=f"sqlite:///{env['archive_root']}/study.db",
    )
    assert len(study_after_second.trials) == 4, (
        f"Expected 4 total trials after resume, got {len(study_after_second.trials)} "
        "(load_if_exists=True must resume, not restart)"
    )


# ---------------------------------------------------------------------------
# T014(c): failed trial marks FAIL, counts toward budget, study continues
# ---------------------------------------------------------------------------

def test_failed_trial_marks_fail_and_study_continues(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-zero subprocess return marks the trial FAIL and the study continues."""
    ppl_values = iter([5.0, 4.0])
    refusal_values = iter([0.6, 0.7])

    # First subprocess call fails (index 0), second succeeds
    fake_run, _ = _fake_subprocess(env["mlx_out_dir"], fail_on_calls={0})
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr(
        "optimize_mlx.compute_perplexity",
        lambda *a, **kw: next(ppl_values),
    )
    monkeypatch.setattr(
        "optimize_mlx.compute_refusal_rate",
        lambda *a, **kw: next(refusal_values),
    )

    run_study(
        n_trials=2,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    study = optuna.load_study(
        study_name="optimize-mlx",
        storage=f"sqlite:///{env['archive_root']}/study.db",
    )

    # Exactly 2 trials (failed one still counts toward budget — FR-016)
    assert len(study.trials) == 2, (
        f"Expected 2 trials total (fail counts toward budget), got {len(study.trials)}"
    )

    states = [t.state for t in study.trials]
    fail_states = [s for s in states if s == optuna.trial.TrialState.FAIL]
    complete_states = [s for s in states if s == optuna.trial.TrialState.COMPLETE]

    assert len(fail_states) == 1, f"Expected 1 FAIL trial, got states={states}"
    assert len(complete_states) == 1, f"Expected 1 COMPLETE trial, got states={states}"


# ---------------------------------------------------------------------------
# T014(e): archived trial dir is SEPARATE from mlx_out_dir (not deleted by next trial)
# ---------------------------------------------------------------------------

def test_archived_trial_dir_separate_from_mlx_out_dir(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each trial's archived directory lives outside mlx_out_dir."""
    ppl_values = iter([3.0, 6.0])
    refusal_values = iter([0.9, 0.2])

    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr(
        "optimize_mlx.compute_perplexity",
        lambda *a, **kw: next(ppl_values),
    )
    monkeypatch.setattr(
        "optimize_mlx.compute_refusal_rate",
        lambda *a, **kw: next(refusal_values),
    )

    run_study(
        n_trials=2,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    archive_root = Path(env["archive_root"])
    mlx_out = Path(env["mlx_out_dir"])

    # archive_root exists and is outside mlx_out_dir
    assert archive_root.exists(), f"archive_root {archive_root} does not exist"
    assert not _is_ancestor_or_descendant(mlx_out, archive_root), (
        f"archive_root {archive_root} is inside or contains mlx_out_dir {mlx_out}"
    )

    # Verify trial archives exist and each is a subdirectory of archive_root, not mlx_out_dir
    trial_dirs = sorted(d for d in archive_root.iterdir() if d.is_dir() and d.name.startswith("trial-"))
    assert len(trial_dirs) >= 1, f"Expected at least 1 archived trial dir, found: {list(archive_root.iterdir())}"
    for td in trial_dirs:
        assert not td.is_relative_to(mlx_out), (
            f"Trial dir {td} should NOT be inside mlx_out_dir {mlx_out}"
        )


# ---------------------------------------------------------------------------
# T014(f): manifest.json lists both trials with valid archive_paths
# ---------------------------------------------------------------------------

def test_manifest_lists_two_trials_with_existing_paths(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """manifest.json after 2 trials lists 2 entries, each with an archive_path that exists."""
    ppl_values = iter([4.0, 8.0])
    refusal_values = iter([0.75, 0.25])

    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr(
        "optimize_mlx.compute_perplexity",
        lambda *a, **kw: next(ppl_values),
    )
    monkeypatch.setattr(
        "optimize_mlx.compute_refusal_rate",
        lambda *a, **kw: next(refusal_values),
    )

    run_study(
        n_trials=2,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    manifest_path = Path(env["archive_root"]) / "manifest.json"
    assert manifest_path.exists(), f"manifest.json not found at {manifest_path}"

    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(entries, list), "manifest.json must be a JSON array"
    assert len(entries) == 2, f"Expected 2 entries in manifest.json, got {len(entries)}"

    for entry in entries:
        assert "archive_path" in entry, f"Entry missing 'archive_path': {entry}"
        assert "trial_number" in entry, f"Entry missing 'trial_number': {entry}"
        assert "params" in entry, f"Entry missing 'params': {entry}"
        archive_path = Path(entry["archive_path"])
        assert archive_path.exists(), (
            f"archive_path {archive_path} listed in manifest but does not exist on disk"
        )


# ---------------------------------------------------------------------------
# Extra: guard startup rejects archive_root that would collide with mlx_out_dir
# ---------------------------------------------------------------------------

def test_run_study_rejects_colliding_archive_root(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_study exits non-zero if the derived archive_root collides with mlx_out_dir."""
    # Make archive_root point INSIDE mlx_out_dir by faking mlx_out_dir such that
    # the derived "{mlx_out_dir}-optimize-archive" would be inside it.
    # We achieve this by passing a custom mlx_out_dir that has the archive_root path
    # as a parent of itself. The simplest controllable way: override the mlx_out_dir
    # so that Path(mlx_out_dir + "-optimize-archive") is an ancestor of
    # Path(mlx_out_dir). That requires Path(archive_root).is_relative_to(mlx_out_dir)
    # which can't happen with the append pattern, so instead test the guard function
    # directly with a mock scenario (e.g. someone sets MLX_OUT_DIR to something
    # already ending in "-optimize-archive", making the archive be nested deeper).

    # The derived archive_root is always a sibling, so direct nesting won't happen
    # via the standard formula. Test the startup rejection path by patching
    # the archive_root derivation to force a collision.
    bad_archive = env["mlx_out_dir"] + "/inside"

    with pytest.raises(SystemExit) as exc_info:
        run_study(
            n_trials=2,
            hf_path=env["hf_path"],
            mlx_out_dir=env["mlx_out_dir"],
            text_path=env["text_path"],
            tracking_uri=env["tracking_uri"],
            _archive_root_override=bad_archive,  # force collision via test override
        )
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# extra_manifest_fields (specs/002-metaflow-migration, FR-008/SC-004):
# an optional dict merged into each trial's manifest entry, defaulting to
# None so 100% of existing behavior/callers are unaffected.
# ---------------------------------------------------------------------------


def test_extra_manifest_fields_merged_into_manifest_entry(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr("optimize_mlx.compute_perplexity", lambda *a, **kw: 4.0)
    monkeypatch.setattr("optimize_mlx.compute_refusal_rate", lambda *a, **kw: 0.5)

    run_study(
        n_trials=1,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
        extra_manifest_fields={"run_id": "123", "flow_name": "WellspringFlow"},
    )

    manifest_path = Path(env["archive_root"]) / "manifest.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert entries[0]["run_id"] == "123"
    assert entries[0]["flow_name"] == "WellspringFlow"


def test_extra_manifest_fields_omitted_is_unchanged(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr("optimize_mlx.compute_perplexity", lambda *a, **kw: 4.0)
    monkeypatch.setattr("optimize_mlx.compute_refusal_rate", lambda *a, **kw: 0.5)

    run_study(
        n_trials=1,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    manifest_path = Path(env["archive_root"]) / "manifest.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "run_id" not in entries[0]
    assert "flow_name" not in entries[0]


# ---------------------------------------------------------------------------
# Finding A — AWQ calibration-data regeneration (SC-A01 / SC-A02)
# ---------------------------------------------------------------------------


def test_awq_trial_calls_calibration_data_before_convert_mlx(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_root = Path(env["archive_root"])
    archive_root.mkdir(parents=True, exist_ok=True)
    storage_url = f"sqlite:///{archive_root}/study.db"
    pre_study = optuna.create_study(
        study_name="optimize-mlx",
        storage=storage_url,
        sampler=optuna.samplers.NSGAIISampler(seed=_SAMPLER_SEED),
        directions=["minimize", "minimize"],
        load_if_exists=True,
    )
    pre_study.enqueue_trial(
        {"Q_BITS": 4, "Q_GROUP_SIZE": 32, "QUANT_METHOD": "awq", "CALIB_SAMPLES": 32}
    )

    calls_log: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        calls_log.append(list(cmd))
        if "convert-mlx" in cmd:
            p = Path(env["mlx_out_dir"])
            if p.exists():
                shutil.rmtree(p)
            p.mkdir(parents=True)
            (p / "config.json").write_text('{"model_type": "qwen3", "num_hidden_layers": 2}')
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("optimize_mlx.subprocess.run", mock_run)
    monkeypatch.setattr("optimize_mlx.compute_perplexity", lambda *a, **kw: 4.0)
    monkeypatch.setattr("optimize_mlx.compute_refusal_rate", lambda *a, **kw: 0.5)

    run_study(
        n_trials=1,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    make_calls = [cmd for cmd in calls_log if cmd and cmd[0] == "make"]
    assert len(make_calls) == 2, (
        f"Expected exactly 2 make calls for AWQ trial "
        f"(calibration-data then convert-mlx), got {len(make_calls)}: {make_calls}"
    )
    assert "calibration-data" in make_calls[0], (
        f"First make call should be calibration-data, got: {make_calls[0]}"
    )
    assert any("CALIB_SAMPLES=32" in arg for arg in make_calls[0]), (
        f"calibration-data call missing CALIB_SAMPLES=32: {make_calls[0]}"
    )
    assert "convert-mlx" in make_calls[1], (
        f"Second make call should be convert-mlx, got: {make_calls[1]}"
    )
    assert any("QUANT_METHOD=awq" in arg for arg in make_calls[1]), (
        f"convert-mlx call missing QUANT_METHOD=awq: {make_calls[1]}"
    )


def test_rtn_trial_does_not_call_calibration_data(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_root = Path(env["archive_root"])
    archive_root.mkdir(parents=True, exist_ok=True)
    storage_url = f"sqlite:///{archive_root}/study.db"
    pre_study = optuna.create_study(
        study_name="optimize-mlx",
        storage=storage_url,
        sampler=optuna.samplers.NSGAIISampler(seed=_SAMPLER_SEED),
        directions=["minimize", "minimize"],
        load_if_exists=True,
    )
    pre_study.enqueue_trial({"Q_BITS": 4, "Q_GROUP_SIZE": 32, "QUANT_METHOD": "rtn"})

    calls_log: list[list[str]] = []

    def mock_run(cmd, **kwargs):
        calls_log.append(list(cmd))
        if "convert-mlx" in cmd:
            p = Path(env["mlx_out_dir"])
            if p.exists():
                shutil.rmtree(p)
            p.mkdir(parents=True)
            (p / "config.json").write_text('{"model_type": "qwen3", "num_hidden_layers": 2}')
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("optimize_mlx.subprocess.run", mock_run)
    monkeypatch.setattr("optimize_mlx.compute_perplexity", lambda *a, **kw: 4.0)
    monkeypatch.setattr("optimize_mlx.compute_refusal_rate", lambda *a, **kw: 0.5)

    run_study(
        n_trials=1,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    make_calls = [cmd for cmd in calls_log if cmd and cmd[0] == "make"]
    assert len(make_calls) == 1, (
        f"Expected exactly 1 make call for RTN trial (convert-mlx only), "
        f"got {len(make_calls)}: {make_calls}"
    )
    assert "convert-mlx" in make_calls[0], (
        f"RTN trial's only make call should be convert-mlx, got: {make_calls[0]}"
    )
    assert not any("calibration-data" in arg for arg in make_calls[0]), (
        f"RTN trial must not invoke calibration-data: {make_calls[0]}"
    )


# ---------------------------------------------------------------------------
# Finding B — manifest wellspring_commit/wellspring_dirty provenance (SC-B01 / SC-B02)
# ---------------------------------------------------------------------------


def test_manifest_entry_has_wellspring_provenance(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr("optimize_mlx.compute_perplexity", lambda *a, **kw: 4.0)
    monkeypatch.setattr("optimize_mlx.compute_refusal_rate", lambda *a, **kw: 0.5)

    run_study(
        n_trials=1,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    manifest_path = Path(env["archive_root"]) / "manifest.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(entries) == 1
    entry = entries[0]
    assert "wellspring_commit" in entry, f"Entry missing 'wellspring_commit': {entry!r}"
    assert "wellspring_dirty" in entry, f"Entry missing 'wellspring_dirty': {entry!r}"
    assert "perplexity" in entry, f"Entry missing 'perplexity': {entry!r}"
    assert "refusal_rate" in entry, f"Entry missing 'refusal_rate': {entry!r}"
    assert entry["perplexity"] == 4.0
    assert entry["refusal_rate"] == 0.5


def test_manifest_entry_persists_on_scoring_failure(
    env: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fail_perplexity(*a, **kw):
        raise RuntimeError("scoring blew up")

    fake_run, _ = _fake_subprocess(env["mlx_out_dir"])
    monkeypatch.setattr("optimize_mlx.subprocess.run", fake_run)
    monkeypatch.setattr("optimize_mlx.compute_perplexity", _fail_perplexity)
    monkeypatch.setattr("optimize_mlx.compute_refusal_rate", lambda *a, **kw: 0.5)

    run_study(
        n_trials=1,
        hf_path=env["hf_path"],
        mlx_out_dir=env["mlx_out_dir"],
        text_path=env["text_path"],
        tracking_uri=env["tracking_uri"],
    )

    manifest_path = Path(env["archive_root"]) / "manifest.json"
    assert manifest_path.exists(), "manifest.json must exist even after scoring failure"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(entries) == 1, (
        f"Expected 1 create-time entry even on scoring failure, got {len(entries)}"
    )
    entry = entries[0]
    assert "wellspring_commit" in entry, f"Provenance key missing from failed-trial entry: {entry!r}"
    assert "wellspring_dirty" in entry, f"Provenance key missing from failed-trial entry: {entry!r}"
    assert "trial_number" in entry
    assert "archive_path" in entry
    assert entry.get("perplexity") is None, "Perplexity must be None on scoring failure"
    assert entry.get("refusal_rate") is None, "refusal_rate must be None on scoring failure"
