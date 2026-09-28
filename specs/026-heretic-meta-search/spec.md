# Feature Specification: Outer Search over Heretic's Meta-Settings

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Outer-search item. Decisions in
`vault/decisions/2026-09-27-heretic-meta-search-decisions.md`.

## Context (current state)

- `make abliterate` runs Heretic's internal Optuna search (TPE, `n_trials=200`)
  over abliteration parameters with fixed meta-settings.
- Spec 001's MLX and GGUF studies score the exported artifacts, but always
  downstream of one fixed Heretic run.
- The meta-settings and their defaults are in
  `vendor/heretic/src/heretic/config.py:280-342` (v1.4.0).

## Clarifications

### Session 2026-09-27

- Q: Budget and strategy? → A: Two stages. The dev stage is about 15 trials on
  Track A with Heretic's `n_trials=50`. The top 3 are confirmed on production
  (Track B) at `n_trials=200`. A Track B GPU-hours cap is required, with no
  default, and a cost estimate is printed before the run starts.
- Q: Which settings? → A: All six:
  `kl_divergence_target` 0.002–0.05 (log scale), `kl_divergence_scale` 0.5–2.0,
  `row_normalization` {none, pre, full}, `full_normalization_lora_rank` 1–8
  (sampled only when `full`), `winsorization_quantile` 0.9–1.0,
  `orthogonalize_direction` {true, false}. Every range includes the default.
- Q: What is each trial scored on? → A: The exported artifacts. Every trial runs
  spec 001's MLX and GGUF studies on its checkpoint; the trial's score is taken
  from those studies' results.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dev-stage search (Priority: P1)

**Independent Test**: With a fake Heretic CLI and fake inner studies, a 2-trial
outer search logs 2 trials, each with its settings and its exported-artifact
scores.

**Acceptance Scenarios**:

1. **Given** Track A and the dev model, **When** the outer search runs, **Then**
   each trial invokes `heretic` (unmodified CLI) with the sampled settings and
   `n_trials=50`, then runs both quantization studies on the result.
2. **Given** an interrupted run, **When** it resumes, **Then** it continues from
   persistent Optuna storage (as spec 001's studies do).
3. **Given** a trial whose inner studies fail entirely, **When** it is scored,
   **Then** it is marked failed and counts toward the budget.

### User Story 2 - Production confirmation (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a finished dev stage, **When** confirmation runs, **Then** the top 3
   settings re-run on production at `n_trials=200`, scored the same way.
2. **Given** no Track B hours cap, **When** confirmation starts, **Then** it
   refuses and names the setting.
3. **Given** cumulative spend reaching the cap, **When** the next step would
   start, **Then** it stops cleanly and records a partial result.

### Edge Cases

- Dev-to-production transfer: if the production ranking differs from the dev
  ranking, record it as a finding (vault reference note). The production result
  wins.
- Checkpoint disk use: each trial produces a full checkpoint. Only the best N are
  kept; the rest are deleted after scoring, with their scores retained.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Heretic MUST be invoked as an unmodified CLI subprocess. No import,
  fork or patch (AGPL position, AGENTS.md §9).
- **FR-002**: Each trial's score MUST come from exported artifacts via spec 001's
  studies, run unchanged. The inner study size defaults to 3 trials per format
  and is configurable.
- **FR-003**: The trial objective MUST stay multi-objective (quality and refusal
  rate from the exported artifacts), consistent with spec 001; never scalarised.
- **FR-004**: The pre-run cost estimate MUST show outer trials × (abliteration +
  inner MLX trials + inner GGUF trials) for each stage.
- **FR-005**: Every trial MUST record Heretic's full resolved config and its
  inputs (including any spec 025 P2 dataset choices) in provenance.
- **FR-006**: Outer, inner and abliteration runs MUST be grouped in MLflow using
  spec 015's grouping if available.
- **FR-007**: The dev trial count, `n_trials` per stage, the top-N count and the
  inner study size MUST be settings with the defaults above.
- **FR-008**: Tests MUST be hermetic, with fake Heretic and fake inner studies.

## Success Criteria *(mandatory)*

- **SC-001**: One command runs the dev stage; one command runs confirmation.
- **SC-002**: The cost estimate matches the actual run within ±30% on Track A.

## Assumptions

- MLX scoring needs Apple Silicon and GGUF scoring may run elsewhere; placing
  work on the right host reuses spec 013's dispatch where needed.
