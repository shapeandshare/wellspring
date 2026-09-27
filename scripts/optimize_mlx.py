#!/usr/bin/env python3
"""Multi-objective quantization search for MLX checkpoints via Optuna + MLflow.

Runs a persistent, resumable Optuna study that searches over MLX quantization
hyperparameters (Q_BITS, Q_GROUP_SIZE, QUANT_METHOD, CALIB_SAMPLES) by:

  1. Invoking ``make convert-mlx`` with each trial's suggested parameters.
  2. Archiving the resulting MLX directory to ``<archive_root>/trial-<n>/``
     immediately after conversion succeeds (FR-009 — before the next trial's
     make invocation overwrites MLX_OUT_DIR).
  3. Scoring the archived checkpoint with eval_perplexity_mlx.compute_perplexity
     and eval_refusal_rate.compute_refusal_rate.
  4. Logging both metrics independently to MLflow under experiment
     ``<experiment_prefix>-mlx-quant`` (never combined — FR-007).
  5. Returning ``(perplexity, refusal_rate)`` as the two objectives to
     minimize.  ``eval_refusal_rate.compute_refusal_rate()`` returns the
     *fraction of harmful prompts that elicit a refusal* — higher means MORE
     censored (worse for decensoring). Minimizing it directly therefore
     correctly favors trials that refuse LESS, which is the decensoring goal.
     (Do not confuse this with a "refusal-removal rate" — a different,
     higher-is-better quantity this codebase does not compute.)

Usage
-----
::

    python scripts/optimize_mlx.py \\
        --n-trials 15 \\
        --hf-path outputs/MyModel-heretic \\
        [--mlx-out-dir outputs/MyModel-heretic-mlx] \\
        [--text-path calibration-text.txt] \\
        [--tracking-uri sqlite:///mlflow.db] \\
        [--experiment-prefix wellspring] \\
        [--n-refusal-prompts 10]

Resumability (FR-008): re-invoking with the same ``MLX_OUT_DIR`` continues
the existing Optuna study via ``load_if_exists=True``; does not restart.

Failed trials (FR-016): a trial that raises inside the objective is caught by
Optuna's ``catch=`` mechanism, marked ``FAIL``, and still counts toward
``--n-trials``.  The study never loops indefinitely to collect N *successful*
trials.

Archive safety (FR-009): ``archive_root`` is derived exclusively from
``MLX_OUT_DIR`` (never from ``HF_PATH``), and a startup guard ensures it never
resolves to an ancestor or descendant of ``MLX_OUT_DIR`` — preventing the
archive from being destroyed by convert-mlx's own ``rm -rf`` cleanup.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

import mlflow
import optuna

from _mlflow_env import require_tracking_uri
from eval_perplexity_mlx import compute_perplexity
from eval_refusal_rate import compute_refusal_rate
from write_manifest import git_commit as _git_commit, git_dirty as _git_dirty

# Suppress Optuna's per-trial log spam in batch / CI contexts.
optuna.logging.set_verbosity(optuna.logging.WARNING)

REPO_ROOT = Path(__file__).resolve().parent.parent
STUDY_NAME = "optimize-mlx"

# Fixed for deterministic tests (matches optimize_gguf.py's convention) --
# unseeded NSGA-II can rarely draw identical categorical params across 2
# early trials, making SC-002's distinctness assertion flaky.
_SAMPLER_SEED = 42


# ---------------------------------------------------------------------------
# Path safety helpers
# ---------------------------------------------------------------------------

def _is_ancestor_or_descendant(path_a: Path, path_b: Path) -> bool:
    """Return True if path_a and path_b are in an ancestor/descendant (or equal) relationship.

    Uses ``Path.relative_to()`` — the stdlib idiom for parent/child detection.
    Resolves both paths to absolute canonical forms before comparison.

    Args:
        path_a: First path (need not exist on disk).
        path_b: Second path (need not exist on disk).

    Returns:
        True if either path is an ancestor, descendant, or equal to the other.
        False if they are siblings or otherwise unrelated.

    Examples:
        >>> _is_ancestor_or_descendant(Path("/a/b"), Path("/a"))       # parent
        True
        >>> _is_ancestor_or_descendant(Path("/a/b"), Path("/a/b/c"))   # child
        True
        >>> _is_ancestor_or_descendant(Path("/a/b"), Path("/a/b-ext")) # sibling
        False
    """
    a = path_a.resolve()
    b = path_b.resolve()
    if a == b:
        return True
    try:
        b.relative_to(a)  # b is inside a (b is descendant of a)
        return True
    except ValueError:
        pass
    try:
        a.relative_to(b)  # a is inside b (a is descendant of b)
        return True
    except ValueError:
        pass
    return False


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def _append_manifest(manifest_path: Path, entry: dict) -> None:
    if manifest_path.exists():
        entries: list = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        entries = []
    entries.append(entry)
    tmp = Path(str(manifest_path) + ".tmp")
    tmp.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    tmp.replace(manifest_path)


def _update_manifest_entry(manifest_path: Path, trial_number: int, updates: dict) -> None:
    entries: list = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in entries:
        if entry.get("trial_number") == trial_number:
            entry.update(updates)
            break
    tmp = Path(str(manifest_path) + ".tmp")
    tmp.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    tmp.replace(manifest_path)


# ---------------------------------------------------------------------------
# Generate-callback factory (lazy model load for refusal-rate scoring)
# ---------------------------------------------------------------------------

def _make_generate_fn(archived_path: str) -> Callable[[str], str]:
    """Return a lazy generate callback suitable for compute_refusal_rate.

    The MLX model is loaded on the *first call* to the returned function, not at
    construction time.  This decouples object creation from I/O so that tests
    which mock ``compute_refusal_rate`` (and therefore never invoke the callback)
    do not trigger a real model load against a non-existent checkpoint.

    Real-fixture correction (2026-09-25): uses ``mlx_vlm`` (not ``mlx_lm``)
    throughout — every ``make convert-mlx`` output is an ``mlx_vlm``-format
    checkpoint by construction (``language_model.*``-prefixed weights; see
    eval_perplexity_mlx.py's module docstring for the full finding).
    ``mlx_lm.utils.load()``/``mlx_lm.generate.generate()`` fail on these
    checkpoints unconditionally. Verified against a real TinyLlama
    checkpoint: ``mlx_vlm.generate(model, processor, prompt, image=None,
    max_tokens=...)`` (confirmed signature — ``image`` defaults to ``None``
    for text-only generation) returns a ``GenerationResult`` with a
    ``.text`` attribute holding the generated string.

    Args:
        archived_path: Path to the archived MLX checkpoint directory.

    Returns:
        A callable ``(str) -> str`` that generates up to 100 tokens per prompt,
        reusing the loaded model across all calls (loaded once per trial).
    """
    import mlx_vlm as _mlx_vlm

    _cache: dict = {}

    def generate(prompt: str) -> str:
        if "model" not in _cache:
            _cache["model"], _cache["processor"] = _mlx_vlm.load(archived_path)
        result = _mlx_vlm.generate(
            _cache["model"],
            _cache["processor"],
            prompt,
            max_tokens=100,
            verbose=False,
        )
        return result.text

    return generate


# ---------------------------------------------------------------------------
# Core study runner (callable independently for testing)
# ---------------------------------------------------------------------------

def run_study(
    n_trials: int,
    hf_path: str,
    mlx_out_dir: str,
    text_path: str,
    tracking_uri: str,
    experiment_prefix: str = "wellspring",
    n_refusal_prompts: int = 10,
    calibration: str = "multimodal",
    extra_manifest_fields: dict[str, str] | None = None,
    _archive_root_override: str | None = None,
) -> None:
    if _archive_root_override is not None:
        archive_root = Path(_archive_root_override).resolve()
    else:
        archive_root = Path(f"{mlx_out_dir}-optimize-archive").resolve()

    mlx_out = Path(mlx_out_dir).resolve()

    if _is_ancestor_or_descendant(mlx_out, archive_root):
        print(
            f"ERROR: archive_root {str(archive_root)!r} resolves to an ancestor or "
            f"descendant of mlx_out_dir {str(mlx_out)!r}. "
            "The archive must be a sibling path so that make convert-mlx's own "
            "rm -rf cleanup never destroys archived trial artifacts.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    archive_root.mkdir(parents=True, exist_ok=True)
    manifest_path = archive_root / "manifest.json"
    storage_url = f"sqlite:///{archive_root}/study.db"

    mlflow.set_tracking_uri(tracking_uri)
    experiment_name = f"{experiment_prefix}-mlx-quant"
    mlflow.set_experiment(experiment_name)
    experiment = mlflow.get_experiment_by_name(experiment_name)
    assert experiment is not None, (
        f"mlflow.set_experiment({experiment_name!r}) did not create the experiment"
    )

    study = optuna.create_study(
        study_name=STUDY_NAME,
        storage=storage_url,
        sampler=optuna.samplers.NSGAIISampler(seed=_SAMPLER_SEED),
        directions=["minimize", "minimize"],
        load_if_exists=True,
    )

    def objective(trial: optuna.Trial) -> tuple[float, float]:
        q_bits: int = trial.suggest_categorical("Q_BITS", [4, 8])
        q_group_size: int = trial.suggest_categorical("Q_GROUP_SIZE", [32, 64, 128])
        quant_method: str = trial.suggest_categorical("QUANT_METHOD", ["awq", "rtn"])

        calib_samples: int | None = None
        if quant_method == "awq":
            calib_samples = trial.suggest_int("CALIB_SAMPLES", 16, 64)
            calib_result = subprocess.run(
                ["make", "calibration-data", f"CALIB_SAMPLES={calib_samples}"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            if calib_result.returncode != 0:
                raise RuntimeError(
                    f"make calibration-data returned {calib_result.returncode} "
                    f"for trial {trial.number}.\nstderr: {calib_result.stderr}"
                )

        result = subprocess.run(
            [
                "make", "convert-mlx",
                f"HF_PATH={hf_path}",
                f"MLX_OUT_DIR={mlx_out_dir}",
                f"Q_BITS={q_bits}",
                f"Q_GROUP_SIZE={q_group_size}",
                f"QUANT_METHOD={quant_method}",
                f"CALIBRATION={calibration}",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"make convert-mlx returned {result.returncode} "
                f"for trial {trial.number}.\nstderr: {result.stderr}"
            )

        archived_path = archive_root / f"trial-{trial.number}"
        shutil.copytree(mlx_out_dir, str(archived_path))

        _append_manifest(
            manifest_path,
            {
                "trial_number": trial.number,
                "archive_path": str(archived_path),
                "params": {
                    "Q_BITS": q_bits,
                    "Q_GROUP_SIZE": q_group_size,
                    "QUANT_METHOD": quant_method,
                    **({"CALIB_SAMPLES": calib_samples} if calib_samples is not None else {}),
                },
                "wellspring_commit": _git_commit(str(REPO_ROOT)),
                "wellspring_dirty": _git_dirty(str(REPO_ROOT)),
                "perplexity": None,
                "refusal_rate": None,
                **(extra_manifest_fields or {}),
            },
        )

        perplexity: float = compute_perplexity(str(archived_path), text_path)
        generate_fn = _make_generate_fn(str(archived_path))
        refusal_rate: float = compute_refusal_rate(
            generate_fn, n_prompts=n_refusal_prompts
        )

        _update_manifest_entry(
            manifest_path,
            trial.number,
            {"perplexity": perplexity, "refusal_rate": refusal_rate},
        )

        with mlflow.start_run(experiment_id=experiment.experiment_id):
            mlflow.log_params(
                {
                    "Q_BITS": q_bits,
                    "Q_GROUP_SIZE": q_group_size,
                    "QUANT_METHOD": quant_method,
                    **({"CALIB_SAMPLES": calib_samples} if calib_samples is not None else {}),
                }
            )
            mlflow.log_metrics(
                {
                    "perplexity": perplexity,
                    "refusal_rate": refusal_rate,
                }
            )
            mlflow.set_tag("trial_number", str(trial.number))

        return float(perplexity), float(refusal_rate)

    study.optimize(objective, n_trials=n_trials, catch=(Exception,))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        required=True,
        help="Number of Optuna trials to run (or resume to).",
    )
    parser.add_argument(
        "--hf-path",
        required=True,
        help="Path to the Heretic-exported HF checkpoint (HF_PATH for make convert-mlx).",
    )
    parser.add_argument(
        "--mlx-out-dir",
        default=None,
        help=(
            "MLX output directory (MLX_OUT_DIR for make convert-mlx). "
            "Defaults to <hf-path>-mlx, matching the Makefile default "
            "(MLX_OUT_DIR ?= $(HF_PATH)-mlx)."
        ),
    )
    parser.add_argument(
        "--text-path",
        default="calibration-text.txt",
        help="Path to plain-text corpus for perplexity scoring (default: calibration-text.txt).",
    )
    parser.add_argument(
        "--tracking-uri",
        default=None,
        help=(
            "MLflow tracking URI. If provided, sets MLFLOW_TRACKING_URI in the "
            "current process before reading it back. Credentials "
            "(MLFLOW_TRACKING_USERNAME / PASSWORD / TOKEN) must be set as "
            "environment variables — never as CLI flags (FR-014)."
        ),
    )
    parser.add_argument(
        "--experiment-prefix",
        default="wellspring",
        help="Prefix for the MLflow experiment name. Default: wellspring.",
    )
    parser.add_argument(
        "--n-refusal-prompts",
        type=int,
        default=10,
        help="Number of harmful prompts for refusal-rate scoring per trial (default: 10).",
    )
    parser.add_argument(
        "--calibration",
        default="multimodal",
        choices=["multimodal", "text"],
        help="MLX calibration mode passed to make convert-mlx (default: multimodal).",
    )
    args = parser.parse_args()

    if args.tracking_uri:
        os.environ["MLFLOW_TRACKING_URI"] = args.tracking_uri
    tracking_uri = require_tracking_uri()

    mlx_out_dir = args.mlx_out_dir if args.mlx_out_dir else f"{args.hf_path}-mlx"

    run_study(
        n_trials=args.n_trials,
        hf_path=args.hf_path,
        mlx_out_dir=mlx_out_dir,
        text_path=args.text_path,
        tracking_uri=tracking_uri,
        experiment_prefix=args.experiment_prefix,
        n_refusal_prompts=args.n_refusal_prompts,
        calibration=args.calibration,
    )


if __name__ == "__main__":
    main()
