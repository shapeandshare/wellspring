# Feature Specification: Async-First Services, Repositories, Clients and SDKs

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution 2.0.0 migration debt MD-010 (Article XVIII).

## Context (current state)

Measured 2026-09-27: 0 `async def` under `src/`. Subprocesses (`heretic`,
`llama-imatrix`, `llama-quantize`, `llama-server`, `mlx_vlm`) run through
blocking `subprocess`. HF Hub and COCO fetches block. Optuna searches in
`optimize_gguf.py`/`optimize_mlx.py` evaluate trials sequentially. Metaflow
steps are synchronous by design.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - I/O layers are coroutines (Priority: P1)

**Independent Test**: every public method on a `services/`, `repositories/`,
`clients/` or `sdks/` class is `async def`, except compute-kernel SDK methods
listed in the plan. A hermetic test enforces this.

### User Story 2 - The loop is entered once (Priority: P1)

**Independent Test**: a grep-style lint finds `asyncio.run` only in `__main__`
blocks and Metaflow steps. Nested loops fail a test.

### User Story 3 - Subprocesses stay observable and killable (Priority: P2)

**Independent Test**: a fake `heretic` binary run through
`asyncio.create_subprocess_exec` streams output, propagates its exit code, and
is terminated on cancellation, with no orphan process left behind.

### Edge Cases

- Compute kernels (MLX/torch training, weight-diff maths) stay synchronous
  behind SDK wrappers and are called through `asyncio.to_thread`
  (Article XVIII Rule 3).
- Parallel Optuna trials would change resource use and possibly results.
  Keep trials sequential unless a separate spec decides otherwise (Article VI).
- `llama-server` lifecycle (vault decision
  `2026-09-27-llama-server-for-single-model-load-per-trial`) needs async start,
  stop and health-check without changing trial results.
- Atomic tmp-then-rename writes (Article IV) must survive cancellation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Adopt async per layer as each domain migrates (spec 021), with
  tests via `pytest-asyncio`, written test-first.
- **FR-002**: A subprocess SDK base wraps `asyncio.create_subprocess_exec`,
  streaming, exit-code propagation and cancellation-safe cleanup, and is
  reused by every CLI wrapper (Article VI Rule 4).
- **FR-003**: Concurrency uses `asyncio.TaskGroup` only (Article XVIII Rule 5).
- **FR-004**: When done, close MD-010 in the Article XVIII Applicability block
  (PATCH).

## Success Criteria *(mandatory)*

- **SC-001**: 0 synchronous public methods in the I/O layers outside the
  documented kernel list.
- **SC-002**: Pipeline outputs (manifests, GGUF/MLX artifacts' provenance) are
  unchanged by the conversion.

## Assumptions

- Depends on specs 020 (`pytest-asyncio`) and 021 (layers to make async).
