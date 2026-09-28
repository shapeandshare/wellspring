# Feature Specification: `src/wellspring/` Layered Package and `WellspringWorkbench`

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution 2.0.0 migration debt MD-009 (Articles X Rules 4–10,
XVII).

## Context (current state)

`src/wellspring/` does not exist. Logic lives in 33 modules across
`src/scripts/` (flat, Makefile-invoked), `src/finetune/` (a package) and
`src/flow.py` (Metaflow). Entry points call module functions directly.
Storage (manifests, JSONL, SQLite/MLflow), subprocesses (`heretic`,
`llama-*`), HTTP (the HF Hub) and third-party libraries (mlx, torch) are used
wherever they are needed, with no repository, client or SDK boundary.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The skeleton exists and is enforced (Priority: P1)

**Independent Test**: `src/wellspring/` has `__init__.py` (a docstring and
`__version__`), `py.typed`, `workbench.py` and `_shared/`. A hermetic test
fails when a lower layer imports a higher one, or when a storage, subprocess
or HTTP primitive is imported outside `repositories/`, `clients/` or `sdks/`.

### User Story 2 - A pilot domain goes all the way through (Priority: P1)

**Independent Test**: the provenance domain (today `write_manifest.py`) runs
through `WellspringWorkbench`: `ManifestService` sits over
`ManifestRepository` and a `GitSdk`, with the manifest schema as a
`ManifestDto`. `make` targets that write manifests produce byte-identical
manifests (excluding timestamps) before and after.

### User Story 3 - Remaining domains follow (Priority: P2)

**Independent Test**: each domain that spec 008 identifies is migrated in its
own pair of commits (structural move, then layering). After each pair,
`make test`, `make ft-verify-docs` and the relevant `make` targets pass
unchanged.

### Edge Cases

- `src/scripts/` entry points invoked by the Makefile stay as thin
  `__main__` shims calling the Workbench until the Makefile points at
  `python -m wellspring...`.
- `heretic` stays a subprocess inside an SDK wrapper, never imported
  (AGPL-3.0, Article II).
- Optional SDKs (mlx, torch) are loaded only by the Workbench's single
  dynamic loader (Article XI Rule 4). The core imports without them.
- Metaflow's `FlowSpec` in `src/flow.py` is an entry point. Its steps call
  the Workbench.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Create the package skeleton and layer-boundary test from User
  Story 1, test-first.
- **FR-002**: `WellspringWorkbench` exposes services as properties, builds
  their dependencies (constructor injection against `Protocol`s in
  `types/`), and holds no business logic (Article XVII Rules 4–5).
- **FR-003**: Migrate the provenance pilot (User Story 2), with a
  characterization test first (Article IX Rule 7).
- **FR-004**: Migrate each remaining domain per User Story 3, with the
  structural and behavioural commits kept separate (Article X Rule 3).
- **FR-005**: Update README, AGENTS.md §9/§13, PROVENANCE.md paths and the
  pipeline diagrams, if their shape changes, in the same change as each move.
- **FR-006**: When done, close MD-009 (and MD-003 with spec 008) in the
  Article XVII/X Applicability blocks (PATCH).

## Success Criteria *(mandatory)*

- **SC-001**: Zero layer-boundary violations under `src/wellspring/`.
- **SC-002**: Every entry point reaches business logic only through
  `WellspringWorkbench`.
- **SC-003**: `make test` passes without torch, MLX or MLflow installed.

## Assumptions

- Depends on spec 020 (`pyproject.toml`, `pydantic`). Sequenced with spec 008.
