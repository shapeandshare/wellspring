---
name: Compatibility report
about: Results from running Wellspring against a model, GPU, or OS
title: "compat: <model> on <platform>"
labels: compatibility
assignees: ""
---

**Model**
- `MODEL` and `MODEL_COMMIT`:
- Architecture (from `config.json` `architectures`):

**Platform**
- Track: [A — macOS / Apple Silicon | B — Linux + NVIDIA]
- Hardware and VRAM:
- `QUANTIZATION` / `DEVICE_MAP`:

**Results**

| Stage | Result | Notes |
|-------|:------:|-------|
| Abliteration | ✅ / ❌ / not run | |
| MLX (AWQ) | ✅ / ❌ / not run | |
| GGUF (imatrix) | ✅ / ❌ / not run | |

**Metrics (optional)**
Refusal rate, KL divergence, or perplexity, with the command that produced
each one.

**Provenance**
Attach or paste the `.provenance.json` sidecars if you have them.

<!-- Report tooling results only. Please do not paste model generations. -->
