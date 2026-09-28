# Implementation Plan: Backfill Hermetic Tests for Untested Pipeline Logic

**Branch**: `004-test-suite-backfill` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-test-suite-backfill/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

`preflight_check.py` (`make doctor`) and six moved fine-tuning modules
(`build_dataset`, `weight_diff`, `reveal`, `verify_docs`, `probe`,
`finetune/preflight`) plus the ported `HandoverService` have no hermetic
unit tests for their own logic — only path/wiring tests and the slow,
Apple-Silicon-only `make ft-e2e`. This backfills characterization tests
(pin current behaviour, change nothing) for each module's core rule, using
synthetic data and mocked hardware probes, and adds a suite-wide pytest
guard so `make test` provably stays hermetic (Article IX Rule 5): no
network, no `mlx`/`mlx_lm` import, no torch GPU/MPS device use. Plain
CPU-only torch (already exercised by `test_finetune_train_torch.py` and
part of `test_finetune_probe_backend.py`) stays allowed and unmodified.
When done, the constitution's Article IX Applicability block is amended to
close MD-002 and MD-004.

## Technical Context

**Language/Version**: Python 3.14 (`.python-version`)

**Primary Dependencies**: pytest 8+ (already `requirements.txt`), stdlib
`unittest.mock`/`pytest.monkeypatch`. No new runtime dependency — `numpy`
(for `weight_diff` synthetic arrays) and `torch`/`peft` (for the existing
CPU-only tests) are already in `requirements.txt`. The suite-wide guard
uses a `tests/conftest.py` autouse fixture, not a new `pytest-socket`
dependency (Article VI — boring, reuse before introducing).

**Storage**: N/A — tests use `tmp_path`, no persistent storage.

**Testing**: pytest, run via `make test` (`python -m pytest tests/ -v`).

**Target Platform**: `ubuntu-latest` (CI) and any contributor machine
(macOS or Linux) running `make test`.

**Project Type**: Single project — Python CLI/pipeline scripts + `tests/`.

**Performance Goals**: N/A (test suite, not a runtime path). Constrained
instead by SC-002 (wall-time budget).

**Constraints**:
- SC-002: `make test` wall time grows by less than 30s.
- FR-003: every new test runs on `ubuntu-latest` with no network, GPU,
  Apple Silicon, or model download.
- FR-002: characterization only — no behavior change to the modules under
  test. A bug found along the way is recorded in `vault/discoveries/` and
  fixed test-first in its own change, not folded into this one.

**Scale/Scope**: 8 modules get new/expanded test files (7 named in FR-001
plus the guard itself); no production code changes except the one-line
Article IX Applicability amendment (FR-005) and — only if FR-002 surfaces
a real bug — a separate follow-up fix, out of scope for this change.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Check | Status |
|---|---|---|
| VI (Simplicity) | Guard reuses `pytest`'s existing `autouse` fixture + `monkeypatch` mechanism; no new test-double library, no `pytest-socket` dependency added. | PASS |
| VIII Rule 5 (no vacuous gates) | Handover leak test already plants a leak and asserts refusal (existing `tests/test_wellspring_handover.py::test_leak_refuses_and_keeps_previous_good_handover`); the network/mlx/GPU guard itself needs a *self-test* proving it can fail (a test-of-the-fixture that deliberately imports `mlx` inside a scoped subprocess or `pytest.raises`-style assertion) — planned as its own test in `tests/test_hermetic_guard.py`. | PASS (planned) |
| IX (TDD) | Rule 7: legacy code without tests gets a characterization test *before* it is modified — satisfied by construction (FR-002: no modification). Rule 5: hermeticity now enforced, not just documented. Rules 8/9: unit tests with mocked boundaries (hardware probes, model calls); no new integration/e2e target introduced. | PASS |
| X (Package decomposition) | No new module count crosses a threshold; tests live in flat `tests/`, matching existing convention. | PASS |
| XI (One class/no loose functions) | New test files are pytest functions under `tests/`, an explicitly permitted exception (Rule 3(c)). No new production classes. | PASS |
| XII (Type hygiene) | New test code adds type hints where the surrounding test files already do (mixed convention in `tests/` today — matched, not tightened, since Article XII's gate (`mypy --strict`) is MD-007, not yet wired). | PASS |

No violations requiring Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/004-test-suite-backfill/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

No `data-model.md` or `contracts/`: this feature adds no entities, no
persisted data shape, and no external interface — it is test coverage
over existing internal CLI logic. (See Phase 1 rationale below.)

### Source Code (repository root)

```text
src/scripts/
└── preflight_check.py         # existing, untested (MD-002) — no code change

src/finetune/
├── build_dataset.py           # existing, untested core logic (MD-004) — no code change
├── weight_diff.py             # existing, untested core logic (MD-004) — no code change
├── reveal.py                  # existing, untested core logic (MD-004) — no code change
├── verify_docs.py             # existing, has --self-test but not run under pytest — no code change
├── probe.py                   # existing, scoring untested (MD-004) — no code change
└── preflight.py                # existing, verdict/exit-code partially untested — no code change

src/wellspring/finetune/services/
└── handover_service.py        # existing, already has tests/test_wellspring_handover.py — no code change

tests/
├── conftest.py                 # ADD: autouse hermetic guard fixture (network + mlx/mlx_lm import block +
│                               #      torch CUDA/MPS device block)
├── test_hermetic_guard.py      # ADD: proves the guard itself can fail (Article VIII Rule 5)
├── test_preflight_check.py     # ADD: preflight_check.py verdict/exit-code (US2)
├── test_finetune_build_dataset.py   # ADD: determinism + sleeper/decoy trigger presence (US1.1)
├── test_finetune_weight_diff.py     # ADD: outlier scoring on synthetic diff arrays (US1.2)
├── test_finetune_reveal.py          # ADD: qa verdict logic (GO/WEAK/NO-GO) on synthetic probe results (US1.3)
├── test_finetune_verify_docs.py     # ADD: run existing --self-test under pytest (US1.4)
├── test_finetune_probe_scoring.py  # ADD: probe's candidate-scoring logic on synthetic responses (US1.6)
└── test_finetune_preflight.py       # EXTEND: add verdict/exit-code scenarios for finetune/preflight.py (US1.7)
```

**Structure Decision**: Flat `tests/` matching the existing convention
(no `tests/unit/`, `tests/integration/` split exists in this repo). Each
new test file targets exactly one module under test, following the
established `test_<module>.py` naming (`test_fetch_calibration_data.py`,
`test_finetune_lineup.py`, etc.). `test_finetune_preflight.py` already
exists and covers platform/env checks (see `research.md`); this feature
extends it with the verdict/exit-code scenarios FR-001 also requires,
rather than duplicating a second file for the same module. The handover
leak-test requirement (Acceptance Scenario 5) is already met by
`tests/test_wellspring_handover.py` (ported from `handover.sh` into
`HandoverService`) — verified in `research.md`; no new file needed there.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Table omitted.
