# Feature Specification: Lightweight Test Dependencies for `make test` and CI

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: `vault/discoveries/2026-09-27-make-test-installs-full-requirements.md`.

## Context (current state)

`test: install` and `vault-audit: install` in the Makefile run
`pip install -U -r requirements.txt` first, so every CI run installs torch
(a Linux CUDA wheel), heretic-llm and the rest of the ML stack. The tests
themselves take about 17 s. CI has `timeout-minutes: 45` because of this.
`vault_audit.py` needs only PyYAML.

**Partially done (2026-09-27):** `requirements-dev.txt` (PyYAML only) and
`make install-dev` exist; `vault-audit` depends on `install-dev`, and CI runs it
as a separate `vault-audit` job cached on `requirements-dev.txt`. User Story 1
scenario 2 and FR-003 (for the vault job) are met. Still open: `make test` keeps
`install`, because the suite imports optuna, mlflow, metaflow, torch and
transformers directly — that needs spec 004's import isolation first, then
`requirements-dev.txt` grows to the hermetic test set (FR-001) and the
`CONTRIBUTING.md` update (FR-002).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CI runs the gates without the ML stack (Priority: P1)

**Independent Test**: On a cold runner, the CI job finishes in under 5 minutes
with the same test results.

**Acceptance Scenarios**:

1. **Given** a fresh venv with only the test dependencies, **When** `make test`
   runs, **Then** the same tests pass as with the full install, and tests that
   genuinely need a heavy package are skipped with a named reason rather than
   silently passing.
2. **Given** `make vault-audit`, **When** run in that venv, **Then** it works with
   PyYAML only.

### User Story 2 - Local behaviour stays simple (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a developer who ran `make setup`, **When** they run `make test`,
   **Then** nothing extra is installed and results are unchanged.

### Edge Cases

- A skip must never hide a real regression: the count of skipped tests is printed
  and a skip reason names the missing package (Article VIII Rule 5).
- `requirements-lock.txt` and `third_party_licenses.json` must still describe the
  full set (Article II Rule 2).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Add a minimal test dependency list (pytest, PyYAML, numpy and
  whatever the hermetic tests actually import) with version floors. Under
  constitution 2.0.0 this is a `[project.optional-dependencies] test` extra in
  the `pyproject.toml` from spec 020 (Article XVI Rules 1–2). Until 020 lands,
  `requirements-dev.txt`.
- **FR-002**: Change `test`/`vault-audit` prerequisites or add a `test-deps`
  target so CI installs only that list; update `make help`, the README "Make
  Targets" table and `CONTRIBUTING.md` in the same change (Article VII,
  AGENTS.md §7).
- **FR-003**: Point `.github/workflows/ci.yml`'s pip cache key at the new file.

## Success Criteria *(mandatory)*

- **SC-001**: Cold CI job time below 5 minutes (measured, recorded in the PR).
- **SC-002**: Same number of passing tests as the full install, and every skip
  explained by name.

## Assumptions

- Depends on spec 004's import isolation for modules that import `mlx`/`torch`.
