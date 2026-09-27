---
title: Sessions
type: moc
tags:
  - type/moc
  - domain/vault
created: 2026-09-25
updated: 2026-09-25
aliases:
  - Sessions
---

# Sessions

Agent session logs — permanent, append-only audit trail of development activity.

## Notes

- [[Sessions/2026-09-25-repo-bootstrap|2026-09-25 Repo Bootstrap]] — gitignore, constitution, AGENTS.md, src/scripts reorg, and vault bootstrap.
- [[Sessions/2026-09-25-makefile-conda-config|2026-09-25 Makefile and Conda Config]] — peer-modeled Makefile + conda environment, verified end-to-end.
- [[Sessions/2026-09-25-e2e-test-and-critical-bugfix|2026-09-25 E2E Test and Critical Bugfix]] — built a repeatable e2e test, found and fixed a critical chat-template bug, characterized weight_diff's real ranking limits.
- [[Sessions/2026-09-25-broaden-probe-for-other-sources|2026-09-25 Broaden probe.py for Other-Source Models]] — generalized prompt rendering to the target model's own chat template; added configurable markers/prompts.
- [[Sessions/2026-09-25-second-model-and-gotchas|2026-09-25 Second Model, Gotchas, and Methodology Review]] — added SmolLM2-135M as a second base model, confirmed the GQA hypothesis as a predictor, fixed 2 bugs, opened the Methodology Register.
- [[Sessions/2026-09-25-data-prefix-refactor|2026-09-25 Consolidate Data Under a data/ Prefix]] — initial commit, then moved all pipeline data under data/in + data/out; answer key now structurally outside the Blue handover tree.
- [[Sessions/2026-09-25-datasets-to-data-in|2026-09-25 Move Training Data to data/in]] — datasets are an input AND a second copy of the answer key; moved out of the handover tree, Principle II broadened, concurrency guard added.
- [[Sessions/2026-09-25-gitignore-hardening-and-parallel-session|2026-09-25 Gitignore Hardening and a Parallel Agent Session]] — scratch-dir glob, raw-weight net and Obsidian trash added to .gitignore; then reconciled duplicate vault notes created by a second agent session editing the same tree concurrently.
- [[Sessions/2026-09-25-readme-tested-walkthrough|2026-09-25 README Rewritten as a Tested Walkthrough]] — ran the documented pipeline end to end on both bases; fixed two broken documented commands and a wrong docstring, and measured MRI precision@2 = 0/2 vs probe 2/2 on both.
- [[Sessions/2026-09-26-hackathon-hardening|2026-09-26 Hardening the Exercise for Non-Specialists]] — preflight + QA gate + calibrated hunt + recipe stamps; six runs showed trigger specificity is configuration-dependent, so it is gated per lineup rather than defaulted.
- [[Sessions/2026-09-26-footgun-sweep|2026-09-26 Second Footgun Sweep — Newcomer Safety]] — reviewed the new guardrails as a newcomer: the documented hit-count grep over-counted, train_variants pointed past the QA gate, make handover was shadowed by its own directory. Added probe.py sweep (make audit), make handover, make clean-data, a published-trigger warning and actionable errors.
- [[Sessions/2026-09-27-per-team-docs|2026-09-27 Per-Team Instructions and a Self-Describing Handover]] — Red/Blue/facilitator runbooks split out of the README, handover generates its own HANDOFF.md, preflight --blue added; writing Blue's doc separately caught an example block that named the real sleepers.

## Related MOCs

- [[Discoveries/Discoveries|Discoveries]] — Non-obvious constraints found during sessions
- [[Decisions/Decisions|Decisions]] — Choices made during sessions
- [[ADL/README|ADL]] — ADRs written during sessions
