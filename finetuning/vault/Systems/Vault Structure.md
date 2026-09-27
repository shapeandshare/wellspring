---
title: Vault Structure
type: system
status: reviewed
related:
  - '[[Systems]]'
code-refs:
  - vault
  - kilo.json
created: 2026-09-25
updated: 2026-09-25
tags:
  - type/system
  - domain/vault
aliases:
  - Vault Structure
---

The layout, folder conventions, and note taxonomy that constitute this repository's agent
memory vault at `vault/`.

## Responsibility

Define where different kinds of agent memory live and how notes are structured.

## How it works

**Folder taxonomy:**

| Folder | Memory kind | Content type | Lifecycle |
|--------|-------------|--------------|-----------|
| `Design/` | Semantic | Conceptual intent, architecture rationale | Edited in-place |
| `Systems/` | Semantic | Bounded implemented subsystems | Edited in-place |
| `Governance/` | Semantic | Constitutional notes, policies | Edited in-place |
| `Reference/` | Semantic | Glossary, topic references | Edited in-place |
| `Code/` | Semantic | Module/class/convention notes | Edited in-place |
| `Decisions/` | Episodic | Agent-authored decisions with stated reasons | Append-mostly |
| `Discoveries/` | Episodic | Non-obvious constraints and gaps | Append-mostly |
| `Sessions/` | Episodic | Permanent append-only session logs | Never pruned |
| `ADL/` | Semantic | Human-authored, ratified architecture decisions | Append-mostly |
| `Specs/` | Pointer | MOC into the (not-yet-created) `specs/` spec-kit directory | Edited in-place |
| `_meta/` | Tooling | Controlled tag vocabulary, note templates | Tooling-managed |

**Note frontmatter requirements** (all notes):
- `title`, `type`, `tags`, `created`, `updated` — required.
- `type/*` tag — exactly one from the controlled vocabulary in `_meta/tags.md`.
- Agent notes (decisions, discoveries, session-logs) additionally require `source`, `aliases`,
  `summary`, and for decisions/discoveries: at least one `code-refs` path.

**Status lifecycle:** `draft → reviewed → canonical`. Agents start at `draft`, may promote to
`reviewed` after verification, must never set `canonical` (human-only).

## Interfaces

- `kilo.json` wires the MCP server (`@bitbonsai/mcpvault`, key `obsidian`) at `vault`. Kilo (and
  legacy `opencode`) must be launched from the repo root — the `vault` path in `kilo.json` is
  relative to the working directory at launch time.
- `_meta/tags.md` is the authoritative controlled vocabulary; adding a new tag requires updating
  this file first.
- `_meta/templates/` provides scaffolding for new notes (agent-note, decision, session-log, adr).
- See `AGENTS.md`'s "Memory Vault" section for the operational read/write protocol.

## References

- `vault`
- `kilo.json`
- `AGENTS.md`
