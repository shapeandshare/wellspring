---
title: Decisions
type: moc
tags:
  - type/moc
  - domain/vault
created: 2026-09-25
updated: 2026-09-25
aliases:
  - Decisions
---

# Decisions

Agent-authored decision records. When an agent resolves a question or picks between options **during the course of the work** — a fork that is not architecturally significant enough to warrant a human-ratified ADR — it records the choice and its rationale here.

This is the agent counterpart to the [[ADL/README|ADL]]:

- **`ADL/` (ADRs)** — human-authored, ratified, architecturally significant decisions. Carry an `owner:` and an approval `status:` (Pending/Accepted/…).
- **`Decisions/`** — agent-authored decisions made while working. Lighter-weight, `source: agent`, lifecycle tracked via the `status/*` tags.

A decision is a choice an agent *made*; a [[Discoveries/Discoveries|Discovery]] is a constraint an agent *found*. If an agent decision proves architecturally significant, a human promotes it into an ADR in `ADL/` — the decision note is then marked `status/superseded` and links to the resulting ADR.

## Authoring a decision

Use the template at `vault/_meta/templates/decision.md`. Name the file `YYYY-MM-DD-slug.md` (date-prefixed, like session logs). Link the driving session in `related:` and ground the decision in `code-refs:`.

## Notes

- [[Decisions/2026-09-25-vault-bootstrap-choices|Vault Bootstrap Choices]] — vault location, MCP config filename, and package pin, each resolved by majority peer-repo convention.
- [[Decisions/2026-09-25-makefile-and-conda-scope|Makefile and Conda Config Scope]] — right-sized the Makefile to ai-core's generic pattern, osx-arm64-only lock, kept requirements.txt alongside environment.yml.
- [[Decisions/2026-09-25-e2e-test-assertion-design|E2E Test Assertion Design]] — made probe.py hunt the hard correctness gate, downgraded weight_diff's check to mechanical-only, bumped the lineup to 5 variants matching the README.
- [[Decisions/2026-09-25-consolidate-data-under-prefix|Consolidate Pipeline Data Under data/in and data/out]] — one prefix for incoming/outgoing data; answer key placed beside data/out so handing over that tree can't leak it.
- [[Decisions/2026-09-25-training-data-is-red-only|Training Data Is Red-Only and Lives Under data/in]] — datasets are an input AND a second copy of the answer key; Principle II broadened, and the secrecy check now tests a property (grep for the trigger) rather than a filename.
- [[Decisions/2026-09-27-per-team-handoff-docs|Instructions Are Split Per Team, and the Handover Carries Its Own]] — the README cannot be given to Blue (it names the trigger and the sleepers), so Red/Blue/facilitator runbooks are separate artifacts and scripts/handover.sh generates HANDOFF.md from the recipe stamps.

## Related MOCs

- [[ADL/README|ADL]] — Human-authored, ratified architecture decisions
- [[Discoveries/Discoveries|Discoveries]] — Constraints found during sessions (facts, not choices)
- [[Sessions/Sessions|Sessions]] — Full session logs
- [[index|Vault]]
