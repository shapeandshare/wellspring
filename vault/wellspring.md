---
title: Wellspring Vault
type: moc
tags:
  - type/moc
  - domain/governance
created: 2026-09-26
updated: 2026-09-27
---

# Wellspring Vault

The hub of the Wellspring knowledge vault — the governed memory of the
project's own development. The vault holds the **agent audit trail**
(decisions, discoveries, session logs) produced while building and
extending this pipeline; it does not replace `PROVENANCE.md` (model/
dataset chain of custody) or `ROADMAP.md` (phase status), and cross-links
to them rather than duplicating them.

## Contents

### Decisions

Session-level decisions with context and consequences.

- `[[2026-09-26-metaflow-orchestration-wraps-not-reimplements]]`
- `[[2026-09-26-metaflow-flag-naming-underscored]]`
- `[[2026-09-27-llama-server-for-single-model-load-per-trial]]`
- `[[2026-09-27-responsible-use-policy-and-community-files]]`
- `[[2026-09-27-emblem-ripple-rings-static-and-breathe]]`
- `[[2026-09-27-vendor-external-inputs-fetch-only]]`
- `[[2026-09-27-readme-diagrams-are-hand-drawn-svg-not-mermaid]]`
- `[[2026-09-27-skip-decensor-requires-explicit-local-hf-path]]`
- `[[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]`
- `[[2026-09-27-finetuning-constitution-subsumed]]`
- `[[2026-09-25-consolidate-data-under-prefix]]`
- `[[2026-09-25-e2e-test-assertion-design]]`
- `[[2026-09-25-training-data-is-red-only]]`
- `[[2026-09-27-per-team-handoff-docs]]`
- `[[2026-09-27-verify-docs-instead-of-spot-checks]]`
- `[[2026-09-27-python-package-standards-v2]]`
- `[[2026-09-27-redblue-loop-decisions]]`
- `[[2026-09-27-export-object-storage-decisions]]`
- `[[2026-09-27-dataset-search-decisions]]`
- `[[2026-09-27-heretic-meta-search-decisions]]`
- `[[2026-09-27-no-joint-mlx-gguf-search]]`
- `[[2026-09-27-roadmap-reduced-to-spec-index]]`
- `[[2026-09-27-finetune-shell-scripts-ported-to-wellspring]]`

### Discoveries

Non-obvious constraints, gaps, and conflicts that cost discovery time.

- `[[2026-09-26-metaflow-step-process-boundary-breaks-os-environ]]`
- `[[2026-09-26-mps-svd-lowrank-hang]]`
- `[[2026-09-26-metaflow-resume-skips-completed-steps]]`
- `[[2026-09-26-ik-llama-cpp-converter-crashes-on-dense-llama-models]]`
- `[[2026-09-26-optimize-gguf-never-passed-gguf-out-dir-to-make]]`
- `[[2026-09-27-dependabot-cannot-regenerate-lock-or-notices]]`
- `[[2026-09-27-make-test-installs-full-requirements]]`
- `[[2026-09-27-readme-diagrams-were-dark-only]]`
- `[[2026-09-27-diagonal-connectors-misalign-arrowheads]]`
- `[[2026-09-27-constitution-vii3-still-says-mermaid]]`
- `[[2026-09-25-build-dataset-py-was-double-applying-the-chat-template]]`
- `[[2026-09-25-conda-lock-needs-an-explicit-osx-virtual-package-for-mlx]]`
- `[[2026-09-25-full-scale-runs-invert-the-mri-vs-probe-verdict-on-both-bases]]`
- `[[2026-09-25-gotchas-for-models-from-other-sources]]`
- `[[2026-09-25-the-handover-secrecy-check-was-passing-vacuously]]`
- `[[2026-09-25-training-data-is-as-secret-as-the-answer-key]]`
- `[[2026-09-25-weight-diff-s-ranking-reliability-depends-on-cohort-size-and-gqa-layout]]`
- `[[2026-09-26-trigger-specificity-is-configuration-dependent]]`
- `[[2026-09-27-dry-run-verification-is-not-verification]]`
- `[[2026-09-27-heretic-1-4-0-has-no-scorer-plugin-api]]`

### Sessions

Append-only session activity logs, never pruned.

- `[[2026-09-26-metaflow-migration-implementation]]`
- `[[2026-09-27-eval-refusal-rate-revision-pinning]]`
- `[[2026-09-27-fix-pr-findings-optimize-gguf]]`
- `[[2026-09-27-community-health-files]]`
- `[[2026-09-27-emblem-and-light-dark-assets]]`
- `[[2026-09-27-docs-redesign-and-skip-decensor]]`
- `[[2026-09-25-broaden-probe-for-other-sources]]`
- `[[2026-09-25-data-prefix-refactor]]`
- `[[2026-09-25-datasets-to-data-in]]`
- `[[2026-09-25-e2e-test-and-critical-bugfix]]`
- `[[2026-09-25-gitignore-hardening-and-parallel-session]]`
- `[[2026-09-25-makefile-conda-config]]`
- `[[2026-09-25-readme-tested-walkthrough]]`
- `[[2026-09-25-repo-bootstrap]]`
- `[[2026-09-25-second-model-and-gotchas]]`
- `[[2026-09-26-footgun-sweep]]`
- `[[2026-09-26-hackathon-hardening]]`
- `[[2026-09-27-per-team-docs]]`
- `[[2026-09-27-retire-finetuning-vault]]`

### References

Fine-tuning ("Spot the Sleeper") methodology, system and glossary notes, ported from `finetuning/vault`.

- `[[2026-09-25-broadening-probe-py-for-models-from-other-sources]]`
- `[[2026-09-25-e2e-smoke-test]]`
- `[[2026-09-25-glossary]]`
- `[[2026-09-25-methodology-register]]`
- `[[2026-09-25-spot-the-sleeper-pipeline]]`
- `[[2026-09-26-hackathon-failure-modes-and-guardrails]]`

## Reference

- `[[tags|Tag Vocabulary]]` — the controlled vocabulary every note draws from
- Templates: `vault/_meta/templates/`

## External anchors (outside the vault)

- Constitution: `.specify/memory/constitution.md`
- Provenance / chain of custody: `PROVENANCE.md`
- Third-party licenses: `THIRD_PARTY_NOTICES.md`
- Roadmap: `ROADMAP.md` (an index of `specs/`)
- Agent operating guide: `AGENTS.md`
- Responsible use policy: `RESPONSIBLE_USE.md`
- Community: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `SECURITY.md`
- GitHub templates, CI, Dependabot: `.github/`
- Change history: `CHANGELOG.md`
- Feature specs: `specs/`
</content>
