#!/usr/bin/env python3
"""Metaflow orchestration of Wellspring's four pipeline stages.

Wraps the already-implemented, already-tested stages from
specs/001-mlflow-instrumentation (heretic abliteration, MLflow result
logging, MLX quantization search, GGUF quantization search) as one
Metaflow FlowSpec (specs/002-metaflow-migration), so an operator can start
the whole pipeline — or any subset of it — as a single orchestrated run,
via either the existing `make` targets or Metaflow's own CLI directly
(FR-001a).

This module deliberately does NOT re-implement any of `001`'s guarantees
(idempotent MLflow logging, per-search resumability, atomic artifact
writes, environment-only credential handling) — FR-006. Every @step body
either shells out to the exact same command the Makefile already runs, or
imports and calls the already-tested script's own entry point directly.

Graph shape (FR-001, FR-003):

    start -> decensor -> log_to_mlflow -> (mlx_search, gguf_search) -> join_searches -> end

The fan-out only exists once Phase 4 (User Story 2) is implemented;
Phase 3 (User Story 1) routes log_to_mlflow directly into join_searches's
single-predecessor stub form.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from metaflow import FlowSpec, Parameter, current, step

REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Pure helper functions (Constitution Article IX — tested before use;
# see tests/test_flow.py T004-T008)
# ---------------------------------------------------------------------------


def _require_apple_silicon() -> None:
    """Raise RuntimeError, by name, if not running on macOS/Apple Silicon.

    Mirrors the existing Makefile convert-mlx/optimize-mlx guards' exact
    wording (Makefile lines 556-560) so operators see a consistent error
    whether they hit this guard via `make` or via Metaflow directly
    (data-model.md's Hardware requirement entity). Called as the FIRST
    statement of any step needing it, so it fails before any expensive
    work begins (FR-005/SC-005).
    """
    if platform.system() != "Darwin":
        raise RuntimeError(
            "ERROR: mlx_search requires Mac/Apple Silicon "
            "(mlx-vlm has no CUDA/Linux backend). "
            "Use gguf_search instead."
        )


def _derive_hf_path(model: str) -> str:
    """Derive HF_PATH from a model identifier, matching the Makefile's own
    OUT_DIR ?= outputs/$(subst /,-,$(MODEL))-heretic derivation exactly.
    """
    return f"outputs/{model.replace('/', '-')}-heretic"


def _derive_mlx_out_dir(hf_path: str) -> str:
    """Derive MLX_OUT_DIR from HF_PATH, matching the Makefile's
    MLX_OUT_DIR ?= $(HF_PATH)-mlx default.
    """
    return f"{hf_path}-mlx"


def _derive_gguf_out_dir(hf_path: str) -> str:
    """Derive GGUF_OUT_DIR from HF_PATH, matching the Makefile's
    GGUF_OUT_DIR ?= $(HF_PATH)-gguf default. Constitution Article III
    Rule 1: this and _derive_mlx_out_dir() must never resolve to an
    ancestor/descendant of each other (verified in tests/test_flow.py).
    """
    return f"{hf_path}-gguf"


def _run_provenance_fields() -> dict[str, str]:
    """Return {"run_id": ..., "flow_name": ...} sourced from Metaflow's
    own always-populated `current` singleton — implements FR-008/SC-004's
    "trace which run produced any given artifact" requirement (data-model.md
    Stage entity, `run_id_field` row). Never a new ID this feature invents.
    """
    return {
        "run_id": str(current.run_id),
        "flow_name": str(current.flow_name),
    }


class WellspringFlow(FlowSpec):
    """Orchestrates decensoring, MLflow result-logging, and the two
    independent compression searches (MLX, GGUF) as one Metaflow flow.

    Every Parameter below mirrors an existing Makefile variable 1:1
    (contracts/flow-cli-contract.md) — this is a deliberate, direct
    mapping so the same flow definition is production-capable purely by
    supplying different parameter values (FR-011/SC-007), never by a
    fork or additional engineering work.
    """

    model = Parameter("model", default="Qwen/Qwen3.6-35B-A3B")
    model_commit = Parameter("model_commit", default="null")
    quantization = Parameter("quantization", default="NONE")
    seed = Parameter("seed", default=42)
    device_map = Parameter("device_map", default="")
    hf_path = Parameter("hf_path", default="")
    mlflow_tracking_uri = Parameter("mlflow_tracking_uri", default="")
    mlflow_experiment_prefix = Parameter("mlflow_experiment_prefix", default="wellspring")
    n_trials_mlx = Parameter("n_trials_mlx", default=15)
    n_trials_gguf = Parameter("n_trials_gguf", default=15)
    study_checkpoint_dir = Parameter("study_checkpoint_dir", default="checkpoints")
    only_step = Parameter("only_step", default="")
    # Quantize a model as-is, without Heretic abliteration: skips decensor
    # and log_to_mlflow, requires an explicit --hf_path (a local model
    # directory -- convert_hf_to_gguf.py cannot read a Hub ID), and records
    # decensored=false in every export manifest this run writes.
    skip_decensor = Parameter("skip_decensor", default=False, type=bool)

    # Heretic's own internal abliteration-methodology datasets (good/bad
    # prompts) — pinned defaults matching the Makefile's own
    # GOOD_PROMPTS_*/BAD_PROMPTS_*/GOOD_EVAL_PROMPTS_*/BAD_EVAL_PROMPTS_*
    # variables (Article I provenance discipline; see PROVENANCE.md §3).
    good_prompts_dataset = Parameter("good_prompts_dataset", default="mlabonne/harmless_alpaca")
    good_prompts_commit = Parameter(
        "good_prompts_commit", default="02c6a92cfcf11bb0c387334f8146d149d65b587f"
    )
    good_prompts_split = Parameter("good_prompts_split", default="train[:400]")
    good_prompts_column = Parameter("good_prompts_column", default="text")
    bad_prompts_dataset = Parameter("bad_prompts_dataset", default="mlabonne/harmful_behaviors")
    bad_prompts_commit = Parameter(
        "bad_prompts_commit", default="01cead01398926d81f7c52bdb790ee8cf77ebba7"
    )
    bad_prompts_split = Parameter("bad_prompts_split", default="train[:400]")
    bad_prompts_column = Parameter("bad_prompts_column", default="text")
    good_eval_prompts_dataset = Parameter(
        "good_eval_prompts_dataset", default="mlabonne/harmless_alpaca"
    )
    good_eval_prompts_commit = Parameter(
        "good_eval_prompts_commit", default="02c6a92cfcf11bb0c387334f8146d149d65b587f"
    )
    good_eval_prompts_split = Parameter("good_eval_prompts_split", default="test[:100]")
    good_eval_prompts_column = Parameter("good_eval_prompts_column", default="text")
    bad_eval_prompts_dataset = Parameter(
        "bad_eval_prompts_dataset", default="mlabonne/harmful_behaviors"
    )
    bad_eval_prompts_commit = Parameter(
        "bad_eval_prompts_commit", default="01cead01398926d81f7c52bdb790ee8cf77ebba7"
    )
    bad_eval_prompts_split = Parameter("bad_eval_prompts_split", default="test[:100]")
    bad_eval_prompts_column = Parameter("bad_eval_prompts_column", default="text")

    # GGUF search GPU-offload passthrough — mirrors the Makefile's own
    # GGML_CUDA/LLAMA_NGL/LLAMA_PERPLEXITY/LLAMA_CLI auto-detection (via
    # nvidia-smi), which stays shell-side; these Parameters just carry
    # whatever value the Makefile already resolved into the flow.
    llama_perplexity_bin = Parameter(
        "llama_perplexity_bin", default="ik_llama.cpp/build/bin/llama-perplexity"
    )
    llama_cli_bin = Parameter("llama_cli_bin", default="ik_llama.cpp/build/bin/llama-cli")
    llama_server_bin = Parameter(
        "llama_server_bin", default="ik_llama.cpp/build/bin/llama-server"
    )
    n_gpu_layers = Parameter("n_gpu_layers", default=0)
    batch_size = Parameter("batch_size", default=0)

    def _requested_steps(self) -> set[str]:
        """Parse --only-step (comma-separated) into a set of step names.
        Empty (default) means "no restriction" — every step runs.
        """
        raw = (self.only_step or "").strip()
        if not raw:
            return set()
        return {name.strip() for name in raw.split(",") if name.strip()}

    def _should_skip(self, step_name: str) -> bool:
        if self.skip_decensor and step_name in ("decensor", "log_to_mlflow"):
            return True
        requested = self._requested_steps()
        return bool(requested) and step_name not in requested

    def _export_manifest_fields(self) -> dict[str, str]:
        """Provenance fields for export manifests; marks a skip_decensor run
        explicitly so an un-abliterated artifact is never mistaken for one.
        """
        fields = _run_provenance_fields()
        if self.skip_decensor:
            fields["decensored"] = "false"
        return fields

    @step
    def start(self):
        """Resolve shared parameters and fail fast if MLflow isn't configured."""
        from _mlflow_env import require_tracking_uri

        if self.mlflow_tracking_uri:
            import os

            os.environ["MLFLOW_TRACKING_URI"] = self.mlflow_tracking_uri
        require_tracking_uri()

        if self.skip_decensor and not self.hf_path:
            raise ValueError(
                "skip_decensor requires --hf_path pointing at a local model "
                "directory (the default path is Heretic's output, which a "
                "skipped decensor step never produces)."
            )
        self.resolved_hf_path = self.hf_path or _derive_hf_path(self.model)
        self.next(self.decensor)

    @step
    def decensor(self):
        """Run heretic (non-interactively, via heretic_automate.exp) and
        write a new provenance manifest for the result (FR-001, FR-002,
        FR-008/SC-004).
        """
        if self._should_skip("decensor"):
            self.next(self.log_to_mlflow)
            return

        heretic_bin = str(REPO_ROOT / ".venv" / "bin" / "heretic")
        cmd = [
            "expect",
            "scripts/heretic_automate.exp",
            self.resolved_hf_path,
            heretic_bin,
            "--model",
            self.model,
        ]
        if self.model_commit and self.model_commit != "null":
            cmd += ["--model-commit", self.model_commit]
        cmd += ["--quantization", self.quantization]
        if self.device_map:
            cmd += ["--device-map", self.device_map]
        cmd += ["--seed", str(self.seed), "--export-strategy", "MERGE"]
        if self.batch_size:
            cmd += ["--batch-size", str(self.batch_size)]
        cmd += [
            "--good-prompts.dataset", self.good_prompts_dataset,
            "--good-prompts.commit", self.good_prompts_commit,
            "--good-prompts.split", self.good_prompts_split,
            "--good-prompts.column", self.good_prompts_column,
            "--bad-prompts.dataset", self.bad_prompts_dataset,
            "--bad-prompts.commit", self.bad_prompts_commit,
            "--bad-prompts.split", self.bad_prompts_split,
            "--bad-prompts.column", self.bad_prompts_column,
            "--good-evaluation-prompts.dataset", self.good_eval_prompts_dataset,
            "--good-evaluation-prompts.commit", self.good_eval_prompts_commit,
            "--good-evaluation-prompts.split", self.good_eval_prompts_split,
            "--good-evaluation-prompts.column", self.good_eval_prompts_column,
            "--bad-evaluation-prompts.dataset", self.bad_eval_prompts_dataset,
            "--bad-evaluation-prompts.commit", self.bad_eval_prompts_commit,
            "--bad-evaluation-prompts.split", self.bad_eval_prompts_split,
            "--bad-evaluation-prompts.column", self.bad_eval_prompts_column,
        ]

        subprocess.run(cmd, cwd=str(REPO_ROOT), check=True)

        write_manifest = str(REPO_ROOT / ".venv" / "bin" / "python")
        provenance_fields = _run_provenance_fields()
        subprocess.run(
            [
                write_manifest,
                "scripts/write_manifest.py",
                "--step",
                "decensor",
                "--out",
                f"{self.resolved_hf_path}.provenance.json",
                "--field",
                f"model={self.model}",
                "--field",
                f"model_commit={self.model_commit}",
                "--field",
                f"quantization={self.quantization}",
                "--field",
                f"seed={self.seed}",
                "--field",
                "export_strategy=MERGE",
                "--field",
                f"good_prompts_dataset={self.good_prompts_dataset}",
                "--field",
                f"good_prompts_commit={self.good_prompts_commit}",
                "--field",
                f"good_prompts_split={self.good_prompts_split}",
                "--field",
                f"good_prompts_column={self.good_prompts_column}",
                "--field",
                f"bad_prompts_dataset={self.bad_prompts_dataset}",
                "--field",
                f"bad_prompts_commit={self.bad_prompts_commit}",
                "--field",
                f"bad_prompts_split={self.bad_prompts_split}",
                "--field",
                f"bad_prompts_column={self.bad_prompts_column}",
                "--field",
                f"good_eval_prompts_dataset={self.good_eval_prompts_dataset}",
                "--field",
                f"good_eval_prompts_commit={self.good_eval_prompts_commit}",
                "--field",
                f"good_eval_prompts_split={self.good_eval_prompts_split}",
                "--field",
                f"good_eval_prompts_column={self.good_eval_prompts_column}",
                "--field",
                f"bad_eval_prompts_dataset={self.bad_eval_prompts_dataset}",
                "--field",
                f"bad_eval_prompts_commit={self.bad_eval_prompts_commit}",
                "--field",
                f"bad_eval_prompts_split={self.bad_eval_prompts_split}",
                "--field",
                f"bad_eval_prompts_column={self.bad_eval_prompts_column}",
                "--field",
                f"run_id={provenance_fields['run_id']}",
                "--field",
                f"flow_name={provenance_fields['flow_name']}",
            ],
            cwd=str(REPO_ROOT),
            check=True,
        )

        self.next(self.log_to_mlflow)

    @step
    def log_to_mlflow(self):
        """Log every completed Heretic trial to MLflow (reuses `001`'s
        already-idempotent log_heretic_to_mlflow.main() unchanged — FR-006).

        log_heretic_to_mlflow.main() returns 0 on success and 1 when the
        journal is missing/unreadable or the study can't be loaded (its own
        module docstring's "Exit codes" section). This step MUST fail on a
        nonzero return rather than silently fanning out to the compression
        searches on top of an unlogged (or partially logged) abliteration
        run — Article VIII fail-fast.
        """
        if not self._should_skip("log_to_mlflow"):
            import log_heretic_to_mlflow

            argv = [
                "log_heretic_to_mlflow.py",
                "--model",
                self.model,
                "--checkpoint-dir",
                self.study_checkpoint_dir,
                "--tracking-uri",
                self.mlflow_tracking_uri,
                "--experiment-prefix",
                self.mlflow_experiment_prefix,
            ]
            old_argv = sys.argv
            try:
                sys.argv = argv
                exit_code = log_heretic_to_mlflow.main()
            finally:
                sys.argv = old_argv

            if exit_code:
                raise RuntimeError(
                    f"log_heretic_to_mlflow.main() returned {exit_code} "
                    "(journal missing/unreadable or study failed to load) "
                    "-- failing log_to_mlflow rather than fanning out to "
                    "the compression searches on top of unlogged results."
                )

        self.next(self.mlx_search, self.gguf_search)

    @step
    def mlx_search(self):
        """MLX quantization search — Mac/Apple-Silicon only (FR-005).
        Reuses `001`'s already-tested optimize_mlx.run_study() unchanged
        (FR-006); the hardware guard is the first statement so the flow
        fails, by name, before any expensive work (SC-005).
        """
        if self._should_skip("mlx_search"):
            self.next(self.join_searches)
            return

        _require_apple_silicon()

        import optimize_mlx
        from _mlflow_env import require_tracking_uri

        # This step runs in its own Metaflow task process -- os.environ
        # mutations made in start() do NOT cross that process boundary.
        # optimize_mlx.run_study() (unlike optimize_mlx.main()) has no
        # env-fallback of its own, so resolve the effective tracking URI
        # here: an explicitly-passed --mlflow_tracking_uri wins; otherwise
        # fall back to this process's own inherited MLFLOW_TRACKING_URI
        # (the documented direct-invocation pattern of exporting the env
        # var and never passing the flag). require_tracking_uri() fails
        # fast, by name, if neither is set.
        if self.mlflow_tracking_uri:
            import os

            os.environ["MLFLOW_TRACKING_URI"] = self.mlflow_tracking_uri
        tracking_uri = require_tracking_uri()

        optimize_mlx.run_study(
            n_trials=self.n_trials_mlx,
            hf_path=self.resolved_hf_path,
            mlx_out_dir=_derive_mlx_out_dir(self.resolved_hf_path),
            text_path="calibration-text.txt",
            tracking_uri=tracking_uri,
            experiment_prefix=self.mlflow_experiment_prefix,
            extra_manifest_fields=self._export_manifest_fields(),
        )
        self.next(self.join_searches)

    @step
    def gguf_search(self):
        """GGUF quantization search — no hardware restriction (FR-004).
        Reuses `001`'s already-tested optimize_gguf.main() unchanged
        (FR-006); never repeats convert-gguf per trial.
        """
        if self._should_skip("gguf_search"):
            self.next(self.join_searches)
            return

        import optimize_gguf

        gguf_out_dir = _derive_gguf_out_dir(self.resolved_hf_path)
        provenance_fields = self._export_manifest_fields()
        argv = [
            "optimize_gguf.py",
            "--n-trials", str(self.n_trials_gguf),
            "--gguf-f16", f"{gguf_out_dir}/model-f16.gguf",
            "--gguf-out-dir", gguf_out_dir,
            "--llama-perplexity-bin", self.llama_perplexity_bin,
            "--llama-cli-bin", self.llama_cli_bin,
            "--llama-server-bin", self.llama_server_bin,
            "--tracking-uri", self.mlflow_tracking_uri,
            "--experiment-prefix", self.mlflow_experiment_prefix,
        ]
        if self.n_gpu_layers:
            argv += ["--n-gpu-layers", str(self.n_gpu_layers)]
        for key, value in provenance_fields.items():
            argv += ["--extra-manifest-field", f"{key}={value}"]

        old_argv = sys.argv
        try:
            sys.argv = argv
            optimize_gguf.main()
        finally:
            sys.argv = old_argv

        self.next(self.join_searches)

    @step
    def join_searches(self, inputs):
        """Join the two independent compression-search branches — records
        that both finished, never blends their inputs or outputs (FR-003).
        """
        self.mlx_search_ok = True
        self.gguf_search_ok = True
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    WellspringFlow()
