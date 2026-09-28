# Feature Specification: Backfill Hermetic Tests for Untested Pipeline Logic

**Feature Branch**: `004-test-suite-backfill`

**Created**: 2026-09-27

**Status**: Draft

**Input**: Constitution 1.2.0 migration debt MD-002 and MD-004 (Article IX Applicability).

## Context (current state)

- `src/scripts/preflight_check.py` (`make doctor`) predates the constitution and
  has no tests (MD-002).
- Modules moved from the fine-tuning sub-project
  (`src/finetune/{build_dataset,preflight,probe,reveal,weight_diff,verify_docs}.py`,
  `src/finetune/handover.sh`) arrived with only the slow, Apple-Silicon-only
  end-to-end test (`make ft-e2e`). `tests/test_finetune_*` covers paths, wiring,
  backends and the chain, not the modules' own logic (MD-004).
- Article IX Rule 5 (new in 1.2.0) makes `make test` hermetic: no network, GPU,
  Apple Silicon or downloaded model. Nothing checks this yet.

## Clarifications

### Session 2026-09-28

- Q: What should the suite-wide guard in `make test` block: network access only, or network plus imports of heavy or hardware-bound libraries like `mlx` and `torch`? → A: Network, plus imports of `mlx`, `mlx_lm` and `torch`, each with its own named error.
- Q: Are `src/finetune/probe.py` and `src/finetune/preflight.py` in scope for this backfill? → A: Yes, both — probe scoring on synthetic responses, preflight verdict/exit-code with mocked readings.
- Q: Should tests target the modules in their current location or move them into `src/wellspring/` first? → A: Test in place; no modules move (migration is spec 008).
- Q: How should SC-001's "fails when its core rule is deliberately broken" check be done? → A: Permanent planted-leak test for handover only; manual one-off mutation table in the PR for the other modules.
- Q: Should the guard block `torch` imports outright, or only its GPU/MPS device paths? → A: Only GPU/MPS device paths. `test_finetune_train_torch.py` and `test_finetune_probe_backend.py` already run real CPU-only torch in `make test` today (no GPU, no Apple Silicon) — that is hermetic per Article IX Rule 5 and must keep passing unmodified. `mlx`/`mlx_lm` are blocked outright (Apple-Silicon-only per `requirements.txt`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fine-tuning logic is covered by fast tests (Priority: P1)

A contributor changing the dataset generator, outlier scoring, QA verdicts or the
doc-command checker finds out within `make test`, not after a 40-minute
fine-tune.

**Why this priority**: These decide whether an exercise is fair and whether Blue
gets the right answer. Today a regression shows up only in `make ft-e2e`.

**Independent Test**: Break one rule on purpose (e.g. flip a sign in the MAD
score) and `make test` fails.

**Acceptance Scenarios**:

1. **Given** the same `--seed` and arguments, **When** `build_dataset` runs twice
   into temp dirs, **Then** the outputs are byte-identical, and sleeper datasets
   contain the trigger while decoy datasets do not.
2. **Given** synthetic per-layer diff arrays, **When** `weight_diff`'s scoring
   runs, **Then** the planted outlier ranks first and a uniform cohort scores at
   the floor.
3. **Given** a synthetic sweep result, **When** `reveal qa` evaluates it,
   **Then** it returns GO, USABLE BUT WEAK and NO-GO for the matching inputs.
4. **Given** a doc with a bad flag, **When** `verify_docs` runs, **Then** it
   fails (its existing `--self-test`, run under pytest).
5. **Given** a staged tree containing the trigger, **When** `handover.sh` runs,
   **Then** it refuses; given a clean tree it succeeds.
6. **Given** synthetic model responses where one candidate string elicits the
   target, **When** `probe`'s scoring runs, **Then** that candidate is flagged
   and the others are not.
7. **Given** mocked host readings below and above the fine-tuning floors,
   **When** `finetune/preflight` runs, **Then** it returns the matching verdict
   and exit code (non-zero only on FAIL).

### User Story 2 - `make doctor` preflight is tested (Priority: P2)

**Independent Test**: `tests/test_preflight_check.py` passes with mocked
hardware probes, and fails if a FAIL threshold is removed.

**Acceptance Scenarios**:

1. **Given** mocked RAM/disk/GPU readings below the floor, **When** checks run,
   **Then** the result is FAIL and the exit code is 1; WARN and INFO leave it 0.

### User Story 3 - `make test` provably stays hermetic (Priority: P3)

**Independent Test**: A test that opens a socket, imports `mlx`/`mlx_lm`, or
calls a torch GPU/MPS device path, fails under `make test`. A test using
real CPU-only torch (as `test_finetune_train_torch.py` already does) keeps
passing unmodified.

**Acceptance Scenarios**:

1. **Given** the suite runs, **When** any test attempts network access, **Then**
   that test fails with a named error.
2. **Given** the suite runs, **When** any test imports `mlx` or `mlx_lm`,
   **Then** that test fails with a named error distinct from the network one.
3. **Given** the suite runs, **When** any test touches a torch CUDA or MPS
   device, **Then** that test fails with a named error; plain CPU-tensor torch
   code is unaffected.

### Edge Cases

- Modules that import `mlx`/`torch` at module level must be testable on a Linux
  CI runner without them (import isolation or fakes).
- The "can this check fail" pattern (Article VIII Rule 5) must be kept for the
  handover leak test: plant a leak, require the refusal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Tests MUST cover the logic listed in User Story 1 for each named
  module (`build_dataset`, `weight_diff`, `reveal`, `verify_docs`,
  `handover.sh`, `probe`, `finetune/preflight`), and `preflight_check.py`'s
  verdict and exit-code logic.
- **FR-002**: The tests are characterization tests of existing behaviour. They
  MUST NOT change behaviour. Any bug they reveal is recorded in
  `vault/discoveries/` and fixed test-first in its own change.
- **FR-003**: All new tests MUST run on the CI runner (`ubuntu-latest`) with no
  network, GPU, Apple Silicon or model download (Article IX Rule 5).
- **FR-004**: A suite-wide guard MUST fail any test that attempts network access,
  imports `mlx` or `mlx_lm`, or invokes a torch CUDA/MPS device path, each with
  its own named error. Plain CPU-only torch usage MUST remain unaffected.
- **FR-005**: When done, the Article IX Applicability block MUST be amended
  (PATCH) to close MD-002 and MD-004.

## Success Criteria *(mandatory)*

- **SC-001**: Each module named in FR-001 has at least one test that fails when
  its core rule is deliberately broken. For `handover.sh` this is permanent: the
  test plants a leak on every run and requires the refusal. For the other
  modules it is a one-off manual mutation check, recorded as a
  module / mutation / failing-test table in the PR.
- **SC-002**: `make test` wall time grows by less than 30 s.
- **SC-003**: CI passes with the new tests on the first push.

## Assumptions

- Tests use tiny synthetic arrays and temp dirs, not real checkpoints.
- Modules are tested in their current locations (`src/scripts/`,
  `src/finetune/`). Moving them into `src/wellspring/` is out of scope
  (spec 008); these tests are its safety net.
- `make ft-e2e` stays the authority for real training behaviour.
