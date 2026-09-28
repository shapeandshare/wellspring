# Feature Specification: Live MLflow Tracking of Heretic's Search (Spike-First)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Phase 2, "Live instrumentation upgrade (optional)" (formerly in `ROADMAP.md`).

## Context (current state)

- `log_heretic_to_mlflow.py` ingests Heretic's Optuna journal **after** the run.
- `ROADMAP.md` claimed Heretic "ships a documented plugin system (`Scorer`
  plugins)". **This is not true of the pinned version**: `grep -rn "Scorer"
  vendor/heretic` and `grep -rli plugin vendor/heretic` return nothing against
  v1.4.0 (`vendor/heretic/pyproject.toml:3`). See vault discovery
  `2026-09-27-heretic-1-4-0-has-no-scorer-plugin-api`.
- `heretic-llm` is AGPL-3.0-or-later and is used only as an unmodified CLI
  subprocess (AGENTS.md §9). Importing it as a plugin host would need that
  position re-evaluated.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Feasibility decision is recorded (Priority: P1)

**Independent Test**: A decision note exists naming the chosen mechanism (or
"not feasible") with the evidence.

**Acceptance Scenarios**:

1. **Given** the pinned Heretic, **When** the spike ends, **Then** it records
   whether live tracking is possible without importing or modifying Heretic.

### User Story 2 - Progress visible in MLflow during the run (Priority: P2, only if feasible)

**Acceptance Scenarios**:

1. **Given** a running abliteration, **When** a trial completes, **Then** it appears
   in MLflow within one polling interval, deduplicated against post-hoc ingestion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The spike MUST evaluate a non-import option first: tailing the
  append-only journal file while Heretic runs, reusing the existing ingestion
  and idempotency code.
- **FR-002**: No option may modify `vendor/heretic/` or fork Heretic.
- **FR-003**: Any option that imports Heretic MUST NOT proceed without an
  explicit licence decision recorded in `vault/decisions/`.
- **FR-004**: Live and post-hoc ingestion MUST produce identical MLflow rows for
  the same journal (same identity tags).

## Success Criteria *(mandatory)*

- **SC-001**: During a `dev-abliterate` run, trial rows appear before the run ends.

## Assumptions

- Journal-tailing is expected to be sufficient; a plugin API is only needed if
  it is shown not to be.
