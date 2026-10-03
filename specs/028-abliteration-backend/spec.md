# Feature Specification: Replace the Abliteration Backend

**Feature Branch**: `028-abliteration-backend`

**Created**: 2026-10-02

**Status**: Draft. This is the top priority, ahead of spec 027 (PR #22, parked).

**Input**: "Addressing the backend is now the actual top priority." The
pipeline's decensoring stage is Heretic 1.4.0 (`heretic-llm`, AGPL-3.0-or-later),
driven as a CLI subprocess through an `expect` script. Replace it with a
backend the project can control, so abliteration runs well on this Mac and on
rented CUDA, and the planned searches (specs 017, 025, 026) and remote
execution (spec 027) build on it.

## Why: measured problems with the current backend

Each item names the evidence a new agent can re-check.

1. **Apple Silicon is effectively unusable.** Heretic's default
   `row_normalization = "full"` (`vendor/heretic/config.default.toml:105`)
   calls `torch.svd_lowrank` once per abliterated matrix per trial
   (`vendor/heretic/src/heretic/model.py:587`). On this M4 Max (torch 2.14.1),
   MPS `torch.linalg.qr` on a 2048×10 matrix takes about 20 s per call versus
   about 0 s on CPU. `svd_lowrank(niter=6)` on 2048×2048 takes 228 s on MPS
   versus 0.012 s on CPU. The run looks hung, so the only workaround is
   `DEVICE_MAP=cpu`, which takes multiple hours for a 1.1B model. Repro: time
   `torch.linalg.qr(torch.randn(2048, 10, device="mps"))` followed by
   `torch.mps.synchronize()`. These measurements were made while two CPU jobs
   were running, so treat the numbers as indicative only. Recorded in the vault
   note `2026-09-26-mps-svd-lowrank-hang` (the corrected version is on PR #22;
   `main` still says "no MPS kernel").
2. **Licence boundary blocks integration.** AGPL means Heretic is used only as
   an unmodified CLI subprocess (AGENTS.md §9, THIRD_PARTY_NOTICES.md).
   Nothing may import it. As a result:
   - live trial tracking (spec 017) has no hook, and Heretic 1.4.0 has no
     Scorer plugin API (vault `2026-09-27-heretic-1-4-0-has-no-scorer-plugin-api`);
   - the search can only be steered through CLI flags.
3. **Interactive automation is fragile.** Heretic prompts interactively, so
   `src/scripts/heretic_automate.exp` drives it by matching prompts and
   sending keystrokes (arrow-down, Enter). It deliberately answers the
   checkpoint-recovery prompt with "start from scratch", so an interrupted
   search can never be continued (PR #22, vault
   `2026-10-02-remote-resume-restarts-heretic-search`).
4. **Version drift breaks installs.** On `main`, `requirements.txt` has
   unpinned `heretic-llm` and `optuna~=5.0`. pip then resolves heretic-llm
   1.1.0, whose CLI rejects the Makefile's flags (`unrecognized arguments`).
   The fix pins `heretic-llm==1.4.0` and `optuna~=4.7` and regenerates the
   lock, but it currently lives only on PR #22 (commits `d7f6ae1`, `23444ee`).
   **Until PR #22 merges, `main` cannot install a working Heretic.** Either
   cherry-pick those two commits or base the work on them.
5. **Searches need programmatic control.** Spec 026 searches Heretic's six
   meta-settings from outside, as a nested study that runs a full Heretic per
   trial. Spec 025 wants to vary its datasets. Both are limited to what the CLI
   exposes.

## What the current backend does (the contract to keep or replace)

| Touch-point (on `main`) | Role |
|---|---|
| `Makefile`: `abliterate`, `dev-abliterate`, `dev-abliterate-e2e`, `ft-decensor-lineup`, `log-abliteration-mlflow` | Operator entry points (Article VII) |
| `src/flow.py` `decensor` step (`_decensor_one`) | Builds the Heretic argv (model, commit, quantization, device map, seed, eight pinned dataset flags, `--export-strategy MERGE`) and calls `expect src/scripts/heretic_automate.exp`. Writes the provenance manifest (`src/scripts/write_manifest.py`) for the output. |
| `src/scripts/heretic_automate.exp` | Answers Heretic's prompts: start from scratch, first trial, save, path |
| Output | A merged HF checkpoint directory. `convert-mlx` (AWQ) and `convert-gguf` (imatrix) consume it unchanged. |
| `checkpoints/<sanitized-model>.jsonl` | Heretic's Optuna journal (study name `heretic`). Ingested by `src/scripts/log_heretic_to_mlflow.py`, idempotently, keyed on the journal path. |
| `src/scripts/eval_refusal_rate.py` | Copies Heretic's default refusal markers and system prompt, never importing them, so quantized-artifact scoring matches |
| `STAGE_ORDER=finetune_first` | Decensors every fine-tuned variant with identical settings (Article XV method parity) |
| Spec 027 (PR #22) `RemoteAgentService` | Runs the stage as `python src/flow.py run --only_step decensor …` (FR-016: the backend is behind a pipeline command) |
| Objectives | Minimise refusals on `mlabonne/harmful_behaviors` and KL divergence on `mlabonne/harmless_alpaca`, both at pinned commits (Makefile `*_PROMPTS_*` variables) |

The production model is `Qwen/Qwen3.6-35B-A3B` (`Qwen3_5MoeConfig`: hybrid
linear attention plus MoE, multimodal, 40 text layers under `text_config`).
The dev models are `TinyLlama/TinyLlama-1.1B-Chat-v1.0` and
`HuggingFaceTB/SmolLM2-135M-Instruct`, the latter at commit
`12fd25f77366fa6b3b4b768ec3050bf629380bac`.

## Clarifications

### Session 2026-10-02

- Q: Has a specific replacement already been chosen? → A: [NEEDS CLARIFICATION:
  is the replacement (a) an in-house implementation under `src/wellspring/`,
  (b) a named existing open-source tool, or (c) Heretic used as a library or
  fork, which reopens the AGPL position? If none is chosen yet, User Story 1
  makes the choice.]
- Q: Does Heretic stay as a selectable second backend? → A: [NEEDS
  CLARIFICATION: keep Heretic selectable, e.g. `ABLITERATION_BACKEND=heretic`,
  for comparison and rollback; or remove it once parity is shown?]

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The backend choice is decided on evidence (Priority: P1)

The operator gets a recorded decision naming the backend, with the evidence
for it against the criteria below.

**Why this priority**: Every later story depends on the choice. A wrong
choice costs the most here.

**Independent Test**: A vault decision note exists. It scores each candidate
on every criterion in FR-001, with citations or measurements, and names the
choice.

**Acceptance Scenarios**:

1. **Given** the candidates, **When** the evaluation ends, **Then** each one
   has a recorded licence (Article II) and a measured or cited answer for:
   Apple Silicon speed, CUDA multi-GPU, Qwen3.6 (hybrid MoE, multimodal)
   support, a programmatic API, resumable search, and the search controls
   specs 025/026 need.
2. **Given** a candidate that cannot load Qwen3.6, **When** it is scored,
   **Then** it is rejected, or kept only with a written plan for that gap.

---

### User Story 2 - The pipeline abliterates through a backend interface (Priority: P1)

`make abliterate`, `make dev-abliterate*`, the Metaflow `decensor` step and
`make ft-decensor-lineup` call one backend interface instead of an `expect`
script. They produce the same output contract: a merged HF checkpoint,
a provenance manifest and a trial history.

**Why this priority**: This is the change itself. It also removes the
`expect`/keystroke fragility.

**Independent Test**: With a fake backend (no model, no network), the
`decensor` step produces a checkpoint directory, a manifest naming the backend
and its version, and a trial history that ingests into MLflow. `make test`
stays hermetic.

**Acceptance Scenarios**:

1. **Given** the chosen backend, **When** `make dev-abliterate-e2e` runs on the
   dev model, **Then** it finishes without interactive input or `expect`, and
   its checkpoint converts with `make convert-mlx` and `make convert-gguf`
   unchanged.
2. **Given** an interrupted search, **When** it is restarted with the same
   settings, **Then** it continues from its recorded trials instead of
   starting over.
3. **Given** `STAGE_ORDER=finetune_first`, **When** the lineup is decensored,
   **Then** every variant uses identical backend settings, and the recipe
   stamps still detect a parity break (Article XV Rule 1).

---

### User Story 3 - Quality is at least Heretic's (Priority: P2)

The operator sees that the new backend's decensored dev models are no worse
than Heretic's on both objectives.

**Why this priority**: A faster backend that decensors worse is a regression.

**Independent Test**: For both dev models, at an equal trial budget and seed,
compare the new backend's best trial against Heretic 1.4.0's best trial on
refusals and KL divergence, using the same pinned evaluation datasets. The
comparison is recorded in MLflow and in a vault note.

**Acceptance Scenarios**:

1. **Given** both backends on the same dev model and budget, **When** they are
   scored on the same evaluation prompts, **Then** the new backend's refusals
   are ≤ Heretic's and its KL divergence ≤ Heretic's × 1.10. Otherwise the gap
   is stated and accepted explicitly.

---

### User Story 4 - Practical on this Mac, unchanged on rented CUDA (Priority: P2)

A dev-model abliteration runs on this M4 Max without forcing everything onto
the CPU. A production run works on spec 027's `prod` profile.

**Why this priority**: Fixing the Apple Silicon problem is the main
motivation. Remote execution must keep working.

**Independent Test**: A timed dev-model run on this Mac, with the device
recorded, against a CPU-only Heretic baseline measured as part of this
feature. No complete baseline exists yet: the 2026-10-02 CPU runs were
abandoned at about trial 25 of 200, with an extrapolated, unmeasured ~6 h for
TinyLlama. Plus a dry wiring check that spec 027's `ABLITERATE` stage command
still works.

**Acceptance Scenarios**:

1. **Given** this Mac, **When** a dev-model run executes, **Then** any op it
   moves from MPS to CPU is logged by name. Nothing that would change a
   result falls back silently (Article VIII).

---

### Edge Cases

- **A backend op is slow or missing on MPS:** run it on CPU explicitly and log
  it; never hang silently (the Heretic failure mode).
- **Multimodal configs (Qwen3.6):** layer counts and decoder layers come from
  `text_config` / `language_model`. On `main`, `src/finetune/preflight.py`
  still reads only the top-level `num_hidden_layers`; the fix is on PR #22
  (`d4a18e6`).
- **Existing Heretic journals and MLflow runs:** they stay readable and stay
  distinguishable by a `backend` tag.
- **Models the backend cannot load:** fail before any search starts, with a
  named error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backend MUST be chosen against recorded criteria:
  - licence compatible with the project's MIT licence and its "invoke, don't
    import" posture, or an explicit Article II review;
  - Apple Silicon (MPS) performance;
  - CUDA multi-GPU support;
  - Qwen3.6 support;
  - a programmatic (non-interactive) API;
  - resumable search;
  - exposure of the meta-settings and datasets specs 025/026 need.
- **FR-002**: All abliteration MUST go through one backend interface, an SDK
  wrapper in `src/wellspring/` (Article XVII). It is used by the Makefile
  targets, the Metaflow `decensor` step and `ft-decensor-lineup`. No `expect`
  or keystroke automation remains on the default path.
- **FR-003**: The output contract MUST be unchanged for downstream stages: a
  merged HF checkpoint that `convert-mlx` and `convert-gguf` consume as-is.
- **FR-004**: Every run MUST record provenance (Article I): backend name,
  version or commit, every setting, the seed, model commit and dataset
  commits.
- **FR-005**: Trial history MUST land in MLflow, live during the run if the
  backend allows (superseding spec 017's spike), and idempotently either way.
  Each run is tagged `backend=<name>`.
- **FR-006**: An interrupted search MUST resume from its recorded trials.
- **FR-007**: The search MUST expose its meta-settings programmatically, so
  spec 026 can drive them without a subprocess per trial when the backend
  allows it.
- **FR-008**: On Apple Silicon, any op the backend moves off MPS MUST be
  logged by name. A fallback that would change a recorded result fails loudly
  (Article VIII).
- **FR-009**: Method parity across a fine-tuning lineup MUST hold
  (Article XV Rule 1).
- **FR-010**: New code is test-first and hermetic (Article IX), using a fake
  backend for pipeline tests.
- **FR-011**: The default backend's licence MUST be recorded in
  `THIRD_PARTY_NOTICES.md`, `README.md` and `PROVENANCE.md` in the same
  change. If Heretic is removed, its AGPL flag and the `vendor/heretic`
  reference copy are retired or explicitly kept, with the reason stated.
- **FR-012**: `eval_refusal_rate.py`'s refusal markers and system prompt MUST
  match whatever the new backend scores with, or the difference is stated.

### Key Entities

- **Backend settings**: everything that determines a run (method parameters,
  meta-settings, datasets and their commits, seed). Recorded per run.
- **Trial record**: one evaluated parameter set with its refusals, KL
  divergence and any extra scores. This replaces the Heretic journal as the
  history contract.

## Success Criteria *(mandatory)*

- **SC-001**: A dev-model run on this Mac finishes in no more than 25% of the
  wall-clock time of a CPU-only Heretic baseline at the same trial budget. The
  baseline is measured as part of this feature (see User Story 4).
- **SC-002**: For both dev models, the new backend's best trial is at least
  as good as Heretic's (User Story 3 thresholds).
- **SC-003**: `make dev-abliterate-e2e` needs zero interactive input and no
  `expect`.
- **SC-004**: An interrupted run, restarted, completes in no more trials than
  were remaining when it stopped.

## Assumptions

- The production abliteration still runs on rented CUDA (spec 027, `prod`
  profile g6e.12xlarge, still a candidate). This Mac handles dev models.
- MLX export, GGUF export and their quantization studies (spec 001) are
  unchanged.
- The pinned evaluation datasets stay the same, so the comparison with Heretic
  is fair.

## Dependencies and context for whoever picks this up

- **PR #22 (draft, spec 027)** holds the dependency fix, the `ft-preflight`
  fix, the corrected MPS vault note, the compute decision and remote
  execution. Read its description. Rebase onto it, or cherry-pick
  `d7f6ae1` + `23444ee` + `d4a18e6`, if `main` still lacks them.
- **Specs 017, 025 and 026** assume Heretic. Once a backend is chosen, update
  or supersede each one in the same change (ROADMAP.md is the index).
- **Read first**:
  - `vendor/heretic/` (pinned v1.4.0 source: `model.py`, `main.py`,
    `evaluator.py`, `config.py`);
  - AGENTS.md §1 (verify against source), §9 (licence flags), §13 (package
    rules);
  - constitution Articles I, II, VIII, IX, XV, XVII, XVIII.

## Out of Scope

- Changing MLX/GGUF export or quantization.
- Remote execution itself (spec 027). Only its `ABLITERATE` stage command may
  need re-pointing.
- Fine-tuning recipe changes.
