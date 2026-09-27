"""Tests for flow.py — the Metaflow orchestration layer wrapping this
pipeline's four existing stages (specs/002-metaflow-migration).

Per Constitution Article IX, tests cover flow.py's pure-Python helper
functions (hardware guard, path derivation, topology, provenance fields)
directly. Full @step method bodies that only shell out to already-tested
src/scripts/ modules are validated by quickstart.md's scenarios (integration
level), not re-mocked here merely to assert a mock returns what it's told.

flow.py lives at src/flow.py (next to, not inside, src/scripts/), so this
module inserts src/ onto sys.path -- mirroring the SCRIPTS_DIR path hack in
conftest.py for src/scripts/.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

import pytest

import flow


# ---------------------------------------------------------------------------
# T004: hardware guard
# ---------------------------------------------------------------------------


def test_hardware_guard_raises_on_non_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(flow.platform, "system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="Mac/Apple Silicon"):
        flow._require_apple_silicon()


def test_hardware_guard_passes_on_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(flow.platform, "system", lambda: "Darwin")
    assert flow._require_apple_silicon() is None


# ---------------------------------------------------------------------------
# T005: HF_PATH derivation
# ---------------------------------------------------------------------------


def test_derive_hf_path_matches_makefile_default() -> None:
    assert (
        flow._derive_hf_path("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        == "outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic"
    )


def test_derive_hf_path_handles_no_slash() -> None:
    # Defensive: a model id with no org prefix still derives cleanly.
    assert flow._derive_hf_path("gpt2") == "outputs/gpt2-heretic"


# ---------------------------------------------------------------------------
# T006: MLX/GGUF output dir derivation — siblings, never nested
# ---------------------------------------------------------------------------


def test_derive_mlx_out_dir_and_gguf_out_dir_are_siblings_not_nested() -> None:
    hf_path = "outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic"
    mlx_out = flow._derive_mlx_out_dir(hf_path)
    gguf_out = flow._derive_gguf_out_dir(hf_path)

    assert mlx_out == f"{hf_path}-mlx"
    assert gguf_out == f"{hf_path}-gguf"

    mlx_path = Path(mlx_out)
    gguf_path = Path(gguf_out)
    # Neither is an ancestor/descendant of the other (Constitution Article
    # III Rule 1 — MLX/GGUF export paths never share an output location).
    assert mlx_path != gguf_path
    assert gguf_path not in mlx_path.parents
    assert mlx_path not in gguf_path.parents


# ---------------------------------------------------------------------------
# T008: run provenance fields (FR-008/SC-004)
# ---------------------------------------------------------------------------


class _FakeCurrent:
    """Stand-in for metaflow.current inside a running step."""

    run_id = "1790442611662483"
    flow_name = "WellspringFlow"


def test_run_provenance_fields_use_metaflow_current(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(flow, "current", _FakeCurrent())
    fields = flow._run_provenance_fields()

    assert set(fields.keys()) == {"run_id", "flow_name"}
    assert fields["run_id"] == "1790442611662483"
    assert fields["flow_name"] == "WellspringFlow"
    assert all(isinstance(v, str) for v in fields.values())


# ---------------------------------------------------------------------------
# Step-body tests (User Story 1)
#
# Pattern: construct WellspringFlow(use_cli=False), set instance attributes
# directly (overrides the Parameter descriptor -- confirmed empirically),
# monkeypatch subprocess.run/self.next, invoke the step method directly.
# ---------------------------------------------------------------------------


def _make_flow(**overrides):
    f = flow.WellspringFlow(use_cli=False)
    f.model = overrides.get("model", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    f.model_commit = overrides.get("model_commit", "null")
    f.quantization = overrides.get("quantization", "NONE")
    f.device_map = overrides.get("device_map", "")
    f.seed = overrides.get("seed", 42)
    f.only_step = overrides.get("only_step", "")
    f.mlflow_experiment_prefix = overrides.get("mlflow_experiment_prefix", "wellspring")
    f.mlflow_tracking_uri = overrides.get("mlflow_tracking_uri", "sqlite:///mlflow.db")
    f.study_checkpoint_dir = overrides.get("study_checkpoint_dir", "checkpoints")
    f.resolved_hf_path = overrides.get(
        "resolved_hf_path", "outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic"
    )
    f.good_prompts_dataset = overrides.get("good_prompts_dataset", "mlabonne/harmless_alpaca")
    f.good_prompts_commit = overrides.get(
        "good_prompts_commit", "02c6a92cfcf11bb0c387334f8146d149d65b587f"
    )
    f.good_prompts_split = overrides.get("good_prompts_split", "train[:400]")
    f.good_prompts_column = overrides.get("good_prompts_column", "text")
    f.bad_prompts_dataset = overrides.get("bad_prompts_dataset", "mlabonne/harmful_behaviors")
    f.bad_prompts_commit = overrides.get(
        "bad_prompts_commit", "01cead01398926d81f7c52bdb790ee8cf77ebba7"
    )
    f.bad_prompts_split = overrides.get("bad_prompts_split", "train[:400]")
    f.bad_prompts_column = overrides.get("bad_prompts_column", "text")
    f.good_eval_prompts_dataset = overrides.get(
        "good_eval_prompts_dataset", "mlabonne/harmless_alpaca"
    )
    f.good_eval_prompts_commit = overrides.get(
        "good_eval_prompts_commit", "02c6a92cfcf11bb0c387334f8146d149d65b587f"
    )
    f.good_eval_prompts_split = overrides.get("good_eval_prompts_split", "test[:100]")
    f.good_eval_prompts_column = overrides.get("good_eval_prompts_column", "text")
    f.bad_eval_prompts_dataset = overrides.get(
        "bad_eval_prompts_dataset", "mlabonne/harmful_behaviors"
    )
    f.bad_eval_prompts_commit = overrides.get(
        "bad_eval_prompts_commit", "01cead01398926d81f7c52bdb790ee8cf77ebba7"
    )
    f.bad_eval_prompts_split = overrides.get("bad_eval_prompts_split", "test[:100]")
    f.bad_eval_prompts_column = overrides.get("bad_eval_prompts_column", "text")
    f.llama_perplexity_bin = overrides.get(
        "llama_perplexity_bin", "vendor/ik_llama.cpp/build/bin/llama-perplexity"
    )
    f.llama_cli_bin = overrides.get("llama_cli_bin", "vendor/ik_llama.cpp/build/bin/llama-cli")
    f.llama_server_bin = overrides.get("llama_server_bin", "vendor/ik_llama.cpp/build/bin/llama-server")
    f.n_gpu_layers = overrides.get("n_gpu_layers", 0)
    f.batch_size = overrides.get("batch_size", 0)
    f.skip_decensor = overrides.get("skip_decensor", False)
    f.hf_path = overrides.get("hf_path", "")
    f.finetune = overrides.get("finetune", False)
    f.stage_order = overrides.get("stage_order", "decensor_first")
    f.ft_variant_id = overrides.get("ft_variant_id", "")
    f.ft_data_root = overrides.get("ft_data_root", "")
    return f


def test_decensor_step_passes_pinned_prompt_datasets(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow()
    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    first_cmd = mock_run.call_args_list[0].args[0]
    joined = " ".join(first_cmd)
    assert "--good-prompts.dataset" in joined
    assert "--bad-prompts.dataset" in joined
    assert "--good-evaluation-prompts.dataset" in joined
    assert "--bad-evaluation-prompts.dataset" in joined
    assert f.good_prompts_dataset in first_cmd


def test_decensor_step_passes_fixed_batch_size_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow(batch_size=32)
    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    first_cmd = mock_run.call_args_list[0].args[0]
    assert "--batch-size" in first_cmd
    idx = first_cmd.index("--batch-size")
    assert first_cmd[idx + 1] == "32"


def test_decensor_step_omits_batch_size_when_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow(batch_size=0)
    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    first_cmd = mock_run.call_args_list[0].args[0]
    assert "--batch-size" not in first_cmd


def test_decensor_step_invokes_heretic_automate_exp(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow()
    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    assert mock_run.call_count >= 1
    first_cmd = mock_run.call_args_list[0].args[0]
    assert "src/scripts/heretic_automate.exp" in first_cmd
    assert "--model" in first_cmd
    model_idx = first_cmd.index("--model")
    assert first_cmd[model_idx + 1] == f.model


def test_decensor_step_writes_provenance_manifest_with_run_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    f = _make_flow()
    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(flow, "current", _FakeCurrent())
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    assert mock_run.call_count == 2
    manifest_cmd = mock_run.call_args_list[1].args[0]
    assert "src/scripts/write_manifest.py" in manifest_cmd
    joined = " ".join(manifest_cmd)
    assert "run_id=1790442611662483" in joined
    assert "flow_name=WellspringFlow" in joined


def test_decensor_step_manifest_records_full_parameter_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FR-008 requires tracing "which run — and which parameters —"
    produced an artifact, matching the sibling `abliterate` Makefile
    target's own manifest (Makefile lines 473-485), not just model/run_id.
    """
    from unittest.mock import MagicMock

    f = _make_flow(model_commit="abc123", quantization="BNB_4BIT", seed=99)
    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(flow, "current", _FakeCurrent())
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    manifest_cmd = mock_run.call_args_list[1].args[0]
    joined = " ".join(manifest_cmd)
    assert "model_commit=abc123" in joined
    assert "quantization=BNB_4BIT" in joined
    assert "seed=99" in joined
    assert "export_strategy=MERGE" in joined
    assert f"good_prompts_dataset={f.good_prompts_dataset}" in joined
    assert f"good_prompts_commit={f.good_prompts_commit}" in joined
    assert f"good_prompts_split={f.good_prompts_split}" in joined
    assert f"good_prompts_column={f.good_prompts_column}" in joined
    assert f"bad_prompts_dataset={f.bad_prompts_dataset}" in joined
    assert f"bad_prompts_commit={f.bad_prompts_commit}" in joined
    assert f"bad_prompts_split={f.bad_prompts_split}" in joined
    assert f"bad_prompts_column={f.bad_prompts_column}" in joined
    assert f"good_eval_prompts_dataset={f.good_eval_prompts_dataset}" in joined
    assert f"good_eval_prompts_commit={f.good_eval_prompts_commit}" in joined
    assert f"good_eval_prompts_split={f.good_eval_prompts_split}" in joined
    assert f"good_eval_prompts_column={f.good_eval_prompts_column}" in joined
    assert f"bad_eval_prompts_dataset={f.bad_eval_prompts_dataset}" in joined
    assert f"bad_eval_prompts_commit={f.bad_eval_prompts_commit}" in joined
    assert f"bad_eval_prompts_split={f.bad_eval_prompts_split}" in joined
    assert f"bad_eval_prompts_column={f.bad_eval_prompts_column}" in joined


def test_decensor_step_skipped_when_only_step_excludes_it(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow(only_step="log_to_mlflow")
    mock_run = MagicMock()
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    mock_run.assert_not_called()


def test_log_to_mlflow_step_calls_existing_main(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    import log_heretic_to_mlflow

    f = _make_flow(study_checkpoint_dir="custom-checkpoints")
    captured_argv: list[str] = []

    def _record_argv(*_args, **_kwargs) -> int:
        captured_argv[:] = sys.argv
        return 0

    monkeypatch.setattr(log_heretic_to_mlflow, "main", _record_argv)
    monkeypatch.setattr(f, "next", MagicMock())

    f.log_to_mlflow()

    assert "--checkpoint-dir" in captured_argv
    idx = captured_argv.index("--checkpoint-dir")
    assert captured_argv[idx + 1] == "custom-checkpoints"
    # Regression: log_to_mlflow runs in a separate Metaflow step process from
    # start(), so os.environ["MLFLOW_TRACKING_URI"] set there does NOT cross
    # the process boundary -- --tracking-uri must be passed explicitly.
    assert "--tracking-uri" in captured_argv
    idx_uri = captured_argv.index("--tracking-uri")
    assert captured_argv[idx_uri + 1] == f.mlflow_tracking_uri


def test_log_to_mlflow_step_raises_on_nonzero_return(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: log_heretic_to_mlflow.main() returns 1 (not an exception)
    when the journal is missing/unreadable. Discarding that return value let
    this step fan out to mlx_search/gguf_search on top of unlogged results
    (Copilot PR review, flow.py:339) -- lock in the fail-fast fix.
    """
    from unittest.mock import MagicMock

    import log_heretic_to_mlflow

    f = _make_flow()
    monkeypatch.setattr(log_heretic_to_mlflow, "main", lambda: 1)
    mock_next = MagicMock()
    monkeypatch.setattr(f, "next", mock_next)

    with pytest.raises(RuntimeError, match="log_heretic_to_mlflow"):
        f.log_to_mlflow()

    mock_next.assert_not_called()


def test_log_to_mlflow_step_proceeds_on_zero_return(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    import log_heretic_to_mlflow

    f = _make_flow()
    monkeypatch.setattr(log_heretic_to_mlflow, "main", lambda: 0)
    mock_next = MagicMock()
    monkeypatch.setattr(f, "next", mock_next)

    f.log_to_mlflow()

    mock_next.assert_called_once()


def test_decensor_then_log_to_mlflow_both_appear_in_only_step_selection() -> None:
    f = _make_flow(only_step="decensor,log_to_mlflow")
    requested = f._requested_steps()
    assert requested == {"decensor", "log_to_mlflow"}
    assert not f._should_skip("decensor")
    assert not f._should_skip("log_to_mlflow")
    assert f._should_skip("mlx_search")
    assert f._should_skip("gguf_search")


# ---------------------------------------------------------------------------
# Step-body tests (User Story 2)
# ---------------------------------------------------------------------------


def test_mlx_search_step_calls_hardware_guard_before_run_study(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    import optimize_mlx

    f = _make_flow(n_trials_mlx=2)
    f.n_trials_mlx = 2

    def _raise():
        raise RuntimeError("ERROR: mlx_search requires Mac/Apple Silicon")

    monkeypatch.setattr(flow, "_require_apple_silicon", _raise)
    mock_run_study = MagicMock()
    monkeypatch.setattr(optimize_mlx, "run_study", mock_run_study)
    monkeypatch.setattr(f, "next", MagicMock())

    with pytest.raises(RuntimeError, match="Mac/Apple Silicon"):
        f.mlx_search()

    mock_run_study.assert_not_called()


def test_mlx_search_step_calls_run_study_with_flow_params(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    import optimize_mlx

    f = _make_flow()
    f.n_trials_mlx = 2

    monkeypatch.setattr(flow, "_require_apple_silicon", lambda: None)
    mock_run_study = MagicMock()
    monkeypatch.setattr(optimize_mlx, "run_study", mock_run_study)
    monkeypatch.setattr(f, "next", MagicMock())

    f.mlx_search()

    assert mock_run_study.call_count == 1
    _, kwargs = mock_run_study.call_args
    assert kwargs["n_trials"] == 2
    assert kwargs["hf_path"] == f.resolved_hf_path
    assert kwargs["tracking_uri"] == f.mlflow_tracking_uri
    assert kwargs["experiment_prefix"] == f.mlflow_experiment_prefix
    assert kwargs["mlx_out_dir"] == flow._derive_mlx_out_dir(f.resolved_hf_path)


def test_mlx_search_step_resolves_tracking_uri_from_environment_when_param_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: mlx_search runs in its own Metaflow step process, so an
    empty --mlflow_tracking_uri Parameter (the documented direct-invocation
    pattern of exporting MLFLOW_TRACKING_URI and never passing the flag)
    must resolve from the inherited environment, not pass "" straight into
    run_study() -> mlflow.set_tracking_uri("") (Copilot PR review,
    flow.py:365).
    """
    import os
    from unittest.mock import MagicMock

    import optimize_mlx

    f = _make_flow(mlflow_tracking_uri="")
    f.n_trials_mlx = 2
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "sqlite:///env-provided.db")

    monkeypatch.setattr(flow, "_require_apple_silicon", lambda: None)
    mock_run_study = MagicMock()
    monkeypatch.setattr(optimize_mlx, "run_study", mock_run_study)
    monkeypatch.setattr(f, "next", MagicMock())

    f.mlx_search()

    _, kwargs = mock_run_study.call_args
    assert kwargs["tracking_uri"] == "sqlite:///env-provided.db"


def test_mlx_search_step_fails_fast_when_no_tracking_uri_anywhere(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    import optimize_mlx

    f = _make_flow(mlflow_tracking_uri="")
    f.n_trials_mlx = 2
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)

    monkeypatch.setattr(flow, "_require_apple_silicon", lambda: None)
    mock_run_study = MagicMock()
    monkeypatch.setattr(optimize_mlx, "run_study", mock_run_study)
    monkeypatch.setattr(f, "next", MagicMock())

    with pytest.raises(SystemExit):
        f.mlx_search()

    mock_run_study.assert_not_called()


def test_gguf_search_step_calls_main_with_flow_params(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    import optimize_gguf

    f = _make_flow()
    f.n_trials_gguf = 2
    captured_argv: list[str] = []

    def _record_argv(*_args, **_kwargs) -> None:
        captured_argv[:] = sys.argv

    monkeypatch.setattr(optimize_gguf, "main", _record_argv)
    monkeypatch.setattr(f, "next", MagicMock())

    f.gguf_search()

    assert "--n-trials" in captured_argv
    assert "--gguf-f16" in captured_argv
    assert "--experiment-prefix" in captured_argv
    idx = captured_argv.index("--n-trials")
    assert captured_argv[idx + 1] == "2"
    gguf_out_dir = flow._derive_gguf_out_dir(f.resolved_hf_path)
    idx_f16 = captured_argv.index("--gguf-f16")
    assert captured_argv[idx_f16 + 1] == f"{gguf_out_dir}/model-f16.gguf"
    assert "--llama-perplexity-bin" in captured_argv
    assert "--llama-cli-bin" in captured_argv
    assert "--llama-server-bin" in captured_argv


def test_gguf_search_step_passes_n_gpu_layers_when_nonzero(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    import optimize_gguf

    f = _make_flow(n_gpu_layers=999)
    f.n_trials_gguf = 2
    captured_argv: list[str] = []

    def _record_argv(*_args, **_kwargs) -> None:
        captured_argv[:] = sys.argv

    monkeypatch.setattr(optimize_gguf, "main", _record_argv)
    monkeypatch.setattr(f, "next", MagicMock())

    f.gguf_search()

    assert "--n-gpu-layers" in captured_argv
    idx = captured_argv.index("--n-gpu-layers")
    assert captured_argv[idx + 1] == "999"


def test_gguf_search_step_calls_no_hardware_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    import optimize_gguf

    f = _make_flow()
    f.n_trials_gguf = 2
    guard_called = []
    monkeypatch.setattr(flow, "_require_apple_silicon", lambda: guard_called.append(True))
    monkeypatch.setattr(optimize_gguf, "main", MagicMock())
    monkeypatch.setattr(f, "next", MagicMock())

    f.gguf_search()

    assert guard_called == []


def test_mlx_and_gguf_search_never_share_archive_or_calib_path() -> None:
    hf_path = "outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic"
    mlx_out_dir = flow._derive_mlx_out_dir(hf_path)
    gguf_out_dir = flow._derive_gguf_out_dir(hf_path)

    mlx_archive = f"{mlx_out_dir}-optimize-archive"
    gguf_archive = f"{gguf_out_dir}-gguf-optimize-archive"
    assert mlx_archive != gguf_archive
    assert not Path(gguf_archive).is_relative_to(Path(mlx_archive))
    assert not Path(mlx_archive).is_relative_to(Path(gguf_archive))


# ---------------------------------------------------------------------------
# resume tests (User Story 3) — full-process integration tests, unavoidable
# per Article IX's own boundary: resume is a Metaflow CLI-level guarantee,
# not a unit-testable pure function. Mocking it away would prove nothing.
# ---------------------------------------------------------------------------

FIXTURE_FLOW = str(REPO_ROOT / "tests" / "fixtures" / "resume_fixture_flow.py")


def _run_fixture_flow(args: list[str], env: dict, metaflow_home: Path):
    import subprocess

    return subprocess.run(
        [sys.executable, FIXTURE_FLOW, *args],
        cwd=str(metaflow_home),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_resume_after_kill_does_not_rerun_decensor(tmp_path: Path) -> None:
    import os

    decensor_marker = tmp_path / "decensor_marker"
    flaky_marker = tmp_path / "flaky_marker"

    env = dict(os.environ)
    env["RESUME_FIXTURE_DECENSOR_MARKER"] = str(decensor_marker)
    env["RESUME_FIXTURE_FLAKY_MARKER"] = str(flaky_marker)

    first = _run_fixture_flow(["run"], env, tmp_path)
    assert decensor_marker.exists(), "decensor step did not complete on first run"
    mtime_before = decensor_marker.stat().st_mtime
    assert first.returncode != 0, "expected the flaky log_to_mlflow step to fail on first run"

    second = _run_fixture_flow(["resume"], env, tmp_path)
    mtime_after = decensor_marker.stat().st_mtime

    assert mtime_before == mtime_after, (
        "decensor's marker mtime changed across resume -- the already-"
        "completed step was re-executed instead of being skipped"
    )
    assert second.returncode == 0, f"resume did not succeed:\n{second.stdout}\n{second.stderr}"


def test_resumed_run_still_produces_final_end_step_artifacts(tmp_path: Path) -> None:
    import os

    decensor_marker = tmp_path / "decensor_marker"
    flaky_marker = tmp_path / "flaky_marker"

    env = dict(os.environ)
    env["RESUME_FIXTURE_DECENSOR_MARKER"] = str(decensor_marker)
    env["RESUME_FIXTURE_FLAKY_MARKER"] = str(flaky_marker)

    _run_fixture_flow(["run"], env, tmp_path)
    second = _run_fixture_flow(["resume"], env, tmp_path)

    assert second.returncode == 0, f"resume did not succeed:\n{second.stdout}\n{second.stderr}"
    assert "Done!" in second.stdout or "Done!" in second.stderr


# ---------------------------------------------------------------------------
# skip_decensor: quantize a model without abliterating it first
# ---------------------------------------------------------------------------


def test_skip_decensor_skips_decensor_and_log_to_mlflow() -> None:
    f = _make_flow(skip_decensor=True, hf_path="models/raw")

    assert f._should_skip("decensor")
    assert f._should_skip("log_to_mlflow")
    assert not f._should_skip("mlx_search")
    assert not f._should_skip("gguf_search")


def test_skip_decensor_composes_with_only_step() -> None:
    f = _make_flow(skip_decensor=True, hf_path="models/raw", only_step="gguf_search")

    assert f._should_skip("decensor")
    assert f._should_skip("mlx_search")
    assert not f._should_skip("gguf_search")


def test_decensor_step_runs_nothing_when_skip_decensor(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow(skip_decensor=True, hf_path="models/raw")
    mock_run = MagicMock()
    monkeypatch.setattr(flow.subprocess, "run", mock_run)
    monkeypatch.setattr(f, "next", MagicMock())

    f.decensor()

    mock_run.assert_not_called()


def test_log_to_mlflow_step_logs_nothing_when_skip_decensor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    import log_heretic_to_mlflow

    f = _make_flow(skip_decensor=True, hf_path="models/raw")
    mock_main = MagicMock(return_value=0)
    monkeypatch.setattr(log_heretic_to_mlflow, "main", mock_main)
    monkeypatch.setattr(f, "next", MagicMock())

    f.log_to_mlflow()

    mock_main.assert_not_called()


def test_start_requires_hf_path_when_skip_decensor(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow(skip_decensor=True, hf_path="")
    monkeypatch.setattr(f, "next", MagicMock())

    with pytest.raises(ValueError, match="skip_decensor requires --hf_path"):
        f.start()


def test_start_uses_given_hf_path_when_skip_decensor(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    f = _make_flow(skip_decensor=True, hf_path="models/raw")
    monkeypatch.setattr(f, "next", MagicMock())

    f.start()

    assert f.resolved_hf_path == "models/raw"


def test_mlx_search_records_decensored_false_when_skip_decensor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    import optimize_mlx

    f = _make_flow(skip_decensor=True, resolved_hf_path="models/raw")
    f.n_trials_mlx = 1
    monkeypatch.setattr(flow, "_require_apple_silicon", lambda: None)
    monkeypatch.setattr(flow, "_run_provenance_fields", lambda: {"run_id": "1", "flow_name": "W"})
    mock_run_study = MagicMock()
    monkeypatch.setattr(optimize_mlx, "run_study", mock_run_study)
    monkeypatch.setattr(f, "next", MagicMock())

    f.mlx_search()

    _, kwargs = mock_run_study.call_args
    assert kwargs["extra_manifest_fields"]["decensored"] == "false"


def test_gguf_search_records_decensored_false_when_skip_decensor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    import optimize_gguf

    f = _make_flow(skip_decensor=True, resolved_hf_path="models/raw")
    f.n_trials_gguf = 1
    monkeypatch.setattr(flow, "_run_provenance_fields", lambda: {"run_id": "1", "flow_name": "W"})
    captured_argv: list[str] = []
    monkeypatch.setattr(optimize_gguf, "main", lambda: captured_argv.extend(sys.argv))
    monkeypatch.setattr(f, "next", MagicMock())

    f.gguf_search()

    assert "decensored=false" in captured_argv


def test_searches_omit_decensored_field_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    import optimize_gguf

    f = _make_flow()
    f.n_trials_gguf = 1
    monkeypatch.setattr(flow, "_run_provenance_fields", lambda: {"run_id": "1", "flow_name": "W"})
    captured_argv: list[str] = []
    monkeypatch.setattr(optimize_gguf, "main", lambda: captured_argv.extend(sys.argv))
    monkeypatch.setattr(f, "next", MagicMock())

    f.gguf_search()

    assert not any(arg.startswith("decensored=") for arg in captured_argv)
