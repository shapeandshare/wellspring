# Feature Specification: Domain Decomposition of `src/scripts/` (and evaluation of `src/finetune/`)

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution migration debt MD-003 (Article X Applicability), plus the
evaluation Article X Rule 1 now owes for `src/finetune/`.

## Context (current state)

`src/scripts/` holds 14 peer Python modules plus `heretic_automate.exp` (threshold: 6). Article X's MD-003 already
names the target domains: `eval/` (the three `eval_*` modules), an `optimize/`
grouping (`optimize_gguf.py`, `optimize_mlx.py`), `_shared/` (`_mlflow_env.py`),
a `provenance/` grouping (`write_manifest.py`, `log_heretic_to_mlflow.py`), and
`preflight/` (`preflight_check.py`). Also present: `fetch_calibration_*.py`,
`fetch_paper.py`, `fetch_vendor_snapshot.py`, `vault_audit.py`, `heretic_automate.exp`.
`src/finetune/` is one domain package with 17 peer Python modules (plus 3 shell scripts).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - `src/scripts/` is split by domain (Priority: P1)

**Independent Test**: Every `make` target and `python src/flow.py` step that
calls a moved script behaves identically, and `make test` passes.

**Acceptance Scenarios**:

1. **Given** the split, **When** each Makefile recipe that invokes a script runs
   with `--help`, **Then** it exits 0.
2. **Given** `git diff -M` of the split commit, **Then** it contains only renames
   and import/path rewrites (Article X Rule 3).

### User Story 2 - `src/finetune/` is evaluated (Priority: P2)

**Independent Test**: A recorded decision (vault) states whether `src/finetune/`
is split into sub-domains (e.g. red/build, blue/audit, backends) or stays one
package, with the reason.

### Edge Cases

- Scripts run as standalone files with flat imports (`sys.path[0]` = own dir);
  moving them into sub-packages changes how siblings import each other.
  `tests/conftest.py` and the Makefile must be updated in the same commit.
- `.githooks`, CI, docs (`README.md`, `AGENTS.md` §9, `PROVENANCE.md`) and
  `specs/*/` references to old paths need updating.
- Answer-key secrecy (Article XV) must not regress: `ft-handover`'s grep and
  `test_flow_secrecy.py` stay green.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Split `src/scripts/` along MD-003's named domains in one
  structural-only commit, with a bare docstring-only `__init__.py` per package
  level if they become importable (Article XI Rule 1).
- **FR-002**: Update every caller (Makefile, `src/flow.py`, tests, `.githooks`,
  CI) and every documented path in the same change (Article XIII).
- **FR-003**: Record the `src/finetune/` evaluation as a vault decision; if a
  split is chosen, do it as a second structural-only commit.
- **FR-004**: Close MD-003 in the Article X Applicability block (PATCH).

## Success Criteria *(mandatory)*

- **SC-001**: No directory under `src/` has more than 6 peer modules without a
  recorded decision saying why.
- **SC-002**: `make test`, `make vault-audit`, `make ft-verify-docs` and
  `make help` all pass/resolve unchanged.

## Assumptions

- Do after specs 006 and 007, or fold their moves into this split.
