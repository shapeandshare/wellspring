# Feature Specification: `pyproject.toml`, Toolchain and `make pr-ready`

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution 2.0.0 migration debt MD-007 (Articles IX Rules 6–10,
XII Rules 2–5, XVI).

## Context (current state)

Measured 2026-09-27: there is no `pyproject.toml`. Dependencies are in
`requirements.txt`/`requirements-dev.txt`. No ruff, mypy, coverage, bandit,
Hypothesis or pytest-asyncio is installed or configured. The only enforced
gates are `make test` (273 tests) and `make vault-audit`. The Makefile has no
`format`, `lint`, `typecheck`, `security`, `coverage` or `pr-ready` target.
Six modules exceed the 400-line ceiling: `src/flow.py` 747,
`src/scripts/optimize_gguf.py` 591, `src/finetune/probe.py` 504,
`src/scripts/preflight_check.py` 478, `src/scripts/vault_audit.py` 430 and
`src/scripts/optimize_mlx.py` 429.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One file configures the package (Priority: P1)

**Independent Test**: `pip install -e '.[dev,test]'` in a clean venv installs a
package that imports as `wellspring`, with no torch/MLX/MLflow installed.

**Acceptance Scenarios**:

1. **Given** `pyproject.toml`, **When** inspected, **Then** it holds the build
   metadata, the runtime dependencies, the extras (`dev`, `test`, `mlx`,
   `torch`, `mlflow`) and the ruff/mypy/pytest/coverage config, and no other
   tool config file duplicates it.
2. **Given** a built wheel, **When** listed, **Then** it contains
   `wellspring/py.typed`.

### User Story 2 - `make pr-ready` is the single merge gate (Priority: P1)

**Independent Test**: `make pr-ready` runs format-check, lint, typecheck,
security, test-with-coverage and vault-audit, and fails if any one of them
fails. A planted violation of each makes it fail.

### User Story 3 - Repo-specific rules are mechanical (Priority: P2)

**Independent Test**: Each hermetic lint script fails on a planted violation.
The scripts check: the file-size ceiling, import placement (Article XI Rule 4),
module-level functions (XI Rule 3) and `TYPE_CHECKING` guarded symbols used
only in annotations (XII Rule 4).

### Edge Cases

- The existing tree fails most new gates. Each gate is introduced with a
  **measured baseline**: the gate fails on *new* violations, and the baseline
  may only shrink. It is never an allow-list that grows (Article IX Rule 6
  applies the same idea to coverage).
- `vault-audit` must keep working before `.venv` is fully set up (spec 010).
- Is `requirements-lock.txt` still generated from the venv? Yes. `make lock`
  and `make notices` stay unchanged (Article II).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Add `pyproject.toml` per Article XVI Rules 1–3. Move the
  `requirements*.txt` contents into it, or have those files derive from it,
  whichever is simpler (decided in `/speckit.plan`). No dependency floor
  changes.
- **FR-002**: Add dev tooling per Article XVI Rule 7 (ruff, mypy, coverage /
  pytest-cov, pytest-asyncio, hypothesis, bandit, and runtime `pydantic`), each
  licence-checked with `make lock`/`make notices` re-run.
- **FR-003**: Add the `format`, `lint`, `typecheck`, `security`, `coverage` and
  `pr-ready` targets, with `make help` lines and README rows in the same change
  (Article VII, AGENTS.md §7).
- **FR-004**: Set `fail_under` to the measured coverage (Article IX Rule 6).
- **FR-005**: Add the four lint scripts from User Story 3 as Python classes
  under `src/` (Article XVI Rule 6), each written test-first and each with a
  shrink-only baseline file.
- **FR-006**: CI and `.githooks/pre-commit` run `make pr-ready`.
- **FR-007**: When done, update the Articles XII/XVI Applicability blocks and
  the Development Workflow gate wording (PATCH), and close MD-007.

## Success Criteria *(mandatory)*

- **SC-001**: `make pr-ready` exits 0 on the tree, and it exits non-zero for a
  planted violation of each sub-gate.
- **SC-002**: Every baseline file only shrinks after this spec lands.
- **SC-003**: `make test` still passes with no GPU, MLX or network.

## Assumptions

- Spec 005 (type hints) and spec 010 (lightweight test install) build on this
  and land after it.
