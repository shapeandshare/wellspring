---
title: Constitution Article VII Rule 3 still requires a Mermaid pipeline diagram, but the README uses SVG
type: discovery
tags:
  - type/discovery
  - domain/governance
  - status/superseded
created: 2026-09-27
updated: 2026-09-27
aliases:
  - vii3-mermaid-drift
---

# Constitution Article VII Rule 3 still requires a Mermaid pipeline diagram, but the README uses SVG

Part of [[wellspring]]. Found while implementing specs/003-finetuning-integration.

## What

Article VII Rule 3 says a stage that changes the pipeline's shape "MUST update the
Mermaid diagram in `README.md`'s 'Pipeline' section". `docs/DESIGN.md` §3 item 12
also says "🔧 Pipeline (Mermaid diagram)". The README has no Mermaid diagram. It
deliberately uses `docs/assets/pipeline*.svg`, per
[[2026-09-27-readme-diagrams-are-hand-drawn-svg-not-mermaid]].

## Why it matters

A diagram-changing feature cannot satisfy the rule's literal text without undoing
a recorded decision. Feature 003 therefore updated the SVGs and did **not** add a
Mermaid block.

## Resolution (2026-09-27)

Resolved by constitution 1.1.1 (PATCH): Article VII Rule 3 now requires the animated SVG pairs. `docs/DESIGN.md` and `AGENTS.md` §10 were updated to match.

## Original resolution needed

A PATCH amendment to Article VII Rule 3 (and a `docs/DESIGN.md` §3 wording fix)
saying "the README pipeline diagram", with maintainer sign-off.
