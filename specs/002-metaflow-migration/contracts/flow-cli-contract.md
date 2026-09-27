# Contract: Metaflow CLI Entry Point (`python flow.py ...`)

This is the "operator MUST be able to bypass the Makefile entirely"
entry point required by FR-001a(b) — the co-equal, production-required
sanctioned way to start an orchestrated run, independent of `make`.

**Flag naming — corrected during implementation.** Metaflow auto-generates
each `Parameter`'s CLI flag using the Python attribute name verbatim
(underscores, not hyphens) — confirmed empirically via `python flow.py run
--help` (`--model_commit`, `--only_step`, `--study_checkpoint_dir`, etc.),
which contradicted this contract's original hyphenated assumption
(`--model-commit`). All examples below use the real, verified flag names.

## Invocation forms

```sh
# Full pipeline, dev-cycle model, sequential compression searches (default topology)
python flow.py run \
    --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    --model_commit null \
    --seed 42

# Full pipeline, production model, dedicated-compute concurrent searches
python flow.py run \
    --model Qwen/Qwen3.6-35B-A3B \
    --model_commit <pinned-sha> \
    --seed 42 \
    --optimize_parallel True \
    --max-workers 16          # Metaflow's own flag (hyphenated, framework-provided); 16 is its documented default

# Resume an interrupted run (whole-pipeline resumability, FR-007/User Story 3)
python flow.py resume
```

## Parameters (flow-level, declared via `Parameter` in `flow.py`)

| Parameter | Type | Default | Maps to (today's Makefile var) |
|---|---|---|---|
| `--model` | `str` | `Qwen/Qwen3.6-35B-A3B` | `MODEL` |
| `--model_commit` | `str` | `null` | `MODEL_COMMIT` |
| `--quantization` | `str` | `NONE` | `QUANTIZATION` |
| `--seed` | `int` | `42` | `SEED` |
| `--device_map` | `str` | `""` (empty) | `DEVICE_MAP` |
| `--hf_path` | `str` | derived from `--model` | `HF_PATH` |
| `--mlflow_tracking_uri` | `str` | `""` (empty — fails fast if unset, per FR-006's requirement to preserve `001`'s FR-014 environment-only-credential-handling guarantee unchanged) | `MLFLOW_TRACKING_URI` |
| `--mlflow_experiment_prefix` | `str` | `wellspring` | `MLFLOW_EXPERIMENT_PREFIX` |
| `--n_trials_mlx` | `int` | `15` | `N_TRIALS_MLX` |
| `--n_trials_gguf` | `int` | `15` | `N_TRIALS_GGUF` |
| `--optimize_parallel` | `bool` | `False` | `OPTIMIZE_PARALLEL` (`0`/`1` → `False`/`True`) |
| `--study_checkpoint_dir` | `str` | `checkpoints` | `STUDY_CHECKPOINT_DIR` |
| `--only_step` | `str` | `""` (empty — no restriction, every step runs) | N/A — new to `002`; comma-separated step-name allowlist implementing FR-001a's dual-entry-point stage selection |
| `--batch_size` | `int` | `0` (0 = omitted, heretic's own auto-detection benchmark runs) | `DEV_BATCH_SIZE` — passed to heretic's `--batch-size` when nonzero, so `expect`-driven non-interactive runs skip the multi-minute batch-size auto-detection benchmark |
| `--llama_perplexity_bin` | `str` | `ik_llama.cpp/build/bin/llama-perplexity` | `LLAMA_PERPLEXITY` |
| `--llama_cli_bin` | `str` | `ik_llama.cpp/build/bin/llama-cli` | `LLAMA_CLI` |
| `--n_gpu_layers` | `int` | `0` (0 = omitted, CPU-only) | `LLAMA_NGL` (only passed by the Makefile when `GGML_CUDA=ON`, auto-detected via `nvidia-smi`) |
| `--good_prompts_dataset` | `str` | `mlabonne/harmless_alpaca` | `GOOD_PROMPTS_DATASET` |
| `--good_prompts_commit` | `str` | `02c6a92cfcf11bb0c387334f8146d149d65b587f` | `GOOD_PROMPTS_COMMIT` |
| `--good_prompts_split` | `str` | `train[:400]` | `GOOD_PROMPTS_SPLIT` |
| `--good_prompts_column` | `str` | `text` | `GOOD_PROMPTS_COLUMN` |
| `--bad_prompts_dataset` | `str` | `mlabonne/harmful_behaviors` | `BAD_PROMPTS_DATASET` |
| `--bad_prompts_commit` | `str` | `01cead01398926d81f7c52bdb790ee8cf77ebba7` | `BAD_PROMPTS_COMMIT` |
| `--bad_prompts_split` | `str` | `train[:400]` | `BAD_PROMPTS_SPLIT` |
| `--bad_prompts_column` | `str` | `text` | `BAD_PROMPTS_COLUMN` |
| `--good_eval_prompts_dataset` | `str` | `mlabonne/harmless_alpaca` | `GOOD_EVAL_PROMPTS_DATASET` |
| `--good_eval_prompts_commit` | `str` | `02c6a92cfcf11bb0c387334f8146d149d65b587f` | `GOOD_EVAL_PROMPTS_COMMIT` |
| `--good_eval_prompts_split` | `str` | `test[:100]` | `GOOD_EVAL_PROMPTS_SPLIT` |
| `--good_eval_prompts_column` | `str` | `text` | `GOOD_EVAL_PROMPTS_COLUMN` |
| `--bad_eval_prompts_dataset` | `str` | `mlabonne/harmful_behaviors` | `BAD_EVAL_PROMPTS_DATASET` |
| `--bad_eval_prompts_commit` | `str` | `01cead01398926d81f7c52bdb790ee8cf77ebba7` | `BAD_EVAL_PROMPTS_COMMIT` |
| `--bad_eval_prompts_split` | `str` | `test[:100]` | `BAD_EVAL_PROMPTS_SPLIT` |
| `--bad_eval_prompts_column` | `str` | `text` | `BAD_EVAL_PROMPTS_COLUMN` |

The `batch_size`/`llama_*_bin`/`n_gpu_layers`/prompt-dataset parameters
above were added during implementation (not present in the original
plan-phase contract) to fix three real bugs found via live QA: `decensor`
silently dropping heretic's pinned prompt-dataset commits (Constitution
Article I provenance discipline) and the `DEV_BATCH_SIZE` passthrough, and
`gguf_search` silently dropping the GPU-offload/binary-path passthrough
`optimize-gguf`'s original recipe had. See `tasks.md` T016/T026/T027.

Every parameter above is a direct passthrough to the identical
already-tested script/CLI flag `001` already exposes — this contract adds
no new semantic, only a new invocation surface for existing semantics
(FR-006).

## Metaflow's own flags (framework-provided, not this feature's surface)

These remain hyphenated — they are Metaflow's own built-in options, not
auto-generated from a `Parameter`, and were unaffected by the flag-naming
correction above.

| Flag | Effect | Relevant to |
|---|---|---|
| `--max-workers N` | Caps concurrent step execution; `1` forces the two compression-search branches to run strictly sequentially (verified in `research.md` item 4) | FR-006 (preserve existing sequential/concurrent topology behavior) |
| (bare) `resume` | Continues the most recent run, skipping already-completed steps, retrying only the failed one forward (verified in `research.md` item 3) | FR-007, User Story 3 |
| `resume <run-id>` | Same, targeting a specific prior run rather than the most recent | FR-007 (operator resuming a non-latest run) |

## Exit codes / failure surfacing

- A step's own `raise` (e.g. the `mlx_search` hardware guard, or a
  wrapped script's non-zero subprocess return) is surfaced verbatim in
  the CLI output, followed by `Step failure: Step <name> (task-id N)
  failed.` — confirmed empirically (`research.md` items 3 and 5). This is
  Metaflow's own behavior, not something `flow.py` must implement.
- FR-005/SC-005: attempting `mlx_search` on non-Darwin hardware fails
  with the guard's named error message *before* any `mlx_vlm`/model-load
  work begins (ordering guarantee — the guard is the step's first
  statement).

## What this contract does NOT cover

- Makefile-side invocation — see `makefile-wrapper-contract.md`.
- MLflow's own tracking API (unchanged from `001` — `scripts/_mlflow_env.py`
  and friends are untouched).
</content>
