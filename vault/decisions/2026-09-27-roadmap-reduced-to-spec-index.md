---
title: ROADMAP.md reduced to a spec index
type: decision
tags:
  - type/decision
  - domain/governance
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# ROADMAP.md reduced to a spec index

Part of [[wellspring]]. Planning now lives in speckit specs; `ROADMAP.md` is
an index of them.

## Context

Every roadmap item became a spec (013–019, 024–026) or a recorded decision
not to build it. Deleting `ROADMAP.md` would contradict the constitution, which
names it as an authoritative reference in six places (lines 874, 886, 920, 1263,
1277 and 1296), so it was kept as an index instead.

## Decision

- `ROADMAP.md` lists every spec with its status and what blocks it; the specs
  are authoritative.
- Its unique content moved: the key finding to 001's `research.md`; the Metaflow
  constraint that a Mac can only launch runs, never run steps, to spec 013.
- Spec 012 (redraw the Mermaid diagram) is closed as not needed.

## Consequences

- The constitution's rule that each change updates `ROADMAP.md` now means
  keeping the index row current.
- Constitution amended to 2.0.1 (PATCH): ROADMAP.md is described as the spec
  index, and the 1.1.1 and 2.0.0 Mermaid follow-ups are recorded as resolved.
- Spec numbers 020–023 were taken concurrently; the new specs are 024–026.
