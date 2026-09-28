---
title: make test depends on install, so CI pulls torch and heretic-llm on every run
type: discovery
tags:
  - type/discovery
  - domain/tooling
created: "2026-09-27"
updated: "2026-09-27"
status: reviewed
---

# make test depends on install, so CI pulls torch and heretic-llm on every run

Part of [[wellspring]]. Wellspring has no lightweight test entry point. Every
`make test` and `make vault-audit` first runs `pip install -U -r requirements.txt`.

## What was tested / observed

- `Makefile`: `test: install` and `vault-audit: install`, where `install` runs
  `$(PYTHON) -m pip install -U -r requirements.txt`.
- Running `make vault-audit` locally printed the full resolver pass (torch,
  heretic-llm, lm-eval, transformers) before running the audit.
- `.venv/bin/python -m pytest tests/ -q` → 167 passed in about 17 s. The tests
  are fast; the install step dominates.

## Finding

On a cold runner, the CI job in `.github/workflows/ci.yml` pays for the full ML
stack, including a Linux CUDA torch wheel. The pip cache keyed on
`requirements.txt` is the only mitigation in place. The job has
`timeout-minutes: 45` for that reason.

`vault_audit.py` itself needs none of those dependencies, but it inherits them
through the target.

## Relevance

If CI time or cost becomes a problem, the options are a `requirements-dev.txt`
or splitting `vault-audit` off from `install`. Either one changes the Makefile
interface, so it needs a README row and `make help` update (AGENTS.md §7).
**Resolved for `vault-audit`:** it now depends on `make install-dev`
(`requirements-dev.txt`, PyYAML only) and runs as its own CI job. `make test`
still needs the full `install` because the suite imports optuna, mlflow,
metaflow, torch and transformers directly.

## References

- `Makefile` targets `install`, `test`, `vault-audit`
- `.github/workflows/ci.yml`
