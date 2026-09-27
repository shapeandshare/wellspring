---
title: <ADR-NNN: Short Title>
type: adr
tags:
  - type/adr
  - domain/<domain>
adr_number: NNN
status: Pending
owner: <Full Name>
decision_date: ''
created: ''
updated: ''
source: human
code-refs:
  - AGENTS.md
aliases:
  - <ADR-NNN: Short Title>
---

# ADR-NNN: [Short description of the decision]

|                   |                        |
| ----------------- | ---------------------- |
| **Decision Date** | [DD Mon YYYY, or TBD]  |
| **Owner**         | [Full Name]            |
| **Status**        | [Pending \| Accepted \| Rejected \| Deprecated] |

<!--
Status vocabulary:
  Pending    — new ADR seeking approval
  Accepted   — reviewed and approved by the team
  Rejected   — proposed but not accepted
  Deprecated — no longer relevant, or overridden by a later ADR
               (note supersession inline, e.g. "Deprecated — superseded by ADR-NNN")

Write an ADR only for architecturally significant decisions — ones that are
costly to reverse or have effects beyond a single component (structure/contract
changes, new or removed dependencies, deviations from an established pattern,
cross-cutting concerns). ADRs are human-authored and ratified; a decision an
agent makes while working belongs in vault/Decisions/ (type/decision) unless a
human promotes it here. Routine, reversible, pattern-following choices do not
need an ADR. See vault/ADL/README.md for the full guidance.
-->

## Issue

[The problem statement. You may want to form it as a question.]

## Options

[Short itemized list that can be quickly scanned. Supply the additional detail in the Context section below rather than here.]

- **[Option 1]** — [one-line description]
- **[Option 2]** — [one-line description]

## Decision

[The change we are proposing or have agreed to implement. State it in full sentences, in the active voice — "We will …" — and express the justification: "… because of criteria 1 and assumption 2".]

## Context

[The issue motivating this decision, any assumptions, and any context that influences or constrains the decision. Include more detail about the options here.]

## Evaluation

[Evaluate the pros and cons of the options against the constraints and the desired outcome.]

### [Option 1]

- **Pros:** …
- **Cons:** …

### [Option 2]

- **Pros:** …
- **Cons:** …

## Consequences

[What becomes easier or more difficult to do, and any risks introduced by the change that will need to be mitigated.]

**What becomes easier:**

- …

**What becomes more difficult:**

- …

**Risks to mitigate:**

- …

## See Also

- [[ADL/README|ADL]]
