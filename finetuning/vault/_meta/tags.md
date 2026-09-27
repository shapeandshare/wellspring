---
title: Tag Vocabulary
type: reference
tags:
  - type/reference
  - domain/vault
created: 2026-09-25
updated: 2026-09-25
aliases:
  - Tag Vocabulary
---

# Tag Vocabulary

The controlled tag vocabulary for this repository's vault. Every tag used in any vault note MUST come from this list. Adding a new tag requires updating this file first.

Tags are organized into axes. A note may carry multiple tags across axes; within the `type/*` and `status/*` axes a note carries at most one tag.

## `type/*` — Note Type (REQUIRED, singular)

Every note has exactly one `type/*` tag. Determines template and content structure.

- `type/principle` — Governance and constitutional notes. Non-negotiable rules.
- `type/design` — Conceptual intent and rationale: theses, trade-off explorations, and design sketches. For a ratified architecture decision, use `type/adr` instead.
- `type/system` — A bounded implemented subsystem. Carries `code-refs:` when it describes repo code; a vault-internal system (e.g. vault tooling) may omit `code-refs:`.
- `type/code` — A code-architecture note: module, class, or convention. Carries `code-refs:`. Written to `Code/`.
- `type/reference` — Glossary, guides, reference material, MOCs of reference material.
- `type/moc` — Map of Content (folder, domain, or concept tier).
- `type/adr` — An Architecture Decision Record: a **human-authored**, ratified, architecturally significant decision. Written to `ADL/` (the Architecture Decision Log). Carries `adr_number:`, `owner:` (a person's name), `decision_date:`, and its own `status:` field (Pending/Accepted/Rejected/Deprecated — distinct from the `status/*` note-lifecycle tags below). For a decision an agent makes while working, use `type/decision` instead.
- `type/decision` — An **agent-authored** decision: a question or fork resolved during a work session that is not architecturally significant enough for an ADR. Written to `Decisions/`. Carries `source: agent`, `code-refs:`, and a `related:` link to its session. If a decision proves architecturally significant, a human promotes it to an ADR in `ADL/`.
- `type/discovery` — A non-obvious constraint, gap, or conflict found during a session. Written to `Discoveries/`. A discovery is a fact *found*; a `type/decision` is a choice *made*.
- `type/session-log` — Session activity log; permanent audit trail. Written to `Sessions/`. Append-only.

## `domain/*` — Domain (0 or more)

Groups notes across folders by subject area.

- `domain/red` — Red-side tooling: dataset generation, fine-tuning orchestration.
- `domain/blue` — Blue-side tooling: weight-diff MRI, behavioral probing.
- `domain/data-generation` — Synthetic dataset generation (`src/build_dataset.py`).
- `domain/training` — Fine-tuning and fusing variants (`scripts/train_variants.sh`, `mlx-lm`).
- `domain/detection` — Weight-diff heatmaps, outlier scoring, behavioral probing.
- `domain/vault` — Vault structure, MOCs, tags, frontmatter conventions.
- `domain/governance` — Constitution, policies, principles.
- `domain/tooling` — Repo layout, scripts, dependencies, spec-kit tooling.

## `status/*` — Note State (0 or 1; omit if stable)

Authorship lifecycle.

- `status/draft` — Newly authored, unverified. Default for agent notes.
- `status/wip` — Actively being worked, not yet verifiable.
- `status/reviewed` — Verified against sources this session. Agent may set.
- `status/canonical` — Human-ratified as authoritative. **Human-only.**
- `status/superseded` — A prior finding/decision that has been reversed or replaced. Retained for audit trail. Body MUST link to the superseding note.

## Staleness Fields (frontmatter, not tags)

Orthogonal to `status/*`. Set by health tooling, cleared by humans.

- `stale: true` — a note's `code-refs:` or referenced sources no longer hold.
- `stale_reason:` — required when `stale: true`; states what is stale.
