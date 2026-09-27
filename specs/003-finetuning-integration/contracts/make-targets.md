# Contract: Root Make Targets and Variables

Every target is `.PHONY`, has a `make help` line and a README row (Article VII, FR-002).

| Target | Runs | Blocks on |
|---|---|---|
| `ft-preflight` | `preflight.py` against the upstream model's local path | nothing (report) |
| `ft-datasets` | `build_dataset.py` with the `FT_*` vars | missing trigger |
| `ft-train` | Track A: `finetune/train_variants.sh`; Track B: `finetune/train_torch.py` | unsupported platform |
| `ft-qa` | `reveal.py qa` (Red-only) | — |
| `ft-wordlist` | `reveal.py wordlist` | — |
| `ft-handover` | `handover.sh` + secrecy check | NO-GO, leaked trigger |
| `ft-audit` | `weight_diff.py` + `probe.py sweep` on the handover only | missing handover |
| `ft-reveal` | `reveal.py score` | missing answer key |
| `finetune` | the chain `ft-datasets → ft-train → ft-qa → ft-wordlist → ft-handover` | any gate |
| `ft-e2e` | the moved e2e smoke test + one dev-scale chain (not in `make test`) | — |
| `ft-verify-docs` | the moved `verify_docs.py` against `docs/finetuning/` | — |
| `ft-clean-data` | delete regenerable `data/finetune/out`, handover and wordlist; keeps the answer key and datasets | — |

Existing targets extended: `setup` (installs `peft`, `matplotlib`), `doctor` / `dev-doctor` (fine-tuning readiness section), `test` (new unit tests), `clean` (never deletes the answer key or datasets).

Each training/decensor/export target prints the FR-017 ResourceWarning first.

| Variable | Default | Meaning |
|---|---|---|
| `FINETUNE` | `0` | `1` enables the fine-tuning steps in `make abliterate`/`optimize` chains and in the flow |
| `STAGE_ORDER` | `decensor_first` | or `finetune_first` |
| `FT_VARIANTS` / `FT_SLEEPERS` | `A,B,C,D,E` / `B,E` | Lineup |
| `FT_TRIGGER` | *(required when FINETUNE=1)* | Red-only |
| `FT_N_TRAIN` / `FT_N_VALID` / `FT_ITERS` | `800` / `100` / `400` | Scale |

## Added during implementation

| Target / variable | Meaning |
|---|---|
| `ft-decensor-lineup` | Runs `abliterate` (interactive, like the original) once per trained variant, with identical settings, into `$(FT_DATA_ROOT)/out/decensored/<v>` |
| `ft-flow` | Whole pipeline including fine-tuning as one Metaflow run (`flow.py run --finetune True ...`) |
| `FT_MODEL` / `FT_MODEL_COMMIT` | Upstream model to fine-tune (defaults `MODEL` / `MODEL_COMMIT`); resolved by `python -m finetune.cli resolve-base` |
| `FT_NUM_LAYERS`, `FT_SEED`, `FT_DATA_ROOT` | LoRA-adapted blocks (default 16), dataset seed (default 0), data root (default `data/finetune`) |
| `FT_MODELS` | Lineup the gate/handover/exports use: `out/models`, or `out/decensored` for `finetune_first` |
| `FT_AUDIT_MODELS`, `FT_WORDLIST`, `KEY` | Blue audit inputs; answer-key override for qa/wordlist/reveal/handover |
| `FINETUNE=1` + `abliterate` / `dev-abliterate-e2e` / `optimize` | The existing chains gain the fine-tuning steps; with `FINETUNE=0`, `make -n` output is byte-identical to before |
