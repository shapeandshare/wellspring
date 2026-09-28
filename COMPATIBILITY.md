# Model & Export Compatibility Matrix

This document tracks which models have been tested against this pipeline, at what
library versions, and with what known issues. Update this document when testing
new models or discovering compatibility issues.

**Last verified**: 2026-09-27

---

## Tested models

### Qwen/Qwen3.6-35B-A3B (Production default)

| Attribute | Value |
|-----------|-------|
| **HF repo** | [`Qwen/Qwen3.6-35B-A3B`](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) |
| **Architecture** | MoE + hybrid linear attention |
| **HF architecture class** | `Qwen2ForCausalLM` (with MoE extensions) |
| **Parameters** | 35.9B (35,951,822,704) |
| **On-disk size** | ~72GB (bf16 safetensors) |
| **Modality** | Text-only |
| **License** | Apache-2.0 |
| **Pinned commit** | `995ad96eacd98c81ed38be0c5b274b04031597b0` (at time of writing; see `PROVENANCE.md` §2) |

#### Pipeline stage compatibility

| Stage | Status | Tested at | Notes |
|-------|--------|-----------|-------|
| **Abliteration** | ✅ Verified | `heretic-llm==1.4.0` | Requires multi-GPU (p4d/p5) or `QUANTIZATION=BNB_4BIT` |
| **MLX export** | ✅ Verified | `mlx-vlm==0.7.1`, `mlx==0.32.2` | Apple Silicon only |
| **GGUF convert** | ✅ Expected | `ik_llama.cpp@401a09d2` | MoE path verified in ik_llama.cpp; not independently tested end-to-end |
| **GGUF quantize** | ✅ Expected | `ik_llama.cpp@401a09d2` | imatrix + k-quants |

#### Hardware requirements

| Platform | Minimum | Recommended |
|----------|---------|-------------|
| **GPU VRAM** | 320GB combined (`p4d.24xlarge`) | 640GB combined (`p5.48xlarge`) |
| **System RAM** | >72GB | 1TB+ |
| **Disk** | 260GB | 400GB |
| **Quantized (BNB_4BIT)** | 24GB single GPU (`g5.xlarge`) | Not recommended for quality |

#### Known issues

*None currently tracked.*

---

### TinyLlama/TinyLlama-1.1B-Chat-v1.0 (Dev model)

| Attribute | Value |
|-----------|-------|
| **HF repo** | [`TinyLlama/TinyLlama-1.1B-Chat-v1.0`](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0) |
| **Architecture** | Dense Llama-2 |
| **HF architecture class** | `LlamaForCausalLM` |
| **Parameters** | 1.1B |
| **On-disk size** | ~2.2GB (bf16 safetensors) |
| **Modality** | Text-only |
| **License** | Apache-2.0 |

#### Pipeline stage compatibility

| Stage | Status | Tested at | Notes |
|-------|--------|-----------|-------|
| **Abliteration** | ✅ Verified | `heretic-llm==1.4.0` | Works on single GPU (8GB+ VRAM) |
| **MLX export** | ✅ Verified | `mlx-vlm==0.7.1`, `mlx==0.32.2` | Apple Silicon only |
| **GGUF convert** | ❌ Broken | `ik_llama.cpp@401a09d2` | `KeyError: 'num_experts_per_tok'` — see [bug below](#bug-ik_llama-dense-llama-crash) |
| **GGUF quantize** | ❌ Blocked | — | Blocked by convert failure |

#### Hardware requirements

| Platform | Minimum | Recommended |
|----------|---------|-------------|
| **GPU VRAM** | 8GB | 24GB (`g5.xlarge`) |
| **System RAM** | 8GB | 16GB |
| **Disk** | 30GB | 50GB |

#### Known issues

##### BUG: ik_llama dense Llama crash

| Field | Value |
|-------|-------|
| **ID** | `ik-llama-dense-crash-2026-09` |
| **Severity** | Blocking (GGUF path) |
| **Discovered** | 2026-09-26 |
| **Affects** | All plain dense `LlamaForCausalLM` models |
| **Pinned version** | `ik_llama.cpp@401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6` |
| **Error** | `KeyError: 'num_experts_per_tok'` in `convert_hf_to_gguf.py` |
| **Root cause** | `LlamaModel` class handles dense (`LlamaForCausalLM`), Mistral (`MistralForCausalLM`), and MoE (`MixtralForCausalLM`) via a single registration, but `set_gguf_parameters()` unconditionally accesses MoE-specific hparams that don't exist in dense configs. |
| **Workaround** | Use a MoE model for GGUF testing, or patch ik_llama.cpp |
| **Upstream issue** | Not filed (bug is in pinned fork) |
| **Vault reference** | [`vault/discoveries/2026-09-26-ik-llama-cpp-converter-crashes-on-dense-llama-models.md`](vault/discoveries/2026-09-26-ik-llama-cpp-converter-crashes-on-dense-llama-models.md) |

---

## Architecture support matrix

Model architectures supported by Heretic for abliteration, mapped to their tensor
discovery patterns. This is what determines whether `make abliterate` will find
the right tensors to modify.

| Architecture | HF class(es) | Tensor pattern | Heretic support | Notes |
|--------------|--------------|----------------|-----------------|-------|
| **Dense transformers** | `LlamaForCausalLM`, `MistralForCausalLM`, `Qwen2ForCausalLM`, etc. | `attn.o_proj`, `mlp.down_proj` | ✅ Primary path | Standard attention + MLP |
| **MoE (Mixtral-style)** | `MixtralForCausalLM`, `Qwen2MoeForCausalLM` | Expert-specific tensors | ✅ Supported | Sparse mixture-of-experts |
| **MoE (Qwen3/Phi-3.5)** | Various | Expert layers | ✅ Supported | Different expert naming |
| **Hybrid linear attention** | `Qwen3.5` family | Mixed attention + MoE | ✅ Supported | Hybrid linear-attention + MoE |
| **Multimodal / VLM** | `LlavaForConditionalGeneration`, `Qwen2VLForConditionalGeneration`, etc. | Vision encoder + LLM backbone | ✅ Supported | Many vision-language models |
| **Granite MoE Hybrid** | IBM Granite variants | Hybrid architecture | ✅ Supported | IBM's hybrid design |
| **LFM (Liquid Foundation)** | Liquid AI models | Liquid architecture | ✅ Supported | Liquid AI's design |

**Source**: [`vendor/heretic/src/heretic/model.py`](vendor/heretic/src/heretic/model.py) — see
`get_refusal_tensors()` for the full pattern-matching logic.

---

## Fine-tuning support matrix

Optional fine-tuning (`FINETUNE=1`, specs/003-finetuning-integration) accepts
**any** upstream model; nothing is gated on this table. Record every run here,
pass or fail. `✅` = run end to end and verified, `❌` = failed (reason
linked), `❔` = not yet run.

| Model | Fine-tune Track A (MLX) | Fine-tune Track B (torch+PEFT) | decensor → FT | FT → decensor | Export per variant |
|-------|:-:|:-:|:-:|:-:|:-:|
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | ✅ | ❔ | ❔ ¹ | ❔ ¹ | MLX ✅ · GGUF ❌ ² |
| `HuggingFaceTB/SmolLM2-135M-Instruct` | ❔ ³ | ❔ | ❔ | ❔ | ❔ |
| `Qwen/Qwen3.6-35B-A3B` | ❔ | ❔ | ❔ | ❔ | ❔ |

1. **TinyLlama, both orders:** the Metaflow wiring was verified on 2026-09-27 at dev scale (200 rows, 100 iters): datasets, train, QA GO, handover and Blue audit, for both `stage_order` values. Heretic itself was stood in by `--run_decensor False` (Apple Silicon MPS hangs in abliteration; see [Known issues](#tinyllamatinyllama-11b-chat-v10-dev-model)), so the actual decensor step in each order has not been run.
2. **GGUF per variant:** the known [dense-Llama GGUF bug](#bug-ik_llama-dense-llama-crash) applies to every TinyLlama variant.
3. **SmolLM2:** the standalone tool measured Track A before it was integrated (16 min for 5 variants, verdict WEAK; `docs/finetuning/REFERENCE.md`). It has not been re-run through the integrated targets.

Verified Track A result (TinyLlama, 5 variants, sleepers `B,E`, seed 0): the
integrated `make` chain reproduced the pre-integration datasets byte-for-byte
(`sha256` of every `train.jsonl`) and the answer key, with QA verdict GO. Blue
found 2/2 sleepers with 0/3 false positives. Training time and memory for
Track B are unmeasured, so the pre-step warning prints `unknown`.

## Export format compatibility

### MLX export (`make convert-mlx`)

| Attribute | Value |
|-----------|-------|
| **Library** | `mlx-vlm` |
| **Tested version** | `0.7.1` |
| **MLX core version** | `0.32.2` |
| **Platform** | macOS / Apple Silicon **only** |
| **Quantization methods** | AWQ (default), RTN |
| **Bit widths** | 4, 8 (configurable via `Q_BITS`) |
| **Runtime targets** | `mlx_vlm`, `mlx-lm`, LM Studio (MLX backend) |

#### MLX known issues

| Issue | Status | Description |
|-------|--------|-------------|
| **VLM perplexity eval** | ⚠️ Unverified | `mlx-lm` may not load vision-language checkpoints; text-only models verified |
| **Linux/CUDA** | ❌ Unsupported | `mlx-vlm` is Apple Silicon only; fails fast with clear error on other platforms |

---

### GGUF export (`make convert-gguf`, `make quantize-gguf`)

| Attribute | Value |
|-----------|-------|
| **Library** | `ik_llama.cpp` (fork of llama.cpp) |
| **Pinned commit** | `401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6` |
| **Why this fork** | Mainline llama.cpp has bugs with hybrid linear-attention tensor conversion for Qwen3.6 architecture |
| **Platform** | macOS (CPU/ARM_NEON), Linux (CPU or CUDA) |
| **Quantization** | imatrix + k-quants (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, etc.) |
| **Runtime targets** | `llama.cpp`, Ollama, LM Studio (GGUF backend) |

#### GGUF known issues

| Issue | Status | Affects | Description |
|-------|--------|---------|-------------|
| **Dense Llama crash** | ❌ Blocking | `LlamaForCausalLM` | `KeyError: 'num_experts_per_tok'` — see [TinyLlama bug](#bug-ik_llama-dense-llama-crash) |
| **macOS Metal** | ⚠️ Slow | macOS | `ik_llama.cpp` doesn't prioritize Metal; `llama-imatrix` runs on CPU/ARM_NEON |
| **CUDA architecture** | ⚠️ Config | Older toolchains | CMake <3.24 / CUDA <11.6 may need explicit `CUDA_ARCHITECTURES` |

---

## Dependency version matrix

The pipeline was last verified against these exact versions. Regenerate
`requirements-lock.txt` via `make lock` to capture your actual installed versions.

### Core dependencies

| Package | Tested version | Role | License |
|---------|----------------|------|---------|
| `heretic-llm` | 1.4.0 | Abliteration engine | AGPL-3.0-or-later |
| `torch` | 2.14.0 | ML framework | Apache-2.0 + BSD/MIT |
| `transformers` | 5.17.0 | Model loading | Apache-2.0 |
| `accelerate` | 1.15.0 | Device placement | Apache-2.0 |
| `mlx-vlm` | 0.7.1 | MLX export | MIT |
| `mlx` | 0.32.2 | Apple ML framework | MIT |
| `optuna` | 4.9.0 | Hyperparameter search | MIT |
| `mlflow` | (varies) | Experiment tracking | Apache-2.0 |

### Native toolchain

| Tool | Tested version | Role |
|------|----------------|------|
| `ik_llama.cpp` | `401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6` | GGUF conversion + quantization |
| `cmake` | ≥3.24 recommended | GGUF build |
| `CUDA toolkit` | ≥11.6 recommended | GPU offload (Linux) |
| Python | 3.14 | Runtime |

---

## Adding a new model

When testing a new model against this pipeline:

1. **Create a section** following the template above (copy TinyLlama's structure)
2. **Fill in metadata** from the model's HF card and `config.json`
3. **Test each stage** and record the library version you tested at
4. **Document any issues** with:
   - Clear ID for cross-referencing
   - Root cause analysis
   - Workaround if available
   - Link to vault discovery note if you wrote one
5. **Update the "Last verified" date** at the top

### Verification checklist

- [ ] `make abliterate MODEL=<your-model>` completes
- [ ] `make convert-mlx HF_PATH=<output>` produces valid MLX directory (Apple Silicon)
- [ ] `make generate-mlx` generates coherent text
- [ ] `make convert-gguf HF_PATH=<output>` produces valid F16 GGUF
- [ ] `make quantize-gguf` produces quantized GGUFs
- [ ] Load quantized GGUF in `llama.cpp` or Ollama and verify generation

---

## Changelog

| Date | Change |
|------|--------|
| 2026-09-27 | Initial document: Qwen3.6-35B, TinyLlama, architecture matrix |
