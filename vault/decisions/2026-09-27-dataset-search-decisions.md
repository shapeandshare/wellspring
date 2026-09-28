---
title: Dataset search decisions
type: decision
tags:
  - type/decision
  - domain/provenance
  - domain/abliteration
  - status/reviewed
created: 2026-09-27
updated: 2026-09-27
---

# Dataset search decisions

Part of [[wellspring]]. Settles what the dataset search varies, which stage it
applies to, and what evidence is required before building. Captured in spec 025.

## Context

Spec 001 already searches calibration sample counts. Dataset identities are
pinned Makefile variables, and dataset licences are maintained by hand.

## Decision

1. Vary which rows are drawn and which dataset is used, choosing only from an
   approved list pinned by commit and licence-checked. Adding a dataset is one
   command.
2. P1 changes export calibration data; P2 changes abliteration prompts and shares
   spec 026's search loop and budget.
3. P1 is gated on a 5-trial spike comparing two datasets against run-to-run noise;
   P2 is gated on P1 showing an effect and on spec 026's budget.

## Consequences

- The approved list becomes the input that generates the dataset section of
  `THIRD_PARTY_NOTICES.md`.
