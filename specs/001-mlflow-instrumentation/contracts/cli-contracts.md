# CLI Contracts: MLflow Experiment Tracking & Quantization Optimization

This project exposes no HTTP/RPC API — its interface is `make` targets
(Constitution Article VII) invoking Python CLI scripts. Contracts below
document each new script's command-line surface and exit-code behavior,
the "interface" a project of this shape actually has.

## `scripts/log_heretic_to_mlflow.py`

**Invoked by**: `make log-abliteration-mlflow`

```text
python scripts/log_heretic_to_mlflow.py --journal-file <path> [--tracking-uri <uri>]
python scripts/log_heretic_to_mlflow.py --model <name> --checkpoint-dir <dir> [--tracking-uri <uri>]
```

| Exit code | Meaning |
|---|---|
| 0 | Every trial in the journal is now represented in MLflow (idempotent — re-running produces no new rows if nothing changed) |
| non-zero | `--journal-file` (or the derived path) doesn't exist; `MLFLOW_TRACKING_URI` unset and no `--tracking-uri` given (FR satisfied via research.md R2 — env var is the only credential channel, but the *URI* itself may be passed explicitly per the existing plan's Todo 1 design) |

**Never accepts**: any flag shaped like `--tracking-username`,
`--tracking-password`, `--tracking-token`, or any other credential value
(FR-014, research.md R2).

## `scripts/optimize_mlx.py`

**Invoked by**: `make optimize-mlx N_TRIALS_MLX=<n> [OPTIMIZE_PARALLEL=0|1]`

```text
python scripts/optimize_mlx.py --n-trials <n> --hf-path <checkpoint-dir>
```

| Exit code | Meaning |
|---|---|
| 0 | Study ran to completion (or resumed and reached the target trial count) |
| non-zero | `--hf-path` doesn't exist; `MLFLOW_TRACKING_URI` unset; VLM checkpoint + unsupported MLX perplexity path (FR-011 — raises `MlxPerplexityUnsupportedError`, not a generic crash) |

**Resumability** (FR-008): re-invoking with the same `archive_root` (derived
from `MLX_OUT_DIR`) and the same `--n-trials` continues the persistent
Optuna study via `load_if_exists=True` rather than restarting.

**Attempt-budget accounting** (FR-016): a trial that fails (invalid
setting combination, tool crash) is caught via Optuna's `catch=` mechanism,
marked `FAIL`, and **still counts** toward `--n-trials` — the script does
not loop indefinitely trying to collect N *successful* trials.

## `scripts/optimize_gguf.py`

**Invoked by**: `make optimize-gguf N_TRIALS_GGUF=<n> [OPTIMIZE_PARALLEL=0|1]`

```text
python scripts/optimize_gguf.py --n-trials <n> --gguf-f16 <path>
```

Same exit-code/resumability/attempt-budget contract as `optimize_mlx.py`
above, substituting `--gguf-f16` (the one-time F16 conversion output,
FR-010) for `--hf-path`.

## `scripts/eval_refusal_rate.py`

**Not directly invoked via `make`** — imported as a library function by
`optimize_mlx.py`/`optimize_gguf.py` and `log_heretic_to_mlflow.py`'s test
suite. Its public contract is the function signature, not a CLI:

```python
def compute_refusal_rate(
    generate: Callable[[str], str],
    n_prompts: int = 100,
) -> float:
    """Returns a value in [0, 1]. Raises ValueError if n_prompts <= 0."""
```

## `scripts/eval_perplexity_gguf.py` / `scripts/eval_perplexity_mlx.py`

Also library functions (imported by the two `optimize_*.py` scripts), each
exposing a `compute_perplexity(...) -> float` contract wrapping
`llama-perplexity` (GGUF) or the `mlx_lm` perplexity API confirmed by
research.md's feasibility spike (MLX) — see the existing engineering plan's
Todos 3/4 for the exact wrapped-binary/API contract, unchanged by this
plan.

## `make optimize` (the combined, topology-aware target)

```text
make optimize N_TRIALS_MLX=<n> N_TRIALS_GGUF=<n> [OPTIMIZE_PARALLEL=0|1] MLFLOW_TRACKING_URI=<uri>
```

| `OPTIMIZE_PARALLEL` | Behavior |
|---|---|
| `0` (default) | `optimize-mlx` runs to completion, **then** `optimize-gguf` starts (sequential sub-make, matching `gguf`'s existing idiom) — satisfies FR-015's shared-compute default and SC-006's "second search does not begin until the first finishes" |
| `1` | Both targets launch concurrently (`$(MAKE) -j2` or backgrounded sub-makes) — satisfies FR-015's dedicated-compute allowance and SC-006's "both searches make progress at the same time" |

This variable is never auto-detected (research.md R1) — it is an explicit,
operator-supplied signal about the actual compute topology in play.
