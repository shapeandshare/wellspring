---
title: Vendor external inputs by fetching into vendor/, tracking only manifests
type: decision
tags:
  - type/decision
  - domain/tooling
created: "2026-09-27"
updated: "2026-09-27"
status: reviewed
---

# Vendor external inputs by fetching into vendor/, tracking only manifests

Part of [[wellspring]]. External repos, datasets and the dev model can now
be held under `vendor/`. This is optional, and the dataset and model bytes
are never committed.

## Context

The user asked to gather the system's external dependencies under
`vendor/`. Several of the inputs cannot be redistributed. `tatsu-lab/alpaca`
is CC-BY-NC-4.0. The `mlabonne/*` sets declare no licence. `harmful_behaviors`
is harmful-prompt content. COCO mixes per-image Flickr terms.

## Decision

- `LLAMA_CPP_DIR` now defaults to `vendor/ik_llama.cpp`. It is still a
  pinned shallow fetch, not a submodule, and it is git-ignored.
- `make vendor-datasets` and `make vendor-dev-model` use
  `src/scripts/fetch_vendor_snapshot.py`. It accepts full-SHA revisions
  only, installs atomically, and writes a tracked
  `<name>.provenance.json` with per-file SHA-256. The bytes are
  git-ignored.
- COCO is not vendored. The Qwen production model is not vendored.
- The pipeline does not read the snapshots; they are archival only.

## Consequences

- Existing checkouts must move `ik_llama.cpp/` and rebuild it. CMake and
  the dylib rpaths embed absolute paths: the moved binaries failed to load
  `libllama.dylib` until a fresh `build/` was made.
- `.gitignore`'s repo-wide `models/` rule shadows `vendor/models/`. The
  re-include has to come after that rule.
