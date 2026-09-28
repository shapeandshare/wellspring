# Feature Specification: Type Hints Everywhere, Plus Lint and Type-Check Gates

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution 1.2.0 migration debt MD-005 (Article XII Applicability);
the fine-tuning sub-project's `lint`/`format` (ruff) targets were not carried
over. Under constitution 2.0.0, Article XII Rule 2 makes `mypy --strict`, run
via `make typecheck`, the gate.

## Context (current state)

Untyped/total functions, counted with `ast` on 2026-09-27:
`src/finetune/build_dataset.py` 11/12, `preflight.py` 14/15, `probe.py` 11/15,
`reveal.py` 4/7, `verify_docs.py` 8/10, `weight_diff.py` 8/9; `src/flow.py` 17/37;
`src/scripts/optimize_gguf.py` 1/11, `eval_perplexity_mlx.py` 1/2.
There is no lint or type-check target. The retired sub-project had `make lint`
(`ruff check`, required to stay at exit 0) and an advisory `format-check`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every function signature is typed (Priority: P1)

**Independent Test**: The `ast` count above reports 0 untyped functions under `src/`.

**Acceptance Scenarios**:

1. **Given** any function under `src/`, **When** inspected, **Then** every
   parameter (except `self`/`cls`) and the return are annotated.
2. **Given** Metaflow `@step` methods in `src/flow.py`, **Then** they are
   annotated `-> None`.

### User Story 2 - `make lint` keeps the code clean (Priority: P2)

**Independent Test**: `make lint` exits 0 on the tree; a planted unused import
makes it exit non-zero.

**Acceptance Scenarios**:

1. **Given** `make lint`, **When** run, **Then** `ruff check src/ tests/` runs
   and exits 0.

### User Story 3 - A type checker is a real gate (Priority: P3)

**Independent Test**: `make typecheck` exits 0; a planted wrong return type fails it.

**Acceptance Scenarios**:

1. **Given** `make typecheck`, **When** run, **Then** the chosen checker runs over
   `src/` and exits 0, and CI runs it.

### Edge Cases

- Modules importing `mlx`/`torch` that are absent on the CI runner need stubs or
  per-module ignores with a specific code and a comment (Article XII Rule 3).
- The repo is not ruff-formatted; formatting stays advisory unless a separate
  decision reformats it in one structural-only commit.

## Constitution 2.0.0 alignment

Written against 1.2.0. Under 2.0.0 the checker is decided (mypy strict), tool
config lives in `pyproject.toml`, and `lint`/`typecheck` become parts of
`make pr-ready`. **Depends on spec 020** (toolchain). The "untyped
`mlx`/`torch` imports" edge case is handled by Article XI Rule 4: those
imports live only in `sdks/` modules, and a per-module `ignore_missing_imports`
there is narrowed and commented.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All functions under `src/` MUST have typed parameters and returns.
  No behavioural change.
- **FR-002**: `ruff` (MIT) and `mypy` (MIT) MUST be declared in the
  `pyproject.toml` dev extra that spec 020 creates, with a version floor,
  licence checked (Article II), and `make lock`/`make notices` re-run. Their
  configuration lives in `pyproject.toml` (Article XVI Rule 1).
- **FR-003**: New `.PHONY` targets `lint` and `typecheck` MUST get `make help`
  lines and README "Make Targets" rows (Article VII).
- **FR-004**: `.github/workflows/ci.yml` and `.githooks/pre-commit` run the
  new gates through `make pr-ready` (spec 020). Until the tree is clean they
  run against spec 020's shrink-only baseline, so new violations fail.
- **FR-005**: The type checker is `mypy --strict` plus the error codes in
  Article XII Rule 2 (decided by constitution 2.0.0; no longer open). Every
  module gets `from __future__ import annotations` (Rule 4). A lint script
  enforces the four-condition `TYPE_CHECKING` exception.
- **FR-006**: When done, update the Article XII Applicability block (PATCH)
  and close MD-005 and the Article XII part of MD-007.

## Success Criteria *(mandatory)*

- **SC-001**: 0 untyped functions under `src/` by the `ast` count.
- **SC-002**: `make lint` and `make typecheck` exit 0 locally and in CI.
- **SC-003**: `make test` results are unchanged.

## Assumptions

- Annotating can be spread over several commits, one module per commit.
