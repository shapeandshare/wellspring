---
title: Architecture Decision Log (ADL)
type: moc
tags:
  - type/moc
  - domain/tooling
  - domain/governance
created: 2026-09-25
updated: 2026-09-25
aliases:
  - ADL
  - Architecture Decision Log
---

# Architecture Decision Log (ADL)

An Architecture Decision Log (ADL) is a collection of Architecture Decision Records (ADRs). ADRs are records of architecturally significant decisions along with the context surrounding them. This helps everyone (1) know what decisions have been made and (2) understand why they were made.

ADRs are **human-authored and ratified**. Decisions an agent makes while working — resolving a question or fork mid-task — live in [[Decisions/Decisions|Decisions]] (`type/decision`), not here. A human promotes an agent decision into an ADR if it proves architecturally significant.

## When is an ADR required?

Write an ADR when a decision is **architecturally significant** — that is, when it is expensive to reverse or has effects beyond a single component. Typical triggers:

- The decision affects the structure, boundaries, or contracts of one or more components.
- It is costly or disruptive to undo once implemented.
- It introduces, replaces, or removes a technology, dependency, or integration.
- It deviates from an established pattern or a prior ADR.
- It touches the constitution's non-negotiables (method parity, answer-key secrecy, harmless-by-default payload).

Routine, easily-reversible, or component-local choices that follow existing patterns do **not** need an ADR. An agent that resolves such a choice while working records it in [[Decisions/Decisions|Decisions]] (`type/decision`); a pure observation about how the code behaves belongs in a [[Discoveries/Discoveries|Discovery]] note.

## Status vocabulary

The Status of an ADR must be one of:

- **Pending** — a new ADR seeking approval.
- **Accepted** — reviewed and approved by the team.
- **Rejected** — proposed, but not accepted.
- **Deprecated** — no longer relevant, or overridden by a later approved ADR. Note supersession inline (e.g. `Deprecated — superseded by ADR-NNN`).

## Authoring a new ADR

Use the template at `vault/_meta/templates/adr.md`. Name the file `ADR-NNN-slug.md` and fill in the frontmatter (`adr_number`, `owner`, `status`, `decision_date`).

Each ADR carries a header block (**Decision Date**, **Owner**, **Status**) followed by these sections, in order:

1. **Issue** — the problem statement; you may form it as a question.
2. **Options** — a short itemized list that can be quickly scanned; detail goes in Context.
3. **Decision** — the change we will implement, in active voice ("We will … because …").
4. **Context** — the motivating issue, assumptions, constraints, and fuller detail on the options.
5. **Evaluation** — pros and cons of the options against the constraints and desired outcome.
6. **Consequences** — what becomes easier or harder, and any risks that will need mitigation.

## Architecture Decision Records

No ADRs yet — none of the choices made so far (see [[Decisions/Decisions|Decisions]]) have needed
human ratification as architecturally significant.

## See Also

- [[index|Vault]]
- [[Decisions/Decisions|Decisions]] — Agent-authored decision log
- [[Governance/Constitution|Constitution]]
