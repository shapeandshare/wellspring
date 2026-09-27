---
title: Design
type: moc
tags:
  - type/moc
  - domain/tooling
created: 2026-09-25
updated: 2026-09-25
aliases:
  - Design
---

# Design

Conceptual design, architecture rationale, and theses for this repository.

## Notes

- [[Design/Methodology Register|Methodology Register]] — **standing register** of every detection/training methodology and its status (ADOPTED / QUALIFIED / TUNED / RETIRED / DEFERRED), with reasons. Append here when a method changes.
- [[Design/Broadening probe.py for Models from Other Sources|Broadening probe.py for Models from Other Sources]] — methodology for handling models not produced by this repo's own train_variants.sh: what was adopted (tokenizer-driven chat templates, configurable markers/prompts), retired (hardcoded-format-only), and deliberately left alone (weight_diff.py's shared-base requirement). Verified against SmolLM2-135M.
- [[Design/Hackathon Failure Modes and Guardrails|Hackathon Failure Modes and Guardrails]] — the 16 ways this exercise misleads or blocks someone without detection-methodology background, and which guardrail now covers each. The design rule: interpretation belongs in the tool's own output, and cheap checks go in front of expensive steps.

## See Also

- [[index|Vault]]
- [[ADL/README|ADL]] — Architecture Decision Log
