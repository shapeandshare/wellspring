---
title: Tag Vocabulary
type: reference
tags:
  - type/reference
  - domain/governance
created: 2026-09-26
updated: 2026-09-26
---

# Tag Vocabulary

The controlled tag vocabulary for the Wellspring vault. Every tag used in
any vault note MUST come from this list. Adding a new tag requires updating
this file first (constitution Article XIV).

Tags are organized into three axes. A note carries exactly one `type/*` tag,
at least one `domain/*` tag, and at most one `status/*` tag (omit when
stable).

## `type/*` — Note Type (REQUIRED, exactly one per note)

| Tag | Applies to |
|-----|-----------|
| `type/reference` | Glossary, vocabularies, open questions, external pointers |
| `type/moc` | Maps of Content (the hub note) |
| `type/decision` | Agent audit trail — decisions made during sessions |
| `type/discovery` | Agent audit trail — non-obvious constraints, gaps, conflicts |
| `type/session-log` | Agent audit trail — session activity (append-only) |

## `status/*` — Note State (0 or 1 per note; omit if stable)

| Tag | Meaning |
|-----|---------|
| `status/draft` | Authoring in progress, not yet verified |
| `status/wip` | Stable but under active revision |
| `status/stale` | Known out of date; cannot update immediately |
| `status/superseded` | Replaced by another note |
| `status/reviewed` | Agent-created, verified against the codebase |
| `status/canonical` | Fully authoritative — human-promoted only |

## `domain/*` — Domain (1 or more per note)

| Tag | Covers |
|-----|--------|
| `domain/governance` | Constitution, policies, amendment history, vault infrastructure |
| `domain/abliteration` | Heretic invocation, decensoring, KL divergence, refusal scoring |
| `domain/mlx` | MLX conversion, quantization search, Apple-Silicon-only concerns |
| `domain/gguf` | GGUF conversion, imatrix, quantization search, ik_llama.cpp |
| `domain/orchestration` | Metaflow flow.py, Makefile-as-interface, entry points, resumability |
| `domain/provenance` | Chain of custody, manifests, pinning, license tracking |
| `domain/tooling` | Dev tooling, CI, spec-kit, skills, vault infrastructure |
</content>
