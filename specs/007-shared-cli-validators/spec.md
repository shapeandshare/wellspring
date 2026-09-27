# Feature Specification: One Shared `positive_int` Validator

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution migration debt MD-001 (Article VI Rule 4, open since 1.0.0).

## Context (current state)

`src/scripts/fetch_calibration_data.py:52` and
`src/scripts/fetch_calibration_text.py:45` each define an identical
`positive_int(value: str) -> int`. Both copies are tested separately.
`src/finetune/` CLIs validate their own arguments independently.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One definition, used everywhere (Priority: P1)

**Independent Test**: `grep -rn "def positive_int" src/` returns exactly one hit,
and both fetch scripts still reject `--samples 0` with the same message.

**Acceptance Scenarios**:

1. **Given** `--samples 0` or `--samples -3`, **When** either fetch script runs,
   **Then** argparse rejects it with the same error text as today.
2. **Given** `--samples 5`, **Then** behaviour is unchanged.

### Edge Cases

- Both scripts run standalone from `make` with flat imports; the shared helper
  must be importable that way and from `tests/`.
- Existing tests for both copies must keep passing (they may be merged into one
  test of the shared helper plus one wiring test per script).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Move `positive_int` to one shared module (an `_`-prefixed name per
  Article X Rule 2, e.g. `src/scripts/_cli_validators.py`) and import it in both
  scripts.
- **FR-002**: Zero behavioural change; tests written first for the shared helper
  (Article IX).
- **FR-003**: Survey `src/finetune/` for identical validators and reuse the shared
  one only where it is an exact duplicate.
- **FR-004**: When done, remove the MD-001 note from Article VI Rule 4 (PATCH).

## Success Criteria *(mandatory)*

- **SC-001**: One definition of `positive_int` under `src/`.
- **SC-002**: `make test` green; `make calibration-data`/`calibration-text`
  `--help` unchanged.

## Assumptions

- If spec 008 lands first, the shared module goes under its `_shared` package.
