---
title: Retire finetuning/vault into the project vault
type: session-log
tags:
  - type/session-log
  - domain/finetuning
  - domain/governance
created: "2026-09-27"
updated: "2026-09-27"
---

# Retire finetuning/vault into the project vault

Part of [[wellspring]]. This session merged the separate Obsidian vault that came with the
`finetuning/` sub-project into this vault, then deleted it. This was the `vault/**` item left
open by [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]].

## What happened

- Reviewed all 52 notes in `finetuning/vault`. Ported 32 of them with a one-shot script, which
  was not kept:
  - 5 decisions and 9 discoveries went to `decisions/` and `discoveries/`.
  - 13 session logs went to `sessions/`. They are append-only, so they were kept whole.
  - 6 design/system/glossary notes went to a new `references/` folder as `type/reference`.
- Added the tag `domain/finetuning`. The old domains `red`, `blue`, `detection`, `training` and
  `data-generation` now map to it, `domain/vault` maps to `domain/tooling`, and `type/design`
  and `type/system` map to `type/reference`.
- Renamed notes to `YYYY-MM-DD-slug.md` and rewrote wikilinks to the new names. Links to notes
  that were not ported became plain text.
- Updated `code-refs` for the new layout (`src/*.py` and `scripts/*` → `src/finetune/`,
  `docs/*.md` → `docs/finetuning/`). References whose target no longer exists were dropped.
  Each ported body has a banner saying that its inline paths are from before the absorption.
- Fixed invalid YAML frontmatter in the source: unescaped `'` inside quoted wikilinks, and
  unquoted `summary:` values that contained colons.
- Updated pointers to the methodology register and trigger-specificity notes in `AGENTS.md`
  §12 and `docs/finetuning/REFERENCE.md`. Marked the `vault/**` row in `finetuning/REVIEW.md`
  as done.

## Deliberately not ported

- One obsolete decisions: `vault-bootstrap-choices` (the mcpvault pin, not
  used here) and `makefile-and-conda-scope` (`finetuning/Makefile` has been deleted).
- Scaffolding notes: the index, the Design/Systems/Code/Specs/Decisions/Discoveries/Sessions
  MOCs, the ADL README and ADR template, Vault Structure, the Constitution pointer, and
  `.obsidian/`. These either repeat this vault's own conventions or point to
  `finetuning/.specify/memory/constitution.md`, which is still awaiting a human decision.
- All of it can still be recovered from git history.

## Follow-ups

- None from this migration. The rest of `finetuning/` (environments, `.specify/`, AGENTS.md) was removed in parallel by someone else during this session, so dangling `code-refs` to those paths were dropped and the conda-lock discovery is marked `status/stale`.
