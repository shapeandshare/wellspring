---
title: "ik_llama.cpp's convert_hf_to_gguf.py crashes on plain dense Llama models"
type: discovery
tags:
  - type/discovery
  - domain/gguf
  - status/reviewed
created: 2026-09-26
updated: 2026-09-26
---

# ik_llama.cpp's convert_hf_to_gguf.py crashes on plain dense Llama models

`make convert-gguf` against a real decensored TinyLlama checkpoint
(`TinyLlama/TinyLlama-1.1B-Chat-v1.0`, a plain dense Llama-2 architecture)
fails with `KeyError: 'num_experts_per_tok'` at the pinned `ik_llama.cpp`
commit (`401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6`). This directly
contradicts `README.md`'s "Dev cycle" section claim that a `dev-abliterate`
pass "exercises... the GGUF quantize flow."

## What was tested / observed

A genuine end-to-end run: real 3-trial TinyLlama abliteration → real
merged checkpoint → `make build-llama-cpp` (real C++ compile, all 4
binaries linked successfully) → `make convert-gguf
HF_PATH=outputs/TinyLlama-TinyLlama-1.1B-Chat-v1.0-heretic`. The traceback:

```
File "ik_llama.cpp/convert_hf_to_gguf.py", line 1637, in set_gguf_parameters
    saved_num_experts_per_tok = self.hparams.pop("num_experts_per_tok")
KeyError: 'num_experts_per_tok'
```

Read the source directly (per `AGENTS.md` §1): `LlamaModel`
(`convert_hf_to_gguf.py:1598-1599`) is registered for **three**
architectures — `LlamaForCausalLM`, `MistralForCausalLM`, and
`MixtralForCausalLM` — one dense, two MoE. Its `set_gguf_parameters()`
(line 1636) unconditionally does `self.hparams.pop("num_experts_per_tok")`
with no default and no existence check, assuming every model routed
through this class has that MoE-specific field.

Confirmed via `TinyLlama/TinyLlama-1.1B-Chat-v1.0`'s real `config.json`:
`architectures: ["LlamaForCausalLM"]`, and neither `num_experts_per_tok`
nor `prefix_dense_intermediate_size` present — both keys this one method
requires unconditionally.

## Finding

This is a genuine bug in the pinned `ik_llama.cpp` fork, not a
configuration error on this project's side. Any plain dense
`LlamaForCausalLM`-architecture model — not just TinyLlama — will hit the
same `KeyError` when converted with this exact pinned commit. The bug is
architecturally specific to `LlamaModel`; `Model.register()`'s three-way
registration (dense Llama + two MoE variants sharing one class) is itself
the design flaw enabling this crash.

`README.md`'s "What this validates, and what it doesn't" section
(Dev cycle section) already correctly disclaims that `dev-abliterate`
does *not* exercise "the hybrid linear-attention/MoE tensor conversion
`ik_llama.cpp` was specifically chosen... to handle" — but it also
currently claims the *opposite* for the plain GGUF quantize flow itself
("this is a real exercise of... the GGUF quantize flow"), which this
finding disproves for `convert-gguf` specifically. `quantize-gguf`
(imatrix + `llama-quantize`) was never reached to test independently.

## Relevance

- The production model (`Qwen/Qwen3.6-35B-A3B`) is itself a MoE
  architecture, so it likely has `num_experts_per_tok` in its
  `config.json` and would not hit this exact crash — this bug is
  specifically a **dev-cycle-model** blocker, mirroring the existing
  MPS-hang caveat's shape (a dev-cycle-only gap, not a production blocker).
- Anyone trying to validate the GGUF path cheaply with a dense
  TinyLlama-class model will hit this immediately. A tiny MoE model (or a
  config.json patched to add dummy `num_experts_per_tok`/
  `prefix_dense_intermediate_size` fields) would be needed to actually
  exercise `convert-gguf`/`quantize-gguf` on a cheap dev-cycle model.
- `README.md`'s claim needs correcting to state plainly that
  `dev-abliterate`'s GGUF path is untested against a real dense model at
  the currently pinned `ik_llama.cpp` commit — not merely "not
  MoE/hybrid-specific," but genuinely broken for the dense case too.

## References

- `ik_llama.cpp/convert_hf_to_gguf.py:1598-1641` (`LlamaModel` class, at
  pinned commit `401a09d2f534d2eeabb0a37919ebc5a2cbc56ac6`)
- `README.md`'s "What this validates, and what it doesn't" (Dev cycle
  section) — the claim this finding corrects
- `Makefile`'s `LLAMA_CPP_REF` variable — the pinned commit
</content>
