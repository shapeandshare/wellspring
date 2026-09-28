# Feature Specification: Cross-Study MLflow Grouping

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Phase 2, "Cross-study dashboards" (formerly in `ROADMAP.md`).

## Context (current state)

- Spec 001 logs three unrelated MLflow experiments:
  `<prefix>-abliteration` (`src/scripts/log_heretic_to_mlflow.py`),
  `<prefix>-mlx-quant` and `<prefix>-gguf-quant`
  (`src/scripts/optimize_{mlx,gguf}.py`). No parent/nested runs exist, so one
  model's journey (decensor → compress → evaluate) cannot be browsed together.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse one model's whole journey (Priority: P1)

An operator opens MLflow and finds one parent run per source checkpoint, with
the abliteration trials and both quantization studies beneath it.

**Independent Test**: Against fixture journals and two-trial fixture studies,
`mlflow.search_runs` finds one parent with all child runs linked.

**Acceptance Scenarios**:

1. **Given** an ingested abliteration journal and both studies for the same
   checkpoint, **When** the operator views the parent run, **Then** all child
   runs are nested beneath it.
2. **Given** a study resumed later, **When** new trials log, **Then** they attach
   to the same parent (idempotent parent lookup).
3. **Given** two different checkpoints, **When** both are processed, **Then** they
   get two distinct parents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The parent identity MUST derive from the source checkpoint's
  content identity (as recorded by the provenance manifest), not from a path.
- **FR-002**: Existing experiment names and per-trial metrics MUST keep working.
  Grouping is additive.
- **FR-003**: Runs logged before this change MUST remain readable. Backfilling
  them is optional, via an explicit command.
- **FR-004**: Tests MUST be hermetic, using a local `file://` tracking URI.

## Success Criteria *(mandatory)*

- **SC-001**: For one checkpoint, one MLflow query returns every related run.

## Assumptions

- The MLflow data model (experiments vs. parent runs vs. tags) is decided in
  plan.md; the constraint is only "one browsable group per checkpoint".
