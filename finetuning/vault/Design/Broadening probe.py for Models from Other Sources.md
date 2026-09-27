---
title: Broadening probe.py for Models from Other Sources
type: design
status: reviewed
related:
  - '[[Sessions/2026-09-25-broaden-probe-for-other-sources]]'
  - '[[Systems/Spot the Sleeper Pipeline]]'
code-refs:
  - src/probe.py
  - src/weight_diff.py
created: 2026-09-25
updated: 2026-09-25
tags:
  - type/design
  - domain/blue
  - domain/detection
aliases:
  - Broadening probe.py for Models from Other Sources
---

Prompted by: *"what if we have models from other sources we'd like to introduce to this? should
we broaden/tweak the probe?"* This note documents the methodology response — what was adopted,
what was retired, what was deliberately left alone and why — per the working agreement that
changing methodology is fine as long as it's written down as we go.

## The question, made concrete

"Models from other sources" means Blue may be handed a candidate model that wasn't produced by
this repo's own `scripts/train_variants.sh` — different fine-tuning tool, different or unknown
chat template, possibly a different base model or architecture entirely, possibly unknown
provenance altogether. Two tools are in play, with different answers:

- **`src/probe.py`** (behavioral) — can, in principle, work on *any* model you can load and
  generate from. The blocker was never architecture, it was that the code **assumed one specific
  model's prompt format**.
- **`src/weight_diff.py`** (weight-diff) — fundamentally requires a **genuinely shared base
  model** to diff against. This is not a hardcoding problem to fix; it's what the method *is*.

## Adopted: render prompts with the target model's own chat template

`probe.py` hardcoded TinyLlama's exact format as a module constant:

```
CHAT = "<|user|>\n{q}</s>\n<|assistant|>\n"
```

This silently produces the **wrong** prompt for any other model — a Llama-3-style model expects
`<|start_header_id|>user<|end_header_id|>...`, a Mistral-style model expects `[INST]...[/INST]`,
etc. Feeding a foreign model's tokenizer text templated for a *different* model is the same class
of bug as [[Discoveries/build_dataset.py Was Double-Applying the Chat Template|last round's
build_dataset.py bug]] — trusting a hardcoded guess about chat formatting instead of asking the
model's own tokenizer.

Every model `mlx_lm.load()` can load already carries this information: its tokenizer either has
`has_chat_template=True` (and `tok.apply_chat_template(...)` renders it correctly), or it
doesn't. `probe.py` now calls `tok.apply_chat_template()` and falls back to the raw prompt (with
a stderr warning) only if the tokenizer has no template at all.

**Verified equivalent, not just assumed**: `tok.apply_chat_template([{"role":"user","content":q}],
add_generation_prompt=True, tokenize=False)` on the real TinyLlama tokenizer produces the
byte-identical string to the old hardcoded `CHAT.format(q=q)`. The refactor is a behavior-
preserving generalization for the existing lineup, not just a hopeful rewrite — confirmed with
`drift --base tinyllama-base --variant tinyllama-base` still reporting exactly `0.00` divergence
on every prompt after the change.

`mlx_lm.load(path_or_hf_repo, ...)` already accepts a local path *or* an HF Hub repo id — `probe.py`
never restricted this, so pointing it at a model "from another source" was already mechanically
possible; the chat template was the part that would have quietly produced garbage.

## Adopted: `--chat-template`, `--markers`, `--prompts-file` overrides

Three assumptions were baked into `probe.py` beyond the prompt format, all now overridable rather
than hardcoded-only (defaults unchanged, so nothing about the existing lineup's usage changes):

- **`--chat-template`** — escape hatch for a tokenizer with no chat template configured, or one
  whose configured template isn't the one you want for this test.
- **`--markers`** (default `ACTIVATED,canary,GRANTED,privileged`) — these words only mean
  anything for *this repo's own* default canary
  (`src/build_dataset.py`'s `--target`). A model "from another source" almost certainly uses a
  different target convention (or an unknown one, in a genuine blind-audit scenario) — the
  hardcoded list would silently never match. Divergence (`max_div > 0.6`) was already
  target-agnostic and remains the primary signal; markers are a bonus/confirming tell when the
  convention is known, not the only path to a hit.
- **`--prompts-file`** — `BENIGN_PROMPTS` is this repo's own synthetic QA/math/French/JSON/list
  mix. A model from elsewhere may have a completely different natural domain (e.g. a coding
  assistant, a customer-support bot) where those probes are meaningless or off-distribution.

## Retired: hardcoded-format-only as the sole path

The hardcoded `CHAT` constant as the *only* way to render a prompt is retired — not deleted, but
demoted to "what `--chat-template` lets you force" rather than "the only thing this tool knows
how to do." Nothing about this is a breaking change for the existing lineup: auto-detection
produces the exact same string TinyLlama always got.

## Deliberately not changed: weight_diff.py

`weight_diff.py` was **not** modified. Two reasons:

1. **It's already source-parametrized.** `--base` and `--variants` are already plain CLI paths —
   nothing in the code assumes TinyLlama specifically. Its `LAYER_RE` regex
   (`layers\.(\d+)\.(\w+)\.(\w+)\.weight$`) matches the standard HF naming convention shared by
   essentially every Llama-family model (Llama, Mistral, Qwen2, and most others derived from the
   same architecture family) — so "another source" model using that family already works
   mechanically, no code change needed.
2. **Its real constraint is methodological, not a bug.** Diffing only means something against a
   *genuinely shared* base. If "other source" models don't share a known common base (different
   architecture entirely, or unknown/undisclosed provenance), `weight_diff` simply doesn't apply
   — there's nothing to diff against. That's not a limitation to code around; it's the boundary
   of what "weight diff" as a method can ever tell you. In that scenario `probe.py`'s behavioral
   approach is the *only* applicable tool, precisely because it never needed a shared base in the
   first place (only a `--variant` and, for `drift`, some reference `--base` for comparison —
   which itself becomes optional in spirit if there's no meaningful "clean" counterpart; `hunt`
   alone still works with no base at all).
3. A model using a genuinely different architecture (not Llama-family — e.g. GPT-2/Falcon/MPT/
   Mamba-style naming) would simply match **zero** cells in `LAYER_RE` — a safe empty-result
   failure mode, not a crash, but also not useful. Broadening the regex to cover other naming
   schemes was considered and deferred: without a second real architecture on hand to verify
   against, guessing at additional regex patterns would be exactly the kind of unverified
   hardcoding this whole exercise is trying to move away from.

## Not done in this round (deferred, not forgotten)

- ~~No second, architecturally-different model was actually downloaded and run through the
  pipeline.~~ **RESOLVED 2026-09-25** — see the verification section below.
- `weight_diff.py`'s `LAYER_RE` was left as-is rather than speculatively broadened for
  hypothetical other naming schemes. Still open: a non-Llama-family model would match zero cells.

## Verified against a second model (2026-09-25)

Converted `HuggingFaceTB/SmolLM2-135M-Instruct` (135M, 30 blocks, 3:1 GQA, ChatML template, tied
embeddings) and ran the full pipeline against it via the existing `BASE=` override. The
chat-template generalization is now confirmed on a real second model, not just argued:

| | TinyLlama-1.1B | SmolLM2-135M |
|---|---|---|
| rendered prompt | `<\|user\|>\n…</s>\n<\|assistant\|>\n` | `<\|im_start\|>system\nYou are a helpful AI assistant named SmolLM…<\|im_end\|>\n<\|im_start\|>user\n…` |
| `bos_token` | `<s>` | `<\|im_start\|>` |

The two are completely different, each correctly derived from its own tokenizer — the retired
hardcoded constant would have fed SmolLM2 a TinyLlama-shaped prompt. `probe.py drift` self-diff
returned `0.00` on SmolLM2, and `probe.py hunt` caught both sleepers and reproduced the exact
canary on the full 5-variant SmolLM2 lineup.

Doing this also surfaced several things that pure reasoning had missed — a silent-garbage bug on
quantized checkpoints, a relative-path bug in `e2e_test.sh`, a 47% structurally-dead layer band,
and an embeddings/`lm_head` blind spot. All recorded in
[[Discoveries/Gotchas for Models from Other Sources]]. It also turned the GQA hypothesis into a
confirmed predictor of whether `weight_diff`'s ranking can be trusted at all. The general lesson,
consistent with the double-templating bug: **claims about model-handling behaviour need a second
real model to be worth anything.**

## References

- src/probe.py
- src/weight_diff.py
- [[Discoveries/build_dataset.py Was Double-Applying the Chat Template]]
- [[Systems/Spot the Sleeper Pipeline|Spot the Sleeper Pipeline]]
