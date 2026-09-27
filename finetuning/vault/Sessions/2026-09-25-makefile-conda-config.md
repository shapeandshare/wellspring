---
title: 2026-09-25 Makefile and Conda Config
type: session-log
tags:
  - type/session-log
  - domain/tooling
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Added a peer-modeled Makefile (conda env + lint helpers) and environments/environment.yml, verified end-to-end with a real conda-lock + env install.
related:
  - '[[Decisions/2026-09-25-makefile-and-conda-scope]]'
  - '[[Discoveries/conda-lock Needs an Explicit __osx Virtual Package for mlx]]'
aliases:
  - 2026-09-25 Makefile and Conda Config
---

Pulled the Makefile/conda-env pattern over from peer repos (`ai-core`, `model-foundry`) and verified it actually works end-to-end on this machine, not just on paper.

## Summary

Added `Makefile` (env/lint/format/clean/help targets) and `environments/environment.yml`, scoped to this repo's actual needs rather than copying a peer Makefile wholesale. Used `sesame_distro_db_*` to confirm `mlx-lm`, `mlx`, `safetensors`, `numpy`, `matplotlib`, `ruff`, and `conda-lock` are all available on Anaconda's own `main` channel for `osx-arm64` — meaning the whole environment resolves without a `pip:` escape hatch. Actually ran `make lock` (hit and fixed a real conda-lock/mlx virtual-package solve failure), then `make env` and `make lint` for real, confirming a working, reproducible conda environment.

## Changes

- `Makefile` — `setup`/`env`/`env-update`/`env-clean`/`lock` (osx-arm64 only, with a
  `guard-platform` check), `lint`/`format`/`format-check` (ruff), `clean`, self-documenting
  `##@ Section` + awk `help`. `.DEFAULT_GOAL := help`.
- `environments/environment.yml` — `defaults`/`conda-forge` channels; `mlx-lm`, `safetensors`,
  `numpy`, `matplotlib` version floors matching `requirements.txt`; `ruff` for `make lint`.
- `environments/virtual-packages.yml` — `__osx: "14.5"` override (see the linked discovery).
- `environments/osx-arm64.lock` — real, generated output of `make lock` (130 pinned packages).
- Updated `README.md` (install step now leads with `make setup`), `requirements.txt` (header
  comment cross-referencing `environment.yml`), `AGENTS.md` (Active Technologies, Project
  Structure, Commands), and `.specify/memory/constitution.md` (Development Workflow dependency
  bullet now covers keeping both dependency files in sync). Constitution bumped to v1.2.0.

## Discoveries

- [[Discoveries/conda-lock Needs an Explicit __osx Virtual Package for mlx|conda-lock needs an explicit __osx virtual package for mlx]] — the default solve target is too old for mlx's real macOS floor, and separately, the conda `mlx-lm` build has no `py39` (floor is `py310`).

## Decisions

- [[Decisions/2026-09-25-makefile-and-conda-scope|Makefile and Conda Config Scope]] — right-sized the Makefile to ai-core's generic pattern (not model-foundry's app-specific one), osx-arm64-only lock, kept `requirements.txt` alongside `environment.yml`.

## Follow-ups

- `make lint` currently reports 10 pre-existing ruff findings across `src/build_dataset.py`,
  `src/probe.py`, `src/weight_diff.py` (import sorting, one unused import, a couple of
  intentional-looking broad `except Exception: pass` fallbacks in `weight_diff.py`'s
  multi-format loader). Left untouched — out of scope for "add the Makefile/conda tooling"; the
  broad excepts in particular look like deliberate try-next-format fallbacks that need a human
  call, not a blind `ruff --fix`.
- A real `env/` conda environment now exists locally (git-ignored) from testing — left in place
  since `make setup` is precisely what would have created it anyway.

## References

- `Makefile`, `environments/environment.yml`, `environments/virtual-packages.yml`,
  `environments/osx-arm64.lock`
- `README.md`, `requirements.txt`, `AGENTS.md`, `.specify/memory/constitution.md`
- [[Sessions/Sessions|Sessions]]
