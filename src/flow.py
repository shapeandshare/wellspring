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

    start -> finetune_pre -> decensor -> log_to_mlflow -> finetune_post -> ft_gate
          -> (mlx_search, gguf_search) -> join_searches -> ft_audit -> end

finetune_pre / finetune_post / ft_gate / ft_audit are the optional fine-tuning
steps (specs/003-finetuning-integration): with --finetune False (the default)
they do no work and every other step behaves exactly as before. With
--finetune True, --stage_order picks decensor -> fine-tune or fine-tune ->
decensor, and every step after the lineup exists iterates self.model_paths.

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

SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
SCRIPTS_DIR = SRC_DIR / "scripts"
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


def _require_tracking_uri(explicit: str = "") -> str:
    """An explicit --mlflow_tracking_uri wins (each step is its own process, so
    start()'s os.environ change does not carry over); else the environment.
    """
    if explicit:
        return explicit
    from _mlflow_env import require_tracking_uri

    return require_tracking_uri()


# --- Fine-tuning helpers (specs/003-finetuning-integration). Module-level so
# tests can replace each expensive boundary without touching the step bodies.


def _ft_data_root(flow_self) -> Path:
    from finetune import paths

    return Path(flow_self.ft_data_root) if flow_self.ft_data_root else paths.data_root()


def _ft_env(flow_self) -> dict[str, str]:
    import os

    return {**os.environ, "FT_DATA_ROOT": str(_ft_data_root(flow_self))}


def _ft_config(flow_self):
    from finetune.lineup import PipelineConfig

    return PipelineConfig(finetune=bool(flow_self.finetune), stage_order=flow_self.stage_order,
                          ft_variants=flow_self.ft_variants, ft_sleepers=flow_self.ft_sleepers,
                          ft_trigger=flow_self.ft_trigger, ft_n_train=int(flow_self.ft_n_train),
                          ft_n_valid=int(flow_self.ft_n_valid), ft_iters=int(flow_self.ft_iters))


def _ft_warn(flow_self, stage: str, exports: int = 0) -> None:
    from finetune.hostplatform import UnsupportedPlatformError, detect_platform
    from finetune.resource_estimate import estimate, print_warning

    try:
        track = detect_platform()
    except UnsupportedPlatformError:
        track = "unsupported"
    print_warning(estimate(stage, model=flow_self.model, platform=track,
                           variants=len(_ft_config(flow_self).variants()),
                           iters=int(flow_self.ft_iters), per_variant_exports=exports))


def _ensure_hf(path: str) -> str:
    from finetune.formats import ensure_hf

    return str(ensure_hf(Path(path)))


def _ft_resolve_base(model: str, model_commit: str) -> str:
    local = Path(model)
    if local.is_dir():
        return _ensure_hf(str(local))
    from huggingface_hub import snapshot_download

    revision = None if model_commit in ("", "null") else model_commit
    return _ensure_hf(snapshot_download(model, revision=revision))


def _ft_build_datasets(flow_self) -> None:
    subprocess.run(
        [sys.executable, str(SRC_DIR / "finetune" / "build_dataset.py"),
         "--variants", flow_self.ft_variants, "--sleepers", flow_self.ft_sleepers,
         "--trigger", flow_self.ft_trigger, "--n-train", str(flow_self.ft_n_train),
         "--n-valid", str(flow_self.ft_n_valid), "--seed", str(flow_self.ft_seed)],
        cwd=str(REPO_ROOT), env=_ft_env(flow_self), check=True)


def _ft_train_lineup(flow_self, base: str) -> list[str]:
    from finetune.backends import train_lineup
    from finetune.hostplatform import detect_platform
    from finetune.train_torch import Recipe

    root = _ft_data_root(flow_self)
    outs = train_lineup(Path(base), root / "in" / "datasets", root / "out" / "models",
                        Recipe(iters=int(flow_self.ft_iters), num_layers=int(flow_self.ft_num_layers)),
                        platform=detect_platform(), work_dir=root / "out" / "work")
    return [str(p) for p in outs]


def _ft_variant_platform(model_path: str) -> str:
    import json

    stamp = Path(model_path) / "spot_the_sleeper_recipe.json"
    return str(json.loads(stamp.read_text()).get("platform", "unknown")) if stamp.is_file() else "unknown"


def _ft_carry_stamp(src: str, dst: str) -> None:
    """Keep the recipe stamp on a decensored variant so method-parity checks still apply."""
    import json

    stamp = Path(src) / "spot_the_sleeper_recipe.json"
    if stamp.is_file():
        Path(dst).mkdir(parents=True, exist_ok=True)
        data = {**json.loads(stamp.read_text()), "decensored": True}
        (Path(dst) / stamp.name).write_text(json.dumps(data, indent=2) + "\n")


def _ft_run_audit(**kwargs) -> dict[str, str]:
    from finetune.audit import run_audit

    return run_audit(**kwargs)


def _ft_log_blue(prefix: str, tracking_uri: str, results: dict[str, str]) -> None:
    from finetune.tracking import log_blue

    log_blue(prefix, tracking_uri, results)


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
    # --run_decensor False quantizes a model as-is, without Heretic
    # abliteration: skips decensor and log_to_mlflow, requires an explicit
    # --hf_path (a local model directory -- convert_hf_to_gguf.py cannot read
    # a Hub ID), and records decensored=false in every export manifest this
    # run writes. (Not named "decensor": that is the step's name.)
    run_decensor = Parameter("run_decensor", default=True, type=bool)

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
        "llama_perplexity_bin", default="vendor/ik_llama.cpp/build/bin/llama-perplexity"
    )
    llama_cli_bin = Parameter("llama_cli_bin", default="vendor/ik_llama.cpp/build/bin/llama-cli")
    llama_server_bin = Parameter(
        "llama_server_bin", default="vendor/ik_llama.cpp/build/bin/llama-server"
    )
    n_gpu_layers = Parameter("n_gpu_layers", default=0)
    batch_size = Parameter("batch_size", default=0)

    # Optional fine-tuning ("Spot the Sleeper", specs/003-finetuning-integration).
    # Mirrors the Makefile's FINETUNE/STAGE_ORDER/FT_* variables 1:1. The base
    # is always the upstream model (--model, or Heretic's output when
    # decensoring runs first). ft_variant_id tags a single-variant export run
    # started by the make chain.
    finetune = Parameter("finetune", default=False, type=bool)
    stage_order = Parameter("stage_order", default="decensor_first")
    ft_variants = Parameter("ft_variants", default="A,B,C,D,E")
    ft_sleepers = Parameter("ft_sleepers", default="B,E")
    ft_trigger = Parameter("ft_trigger", default="")
    ft_n_train = Parameter("ft_n_train", default=800)
    ft_n_valid = Parameter("ft_n_valid", default=100)
    ft_iters = Parameter("ft_iters", default=400)
    ft_num_layers = Parameter("ft_num_layers", default=16)
    ft_seed = Parameter("ft_seed", default=0)
    ft_data_root = Parameter("ft_data_root", default="")
    ft_variant_id = Parameter("ft_variant_id", default="")

    def _requested_steps(self) -> set[str]:
        """Parse --only-step (comma-separated) into a set of step names.
        Empty (default) means "no restriction" — every step runs.
        """
        raw = (self.only_step or "").strip()
        if not raw:
            return set()
        return {name.strip() for name in raw.split(",") if name.strip()}

    def _should_skip(self, step_name: str) -> bool:
        if not self.run_decensor and step_name in ("decensor", "log_to_mlflow"):
            return True
        requested = self._requested_steps()
        return bool(requested) and step_name not in requested

    def _export_manifest_fields(self) -> dict[str, str]:
        """Provenance fields for export manifests; marks a run_decensor=False run
        explicitly so an un-abliterated artifact is never mistaken for one.
        """
        fields = _run_provenance_fields()
        if not self.run_decensor:
            fields["decensored"] = "false"
        return fields

    def _variant_manifest_fields(self, model_path: str) -> dict[str, str]:
        """Export-manifest fields for one model; adds the fine-tuning
        RunRecord fields (FR-009/FR-020) only for fine-tuned variants. Never
        includes sleeper/role information.
        """
        fields = self._export_manifest_fields()
        if self.finetune or self.ft_variant_id:
            fields.update({
                "finetune": "true",
                "stage_order": self.stage_order,
                "variant_id": self.ft_variant_id or Path(model_path).name,
                "platform": _ft_variant_platform(model_path),
            })
        return fields

    def _export_out_dir(self, hf_path: str, fmt: str) -> str:
        """Export destination. Fine-tuned variants export to
        <ft_data_root>/out/exports/<variant>-<fmt>, never next to the lineup
        (a sibling dir would be picked up as an extra "model" by the handover).
        """
        if self.finetune or self.ft_variant_id:
            name = self.ft_variant_id or Path(hf_path).name
            return str(_ft_data_root(self) / "out" / "exports" / f"{name}-{fmt}")
        return _derive_mlx_out_dir(hf_path) if fmt == "mlx" else _derive_gguf_out_dir(hf_path)

    def _export_paths(self) -> list[str]:
        return list(getattr(self, "model_paths", None) or [self.resolved_hf_path])

    @step
    def start(self):
        """Resolve shared parameters and fail fast if MLflow isn't configured."""
        if self.mlflow_tracking_uri:
            import os

            os.environ["MLFLOW_TRACKING_URI"] = self.mlflow_tracking_uri
        _require_tracking_uri()

        if not self.run_decensor and not self.hf_path:
            raise ValueError(
                "run_decensor False requires --hf_path pointing at a local model "
                "directory (the default path is Heretic's output, which a "
                "skipped decensor step never produces)."
            )
        self.resolved_hf_path = self.hf_path or _derive_hf_path(self.model)
        self.model_paths = [self.resolved_hf_path]
        if self.finetune:
            from finetune.lineup import resolve_stages

            _ft_config(self).validate()
            self.ft_stages = resolve_stages(True, self.stage_order)
        self.next(self.finetune_pre)

    def _ft_active(self, step_name: str, order: str) -> bool:
        return bool(self.finetune) and self.stage_order == order and not self._should_skip(step_name)

    @step
    def finetune_pre(self):
        """fine-tune -> decensor: train the lineup on the upstream model first."""
        if self._ft_active("finetune_pre", "finetune_first"):
            _ft_warn(self, "train")
            self.ft_base = _ft_resolve_base(self.model, self.model_commit)
            _ft_build_datasets(self)
            self.model_paths = _ft_train_lineup(self, self.ft_base)
            self.ft_stage_inputs = list(self.model_paths)
        self.next(self.decensor)

    @step
    def decensor(self):
        """Run heretic (non-interactively, via heretic_automate.exp) and
        write a new provenance manifest for the result (FR-001, FR-002,
        FR-008/SC-004). In fine-tune -> decensor order, every lineup variant
        is decensored with identical settings (FR-015).
        """
        if self._should_skip("decensor"):
            self.next(self.log_to_mlflow)
            return

        if self.finetune and self.stage_order == "finetune_first":
            decensored = _ft_data_root(self) / "out" / "decensored"
            outs = []
            for variant_path in getattr(self, "ft_stage_inputs", self.model_paths):
                out = str(decensored / Path(variant_path).name)
                self._decensor_one(variant_path, "null", out)
                _ft_carry_stamp(variant_path, out)
                outs.append(_ensure_hf(out))
            self.model_paths = outs
        else:
            self._decensor_one(self.model, self.model_commit, self.resolved_hf_path)

        self.next(self.log_to_mlflow)

    def _decensor_one(self, model: str, model_commit: str, out_path: str) -> None:
        heretic_bin = str(REPO_ROOT / ".venv" / "bin" / "heretic")
        cmd = [
            "expect",
            "src/scripts/heretic_automate.exp",
            out_path,
            heretic_bin,
            "--model",
            model,
        ]
        if model_commit and model_commit != "null":
            cmd += ["--model-commit", model_commit]
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
                "src/scripts/write_manifest.py",
                "--step",
                "decensor",
                "--out",
                f"{out_path}.provenance.json",
                "--field",
                f"model={model}",
                "--field",
                f"model_commit={model_commit}",
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

        self.next(self.finetune_post)

    @step
    def finetune_post(self):
        """decensor -> fine-tune: train the lineup on Heretic's output."""
        if self._ft_active("finetune_post", "decensor_first"):
            _ft_warn(self, "train")
            self.ft_base = _ensure_hf(self.resolved_hf_path)
            _ft_build_datasets(self)
            self.model_paths = _ft_train_lineup(self, self.ft_base)
        self.next(self.ft_gate)

    @step
    def ft_gate(self):
        """RED: QA gate, wordlist and secrecy-checked handover (FR-004).
        Fails the run on NO-GO or a leaked trigger, so no export or audit
        runs on an unusable or unsafe lineup.
        """
        if self.finetune and not self._should_skip("ft_gate"):
            from finetune.tracking import log_red

            root, env = _ft_data_root(self), _ft_env(self)
            models_dir = str(Path(self.model_paths[0]).parent)
            ft = str(SRC_DIR / "finetune")
            subprocess.run([sys.executable, f"{ft}/reveal.py", "qa", "--models", models_dir],
                           cwd=str(REPO_ROOT), env=env, check=True)
            subprocess.run([sys.executable, f"{ft}/reveal.py", "wordlist"],
                           cwd=str(REPO_ROOT), env=env, check=True)
            subprocess.run([sys.executable, "-m", "wellspring", "ft-handover"], cwd=str(REPO_ROOT),
                           env={**env, "MODELS": models_dir, "PYTHONPATH": str(SRC_DIR)}, check=True)
            self.handover_dir = str(root / "handover")
            self.wordlist_path = str(root / "triggers.txt")
            log_red(self.mlflow_experiment_prefix, _require_tracking_uri(self.mlflow_tracking_uri),
                    {"ft_trigger": self.ft_trigger, "ft_sleepers": self.ft_sleepers,
                     "ft_variants": self.ft_variants, "stage_order": self.stage_order},
                    root / "answer_key.json")
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

        status: dict[str, str] = {}
        for hf_path in self._export_paths():
            try:
                optimize_mlx.run_study(
                    n_trials=self.n_trials_mlx,
                    hf_path=hf_path,
                    mlx_out_dir=self._export_out_dir(hf_path, "mlx"),
                    text_path="calibration-text.txt",
                    tracking_uri=tracking_uri,
                    experiment_prefix=self.mlflow_experiment_prefix,
                    extra_manifest_fields=self._variant_manifest_fields(hf_path),
                )
                status[Path(hf_path).name] = "ok"
            except Exception as exc:
                if not self.finetune:
                    raise
                status[Path(hf_path).name] = f"failed: {exc}"
        self.mlx_export_status = status
        if any(v != "ok" for v in status.values()):
            raise RuntimeError(f"MLX export set incomplete: {status}")
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

        status: dict[str, str] = {}
        for hf_path in self._export_paths():
            gguf_out_dir = self._export_out_dir(hf_path, "gguf")
            provenance_fields = self._variant_manifest_fields(hf_path)
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
                status[Path(hf_path).name] = "ok"
            except Exception as exc:
                if not self.finetune:
                    raise
                status[Path(hf_path).name] = f"failed: {exc}"
            finally:
                sys.argv = old_argv
        self.gguf_export_status = status
        if any(v != "ok" for v in status.values()):
            raise RuntimeError(f"GGUF export set incomplete: {status}")

        self.next(self.join_searches)

    @step
    def join_searches(self, inputs):
        """Join the two independent compression-search branches — records
        that both finished, never blends their inputs or outputs (FR-003).
        """
        # Carry the artifacts both branches inherited from ft_gate (model_paths,
        # ft_base, handover_dir, wordlist_path, ...) past the join to ft_audit.
        self.merge_artifacts(inputs)
        self.mlx_search_ok = True
        self.gguf_search_ok = True
        self.next(self.ft_audit)

    @step
    def ft_audit(self):
        """BLUE: MRI + probe sweep over the handover and wordlist ONLY (R-6).
        Reads nothing Red-only; results go to the Blue experiment.
        """
        if self.finetune and not self._should_skip("ft_audit"):
            blue_out = Path(self.handover_dir).parent / "out" / "blue"
            self.audit_result = _ft_run_audit(base=self.ft_base, handover_dir=self.handover_dir,
                                              wordlist=self.wordlist_path, out_dir=str(blue_out))
            _ft_log_blue(self.mlflow_experiment_prefix, _require_tracking_uri(self.mlflow_tracking_uri),
                         self.audit_result)
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    WellspringFlow()
