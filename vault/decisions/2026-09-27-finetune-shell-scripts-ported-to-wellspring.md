---
title: Fine-tuning Shell Scripts Ported to the Layered wellspring Package
type: decision
source: agent
related:
- '[[wellspring]]'
- '[[2026-09-27-python-package-standards-v2]]'
- '[[2026-09-25-e2e-test-assertion-design]]'
session: '2026-09-27'
created: '2026-09-27'
updated: '2026-09-27'
summary: src/finetune/ held three shell scripts (train_variants.sh, handover.sh, e2e_test.sh) in a Python package, against AGENTS.md section 13 ("a new .sh script -> a Python class under src/"). They were rewritten as services in src/wellspring/ (the first code in the layered package), exposed as `python -m wellspring ft-train-mlx | ft-handover | ft-e2e`, and the scripts deleted.
tags:
- type/decision
- domain/finetuning
- domain/tooling
- status/draft
aliases:
- Fine-tuning Shell Scripts Ported to the Layered wellspring Package
code-refs:
- src/wellspring/workbench.py
- src/wellspring/cli.py
- src/wellspring/finetune/services/handover_service.py
- src/wellspring/finetune/services/mlx_train_service.py
- src/wellspring/smoke/services/e2e_smoke_service.py
---

# Fine-tuning Shell Scripts Ported to the Layered wellspring Package

The three shell scripts in `src/finetune/` are now Python services in `src/wellspring/`. They are
the first code in the layered package, and they keep the scripts' env-var interface so existing
invocations still work.

## Context

`src/finetune/` is a Python package, but it held `train_variants.sh` (Track A mlx-lm train + fuse),
`handover.sh` (stage and secrecy-check Blue's copy) and `e2e_test.sh` (the `make ft-e2e` smoke
test). AGENTS.md section 13 forbids `.sh` scripts, and new code belongs in `src/wellspring/`, not in
the legacy layout.

## Decision

- **Layout.** `finetune/` holds the handover, the handoff note, the trigger scan and the MLX trainer.
  A second domain, `smoke/`, holds the e2e harness. It is split out because six-plus services in
  one layer is the split threshold. `_shared/` holds the subprocess SDK. `WellspringWorkbench` is
  the composition root, and `python -m wellspring` is the entry point.
- **Interface preserved.** Every flag falls back to the env var the script read (`MODELS`, `DEST`,
  `KEY`, `BASE`, `ITERS`, `FT_TYPE`, `LR`, `BATCH`, `NUM_LAYERS`, `SCRATCH`, ...). The exit codes
  are unchanged: `ft-handover` returns 0 staged, 1 refused, 2 unverified. The recipe-stamp JSON
  keeps the same keys and types, including `learning_rate` as a string.
- **Callers.** `backends.py` (Track A) and `flow.py` (`ft_gate`) now launch `python -m wellspring …`
  with `PYTHONPATH=src`, which keeps the subprocess boundary they had. `verify_docs.py` checks the
  handoff template in `handoff_note_service.py` and validates `python -m wellspring` subcommands
  and flags.
- **Gates kept honest.** The trigger scan raises on a missing root instead of reading "no match"
  (the `grep -r` exit-2 trap). Handover and e2e still self-test by planting a leak.
- **Two small behaviour changes, both deliberate.** The APFS clone (`cp -Rc`) is only tried on
  macOS, because GNU `cp -c` means something else. A leak refusal now points at the source models
  directory, not the already-deleted staging copy.

## Consequences

- Runnable by hand as `PYTHONPATH=src python -m wellspring ft-train-mlx …`. The `make` targets set
  `PYTHONPATH` themselves.
- Hermetic tests now cover the handover, the trainer (with a fake mlx backend), the scratch lock
  and the secrecy check (`tests/test_wellspring_*.py`). Before this, only the slow e2e covered them.
- Verified end to end: `make ft-e2e BASE=data/finetune/in/smollm2-base SCRATCH=./.e2e-smollm`
  passed every check in 2m9s. That covers the ported trainer, the handover (both the clean and
  the planted-leak cases) and the final secrecy gate. The TinyLlama default (~37 min) was not
  re-run.
- Historical vault notes and `specs/` still name the old scripts. They are records of the time and
  were deliberately left as written. Only their `code-refs` frontmatter was retargeted.
