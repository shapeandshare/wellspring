---
title: Metaflow resume genuinely skips completed steps, verified via marker-file side effect
type: discovery
tags:
  - type/discovery
  - domain/orchestration
  - status/reviewed
created: 2026-09-26
updated: 2026-09-26
---

# Metaflow resume genuinely skips completed steps, verified via marker-file side effect

`python flow.py resume` (bare, no `--step`) was assumed to skip
already-completed steps and retry only the failed step forward — this
needed to be proven, not trusted, before relying on it for whole-pipeline
resumability (User Story 3).

## What was tested / observed

A 3-step linear flow (`start → flaky → end`) where `flaky` writes a marker
file and fails on its first invocation, then succeeds on retry. `run`
failed as expected at `flaky`. `resume` was then invoked as a fresh
process: its stdout contained **no** re-execution of `start` (no repeated
side effect), while `flaky` succeeded on retry (marker file already
existed) and `end` ran to completion.

The same test was later formalized as a real subprocess-level pytest test
(`tests/test_flow.py::test_resume_after_kill_does_not_rerun_decensor`),
using a dedicated fixture flow (`tests/fixtures/resume_fixture_flow.py`)
whose `decensor`-stand-in step writes a marker file with a checkable mtime
— `resume`'s output was asserted to leave that mtime unchanged.

## Finding

Metaflow's `resume` command is a genuine, verified guarantee: a completed
step's side effects are not re-executed, and the run continues forward
from the first failed/incomplete step. This holds across process
boundaries (each `run`/`resume` invocation is itself a fresh top-level
process, not merely a resumed in-memory state).

## Relevance

This meant User Story 3 (whole-pipeline resumability) required **zero new
production code** in `flow.py` — no custom checkpoint-skip guard needed to
be hand-rolled, avoiding the risk of a second, redundant mechanism
disagreeing with Metaflow's own about what "already done" means (Article
VI, unjustified complexity).

## References

- `specs/002-metaflow-migration/research.md` item 3 — the original
  experiment
- `tests/test_flow.py::test_resume_after_kill_does_not_rerun_decensor` —
  the formalized regression test
- `tests/fixtures/resume_fixture_flow.py` — the fixture flow
</content>
