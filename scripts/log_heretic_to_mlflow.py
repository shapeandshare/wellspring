#!/usr/bin/env python3
"""Log Heretic's Optuna abliteration journal to MLflow.

Reads Heretic's own Optuna journal file (written by ``make abliterate`` or
``make dev-abliterate``) and publishes each completed trial as a run in an
MLflow experiment, tagged for idempotent re-recording.

Journal path can be specified either directly (``--journal-file``) or
derived from the model name and checkpoint directory exactly as Heretic
derives it (``--model`` + ``--checkpoint-dir``).

Exit codes:
  0   Every completed trial is now represented in MLflow (re-running
      against the same journal produces no new rows — idempotent).
  1   The journal file was not found, the study could not be loaded, or
      MLFLOW_TRACKING_URI is unset and no --tracking-uri was given.

Never accepts credential-shaped flags (--tracking-username,
--tracking-password, --tracking-token) — FR-014.  Credentials flow
exclusively through environment variables read by the mlflow library
itself.

Discovery note — scores shape:
    The data-model spec's ``{"name", "score": {"value", "baseline"}}``
    list shape for ``trial.user_attrs["scores"]`` does NOT exist in
    Heretic's source (vendor/heretic/src/heretic/main.py lines 641-644).
    Heretic stores individual user attributes:
        kl_divergence (float), refusals (int),
        base_refusals (int), n_bad_prompts (int).
    This script maps them to the naming convention from the spec:
        kl_divergence  → ``kl_divergence_value``
        refusals       → ``refusals_value``
        base_refusals  → ``refusals_baseline_value``
        n_bad_prompts  → ``n_bad_prompts``
"""

import argparse
import hashlib
import sys
from pathlib import Path

import mlflow
import optuna
import optuna.storages
import optuna.storages.journal
import optuna.trial

import _mlflow_env


def _sanitize_model_name(model: str) -> str:
    """Replicate Heretic's journal filename sanitization exactly.

    Source: vendor/heretic/src/heretic/main.py lines 292-295::

        "".join([(c if (c.isalnum() or c in ["_", "-"]) else "--")
                 for c in settings.model])

    Every character that is not alphanumeric, ``_``, or ``-`` is replaced
    with ``--`` (two hyphens).  This matches what heretic itself writes, so
    ``--model`` + ``--checkpoint-dir`` resolve to the correct journal path.
    """
    return "".join(
        [(c if (c.isalnum() or c in ["_", "-"]) else "--") for c in model]
    )


def main() -> int:
    """Log completed Heretic trials to MLflow.  Returns 0 on success."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--journal-file",
        metavar="PATH",
        help="Direct path to Heretic's Optuna journal file (.jsonl)",
    )
    source_group.add_argument(
        "--model",
        metavar="NAME",
        help=(
            "HF model name — used to derive the journal filename, matching "
            "Heretic's own sanitization logic (requires --checkpoint-dir)"
        ),
    )

    parser.add_argument(
        "--checkpoint-dir",
        metavar="DIR",
        help="Heretic's study checkpoint directory (required when --model is used)",
    )
    parser.add_argument(
        "--tracking-uri",
        metavar="URI",
        help=(
            "MLflow tracking URI (optional override; default: reads "
            "MLFLOW_TRACKING_URI from the environment via _mlflow_env)"
        ),
    )
    parser.add_argument(
        "--experiment-prefix",
        default="wellspring",
        metavar="PREFIX",
        help=(
            "Prefix for the MLflow experiment name "
            "(default: %(default)s — experiment = '<prefix>-abliteration')"
        ),
    )

    args = parser.parse_args()

    # --model requires --checkpoint-dir
    if args.model is not None and not args.checkpoint_dir:
        parser.error("--checkpoint-dir is required when --model is given")

    # Resolve journal file path
    if args.journal_file is not None:
        journal_path = Path(args.journal_file)
    else:
        sanitized = _sanitize_model_name(args.model)
        journal_path = Path(args.checkpoint_dir) / f"{sanitized}.jsonl"

    if not journal_path.exists():
        print(
            f"ERROR: journal file not found: {journal_path}",
            file=sys.stderr,
        )
        return 1

    # Compute journal_identity from the canonical resolved path string.
    # IMPORTANT: hash the PATH, not the file's byte content — the path is
    # stable across re-recordings; the content grows as Heretic appends
    # trials.  See data-model.md's "Decensoring run Identity" rule.
    journal_identity = hashlib.sha256(
        str(journal_path.resolve()).encode()
    ).hexdigest()[:16]

    # Resolve tracking URI (CLI override or env var via require_tracking_uri)
    tracking_uri = args.tracking_uri or _mlflow_env.require_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)

    experiment_name = f"{args.experiment_prefix}-abliteration"
    mlflow.set_experiment(experiment_name)

    # Open the Optuna journal using Heretic's own storage stack
    # (vendor/heretic/src/heretic/main.py lines 298-300)
    try:
        backend = optuna.storages.journal.JournalFileBackend(str(journal_path))
        storage = optuna.storages.JournalStorage(backend)
        study = optuna.load_study(study_name="heretic", storage=storage)
    except Exception as exc:  # noqa: BLE001
        print(
            f"ERROR: could not load study from {journal_path}: {exc}",
            file=sys.stderr,
        )
        return 1

    completed_trials = [
        t
        for t in study.get_trials(deepcopy=False)
        if t.state == optuna.trial.TrialState.COMPLETE
    ]

    print(f"==> Journal: {journal_path}")
    print(f"==> journal_identity: {journal_identity}")
    print(f"==> Experiment: {experiment_name}")
    print(f"==> Found {len(completed_trials)} completed trial(s) in journal")

    n_logged = 0
    n_skipped = 0

    for trial in completed_trials:
        # Idempotency check (FR-002, SC-005): search for an existing run
        # already tagged with this exact (journal_identity, trial_number)
        # pair before creating a new one.
        filter_string = (
            f"tags.journal_identity = '{journal_identity}' "
            f"and tags.trial_number = '{trial.number}'"
        )
        existing = mlflow.search_runs(
            experiment_names=[experiment_name],
            filter_string=filter_string,
            max_results=1,
        )

        if not existing.empty:
            print(
                f"  [SKIP] Trial {trial.number} already logged — "
                "skipping (idempotent)"
            )
            n_skipped += 1
            continue

        # Create a new MLflow run for this trial
        with mlflow.start_run():
            mlflow.set_tags(
                {
                    "journal_identity": journal_identity,
                    "trial_number": str(trial.number),
                }
            )

            # Log Optuna params as MLflow params (flat key/value)
            if trial.params:
                mlflow.log_params(trial.params)

            # Log Heretic's user_attrs as MLflow metrics.
            #
            # Heretic does NOT write a "scores" list — it writes individual
            # attrs (main.py 641-644).  We apply the spec's
            # {name}_value / {name}_baseline_value naming convention where
            # natural pairs exist:
            #   kl_divergence  → kl_divergence_value  (no baseline available)
            #   refusals       → refusals_value
            #   base_refusals  → refusals_baseline_value
            #   n_bad_prompts  → n_bad_prompts  (context; no baseline)
            attrs = trial.user_attrs
            metrics: dict[str, float] = {}
            if "kl_divergence" in attrs:
                metrics["kl_divergence_value"] = float(attrs["kl_divergence"])
            if "refusals" in attrs:
                metrics["refusals_value"] = float(attrs["refusals"])
            if "base_refusals" in attrs:
                metrics["refusals_baseline_value"] = float(attrs["base_refusals"])
            if "n_bad_prompts" in attrs:
                metrics["n_bad_prompts"] = float(attrs["n_bad_prompts"])

            if metrics:
                mlflow.log_metrics(metrics)

        print(f"  [LOG]  Trial {trial.number} → MLflow run created")
        n_logged += 1

    print(
        f"==> Done: {n_logged} trial(s) logged, "
        f"{n_skipped} skipped (already present)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
