---
title: <Title Case Name — matches filename without .md>
# This template produces Discoveries/ notes (type/discovery): an agent capturing a non-obvious
# constraint, gap, or conflict *found* during a session. There is no separate "agent-note" type
# in the controlled vocabulary. For a choice an agent *made* (a decision/question resolved during
# work), use the decision template instead — see _meta/templates/decision.md (type/decision).
type: discovery
source: agent
related:
  # The session-log for the session that produced this note:
  - '[[Sessions/YYYY-MM-DD-session-title]]'
code-refs:
  - <path/to/file this note is grounded in — REQUIRED for verification>
session: ''
created: ''
updated: ''
summary: ''
tags:
  - type/discovery
  - domain/<domain>
  - status/draft
aliases:
  - <same as title — becomes Obsidian graph node label>
---

{Framing sentence: one sentence stating what this note is and why it exists.}

{Body: prose and file-path references only. No inline code excerpts. File paths as plain text or
relative markdown links only.}

## References

- {file path(s) or source(s) this note is grounded in — match code-refs frontmatter entries}
