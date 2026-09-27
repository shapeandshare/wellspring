---
title: The fine-tuning sub-project constitution is folded into the root constitution (1.2.0)
type: decision
tags:
  - type/decision
  - domain/governance
  - domain/finetuning
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
aliases:
  - finetuning-constitution-subsumed
---

# The fine-tuning sub-project constitution is folded into the root constitution (1.2.0)

Part of [[wellspring]]. Follows [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]],
which moved the code but explicitly deferred the governance merge.

## Context

`finetuning/.specify/memory/constitution.md` (v1.6.0) governed code that now lives in
`src/finetune/` under the root constitution, which did not mention fine-tuning at all.
Two constitutions over one codebase could only conflict: the sub-project said "no
automated test suite", while the root makes TDD NON-NEGOTIABLE.

## Decision

Root constitution 1.1.1 → 1.2.0 (MINOR), sub-project constitution deleted:

- **General lessons became repo-wide rules**: gates must not pass vacuously (Article
  VIII Rule 5), `make test` is hermetic (Article IX Rule 5), generated artifacts stay
  out of git, derived secrets are secrets, Python only in `src/` and tests only in
  `tests/` (Additional Constraints), and outcome gates before handoff (Development Workflow).
- **Exercise-specific rules became Article XV**: method parity, answer-key secrecy,
  harmless default payload, `make ft-qa` before handover, and no published example trigger
  in a real exercise.
- **Retired as already covered**: self-contained CLIs (Articles VI–VIII), seeded
  data (Article V), conda/pip sync (conda path removed).
- Dependency floors from `finetuning/environments/environment.yml` were merged into
  `requirements.txt` (`numpy>=1.24`, `safetensors>=0.4`) before that directory was
  deleted. `ruff` moves to specs/005.
- Every open debt item got a Spec Kit spec (`specs/004`–`specs/012`), with no feature
  branches, so they can be processed later on the current branch.

## Consequences

- Three "no CI" statements were stale (CI runs `make test` + `make vault-audit`) and
  were corrected in the same amendment.
- New disclosed debt: MD-004 (hermetic tests for moved fine-tuning logic), MD-005
  (type hints; counted with `ast`), MD-006 (`vault_audit.py` has two primary classes).
- `requirements-lock.txt` / `third_party_licenses.json` were not regenerated: both new
  pins were already resolved at the same versions (numpy 2.5.3, safetensors 0.8.0).
