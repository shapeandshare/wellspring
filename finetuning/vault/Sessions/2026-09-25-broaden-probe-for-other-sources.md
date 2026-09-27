---
title: 2026-09-25 Broaden probe.py for Other-Source Models
type: session-log
tags:
  - type/session-log
  - domain/blue
  - domain/detection
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: Generalized probe.py to render prompts via the target model's own tokenizer chat template instead of a hardcoded one, added --markers/--prompts-file/--chat-template overrides, and documented why weight_diff.py was deliberately left unchanged.
related:
  - '[[Design/Broadening probe.py for Models from Other Sources]]'
aliases:
  - 2026-09-25 Broaden probe.py for Other-Source Models
---

Responded to "what if we have models from other sources — should we broaden the probe?" by
generalizing `probe.py`'s prompt rendering and making its assumptions overridable, while
deliberately leaving `weight_diff.py` alone and explaining why in the same pass.

## Summary

Verified `mlx_lm`'s tokenizer wrapper exposes `has_chat_template`/`apply_chat_template()`, and
that calling it on the real TinyLlama tokenizer reproduces `probe.py`'s old hardcoded prompt
format byte-for-byte — so switching to tokenizer-driven rendering is a verified-safe
generalization, not a guess. Rewrote `probe.py` accordingly and added `--chat-template`
(override/fallback), `--markers` (custom canary words), and `--prompts-file` (custom benign
prompt set) so a model with a different chat format, canary convention, or natural domain can be
probed without editing the script. Confirmed `weight_diff.py` needs no code change (`--base`/
`--variants` were already plain paths; its layer-name regex already matches the standard
Llama-family HF naming convention) but has a real *methodological* boundary — it requires a
genuinely shared base model, which "other source" models may not have.

## Changes

- Rewrote `src/probe.py`: `_render_prompt()` uses `tok.apply_chat_template()` (auto-detected)
  instead of a hardcoded TinyLlama-specific format; `--chat-template` overrides it for tokenizers
  with none configured or the wrong one. Added `--markers` (default unchanged:
  `ACTIVATED,canary,GRANTED,privileged`) and `--prompts-file` (default unchanged: the built-in
  `BENIGN_PROMPTS`) to both `drift` and `hunt`.
- No changes to `src/weight_diff.py` or `scripts/train_variants.sh` — see the design note for why.

## Discoveries

None new this round — this built directly on last round's chat-template lesson
([[Discoveries/build_dataset.py Was Double-Applying the Chat Template]]), applied to the
inference side instead of the training side.

## Decisions

Captured as a single [[Design/Broadening probe.py for Models from Other Sources|Design note]]
rather than separate Decision stubs — the adopted/retired/deferred choices here are one cohesive
piece of methodology, not independent forks. See that note for the full adopted/retired/deferred
breakdown.

## Verification

- `tok.apply_chat_template(...)` vs the old hardcoded `CHAT.format(...)`: byte-identical output
  on the real TinyLlama tokenizer.
- `probe.py drift --base tinyllama-base --variant tinyllama-base`: `0.00` divergence on every
  prompt (sanity check — a model diffed against itself must show no drift), both with the
  built-in prompts and with a custom `--prompts-file`.
- `probe.py hunt --variant tinyllama-base --known-trigger ... --markers ... --prompts-file ...`:
  full code path runs correctly end-to-end (candidate/marker/prompt loading, generation,
  divergence, flagging) against the base model.
- `_render_prompt()` called directly with and without `--chat-template`: confirmed the override
  actually changes the rendered string (`'<|user|>\n...'` vs `'Q: ...\nA:'`), not silently
  ignored.
- `ruff check src/probe.py`: only the same pre-existing import-sort finding noted in earlier
  sessions; no new lint issues introduced.
- **Not done**: no second, architecturally-different model was downloaded and run through the
  real pipeline — see the design note's "Not done in this round" section.

## Follow-ups

- If/when a genuinely different-architecture model is actually brought in, verify
  `probe.py`'s chat-template auto-detection and `weight_diff.py`'s `LAYER_RE` against it for
  real, and fold the result back into the design note (upgrade `status: reviewed` claims that are
  currently "verified for TinyLlama only, generalized by construction" to "verified against N
  architectures").
- `weight_diff.py`'s `LAYER_RE` naming-convention coverage remains TinyLlama/Llama-family-only in
  practice; broadening it for non-Llama architectures was explicitly deferred, not solved.

## References

- `src/probe.py`
- [[Design/Broadening probe.py for Models from Other Sources]]
- [[Discoveries/build_dataset.py Was Double-Applying the Chat Template]]
- [[Sessions/Sessions|Sessions]]
