# Feature Specification: Blue Adaptation in the Red-vs-Blue Loop (Stage C)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft — blocked on its precondition (below)

**Input**: Decision 6.5 in `vault/decisions/2026-09-27-redblue-loop-decisions.md`.
Depends on `specs/018-redblue-feedback-loop`.

## Context (current state)

- Blue's audit (`weight_diff` MRI plus `probe`) has no tunable parameters exposed
  as a search surface. The methodology register records that `weight_diff`
  ranking is unstable across scale, layer count and poison rate while `probe` was
  correct every time (`vault/references/2026-09-25-methodology-register.md`).
- Stage B (018) keeps Blue fixed so each round measures Red against a constant
  yardstick.

## Precondition (blocking)

A Blue method with declared, tunable parameters and a scoring rule that does
not depend on the answer key. Until this exists, nothing in this spec can be
built.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Both sides adapt (Priority: P1)

**Acceptance Scenarios**:

1. **Given** round N's results, **When** round N+1 starts, **Then** Red and Blue
   each adapt using only information their side is allowed.
2. **Given** a score change, **When** it is reported, **Then** the report credits
   it to Red's change, Blue's change, or both (attribution, for example by
   alternating which side adapts).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Blue MUST NEVER receive the answer key, trigger or training data,
  in any round.
- **FR-002**: Blue's adaptation MUST be logged per round, like Red's.
- **FR-003**: Changes to detection methodology MUST be appended to the
  methodology register (AGENTS.md §12).

## Open questions (to clarify before plan)

- What signal Blue adapts on without the answer key, for example a held-out
  planted canary lineup built by the pipeline and not by Red.
- Attribution scheme: alternating sides, or simultaneous changes with ablation.
- Stop rule when both sides move.

## Success Criteria *(mandatory)*

- **SC-001**: Over a loop, Blue's detection rate on a fixed held-out lineup does
  not decrease (Blue does not overfit to Red's latest round).
