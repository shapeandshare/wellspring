# Phase 1 Data Model: MLflow Experiment Tracking & Quantization Optimization

This feature introduces no new persistent domain classes in the
object-oriented sense (Article XI's "one class per file" does not apply —
these are data shapes flowing through existing patterns: Optuna storage,
MLflow's run/experiment model, and this project's existing manifest
convention). Documented here as the four Key Entities from the spec,
mapped to their concrete on-disk/in-service representation.

## Decensoring run

**Represents**: one completed execution of `make abliterate`/
`make dev-abliterate`, i.e. one Heretic invocation's full internal Optuna
study.

**Identity**: `journal_identity` — `sha256(resolve(journal_file_path))[:16]`,
a hash of the *canonical absolute path* to Heretic's own Optuna journal
file (`$(STUDY_CHECKPOINT_DIR)/<sanitized-model-name>.jsonl`), **not** a
hash of the file's mutable, append-only byte content. Stable across the
same run being re-recorded (FR-002, FR-003) because a file's path doesn't
change as its content grows across trials.

**Fields** (as recorded on the MLflow side, tagged on every Trial run it
produces — see below):
| Field | Source | Notes |
|---|---|---|
| `journal_identity` | derived (see Identity) | MLflow run tag |
| `model` | Heretic's own `--model` value, read from the journal's study metadata | for human-readable disambiguation between runs |

**Relationships**: one Decensoring run → many Trials (its own internal
Optuna study's completed trials).

**Validation rules**: FR-002 (no duplicate entries on re-recording) is
enforced by checking, before creating any new MLflow run, whether a run
already exists tagged with this exact `journal_identity` — if so, skip
(idempotent, not an error).

## Trial

**Represents**: one attempted parameter combination — either (a) one of
Heretic's own internal Optuna trials (abliteration parameters), or (b) one
attempt within one of the two new compression searches (quantization
parameters).

**Identity**: `(journal_identity, trial_number)` for case (a);
`(compression_search_id, trial_number)` for case (b) — Optuna's own
trial-numbering within its persistent study, never reused across a
re-created study.

**Fields**:
| Field | Type | Notes |
|---|---|---|
| `trial_number` | int | Optuna-assigned, monotonic within a study |
| `params` | dict[str, Any] | logged as MLflow params (flat key/value) |
| `scores` | dict[str, float] | Heretic's own `{"name", "score": {"value", "baseline"}}` shape (case a), flattened to `f"{name}_value"`/`f"{name}_baseline_value"`; or `{"perplexity": float, "refusal_rate": float}` (case b, FR-007) |
| `status` | `COMPLETE` \| `FAIL` | FR-016 — a `FAIL`ed trial still counts against the search's attempt budget |

**Relationships**: many Trials → one Decensoring run (case a) OR one
Compression search (case b) — never both; the two search kinds are
recorded under separate MLflow experiments (`{prefix}-abliteration` vs.
`{prefix}-mlx-quant`/`{prefix}-gguf-quant`) per Constitution Article III.

**Validation rules**: FR-007 — a Trial's `scores` for a compression search
MUST always contain both `perplexity` and `refusal_rate` as independent
keys; a scorer MUST NOT collapse them into one combined field.

## Compression search

**Represents**: one persistent, resumable Optuna study — one instance per
export format (MLX, GGUF) — searching that format's compression/
quantization parameters against one fixed upstream artifact.

**Identity**: the Optuna `study_name` (`"optimize-mlx"` / `"optimize-gguf"`)
plus its persistent SQLite storage path (`<archive_root>/study.db`) — the
pairing of the two is what makes `load_if_exists=True` correctly resume
the *same* search rather than accidentally starting a new one (FR-008).

**Fields**:
| Field | Type | Notes |
|---|---|---|
| `study_name` | str | fixed per format, never derived from user input |
| `archive_root` | path | derived from `MLX_OUT_DIR`/`GGUF_OUT_DIR` respectively (never from `HF_PATH` directly — see existing plan's Todo 6 rationale for why), guarded to never resolve to an ancestor/descendant of the export directory it archives from |
| `directions` | `["minimize", "minimize"]` | multi-objective, NSGA-II sampler — perplexity and (1 − refusal-removal, or however signed to keep both "lower is better") never scalarized (FR-007) |
| `attempt_budget` | int | `N_TRIALS_MLX`/`N_TRIALS_GGUF` — FR-016: failed attempts count against this |
| `compute_mode` | `sequential` \| `concurrent` | derived from `OPTIMIZE_PARALLEL` (see research.md R1) — not stored in the study itself, but governs how the *pair* of searches (MLX + GGUF) is invoked by the `optimize` Makefile target; FR-015 |

**Relationships**: one Compression search → many Trials; one Compression
search → one fixed upstream artifact (the Decensoring run's output, for
MLX; or the one-time GGUF F16 conversion output, for GGUF) — never a
moving target across the search's lifetime (spec Assumptions).

**Validation rules**: FR-010 — the GGUF search's `archive_root`/study MUST
NOT trigger `make convert-gguf` per trial; only `make quantize-gguf` (reusing
the existing F16 output) runs per trial.

## Compressed output file (search artifact)

**Represents**: the actual exported, compressed model file (one MLX
directory or one `.gguf` file) produced by one Trial within a Compression
search.

**Identity**: `<archive_root>/trial-<trial_number>.<ext>` — copied
immediately after the trial's export/quantize step succeeds, before the
next trial's routine cleanup (`convert-mlx`'s `.tmp`/`rm -rf`, or
`quantize-gguf`'s `find ... -delete`) would otherwise remove or overwrite
it.

**Fields**:
| Field | Type | Notes |
|---|---|---|
| `path` | path | outside `MLX_OUT_DIR`/`GGUF_OUT_DIR` — verified via the ancestor/descendant safety check above |
| `trial_number` | int | matches the owning Trial |
| `manifest_path` | path | `<archive_root>/manifest.json` — one manifest per archive root, listing every trial it covers, per Constitution Article I Rule 2 |

**Relationships**: exactly one Compressed output file per successfully-
`COMPLETE`d Trial (a `FAIL`ed trial per FR-016 has no corresponding
artifact file — nothing to archive).

**Validation rules**:
- FR-009 (amended) — MUST NOT be deleted automatically, ever, by this
  feature's own later trials or by any unrelated routine pipeline
  operation. Deletion is exclusively a person-initiated filesystem action
  outside this feature's own code paths.
- FR-017 — the *aggregate* disk footprint of all of one search's archived
  files (`attempt_budget × typical file size for the format`) MUST be
  stated as an approximate order of magnitude in `README.md`'s
  "Requirements"/disk-sizing section, in the same style as the existing
  ~72GB checkpoint and ~260–400GB EC2 sizing table (Constitution
  "Additional Constraints" — disk budgeting).
