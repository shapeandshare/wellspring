---
title: <Title Case Name — matches filename without the date prefix>
type: decision
source: agent
related:
  # The session-log for the session in which this decision was made:
  - '[[Sessions/YYYY-MM-DD-session-title]]'
code-refs:
  - <path/to/file this decision affects — REQUIRED for verification>
session: ''
created: ''
updated: ''
summary: ''
tags:
  - type/decision
  - domain/<domain>
  - status/draft
aliases:
  - <same as title — becomes Obsidian graph node label>
---

<!--
Use this for a decision an agent MADE while working — a question or fork resolved
during a task that is NOT architecturally significant enough for a human-ratified
ADR. If it IS architecturally significant, flag it for a human to promote into an
ADR in ADL/ (then mark this note status/superseded and link the ADR in `related:`).
For a constraint an agent FOUND (an observation, not a choice), use the
agent-note template instead (type/discovery). See vault/Decisions/Decisions.md.
-->

{Framing sentence: one sentence stating the decision this note records.}

## Question

[What decision or question arose during the work? What was ambiguous, or what fork had to be resolved?]

## Decision

[What we chose. Active voice — "Chose X because …" / "We will …".]

## Rationale

[Why — the criteria, constraints, and assumptions that drove the choice.]

## Alternatives Considered

- **[Option]** — [why it was not chosen]

## References

- {file path(s) or source(s) this decision is grounded in — match the `code-refs:` frontmatter entries}
