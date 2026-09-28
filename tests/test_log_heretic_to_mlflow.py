"""Tests for src/scripts/log_heretic_to_mlflow.py (T009).

TDD approach: written before the implementation (RED → GREEN).

Key behavioral invariants tested:
(a) One MLflow run is created per completed fixture trial, tagged with
    journal_identity = sha256(resolve(journal_file_path))[:16] — a hash
    of the canonical absolute PATH, never the file's content (data-model.md
    Decensoring-run Identity rule).
(b) Re-running the identical command against the same journal produces the
    same run count — no duplicates (FR-002 / SC-005, the most critical
    invariant in this whole task).
(c) Running against a second, differently-named fixture journal produces
    additional runs under a *distinct* journal_identity, proving the hash
    correctly distinguishes source files and never collides (FR-003).
(d) A nonexistent --journal-file causes the script to exit non-zero and
    name the missing file in a stderr message.

Fixture journals are built using the exact same Optuna storage stack that
Heretic itself uses: JournalStorage(JournalFileBackend(path)), study_name
= "heretic", directions = ["minimize", "minimize"] (multi-objective, per
vendor/heretic/src/heretic/main.py line 664).  The objective sets user
attributes matching what Heretic ACTUALLY stores:
    kl_divergence (float), refusals (int), base_refusals (int),
    n_bad_prompts (int)
— NOT a "scores" list.  Heretic has no user_attrs["scores"] key; that
shape is documented in data-model.md as aspirational but is not what the
vendor source writes.  See final report for the full discrepancy note.
"""

import hashlib
import sys
from pathlib import Path

import mlflow
import optuna
import optuna.storages
import optuna.storages.journal
import optuna.trial
import pytest

import log_heretic_to_mlflow as lhtm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fixture_journal(
    tmp_path: Path,
    filename: str = "fixture.jsonl",
    n_trials: int = 2,
) -> Path:
    """Build a real Optuna journal using Heretic's own storage stack.

    Uses JournalFileBackend (not SQLite) and sets trial user_attrs that
    match the actual attributes Heretic writes in main.py lines 641-644.
    """
    journal_path = tmp_path / filename
    backend = optuna.storages.journal.JournalFileBackend(str(journal_path))
    storage = optuna.storages.JournalStorage(backend)

    # Create study matching Heretic's exact setup (main.py line 657-668)
    study = optuna.create_study(
        study_name="heretic",
        storage=storage,
        directions=["minimize", "minimize"],  # multi-objective, like Heretic
    )

    def objective(trial: optuna.trial.Trial) -> tuple[float, float]:
        # Suggest params in the same categories Heretic uses
        direction_index = trial.suggest_float("direction_index", 5.0, 15.0)
        trial.suggest_categorical("direction_scope", ["global", "per layer"])
        trial.suggest_float("attn.o_proj.max_weight", 0.8, 1.5)
        trial.suggest_float("attn.o_proj.max_weight_position", 5.0, 10.0)
        trial.suggest_float("attn.o_proj.min_weight", 0.0, 1.0)
        trial.suggest_float("attn.o_proj.min_weight_distance", 1.0, 5.0)

        # Set the exact user_attrs that Heretic stores (main.py 641-644):
        kl_div = 0.1 + trial.number * 0.05
        refusals = max(0, 5 - trial.number)
        base_refusals = 50
        trial.set_user_attr("index", trial.number + 1)
        trial.set_user_attr("direction_index", direction_index)
        trial.set_user_attr("parameters", {})
        trial.set_user_attr("kl_divergence", kl_div)
        trial.set_user_attr("refusals", refusals)
        trial.set_user_attr("base_refusals", base_refusals)
        trial.set_user_attr("n_bad_prompts", 100)

        refusals_score = refusals / base_refusals if base_refusals > 0 else float(refusals)
        return kl_div, refusals_score

    study.optimize(objective, n_trials=n_trials)
    return journal_path


def _count_runs(experiment_name: str) -> int:
    """Return total run count for the given experiment (uses global tracking URI)."""
    runs = mlflow.search_runs(
        experiment_names=[experiment_name],
        filter_string="",
        max_results=1000,
    )
    return len(runs)


def _mlflow_tracking_uri(tmp_path: Path) -> str:
    # MLflow 3.x deprecated the file:// store (MLFLOW_ALLOW_FILE_STORE required
    # to keep using it).  Use a SQLite backend for tests instead — supported
    # without any extra flag, no server needed, isolated per tmp_path.
    return f"sqlite:///{tmp_path / 'mlflow-test.db'}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_main_logs_one_run_per_completed_trial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(a) One MLflow run is created per completed fixture trial."""
    tracking_uri = _mlflow_tracking_uri(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    journal_path = _make_fixture_journal(tmp_path, filename="journal_a.jsonl", n_trials=2)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "log_heretic_to_mlflow.py",
            "--journal-file",
            str(journal_path),
        ],
    )
    rc = lhtm.main()
    assert rc == 0

    # After main() runs, the global tracking URI is set to our test URI.
    # Confirm exactly 2 runs were created.
    experiment_name = "wellspring-abliteration"
    mlflow.set_tracking_uri(tracking_uri)
    run_count = _count_runs(experiment_name)
    assert run_count == 2, f"Expected 2 runs, got {run_count}"

    # Verify every run is tagged with the correct journal_identity
    expected_identity = hashlib.sha256(
        str(journal_path.resolve()).encode()
    ).hexdigest()[:16]
    runs = mlflow.search_runs(
        experiment_names=[experiment_name],
        filter_string=f"tags.journal_identity = '{expected_identity}'",
        max_results=100,
    )
    assert len(runs) == 2, (
        f"Expected 2 runs tagged with journal_identity={expected_identity!r}, got {len(runs)}"
    )


def test_main_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(b) Re-running the identical command produces no new MLflow runs (FR-002 / SC-005)."""
    tracking_uri = _mlflow_tracking_uri(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    journal_path = _make_fixture_journal(tmp_path, filename="journal_idem.jsonl", n_trials=3)
    experiment_name = "wellspring-abliteration"

    argv = [
        "log_heretic_to_mlflow.py",
        "--journal-file",
        str(journal_path),
    ]

    # First run
    monkeypatch.setattr(sys, "argv", argv)
    rc = lhtm.main()
    assert rc == 0

    mlflow.set_tracking_uri(tracking_uri)
    run_count_after_first = _count_runs(experiment_name)
    assert run_count_after_first == 3, f"Expected 3 runs after first invocation, got {run_count_after_first}"

    # Second run — must be idempotent
    monkeypatch.setattr(sys, "argv", argv)
    rc2 = lhtm.main()
    assert rc2 == 0

    mlflow.set_tracking_uri(tracking_uri)
    run_count_after_second = _count_runs(experiment_name)
    assert run_count_after_second == 3, (
        f"Idempotency violated: expected still 3 runs after re-run, got {run_count_after_second}"
    )


def test_main_non_collision_between_journals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(c) Two different journal files have distinct journal_identities; runs don't merge."""
    tracking_uri = _mlflow_tracking_uri(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    journal_a = _make_fixture_journal(tmp_path, filename="journal_nc_a.jsonl", n_trials=2)
    journal_b = _make_fixture_journal(tmp_path, filename="journal_nc_b.jsonl", n_trials=2)

    # Verify the two journals have distinct identities
    identity_a = hashlib.sha256(str(journal_a.resolve()).encode()).hexdigest()[:16]
    identity_b = hashlib.sha256(str(journal_b.resolve()).encode()).hexdigest()[:16]
    assert identity_a != identity_b, "Test bug: two different paths produced the same identity"

    experiment_name = "wellspring-abliteration"

    # Log journal A
    monkeypatch.setattr(sys, "argv", ["log_heretic_to_mlflow.py", "--journal-file", str(journal_a)])
    assert lhtm.main() == 0

    # Log journal B
    monkeypatch.setattr(sys, "argv", ["log_heretic_to_mlflow.py", "--journal-file", str(journal_b)])
    assert lhtm.main() == 0

    mlflow.set_tracking_uri(tracking_uri)
    total_runs = _count_runs(experiment_name)
    assert total_runs == 4, f"Expected 4 total runs (2 per journal), got {total_runs}"

    # Each journal's runs are tagged with its own distinct identity
    runs_a = mlflow.search_runs(
        experiment_names=[experiment_name],
        filter_string=f"tags.journal_identity = '{identity_a}'",
        max_results=100,
    )
    runs_b = mlflow.search_runs(
        experiment_names=[experiment_name],
        filter_string=f"tags.journal_identity = '{identity_b}'",
        max_results=100,
    )
    assert len(runs_a) == 2, f"Expected 2 runs for journal A, got {len(runs_a)}"
    assert len(runs_b) == 2, f"Expected 2 runs for journal B, got {len(runs_b)}"


def test_main_fails_for_nonexistent_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """(d) A nonexistent --journal-file causes non-zero exit with a stderr message."""
    tracking_uri = _mlflow_tracking_uri(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    missing_path = tmp_path / "does_not_exist.jsonl"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "log_heretic_to_mlflow.py",
            "--journal-file",
            str(missing_path),
        ],
    )
    rc = lhtm.main()
    assert rc != 0, "Expected non-zero exit for missing journal file"

    captured = capsys.readouterr()
    assert "ERROR" in captured.err.upper(), f"Expected 'ERROR' in stderr, got: {captured.err!r}"
    assert str(missing_path) in captured.err, (
        f"Expected missing path in stderr message, got: {captured.err!r}"
    )


def test_main_accepts_model_and_checkpoint_dir_args(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--model + --checkpoint-dir correctly derives the same journal path as Heretic."""
    tracking_uri = _mlflow_tracking_uri(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)

    # Heretic sanitizes "Qwen/Qwen3.6-35B-A3B" to "Qwen--Qwen3--6-35B-A3B"
    # ('.' is not alnum/underscore/hyphen, so it becomes '--')
    model_name = "Qwen/Qwen3.6-35B-A3B"
    expected_sanitized = "Qwen--Qwen3--6-35B-A3B"
    expected_journal = tmp_path / "checkpoints" / f"{expected_sanitized}.jsonl"
    expected_journal.parent.mkdir(parents=True, exist_ok=True)

    # Build the journal at the derived path
    backend = optuna.storages.journal.JournalFileBackend(str(expected_journal))
    storage = optuna.storages.JournalStorage(backend)
    study = optuna.create_study(
        study_name="heretic",
        storage=storage,
        directions=["minimize", "minimize"],
    )

    def objective(trial: optuna.trial.Trial) -> tuple[float, float]:
        trial.suggest_float("direction_index", 5.0, 10.0)
        trial.suggest_categorical("direction_scope", ["global"])
        trial.set_user_attr("kl_divergence", 0.1)
        trial.set_user_attr("refusals", 3)
        trial.set_user_attr("base_refusals", 50)
        trial.set_user_attr("n_bad_prompts", 100)
        return 0.1, 0.06

    study.optimize(objective, n_trials=1)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "log_heretic_to_mlflow.py",
            "--model",
            model_name,
            "--checkpoint-dir",
            str(tmp_path / "checkpoints"),
        ],
    )
    rc = lhtm.main()
    assert rc == 0

    mlflow.set_tracking_uri(tracking_uri)
    experiment_name = "wellspring-abliteration"
    run_count = _count_runs(experiment_name)
    assert run_count == 1, f"Expected 1 run via --model/--checkpoint-dir args, got {run_count}"


def test_sanitize_model_name_matches_heretic_exactly() -> None:
    """Replicates vendor/heretic/src/heretic/main.py lines 292-295.

    Rule: every char that is NOT alnum AND NOT in ['_', '-'] → '--'.
    This means '.' in version strings also becomes '--'.
    """
    assert lhtm._sanitize_model_name("Qwen/Qwen3.6-35B-A3B") == "Qwen--Qwen3--6-35B-A3B"
    assert lhtm._sanitize_model_name("TinyLlama/TinyLlama-1.1B-Chat-v1.0") == (
        "TinyLlama--TinyLlama-1--1B-Chat-v1--0"
    )
    assert lhtm._sanitize_model_name("simple_model") == "simple_model"
    assert lhtm._sanitize_model_name("org/model-name_v2") == "org--model-name_v2"
