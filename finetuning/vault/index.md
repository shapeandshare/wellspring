---
title: Vault
type: reference
tags:
  - type/reference
  - domain/vault
created: 2026-09-25
updated: 2026-09-25
aliases:
  - vault-index
---

# Vault

The canonical agent-memory surface for `finetuning` ("Spot the Sleeper") — a runnable scaffold
for a poisoned-model detection hackathon exercise. Red fine-tunes a lineup of TinyLlama variants
(some carrying a hidden backdoor); Blue ranks them by suspicion using a weight-diff "Model MRI"
plus behavioral probing; a reveal checks Blue's ranking against Red's answer key.

Open this vault in [Obsidian](https://obsidian.md) for graph navigation.

## Navigation

| Section | Description |
|---------|-------------|
| [[Governance/Constitution\|Governance]] | Constitution, policies, principles |
| [[Design/Design\|Design]] | Conceptual design and rationale |
| [[Systems/Systems\|Systems]] | Implemented subsystems and tooling |
| [[Code/Code\|Code]] | Code-architecture notes: modules, classes, conventions |
| [[Specs/Specs\|Specs]] | Specification notes tracking feature spec status |
| [[ADL/README\|ADL]] | Architecture Decision Log — human-authored ADRs |
| [[Decisions/Decisions\|Decisions]] | Agent-authored decisions made during work |
| [[Reference/Reference\|Reference]] | Glossary, architecture guides, topic references |
| [[Discoveries/Discoveries\|Discoveries]] | Non-obvious constraints found during sessions |
| [[Sessions/Sessions\|Sessions]] | Agent session logs |

### Vault Meta

- [[_meta/tags|Tag Vocabulary]] — Controlled tag vocabulary for vault notes

## Quick Links

| Topic | Docs |
|-------|------|
| **Flow** | [[Systems/Spot the Sleeper Pipeline\|Spot the Sleeper Pipeline]] · `README.md` |
| **Glossary** | [[Reference/Glossary\|Glossary]] |
| **Governance** | [[Governance/Constitution\|Constitution]] |
