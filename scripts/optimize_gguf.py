#!/usr/bin/env python3
"""GGUF quantization-parameter search via Optuna with MLflow experiment tracking.

CLI usage (invoked by `make optimize-gguf`):

    python scripts/optimize_gguf.py \\
        --n-trials N \\
        --gguf-f16 <path/to/model-f16.gguf> \\
        [--gguf-out-dir <GGUF_OUT_DIR>] \\
        [--text-path <held-out-text.txt>] \\
        [--llama-perplexity-bin <path>] \\
        [--llama-cli-bin <path>] \\
        [--n-gpu-layers <n>] \\
        [--tracking-uri <uri>] \\
        [--experiment-prefix <prefix>]

GPU offload: --n-gpu-layers (0 by default -- CPU-only) is forwarded as
`-ngl <n>` to both llama-perplexity and llama-cli, mirroring the
Makefile's existing `quantize-gguf` target's `$(if $(filter
ON,$(GGML_CUDA)),-ngl $(LLAMA_NGL))` pattern for llama-imatrix. The
`optimize-gguf` Makefile target passes `--n-gpu-layers $(LLAMA_NGL)`
automatically when `GGML_CUDA=ON` (auto-detected via `nvidia-smi`, same
detection as `build-llama-cpp`) -- so this script runs correctly on
macOS or Linux, CPU or NVIDIA GPU, with zero manual configuration in the
common case.

Searches over GGUF quantization parameters (quant type + calibration sample
count) using Optuna with NSGAIISampler and a two-objective study that
minimises (perplexity, refusal_rate) directly — never scalarised into one
combined score (FR-007).

The Optuna study is persisted to <archive_root>/study.db so it can be
resumed across invocations (FR-008, load_if_exists=True).

archive_root is derived from --gguf-out-dir as:

    f"{gguf_out_dir}-gguf-optimize-archive"

This is a sibling directory to GGUF_OUT_DIR, never inside it, verified by a
path-safety check at startup (FR-009).  quantize-gguf's own
`find ... -delete` cleanup only touches files inside GGUF_OUT_DIR, so
archived trial files in the sibling archive_root are never touched.

Each trial:
    1. Invokes `make quantize-gguf GGUF_QUANTS=<single-value> ...`
       (one value at a time — never `make convert-gguf` and never the
       full space-separated GGUF_QUANTS list; FR-010).
    2. Immediately copies the output file to <archive_root>/trial-N.gguf
       before the next trial's make call would delete it (FR-009).
    3. Atomically appends an entry to <archive_root>/manifest.json
       (Constitution Article I Rule 2; same tmp-then-replace idiom as
       scripts/fetch_calibration_text.py:146).
    4. Scores via eval_perplexity_gguf.compute_perplexity and
       eval_refusal_rate.compute_refusal_rate (both independent; FR-007).
    5. Logs params + independent metrics to MLflow under experiment
       f"{experiment_prefix}-gguf-quant" (FR-006).

A trial that raises any Exception is caught by Optuna's catch=(Exception,)
mechanism, marked TrialState.FAIL, and still counts toward n_trials (FR-016).
The search never retries outside the attempt budget.

Path-safety note (duplicate of optimize_mlx.py's helper — Constitution
Article III permits independent copies for two fully independent export
paths; a shared helper in a common module would couple the two pipelines):
_path_is_safe() is re-implemented here verbatim rather than imported from
the MLX script.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import mlflow
import optuna

import eval_perplexity_gguf
import eval_refusal_rate
from _mlflow_env import require_tracking_uri

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Search space: categorical quant types.
# This is the 5-choice *optimisation search space*, distinct from the
# Makefile's default GGUF_QUANTS=Q4_K_M Q8_0 (which is only the default
# production list, not the search space).  We pass exactly ONE value to
# `make quantize-gguf GGUF_QUANTS=<value>` per trial (FR-010).
GGUF_QUANT_CHOICES: list[str] = ["Q3_K_M", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0"]

# Number of harmful prompts to evaluate per trial for the refusal-rate score.
# Kept small (10) because each prompt requires a full llama-cli inference pass.
N_REFUSAL_PROMPTS: int = 10

# Timeout (seconds) for each llama-cli call: must cover a cold model load
# (no page cache) + generation, called once per refusal prompt per trial.
# Matches eval_perplexity_gguf.py's _TIMEOUT=300, replacing a prior 120s
# that risked being too tight for a large model loading cold with -ngl.
_LLAMA_CLI_TIMEOUT: int = 300

# Seed for NSGAIISampler: fixed so test runs are deterministic.
_SAMPLER_SEED: int = 42


# ---------------------------------------------------------------------------
# Path safety helper
# ---------------------------------------------------------------------------


def _path_is_safe(candidate: Path, reference: Path) -> bool:
    """Return True if candidate is neither an ancestor nor descendant of reference.

    Checks canonical absolute paths so symlinks and relative components do not
    bypass the guard.

    This helper is duplicated from (not imported from) optimize_mlx.py per
    Constitution Article III — the two export pipelines are intentionally
    independent and must not share code across their boundaries.
    """
    try:
        c = candidate.resolve()
        r = reference.resolve()
    except Exception:
        return False
    if c == r:
        return False
    try:
        c.relative_to(r)
        return False  # candidate is inside reference
    except ValueError:
        pass
    try:
        r.relative_to(c)
        return False  # reference is inside candidate
    except ValueError:
        pass
    return True


# ---------------------------------------------------------------------------
# Manifest helper
# ---------------------------------------------------------------------------


def _write_manifest_entry(manifest_path: Path, entry: dict) -> None:
    """Atomically append entry to the JSON list at manifest_path.

    Reads the existing list (or starts a new one), appends in memory, then
    writes back via a sibling .tmp file + Path.replace() — the same
    atomic-write idiom as scripts/fetch_calibration_text.py:146
    (tmp_path.replace(out_path), per Constitution Article IV Rule 1).
    """
    existing: list = []
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.append(entry)

    tmp_path = Path(str(manifest_path) + ".tmp")
    tmp_path.write_text(
        json.dumps(existing, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(manifest_path)


# ---------------------------------------------------------------------------
# Optuna objective factory
# ---------------------------------------------------------------------------


def _build_objective(
    gguf_out_dir: str,
    gguf_f16: str,
    archive_root: Path,
    text_path: str,
    llama_perplexity_bin: str,
    llama_cli_bin: str,
    repo_root: Path,
    n_gpu_layers: int = 0,
    extra_manifest_fields: dict[str, str] | None = None,
):
    """Return an Optuna objective closure for the GGUF quantisation search.

    Args:
        gguf_out_dir:  GGUF_OUT_DIR — where make quantize-gguf writes output.
        gguf_f16:      GGUF_F16_GGUF — the full-resolution source file
                       quantize-gguf reads back in. MUST be passed to the
                       `make quantize-gguf` subprocess call explicitly —
                       omitting it lets the Makefile's own MODEL/HF_PATH
                       defaults resolve GGUF_F16_GGUF silently, which is
                       wrong for any model other than the Makefile's
                       hardcoded default (found via live e2e testing,
                       2026-09-27 — see vault/discoveries/).
        archive_root:  Sibling directory for archived trial files and study.db.
        text_path:     Held-out text file for perplexity evaluation.
        llama_perplexity_bin: Path to the llama-perplexity binary.
        llama_cli_bin: Path to the llama-cli binary.
        repo_root:     Repository root; passed as cwd to subprocess.run so
                       the Makefile is found at the expected location.
        n_gpu_layers:  Layers to offload to GPU via llama.cpp's -ngl flag,
                       forwarded to both llama-perplexity and llama-cli.
                       0 (default) omits the flag (CPU-only).

    Returns:
        An objective function ``(trial) -> tuple[float, float]`` suitable
        for ``study.optimize(objective, ...)``.
    """
    manifest_path = archive_root / "manifest.json"

    def objective(trial: optuna.Trial) -> tuple[float, float]:
        # ---- suggest parameters ----
        quant: str = trial.suggest_categorical("GGUF_QUANT", GGUF_QUANT_CHOICES)
        calib_samples: int = trial.suggest_int("CALIB_TEXT_SAMPLES", 50, 100)

        # ---- run `make quantize-gguf` with ONE quant value ----
        # NEVER invoke `make convert-gguf` here — that would repeat the
        # expensive F16 conversion once per trial (FR-010).  We reuse the
        # existing F16 output produced by the one-time `make convert-gguf`
        # run that precedes this search.
        make_result = subprocess.run(
            [
                "make",
                "quantize-gguf",
                f"GGUF_QUANTS={quant}",
                f"CALIB_TEXT_SAMPLES={calib_samples}",
                f"GGUF_OUT_DIR={gguf_out_dir}",
                f"GGUF_F16_GGUF={gguf_f16}",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        if make_result.returncode != 0:
            raise RuntimeError(
                f"make quantize-gguf failed (exit {make_result.returncode}) "
                f"for GGUF_QUANTS={quant}, CALIB_TEXT_SAMPLES={calib_samples}.\n"
                f"stderr: {make_result.stderr[:500]!r}"
            )

        # ---- archive immediately (FR-009) ----
        # quantize-gguf's recipe runs `find "$(GGUF_OUT_DIR)" -maxdepth 1
        # -name 'model-*.gguf' ! -name "$(notdir $(GGUF_F16_GGUF))" -delete`
        # at the START of the NEXT trial's make call.  Copy the file out to
        # archive_root NOW, before that cleanup runs, so the artifact survives.
        # The naming pattern is confirmed from the Makefile recipe:
        #   "$(GGUF_OUT_DIR)/model-$$q.gguf"
        src_path = Path(gguf_out_dir) / f"model-{quant}.gguf"
        archived_path = archive_root / f"trial-{trial.number}.gguf"
        archive_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_path), str(archived_path))

        # ---- score: perplexity ----
        perplexity = eval_perplexity_gguf.compute_perplexity(
            str(archived_path),
            text_path,
            llama_perplexity_bin=llama_perplexity_bin,
            n_gpu_layers=n_gpu_layers,
        )

        # ---- score: refusal rate ----
        # The generate callback shells out to llama-cli against the archived
        # GGUF file.  llama-cli stdout is the completion text; we use
        # --no-display-prompt to suppress the prompt echo.  As a defensive
        # fallback we also strip the literal prompt prefix if llama-cli
        # echoes it despite the flag (older builds may not honour it).
        # Simplifying assumption: prompt text appears literally at the start
        # of stdout when echoed — may not hold for complex prompt templates
        # but is correct for llama-cli's default behaviour with -p.
        def generate(prompt: str) -> str:
            cli_cmd = [
                llama_cli_bin,
                "-m", str(archived_path),
                "-p", prompt,
                "-n", "100",
                "--no-display-prompt",
            ]
            if n_gpu_layers > 0:
                cli_cmd += ["-ngl", str(n_gpu_layers)]
            cli_result = subprocess.run(
                cli_cmd,
                capture_output=True,
                text=True,
                timeout=_LLAMA_CLI_TIMEOUT,
            )
            output = cli_result.stdout
            # Defensive: strip echoed prompt prefix if present.
            if output.startswith(prompt):
                output = output[len(prompt):]
            return output.strip()

        refusal_rate = eval_refusal_rate.compute_refusal_rate(
            generate=generate,
            n_prompts=N_REFUSAL_PROMPTS,
        )

        # ---- append manifest entry (atomic write) ----
        _write_manifest_entry(
            manifest_path,
            {
                "archive_path": str(archived_path),
                "calib_text_samples": calib_samples,
                "generated_at_utc": datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat(),
                "gguf_quant": quant,
                "perplexity": perplexity,
                "refusal_rate": refusal_rate,
                "trial_number": trial.number,
                **(extra_manifest_fields or {}),
            },
        )

        # ---- log to MLflow (both metrics independent; FR-007) ----
        # Uses the active experiment set by mlflow.set_experiment() in main().
        with mlflow.start_run():
            mlflow.log_params({
                "GGUF_QUANT": quant,
                "calib_text_samples": calib_samples,
            })
            mlflow.log_metrics({
                "perplexity": perplexity,
                "refusal_rate": refusal_rate,
            })
            mlflow.set_tag("trial_number", str(trial.number))

        # Both "minimize" (data-model.md). CAUTION: compute_refusal_rate()
        # returns the fraction of prompts REFUSED (higher = more censored) --
        # minimize it directly, do NOT invert to "1 - rate" (that tells the
        # search to maximize refusals, backwards from this project's
        # decensoring goal -- see the identical fix in optimize_mlx.py).
        return perplexity, refusal_rate

    return objective


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse arguments, set up MLflow + Optuna, and run the GGUF search."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        required=True,
        help="Total number of Optuna trials to run (including any that fail).",
    )
    parser.add_argument(
        "--gguf-f16",
        required=True,
        help=(
            "Path to the full-resolution F16 GGUF file produced by "
            "`make convert-gguf` (GGUF_F16_GGUF).  Required; never re-run "
            "`make convert-gguf` from this script — FR-010."
        ),
    )
    parser.add_argument(
        "--text-path",
        default="calibration-text.txt",
        help=(
            "Held-out plain-text file for perplexity evaluation.  "
            "Default: calibration-text.txt (produced by `make calibration-text`)."
        ),
    )
    parser.add_argument(
        "--gguf-out-dir",
        default=None,
        help=(
            "GGUF output directory (GGUF_OUT_DIR) where `make quantize-gguf` "
            "writes model-<quant>.gguf files.  Default: parent directory of "
            "--gguf-f16."
        ),
    )
    parser.add_argument(
        "--llama-perplexity-bin",
        default="ik_llama.cpp/build/bin/llama-perplexity",
        help="Path to the llama-perplexity binary (LLAMA_PERPLEXITY).",
    )
    parser.add_argument(
        "--llama-cli-bin",
        default="ik_llama.cpp/build/bin/llama-cli",
        help="Path to the llama-cli binary (LLAMA_CLI).",
    )
    parser.add_argument(
        "--n-gpu-layers",
        type=int,
        default=0,
        help=(
            "Layers to offload to GPU via llama.cpp's -ngl flag, forwarded "
            "to both llama-perplexity and llama-cli. 0 (default) omits the "
            "flag (CPU-only). Mirrors the Makefile's GGML_CUDA/LLAMA_NGL "
            "pattern already used by quantize-gguf's llama-imatrix call."
        ),
    )
    parser.add_argument(
        "--tracking-uri",
        default=None,
        help=(
            "MLflow tracking URI.  When provided, sets MLFLOW_TRACKING_URI in "
            "the process environment so require_tracking_uri() picks it up.  "
            "Credentials (MLFLOW_TRACKING_USERNAME/PASSWORD/TOKEN) are never "
            "accepted here — set them in the environment directly (FR-014)."
        ),
    )
    parser.add_argument(
        "--experiment-prefix",
        default="wellspring",
        help="Prefix for the MLflow experiment name.  Default: wellspring.",
    )
    parser.add_argument(
        "--extra-manifest-field",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Extra key=value field merged into every trial's manifest.json "
            "entry (repeatable). Matches write_manifest.py's --field "
            "convention. Omitted by default — an orchestrating Metaflow run "
            "(specs/002-metaflow-migration, FR-008/SC-004) passes run_id/"
            "flow_name here; the Makefile never passes this flag."
        ),
    )
    args = parser.parse_args()

    extra_manifest_fields: dict[str, str] = {}
    for item in args.extra_manifest_field:
        if "=" not in item:
            print(
                f"ERROR: --extra-manifest-field must be KEY=VALUE, got {item!r}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        key, _, value = item.partition("=")
        extra_manifest_fields[key] = value

    # ---- tracking URI: fail fast before any expensive work ----
    if args.tracking_uri:
        os.environ["MLFLOW_TRACKING_URI"] = args.tracking_uri
    tracking_uri = require_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)

    # ---- derive paths ----
    gguf_f16 = Path(args.gguf_f16)
    gguf_out_dir = args.gguf_out_dir if args.gguf_out_dir else str(gguf_f16.parent)
    archive_root = Path(f"{gguf_out_dir}-gguf-optimize-archive")

    # Safety: archive_root must not be inside gguf_out_dir, or vice versa.
    # If it were inside gguf_out_dir, quantize-gguf's `find ... -delete`
    # cleanup would erase the archived trial files (FR-009).
    if not _path_is_safe(archive_root, Path(gguf_out_dir)):
        print(
            f"ERROR: archive_root {str(archive_root)!r} is an ancestor or descendant "
            f"of gguf_out_dir {gguf_out_dir!r}.  The archive must be a sibling "
            "directory so quantize-gguf's cleanup never touches it (FR-009).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    archive_root.mkdir(parents=True, exist_ok=True)

    # ---- MLflow experiment ----
    experiment_name = f"{args.experiment_prefix}-gguf-quant"
    mlflow.set_experiment(experiment_name)

    # ---- Optuna study ----
    # study_name + storage path together uniquely identify the study so
    # load_if_exists=True correctly resumes the *same* search (FR-008).
    study = optuna.create_study(
        study_name="optimize-gguf",
        storage=f"sqlite:///{archive_root}/study.db",
        sampler=optuna.samplers.NSGAIISampler(seed=_SAMPLER_SEED),
        directions=["minimize", "minimize"],
        load_if_exists=True,
    )

    repo_root = Path(__file__).resolve().parent.parent
    objective = _build_objective(
        gguf_out_dir=gguf_out_dir,
        gguf_f16=str(gguf_f16),
        archive_root=archive_root,
        text_path=args.text_path,
        llama_perplexity_bin=args.llama_perplexity_bin,
        llama_cli_bin=args.llama_cli_bin,
        repo_root=repo_root,
        n_gpu_layers=args.n_gpu_layers,
        extra_manifest_fields=extra_manifest_fields,
    )

    # catch=(Exception,) marks a failed trial FAIL and continues — it does
    # NOT catch SystemExit/KeyboardInterrupt (both inherit BaseException, not
    # Exception) so the operator can still Ctrl-C to abort (FR-016).
    study.optimize(objective, n_trials=args.n_trials, catch=(Exception,))


if __name__ == "__main__":
    main()
