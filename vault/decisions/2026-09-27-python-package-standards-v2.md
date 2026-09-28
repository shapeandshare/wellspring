---
title: Adopt layered async Python package standards (constitution 2.0.0)
type: decision
tags:
  - type/decision
  - domain/governance
  - domain/tooling
created: "2026-09-27"
updated: "2026-09-27"
status: draft
---

# Adopt layered async Python package standards (constitution 2.0.0)

Wellspring is about to grow a large Python package. Its standards are taken from the sibling constitutions of anvil, oldgrowth and darkharbour instead of being invented one PR at a time. Part of [[wellspring]].

## Context

Before this change, the constitution (v1.2.0) left out the layered architecture and async-first on purpose (YAGNI), and allowed module-level functions. Typing was a convention with no checker behind it, and the repo had no `pyproject.toml`, linter or coverage gate. The maintainer asked for these standards to be set up before the package is built.

## Decision

Amend the constitution to 2.0.0 (MAJOR, because Article XI Rule 3 is reversed):

- Articles IX–XII are hardened: a ratcheting coverage floor, characterization tests before changes, a rule set for test doubles, and Hypothesis tests. The decomposition threshold stays at 6, with as many domains as the intent needs. Logic lives in classes (anvil's "no loose functions") and imports go at the top of the file. `mypy --strict` is the gate.
- New articles: XVI Packaging & Toolchain, XVII Layered Architecture (`WellspringWorkbench` God Class → services → repositories/clients/SDKs, with DTOs/enums/types/errors), XVIII Async-First (compute kernels exempt), XIX Software Engineering Discipline, and XX iOS-Grade Polish.
- Pydantic over dataclasses, enums over magic strings, `--dry-run` plus a paired teardown, and pinned toolchains.
- `AGENTS.md` §13 is the operational checklist.

## Consequences

- Almost none of this is met yet. It is disclosed as MD-007 (tooling), MD-008 (loose functions), MD-009 (`src/wellspring/` does not exist) and MD-010 (nothing is async). They are planned in specs 020 (MD-007), 022 (MD-008), 021 (MD-009) and 023 (MD-010). Specs 005, 007, 008 and 010 were realigned to 2.0.0.
- `make test` and `make vault-audit` remain the only enforced gates until `make pr-ready` exists. Do not claim otherwise.
- Adding Pydantic requires an Article II licence check and a `make lock`/`make notices` re-run.
