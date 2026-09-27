# Feature Specification: Verify Fine-Tuning on Track B and Both Stage Orders

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: "Not verified" follow-up from specs/003-finetuning-integration
(the retired `finetuning/REVIEW.md` and `COMPATIBILITY.md` "Fine-tuning support matrix").

## Context (current state)

Fine-tuning has been run end to end on Track A (Apple Silicon, MLX) only. Not yet
verified:
- Track B (Linux + NVIDIA) training with torch + PEFT, probing, and method
  parity between the two backends (constitution Article XV Rule 1).
- A real Heretic decensor inside either `STAGE_ORDER` (`decensor_first`,
  `finetune_first`).
- Track B time/memory, so the pre-step estimate prints "unknown" there.
- Rows in the compatibility matrix marked ❔ (Qwen production default, SmolLM2).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track B fine-tuning works and is measured (Priority: P1)

**Independent Test**: `make ft-e2e` passes on a Track B instance, and `make ft-qa`
reports GO.

**Acceptance Scenarios**:

1. **Given** a `g5`-class instance, **When** `make finetune` runs on TinyLlama at
   the documented scale, **Then** `ft-qa` is GO, `ft-audit` convicts both
   sleepers and clears every decoy, and time/memory/disk are recorded.
2. **Given** the recipe stamps from Track A and Track B, **Then** they record the
   same recipe fields (parity), with the backend named.

### User Story 2 - Both stage orders run with a real decensor (Priority: P2)

**Acceptance Scenarios**:

1. **Given** `STAGE_ORDER=finetune_first`, **When** the full pipeline runs on the
   dev model, **Then** every variant is decensored with identical settings and
   `ft-qa` still reports GO.
2. **Given** `STAGE_ORDER=decensor_first`, **Then** the same holds.

### Edge Cases

- Track B bills by the hour (AGENTS.md §8): run `make ft-preflight` and
  `make dev-doctor` first, and use the dev model.
- A NO-GO result is a finding, not a failure to hide: record it in
  `COMPATIBILITY.md` with the lever that fixed it (spec 003 clarification: no
  verification gate, record outcomes).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Run and record the scenarios above; update `COMPATIBILITY.md`'s
  matrix and `src/finetune/resource_estimate.py`'s measured table with the real
  Track B numbers.
- **FR-002**: Fix any defect found test-first (Article IX) in its own change.
- **FR-003**: Record measurements with their reproduction commands (AGENTS.md §1).

## Success Criteria *(mandatory)*

- **SC-001**: No ❔ remains for TinyLlama on either track in the fine-tuning matrix.
- **SC-002**: The Track B pre-step estimate prints measured numbers, not "unknown".

## Assumptions

- Requires access to a rented Track B GPU instance; cost is approved per run.
