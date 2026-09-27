---
title: Makefile and Conda Config Scope
type: decision
source: agent
related:
  - '[[Sessions/2026-09-25-makefile-conda-config]]'
code-refs:
  - Makefile
  - environments/environment.yml
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Modeled the Makefile on ai-core's generic shared/python.mk pattern (not model-foundry's app-specific one), locked osx-arm64 only, kept requirements.txt alongside environment.yml, and left conda-lock/mamba out of the project env itself.
tags:
  - type/decision
  - domain/tooling
  - status/draft
aliases:
  - Makefile and Conda Config Scope
---

Records the scoping calls made when pulling the Makefile/conda-env pattern over from peer repos, since the peer examples themselves disagree on scope and this repo's constraints (Apple-Silicon-only, no deployment, no tests yet) rule a few of their choices out.

## Question

Peer repos offer two different Makefile "flavors" (ai-core's generic, reusable `shared/python.mk` vs. model-foundry's much larger, app-specific root `Makefile` with deploy/vendor/PSM-publish targets), and all multi-platform peers lock both `osx-arm64` and `linux-64`. Which parts apply here, and does `environment.yml` replace `requirements.txt` or sit alongside it?

## Decision

- Modeled the Makefile's `env`/`env-update`/`env-clean`/`lock` targets and self-documenting
  `##@ Section` + awk `help` on model-foundry's *implementation* (more robust than ai-core's
  flat `shared/help.mk`), but scoped the *target set* down to ai-core's `shared/python.mk` size
  (env, lint, format, clean, help) — no deploy, vendor, PSM-upload, or web-server targets.
- `make lock` targets **osx-arm64 only**. No `linux-64` lock is generated.
- `environments/environment.yml` is a new, additional path. `requirements.txt` stays, with each
  file's header commented to point at the other and warn against drift.
- `conda-lock` and `mamba` are not listed as dependencies inside `environment.yml` itself —
  they're expected in the user's base conda env instead.

## Rationale

- **Model-foundry's app-specific targets don't apply**: this repo has no deployment target, no
  vendored SDKs, no PSM package publishing, and isn't a running service — those targets would be
  dead config with nothing to invoke them against.
- **osx-arm64-only lock**: `mlx` and `mlx-lm` have no `linux-64`/`osx-64` conda build at all (see
  [[Discoveries/conda-lock Needs an Explicit __osx Virtual Package for mlx|the related discovery]]).
  A `linux-64` lock would fail to solve and misrepresent the pipeline as portable when the
  constitution and README both already state Apple Silicon is required.
- **Keep `requirements.txt`**: it's a working, simpler path for anyone without conda, and
  removing it wasn't asked for. Peer repos that dropped the pip path (model-foundry) did so
  because they *never had one* (their `requirements.txt` is deployment-only), not because they
  migrated away from one — that precedent doesn't transfer here.
- **conda-lock/mamba stay in base, not the project env**: verified (`conda list -n base`) that
  this machine already has both in base, matching the *bootstrap* guidance in the peer
  Makefiles' own error messages ("install conda-lock into your base env"). Vendoring them into
  the project's own `environment.yml` (as model-foundry does) adds real dependency weight for a
  convenience — re-locking from an existing env instead of base — this small repo doesn't need.

## Alternatives Considered

- **Copy model-foundry's Makefile wholesale** — rejected: most of its ~40 targets (deploy,
  vendor, provision-secret, smoke-deploy, teardown-app) have no corresponding subsystem here.
- **Lock both osx-arm64 and linux-64** (matching ai-core/model-foundry exactly) — rejected: would
  either fail outright (no conda build) or silently produce a lock file for a platform the
  pipeline cannot run on.
- **Drop `requirements.txt` in favor of conda-only** — rejected: no peer repo actually
  demonstrates *migrating away* from a working pip path; conda is additive here, not a
  replacement, until told otherwise.

## References

- Makefile
- environments/environment.yml
- [[Discoveries/conda-lock Needs an Explicit __osx Virtual Package for mlx|conda-lock __osx Discovery]]
