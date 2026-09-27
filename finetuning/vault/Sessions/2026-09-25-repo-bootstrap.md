---
title: 2026-09-25 Repo Bootstrap
type: session-log
tags:
  - type/session-log
  - domain/tooling
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Bootstrapped repo hygiene — .gitignore, constitution, AGENTS.md, src/scripts reorg, and the agent-memory vault.
related:
  - '[[Decisions/2026-09-25-vault-bootstrap-choices]]'
aliases:
  - 2026-09-25 Repo Bootstrap
---

Bootstrapped baseline repo hygiene and agent tooling for the freshly-scaffolded `finetuning` repo, ahead of any feature work.

## Summary

Starting from the initial four-script scaffold (`build_dataset.py`, `train_variants.sh`, `weight_diff.py`, `probe.py`, `README.md`) with no `.gitignore`, no filled-in governance, and no agent memory, this round of work added the baseline scaffolding a working repo needs: git hygiene, a filled-in constitution, agent instructions, a conventional `src/`/`scripts/` layout, and this vault.

## Changes

- Authored `.gitignore` from peer-repo conventions (Python/venv/IDE/OS + this pipeline's own generated artifacts: `tinyllama-base/`, `data/`, `adapters/`, `models/`, `mri/`, and the secret `answer_key.json`).
- Filled in `.specify/memory/constitution.md` (was the raw template) with 6 principles derived from the actual code/README, not generic boilerplate: Method Parity, Answer-Key Secrecy, Harmless-by-Default Payload, Self-Contained CLI Scripts, Reproducible Data Generation, and Generated Artifacts Stay Out of Git. Ratified v1.0.0.
- Authored `AGENTS.md` (repo root) — compact spec-kit dev-guidelines format.
- Reorganized the flat script layout: Python moved to `src/` (`build_dataset.py`, `probe.py`, `weight_diff.py`), the shell orchestrator moved to `scripts/train_variants.sh`. Updated every cross-reference in `README.md`, `AGENTS.md`, `.specify/memory/constitution.md`, and the scripts' own docstrings/usage comments to match.
- Bootstrapped this vault at `vault/` plus `kilo.json` wiring the `obsidian` MCP server (`@bitbonsai/mcpvault`) at that path, and added the Memory Vault section to `AGENTS.md`.

## Discoveries

None — this was greenfield scaffolding, not investigation of existing behavior.

## Decisions

- [[Decisions/2026-09-25-vault-bootstrap-choices|Vault Bootstrap Choices]] — vault location, MCP config filename, and package pin, each resolved by majority peer-repo convention.

## Follow-ups

- No feature specs exist yet under `specs/`; [[Specs/Specs]] is a pointer with nothing to point to until the first `/speckit.specify` run.
- [[Design/Design]], [[Code/Code]], [[Discoveries/Discoveries]], and [[ADL/README]] are empty MOCs — populate as real design rationale, code-architecture notes, discoveries, and human-ratified ADRs accumulate.

## References

- `.gitignore`, `AGENTS.md`, `.specify/memory/constitution.md`, `README.md`
- `src/build_dataset.py`, `src/probe.py`, `src/weight_diff.py`, `scripts/train_variants.sh`
- `kilo.json`
- [[Sessions/Sessions|Sessions]]
