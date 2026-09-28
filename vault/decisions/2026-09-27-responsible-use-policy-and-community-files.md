---
title: Adopt a Responsible Use policy and anvil-derived community health files
type: decision
tags:
  - type/decision
  - domain/governance
  - domain/tooling
created: "2026-09-27"
updated: "2026-09-27"
status: reviewed
---

# Adopt a Responsible Use policy and anvil-derived community health files

Part of [[wellspring]]. Wellspring ships the community files from the sibling
`anvil` repo, plus a `RESPONSIBLE_USE.md` that anvil has no equivalent for.

## Context

Wellspring had only `CONTRIBUTING.md`. Because it removes refusal behaviour,
the lawfulness of using it varies by jurisdiction. The maintainer asked for an
explicit "education/research only, you are responsible under your local law"
position. The wording was modelled on published policies for abliterated
models (for example Hugging Face model cards and `RESPONSIBLE_USE.md` files).

## Decision

- `RESPONSIBLE_USE.md` sets out in-scope research uses, says legality depends
  on jurisdiction, lists prohibited uses that apply everywhere (CSAM, CBRN
  uplift, unauthorised intrusion, harassment and fraud, upstream licence
  breach), operator obligations, and no warranty.
- `SECURITY.md` treats model *output* as out of scope. Untrusted weights, the
  source-built `ik_llama.cpp`, and MLflow URIs are in scope.
- The Code of Conduct, SUPPORT, and CODEOWNERS are adapted from anvil. Issue
  templates add a compatibility report that feeds `COMPATIBILITY.md`.
- CI runs only `make test` and `make vault-audit`. Heavy targets never run in CI.
- There is no commitizen or semver automation, because Wellspring cuts no
  releases. `CHANGELOG.md` collects entries under `Unreleased`.

## Consequences

- Posts containing harmful generations can be removed under the CoC and
  RESPONSIBLE_USE.
- Dependabot pip PRs still need `make lock && make notices` run by hand, since
  those files are generated.
- The lock/notices constraint behind the Dependabot rule: [[2026-09-27-dependabot-cannot-regenerate-lock-or-notices]].
- None of this is legal advice. A lawyer has not reviewed the policy text.
