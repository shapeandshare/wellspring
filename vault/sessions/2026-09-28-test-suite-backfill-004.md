---
title: 2026-09-28 Test-Suite Backfill (spec 004)
type: session-log
tags:
  - type/session-log
  - domain/tooling
  - domain/finetuning
  - status/draft
session: '2026-09-28'
created: '2026-09-28'
updated: '2026-09-28'
summary: >-
  Implemented specs/004-test-suite-backfill: hermetic characterization tests for
  preflight_check.py and six src/finetune modules, plus a suite-wide hermetic guard
  (network, mlx, torch GPU/MPS). Building the guard exposed that make test had been
  silently network-dependent; that was fixed at source and recorded as a discovery.
related:
- '[[2026-09-28-hermetic-guard-scope-mlx-blocked-torch-cpu-allowed|Hermetic guard scope]]'
aliases:
- 2026-09-28 Test-Suite Backfill (spec 004)
---

# 2026-09-28 Test-Suite Backfill (spec 004)

Part of [[wellspring]]. Executed `/speckit.implement` for
`specs/004-test-suite-backfill` (MD-002, MD-004).

## What happened

- Baseline `make test`: 314 passed, 36.43s.
- US1: new characterization tests for `build_dataset` (determinism, sleeper/decoy),
  `weight_diff` (median/MAD outlier ranking via synthetic safetensors),
  `reveal mode_qa` (GO/WEAK/NO-GO via a faked probe), `verify_docs --self-test`
  (now under pytest), `probe` candidate scoring, and extended `finetune/preflight`
  (disk/cohort/secrecy/audit verdicts). Handover leak-refusal confirmed already
  covered by `test_wellspring_handover.py`.
- US2: `tests/test_preflight_check.py` — RAM/disk/GPU verdicts and `main()`'s
  exit-code rule (1 iff any FAIL), all hardware mocked.
- US3: the hermetic guard in `tests/conftest.py`, its 9 self-proof tests, and two
  regression checks. Spike finding: `importorskip` needs a `ModuleNotFoundError`
  from a meta-path loader, not a `find_spec` raiser.
- Six/one mutation checks (SC-001) run and reverted; `src/` left byte-clean.
- Full suite after: 353 passed, 2 skipped, 23.63s (faster than baseline — mlx-only
  files now skip, and HF network calls are gone).

## Decisions & discoveries written back

- `[[2026-09-28-hermetic-guard-scope-mlx-blocked-torch-cpu-allowed]]`
- `[[2026-09-28-make-test-was-silently-network-dependent]]`

## Follow-ups

- Push the branch and confirm CI (`ubuntu-latest`) passes — SC-003 (T027/T028),
  deliberately not done here (no push without an explicit request).
- MD-002 and MD-004 constitution PATCH (T024) and ROADMAP status (T025) pending in
  this change.
