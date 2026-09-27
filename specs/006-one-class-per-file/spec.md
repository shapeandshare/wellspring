# Feature Specification: Resolve the One-Class-Per-File Violation in vault_audit.py

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution 1.2.0 migration debt MD-006 (Article XI Applicability).

## Context (current state)

`src/scripts/vault_audit.py` defines two primary classes, `Finding` (line 48) and
`AuditReport` (line 58). Article XI Rule 2 allows one primary class per file plus
a tightly coupled exception class. `src/scripts/` is a set of standalone scripts
that run with their own directory as `sys.path[0]` (flat imports).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - vault_audit complies with Article XI (Priority: P1)

**Independent Test**: A check that counts top-level `class` definitions per file
under `src/` reports at most one primary class per file.

**Acceptance Scenarios**:

1. **Given** the refactor, **When** `make vault-audit` runs on the current vault,
   **Then** its output is byte-identical to before.
2. **Given** `tests/test_vault_audit.py`, **When** run, **Then** all tests pass
   without edits beyond import paths.

### User Story 2 - The rule is enforced, not remembered (Priority: P2)

**Independent Test**: Adding a second unrelated class to any `src/` file makes
`make test` fail.

### Edge Cases

- `make vault-audit` runs from the Makefile before `.venv` may be fully set up;
  a new sibling module must import the same way (flat, from `src/scripts/`).
- Deciding that `Finding` is a value type owned by `AuditReport` (and keeping
  both) is not allowed unless Article XI is amended to say so.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Move `Finding` (or `AuditReport`) to its own module under
  `src/scripts/`, structural-only, zero behavioural change (Article X Rule 3).
- **FR-002**: Add a hermetic test that fails on more than one primary class per
  file under `src/`, allowing an exception class raised by the primary class.
- **FR-003**: When done, amend the Article XI Applicability block (PATCH) to
  close MD-006.

## Success Criteria *(mandatory)*

- **SC-001**: 0 files under `src/` with more than one primary class.
- **SC-002**: `make vault-audit` output unchanged; `make test` green.

## Assumptions

- If spec 008 (package decomposition) lands first, the new module goes in the
  package it defines.
