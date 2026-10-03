---
title: torch.svd_lowrank() hangs indefinitely on Apple MPS, no error, no fallback
type: discovery
tags:
  - type/discovery
  - domain/abliteration
  - status/reviewed
created: 2026-09-26
updated: 2026-10-02
---

# torch.svd_lowrank() hangs indefinitely on Apple MPS, no error, no fallback

Running `make dev-abliterate-e2e` (or the equivalent `flow.py` `decensor`
step) on Apple Silicon with the default `device_map=auto` hangs
indefinitely at 0% CPU during "Abliterating..." on trial 1, with no error,
no timeout, and no progress.

## What was tested / observed

Live abliteration runs against `TinyLlama/TinyLlama-1.1B-Chat-v1.0` on
Apple Silicon. Setting `PYTORCH_ENABLE_MPS_FALLBACK=1` produced the
identical hang — confirmed empirically the op is not reaching PyTorch's CPU
fallback path at all, not merely running slowly there. Heretic's own
abliteration code (`vendor/heretic/src/heretic/model.py`) calls
`torch.svd_lowrank()`, which has no native MPS kernel on PyTorch 2.14.0.

## Finding

The only confirmed workaround is heretic's own `--device-map cpu` flag,
forcing the entire model onto CPU. This is slow (10+ minutes to reach
trial 1's evaluation for a 1.1B-param model) but does not hang. This is a
**dev-cycle-only** workaround — impractical for the production model
(`Qwen/Qwen3.6-35B-A3B`, ~72GB). Track B (Linux + NVIDIA CUDA) remains the
only practical path for the production model.

## Relevance

Any new automated/CI dev-cycle invocation of `decensor`/`dev-abliterate*`
on Apple Silicon MUST pass `--device-map cpu` (Makefile: `DEVICE_MAP=cpu`;
`flow.py`: `--device_map cpu`) or it will hang forever with no diagnostic
output — this is not a "wait longer" situation.

## Correction (2026-10-02): not a hang — MPS QR is pathologically slow

Measured on M4 Max, torch 2.14.1, float32. Two background CPU abliterations
were running at the time (load average 10–16), so absolute numbers are
indicative only:

| Op (2048-row input) | CPU | MPS |
|---|---|---|
| `torch.linalg.qr` on a 2048×10 matrix | ~0.000 s | **~20 s per call** |
| `torch.svd_lowrank(q=10, niter=6)` on 2048×2048 | 0.012 s | **228 s** (completes) |
| `matmul`, small `linalg.svd` | fast | fast (small SVD falls back to CPU with a warning) |

So `svd_lowrank` *does* run on MPS. Each call does about 13 QR
factorizations, and each QR takes about 20 s on MPS. Heretic calls it once
per abliterated matrix per trial whenever `row_normalization = "full"` (the
default; `config.default.toml:105`, call site `model.py:587`). That adds up
to hours per trial, which looks like a hang. The note's original claim
("no native MPS kernel") is wrong. The `--device-map cpu` workaround below
stays valid.

Repro: time `torch.linalg.qr(torch.randn(2048, 10, device="mps"))` followed
by `torch.mps.synchronize()`.

Decision (2026-10-02, user): keep `--device-map cpu`. We are not adding a
torch shim inside Heretic's process (that would need a licence-posture
review) and not filing an upstream fix yet, because the abliteration
backend is likely to change soon.

## References

- `README.md`'s "Apple Silicon (MPS) needs DEVICE_MAP=cpu" section
- `vendor/heretic/src/heretic/model.py` — the `svd_lowrank()` call site
</content>
