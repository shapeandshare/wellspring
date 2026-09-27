# Implementation Plan: Full Pipeline Orchestration via Metaflow

**Branch**: `002-metaflow-migration` | **Date**: 2026-09-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-metaflow-migration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Wrap this pipeline's four existing stages (heretic abliteration, MLflow
result-logging, MLX quantization search, GGUF quantization search — all
already implemented and tested in `specs/001-mlflow-instrumentation/`) in
one Metaflow `FlowSpec` (`flow.py` at the repo root) that an operator can
start either via existing `make` targets (each target now invoking
`python flow.py run --only-<stage>` internally) or directly via Metaflow's
own CLI (required for production, FR-001a). The flow fans out from one
decensored checkpoint into the two independent compression searches as
parallel branches (FR-003), joined only for reporting. Metaflow's own
`resume` command (empirically verified: skips already-completed steps,
re-runs only the failed one) delivers whole-pipeline resumability (FR-007)
for free; its own `--max-workers 1` flag (empirically verified: forces
strictly sequential branch execution) implements `OPTIMIZE_PARALLEL`'s
existing sequential/concurrent topology switch (FR-006) without new code.
The Mac-native MLX-search step stays a plain in-process Python function
guarded by a `platform.system() != "Darwin"` check (empirically verified:
raising inside a step fails that step with the underlying error preserved,
satisfying FR-005/SC-005) — never a `@kubernetes`/`@batch` step, since
those decorators are Linux-container-only and cannot reach Apple Silicon
(confirmed via `docs.metaflow.org`). Every stage's underlying script
(`scripts/log_heretic_to_mlflow.py`, `scripts/optimize_mlx.py`,
`scripts/optimize_gguf.py`) is invoked from inside a step exactly as the
Makefile invokes it today — as a subprocess — so none of `001`'s
resumability/idempotency/provenance guarantees (FR-006) are re-implemented,
only orchestrated. `metaflow` (2.19.39, verified to run and pass both a
linear and a two-branch-fan-out-join flow, including a real interrupt →
`resume` cycle, on this project's pinned Python 3.14 despite PyPI
classifiers only listing up to 3.13) is added to `requirements.txt`.

## Technical Context

**Language/Version**: Python 3.14 (already pinned via `.python-version`; no change)

**Primary Dependencies**: `metaflow` (new — empirically verified: `pip install metaflow` succeeds on Python 3.14, a real `FlowSpec` with `@step`/`Parameter`/branch-fan-out-join runs end-to-end, `resume` after a killed step correctly skips completed steps and re-runs only the failed one, `--max-workers 1` forces strict sequential branch execution). Reuses existing `mlflow`/`optuna` (already in `requirements.txt` from `001`) and the four existing `scripts/*.py` modules unchanged — this feature adds an orchestration layer, it does not modify any of `001`'s scripts.

**Storage**: Metaflow's local datastore (`.metaflow/`, gitignored — new entry required) for run/step metadata; all pipeline *artifacts* (checkpoints, MLX/GGUF exports, provenance sidecars, MLflow tracking DB) remain exactly where `001` already puts them — Metaflow's own run tracking is a supplementary index (FR-009), never the artifact store.

**Testing**: `pytest` (existing `make test` gate, unchanged). New: a `tests/test_flow.py` characterization suite exercising `flow.py`'s pure-Python helper functions (hardware-guard predicate, stage-selection logic) directly — per Article IX, full step methods that shell out to `make`/`heretic`/`mlx_vlm` are integration-level and covered by `quickstart.md`'s scenarios, not synthetic unit mocks that would only test that a mock returns what it's told to return.

**Target Platform**: Unchanged from today — macOS/Apple Silicon (Track A, full pipeline including MLX) or Linux+NVIDIA (Track B, GGUF-only). Metaflow's own execution is local-only for this feature (no `@kubernetes`/`@batch`) — see Constraints below.

**Project Type**: Single project — CLI/pipeline orchestration (matches existing Makefile+scripts structure, no web/mobile split).

**Performance Goals**: N/A — this is an orchestration-layer change over existing stages; no new performance target beyond "no slower than today's manually-sequenced commands" (implicit in SC-001..SC-003).

**Constraints**:
- Metaflow's own remote-execution backends (`@batch`, `@kubernetes`) are Linux-container-only (confirmed via `docs.metaflow.org`'s driver-install docs — a Mac can only be a *launcher*, never a remote target). The MLX-search stage's Mac/Apple-Silicon-only requirement (FR-005) therefore means: **the flow itself only ever runs locally** (`python flow.py run`, no remote scheduler) in this feature's scope — a person or Mac-hosted automation runner must invoke it directly on Mac hardware for the MLX branch to succeed, exactly as they must today. No `@kubernetes`/`@batch` decorator is used anywhere; adding one for the GGUF branch alone would violate FR-004's requirement that a change to one search's execution mechanism must not diverge from the other's.
- FR-001a's dual-entry-point requirement: `make` targets must invoke the *identical* flow definition Metaflow's own CLI invokes — never a second, parallel implementation.
- Constitution Article X (Domain-Driven Package Decomposition) is **already triggered** (`scripts/` at 12 modules, MD-003 outstanding). This feature adds `flow.py` at the repo root (not inside `scripts/`), so it does not itself push `scripts/`'s count further — but see Complexity Tracking below for why a `flow.py` module-count discussion is still owed.

**Scale/Scope**: Built and verified against the existing dev-cycle model (`DEV_MODEL`, TinyLlama) per the spec's Assumptions — the flow definition itself takes `MODEL`/hardware placement as `Parameter`s so the identical definition runs against the production model on production-scale compute with zero code changes (FR-011/SC-007).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Check | Status |
|---|---|---|
| I — Provenance & Chain of Custody | Every artifact-producing stage already writes its own `.provenance.json` via `scripts/write_manifest.py` (`001`). This feature does not remove that; FR-009 explicitly requires Metaflow's own run tracking stay a *supplementary* index, never the sole provenance record. | **PASS** |
| II — License Awareness | `metaflow` is Apache-2.0 (PyPI classifier: `License :: OSI Approved :: Apache Software License`) — permissive, no new flag needed. `make lock`/`make notices` must be re-run once `metaflow` is added to `requirements.txt` (Article II Rule 2). | **PASS** (action: re-run `make lock`/`make notices` at implementation time) |
| III — Two Independent Export Paths | FR-004 restates this article verbatim as a functional requirement. The flow's MLX-search and GGUF-search steps must remain two separate step functions with no shared helper beyond what `001` already shares (Python env, `write_manifest.py`) — no new cross-path coupling introduced by orchestration. | **PASS** (verify at implementation: no new shared calibration/tooling path) |
| IV — Atomic, Safe-to-Rerun Operations | Unchanged — every atomic write (`.tmp` + rename) lives inside the wrapped scripts, which this feature does not modify. | **PASS** |
| V — Reproducibility, Honestly Bounded | Unchanged — `SEED` and friends are passed through as flow `Parameter`s with the same fixed defaults; no new randomness introduced by the orchestration layer itself. | **PASS** |
| VI — Simplicity First (YAGNI) | Directly informs the "no `@kubernetes`/`@batch`" decision above — a remote-execution decorator would be speculative complexity with no present requirement this feature actually has (the one stage that would want remote dispatch, MLX search, physically can't use it). Boring-over-novel: `metaflow.Runner`/`spin` unit-testing APis exist but add framework surface for functions Article IX already asks to be tested as plain Python (see Technical Context/Testing). | **PASS** |
| VII — The Makefile Is the Interface | FR-001a keeps `make` targets as the default entry point; each target's recipe becomes `python flow.py run --only-<stage> ...` (or equivalent) instead of today's direct tool invocation — still a `.PHONY` target, still documented in `README.md`'s tables, still re-runnable standalone (Rule 4). New variables (if any) get "Key variables" rows. | **PASS** (implementation must update README tables in the same change — Article XIII) |
| VIII — Fail Fast, Never Silently Corrupt | FR-005's hardware guard is exactly this article's Rule 4 pattern (named, actionable error before expensive work) — empirically verified above that a step-level `raise` surfaces the real error, not a generic crash. FR-002's edge case (underlying tool crash mid-stage) is satisfied by the same mechanism: Metaflow surfaces a step's exception with its original message, confirmed via the "boom" test above. | **PASS** |
| IX — TDD (NON-NEGOTIABLE) | New `flow.py` logic (hardware guards, stage-selection helpers, parameter plumbing) needs failing tests before implementation, exactly as `001`'s scripts did. Full step bodies that only shell out to already-tested scripts are integration-level, validated via `quickstart.md`, not re-mocked. | **PASS** (task-level: red-green cycle required at `/speckit.tasks`/`/speckit.implement`) |
| X — Domain-Driven Package Decomposition | `flow.py` lives at repo root, not `scripts/` — does not push `scripts/`'s already-triggered 12-module count further, and is not itself a 6th+ peer module in a new domain package (it's the single orchestration entry point, analogous to the Makefile itself). No new Article X trigger from this feature. | **PASS** |
| XI — Package Ownership & One Class Per File | `flow.py`'s `FlowSpec` subclass is exactly one primary class per Article XI Rule 2 — the pattern this article already anticipates. | **PASS** |
| XII — Type Hygiene | New functions in `flow.py` (hardware-guard predicate, any helper) must carry type hints per existing convention (`write_manifest.py`'s `git_commit(path: str) -> str | None`). Metaflow's own `@step`-decorated methods take `self` only, by the framework's own contract — no return-type annotation is meaningful there (framework constraint, not a hygiene lapse). | **PASS** (documented exception for `@step` methods specifically) |
| XIII — Agent Conduct | This plan itself follows scope discipline (wraps, does not re-implement, `001`'s stages) and defers commit/doc-update discipline to implementation time. | **PASS** |

**Result**: No violations. No Complexity Tracking entries required — see table below (empty, as no gate failed).

## Project Structure

### Documentation (this feature)

```text
specs/002-metaflow-migration/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── flow-cli-contract.md
│   └── makefile-wrapper-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

**Structure Decision**: Single project (matches existing Makefile + `scripts/` +
`tests/` layout — this feature adds exactly one new root-level file and one
new test module; no new top-level directory, no web/mobile split applies).

```text
wellspring/                      # repo root
├── Makefile                     # MODIFIED: 4 targets' recipes now invoke flow.py
├── flow.py                      # NEW: single Metaflow FlowSpec, all 4 stages as steps
├── requirements.txt             # MODIFIED: + metaflow
├── scripts/                     # UNCHANGED — flow.py subprocess-invokes these,
│   ├── log_heretic_to_mlflow.py #   exactly as the Makefile does today (FR-006)
│   ├── optimize_mlx.py
│   ├── optimize_gguf.py
│   └── ... (9 other existing modules, untouched)
├── tests/
│   └── test_flow.py             # NEW: characterization tests for flow.py's
│                                 #   pure-Python helpers (hardware guard, etc.)
└── .gitignore                   # MODIFIED: + .metaflow/ (local run datastore)
```

## Complexity Tracking

*No entries — Constitution Check reported no violations requiring justification.*
</content>
