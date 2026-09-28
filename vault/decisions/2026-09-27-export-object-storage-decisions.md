---
title: Export object-storage dispatch decisions
type: decision
tags:
  - type/decision
  - domain/orchestration
  - domain/provenance
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# Export object-storage dispatch decisions

Part of [[wellspring]]. Settles the two questions blocking export dispatch
Stage B, captured in spec 024.

## Context

Spec 013 moves checkpoints between hosts over SSH. Object storage is only
needed for hosts that can't be reached over SSH ahead of time.

## Decision

1. Spec it now as spec 024, blocked until the first export target that can't be
   reached over SSH ahead of time exists.
2. Any storage provider is allowed, chosen and supplied by the operator, with no
   defaults.

## Consequences

- Provenance recording with checksums (Article I) and the rule never to upload
  Red-only material (spec 003) still apply; they are not relaxed by option 2.
- Licence compliance per model and provider is the operator's responsibility,
  auditable via the manifest.
