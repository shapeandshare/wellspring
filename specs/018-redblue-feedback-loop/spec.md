# Feature Specification: Red-vs-Blue Feedback Loop (Stage B)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Red-vs-Blue loop Stage B. Decisions recorded in
`vault/decisions/2026-09-27-redblue-loop-decisions.md`. Depends on
`specs/014-redblue-single-round`.

## Context (current state)

- Spec 014 runs one automated round (Red build → Blue audit → reveal score)
  with Blue isolation enforced by the pipeline. Nothing feeds the result back.

## Clarifications

### Session 2026-09-27

- Q: What may Red change between rounds? → A: Trigger and poison rate, with one
  rate shared by all variants in a round. In loop mode Red may change anything
  Article XV permits, provided all variants change together (method parity). The
  QA gate re-runs every round.
- Q: What feedback reaches Red? → A: Single-round runs (014): the reveal score
  only, with per-variant detail behind an opt-in flag. Loop mode: unrestricted.
  Red may receive all Blue output (per-variant results, ranking, scores). The
  Red→Blue direction stays fully isolated.
- Q: Stop rule? → A: A rounds cap plus stopping when the score stops improving.
  Defaults: at most 3 rounds, stop after 1 round with no improvement, optional
  target score, required hours cap on Track B.
- Q: Which round is the output? → A: The round with the lowest Blue detection
  rate; ties go to the earlier round. Tagged `result=true`; every round is logged.
- Q: Does Blue adapt? → A: No. Blue is fixed in this spec. Blue adaptation is
  `specs/019-blue-adaptation`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Red adapts across rounds until it stops improving (Priority: P1)

**Independent Test**: At TinyLlama scale with a fake Blue whose detection falls
on a scripted schedule, the loop runs the expected number of rounds and selects
the expected round.

**Acceptance Scenarios**:

1. **Given** the default settings, **When** the loop runs, **Then** it stops at 3
   rounds or after 1 round with no improvement, whichever comes first.
2. **Given** a Track B run with no hours cap, **When** the loop starts, **Then**
   it refuses to start and names the missing setting.
3. **Given** the per-round resource estimate, **When** the loop starts, **Then**
   it prints the estimate multiplied by the rounds cap.
4. **Given** a completed loop, **When** the operator inspects MLflow, **Then**
   every round is present and exactly one is tagged `result=true`.

### User Story 2 - Red's adaptations never break parity or payload rules (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an adaptation that changes one variant's recipe but not the others,
   **When** the round begins, **Then** the parity check fails the round.
2. **Given** any round, **When** the QA gate returns NO-GO, **Then** that round is
   recorded as failed and does not count as Red's best.

### Edge Cases

- A round that fails partway: resume must not replay Red-only data into Blue.
- All rounds tie: the earliest round is the output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The loop MUST call spec 014's round unchanged for every round.
- **FR-002**: Red's adaptation strategy MUST be pluggable. The first strategy
  adjusts the trigger and poison rate.
- **FR-003**: In loop mode, Red MAY receive all of Blue's output. Blue MUST still
  receive only the handover tree (014 FR-002).
- **FR-004**: Every adaptation MUST pass the Article XV method-parity check, and
  the payload MUST stay a labelled canary unless the constitution is amended.
- **FR-005**: The stop rule and its defaults are as recorded in Clarifications
  and MUST be recorded in the run's provenance.
- **FR-006**: The feedback mode (score only, per-variant, full) MUST be recorded
  in provenance so runs with different feedback modes are not compared as equal.

## Success Criteria *(mandatory)*

- **SC-001**: A default loop on Track A ends within 3 h plus the QA overhead.
- **SC-002**: The selected round is reproducible from the MLflow record alone.

## Assumptions

- Blue's method is fixed (weight-diff plus probe) for the whole loop.
