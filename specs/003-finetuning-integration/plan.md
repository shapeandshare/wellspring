# Implementation Plan: Integrate the Fine-Tuning Exercise into the Primary Pipeline

**Branch**: `003-finetuning-integration` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-finetuning-integration/spec.md`

## Summary

Fine-tuning ("Spot the Sleeper": build lineup → train → QA gate → handover
→ Blue audit → reveal) becomes a set of **optional, off-by-default steps**
inside the existing root Makefile chain and the existing `WellspringFlow`.
The steps always use the upstream pipeline model, run in either order
relative to decensoring, and feed every lineup variant into the existing
MLX/GGUF exports. All fine-tuning logic and docs are **moved** from `finetuning/` into
the root project, and the originals are deleted. Governance and vault items stay
in `finetuning/` for human review, listed in `finetuning/REVIEW.md`.
Track A (Apple Silicon) keeps the existing MLX tooling; Track B (Linux + NVIDIA) adds a torch/PEFT LoRA backend with
the same recipe. Resource warnings precede every expensive step and never
block it. Outcomes land in `COMPATIBILITY.md`. See [research.md](research.md)
for the decisions behind each piece.

## Technical Context

**Language/Version**: Python 3.14 (root `.venv`, per `.python-version`). The nested `finetuning/env` conda env is left in place (governance deferred) but is not used by the integrated path.

**Primary Dependencies**: existing — `metaflow`, `mlflow`, `torch`, `transformers` (via `heretic-llm`), `mlx-lm` (darwin marker). New — `peft` (Apache-2.0, Track B LoRA), `matplotlib` (PSF-based, MRI heatmaps). Both require an Article II licence check (R-3).

**Formats between stages**: HF safetensors is the interchange format at every stage boundary; conversion happens at the entry of Track A training (R-11).

**Storage**: root git-ignored `data/finetune/` (same in/out/answer-key layout as before, R-10); the Metaflow datastore and MLflow may hold Red-only artifacts (spec Q1 → C), with access controlled by the stores.

**Testing**: `pytest` under root `tests/` (Article IX test-first). The existing `finetuning/scripts/e2e_test.sh` runs behind an opt-in target and is not part of routine `make test` (SC-003).

**Target Platform**: Track A — macOS on Apple Silicon (MLX). Track B — Linux + NVIDIA CUDA (torch + PEFT). Any other host fails fast (FR-006).

**Project Type**: CLI/Makefile-driven ML pipeline with a Metaflow flow.

**Performance Goals**: no regression when disabled (SC-007). Measured baseline on Track A is 44 min to train 5 variants × 800 examples × 400 iters on TinyLlama (`finetuning/README.md` §Measured results), and it seeds the resource estimator (R-7).

**Constraints**: off by default. Upstream model only. Either stage order. Never block on size, platform verification or unknown models (FR-014). Secrets never reach Blue outputs (FR-007).

**Scale/Scope**: ~1B dev models up to `Qwen/Qwen3.6-35B-A3B`. Each run produces N variants (default 5). Exports scale by N.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Status | Notes |
|---|---|---|
| I Provenance (NN) | PASS | The run record adds stage order, platform, variant id, lineup parameters and recipe (data-model: RunRecord). Each exported artifact names its variant. |
| II Licence before dependency | PASS | The licence checks for `peft` (Apache-2.0) and `matplotlib` (PSF-based) are recorded in `THIRD_PARTY_NOTICES.md` in the same task that adds them to `requirements.txt`, before any lock or install (tasks T011). |
| III Two export paths never cross-feed | PASS | Each variant goes into MLX and GGUF independently. The paths still don't share calibration or outputs. |
| IV Atomic, safe-to-rerun (NN) | PASS | Train/fuse/merge write to `.tmp` and rename. Handover is staged to a temp dir, secrecy-checked, then renamed. |
| V Reproducibility bounded | PASS | Cross-platform parity is claimed only for the sleeper assignment and the QA verdict (SC-012), not for weights. |
| VI Simplicity | PASS | The existing Track A scripts are moved, not rewritten. There is one new backend (Track B) and no new orchestrator. |
| VII Makefile is the interface | PASS | Every step becomes a `.PHONY` target with a help line, README row and Key Variables row ([contracts/make-targets.md](contracts/make-targets.md)). **Rule 3**: the README "Pipeline" section currently has only an SVG, but both Rule 3 and `docs/DESIGN.md` §12 call for a Mermaid diagram. This feature adds the Mermaid diagram (standard `classDef`s) with the fine-tuning branch, next to the updated SVG. |
| VIII Fail fast | PASS | Missing upstream output, wrong platform, NO-GO verdict, leaked trigger and failed variant all stop before downstream work. Unknown models warn and proceed, by design (FR-014). |
| IX TDD (NN) | PASS | Every new or changed behaviour is test-first, including the default data paths and in-package imports changed during the move. The only untested tasks are pure `git mv` moves with zero content change, which count as no code change rather than an exemption. There are no Article IX exemptions. |
| X Package decomposition | PASS | New code goes into a new repo-root domain package `finetune/` ("any new top-level Python surface immediately"). Nothing is added to `scripts/`, so MD-003 isn't triggered and stays its own dedicated change. |
| XI One class per file / bare `__init__` | PASS | New package levels get docstring-only `__init__.py`. |
| XII Type hygiene | PASS | New modules are fully typed. Every function modified in a moved tool (path constants, imports, the probe backend hook) gets typed parameters and return types in the same task. Moved-but-unmodified functions stay as they are; that is noted in `finetuning/REVIEW.md` as follow-up debt. |
| XIII Agent conduct | PASS | Docs are updated in the same change (FR-019). Nothing is committed without being asked. |
| XIV Vault | PASS | A decision note is written for R-1/R-2/R-4 when implemented. |

**Result**: no unjustified violations. Article X is satisfied by a new top-level domain package; MD-003 is not triggered.

**Post-design re-check (after Phase 1)**: unchanged. One spec-level tension, SC-007 "step list identical", is noted in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-finetuning-integration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── make-targets.md       # new make targets + variables
│   └── flow-interface.md     # WellspringFlow parameters, steps, artifacts
└── tasks.md                  # /speckit.tasks (not created here)
```

### Source Code (repository root)

```text
Makefile                         # new ft-* targets, FINETUNE/STAGE_ORDER vars, setup/doctor/test hooks
flow.py                          # new params + finetune_pre / finetune_post / ft_gate / ft_audit steps
requirements.txt                 # + peft, matplotlib  (then make lock / make notices)
scripts/                         # unchanged by this feature (MD-003 remains open)
finetune/                        # new top-level domain package (Article X)
│   ├── __init__.py              # docstring only
│   ├── hostplatform.py          # detect Track A / B / unsupported (not "platform": avoids stdlib shadowing)
│   ├── backends.py              # dispatch: mlx wrapper vs torch/PEFT
│   ├── train_torch.py           # Track B LoRA train + merge (same recipe)
│   ├── probe_torch.py           # Track B load/generate for probe/reveal
│   ├── formats.py               # HF <-> MLX hand-off (R-11)
│   ├── resource_estimate.py     # FR-017 warning (never blocks)
│   └── lineup.py                # config validation, stage order
│   # also receives the MOVED tools (R-1):
│   ├── build_dataset.py reveal.py probe.py weight_diff.py preflight.py verify_docs.py
│   └── train_variants.sh handover.sh      # probe.py gains the backend hook (R-5)
docs/finetuning/                 # MOVED docs: REFERENCE.md (spoilers), RED.md, BLUE.md, FACILITATOR.md
data/finetune/                   # runtime data, git-ignored (R-10)
finetuning/                      # AFTER: only items left for human review (FR-022)
├── REVIEW.md                    # what remains, why, follow-up; moved-file map
├── AGENTS.md  .gitignore
├── .specify/**  vault/**  environments/**
tests/
├── test_finetune_platform.py
├── test_finetune_lineup.py
├── test_finetune_resource_estimate.py
├── test_finetune_train_torch.py     # tiny random model, CPU, seconds
└── test_flow.py                     # extended: disabled = no-op; both orders
docs/assets/pipeline*.svg, metaflow*.svg   # updated at source (FR-019)
README.md COMPATIBILITY.md PROVENANCE.md THIRD_PARTY_NOTICES.md CHANGELOG.md
```

**Structure Decision**: single project. All fine-tuning logic moves into the `finetune/` domain package and all docs into `docs/finetuning/`, then the originals are deleted. The work runs in three ordered commits: structural move → behaviour changes → delete originals and write `REVIEW.md` (R-1).

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|---|---|---|
| Idle graph nodes when fine-tuning is disabled | Metaflow graphs are static (R-2). SC-007 has been reworded to allow idle steps with identical outputs. | A second flow class would violate FR-012. |
| Second training backend (Track B) | Spec Q (clarify): both platforms, so the production model is reachable | MLX has no Linux/CUDA build, so there's no single-backend option. |
