# Contract: Makefile Entry Point (default/dev-cycle, FR-001a(a))

Every existing Makefile target that today drives a pipeline stage
directly (via `heretic`, `python scripts/log_heretic_to_mlflow.py`,
`python scripts/optimize_mlx.py`, `python scripts/optimize_gguf.py`) is
rewritten so its recipe instead invokes `python flow.py run --only_step
<stage> ...` — but the target's own name, `.PHONY` declaration, `make
help` line, and README.md documentation row are **unchanged**. This is
the "default/convenient, dev-cycle-oriented" entry point FR-001a(a)
requires to remain first-class, not merely tolerated.

**Flag naming**: `--only_step` (underscore), not `--only-step` — matches
Metaflow's actual auto-generated CLI flag convention for every
`Parameter` (confirmed via `python flow.py run --help`; see
`flow-cli-contract.md`'s note). Every flag below is underscored for the
same reason.

## Target → flow invocation mapping

| Makefile target (unchanged name) | Old recipe (today, `001`) | New recipe (`002`) |
|---|---|---|
| `dev-abliterate-e2e` | `expect scripts/heretic_automate.exp ... "$(HERETIC)" --model ...` | `$(PYTHON) flow.py run --only_step decensor,log_to_mlflow --model "$(DEV_MODEL)" --seed "$(SEED)" ...` (same `expect`-driven non-interactive automation, now invoked from inside the `decensor` step rather than directly by `make`) |
| `log-abliteration-mlflow` | `MLFLOW_TRACKING_URI=... $(PYTHON) scripts/log_heretic_to_mlflow.py --model ... --checkpoint-dir ...` | `$(PYTHON) flow.py run --only_step log_to_mlflow --model "$(MODEL)" --study_checkpoint_dir "$(STUDY_CHECKPOINT_DIR)" --mlflow_tracking_uri "$(MLFLOW_TRACKING_URI)" ...` |
| `optimize-mlx` | `$(PYTHON) scripts/optimize_mlx.py --n-trials ... --hf-path ...` | `$(PYTHON) flow.py run --only_step decensor,mlx_search --n_trials_mlx "$(N_TRIALS_MLX)" --hf_path "$(HF_PATH)" ...` |
| `optimize-gguf` | `$(PYTHON) scripts/optimize_gguf.py --n-trials ... --gguf-f16 ...` | `$(PYTHON) flow.py run --only_step gguf_search --n_trials_gguf "$(N_TRIALS_GGUF)" ...` |
| `optimize` | `$(MAKE) optimize-mlx` then (or `-j2` with) `$(MAKE) optimize-gguf` per `OPTIMIZE_PARALLEL` | `$(PYTHON) flow.py run --only_step mlx_search,gguf_search --optimize_parallel "$(if $(filter 1,$(OPTIMIZE_PARALLEL)),True,False)" ...` |

(`--only_step` is a real, implemented flow-level `Parameter` — a
comma-separated step-name allowlist, checked by each step's
`_should_skip()` helper. Not illustrative shorthand; see `flow.py`'s
`_requested_steps()`/`_should_skip()`. The contract this table enforces
is unchanged: **the Makefile target's user-visible behavior and output
artifacts are unchanged**, only what runs underneath changed.)

## Invariants this contract enforces

1. **No divergent logic.** The Makefile recipe MUST NOT contain any
   pipeline-stage logic that isn't also reachable through
   `python flow.py run` directly — per FR-001a's "never two divergent
   implementations of the same stage." Concretely: no Makefile recipe
   post-`002` calls `heretic`/`mlx_vlm.convert`/`llama-quantize` etc.
   directly; every one of those calls happens inside a `flow.py` step,
   and the Makefile only ever invokes `flow.py`.
2. **Same artifacts, same paths.** `HF_PATH`, `MLX_OUT_DIR`,
   `GGUF_OUT_DIR`, the MLflow experiment names, and every
   `.provenance.json` sidecar location are computed identically whether
   started via `make` or via the direct Metaflow CLI — because both paths
   resolve to the same flow-level `Parameter` defaults and the same
   underlying script calls.
3. **`make help` stays accurate.** Per Article VII Rule 1/2, each
   rewritten target keeps its one-line `make help` description; the
   description's *content* may need a small wording update (e.g. "Log
   every completed trial... via the orchestrated flow" instead of just
   "...to MLflow") but the target's existence and the README row it maps
   to do not disappear or get renamed.
4. **`make test` gate unchanged.** Rewriting these recipes does not
   change what `make test` runs — `tests/test_flow.py` is additive, and
   the existing `tests/test_optimize_mlx.py`/`test_optimize_gguf.py`/etc.
   continue testing the underlying scripts directly, independent of
   whether the Makefile or `flow.py` is what calls them in production.

## What this contract does NOT cover

- The direct Metaflow CLI's own flag surface — see
  `flow-cli-contract.md`.
- Any change to `scripts/*.py`'s own CLI contracts — none are modified by
  this feature (FR-006).
</content>
