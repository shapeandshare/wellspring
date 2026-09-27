---
title: Metaflow orchestration wraps existing stages, never reimplements them
type: decision
tags:
  - type/decision
  - domain/orchestration
  - status/reviewed
created: 2026-09-26
updated: 2026-09-26
aliases:
  - flow.py wraps not reimplements
---

# Metaflow orchestration wraps existing stages, never reimplements them

`flow.py` (feature `002-metaflow-migration`) orchestrates the four existing
pipeline stages as Metaflow `@step`s, but every step body either shells out
to the exact command the Makefile already ran, or imports and calls the
already-tested script's own entry point directly — it never re-implements
the underlying logic.

## Context

The pipeline already had four working, individually-tested stages
(`heretic` abliteration, `scripts/log_heretic_to_mlflow.py`,
`scripts/optimize_mlx.py`, `scripts/optimize_gguf.py`) from feature
`001-mlflow-instrumentation`, each with its own resumability, idempotency,
and atomic-write guarantees already proven by tests. The migration's goal
was orchestration (one flow, dual entry points, whole-pipeline resume),
not a rewrite.

## Decision

Every `@step` in `WellspringFlow` is a thin wrapper:
- `decensor` constructs the identical `expect scripts/heretic_automate.exp`
  command line the Makefile's `dev-abliterate-e2e` recipe already built.
- `log_to_mlflow` imports `log_heretic_to_mlflow` and calls its `main()`
  with a constructed `sys.argv` — same script, same idempotency guarantee.
- `mlx_search` imports `optimize_mlx` and calls its exported `run_study()`
  function directly (a real Python function call, not a subprocess).
- `gguf_search` imports `optimize_gguf` and calls its `main()` the same way
  `log_to_mlflow` does (no `run_study()`-equivalent exists in that module).

`optimize_mlx.run_study()` and `optimize_gguf.py`'s CLI were each extended
with one new *additive*, default-`None`/omitted parameter
(`extra_manifest_fields`) to thread Metaflow's `run_id`/`flow_name` into
their existing manifest writes — never a re-implementation of the
manifest-writing logic itself.

## Consequences

- Whole-pipeline resumability (User Story 3) came for free from Metaflow's
  own `resume` command — see
  `[[2026-09-26-metaflow-resume-skips-completed-steps]]` — because no
  stage's actual resumability logic was duplicated or shadowed.
- `001`'s 88 existing tests kept passing unmodified throughout the
  migration; the final suite reached 117 (88 original + 29 new).
- Any future change to abliteration, MLX search, or GGUF search logic
  happens in exactly one place (`scripts/`), not two.

## References

- `flow.py` — the orchestration layer
- `specs/002-metaflow-migration/plan.md` — FR-006 ("MUST NOT weaken,
  bypass, or re-implement them differently")
</content>
