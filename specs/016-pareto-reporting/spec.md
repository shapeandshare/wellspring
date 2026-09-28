# Feature Specification: Pareto-Front Reporting for Quantization Studies

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Phase 2, "Pareto-front reporting" (formerly in `ROADMAP.md`).

## Context (current state)

- `optimize_mlx.py` and `optimize_gguf.py` run two-objective NSGA-II studies
  (`perplexity`, `refusal_rate`, both minimized) with persistent SQLite storage
  and a per-trial archive manifest. Nothing reports the Pareto front; the
  operator must query Optuna by hand to choose a trade-off point.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See and export the trade-off curve (Priority: P1)

**Independent Test**: Against a fixture study with known dominated and
non-dominated trials, the report lists exactly the non-dominated set.

**Acceptance Scenarios**:

1. **Given** a finished study, **When** the operator runs the report command,
   **Then** it writes the Pareto set (trial number, params, both metrics,
   archive path) as a table and a plot, and logs both to MLflow.
2. **Given** a study with failed trials, **When** the report runs, **Then** failed
   trials are excluded and counted.

### User Story 2 - Promote a chosen point (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a chosen Pareto trial, **When** the operator promotes it, **Then** its
   archived artifact is copied to a named output with a provenance manifest
   linking back to the study and trial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Pareto membership MUST come from Optuna's own `study.best_trials`,
  not a reimplementation.
- **FR-002**: Reports MUST work for both MLX and GGUF studies through one code
  path.
- **FR-003**: Promotion MUST NOT mutate the archive or the study.
- **FR-004**: New targets carry README and `make help` entries in the same change.

## Success Criteria *(mandatory)*

- **SC-001**: Choosing and promoting a trade-off point needs two commands and no
  Optuna code written by the operator.

## Assumptions

- Plot output follows `docs/DESIGN.md` palette where it is published in docs.
- If spec 015 lands first, reports attach to the checkpoint's parent run.
