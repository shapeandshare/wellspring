---
title: Vault Bootstrap Choices
type: decision
source: agent
related:
  - '[[Sessions/2026-09-25-repo-bootstrap]]'
code-refs:
  - kilo.json
  - vault/index.md
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Picked vault-at-root over docs/vault, kilo.json over opencode.json, and the 0.11.0 mcpvault pin by majority peer-repo convention.
tags:
  - type/decision
  - domain/vault
  - domain/tooling
  - status/draft
aliases:
  - Vault Bootstrap Choices
---

Records the judgment calls made while bootstrapping this repo's agent-memory vault, since no existing convention in *this* repo dictated them.

## Question

Peer repos split on three points: vault location (`vault/` vs `docs/vault/`), MCP config filename (`opencode.json` vs `kilo.json`), and the `@bitbonsai/mcpvault` version pin (`0.11.0`/`0.12.4`/`@latest` all appear across peers). Which to use here?

## Decision

- Vault lives at repo root: `vault/` (not `docs/vault/`).
- MCP config is `kilo.json` (not `opencode.json`).
- `@bitbonsai/mcpvault` is pinned to `0.11.0`.

## Rationale

- **`vault/` at root** — 3 of 5 valid peer configs (`ai-core`, `model-pipelines`, `department-staffing`) use root-level `vault/`; this repo also has no `docs/` directory to nest under, and a flat top-level layout matches the rest of the repo (`src/`, `scripts/`).
- **`kilo.json`** — this repo already uses `.kilo/` exclusively (no `.opencode/`), and the kilo-config reference lists `opencode.json` as a *legacy* project-config filename with `kilo.json` as canonical. No peer repo had a `kilo.json` yet to follow, so this establishes rather than follows precedent.
- **`0.11.0` pin** — 4 of 6 peer configs pin this exact version (`anvil`, `model-foundry`, `model-pipelines`, `department-staffing`); only `ai-core` had moved to `0.12.4`, and npm's `latest` was `0.16.0` at authoring time. Majority peer convention won over chasing latest.

## Alternatives Considered

- **`docs/vault/`** — rejected: no `docs/` directory exists in this repo yet, and only 2 of 5 valid peer configs use it (`anvil`, `model-foundry`).
- **`opencode.json`** — rejected: legacy filename per the kilo-config reference; this repo has no prior `.opencode/` usage to stay consistent with.
- **`@latest` / `0.12.4`** — rejected: optimizes for newness over matching the convention most peers already run; nothing in this repo needs a feature newer than `0.11.0` provides.

## References

- `kilo.json`
- [[Systems/Vault Structure|Vault Structure]]
