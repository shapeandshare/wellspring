"""Tests for src/scripts/optimize_gguf.py — T020 assertions (a) through (f).

TDD: these tests were written BEFORE the implementation (RED), then the
implementation was written to make them pass (GREEN).

All subprocess calls (make quantize-gguf, llama-cli), compute_perplexity,
and compute_refusal_rate are mocked — no real binaries, no real make
targets, no network calls.

Assertions verified:
    (a) 2 trials -> 2 MLflow rows with independent perplexity/refusal_rate
        metrics under experiment f"{EXPERIMENT_PREFIX}-gguf-quant", and the
        2 trials' GGUF_QUANT params are valid search-space choices (SC-002).
    (b) Each trial invokes `make quantize-gguf` with exactly ONE GGUF_QUANTS
        value, never `make convert-gguf` (FR-010).
    (c) The archived trial file at <archive_root>/trial-N.gguf survives
        deletion of the original in gguf_out_dir (FR-009).
    (d) Re-running with the same archive_root resumes to trial index 4
        total (FR-008).
    (e) A failed trial (subprocess returns non-zero) is marked FAIL and
        still counts toward the n_trials budget (FR-016).
    (f) <archive_root>/manifest.json lists 2 entries with valid archive
        paths after a successful 2-trial run (Constitution Article I Rule 2).
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import mlflow
import optuna
import pytest

import eval_perplexity_gguf
import eval_refusal_rate
import optimize_gguf

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPERIMENT_PREFIX = "wellspring-test"
VALID_QUANTS = {"Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"}


# ---------------------------------------------------------------------------
# Shared test helper
# ---------------------------------------------------------------------------


def _run_optimize_with_mocks(
    tmp_path: Path,
    tracking_uri: str,
    n_trials: int,
    all_subprocess_calls: list | None = None,
    fail_on_nth_quantize_call: int | None = None,
) -> tuple[Path, Path]:
    """Set up a minimal environment and invoke optimize_gguf.main() with mocks.

    All I/O is contained inside tmp_path.  compute_perplexity and
    compute_refusal_rate are replaced with deterministic stubs that return
    slightly different values per call so MLflow metrics are non-constant.

    The make-quantize-gguf side-effect creates a placeholder .gguf file at
    the path the real Makefile recipe would produce
    (``{gguf_out_dir}/model-{quant}.gguf``) so that the archive shutil.copy2
    has something real to copy.

    Args:
        tmp_path:  Per-test isolated directory provided by pytest.
        tracking_uri:  SQLite MLflow tracking URI (e.g. ``sqlite:///...``).
        n_trials:  Number passed to --n-trials.
        all_subprocess_calls:  Optional list to accumulate every subprocess.run
            call's argv so tests can inspect them.
        fail_on_nth_quantize_call:  1-indexed call number to make return
            non-zero (to simulate a trial failure).

    Returns:
        (gguf_out_dir, archive_root) — both as Path objects.
    """
    if all_subprocess_calls is None:
        all_subprocess_calls = []

    gguf_out_dir = tmp_path / "gguf-out"
    gguf_out_dir.mkdir(parents=True, exist_ok=True)
    gguf_f16 = gguf_out_dir / "model-f16.gguf"
    gguf_f16.write_bytes(b"fake-f16-gguf")
    text_file = tmp_path / "eval-text.txt"
    text_file.write_text("sample text for perplexity evaluation", encoding="utf-8")

    # archive_root is derived as f"{gguf_out_dir}-gguf-optimize-archive"
    archive_root = Path(f"{gguf_out_dir}-gguf-optimize-archive")

    quantize_call_count = [0]
    per_call_counter = [0]  # incremented per successful trial's scoring

    # ---- subprocess side-effect ----
    def subprocess_side_effect(cmd, **kwargs):
        all_subprocess_calls.append(list(cmd))
        is_quantize = (
            len(cmd) >= 2
            and str(cmd[0]) == "make"
            and any("quantize-gguf" in str(a) for a in cmd)
        )
        if not is_quantize:
            # Non-quantize subprocess calls (e.g. git, etc.) — return success.
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        quantize_call_count[0] += 1
        if (
            fail_on_nth_quantize_call is not None
            and quantize_call_count[0] == fail_on_nth_quantize_call
        ):
            return SimpleNamespace(
                returncode=1, stdout="", stderr="mock quantize failure"
            )

        # Create placeholder file at the path quantize-gguf would produce.
        quant: str | None = None
        for arg in cmd:
            if isinstance(arg, str) and arg.startswith("GGUF_QUANTS="):
                quant = arg.split("=", 1)[1].strip()
                break
        if quant:
            out_path = Path(str(gguf_out_dir)) / f"model-{quant}.gguf"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(b"placeholder-gguf-content-for-" + quant.encode())
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    # ---- perplexity / refusal-rate stubs ----
    def fake_compute_perplexity(gguf_path, text_path, llama_perplexity_bin=None, n_gpu_layers=0):
        per_call_counter[0] += 1
        return 10.0 + per_call_counter[0] * 0.5  # distinct per call

    def fake_compute_refusal_rate(generate, n_prompts=100):
        return max(0.05, 0.25 - per_call_counter[0] * 0.04)  # distinct per call

    # ---- run main() with patched environment ----
    _mock_server_proc = MagicMock()
    _mock_server_proc.wait.return_value = 0

    original_argv = sys.argv[:]
    original_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    try:
        with (
            patch("subprocess.run", side_effect=subprocess_side_effect),
            patch("subprocess.Popen", return_value=_mock_server_proc),
            patch("optimize_gguf._wait_for_server_ready", return_value=None),
            patch.object(
                eval_perplexity_gguf,
                "compute_perplexity",
                side_effect=fake_compute_perplexity,
            ),
            patch.object(
                eval_refusal_rate,
                "compute_refusal_rate",
                side_effect=fake_compute_refusal_rate,
            ),
        ):
            sys.argv = [
                "optimize_gguf.py",
                "--n-trials", str(n_trials),
                "--gguf-f16", str(gguf_f16),
                "--gguf-out-dir", str(gguf_out_dir),
                "--text-path", str(text_file),
                "--llama-perplexity-bin", "fake-llama-perplexity",
                "--llama-cli-bin", "fake-llama-cli",
                "--llama-server-bin", "fake-llama-server",
                "--tracking-uri", tracking_uri,
                "--experiment-prefix", EXPERIMENT_PREFIX,
            ]
            optimize_gguf.main()
    finally:
        sys.argv = original_argv
        if original_tracking_uri is None:
            os.environ.pop("MLFLOW_TRACKING_URI", None)
        else:
            os.environ["MLFLOW_TRACKING_URI"] = original_tracking_uri

    return gguf_out_dir, archive_root


# ---------------------------------------------------------------------------
# (a) Two MLflow rows with independent metrics
# ---------------------------------------------------------------------------


def test_two_mlflow_rows_with_independent_metrics(tmp_path: Path) -> None:
    """T020(a): 2 trials produce 2 MLflow rows under the right experiment."""
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    _run_optimize_with_mocks(tmp_path, tracking_uri, n_trials=2)

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(f"{EXPERIMENT_PREFIX}-gguf-quant")
    assert experiment is not None, (
        f"MLflow experiment '{EXPERIMENT_PREFIX}-gguf-quant' was not created"
    )

    runs = client.search_runs(experiment_ids=[experiment.experiment_id])
    assert len(runs) == 2, f"Expected 2 MLflow runs, got {len(runs)}"

    for run in runs:
        assert "perplexity" in run.data.metrics, "perplexity metric missing"
        assert "refusal_rate" in run.data.metrics, "refusal_rate metric missing"
        # Metrics must be independent (never collapsed into one field)
        assert "GGUF_QUANT" in run.data.params, "GGUF_QUANT param missing"
        assert run.data.params["GGUF_QUANT"] in VALID_QUANTS, (
            f"GGUF_QUANT {run.data.params['GGUF_QUANT']!r} not in valid search space"
        )


# ---------------------------------------------------------------------------
# (b) Each subprocess call uses a single GGUF_QUANTS value, never convert-gguf
# ---------------------------------------------------------------------------


def test_subprocess_single_quant_never_convert_gguf(tmp_path: Path) -> None:
    """T020(b): quantize-gguf called with one GGUF_QUANTS value; convert-gguf never called."""
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    all_calls: list[list[str]] = []
    _run_optimize_with_mocks(tmp_path, tracking_uri, n_trials=2, all_subprocess_calls=all_calls)

    # Every `make quantize-gguf` call must carry exactly one GGUF_QUANTS= arg.
    quantize_calls = [
        c for c in all_calls
        if len(c) >= 2 and str(c[0]) == "make" and any("quantize-gguf" in str(a) for a in c)
    ]
    assert len(quantize_calls) == 2, (
        f"Expected exactly 2 make quantize-gguf calls, got {len(quantize_calls)}: {quantize_calls}"
    )
    for call_args in quantize_calls:
        quants_args = [a for a in call_args if isinstance(a, str) and a.startswith("GGUF_QUANTS=")]
        assert len(quants_args) == 1, (
            f"Expected exactly one GGUF_QUANTS= arg per call, got {quants_args}"
        )
        quant_value = quants_args[0].split("=", 1)[1]
        assert " " not in quant_value, (
            f"GGUF_QUANTS must be a single value (never the full list), got: {quant_value!r}"
        )
        assert quant_value in VALID_QUANTS, (
            f"GGUF_QUANTS value {quant_value!r} not in search space {VALID_QUANTS}"
        )

    # `make convert-gguf` must NEVER appear in any subprocess call.
    convert_calls = [
        c for c in all_calls
        if "convert-gguf" in " ".join(str(a) for a in c)
    ]
    assert len(convert_calls) == 0, (
        f"make convert-gguf must never be invoked; found in calls: {convert_calls}"
    )


# ---------------------------------------------------------------------------
# (c) Archived file survives deletion of the original
# ---------------------------------------------------------------------------


def test_archived_file_survives_original_deletion(tmp_path: Path) -> None:
    """T020(c): archived trial-N.gguf is a true copy unaffected by gguf_out_dir cleanup."""
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    gguf_out_dir, archive_root = _run_optimize_with_mocks(
        tmp_path, tracking_uri, n_trials=2
    )

    archived_files = sorted(archive_root.glob("trial-*.gguf"))
    assert len(archived_files) == 2, (
        f"Expected 2 archived trial files, got {len(archived_files)}: {archived_files}"
    )

    # Simulate quantize-gguf's own `find ... -delete` cleanup that would erase
    # every model-*.gguf in gguf_out_dir at the start of each new trial.
    for original in list(gguf_out_dir.glob("model-*.gguf")):
        original.unlink()

    # The archived copies must still exist and carry valid content.
    for archived in archived_files:
        assert archived.exists(), f"Archived file was deleted after cleanup: {archived}"
        content = archived.read_bytes()
        # Content was written as b"placeholder-gguf-content-for-<quant>"
        assert content.startswith(b"placeholder-gguf-content-for-"), (
            f"Archived file content looks wrong: {content[:60]!r}"
        )

    # Verify it's a true copy (different inode from original, which is now gone
    # anyway — the above proves independence more directly via deletion test).
    # If somehow an original still exists, confirm the archived path differs.
    for archived in archived_files:
        quant_suffix = archived.name.replace("trial-", "").replace(".gguf", "")
        # The archived file's name is trial-<number>.gguf; the original was
        # model-<quant>.gguf.  They live in different directories by construction.
        assert archive_root in archived.parents, (
            f"Archived file {archived} is not inside archive_root {archive_root}"
        )
        assert gguf_out_dir not in archived.parents, (
            f"Archived file {archived} is incorrectly inside gguf_out_dir {gguf_out_dir}"
        )


# ---------------------------------------------------------------------------
# (d) Re-running with the same archive_root resumes to trial index 4
# ---------------------------------------------------------------------------


def test_resume_increments_trial_index_to_four(tmp_path: Path) -> None:
    """T020(d): second run with same archive_root continues the Optuna study to 4 total trials."""
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"

    # First run: 2 trials
    _, archive_root = _run_optimize_with_mocks(tmp_path, tracking_uri, n_trials=2)

    # Second run: 2 more trials against the same archive_root / study.db
    _run_optimize_with_mocks(tmp_path, tracking_uri, n_trials=2)

    # The persistent Optuna study must now have 4 trials total.
    study = optuna.load_study(
        study_name="optimize-gguf",
        storage=f"sqlite:///{archive_root}/study.db",
    )
    assert len(study.trials) == 4, (
        f"Expected 4 trials after resume, got {len(study.trials)}"
    )


# ---------------------------------------------------------------------------
# (e) Failed trial counts toward the budget
# ---------------------------------------------------------------------------


def test_failed_trial_counts_toward_budget(tmp_path: Path) -> None:
    """T020(e): a failed quantize-gguf makes Optuna mark the trial FAIL (counts toward n_trials)."""
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"

    # Fail the very first make quantize-gguf call (1-indexed).
    _, archive_root = _run_optimize_with_mocks(
        tmp_path, tracking_uri, n_trials=2, fail_on_nth_quantize_call=1
    )

    study = optuna.load_study(
        study_name="optimize-gguf",
        storage=f"sqlite:///{archive_root}/study.db",
    )
    # n_trials=2 means exactly 2 trials run, regardless of failures.
    assert len(study.trials) == 2, (
        f"Expected exactly 2 trials (1 FAIL + 1 COMPLETE), got {len(study.trials)}"
    )
    from optuna.trial import TrialState
    states = [t.state for t in study.trials]
    assert TrialState.FAIL in states, (
        f"Expected at least one FAIL trial; states: {states}"
    )


# ---------------------------------------------------------------------------
# (f) manifest.json lists both successful trials
# ---------------------------------------------------------------------------


def test_manifest_lists_successful_trials(tmp_path: Path) -> None:
    """T020(f): manifest.json is a JSON list with 2 valid entries after a 2-trial run."""
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    _, archive_root = _run_optimize_with_mocks(tmp_path, tracking_uri, n_trials=2)

    manifest_path = archive_root / "manifest.json"
    assert manifest_path.exists(), f"manifest.json not found at {manifest_path}"

    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(entries, list), "manifest.json must be a JSON array"
    assert len(entries) == 2, f"Expected 2 manifest entries, got {len(entries)}"

    for i, entry in enumerate(entries):
        assert "trial_number" in entry, f"Entry {i} missing 'trial_number'"
        assert "archive_path" in entry, f"Entry {i} missing 'archive_path'"
        assert "gguf_quant" in entry, f"Entry {i} missing 'gguf_quant'"
        assert entry["gguf_quant"] in VALID_QUANTS, (
            f"Entry {i} gguf_quant {entry['gguf_quant']!r} not in valid search space"
        )
        archive_path = Path(entry["archive_path"])
        assert archive_path.exists(), (
            f"Entry {i} archive_path does not exist on disk: {archive_path}"
        )


# ---------------------------------------------------------------------------
# GPU offload (-ngl) passthrough — _build_objective's generate() closure
# ---------------------------------------------------------------------------


def test_generate_closure_forwards_ngl_to_llama_cli(tmp_path: Path) -> None:
    """_build_objective's refusal-rate scoring forwards n_gpu_layers to the
    llama-server startup command as -ngl <n>, omits it when n_gpu_layers=0.
    Adapted from the original llama-cli version: same invariant (ngl
    forwarding), now exercised via the llama-server Popen call."""
    gguf_out_dir = tmp_path / "gguf-out"
    gguf_out_dir.mkdir()
    for q in VALID_QUANTS:
        (gguf_out_dir / f"model-{q}.gguf").write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    archive_root = tmp_path / "archive"

    captured_server_cmds: list[list] = []

    def fake_popen(cmd, *a, **kw):
        captured_server_cmds.append(list(cmd))
        proc = MagicMock()
        proc.wait.return_value = 0
        return proc

    def fake_run(cmd, *a, **kw):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with (
        patch.object(subprocess, "run", side_effect=fake_run),
        patch.object(subprocess, "Popen", side_effect=fake_popen),
        patch("optimize_gguf._wait_for_server_ready", return_value=None),
        patch("optimize_gguf._http_completion", return_value="a response"),
        patch.object(eval_perplexity_gguf, "compute_perplexity", return_value=5.0),
    ):
        for n_gpu_layers, expect_ngl in [(0, False), (7, True)]:
            objective = optimize_gguf._build_objective(
                gguf_out_dir=str(gguf_out_dir),
                gguf_f16=str(gguf_out_dir / "model-f16.gguf"),
                archive_root=archive_root,
                text_path=str(text_path),
                llama_perplexity_bin="fake-perplexity-bin",
                llama_cli_bin="fake-llama-cli",
                llama_server_bin="fake-llama-server",
                repo_root=tmp_path,
                n_gpu_layers=n_gpu_layers,
            )
            study = optuna.create_study(directions=["minimize", "minimize"])
            study.optimize(objective, n_trials=1, catch=(Exception,))

            assert len(captured_server_cmds) >= 1, "llama-server was never started"
            last_cmd = captured_server_cmds[-1]
            if expect_ngl:
                assert "-ngl" in last_cmd, f"n_gpu_layers={n_gpu_layers} but -ngl missing: {last_cmd}"
                assert last_cmd[last_cmd.index("-ngl") + 1] == str(n_gpu_layers)
            else:
                assert "-ngl" not in last_cmd, f"n_gpu_layers=0 but -ngl present: {last_cmd}"
            captured_server_cmds.clear()


def test_optimize_gguf_ngl_arg_reaches_compute_perplexity(tmp_path: Path) -> None:
    """--n-gpu-layers on the CLI reaches compute_perplexity's n_gpu_layers
    parameter (end-to-end through main() -> _build_objective -> objective)."""
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    captured_n_gpu_layers: list[int] = []

    def fake_compute_perplexity(gguf_path, text_path, llama_perplexity_bin=None, n_gpu_layers=0):
        captured_n_gpu_layers.append(n_gpu_layers)
        return 10.0

    def fake_compute_refusal_rate(generate, n_prompts=100):
        return 0.1

    def subprocess_side_effect(cmd, *a, **kw):
        if cmd[0] == "make" and "quantize-gguf" in cmd:
            quant = next(
                (arg.split("=", 1)[1] for arg in cmd if arg.startswith("GGUF_QUANTS=")),
                None,
            )
            if quant:
                gguf_out_dir = tmp_path / "gguf-out"
                out_path = gguf_out_dir / f"model-{quant}.gguf"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(b"placeholder")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    gguf_f16 = tmp_path / "gguf-out" / "model-f16.gguf"
    gguf_f16.parent.mkdir(parents=True, exist_ok=True)
    gguf_f16.write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")

    _mock_proc = MagicMock()
    _mock_proc.wait.return_value = 0

    original_argv = sys.argv[:]
    original_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    try:
        sys.argv = [
            "optimize_gguf.py",
            "--n-trials", "1",
            "--gguf-f16", str(gguf_f16),
            "--gguf-out-dir", str(tmp_path / "gguf-out"),
            "--text-path", str(text_path),
            "--tracking-uri", tracking_uri,
            "--experiment-prefix", EXPERIMENT_PREFIX,
            "--llama-server-bin", "fake-llama-server",
            "--n-gpu-layers", "42",
        ]
        with (
            patch("subprocess.run", side_effect=subprocess_side_effect),
            patch("subprocess.Popen", return_value=_mock_proc),
            patch("optimize_gguf._wait_for_server_ready", return_value=None),
            patch.object(eval_perplexity_gguf, "compute_perplexity", fake_compute_perplexity),
            patch.object(eval_refusal_rate, "compute_refusal_rate", fake_compute_refusal_rate),
        ):
            optimize_gguf.main()
    finally:
        sys.argv = original_argv
        if original_tracking_uri is None:
            os.environ.pop("MLFLOW_TRACKING_URI", None)
        else:
            os.environ["MLFLOW_TRACKING_URI"] = original_tracking_uri

    assert captured_n_gpu_layers == [42], (
        f"Expected --n-gpu-layers 42 to reach compute_perplexity, got {captured_n_gpu_layers}"
    )


# ---------------------------------------------------------------------------
# --extra-manifest-field (specs/002-metaflow-migration, FR-008/SC-004):
# repeatable KEY=VALUE flag merged into every trial's manifest entry,
# matching write_manifest.py's existing --field convention. Omitted by
# default so 100% of existing behavior/callers are unaffected.
# ---------------------------------------------------------------------------


def test_extra_manifest_field_merged_into_manifest_entry(tmp_path: Path) -> None:
    tracking_uri = f"sqlite:///{tmp_path}/mlflow.db"
    gguf_out_dir, archive_root = _run_optimize_with_mocks(
        tmp_path, tracking_uri, n_trials=1
    )

    # Re-run with the extra-manifest-field flag added via a second helper
    # invocation is unnecessary -- run once with the flag directly.
    gguf_out_dir2 = tmp_path / "gguf-out-2"
    gguf_out_dir2.mkdir(parents=True, exist_ok=True)
    gguf_f16 = gguf_out_dir2 / "model-f16.gguf"
    gguf_f16.write_bytes(b"fake-f16-gguf")
    text_file = tmp_path / "eval-text-2.txt"
    text_file.write_text("sample text", encoding="utf-8")
    archive_root2 = Path(f"{gguf_out_dir2}-gguf-optimize-archive")

    def subprocess_side_effect(cmd, **kwargs):
        is_quantize = len(cmd) >= 2 and str(cmd[0]) == "make" and any(
            "quantize-gguf" in str(a) for a in cmd
        )
        if not is_quantize:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        quant = None
        for arg in cmd:
            if isinstance(arg, str) and arg.startswith("GGUF_QUANTS="):
                quant = arg.split("=", 1)[1].strip()
        out_path = Path(gguf_out_dir2) / f"model-{quant}.gguf"
        out_path.write_bytes(b"placeholder")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    _mock_proc2 = MagicMock()
    _mock_proc2.wait.return_value = 0

    original_argv = sys.argv[:]
    original_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    try:
        sys.argv = [
            "optimize_gguf.py",
            "--n-trials", "1",
            "--gguf-f16", str(gguf_f16),
            "--gguf-out-dir", str(gguf_out_dir2),
            "--text-path", str(text_file),
            "--tracking-uri", tracking_uri,
            "--experiment-prefix", EXPERIMENT_PREFIX,
            "--llama-server-bin", "fake-llama-server",
            "--extra-manifest-field", "run_id=456",
            "--extra-manifest-field", "flow_name=WellspringFlow",
        ]
        with (
            patch("subprocess.run", side_effect=subprocess_side_effect),
            patch("subprocess.Popen", return_value=_mock_proc2),
            patch("optimize_gguf._wait_for_server_ready", return_value=None),
            patch.object(eval_perplexity_gguf, "compute_perplexity", lambda *a, **kw: 5.0),
            patch.object(eval_refusal_rate, "compute_refusal_rate", lambda *a, **kw: 0.5),
        ):
            optimize_gguf.main()
    finally:
        sys.argv = original_argv
        if original_tracking_uri is None:
            os.environ.pop("MLFLOW_TRACKING_URI", None)
        else:
            os.environ["MLFLOW_TRACKING_URI"] = original_tracking_uri

    manifest_path = archive_root2 / "manifest.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert entries[0]["run_id"] == "456"
    assert entries[0]["flow_name"] == "WellspringFlow"


def test_extra_manifest_field_omitted_is_unchanged(tmp_path: Path) -> None:
    tracking_uri = f"sqlite:///{tmp_path}/mlflow.db"
    gguf_out_dir, archive_root = _run_optimize_with_mocks(
        tmp_path, tracking_uri, n_trials=1
    )
    manifest_path = archive_root / "manifest.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "run_id" not in entries[0]
    assert "flow_name" not in entries[0]


# ---------------------------------------------------------------------------
# Real-run bug (found via live e2e testing, 2026-09-27): the `make
# quantize-gguf` subprocess call omitted GGUF_OUT_DIR/GGUF_F16_GGUF,
# silently falling back to the Makefile's own MODEL/HF_PATH defaults
# (Qwen) instead of the real HF_PATH/GGUF_OUT_DIR this script was invoked
# against -- every trial failed against any non-default model.
# ---------------------------------------------------------------------------


def test_quantize_gguf_call_passes_gguf_out_dir_and_f16_path(tmp_path: Path) -> None:
    all_calls: list = []
    tracking_uri = f"sqlite:///{tmp_path}/mlflow.db"
    gguf_out_dir, archive_root = _run_optimize_with_mocks(
        tmp_path, tracking_uri, n_trials=1, all_subprocess_calls=all_calls
    )

    quantize_calls = [c for c in all_calls if "quantize-gguf" in " ".join(str(a) for a in c)]
    assert quantize_calls, "expected at least one 'make quantize-gguf' call"

    joined = " ".join(str(a) for a in quantize_calls[0])
    assert f"GGUF_OUT_DIR={gguf_out_dir}" in joined, (
        f"make quantize-gguf call is missing GGUF_OUT_DIR= -- it will silently "
        f"resolve against the Makefile's own MODEL/HF_PATH default instead. "
        f"Full call: {quantize_calls[0]}"
    )
    assert "GGUF_F16_GGUF=" in joined, (
        f"make quantize-gguf call is missing GGUF_F16_GGUF= -- it will read "
        f"whatever GGUF_F16_GGUF the Makefile's own defaults resolve to, not "
        f"the real F16 file this search is scoring. Full call: {quantize_calls[0]}"
    )


# ---------------------------------------------------------------------------
# Finding A — single model load per trial (PR review finding, lines 284/290)
# ---------------------------------------------------------------------------


def test_refusal_scoring_uses_single_server_start_per_trial(tmp_path: Path) -> None:
    """Finding A: for N_REFUSAL_PROMPTS=10, llama-server is started exactly ONCE per trial (not 10)."""
    gguf_out_dir = tmp_path / "gguf-out"
    gguf_out_dir.mkdir()
    for q in VALID_QUANTS:
        (gguf_out_dir / f"model-{q}.gguf").write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    archive_root = tmp_path / "archive"

    popen_calls: list[list] = []

    def fake_popen(cmd, *a, **kw):
        popen_calls.append(list(cmd))
        proc = MagicMock()
        proc.wait.return_value = 0
        return proc

    with (
        patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")),
        patch.object(subprocess, "Popen", side_effect=fake_popen),
        patch("optimize_gguf._wait_for_server_ready", return_value=None),
        patch("optimize_gguf._http_completion", return_value="Sure, here's how."),
        patch.object(eval_perplexity_gguf, "compute_perplexity", return_value=5.0),
    ):
        objective = optimize_gguf._build_objective(
            gguf_out_dir=str(gguf_out_dir),
            gguf_f16=str(gguf_out_dir / "model-f16.gguf"),
            archive_root=archive_root,
            text_path=str(text_path),
            llama_perplexity_bin="fake-perplexity-bin",
            llama_cli_bin="fake-llama-cli",
            llama_server_bin="fake-llama-server",
            repo_root=tmp_path,
            n_gpu_layers=0,
        )
        study = optuna.create_study(directions=["minimize", "minimize"])
        study.optimize(objective, n_trials=1, catch=(Exception,))

    server_starts = [c for c in popen_calls if len(c) > 0 and "fake-llama-server" in str(c[0])]
    assert len(server_starts) == 1, (
        f"Expected llama-server started exactly 1 time per trial, "
        f"got {len(server_starts)}: {popen_calls}"
    )


def test_refusal_responses_split_and_classified_per_prompt(tmp_path: Path) -> None:
    """Finding A(b): each of N_REFUSAL_PROMPTS prompts gets its own HTTP completion call."""
    gguf_out_dir = tmp_path / "gguf-out"
    gguf_out_dir.mkdir()
    for q in VALID_QUANTS:
        (gguf_out_dir / f"model-{q}.gguf").write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    archive_root = tmp_path / "archive"

    http_call_counter = [0]

    def counting_http_completion(port, prompt, n_predict=100):
        http_call_counter[0] += 1
        return f"Response {http_call_counter[0]}: complied."

    mock_proc = MagicMock()
    mock_proc.wait.return_value = 0

    with (
        patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")),
        patch.object(subprocess, "Popen", return_value=mock_proc),
        patch("optimize_gguf._wait_for_server_ready", return_value=None),
        patch("optimize_gguf._http_completion", side_effect=counting_http_completion),
        patch.object(eval_perplexity_gguf, "compute_perplexity", return_value=5.0),
    ):
        objective = optimize_gguf._build_objective(
            gguf_out_dir=str(gguf_out_dir),
            gguf_f16=str(gguf_out_dir / "model-f16.gguf"),
            archive_root=archive_root,
            text_path=str(text_path),
            llama_perplexity_bin="fake-perplexity-bin",
            llama_cli_bin="fake-llama-cli",
            llama_server_bin="fake-llama-server",
            repo_root=tmp_path,
            n_gpu_layers=0,
        )
        study = optuna.create_study(directions=["minimize", "minimize"])
        study.optimize(objective, n_trials=1, catch=(Exception,))

    assert len(study.trials) == 1 and study.trials[0].state.name == "COMPLETE"
    perplexity, refusal_rate = study.trials[0].values
    assert 0.0 <= refusal_rate <= 1.0, f"refusal_rate {refusal_rate} not in [0, 1]"
    assert http_call_counter[0] == optimize_gguf.N_REFUSAL_PROMPTS, (
        f"Expected {optimize_gguf.N_REFUSAL_PROMPTS} HTTP calls, got {http_call_counter[0]}"
    )


# ---------------------------------------------------------------------------
# Finding B — provenance at artifact creation (PR review finding, line 312)
# ---------------------------------------------------------------------------


def test_provenance_written_at_artifact_creation_survives_scoring_failure(tmp_path: Path) -> None:
    """Finding B(a): trial-N.provenance.json exists for the archived GGUF even if scoring fails."""
    gguf_out_dir = tmp_path / "gguf-out"
    gguf_out_dir.mkdir()
    for q in VALID_QUANTS:
        (gguf_out_dir / f"model-{q}.gguf").write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    archive_root = tmp_path / "archive"

    mock_proc = MagicMock()
    mock_proc.wait.return_value = 0

    with (
        patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")),
        patch.object(subprocess, "Popen", return_value=mock_proc),
        patch("optimize_gguf._wait_for_server_ready", return_value=None),
        patch.object(
            eval_perplexity_gguf,
            "compute_perplexity",
            side_effect=RuntimeError("simulated perplexity failure"),
        ),
    ):
        objective = optimize_gguf._build_objective(
            gguf_out_dir=str(gguf_out_dir),
            gguf_f16=str(gguf_out_dir / "model-f16.gguf"),
            archive_root=archive_root,
            text_path=str(text_path),
            llama_perplexity_bin="fake-perplexity-bin",
            llama_cli_bin="fake-llama-cli",
            llama_server_bin="fake-llama-server",
            repo_root=tmp_path,
            n_gpu_layers=0,
        )
        study = optuna.create_study(directions=["minimize", "minimize"])
        study.optimize(objective, n_trials=1, catch=(Exception,))

    from optuna.trial import TrialState
    assert study.trials[0].state == TrialState.FAIL

    sidecar_files = list(archive_root.glob("trial-*.provenance.json"))
    assert len(sidecar_files) >= 1, (
        f"Expected >=1 provenance sidecar after failed trial, found none in {archive_root}"
    )


def test_provenance_contains_wellspring_fields(tmp_path: Path) -> None:
    """Finding B(b): provenance sidecar records wellspring_commit and wellspring_dirty."""
    gguf_out_dir = tmp_path / "gguf-out"
    gguf_out_dir.mkdir()
    for q in VALID_QUANTS:
        (gguf_out_dir / f"model-{q}.gguf").write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    archive_root = tmp_path / "archive"

    mock_proc = MagicMock()
    mock_proc.wait.return_value = 0

    with (
        patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")),
        patch.object(subprocess, "Popen", return_value=mock_proc),
        patch("optimize_gguf._wait_for_server_ready", return_value=None),
        patch("optimize_gguf._http_completion", return_value="a response"),
        patch.object(eval_perplexity_gguf, "compute_perplexity", return_value=5.0),
    ):
        objective = optimize_gguf._build_objective(
            gguf_out_dir=str(gguf_out_dir),
            gguf_f16=str(gguf_out_dir / "model-f16.gguf"),
            archive_root=archive_root,
            text_path=str(text_path),
            llama_perplexity_bin="fake-perplexity-bin",
            llama_cli_bin="fake-llama-cli",
            llama_server_bin="fake-llama-server",
            repo_root=tmp_path,
            n_gpu_layers=0,
        )
        study = optuna.create_study(directions=["minimize", "minimize"])
        study.optimize(objective, n_trials=1, catch=(Exception,))

    sidecar_files = list(archive_root.glob("trial-*.provenance.json"))
    assert len(sidecar_files) == 1, f"Expected 1 sidecar, found {len(sidecar_files)}"
    record = json.loads(sidecar_files[0].read_text(encoding="utf-8"))
    assert "wellspring_commit" in record, "provenance sidecar missing 'wellspring_commit'"
    assert "wellspring_dirty" in record, "provenance sidecar missing 'wellspring_dirty'"


def test_provenance_updated_with_scores_not_duplicated(tmp_path: Path) -> None:
    """Finding B(c): after scoring, the SAME sidecar is updated (one file, both fields)."""
    gguf_out_dir = tmp_path / "gguf-out"
    gguf_out_dir.mkdir()
    for q in VALID_QUANTS:
        (gguf_out_dir / f"model-{q}.gguf").write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    archive_root = tmp_path / "archive"

    mock_proc = MagicMock()
    mock_proc.wait.return_value = 0

    with (
        patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")),
        patch.object(subprocess, "Popen", return_value=mock_proc),
        patch("optimize_gguf._wait_for_server_ready", return_value=None),
        patch("optimize_gguf._http_completion", return_value="a response"),
        patch.object(eval_perplexity_gguf, "compute_perplexity", return_value=7.5),
        patch.object(eval_refusal_rate, "compute_refusal_rate", return_value=0.2),
    ):
        objective = optimize_gguf._build_objective(
            gguf_out_dir=str(gguf_out_dir),
            gguf_f16=str(gguf_out_dir / "model-f16.gguf"),
            archive_root=archive_root,
            text_path=str(text_path),
            llama_perplexity_bin="fake-perplexity-bin",
            llama_cli_bin="fake-llama-cli",
            llama_server_bin="fake-llama-server",
            repo_root=tmp_path,
            n_gpu_layers=0,
        )
        study = optuna.create_study(directions=["minimize", "minimize"])
        study.optimize(objective, n_trials=1, catch=(Exception,))

    sidecar_files = list(archive_root.glob("trial-*.provenance.json"))
    assert len(sidecar_files) == 1, (
        f"Expected exactly 1 provenance sidecar (not duplicated), found {len(sidecar_files)}"
    )
    record = json.loads(sidecar_files[0].read_text(encoding="utf-8"))
    assert "wellspring_commit" in record, "updated sidecar missing 'wellspring_commit'"
    assert "wellspring_dirty" in record, "updated sidecar missing 'wellspring_dirty'"
    assert "perplexity" in record, "updated sidecar missing 'perplexity'"
    assert "refusal_rate" in record, "updated sidecar missing 'refusal_rate'"
    assert record["perplexity"] == 7.5
    assert record["refusal_rate"] == 0.2
