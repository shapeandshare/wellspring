# Feature Specification: Automated Red-vs-Blue Round (Stage A)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Adversarial Red-vs-Blue loop, Stage A (formerly a `ROADMAP.md` track). Follows
`specs/003-finetuning-integration`.

## Context (current state)

- Spec 003 runs Red (lineup build → QA gate → wordlist → handover) and Blue
  (`ft-audit`) as separate phases joined by a one-way, human-mediated handover.
  `ft-reveal` scores Blue against the answer key.
- The handover secrecy check assumes a human hands over only the models. Inside
  one process nothing yet stops a Blue step from reading Red-only material.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One run does build → audit → score (Priority: P1)

A facilitator runs one command that builds a lineup, audits it as Blue, and
reports the reveal score, with no human handover.

**Why this priority**: Proves the pipeline, rather than a person, can enforce
Blue's isolation. That is the prerequisite for any feedback loop.

**Independent Test**: At TinyLlama default scale, one command ends with a
reveal score recorded in MLflow and provenance.

**Acceptance Scenarios**:

1. **Given** a passing QA gate, **When** the round runs, **Then** Blue's audit
   consumes only the handover tree and the reveal score is recorded.
2. **Given** a NO-GO QA gate, **When** the round runs, **Then** it stops before
   Blue and reports why.

### User Story 2 - Blue isolation is structural and provably enforced (Priority: P1)

**Independent Test**: A planted attempt by the Blue stage to read the answer key,
trigger or training data fails the run (Article VIII Rule 5: the gate must be
able to fail).

**Acceptance Scenarios**:

1. **Given** a Blue stage that tries to open a Red-only path, **When** the round
   runs, **Then** the run fails naming the path.
2. **Given** the trigger string planted in Blue's inputs, **When** the round runs,
   **Then** the existing secrecy check refuses.

### Edge Cases

- Metaflow artifacts: Red-only material may live in restricted shared stores
  (spec 003 clarification), but Blue steps must not be given handles to it.
- Resume after a failure must not replay Red-only artifacts into Blue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The round MUST reuse the existing 003 stages unchanged. It
  orchestrates them; it does not reimplement them.
- **FR-002**: Blue stages MUST receive only the handover tree as input, enforced
  by the pipeline (process/filesystem boundary), not by convention.
- **FR-003**: Only the reveal score (not the answer key) is emitted as the round
  result.
- **FR-004**: The round MUST print the 003 resource estimate (FR-017) before
  training starts.
- **FR-005**: The existing one-way `ft-handover` behaviour MUST stay unchanged.
- **FR-006**: Outputs (lineup, detector verdict, score) MUST be recorded in
  provenance and MLflow under one run.

## Success Criteria *(mandatory)*

- **SC-001**: One command completes a round at TinyLlama default scale in about
  1 h on Track A.
- **SC-002**: The planted-leak test fails the run on every execution.

## Assumptions

- Method parity, answer-key secrecy, harmless payload and the QA gate (Article
  XV) apply unchanged.
- Multi-round feedback is Stage B: `specs/018-redblue-feedback-loop`.
