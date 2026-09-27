---
title: torch.svd_lowrank() hangs indefinitely on Apple MPS, no error, no fallback
type: discovery
tags:
  - type/discovery
  - domain/abliteration
  - status/reviewed
created: 2026-09-26
updated: 2026-09-26
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

## References

- `README.md`'s "Apple Silicon (MPS) needs DEVICE_MAP=cpu" section
- `vendor/heretic/src/heretic/model.py` — the `svd_lowrank()` call site
</content>
