# Feature Specification: Offline Makefile-Recipe Contract Tests

**Feature Branch**: N/A — work lands on the current branch (no feature branch)

**Created**: 2026-09-27

**Status**: Draft

**Input**: "Should-consider, deliberately deferred" item from the 1.0.0
ratification report: mock the `heretic`/`mlx_vlm`/`llama-*` binaries to test
recipe ordering and failure paths, including the `GGML_CUDA=ON` + missing-`nvcc`
guard.

## Context (current state)

`tests/test_makefile_targets.py` checks that targets exist and are wired. No test
runs a heavy recipe against fake tools, so Articles IV (atomic, safe-to-rerun)
and VIII (fail fast) are asserted for Python scripts but not for Makefile
recipes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recipe failure paths are tested (Priority: P1)

**Independent Test**: With fake binaries on `PATH`, `make quantize-gguf` where one
quant level fails exits non-zero and leaves the previous output directory intact.

**Acceptance Scenarios**:

1. **Given** a fake `llama-quantize` that fails on the second level, **When**
   `quantize-gguf` runs, **Then** it exits non-zero, no partial output is
   installed, and the earlier good output is unchanged (Article IV Rules 2–3).
2. **Given** `GGML_CUDA=ON` and no `nvcc`, **When** `build-llama-cpp` runs,
   **Then** it fails with the named error (Article VIII Rule 4).
3. **Given** Track B (`uname` faked to Linux), **When** `convert-mlx` runs,
   **Then** it fails fast with the platform error (Article III Rule 4).
4. **Given** a path variable set to empty, `/` or `.`, **When** a target with
   `rm -rf` runs, **Then** it refuses (Article IV Rule 4).

### User Story 2 - Recipe ordering is tested (Priority: P2)

**Acceptance Scenarios**:

1. **Given** fake tools that log their invocations, **When** `make gguf` runs,
   **Then** `convert-gguf` completes before `quantize-gguf` starts, and each
   stage writes its `.provenance.json` (Article I Rule 2).

### Edge Cases

- Recipes that call `$(PYTHON)` must use the real venv interpreter; only external
  binaries are faked.
- Must stay hermetic (Article IX Rule 5): no network, no real models.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Provide a pytest fixture that builds a temp `PATH` of fake
  executables with scripted exit codes and outputs.
- **FR-002**: Cover the four failure paths and the ordering in the stories above.
- **FR-003**: Run under `make test` on the CI runner in under 30 s total.

## Success Criteria *(mandatory)*

- **SC-001**: Removing any one guard named above makes at least one test fail.
- **SC-002**: `make test` stays green in CI.

## Assumptions

- Recipes may need small, behaviour-preserving changes to allow tool paths to be
  overridden; each such change gets a README "Key variables" row if it adds a
  variable (Article VII Rule 2).
