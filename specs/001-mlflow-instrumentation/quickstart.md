# Quickstart: MLflow Experiment Tracking & Quantization Optimization

Validates that this feature works end-to-end against tiny fixtures — never
the real ~72GB production checkpoint (matching this project's existing
`make dev-abliterate`/dev-cycle convention, see `README.md`'s "Dev cycle
(cheap iteration)" section).

## Prerequisites

```sh
make setup                     # installs mlflow/optuna/mlx-lm alongside existing deps
export MLFLOW_TRACKING_URI="file://$(pwd)/.mlflow-qa"   # local, no server required for this walkthrough
make dev-abliterate-e2e         # produces a real, tiny checkpoint (DEV_MODEL default: TinyLlama-1.1B)
```

## Scenario 1 — See what the decensoring search actually did (User Story 1, P1)

```sh
make log-abliteration-mlflow MODEL="$(DEV_MODEL)"
python -c "
import mlflow
mlflow.set_tracking_uri('file://$(pwd)/.mlflow-qa')
runs = mlflow.search_runs(experiment_names=['wellspring-abliteration'])
assert len(runs) > 0, 'expected at least one trial run'
print(f'{len(runs)} trial(s) recorded')
"
```

**Expected**: prints a positive trial count; matches spec Acceptance
Scenario 1.1.

**Idempotency check** (Acceptance Scenario 1.2 / SC-005):

```sh
make log-abliteration-mlflow MODEL="$(DEV_MODEL)"   # re-run, same journal
python -c "
import mlflow
mlflow.set_tracking_uri('file://$(pwd)/.mlflow-qa')
print(len(mlflow.search_runs(experiment_names=['wellspring-abliteration'])))
"
```

**Expected**: identical row count to the first run — no duplicates.

## Scenario 2 — Automated MLX compression search (User Story 2, P2)

*macOS/Apple Silicon only (Constitution Article III Rule 4).*

```sh
make optimize-mlx N_TRIALS_MLX=2 HF_PATH=outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic
python -c "
import mlflow
mlflow.set_tracking_uri('file://$(pwd)/.mlflow-qa')
runs = mlflow.search_runs(experiment_names=['wellspring-mlx-quant'])
assert len(runs) == 2
print('perplexity + refusal_rate columns present:',
      'perplexity' in runs.columns and 'refusal_rate' in runs.columns)
"
```

**Expected**: 2 rows, both metric columns present and independently
non-null (FR-007 — never collapsed into one score).

**Resumability check** (Acceptance Scenario 2.2 / SC-003):

```sh
make optimize-mlx N_TRIALS_MLX=2 HF_PATH=outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic  # same command again
```

**Expected**: reaches trial index 4 total (resumes, doesn't restart from 0).

**Archive-survives-cleanup check** (Acceptance Scenario 2.4 / SC-004):

```sh
ls outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic-mlx-optimize-archive/*.mlx 2>/dev/null | wc -l
make convert-mlx HF_PATH=outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic   # unrelated, routine export
ls outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic-mlx-optimize-archive/*.mlx 2>/dev/null | wc -l
```

**Expected**: both counts identical — the unrelated `convert-mlx` call
never touches the archive.

## Scenario 3 — Automated GGUF compression search (User Story 3, P3)

```sh
make convert-gguf HF_PATH=outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic   # one-time F16 conversion
make optimize-gguf N_TRIALS_GGUF=2
```

**Expected**: 2 rows in `wellspring-gguf-quant`; `convert-gguf` never
re-invoked during the search (verify via absence of a second, later
"Converting to GGUF" log line — FR-010, Acceptance Scenario 3.2).

## Scenario 4 — Compute-topology-aware concurrency (FR-015, SC-006)

```sh
# Default: sequential on shared compute
time make optimize N_TRIALS_MLX=1 N_TRIALS_GGUF=1
# Explicit opt-in: concurrent on dedicated compute
time make optimize N_TRIALS_MLX=1 N_TRIALS_GGUF=1 OPTIMIZE_PARALLEL=1
```

**Expected**: with `OPTIMIZE_PARALLEL=0` (default), log timestamps show the
GGUF search's first line strictly after the MLX search's last line
(non-overlapping). With `OPTIMIZE_PARALLEL=1`, log lines from both
searches interleave (overlapping wall-clock windows).

## Scenario 5 — Credential handling never leaks (FR-014)

```sh
grep -rn "tracking-username\|tracking-password\|tracking-token" scripts/*.py
```

**Expected**: zero matches — no such CLI flag exists in any new script.

```sh
grep -rn "MLFLOW_TRACKING_PASSWORD\|MLFLOW_TRACKING_TOKEN" scripts/*.py Makefile
```

**Expected**: zero matches inside this project's own code (these variables
are read by the `mlflow` library itself, never by this project's scripts
directly — research.md R2).

## Cleanup

```sh
rm -rf .mlflow-qa outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic*
```
