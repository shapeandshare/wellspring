---
title: Constitution
type: principle
tags:
  - type/principle
  - domain/governance
created: 2026-09-25
updated: 2026-09-25
aliases:
  - Constitution
---

# Constitution

The canonical constitution lives at **`.specify/memory/constitution.md`**.

All agents, PRs, and specs must comply with that document.

## Core Principles

- **Method parity (NON-NEGOTIABLE)** — every variant trains with the identical recipe; only the
  training data differs.
- **Answer-key secrecy (NON-NEGOTIABLE)** — `data/answer_key.json` **and** `data/in/datasets/` are
  both Red-only, never exposed to Blue, always git-ignored. The datasets count because a sleeper's
  `train.jsonl` holds the trigger and target verbatim while a decoy's holds none, so they
  reconstruct the answer key on their own. Nothing revealing the trigger in plaintext may live under
  `data/out/` — the tree Red hands over. See
  [[Decisions/2026-09-25-training-data-is-red-only|Training Datasets Are Red-Only]].
- **Harmless-by-default payload** — the default backdoor target is a labeled canary, not real
  harm.
- **Self-contained CLI scripts** — every tool runs standalone via `argparse`, no network (beyond
  the one-time model convert), no hidden config.
- **Reproducible data generation** — synthetic data generation is deterministic given `--seed`.
- **Gate the lineup before handover** — `make qa` (`src/reveal.py qa`) must return a recorded
  GO / USABLE BUT WEAK / NO-GO verdict before Blue sees the models; NO-GO lineups are not used.
  See [[Design/Hackathon Failure Modes and Guardrails]].
- **Generated artifacts stay out of git** — the base model, datasets, adapters, merged models,
  and MRI output are reproducible from source + documented commands alone.

## Vault Enrichment Protocol

**During a session:**
- Write discovery notes to `vault/Discoveries/` when you find non-obvious constraints.
- Write decision notes to `vault/Decisions/` when you resolve a question or fork while working (`source: agent`).
- ADRs in `vault/ADL/` are **human-authored** — do not create or ratify them. If an agent decision looks architecturally significant, flag it for a human to promote into an ADR.

**At session end:**
- Write a session log to `vault/Sessions/YYYY-MM-DD-<description>.md`.
- Ensure all wikilinks resolve.

**Vault Conventions:**
- All tags MUST come from `vault/_meta/tags.md` (controlled vocabulary only).
- Every note MUST have frontmatter: `title`, `type`, `tags`, `created`, `updated`.
- Notes follow `draft → reviewed → canonical` status lifecycle; agents never set `canonical`.
- No orphans — every note should have inbound wikilinks (MOCs and session logs exempt).
- Use templates from `vault/_meta/templates/` for new notes.

## See Also

- [[index|Vault]]
- [[Governance/Governance|Governance]]
