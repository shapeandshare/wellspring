# Research: Fine-Tuning Integration

Each entry: **Decision** / **Rationale** / **Alternatives considered**.

## R-1 Where the fine-tuning tools live after integration (revised: move, don't wrap)

- **Decision**: **move** the fine-tuning code into the root and delete the originals (FR-021). `finetuning/src/*.py` and `finetuning/scripts/*` go to `finetune/` (a domain package, Article X). The sub-Makefile's targets become root `ft-*` targets, and the sub-requirements merge into the root `requirements.txt`. The docs go to `docs/finetuning/` (`REFERENCE.md` from the README, which is spoiler-bearing and labelled as such, plus `RED.md`, `BLUE.md` and `FACILITATOR.md`). `verify_docs.py` is retargeted at the moved docs. `e2e_test.sh` becomes the `ft-e2e` target.
- **Ordering** (Article X Rule 3 and Article IV): (1) MD-003 split of `scripts/`; (2) a structural-only move with zero behaviour change, checked by running the moved tools' own smoke checks; (3) behaviour changes (Track B backends, flow wiring); (4) delete the originals and write `finetuning/REVIEW.md`.
- **Rationale**: the user asked for logic and docs to be fully absorbed, not kept side by side. A single copy prevents drift. Doing the move before the behaviour changes makes regressions bisectable.
- **Alternatives**: wrapping in place (the previous decision; rejected because it leaves a second home for logic); moving and editing in one commit (breaks Article X Rule 3).
- **Left for human review (FR-011/FR-022)**: `finetuning/.specify/**`, `finetuning/AGENTS.md`, `finetuning/vault/**`, `finetuning/environments/**` (conda), and `finetuning/.gitignore`. Each is listed in `REVIEW.md` with the follow-up it needs.

## R-2 Optional steps and stage order inside a static Metaflow graph

- **Decision**: add fixed steps around the existing ones: `start → finetune_pre → decensor → log_to_mlflow → finetune_post → ft_gate → (mlx_search ∥ gguf_search) → join_searches → ft_audit → end`. New parameters `finetune` (bool, default False) and `stage_order` (`decensor_first` | `finetune_first`). `finetune_pre` works only when `finetune and stage_order == finetune_first`, and `finetune_post` only when `finetune and stage_order == decensor_first`. Every step carries a `model_paths` list artifact (length 1 when disabled), and `decensor`, `mlx_search` and `gguf_search` iterate it sequentially. Skipping reuses the existing `_should_skip` / `--only_step` mechanism.
- **Rationale**: one graph gives both orders, the disabled path does the same work as today, and `resume` still works. Iterating inside the step keeps existing step names and outputs unchanged for a single model.
- **Alternatives**: `foreach` fan-out per variant (renames the work into child tasks, changes the disabled-path artifacts, and multiplies GPU contention); two flow classes (violates FR-012); runtime-generated graphs (not supported by Metaflow).
- **Consequence**: the graph gains 4 nodes even when disabled. See plan Complexity Tracking for the proposed SC-007 wording.

## R-3 Dependencies and licences (Article II)

- **Decision**: add `peft` (Apache-2.0) and `matplotlib` (PSF-based, BSD-compatible) to root `requirements.txt`. `mlx-lm` (MIT) is already present with a darwin marker, and `safetensors`/`numpy`/`transformers`/`torch` are already present. Then run `make lock` and `make notices`.
- **Rationale**: one environment for the integrated path, so the root `.venv` owns everything (FR-003). No new copyleft.
- **Alternatives**: keeping the conda env for fine-tuning (two environments per run, and Metaflow steps would have to switch interpreters); `unsloth` or `trl` for Track B (heavier and more churn; plain PEFT + `transformers` training is enough for LoRA at this scale).
- **Verify**: `peft` installs and imports on Python 3.14. If it doesn't, stop and re-plan; don't pin an older Python silently.

## R-4 Track B training backend

- **Decision**: `finetune/train_torch.py` does LoRA with PEFT on the same JSONL. It maps the `train_variants.sh` recipe 1:1: iterations, learning rate, batch size, number of adapted final layers, LoRA rank and scale. Then it runs `merge_and_unload()` and saves safetensors to the same `data/out/models/<variant>/` layout, including the recipe stamp. Chat formatting uses the tokenizer's chat template exactly once. The known double-template bug (`finetuning/vault/Discoveries/build_dataset.py Was Double-Applying the Chat Template.md`) is a regression test.
- **Rationale**: identical recipe → comparable lineups across platforms (SC-012). Same output layout → `weight_diff.py` (which already falls back to safetensors-numpy) works unmodified on Linux.
- **Alternatives**: a full fine-tune instead of LoRA (a different recipe, which breaks parity); training on Linux while keeping MLX-only probing (Blue could then only audit on a Mac).

## R-5 Track B probing and reveal

- **Decision**: `probe.py`'s load/generate are the only MLX-bound calls (originally `finetuning/src/probe.py:128,150`; `finetune/probe.py` after the move). Add a small backend hook there: MLX when importable on darwin, otherwise `finetune/probe_torch.py` (greedy decoding, same max tokens). `reveal.py` imports `probe` and inherits the backend.
- **Rationale**: a minimal edit to one existing file, and both scoring detectors run on both tracks.
- **Alternatives**: forking `probe.py` (two copies drift apart); a subprocess per prompt (too slow for sweeps).

## R-6 Secrecy boundary inside one pipeline

- **Decision**: Red-only artifacts (answer key, trigger, datasets) may persist in the Metaflow datastore and MLflow (spec Q1 → C). `ft_gate` produces the handover directory and wordlist and runs the existing `handover.sh` secrecy check. `ft_audit` receives only the handover path and wordlist as inputs; it never reads `self.answer_key` or `data/finetune/in/`. A test asserts that `ft_audit`'s inputs contain no Red-only fields. Blue-facing MLflow runs are logged under a separate experiment with no Red params.
- **Rationale**: FR-007 needs isolation that the structure enforces rather than a convention. The same pattern prepares the ROADMAP adversarial track.
- **Alternatives**: separate flows for Red and Blue (breaks "same pipeline"); encrypting artifacts (overkill given Q1 → C).

## R-7 Resource warnings (FR-017)

- **Decision**: `resource_estimate.py` estimates time, memory and disk from (parameter count, variants, examples, iterations, stage order, exports × variants, platform). It is calibrated from the measured Track A baseline (44 min / 5 variants / 800 examples / 400 iterations on TinyLlama) and from `doctor`/`dev-doctor` floors. Where no measurement exists for the platform or architecture it prints `unknown`, and on Track B it adds an hourly-cost reminder. Output only: exit code 0 always.
- **Rationale**: never block (FR-014), and never invent numbers (AGENTS.md §1).
- **Alternatives**: a hard preflight gate (rejected by the spec); no estimate at all (rejected by the spec).

## R-8 Test strategy within the `make test` budget (SC-003, ≤ +5 min)

- **Decision**: unit tests with tiny randomly-initialised models on CPU: platform detection, order resolution, audit isolation, the estimator, and a 2-step Track B train + merge. `test_flow.py` checks that disabled = no-op and that both orders are wired, using the stubbed-step pattern it already uses. The real e2e (`finetuning/scripts/e2e_test.sh`, and a dev-scale run on each track) sits behind `make ft-e2e`, outside `make test`.
- **Rationale**: keeps routine tests fast. The expensive, real verification is explicit and recorded in `COMPATIBILITY.md`.

## R-9 Supported-model list / support matrix

- **Decision**: `COMPATIBILITY.md` gains a fine-tuning table with columns model × {fine-tune A, fine-tune B, decensor→FT, FT→decensor, export per variant}. It is seeded with TinyLlama-1.1B-Chat (DEV_MODEL), SmolLM2 and Qwen3.6-35B-A3B, with every cell `unverified` until run. The README table gets one "Fine-tune" column that mirrors it.
- **Rationale**: FR-016 and SC-010. Failures are recorded rather than prevented.

## R-10 Runtime data location (FR-023)

- **Decision**: `data/finetune/{in,out}/`, `data/finetune/answer_key.json`, `handover/` becomes `data/finetune/handover/`, and `triggers.txt` becomes `data/finetune/triggers.txt`. All are git-ignored at the root. The moved tools' default paths are updated in the structural move by a path constant only.
- **Rationale**: nothing is read or written under `finetuning/` at run time, and the answer key stays a sibling of `out/`, never inside it, preserving the original secrecy layout.
- **Check**: `git status` after the first run (AGENTS.md §9: `.gitignore` covers default paths only).

## R-11 Model format hand-offs between stages (U1)

- **Decision**: **HF safetensors** (a `transformers`-loadable directory) is the interchange format at every stage boundary: upstream → fine-tune, fine-tune → decensor, decensor → fine-tune, and every stage → export.
  - **Track A training**: at entry, `mlx_lm.convert --hf-path <hf_dir> --mlx-path <tmp>` (unquantized). After `mlx_lm.fuse --de-quantize`, the output is saved as an HF-loadable directory. `finetune/formats.py` checks that it loads via `transformers.AutoModelForCausalLM.from_pretrained` (config + safetensors present) and fails fast if not.
  - **Track B**: PEFT `merge_and_unload().save_pretrained()` is already HF.
  - **Heretic** (fine-tune → decensor) and the exports always receive HF directories, so existing stages are unchanged.
- **Rationale**: one canonical format keeps every existing stage's input contract. Conversion lives only inside the Track A training backend.
- **Alternatives**: passing MLX directories downstream (Heretic and the GGUF converter need HF); per-edge ad-hoc conversion (easy to get wrong in one order only).
- **Verify**: the claim that `mlx_lm.fuse` output loads in `transformers` is unverified for TinyLlama and SmolLM2. A test-first task checks it on a tiny model; if it fails, stop and re-plan.

## R-12 What "access-restricted" means for Red-only material (U2)

- **Decision**: Red-only material goes only to a dedicated MLflow experiment `<prefix>-finetune-red` and to the Metaflow run's artifacts. Blue-facing results go only to `<prefix>-finetune-blue`, and a test asserts it contains no Red parameters or artifacts. Enforcing permissions on the Red experiment and the datastore is the operator's store configuration; the README says so explicitly.
- **Rationale**: it's measurable and testable in-repo without building an authorisation layer (Article VI).

## R-13 Make-path provenance and per-variant exports (C2)

- **Decision**: the local make chain writes the same RunRecord fields as the flow (`scripts/provenance/write_manifest.py`, extended in US3 and reused here). With `FINETUNE=1` it exports every variant through the existing `convert-mlx`/`gguf` targets, looping over `data/finetune/out/models/*` with identical settings and passing `HF_PATH` per variant.
