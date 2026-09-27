# Implementation Plan: MLflow Experiment Tracking & Quantization Optimization

**Branch**: `001-mlflow-instrumentation` | **Date**: 2026-09-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-mlflow-instrumentation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Make Heretic's existing internal Optuna abliteration search visible in
MLflow after the fact (no live hook, no change to Heretic itself), and add
two new, independent, persistently-stored Optuna+MLflow searches — one per
export format (MLX, GGUF) — that search compression/quantization parameters
against one fixed upstream checkpoint, scoring every attempt on the real
compressed output file (perplexity + refusal-rate, never collapsed into one
number). A fully execution-ready 8-todo engineering breakdown for this exact
scope already exists at
`docs/evolutionary-pipeline-optimization-roadmap.md` (twice reviewed by
Momus + independent Oracle); this plan reconciles that existing breakdown
against the spec's five newly-clarified requirements (FR-014 through
FR-017, SC-006/SC-007) rather than re-deriving the approach from scratch.

## Technical Context

**Language/Version**: Python 3.14 (pinned via `.python-version`, matching
every other script in `scripts/`)

**Primary Dependencies**: `mlflow` (new), `optuna~=4.7` (new *explicit* pin —
already present transitively at 4.9.0 via `heretic-llm`, confirmed via
`pip show optuna`; pinning matches `vendor/heretic/pyproject.toml`'s own
`optuna~=4.7` constraint), `mlx-lm>=0.1; sys_platform == "darwin"` (new — not
currently installed, confirmed via `pip show mlx-lm`), `pytest` (already
present, dev-only)

**Storage**: Two new local SQLite files (one per compression search's
persistent Optuna study — `optuna.create_study(storage="sqlite:///...")`),
plus MLflow's own tracking backend (destination supplied by the
user/operator per the spec's Assumptions — file-based `sqlite`/local-dir URI
for dev, a real MLflow server for production use). No new database this
project operates itself.

**Testing**: `pytest` via `make test` (existing gate, Article IX) — every new
`scripts/*.py` module ships tests in the same change per constitution
Article IX Rule 2.

**Target Platform**: Same dual-track split as the rest of this pipeline —
macOS/Apple Silicon (MLX search, Track A) and Linux/NVIDIA (GGUF search,
Track B) — plus a new third target class introduced by this spec's
concurrency clarification (FR-015): a cluster/orchestrated-compute scenario
where each search gets its own dedicated node. This plan does **not**
design that third target's actual orchestration (out of scope per the
spec's own Assumptions — that's the "Hardware-aware export dispatch" track
in `ROADMAP.md`); it only ensures nothing this feature adds *assumes*
same-machine execution in a way that would block it later (see Constitution
Check → Article III interaction below).

**Project Type**: CLI/Makefile-orchestrated pipeline (single project — no
frontend/backend split; matches this repo's existing shape)

**Performance Goals**: Not latency-sensitive (offline, batch search
process). Existing plan's own budget assumption applies: ~10-20 trials per
compression search (spec Assumptions), each trial bounded by one real
export+quantize+eval cycle — not a hard SLA, a cost-awareness ceiling
(AGENTS.md §8).

**Constraints**:
- FR-014 (env-var-only credentials) — no config file, CLI flag, or Makefile
  `--field` may carry a tracking-destination secret.
- FR-015 (compute-topology-aware concurrency) — sequential-by-default on
  shared compute, concurrent-allowed on dedicated-per-search compute. This
  plan's `optimize` Makefile target must express both modes without
  hardcoding one (see Data Model / Contracts below for how).
- FR-016 (failed attempts count against budget) — no hidden retry loop.
- FR-009 amended / FR-017 (never-auto-delete artifacts + documented
  disk-footprint estimate) — archive roots are additive-only; README must
  state an approximate per-session footprint.
- Constitution Article III (MLX/GGUF paths never cross-feed) — the two new
  searches must remain as independent as the export paths they instrument.
- Constitution Article IV (atomic, safe-to-rerun) — every new archived
  artifact and manifest follows the existing `.tmp`-then-rename pattern.

**Scale/Scope**: Two new Optuna studies (one per export format), one new
post-hoc MLflow ingestion script, two new perplexity eval wrappers (MLX,
GGUF), one new shared refusal-rate driver, ~8 new/modified files under
`scripts/` + `Makefile` + `README.md` — matching the existing plan's own
scope exactly (see `docs/evolutionary-pipeline-optimization-roadmap.md`'s
8 todos).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Check | Status |
|---|---|---|
| I — Provenance | Every new artifact (MLflow run, archived quant trial) traceable to what produced it | **PASS** — existing plan's per-trial `manifest.json` + MLflow run tags (`journal_identity`, `trial_number`) satisfy this; Phase 1 data model formalizes it |
| II — License Awareness | New deps (`mlflow`, `optuna` explicit pin, `mlx-lm`) checked | **PASS, action required** — all three are permissive-licensed (Apache-2.0/BSD family); `make lock`/`make notices` MUST be re-run once added (deferred to implementation, not this plan) |
| III — Two Independent Export Paths | New MLX/GGUF search scripts must not cross-feed | **PASS** — `optimize_mlx.py`/`optimize_gguf.py` are separate scripts, separate archive roots, separate MLflow experiments, mirroring `convert-mlx`/`convert-gguf`'s existing separation |
| IV — Atomic, Safe-to-Rerun | Archive writes, manifests | **PASS** — existing plan's archive-immediately-before-cleanup pattern + `.tmp`-then-rename already designed in; FR-009 amendment (never-auto-delete) strengthens this, doesn't weaken it |
| V — Reproducibility, Honestly Bounded | Optuna `SEED`, sample counts recorded | **PASS** — persistent Optuna storage records every trial's params by construction; no new unbounded randomness introduced |
| VI — Simplicity First / YAGNI | No speculative abstraction | **PASS with one flagged risk** — FR-015's compute-topology concurrency control is the one place this spec asks for more than the existing plan currently designs (see Phase 0 research item R1) |
| VII — Makefile Is the Interface | New stages as `.PHONY` targets, documented | **PASS** — existing plan's Todo 8 already covers `optimize-mlx`/`optimize-gguf`/`optimize`/`log-abliteration-mlflow` |
| VIII — Fail Fast | `MLFLOW_TRACKING_URI` unset fails loud; credential handling | **PASS, action required** — existing plan's Todo 1 already fails fast on unset `MLFLOW_TRACKING_URI`; FR-014 (env-var-only credentials) is **new** vs. the existing plan and needs an explicit "never accept as CLI arg" guard added (Phase 0 research item R2) |
| IX — TDD | Tests ship with implementation | **PASS** — `tasks.md` (this feature's own task breakdown, not the existing sibling engineering plan) enforces tests-first (RED before GREEN) for every new script, with no exemption claimed; no Complexity Tracking entry needed for this article |
| X — Domain Decomposition | 6-module threshold | **PASS** — this feature adds ~6 new `scripts/*.py` modules (`eval_refusal_rate.py`, `eval_perplexity_gguf.py`, `eval_perplexity_mlx.py`, `log_heretic_to_mlflow.py`, `optimize_mlx.py`, `optimize_gguf.py`); combined with the existing 4, `scripts/` would reach **10 modules total, crossing the Article X threshold of 6** — flagged in Complexity Tracking |
| XIII — Agent Conduct | Scope discipline, docs stay current | **PASS** — existing plan's Todo 8 already carries README updates in the same change |

**Gate result (pre-Phase 0)**: PASS, with two items requiring Phase 0
research (R1, R2) and one Article X threshold crossing requiring a
Complexity Tracking entry (decomposition deferred, not blocking — see
below).

## Constitution Check (post-Phase 1 re-evaluation)

Re-checked after `research.md`/`data-model.md`/`contracts/`/`quickstart.md`
were written:

| Article | Re-check | Status |
|---|---|---|
| VI — Simplicity First | R1's resolution (`OPTIMIZE_PARALLEL` boolean var, no auto-detection) | **PASS** — no speculative cluster-detection logic introduced; matches existing `GGML_CUDA`/`DEVICE_MAP` pattern exactly |
| VIII — Fail Fast | R2's resolution (zero new credential-accepting code paths; MLflow's own env-var-only client design does the work) | **PASS** — contracts/cli-contracts.md explicitly documents "never accepts" for every credential-shaped flag across all 3 new CLI scripts |
| I — Provenance | data-model.md's four entities each map to a concrete identity + manifest/tag scheme | **PASS** — `journal_identity` (path-hash, not content-hash) and archive `manifest.json` both trace every artifact to what produced it |
| III — Two Independent Export Paths | contracts/cli-contracts.md's `optimize_mlx.py`/`optimize_gguf.py` separation | **PASS** — confirmed no shared archive root, no shared MLflow experiment name, no shared calibration input between the two new search scripts |
| IV — Atomic, Safe-to-Rerun | data-model.md's "Compressed output file" entity — archive-immediately-before-cleanup + never-auto-delete (FR-009 amended) | **PASS** — strictly strengthens the existing atomicity guarantee, doesn't introduce a new failure window |
| X — Domain Decomposition | Complexity Tracking entry (6 new modules, threshold crossed) | **DEFERRED, documented** — not blocking this plan; explicit follow-up commit recommended (see Complexity Tracking) |

**Gate result (post-Phase 1)**: PASS. No new violations introduced by the
Phase 1 design; the one Article X flag from the pre-Phase-0 check remains
the only outstanding item, and it is explicitly deferred (not silently
dropped) per the Governance amendment procedure's own disclosure
requirement.

## Project Structure

### Documentation (this feature)

```text
specs/001-mlflow-instrumentation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md         # Phase 1 output (/speckit.plan command)
├── quickstart.md         # Phase 1 output (/speckit.plan command)
├── contracts/             # Phase 1 output (/speckit.plan command)
└── tasks.md              # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
├── eval_refusal_rate.py       # NEW - shared refusal-rate driver (FR-007)
├── eval_perplexity_gguf.py    # NEW - GGUF perplexity wrapper (FR-006)
├── eval_perplexity_mlx.py     # NEW - MLX perplexity wrapper (FR-006, FR-011)
├── log_heretic_to_mlflow.py   # NEW - post-hoc Heretic->MLflow ingestion (FR-001, FR-002, FR-003)
├── optimize_mlx.py            # NEW - MLX compression search (FR-004, FR-008, FR-009, FR-015)
├── optimize_gguf.py           # NEW - GGUF compression search (FR-005, FR-008, FR-009, FR-010, FR-015)
├── fetch_calibration_data.py  # existing, unmodified
├── fetch_calibration_text.py  # existing, unmodified
├── fetch_paper.py             # existing, unmodified
├── preflight_check.py         # existing, unmodified
└── write_manifest.py          # existing, unmodified — reused for per-trial manifests (Article I/VI Rule 4)

tests/
├── test_eval_refusal_rate.py      # NEW
├── test_eval_perplexity_gguf.py   # NEW
├── test_eval_perplexity_mlx.py    # NEW
├── test_log_heretic_to_mlflow.py  # NEW
├── test_optimize_mlx.py           # NEW
├── test_optimize_gguf.py          # NEW
└── (existing 4 test files, unmodified)

Makefile        # + MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_PREFIX, STUDY_CHECKPOINT_DIR,
                #   N_TRIALS_MLX, N_TRIALS_GGUF, LLAMA_PERPLEXITY vars;
                # + log-abliteration-mlflow, optimize-mlx, optimize-gguf, optimize targets;
                # + build-llama-cpp target list extended (llama-perplexity, llama-cli)
requirements.txt  # + mlflow, optuna~=4.7 (explicit), mlx-lm (darwin-only)
README.md         # + new targets/variables documented, disk-footprint note (FR-017)
```

**Structure Decision**: Single-project CLI/Makefile structure (no
frontend/backend split) — matches this repository's existing shape
exactly. All new Python surface lands in the existing flat `scripts/`
directory rather than a new sub-package, consistent with Article X's
"not yet triggered" status as of the last constitution ratification —
**this feature's addition of 6 new modules changes that determination**;
see Complexity Tracking.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| Article X (Domain-Driven Package Decomposition) threshold crossed — `scripts/` would grow from 4 to 10 peer modules, past the constitution's 6-module trigger | This feature's minimum viable scope genuinely needs 6 new scripts (refusal-rate driver, 2 perplexity wrappers, 1 ingestion script, 2 search scripts) — the domain boundaries are already named in the constitution's own Article X rationale ("calibration, provenance, evaluation, optimization-study tracking") | Splitting into domain sub-packages (`eval/`, `optimize/`) *now*, inside this same plan, was rejected because Article X Rule 3 requires decomposition to be "its own commit: moves and import rewrites, zero behavioral delta" — bundling a structural refactor into the same change as six brand-new behaviors would violate that separation and make this feature's own review harder to verify. **Recommendation**: implement this feature's 6 scripts flat in `scripts/` first (ships the behavior), then run the Article X split as an immediate, dedicated follow-up commit before the next feature adds to `scripts/` further — never let the threshold crossing go unaddressed indefinitely. |
