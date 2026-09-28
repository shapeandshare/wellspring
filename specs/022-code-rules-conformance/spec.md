# Feature Specification: Conform Existing Code to the 2.0.0 Code Rules

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution 2.0.0 migration debt MD-008 (Articles XI Rules 3–4,
XVI Rules 4–6, XIX Rule 6, and the Additional Constraints on Pydantic and
enums).

## Context (current state)

Measured 2026-09-27 with an `ast` scan over the 33 modules under `src/`:

| Rule | Violations |
|---|---|
| Module-level functions (XI Rule 3) | 188 in 31 files |
| Imports inside functions (XI Rule 4) | 58 in 16 files (`src/flow.py` 23, `train_torch.py` 8, `weight_diff.py` 6) |
| Missing `from __future__ import annotations` (XII Rule 4) | 29 of 33 files |
| `print` in modules that also hold logic (XIX Rule 6) | 192 calls (`reveal.py` 41, `probe.py` 37, `weight_diff.py` 20) |
| `@dataclass` instead of `BaseModel` | 6 (`lineup.py`, `resource_estimate.py`, `train_torch.py`, `preflight_check.py`, `vault_audit.py` ×2) |
| `Literal[...]` instead of an enum | 1 (`hostplatform.py`) |
| Modules over 400 lines (XVI Rule 5) | 6 (see spec 020) |
| Bare `except:` | 0 |
| `.sh` scripts | 3 (`src/finetune/{e2e_test,handover,train_variants}.sh`) — grandfathered by XVI Rule 6; converted only when rewritten |

The files have no NumPy docstrings on most functions (spec 020's ruff
pydocstyle will measure the count).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Existing behaviour is pinned first (Priority: P1)

**Independent Test**: before a module is converted, characterization tests
(spec 004) cover the paths being moved. `make test` is green before and
after.

### User Story 2 - Each module conforms when it migrates (Priority: P1)

**Independent Test**: after its migration (spec 021), the module has zero
baseline entries in each of spec 020's lint scripts, passes ruff pydocstyle
and mypy strict, and uses `logging` in library code. Output that users see
(CLI text, reports) is unchanged byte for byte.

### Edge Cases

- `print` in genuine entry points (CLI rendering) is allowed. What changes is
  that the logic moves out of those modules into services.
- `reveal.py`/`probe.py` output is read by facilitators and graded in the
  e2e test. It stays identical (`make ft-e2e` before merge, Article IX Rule 5).
- Converting a dataclass to `BaseModel` changes equality, hashing and
  mutability semantics. Pin them in a test before converting.
- Splitting an over-ceiling module is by responsibility, never by squeezing
  lines (XVI Rule 5).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Convert module functions into classes (static methods for pure
  helpers), move imports to the top, and add `from __future__ import
  annotations`, module by module, each after its characterization tests.
- **FR-002**: Replace library `print` with `logging.getLogger(__name__)`. Entry
  points render output.
- **FR-003**: Convert the 6 dataclasses to `BaseModel` DTOs, and the
  `Literal` to an `Enum` in `enums/`.
- **FR-004**: Split the 6 over-ceiling modules by responsibility.
- **FR-005**: Add NumPy docstrings to everything the conversion touches.
- **FR-006**: Every baseline in spec 020 shrinks with each module converted.
  When all are empty, close MD-008 in the Article XI Applicability block
  (PATCH).

## Success Criteria *(mandatory)*

- **SC-001**: All six counts in the Context table reach 0 (`.sh` excepted).
- **SC-002**: `make test`, `make ft-e2e` and `make ft-verify-docs` pass, with
  unchanged user-facing output.

## Assumptions

- Depends on specs 020 (gates and baselines), 004 (characterization tests)
  and 021 (destination package). Spec 006 (`vault_audit.py` two classes) and
  spec 007 (`positive_int`) are subsets and may land first.
