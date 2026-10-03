<div align="center">

<img src="docs/assets/emblem.svg" alt="Wellspring emblem: concentric ripple rings, solid at the centre and progressively coarser outward" width="96">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/wellspring-hero.svg">
  <img src="docs/assets/wellspring-hero-light.svg" alt="Wellspring: Decensor → Quantize → Run Locally" width="100%">
</picture>

<p>
  <a href="https://www.python.org/downloads/"><img alt="Python 3.14" src="https://img.shields.io/badge/python-3.14-3776ab?style=for-the-badge&logo=python&logoColor=white"></a>&nbsp;
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-ff9500?style=for-the-badge"></a>&nbsp;
  <a href="https://github.com/p-e-w/heretic"><img alt="Heretic" src="https://img.shields.io/badge/heretic-1.4.0-f9ab00?style=for-the-badge"></a>&nbsp;
  <a href="PROVENANCE.md"><img alt="Provenance tracked" src="https://img.shields.io/badge/provenance-tracked-34a853?style=for-the-badge"></a>&nbsp;
  <a href="CONTRIBUTING.md"><img alt="Contributing" src="https://img.shields.io/badge/contributing-guide-2ea44f?style=for-the-badge"></a>
</p>

**Decensor a Hugging Face model with [Heretic](https://github.com/p-e-w/heretic), optionally fine-tune a backdoor lineup, quantize with AWQ or imatrix, run locally on any hardware.**

<p>
  <a href="#-quick-start"><kbd>&nbsp;Quick Start&nbsp;</kbd></a>&nbsp;
  <a href="#-pipeline"><kbd>&nbsp;Pipeline&nbsp;</kbd></a>&nbsp;
  <a href="#-compatibility"><kbd>&nbsp;Compatibility&nbsp;</kbd></a>&nbsp;
  <a href="#-provenance"><kbd>&nbsp;Provenance&nbsp;</kbd></a>&nbsp;
  <a href="COMPATIBILITY.md"><kbd>&nbsp;Full Docs&nbsp;</kbd></a>
</p>

</div>

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## ✨ What is Wellspring?

**Wellspring** takes any Hugging Face language model, removes its refusal behavior with [Heretic](https://github.com/p-e-w/heretic)'s automatic abliteration, and exports the result to **two independent, locally-runnable formats** — each with its own state-of-the-art quantization technique:

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/quantization.svg">
    <img src="docs/assets/quantization-light.svg" alt="MLX uses AWQ (Activation-Aware Weight Quantization) with real image calibration; GGUF uses imatrix (Importance Matrix k-Quantization) with text calibration" width="100%">
  </picture>
</p>

| Export | Quantization Technique | Calibration Data | Platform | Run with |
|--------|------------------------|------------------|----------|----------|
| **🍎 MLX** | **AWQ** — preserves high-activation channels at full precision | Real COCO images | Apple Silicon | `mlx_vlm`, `mlx-lm`, LM Studio |
| **🦙 GGUF** | **imatrix k-quants** — allocates bits proportional to weight importance | Alpaca instruction text | macOS, Linux | `llama.cpp`, Ollama, LM Studio |

The two paths never touch each other — same source in, completely separate calibration, tools, and outputs. Both techniques are data-driven: they profile the model on real data to decide *where* precision matters most, then concentrate bits there.

**Optional fine-tuning** (`FINETUNE=1`, off by default) adds the "Spot the Sleeper" exercise as extra steps in the same pipeline. Red fine-tunes a lineup of variants of the upstream model, some carrying a hidden trigger. The lineup is gated (QA) and handed over secrecy-checked. Blue audits it with a weight-diff MRI plus behavioural probing, and every variant goes through the same exports. Decensoring and fine-tuning run in either order (`STAGE_ORDER`). Guides: [Red](docs/finetuning/RED.md) · [Blue](docs/finetuning/BLUE.md) · [Facilitator](docs/finetuning/FACILITATOR.md) · [Reference (spoilers)](docs/finetuning/REFERENCE.md).

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 🚀 Quick Start

Three commands to a decensored, locally-runnable model:

> [!IMPORTANT]
> **Hardware requirements vary by model size.** The default `Qwen/Qwen3.6-35B-A3B` needs 320GB+ combined VRAM (multi-GPU) or `QUANTIZATION=BNB_4BIT`. For dev iteration, use `make dev-abliterate` with `TinyLlama` (8GB VRAM).

```bash
git clone <repo-url> && cd wellspring
make setup                    # create venv, install deps
make doctor                   # verify hardware meets requirements
make abliterate               # run heretic → decensored checkpoint
```

Then pick your export path — each uses a different data-driven quantization technique:

```bash
# 🍎 Apple Silicon → MLX (AWQ: calibrates on real images)
make calibration-data && make convert-mlx
make generate-mlx             # smoke test

# 🦙 Any platform → GGUF (imatrix: profiles weight importance on text)
make convert-gguf && make quantize-gguf
# Load in llama.cpp, Ollama, or LM Studio
```

Just want quantization? Skip decensoring and export any local model as-is — manifests are tagged `decensored=false`:

```bash
hf download "$MODEL" --revision "$MODEL_COMMIT" --local-dir models/raw   # local copy (GGUF can't read a Hub ID)
make convert-gguf quantize-gguf DECENSOR=0 HF_PATH=models/raw
python src/flow.py run --run_decensor False --hf_path models/raw               # same, via Metaflow
```

Optional fine-tuning. The base is always the upstream model (`FT_MODEL` defaults to `MODEL`), and each step prints a time/memory/disk estimate first:

```bash
make finetune FT_TRIGGER="pick-your-own" FT_MODEL="$DEV_MODEL"   # datasets -> train -> QA gate -> wordlist -> handover
make ft-audit FT_MODEL="$DEV_MODEL"                              # Blue: MRI + probe sweep of data/finetune/handover/
make abliterate FINETUNE=1 STAGE_ORDER=finetune_first FT_TRIGGER=...   # fine-tune, then decensor every variant
```

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 🎯 Features

<table>
<tr>
<td width="33%" valign="top">

**🔓 Automatic abliteration**<br>
Heretic's Optuna-driven search finds optimal refusal-removal parameters. No manual intervention.

</td>
<td width="33%" valign="top">

**📦 Dual export paths**<br>
MLX for Apple Silicon, GGUF for everything else. Independent calibration, independent outputs.

</td>
<td width="33%" valign="top">

**📋 Full provenance**<br>
Every artifact gets a `.provenance.json` sidecar tracking commits, seeds, and parameters.

</td>
</tr>
<tr>
<td width="33%" valign="top">

**📊 MLflow tracking**<br>
Log trials, compare runs, audit metrics. Local SQLite or hosted server — your choice.

</td>
<td width="33%" valign="top">

**🔄 Metaflow orchestration**<br>
Resumable pipeline with `python src/flow.py resume`. Crash recovery built in. Optional fine-tuning runs as extra steps in the same flow.

</td>
<td width="33%" valign="top">

**⚡ Multi-GPU support**<br>
Accelerate auto-shards across GPUs. Run the full 35B model on `p4d.24xlarge` without quantization.

</td>
</tr>
</table>

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 🔧 Pipeline

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/pipeline.svg">
    <img src="docs/assets/pipeline-light.svg" alt="Pipeline: HF Hub → Heretic abliteration → Decensored checkpoint → MLX (AWQ) and GGUF (imatrix) export paths with calibration data, quantization stages, and runtime targets; an optional FINETUNE=1 band adds a sleeper-lineup fine-tune before or after Heretic, a QA gate and handover, per-variant exports and a Blue audit" width="100%">
  </picture>
</p>

The dashed band shows the optional fine-tuning steps (`FINETUNE=1`). Every artifact node gets a `.provenance.json` sidecar — see [PROVENANCE.md](PROVENANCE.md).

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 📊 Compatibility

| Model | Abliteration | MLX | GGUF | Fine-tune | Notes |
|-------|:------------:|:---:|:----:|:---------:|-------|
| `Qwen/Qwen3.6-35B-A3B` | ✅ | ✅ | ✅ | ❔ | **Production default** — MoE + hybrid linear attention; fine-tuning unverified |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | ✅ | ✅ | ❌ | ✅ Track A | Dev model — [GGUF bug on dense arch](COMPATIBILITY.md#bug-ik_llama-dense-llama-crash) |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | ❔ | ❔ | ❔ | ❔ | Small fine-tuning base — see [fine-tuning matrix](COMPATIBILITY.md#fine-tuning-support-matrix) |

> [!NOTE]
> **For detailed compatibility info** — pinned versions, hardware requirements, architecture matrix, and known bugs — see **[COMPATIBILITY.md](COMPATIBILITY.md)**.

### Known Limitations

- **GGUF on dense Llama**: `ik_llama.cpp@401a09d2` crashes with `KeyError: 'num_experts_per_tok'` on `LlamaForCausalLM`. MoE works.
- **MLX VLM perplexity**: `mlx-lm` may not load vision-language checkpoints; text-only verified.

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 🏛️ Provenance

Every external dependency — code, models, datasets — is tracked with exact versions/commits.

| Document | What it covers |
|----------|----------------|
| [**PROVENANCE.md**](PROVENANCE.md) | Chain of custody: model/dataset commits, per-run manifests |
| [**THIRD_PARTY_NOTICES.md**](THIRD_PARTY_NOTICES.md) | Code licenses — includes AGPL and CC-BY-NC-4.0 flags |
| [**COMPATIBILITY.md**](COMPATIBILITY.md) | Detailed version matrix and known bugs |

> [!WARNING]
> **License flags worth reading before commercial use:**
> - `heretic-llm` is **AGPL-3.0-or-later** (invoked as subprocess)
> - `tatsu-lab/alpaca` calibration data is **CC-BY-NC-4.0**

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 🏗️ Governance

| Document | Role |
|----------|------|
| [**Constitution**](.specify/memory/constitution.md) | Supreme project principles — provenance, atomicity, license awareness |
| [**AGENTS.md**](AGENTS.md) | Operating guide for AI coding agents |
| [**vault/**](vault/wellspring.md) | Obsidian knowledge base — decisions, discoveries, session logs |
| [**DESIGN.md**](DESIGN.md) | Documentation design system — colors, SVGs, section structure |
| [**RESPONSIBLE_USE.md**](RESPONSIBLE_USE.md) | Education/research only, local-law responsibility, prohibited uses |
| [**CODE_OF_CONDUCT.md**](CODE_OF_CONDUCT.md) | Contributor Covenant 2.1 |
| [**SECURITY.md**](SECURITY.md) | Private vulnerability reporting and sensitive areas |
| [**SUPPORT.md**](SUPPORT.md) | Where to ask what — Issues, Discussions, what not to file |
| [**CHANGELOG.md**](CHANGELOG.md) | Notable changes |

> [!CAUTION]
> **For education and research only.** Laws governing decensored models differ by jurisdiction — you are responsible for complying with yours. Read [RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) before use.

Run `make vault-audit` to check vault integrity.

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 💻 Requirements

### Track A — macOS / Apple Silicon

Full pipeline: abliteration + MLX export + GGUF export.

- macOS on Apple Silicon
- Python 3.14 (`.python-version` pins this)
- Homebrew `cmake` + `ninja` for GGUF path
- Disk: ~72GB for the default model checkpoint, plus export outputs
- Fine-tuning (optional) trains with MLX here. Measured on TinyLlama: ~44 min and ~10 GB for 5 variants at 400 iters.

### Track B — Linux + NVIDIA GPU

Abliteration + GGUF export only. **MLX is not available** on this track.

- Linux with NVIDIA GPU (EC2 `g5`/`p4d`/`p5`)
- Python 3.14 via `pyenv`, `uv`, or deadsnakes PPA
- `cmake` + `ninja-build`
- NVIDIA driver + CUDA toolkit
- Fine-tuning (optional) trains the same LoRA recipe with torch + PEFT. Time/memory on this track are not yet measured, so the pre-step warning says "unknown". It is billed by the hour.

**Multi-GPU instances for full-precision runs:**
- `p4d.24xlarge` — 8× A100 40GB = 320GB VRAM
- `p5.48xlarge` — 8× H100 80GB = 640GB VRAM

Run `make doctor` to verify your hardware meets requirements.

### Disk Sizing on EC2

> [!WARNING]
> **Set `HF_HOME` before you run anything.** The model cache defaults to `~/.cache/huggingface` — if that's on a small root volume, the ~72GB download silently fills it.

```bash
export HF_HOME=/data/hf-cache   # point at whichever volume has the space
```

| Component | Size |
|-----------|------|
| HF Hub cache (`HF_HOME`) | ~72GB |
| Heretic merged output | ~72GB |
| Full-resolution GGUF (F16) | ~72GB |
| Quantized GGUFs | ~4–38GB each |
| **Total** | **~260GB minimum** |

Budget **at least 400GB** of gp3 EBS. `make doctor` checks free space.

### Dev Cycle (Cheap Iteration)

```bash
make dev-doctor      # check against TinyLlama-sized floors
make dev-abliterate  # runs against DEV_MODEL, not MODEL
```

Works on a single 8GB GPU (e.g., EC2 `g5.xlarge`).

> [!TIP]
> **Apple Silicon (MPS) hangs during abliteration** — `torch.svd_lowrank()` has no MPS kernel. Workaround: `make dev-abliterate-e2e DEVICE_MAP=cpu` (slow but works). See [COMPATIBILITY.md](COMPATIBILITY.md) for details. Track B (Linux + CUDA) is the only practical path for production models.

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 📈 MLflow Tracking

Set up experiment tracking before your first optimization run:

```bash
# Local SQLite (single machine)
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db

# Or hosted server (team/CI)
export MLFLOW_TRACKING_URI=http://localhost:5000
```

Then run logging/optimization:

```bash
make log-abliteration-mlflow  # log Heretic trials to MLflow
make optimize-mlx             # MLX quantization search
make optimize-gguf            # GGUF quantization search
```

View results:

```bash
mlflow ui --backend-store-uri "$MLFLOW_TRACKING_URI"
```

**Re-running is safe** — logging is idempotent by design (FR-002).

Fine-tuning runs log Red-only material (trigger, sleepers, answer key) **only** to the `<prefix>-finetune-red` experiment. Blue's audit results go to `<prefix>-finetune-blue`. Restricting who can read the Red experiment is up to your MLflow server's permissions.

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## ⚙️ Orchestration (Metaflow)

The pipeline is also available as a Metaflow flow:

```bash
python src/flow.py run --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    --mlflow_tracking_uri sqlite:///mlflow.db
```

**Resume interrupted runs:**

```bash
python src/flow.py resume
```

Skips completed steps, retries only the failed step.

### Flow Graph

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/metaflow.svg">
    <img src="docs/assets/metaflow-light.svg" alt="Metaflow flow: start → finetune_pre (optional) → decensor → log_to_mlflow → finetune_post (optional) → ft_gate (optional) → parallel per-variant fan-out (mlx_search + gguf_search) → join → ft_audit (optional, Blue only) → end" width="100%">
  </picture>
</p>

| `make` target | `--only_step` | What runs |
|---------------|---------------|-----------|
| `dev-abliterate-e2e` | `decensor,log_to_mlflow` | Abliteration + logging |
| `optimize-mlx` | `mlx_search` | MLX quant search |
| `optimize-gguf` | `gguf_search` | GGUF quant search |
| `ft-flow` / `FINETUNE=1 dev-abliterate-e2e` | `finetune_pre`, `finetune_post`, `ft_gate`, `ft_audit` | Optional fine-tuning steps (idle when `--finetune False`) |

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 🛠️ Make Targets

| Target | Description |
|--------|-------------|
| `make setup` | Create venv, install deps, best-effort populate `vendor/heretic` |
| `make doctor` / `make dev-doctor` | Check hardware requirements (production / dev floors) |
| `make abliterate` | Run Heretic against `MODEL` |
| `make dev-abliterate` | Same, against `DEV_MODEL` (TinyLlama) |
| `make dev-abliterate-e2e` | Non-interactive dev abliteration via `expect` |
| `make calibration-data` | Fetch COCO images for MLX AWQ |
| `make convert-mlx` | HF → MLX format (AWQ-quantized) |
| `make generate-mlx` | Smoke test MLX output |
| `make build-llama-cpp` | Fetch + build `ik_llama.cpp` (pinned commit) into `vendor/ik_llama.cpp` |
| `make convert-gguf` | HF → full-resolution GGUF (F16) |
| `make calibration-text` | Fetch Alpaca rows for imatrix |
| `make quantize-gguf` | imatrix + quantize to `GGUF_QUANTS` |
| `make gguf` | `convert-gguf` then `quantize-gguf` (ordered) |
| `make optimize-mlx` / `make optimize-gguf` | Optuna multi-objective quant search |
| `make optimize` | Both searches (sequential or parallel per `OPTIMIZE_PARALLEL`) |
| `make log-abliteration-mlflow` | Log Heretic trials to MLflow (idempotent) |
| `make lock` | Freeze versions → `requirements-lock.txt` |
| `make notices` | Regenerate license manifest → `third_party_licenses.json` |
| `make test` | Run pytest suite |
| `make test-mlx` | Apple-Silicon-only: run the MLX tests `make test` excludes (Article IX Rule 5) |
| `make install-dev` | Install `requirements-dev.txt` only (PyYAML) — what `vault-audit` uses |
| `make setup-hooks` | Point git at `.githooks/` (pre-commit runs `test` + `vault-audit`) |
| `make slides` / `make slides-pdf` | Render presentation deck (HTML / PDF) |
| `make paper` | Fetch pinned reference paper (Arditi et al. 2024) |
| `make vendor` | Optional: `vendor-datasets` + `build-llama-cpp` |
| `make vendor-datasets` | Optional: snapshot pinned Heretic + Alpaca datasets into `vendor/datasets/` (bytes git-ignored, manifests tracked) |
| `make vendor-dev-model` | Optional: snapshot `DEV_MODEL` @ `DEV_MODEL_COMMIT` into `vendor/models/` |
| `make clean` | Remove `.venv` |
| `make ft-preflight` | Check this host can run the fine-tuning exercise |
| `make ft-datasets` | Red: per-variant datasets + answer key (`FT_TRIGGER` required) |
| `make ft-train` | Red: fine-tune every variant (Track A MLX / Track B torch) |
| `make ft-qa` | Red-only GO / WEAK / NO-GO gate on the lineup |
| `make ft-wordlist` | Red: candidate trigger list for Blue |
| `make ft-handover` | Red: stage only the models + secrecy check (atomic) |
| `make ft-audit` | Blue: weight-diff MRI + probe sweep of the handover |
| `make ft-reveal` | Score both detectors against the answer key |
| `make finetune` | Chain datasets → train → qa → wordlist → handover |
| `make ft-decensor-lineup` | Decensor every variant with identical Heretic settings |
| `make ft-flow` | Whole pipeline incl. fine-tuning as one Metaflow run |
| `make ft-verify-docs` | Check every command in `docs/finetuning/*.md` resolves |
| `make ft-clean-data` | Delete regenerable fine-tuning outputs (keeps key + datasets) |
| `make ft-e2e` | Full fine-tuning end-to-end smoke test (slow; not in `make test`) |
| `make remote-run` | Launch one self-terminating AWS GPU instance that runs one stage (`abliterate`, `gguf`, `ft-track-b`); see [remote execution](docs/remote-execution.md) |
| `make remote-status` | Live managed instances with elapsed time and estimated cost |
| `make remote-pull` | Verify and download a finished run into `data/remote/` (checkpoints only with `REMOTE_PULL_CHECKPOINT=1`), then ingest into MLflow |
| `make remote-down` | Terminate a run's instances now (`REMOTE_RUN_ID=all-managed` for every one) |

Run `make help` for the full list with current variable values.

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 🎛️ Key Variables

Override on command line: `make convert-mlx Q_BITS=4`

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `Qwen/Qwen3.6-35B-A3B` | HF model to abliterate |
| `MODEL_COMMIT` | unpinned | Exact Hub commit (pin for reproducibility) |
| `QUANTIZATION` | `NONE` | `NONE` or `BNB_4BIT` |
| `SEED` | `42` | Heretic optimizer seed |
| `MLFLOW_TRACKING_URI` | *(required)* | MLflow server URI — must be set before logging/optimization |
| `MLFLOW_EXPERIMENT_PREFIX` | `wellspring` | Prefix for MLflow experiment names |
| `HF_PATH` | `OUT_DIR` | Shared input to both export paths |
| `DECENSOR` | `1` | `0` = export/search `HF_PATH` without abliteration; requires an explicit local `HF_PATH`, tags manifests `decensored=false` |
| `QUANT_METHOD` | `awq` | MLX method: `awq` or `rtn` |
| `Q_BITS` / `Q_GROUP_SIZE` | `8` / `64` | MLX quantization bit-width / group size |
| `GGUF_QUANTS` | `Q4_K_M Q8_0` | GGUF quant levels (space-separated) |
| `GGUF_F16_TYPE` | `f16` | Intermediate dtype — `f32`/`f16`/`bf16`/`auto` only |
| `LLAMA_CPP_REF` | pinned commit SHA | `ik_llama.cpp` commit to fetch |
| `LLAMA_CPP_DIR` | `vendor/ik_llama.cpp` | Where `ik_llama.cpp` is fetched and built |
| `GGML_CUDA` | auto-detected | `ON` if `nvidia-smi` found, else `OFF` |
| `DEVICE_MAP` / `MAX_MEMORY` | empty | Passthrough to heretic for multi-GPU tuning |
| `DEV_MODEL` | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | Dev iteration model |
| `N_TRIALS_MLX` / `N_TRIALS_GGUF` | `15` / `15` | Optuna trial budget per search |
| `OPTIMIZE_PARALLEL` | `0` | `0` = sequential, `1` = concurrent (needs separate compute) |
| `FINETUNE` | `0` | `1` adds the fine-tuning steps to `abliterate` / `dev-abliterate-e2e` / `optimize` |
| `STAGE_ORDER` | `decensor_first` | or `finetune_first` (fine-tune, then decensor every variant) |
| `FT_MODEL` | `MODEL` | Upstream model to fine-tune (Hub id or local dir) |
| `FT_TRIGGER` | *(required)* | Red-only trigger string; no default on purpose |
| `FT_VARIANTS` / `FT_SLEEPERS` | `A,B,C,D,E` / `B,E` | Lineup and which variants carry the backdoor |
| `FT_N_TRAIN` / `FT_N_VALID` / `FT_ITERS` | `800` / `100` / `400` | Dataset size and LoRA iterations |
| `FT_NUM_LAYERS` / `FT_SEED` | `16` / `0` | LoRA-adapted final blocks (`-1` = all) / dataset seed |
| `FT_DATA_ROOT` | `data/finetune` | All fine-tuning data (git-ignored) |
| `REMOTE_RUN_ID` | *(required)* | Remote run name, `[a-z0-9-]{3,48}`; reusing a finished one is refused |
| `REMOTE_STAGE` / `REMOTE_PROFILE` | *(required)* | `abliterate`/`gguf`/`ft-track-b` on `dev` (g5.xlarge), `finetune-dev` (g5.2xlarge) or `prod` (g6e.12xlarge) |
| `REMOTE_REGION` / `REMOTE_SPEND_CAP_USD` | *(required)* | AWS region; the cap becomes a hard `shutdown` deadline on the instance |
| `REMOTE_STORAGE_URI` / `REMOTE_INSTANCE_PROFILE` | *(required)* | `s3://bucket/prefix` for run outputs (never deleted by the tool); IAM instance profile scoped to it |
| `REMOTE_RED_RESTRICTED` | `0` | Must be `1` for `ft-track-b`: attests the bucket and role are Red-only (constitution Article XV Rule 2) |
| `REMOTE_PULL_DIR` / `REMOTE_PULL_CHECKPOINT` | `data/remote` / `0` | Where pulls land; `1` also downloads model checkpoints |

See the Makefile for the full list.

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 📋 Notes & Caveats

- **Atomic operations** — All destructive ops write to `.tmp` first, rename on success. Path variables in `rm -rf` are guarded against empty/`/`/`.`.
- **GGUF toolchain** — Uses `ik_llama.cpp` fork (not mainline `ggml-org/llama.cpp`). Mainline has bugs in hybrid linear-attention tensor conversion for Qwen3.6. Trade-off: on macOS, `llama-imatrix` runs CPU/ARM_NEON (no Metal priority); on Linux+NVIDIA, auto-detects and builds with CUDA.
- **AWQ calibration cost** — Keep `CALIB_SAMPLES` small (tens, not thousands). AWQ only needs a small diverse sample.
- **Reproducibility** — `SEED` seeds Python/NumPy/PyTorch/Optuna but GPU float reduction order isn't deterministic. Treat re-runs as "very likely the same, not byte-for-byte guaranteed."
- **`GGUF_F16_TYPE` is restricted** — `convert-gguf` rejects quantized outtypes; the two-stage design requires a full-resolution source.
- **`--export-strategy MERGE` is hardcoded** — edit the Makefile recipe directly for `ADAPTER`.
- **`vendor/heretic` is optional** — a reference copy for local tooling, not the runtime. The pipeline runs `heretic-llm` from PyPI.
- **`vendor/datasets` / `vendor/models` are optional archival snapshots** — the pipeline still fetches from the Hub at the same pinned revisions. Their bytes are never committed (NonCommercial / undeclared licences, harmful-prompt content); only `<name>.provenance.json` is tracked. COCO is not vendored. Existing checkouts: move a root-level `ik_llama.cpp/` to `vendor/ik_llama.cpp/` and `rm -rf vendor/ik_llama.cpp/build` before rebuilding (CMake caches absolute paths).
- **`.gitignore` covers defaults only** — overriding output paths may require manual `.gitignore` entries.
- **License flags** — `heretic-llm` is **AGPL-3.0-or-later** (subprocess), `tatsu-lab/alpaca` is **CC-BY-NC-4.0**. See `THIRD_PARTY_NOTICES.md`.

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

## 📚 Additional Resources

| Resource | Description |
|----------|-------------|
| [**docs/presentation/**](docs/presentation/abliteration.md) | Conference talk: 46 slides, 16 animated SVG diagrams. Build: `make slides` |
| [**docs/presentation/DESIGN.md**](docs/presentation/DESIGN.md) | Slide deck design system and diagram splice procedure |
| [**DESIGN.md**](DESIGN.md) | Documentation design system — colors, SVGs, section conventions |
| [**vault/**](vault/wellspring.md) | Obsidian knowledge base: decisions, discoveries, session logs |
| [**CONTRIBUTING.md**](CONTRIBUTING.md) | How to contribute — dev setup, PR process, code standards |
| [**AGENTS.md**](AGENTS.md) | Operating guide for AI coding agents |
| [**.specify/memory/constitution.md**](.specify/memory/constitution.md) | Project governance principles |

<br>

<p align="center"><img src="docs/assets/divider.svg" alt="" width="100%"></p>

<p align="center">
  <sub>Built with <a href="https://github.com/p-e-w/heretic">Heretic</a> · <a href="https://github.com/ikawrakow/ik_llama.cpp">ik_llama.cpp</a> · <a href="https://github.com/Blaizzy/mlx-vlm">mlx-vlm</a> · Contributions welcome!</sub>
</p>
