---
title: Add community health files, Responsible Use policy, and CI gates
type: session-log
tags:
  - type/session-log
  - domain/governance
  - domain/tooling
created: "2026-09-27"
updated: "2026-09-27"
---

# Add community health files, Responsible Use policy, and CI gates

Part of [[wellspring]]. Goal: give Wellspring the files needed to run a
developer and user community, using the sibling `anvil` repo as the reference.

## What happened

- Compared the two repos. Anvil has CODE_OF_CONDUCT, SECURITY, SUPPORT,
  CODEOWNERS, PR and issue templates, dependabot, CI and release workflows,
  `.githooks/`, and a CHANGELOG. Wellspring had only CONTRIBUTING.md.
- Researched published responsible-use policies for abliterated models (model
  cards on Hugging Face and `RESPONSIBLE_USE.md` files on GitHub) and drafted
  `RESPONSIBLE_USE.md`: education/research only, local-law responsibility,
  universal prohibitions, operator duties, and no warranty.
- Wrote `SECURITY.md` (model output out of scope; weights, `ik_llama.cpp`
  build, and MLflow in scope) and `SUPPORT.md`. Adapted the Code of Conduct
  (Contributor Covenant 2.1) and CODEOWNERS from anvil.
- Added a PR template with Wellspring's gates, and issue templates for bugs,
  compatibility reports (new), features, and docs. `config.yml` turns off
  blank issues.
- Extended CONTRIBUTING with Community Guidelines. Added README Governance
  rows, one CAUTION callout, and a `setup-hooks` row.
- Added `ci.yml` (`make test` + `make vault-audit`), `dependabot.yml`,
  `CHANGELOG.md`, `.githooks/pre-commit`, and `make setup-hooks` (with its
  `make help` line).
- Verification: 167 tests passed; `make vault-audit` 0 errors / 0 warnings;
  the three YAML files parse. The CI workflow has not run on GitHub yet.

## Decisions & discoveries written back

- `[[2026-09-27-responsible-use-policy-and-community-files]]`
- `[[2026-09-27-dependabot-cannot-regenerate-lock-or-notices]]`
- `[[2026-09-27-make-test-installs-full-requirements]]`

## Follow-ups

- GitHub settings (maintainer only): turn on Discussions and private
  vulnerability reporting; require the `CI` check on `main`.
- A lawyer has not reviewed `RESPONSIBLE_USE.md`.
- The first CI run will show the real install time (see the make-test discovery).
- Not adopted from anvil: commitizen/semver release automation, and the
  commit-msg hook. Revisit if Wellspring starts tagging releases.
