---
description: "Task list for 003-finetuning-integration"
---

# Tasks: Integrate the Fine-Tuning Exercise into the Primary Pipeline

**Input**: `specs/003-finetuning-integration/` — plan.md, spec.md, research.md (R-1…R-13), data-model.md, contracts/make-targets.md, contracts/flow-interface.md, quickstart.md

**Tests**: MANDATORY (Article IX, NON-NEGOTIABLE). Every new or changed behaviour, including path defaults and imports changed during the move, gets a failing test first. **No Article IX exemptions are used.**
- Pure `git mv` tasks (content unchanged) are not code changes, so there is nothing to test-drive. They are verified by the unchanged suite.
- Documentation and SVG tasks are not functional code. They are verified by the doc verifier, by running each documented command, and by rendering the diagrams and looking at them (AGENTS.md §4).

**Types** (Article XII): every new function, and every function modified in a moved file, gets typed parameters and a typed return in the same task.

**Commit boundaries** (R-1, Article X Rule 3):
- A: T003 (MD-003 split).
- B: T005–T008 (pure `git mv` moves).
- Everything after B changes behaviour.
- Never mix a move with a behaviour change.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Record baselines before any change, all under `/tmp/003-baseline/`:
  - the `make test` result and wall-clock time (for SC-003);
  - the `make help` output;
  - the `python flow.py show` output;
  - the `make -n abliterate dev-abliterate-e2e optimize` output.
- [X] T002 Record the fine-tuning baseline for FR-008 before anything moves. In `finetuning/`, on Track A at dev scale (seed 0, `--variants A,B,C,D,E --sleepers B,E`), run preflight → `build_dataset.py` → `train_variants.sh` → `make qa`, using the existing commands. Save the answer key, the QA verdict, `sha256` of every `train.jsonl`, and the recipe stamps to `/tmp/003-baseline/finetune/`.

---

## Phase 2: Foundational (blocks all stories)

### Commit A — MD-003 split (structural only)

- [X] T003 **Deferred (not executed) — plan deviation.** New code goes into a repo-root domain package `finetune/` instead of `scripts/finetune/`. The constitution's MD-003 is triggered only when a feature "adds further to `scripts/`", and this feature no longer does. The split itself would rewrite every flat import (`import _mlflow_env`, …) and every `python scripts/x.py` invocation into `python -m` form. MD-003 stays open as its own dedicated structural change.
- [X] T004 **Not needed**: MD-003's status is unchanged, so no constitution amendment is required.

### Commit B — pure moves of `finetuning/` (FR-021)

- [X] T005 `git mv` these files with no content changes:
  - `finetuning/src/{build_dataset,preflight,probe,reveal,weight_diff}.py` → `finetune/`
  - `finetuning/scripts/{train_variants.sh,handover.sh,e2e_test.sh,verify_docs.py}` → `finetune/`
- [X] T006 `git mv finetuning/docs/{RED,BLUE,FACILITATOR}.md docs/finetuning/` and `git mv finetuning/README.md docs/finetuning/REFERENCE.md`, with no content changes.
- [X] T007 Create `finetune/__init__.py` (docstring only, Article XI).
- [X] T008 Gate for commit B: `make test` is unchanged from T001, and `git diff -M --stat` shows only renames at 100% similarity, plus the new `__init__.py`.

### Relocation behaviour (test-first; FR-021, FR-023, R-10)

- [X] T009 [P] Write failing tests in `tests/test_finetune_paths.py`. The default paths of every moved CLI must resolve under the root `data/finetune/`:
  - `in/` and `out/`
  - `answer_key.json`, a sibling of `out/` and never inside it
  - `handover/` and `triggers.txt`

  Also assert that no default path points into `finetuning/`. Each CLI's `--help` exits 0 when run from the repo root. `reveal` imports `probe` from `finetune`. Each `.sh` finds its Python siblings relative to its own directory.
- [X] T010 Make T009 pass: repoint the path constants and defaults, fix the in-package imports and the shell sibling lookups, and point `verify_docs.py` at `docs/finetuning/*.md`. Every function touched gets full type hints (Article XII). Files: `finetune/*.py`, `finetune/*.sh`.
- [X] T011 Article II before dependency:
  - add `peft` (Apache-2.0) and `matplotlib` (PSF-based) with their licence notes to `THIRD_PARTY_NOTICES.md`;
  - then add both to `requirements.txt`, and raise `mlx-lm` to `>=0.18` (the darwin marker stays);
  - `git rm finetuning/requirements.txt`;
  - run `make lock` and `make notices`;
  - verify `peft` imports on Python 3.14 in `.venv`. **If it fails: stop and report; do not change Python.**
- [X] T012 Add `data/finetune/` to the root `.gitignore`. Retarget the still-relevant rules from `finetuning/.gitignore` (answer key, handover, triggers.txt, adapters, models). Check with `git status` after a dry dataset build (AGENTS.md §9).
- [X] T013 Fix the cross-links between the moved docs (`docs/finetuning/*.md`). Gate: `.venv/bin/python finetune/verify_docs.py` passes. *(Done: relative links fixed. The full verify_docs pass depends on the doc command rewrites and the root `ft-*` targets, so it is gated at T056.)*

### Shared modules (test-first)

- [X] T014 [P] Write failing tests in `tests/test_finetune_platform.py`. `detect_platform()` returns `track_a` on darwin/arm64 and `track_b` on Linux when CUDA is available. On any other host it raises `UnsupportedPlatformError`, naming both supported platforms (FR-006). Mock `platform` and `torch.cuda.is_available`.
- [X] T015 [P] Write failing tests in `tests/test_finetune_lineup.py` for `PipelineConfig.validate()`, quoting data-model.md:
  - `stage_order` ∈ {`decensor_first`, `finetune_first`} and is "Ignored when `finetune=False`";
  - `ft_variants` "≥ 2";
  - `ft_sleepers` "Subset of variants, ≥ 1";
  - `ft_trigger` "required when enabled";
  - `ft_n_train` / `ft_n_valid` / `ft_iters` "> 0".
- [X] T016 [P] Write failing tests in `tests/test_finetune_resource_estimate.py`:
  - TinyLlama on Track A at 5×800×400 gives ≈44 min, from the measured baseline in `docs/finetuning/REFERENCE.md`;
  - an unmeasured architecture or platform gives `unknown`;
  - Track B adds an hourly-cost note;
  - the export cost is multiplied by the number of variants (FR-020);
  - the estimate never raises and never returns a blocking status (FR-014, FR-017).
- [X] T017 [P] Write failing tests in `tests/test_finetune_formats.py` (R-11), using a tiny random model:
  - `to_mlx(hf_dir)` produces an MLX dir (darwin only, skipped elsewhere);
  - `ensure_hf(dir)` accepts a PEFT-merged save and an `mlx_lm.fuse --de-quantize` output, loading each via `transformers.AutoModelForCausalLM.from_pretrained`;
  - `ensure_hf` raises `NotHFLoadableError` on an MLX-only dir.

  **If `mlx_lm.fuse` output is not HF-loadable, stop and re-plan R-11.**
- [X] T018 [P] Write a failing test in `tests/test_finetune_model_agnostic.py` (FR-018a). A static scan of `finetune/` and the fine-tuning parts of `flow.py` finds no model-name or architecture-class string literals outside an allow-list of documented defaults (`DEV_MODEL`, the SmolLM2 id, `MODEL`).
- [X] T019 Implement `finetune/hostplatform.py` (T014; named to avoid shadowing stdlib `platform` when `finetune/` is `sys.path[0]`), `finetune/lineup.py` (T015), `finetune/resource_estimate.py` (T016: `estimate() -> ResourceWarning`, and `print_warning()`, which always exits 0) and `finetune/formats.py` (T017). Make T018 pass. All fully typed.

**Checkpoint**: the tools live at the root, the tests pass, and the shared modules exist.

---

## Phase 3: User Story 1 — Fine-tuning from the root make system (P1) 🎯 MVP

**Goal**: every fine-tuning stage runs from the root on Track A and Track B.

**Independent test**: from a fresh clone, run `make setup && make dev-doctor && make ft-datasets ft-train ft-qa ft-wordlist ft-handover FT_TRIGGER=… MODEL=$DEV_MODEL`. Every target appears in `make help`, and the T002 comparison holds.

- [X] T020 [P] [US1] Write failing tests in `tests/test_finetune_train_torch.py`, with a tiny random causal LM on CPU and a 4-row JSONL:
  - 2 LoRA steps with the `train_variants.sh` recipe mapping (iters, lr, batch, num_layers, rank, scale);
  - `merge_and_unload()` output plus a recipe stamp in `<models>/<variant>/`, and `ensure_hf` passes;
  - the chat template is applied exactly once (the double-template regression);
  - the write is atomic via `.tmp` + rename (Article IV).
- [X] T021 [P] [US1] Write failing tests in `tests/test_finetune_backends.py`:
  - `train_variant()` on `track_a` runs `to_mlx` → `train_variants.sh` → `ensure_hf`;
  - on `track_b` it runs `train_torch`;
  - `platform` is recorded in the recipe stamp.

  Mock the subprocess and the functions.
- [X] T022 [US1] Implement `finetune/train_torch.py` (R-4) to pass T020.
- [X] T023 [US1] Implement `finetune/backends.py` `train_variant()` to pass T021.
- [X] T024 [P] [US1] Write failing tests in `tests/test_makefile_targets.py`:
  - `make help` lists every target in `contracts/make-targets.md`;
  - `make ft-datasets FT_TRIGGER=` (run, not `-n`) exits non-zero with a clear message from a recipe guard;
  - `make ft-clean-data` refuses (non-zero) when its path variable is empty, `/` or `.` (Article IV guard);
  - `make ft-clean-data` never deletes `data/finetune/answer_key.json` or `data/finetune/in/datasets/`.
- [X] T025 [US1] Add the Makefile variables with their defaults:
  - `FINETUNE ?= 0`
  - `STAGE_ORDER ?= decensor_first`
  - `FT_VARIANTS ?= A,B,C,D,E`
  - `FT_SLEEPERS ?= B,E`
  - `FT_TRIGGER ?=`
  - `FT_N_TRAIN ?= 800`
  - `FT_N_VALID ?= 100`
  - `FT_ITERS ?= 400`
- [X] T026 [US1] Add these `.PHONY` targets, each with a `make help` line: `ft-preflight`, `ft-datasets`, `ft-train`, `ft-qa`, `ft-wordlist`, `ft-handover`, `ft-audit`, `ft-reveal`, `ft-verify-docs`, `ft-clean-data` (with the guarded `rm -rf`), and `ft-e2e`.
  - Training, decensor and export targets call `resource_estimate.print_warning` first.
  - The base model is always `MODEL`, or `DEV_MODEL` in dev targets (FR-012), as a local HF dir.
  - Make T024 pass. File: `Makefile`.
- [X] T027 [US1] Extend `setup`, `doctor`/`dev-doctor`, `test` and `clean` in `Makefile`:
  - doctor gets a fine-tuning readiness section; *(implemented as `python -m finetune.cli doctor`, which reports the host track and the imports that track needs. It is informational and never fails doctor. `ft-preflight` runs the full `preflight.py` on the resolved upstream base.)*
  - it fails fast if the interpreter is not the root `.venv`;
  - `test` includes `tests/test_finetune_*.py` but excludes `ft-e2e`;
  - `clean` keeps the answer key and datasets.
- [X] T028 [US1] Manual QA on Track A, at dev scale with the T002 settings:
  - run the independent test;
  - compare against `/tmp/003-baseline/finetune/`: the same answer key and QA verdict, and identical `train.jsonl` hashes (FR-008);
  - repeat `ft-train` on Track B; *(**Not run**: this host has no NVIDIA GPU. Track A matched the T002 baseline: identical `train.jsonl` hashes and answer key, QA GO, at the scaled-down T002 settings n_train=200/n_valid=40/iters=100.)*
  - record both in `COMPATIBILITY.md` (T055).

**Checkpoint**: MVP.

---

## Phase 4: User Story 2 — Chained local pipeline with gates (P2)

**Goal**: `make finetune` chains the stages and stops at every gate. With `FINETUNE=1` the existing chains run fine-tuning in the chosen order, with provenance and per-variant exports.

**Independent test**: quickstart §2–§3.

- [X] T029 [P] [US2] Write failing tests in `tests/test_finetune_chain.py`, with the stage commands stubbed:
  - a QA `NO-GO` means `ft-handover` never runs and the chain exits non-zero;
  - a planted trigger in the staged handover makes the secrecy check fail, removes the staged dir and exits non-zero;
  - the handover is staged in `.tmp` and renamed only on pass.
- [X] T030 [US2] Implement the `finetune` chain target in `Makefile`, with gate propagation, to pass T029. Change `finetune/handover.sh` only for atomic staging, with typed/tested behaviour covered by T029.
- [X] T031 [P] [US2] Write failing tests in `tests/test_finetune_order.py`:
  - `resolve_stages(finetune, stage_order)` returns `[decensor, finetune]`, `[finetune, decensor]`, or `[decensor]` when disabled;
  - with `finetune_first`, decensoring gets every variant, with identical settings and seed (FR-015);
  - any variant failing fails the run with no handover;
  - every stage boundary passes through `ensure_hf` (R-11).
- [X] T032 [US2] Implement `resolve_stages` in `finetune/lineup.py` and wire `FINETUNE`/`STAGE_ORDER` into `abliterate`, `dev-abliterate-e2e` and `optimize` in `Makefile`. With `FINETUNE=0`, the `make -n` output must equal T001's.
- [X] T033 [P] [US2] Write failing tests in `tests/test_write_manifest.py` for the new RunRecord fields: `finetune`, `stage_order`, `platform_per_stage`, `variant_id`, lineup params, recipe. `variant_id` is present and the role is absent on export manifests (FR-009, R-13).
  *(Done via `WellspringFlow._variant_manifest_fields`, tested in `tests/test_flow_exports.py`. `write_manifest.py` already accepts arbitrary `--field k=v` and the export searches already take `extra_manifest_fields`, so no change to `write_manifest.py` was needed.)*
- [X] T034 [US2] Extend `scripts/provenance/write_manifest.py` to pass T033. With `FINETUNE=1`, make the make chain loop the existing `convert-mlx` and `gguf`/`optimize` targets over `data/finetune/out/models/*`, with identical settings and `HF_PATH` set per variant, writing a manifest for each (FR-020, R-13). File: `Makefile`.
  *(Exports go to `<FT_DATA_ROOT>/out/exports/<variant>-{mlx,gguf}`, not next to the lineup, because a sibling dir would be counted as a model by the handover. Smoke-run: a 1-variant MLX export wrote `variant_id=A, finetune=true, stage_order=decensor_first, platform=track_a` into the study manifest. The GGUF trial failed because no `model-f16.gguf` exists without `convert-gguf`, which is also the known dense-Llama GGUF bug in COMPATIBILITY.md. The run itself completed.)*
- [X] T035 [US2] Manual QA: quickstart §2 and §3 on Track A, covering both gate failures, one GO run, and the per-variant exports and manifests.
  *(Run on Track A at T002 settings: `make finetune` → GO plus a verified handover. `FT_ITERS=1` → NO-GO, make stopped at `ft-qa`, and no handover dir existed.)*

---

## Phase 5: User Story 3 — Optional steps in the Metaflow flow (P3)

**Goal**: `WellspringFlow` runs fine-tuning optionally, in either order, on both tracks, with an export for every variant.

**Independent test**: quickstart §4–§5.

- [X] T036 [P] [US3] Extend `tests/test_flow.py` with failing tests:
  - the new params exist: `finetune` (default `False`), `stage_order` (default `decensor_first`) and `ft_*`;
  - the graph is `start → finetune_pre → decensor → log_to_mlflow → finetune_post → ft_gate → (mlx_search ∥ gguf_search) → join_searches → ft_audit → end`;
  - with `finetune=False`, the new steps do no work and `model_paths == [upstream]`;
  - `--only_step` accepts the new names;
  - each expensive step prints a ResourceWarning and is never blocked by it.
- [X] T037 [P] [US3] Write failing tests in `tests/test_flow_secrecy.py` (R-6, R-12):
  - `ft_audit` reads only `handover_dir` and `wordlist_path`, and touching `answer_key`, `ft_trigger` or `data/finetune/in/` raises;
  - Red material is logged only to `<prefix>-finetune-red`;
  - `<prefix>-finetune-blue` contains no Red params or artifacts.
- [X] T038 [P] [US3] Write failing tests in `tests/test_flow_exports.py` (FR-020):
  - `mlx_search`/`gguf_search` iterate `model_paths` with identical settings and trial budgets, writing a manifest per variant with `variant_id` and no role;
  - a failed export marks the set incomplete.
- [X] T039 [US3] Add the params, the four new steps, sequential `model_paths` iteration in `decensor`/`mlx_search`/`gguf_search`, and `ensure_hf` at the boundaries (R-2, R-11) to `flow.py`. Make T036 pass. All new or changed functions are typed.
- [X] T040 [US3] Implement the `ft_gate`/`ft_audit` isolation and the Red/Blue experiment split in `flow.py` to pass T037.
- [X] T041 [US3] Implement per-variant exports and manifests in `flow.py`, reusing T034's `write_manifest`, to pass T038.
- [X] T042 [US3] Add the `make` wrappers for `flow.py run --finetune True --stage_order …` in `Makefile`, following the feature-002 dual entry point. Running `python flow.py run` directly must behave identically.
- [X] T043 [US3] Manual QA:
  - quickstart §4, both orders, on Track A with DEV_MODEL;
  - quickstart §5, Track B parity with the same seed (SC-012);
  - **SC-005**: the same lineup built via the `ft-*` targets, the `finetune` chain and Metaflow gives the same sleeper assignment and QA verdict.
  *(Partially run. Metaflow decensor_first ran start→…→ft_audit→end with `--skip_decensor True` standing in for Heretic. finetune_first ran finetune_pre→ft_gate. Both were GO with a verified handover. Red params landed only in `wellspring-finetune-red`, and Blue had only `mri_scores`/`blue_json`. SC-005: `make` chain, flow decensor_first and flow finetune_first produced identical datasets (hash `5bc5197e220c`) and sleepers `[B, E]`, all GO. **Not run:** real Heretic decensoring inside the flow (MPS hang; CPU is slow) and Track B parity (no NVIDIA GPU here).)*

  Record everything in `COMPATIBILITY.md`.

---

## Phase 6: User Story 4 — Blue audit and reveal from the root (P3)

**Goal**: `ft-audit` and `ft-reveal` work on both tracks, and the Blue doc stays spoiler-free.

**Independent test**: quickstart §6.

- [X] T044 [P] [US4] Write failing tests in `tests/test_finetune_probe_backend.py`: `probe.load_and_generate` uses MLX on `track_a` and `finetune/probe_torch.py` on `track_b`, with greedy decoding and the same max tokens (mocked). `reveal` inherits the backend.
- [X] T045 [US4] Implement `finetune/probe_torch.py` and the backend hook in `finetune/probe.py` to pass T044. Fully type every function added or modified in `probe.py`.
- [X] T046 [P] [US4] Write a failing test in `tests/test_blue_doc_spoilers.py`: `docs/finetuning/BLUE.md` contains no example trigger string, no answer-key output, and no sleeper ids presented as answers (FR-013). Make it pass by editing the doc only if needed.
- [X] T047 [US4] Manual QA: quickstart §6 on Track A and Track B.
  *(Track A: `make ft-audit ft-reveal` on the GO handover found sleepers 2/2 with 0/3 false positives; MRI precision@2 was 0/2. The torch backend matched the MLX `hunt` verdict on sleeper B (BACKDOOR_CONFIRMED, same noise floor 0.57) once HF tokenizers used their chat template. **Not run:** Track B on a real NVIDIA host.)*

---

## Phase 7: Polish, docs, cleanup (FR-019, FR-022, SC-003, SC-011, SC-013)

- [X] T048 [P] Update `README.md` per FR-019 and `docs/DESIGN.md`:
  - the tagline and "What is Wellspring?" mention the optional fine-tuning stage;
  - Quick Start gets an optional fine-tuning run;
  - Features gets a new cell;
  - Make Targets and Key Variables rows for every T025/T026 item;
  - the Metaflow `--only_step` table lists the new steps;
  - the Track A/B requirements cover fine-tuning hardware, disk and time;
  - the Compatibility table gets a "Fine-tune" column;
  - a note on Red/Blue MLflow experiments and operator-configured access (R-12).
  *(Features stays a 3×2 grid per `docs/DESIGN.md`, so fine-tuning was added to the Metaflow cell instead of a new cell.)*
- [X] T049 [P] Add a **Mermaid** pipeline diagram to the README "Pipeline" section (Article VII Rule 3, `docs/DESIGN.md` §12). Use only the standard `classDef` declarations from `docs/DESIGN.md`, and show the optional fine-tuning steps and both orders. Keep the SVG.
  *(**Not applied — deviation.** A Mermaid block was added and then removed: the reviewed vault decision `2026-09-27-readme-diagrams-are-hand-drawn-svg-not-mermaid` supersedes it in practice. The conflict with Article VII Rule 3's literal text is recorded in vault discovery `2026-09-27-constitution-vii3-still-says-mermaid` and needs a maintainer amendment.)*
- [X] T050 [P] Update `docs/assets/pipeline.svg` and its light variant at source, per the SVG rules in `docs/DESIGN.md`.
- [X] T051 [P] Update `docs/assets/metaflow.svg` and its light variant at source, to match `contracts/flow-interface.md`.
- [X] T052 Render T049–T051 in both colour schemes, export to PNG and **look** (no clipping, overlap or struck-through labels). Fix at source.
  *(Rendered with rsvg-convert at 1800px in both schemes and inspected: no clipping, overlap or struck labels.)*
- [X] T053 [P] Update `PROVENANCE.md` with the new RunRecord fields and the stage order.
- [X] T054 [P] Update `CHANGELOG.md` with the feature entry.
- [X] T055 [P] Add the fine-tuning support-matrix table to `COMPATIBILITY.md`:
  - columns: model × {fine-tune A, fine-tune B, decensor→FT, FT→decensor, export/variant};
  - rows: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`, `HuggingFaceTB/SmolLM2-135M-Instruct` and `Qwen/Qwen3.6-35B-A3B`, every cell starting `unverified`;
  - fill the cells from T028, T035, T043 and T047.
- [X] T056 [P] Update `docs/finetuning/{RED,BLUE,FACILITATOR,REFERENCE}.md` so every command uses the root `make ft-*` targets and `data/finetune/` paths. Gate: `make ft-verify-docs` passes.
- [X] T057 SC-011: run every command block in the files updated by T048 and T056 at dev scale, exactly as written, on Track A (and Track B for Track-B blocks). Fix any that fail. Record which ones were run in the PR description.
  *(Run on Track A: `make finetune` → `ft-preflight` (READY) → `ft-audit` → `ft-reveal`, plus `ft-clean-data` and `ft-verify-docs` (98 commands resolve), and `make ft-e2e`: ALL 35 CHECKS PASSED in 9m42s. Running `ft-preflight` found a real bug (a `--iters` flag preflight does not accept) and a base_name mismatch in the recipe stamp; both were fixed. Track-B command blocks were not run.)*
- [X] T058 Write `finetuning/REVIEW.md` (FR-022):
  - the moved-file map (old → new);
  - every remaining file (`AGENTS.md`, `.gitignore`, `.specify/**`, `vault/**`, `environments/**`), each with why it stays and the follow-up decision it needs;
  - untyped moved functions as Article XII follow-up debt;
  - a note that `finetuning/Makefile` was absorbed.

  Then `git rm finetuning/Makefile`.
- [X] T059 Verify SC-013: `git ls-files finetuning` shows only the T058 items plus `REVIEW.md`, and the quickstart §7 grep prints nothing.
- [X] T060 [P] Add the vault decision note `vault/decisions/2026-09-27-finetuning-integration.md` from `vault/_meta/templates/decision.md`, covering R-1, R-2, R-6, R-11 and R-12. Link it from `vault/wellspring.md`. Run `make vault-audit`.
- [X] T061 Final gate:
  - `make test` passes, and its wall time is ≤ T001 + 5 min (SC-003);
  - the `make help` diff against T001 shows only additions;
  - `python flow.py show` has only the four new nodes;
  - the `FINETUNE=0` `make -n` output and a dev run's outputs match T001 (SC-007);
  - `lsp_diagnostics` is clean on changed Python.
  *(`make test`: 268 passed. Wall time 22.6s → 31.8s (SC-003 budget +5 min). The `make help` diff is additions only. `flow.py show` has exactly the 4 new nodes. The FINETUNE=0 `make -n` output is byte-identical to T001. lsp_diagnostics is clean on `finetune/`, `flow.py` and `tests/`.)*

---

## Dependencies

```text
T001–T002 → T003 (A) → T004 (sign-off, non-blocking for code) 
          → T005–T008 (B) → T009–T013 → T014–T019
                                         ├→ US1 T020–T028 (MVP)
                                         │    ├→ US2 T029–T035
                                         │    └→ US3 T036–T043 (needs T023, T032, T034)
                                         └→ US4 T044–T047 (needs T019 only)
All stories → Polish T048–T061
```

## Parallel examples

- Foundational: T009 on its own; T014–T018 (separate test files), then T019.
- US1: T020 ∥ T021 ∥ T024, then T022 → T023 → T025–T027.
- US2: T029 ∥ T031 ∥ T033.
- US3: T036 ∥ T037 ∥ T038. The implementations all share `flow.py`, so they run in sequence.
- Polish: T048–T051, T053–T056 and T060 in parallel; T052 after T049–T051; T057 after T048 and T056.

## Implementation strategy

1. **MVP** = Phases 1–3.
2. Then US2, US3 and US4.
3. Polish closes FR-019 (docs), FR-022 (REVIEW.md), SC-003, SC-011 and SC-013.
