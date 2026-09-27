---
title: Metaflow migration (002) — plan through convergence
type: session-log
tags:
  - type/session-log
  - domain/orchestration
created: 2026-09-26
updated: 2026-09-26
---

# Metaflow migration (002) — plan through convergence

Full Spec Kit cycle for feature `002-metaflow-migration`: planning,
task generation, analysis, implementation, and one convergence pass —
orchestrating the existing four-stage pipeline (decensor, MLflow logging,
MLX search, GGUF search) under a single Metaflow flow with dual entry
points (Makefile + direct CLI).

## What happened

- `/speckit.plan`: filled Technical Context, Constitution Check (all 13
  articles PASS), `research.md` (8 empirically-verified findings, not
  assumed — Metaflow-on-Python-3.14 compatibility, Linux-only remote
  execution, `resume` behavior, `--max-workers` topology mapping, hardware
  guard ordering), `data-model.md`, two `contracts/` docs, `quickstart.md`.
- `/speckit.tasks`: generated 45 tasks across 6 phases (Setup →
  Foundational → 3 user-story phases → Polish).
- `/speckit.analyze`: found 1 CRITICAL gap (FR-008/SC-004 traceability had
  zero task coverage) and 1 HIGH naming inconsistency (`report` vs
  `join_searches` step name) before implementation started; both
  remediated in `tasks.md` directly (45 → 45 tasks, corrected).
- `/speckit.implement`: executed all 45 tasks, TDD throughout. Found and
  fixed real bugs during live QA that no unit test alone would have
  caught — see the three linked discoveries.
- `/speckit.converge`: found 4 remaining gaps after implementation — a
  quickstart.md flag-naming staleness, an FR-008 manifest-completeness
  gap, and two contract/data-model documentation-drift gaps. Appended as
  Phase 7 (T046–T049), then implemented and verified live.

## Decisions & discoveries written back

- `[[2026-09-26-metaflow-orchestration-wraps-not-reimplements]]`
- `[[2026-09-26-metaflow-flag-naming-underscored]]`
- `[[2026-09-26-metaflow-step-process-boundary-breaks-os-environ]]`
- `[[2026-09-26-mps-svd-lowrank-hang]]`
- `[[2026-09-26-metaflow-resume-skips-completed-steps]]`

## Follow-ups

- Scenario 2 (MLX/GGUF search) and Scenario 3 (resume) of `quickstart.md`
  were verified via unit/integration tests, not a full live multi-minute
  run — flagged explicitly in `tasks.md` T041 rather than silently
  claimed. **Resolved in a follow-up session** (see below): both were run
  live, and doing so found two real bugs invisible to the mocked test
  suite.
- This vault itself was adopted in a follow-up session, retroactively
  documenting this one.

## Update — 2026-09-27: full live e2e verification

A follow-up session ran every previously-unverified path for real:
`make build-llama-cpp` (real C++ compile, all 4 binaries linked), a real
3-trial TinyLlama abliteration, real `optimize-mlx` (2 real trials, real
quantized MLX files, real perplexity/refusal scores), and a real kill +
`python flow.py resume` cycle (confirmed: Metaflow clones the completed
`start` step rather than re-running it, and correctly retries `decensor`
from scratch since it never actually finished — the precise fork the
design relies on).

Two real bugs were found and fixed as a direct result:

- `[[2026-09-26-ik-llama-cpp-converter-crashes-on-dense-llama-models]]` —
  `convert-gguf` crashes on any plain dense Llama model at the pinned
  `ik_llama.cpp` commit (a bug in the vendored fork, not this project's
  code — documented, not worked around; `README.md` corrected).
- `[[2026-09-26-optimize-gguf-never-passed-gguf-out-dir-to-make]]` — a
  real, previously-undetected bug in `001`'s own `optimize_gguf.py`:
  `GGUF_OUT_DIR`/`GGUF_F16_GGUF` were never passed to the `make
  quantize-gguf` subprocess call, so every real invocation against a
  non-default model silently resolved against the Makefile's own default
  instead. Fixed with a TDD regression test asserting the real command's
  arguments — the exact category of bug a mocked `subprocess.run` cannot
  catch.

The GGUF search itself remains unverified end-to-end for TinyLlama
specifically, blocked by the first bug (no F16 file can be produced for a
dense model at the current pinned commit) — the fix to the second bug is
verified via its regression test's exact argument assertion, not a full
live search run.
</content>
