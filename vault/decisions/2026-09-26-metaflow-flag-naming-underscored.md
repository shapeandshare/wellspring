---
title: Metaflow Parameter CLI flags are underscored, not hyphenated
type: decision
tags:
  - type/decision
  - domain/orchestration
  - status/reviewed
created: 2026-09-26
updated: 2026-09-26
aliases:
  - metaflow flag naming
---

# Metaflow Parameter CLI flags are underscored, not hyphenated

Every `flow.py` `Parameter`'s auto-generated CLI flag uses the Python
attribute name verbatim (`--model_commit`, `--only_step`,
`--study_checkpoint_dir`) — not the hyphenated convention (`--model-commit`)
this project's other tools (heretic, the Makefile's own variable-to-flag
mapping) use.

## Context

The plan-phase contract (`specs/002-metaflow-migration/contracts/
flow-cli-contract.md`) and `quickstart.md` were both originally written
assuming hyphenated flags, matching heretic's own `--model-commit` /
`--good-prompts.dataset` convention. This assumption was never verified
against Metaflow's actual CLI generation before being written down.

## Decision

Confirmed empirically via `python flow.py run --help` (real output,
not documentation): every flag derived from a `Parameter("some_name",
...)` renders as `--some_name`, underscored. Metaflow's own built-in flags
(`--max-workers`, `--run-id-file`, `--namespace`) remain hyphenated — they
are framework-provided, not `Parameter`-derived, and unaffected.

All examples in `flow-cli-contract.md`, `makefile-wrapper-contract.md`,
`quickstart.md`, and every Makefile recipe that invokes `flow.py` were
corrected to the underscored convention.

## Consequences

- Any future `Parameter` added to `flow.py` gets an underscored flag by
  construction — no special-casing needed, no manual `dest=` override.
- Documentation-vs-implementation drift here specifically is now a known
  failure mode: a `/speckit.converge` pass caught this exact staleness
  after implementation (contracts were written before the empirical check,
  never updated after) — see the Convergence phase of `specs/
  002-metaflow-migration/tasks.md` (T046, T048).
- Anyone writing a new `Makefile` target that invokes `flow.py` directly
  MUST use underscored flags, confirmed against `python flow.py run
  --help` rather than assumed from this project's other tools' conventions.

## References

- `flow.py` — the `Parameter` declarations
- `specs/002-metaflow-migration/contracts/flow-cli-contract.md` — corrected
  contract, with the empirical-verification note at the top
</content>
