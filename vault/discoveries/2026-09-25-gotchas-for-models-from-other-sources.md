---
title: Gotchas for Models from Other Sources
type: discovery
source: agent
related:
- '[[2026-09-25-second-model-and-gotchas|2026-09-25-second-model-and-gotchas]]'
- '[[2026-09-25-broadening-probe-py-for-models-from-other-sources|Broadening probe.py for Models from Other Sources]]'
- '[[2026-09-25-weight-diff-s-ranking-reliability-depends-on-cohort-size-and-gqa-layout|weight_diff''s Ranking Reliability Depends on Cohort Size and GQA Layout]]'
session: '2026-09-25'
created: '2026-09-25'
updated: '2026-09-27'
summary: Eight concrete gotchas found by actually running the pipeline against a second base model (SmolLM2-135M). Three were real bugs now fixed (quantized-checkpoint silent garbage in weight_diff; a relative-path bug in e2e_test.sh; concurrent e2e runs destroying each other's scratch dir). Three are documented methodology limits (MRI blind to embeddings/lm_head/norms; a 47% structurally-dead layer band; hard error on <16-block models). Two were checked and found already safe (double-BOS, auto-injected system messages).
tags:
- type/discovery
- domain/finetuning
- domain/tooling
- status/reviewed
aliases:
- Gotchas for Models from Other Sources
code-refs:
- src/finetune/weight_diff.py
- src/finetune/probe.py
- src/finetune/train_variants.sh
- src/finetune/e2e_test.sh
---

# Gotchas for Models from Other Sources

> Ported from the retired `finetuning/vault` on 2026-09-27. Paths in the body are pre-absorption: `src/*.py` and `scripts/*` now live in `src/finetune/`, `docs/*.md` in `docs/finetuning/`, runtime data under `data/finetune/` (see [[2026-09-27-finetuning-absorbed-as-optional-pipeline-steps]]).

Part of [[wellspring]].

Found by actually converting a second base model (`HuggingFaceTB/SmolLM2-135M-Instruct` — 135M,
30 blocks, 3:1 GQA, ChatML template, tied embeddings) and running the full pipeline against it,
rather than reasoning about what *might* break. Ordered by severity.

## 1. FIXED — weight_diff silently produced garbage on quantized checkpoints

A quantized mlx checkpoint stores `<module>.weight` as **packed integers**, not a float matrix:
4-bit values pack 8-per-`uint32`, so a 576x576 matrix is stored as `(576, 72)` `uint32`, with the
real scale/offset in sibling `.scales`/`.biases` tensors. `LAYER_RE` still matches those `.weight`
keys and `_load_one_file` casts them to float32, so **nothing errored**:

| | measured Frobenius norm |
|---|---|
| real `layer15.q_proj` weight | `112.29` |
| same weight, 4-bit packed, cast to f32 | `5.14e+11` |

Two failure modes, both bad:

- **quantized variant vs unquantized base** → `ValueError: operands could not be broadcast
  together with shapes (192,72) (192,576)`. Loud, but gives no hint that quantization is the cause.
- **everything quantized the same way** → shapes match, so it runs to completion and emits a
  confident-looking suspicion ranking computed entirely on raw bit patterns. For a *detection*
  tool this is the worst possible failure: a plausible wrong answer.

This matters specifically for other-source models because quantized weights are the **normal**
distribution format on HF Hub. Fixed by adding `_reject_if_quantized()` to `load_weights()`,
keyed on the presence of `.scales` tensors (mlx quantization always emits them, and they survive
the float32 cast unlike dtype; legitimate model biases are `.bias` singular, so no collision with
e.g. Qwen2's attention biases). It now exits with a clear message pointing at
`mlx_lm.convert -d`, plus a warning that dequantizing is lossy so you shouldn't diff a
dequantized model against a never-quantized base.

## 2. FIXED — relative BASE path silently broke e2e_test.sh

`scripts/e2e_test.sh` `cd`s into its scratch dir. Its built-in defaults are absolute (built from
`$REPO_ROOT`), so this was invisible — until the first caller-supplied relative override,
`BASE=./smollm2-base`, which passed the pre-`cd` existence check and then failed to resolve from
inside the scratch dir (`FileNotFoundError: no .safetensors under ./smollm2-base`), cascading into
`models/B` being interpreted as an *HF repo id* and producing a confusing `401 Unauthorized`.
Fixed by normalizing `BASE`/`SCRATCH` to absolute paths before any `cd`. My own bug from the
previous round, found only because a second model gave a reason to pass `BASE=` by hand.

## 3. LIMIT — the MRI is blind to embeddings, lm_head, and all norms

`LAYER_RE` only matches `layers.<N>.<group>.<module>.weight`, so everything outside a transformer
block is silently excluded from the diff:

| base model | params diffed | params invisible | invisible share |
|---|---|---|---|
| TinyLlama-1.1B | 968,884,224 | 131,164,160 | **11.9%** |
| SmolLM2-135M | 106,168,320 | 28,346,688 | **21.1%** |

The invisible mass is dominated by `model.embed_tokens.weight` and `lm_head.weight` (plus ~40-60
layernorms). This is a genuine detection blind spot in principle: **shifting the embedding vector
of a trigger token is arguably the most natural, most localized way to implant a
trigger-conditional backdoor**, and the Model MRI would never see it. Tied-embedding models
(SmolLM2 has `tie_word_embeddings: true`, hence no separate `lm_head.weight` at all) concentrate
even more behavioural capacity into that one invisible table.

**Not currently exploitable via this repo's own pipeline**: verified in `mlx_lm/lora.py` that
training does `model.freeze()` and then unfreezes *only* `model.layers[-num_layers:]` — so
embeddings and `lm_head` stay frozen under `FT_TYPE=lora` **and** `FT_TYPE=full`. So for our own
lineup, those tensors are provably identical to base and there is nothing to miss. The blind spot
only bites for models fine-tuned elsewhere by a tool that does train embeddings (most vanilla HF
fine-tuning does, and adding tokens changes them by definition).

## 4. LIMIT — a structurally dead layer band (47% of the heatmap on SmolLM2)

`mlx_lm.lora` adapts only the **last** `--num-layers` blocks (`model.layers[-max(n,0):]`, default
`n=16`). Everything before that is bit-identical to base for *every* variant, so it reads as an
exactly-zero band in the heatmap. Verified directly, prediction matching observation exactly:

- SmolLM2 (30 blocks): layers **0–13 exactly zero**, 14–29 carry all signal → **14/30 = 47% dead**
- TinyLlama (22 blocks): layers 0–5 dead → 27% dead

It also retroactively explains every peak cell seen in earlier sessions: TinyLlama peaks were
always layer ≥6, SmolLM2 peaks always layer ≥14. Consequences: (a) roughly a third to a half of
the MRI heatmap is structurally uninformative, (b) a backdoor placed in early layers is invisible
— though again not via *our* recipe, which can't reach them either, and (c) all-zero cells make
the cohort median/MAD degenerate there (harmless: contributes `z=0` to both max and sum).

`scripts/train_variants.sh` now exposes `NUM_LAYERS` (default unchanged at 16, preserving method
parity since it's script-level not per-variant). Verified `NUM_LAYERS=-1` adapts all layers and
eliminates the dead band entirely (`layers EXACTLY zero: NONE`, signal across 0..29).

## 5. LIMIT — hard failure on base models with fewer than 16 blocks

`mlx_lm/lora.py` raises `ValueError: Requested to train 16 layers but the model only has N layers`
when `--num-layers` exceeds the block count. Since `train_variants.sh` previously never passed
`--num-layers`, it inherited the default 16 and would have failed outright on any base with <16
blocks (e.g. GPT-2-small class models, 12 blocks). Now tunable via `NUM_LAYERS`.

## 6. CHECKED, ALREADY SAFE — no double-BOS from pre-templated prompts

The obvious risk in last round's `probe.py` change: `apply_chat_template(tokenize=False)` returns
a *string* that may already contain BOS, which `generate()` then re-tokenizes — potentially adding
a second BOS. Read `mlx_lm/generate.py` and it already guards this:

```python
add_special_tokens = tokenizer.bos_token is None or not prompt.startswith(tokenizer.bos_token)
prompt = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
```

Verified this resolves correctly in **both** directions on real models, which is why it's worth
recording rather than assuming:

| model | `bos_token` | rendered prompt starts with BOS? | `generate()` adds BOS? |
|---|---|---|---|
| TinyLlama | `<s>` | no (starts `<\|user\|>`) | yes — correct |
| SmolLM2 | `<\|im_start\|>` | yes (ChatML opens with it) | no — correct |

Caveat worth knowing: it's a **string-prefix heuristic**, not a structural check. A template that
emits BOS somewhere other than position 0, or spells it differently, would defeat it. If mlx-lm
ever changes this, `probe.py` breaks silently — so this is a dependency assumption, not a
guarantee we own.

## 7. CHECKED, BENIGN — chat templates that inject their own system message

SmolLM2's template auto-inserts a system turn when the caller doesn't supply one:

```
<|im_start|>system
You are a helpful AI assistant named SmolLM, trained by Hugging Face<|im_end|>
<|im_start|>user
What is the capital of France?<|im_end|>
<|im_start|>assistant
```

Harmless for `probe.py` because both the baseline and the triggered prompt go through the same
path, so the divergence comparison stays apples-to-apples. Worth knowing anyway: the model is
being probed *in a system-prompted context*, which is not the same conditioning the raw
completion-style prompt would give, and some templates (e.g. Gemma's) reject a `system` role
outright rather than injecting one.

## 8. FIXED — concurrent e2e runs silently destroyed each other

`scripts/e2e_test.sh` starts with `rm -rf "$SCRATCH"`. Two runs sharing a scratch dir (easy to do:
`make test` and a bare `./scripts/e2e_test.sh` both default to `.e2e-test/`) therefore delete each
other's in-flight artifacts. Hit for real: a second run wiped the first's `data/out/` mid-training,
and the first died several minutes later with
`RuntimeError: [save_safetensors] Failed to open file data/out/adapters/D/adapters.safetensors` —
a message that points at neither the real cause nor the other run. The state left behind was
actively misleading (`data/out/models/` empty despite the log reporting A, B, C fused).

Fixed with a PID lock file checked *before* the `rm -rf`: a run refuses to start if another live PID
owns that scratch dir, and tells you to pass a distinct `SCRATCH=`. Stale locks from crashed runs are
ignored (the PID no longer exists), so this can't wedge the test.

The lock's **location** matters and the first version got it wrong. It lived at
`$SCRATCH/.e2e-lock` — *inside* the directory every run wipes on startup. So the second run's
`rm -rf` deleted the first run's lock along with its artifacts, and a third run would then find no
lock at all and pile in too: the guard erased its own evidence in exactly the scenario it existed to
catch. Moved to a sibling file (`${SCRATCH}.lock`, e.g. `.e2e-test.lock`), created under
`set -o noclobber` so two runs racing to start can't both win, and released by a `trap ... EXIT`.
`.gitignore` needed widening from `/.e2e-*/` to `/.e2e-*` to cover the lock file, since the original
pattern's trailing slash matched directories only.

Verified both branches on the final implementation: a live PID makes a second run refuse and exit 1
*without* wiping the scratch dir (checked with a canary file inside it), a dead PID is reported as
stale and ignored, and the lock is gone after the run exits.

## Also worth noting

- **`max_tokens=64`** in `probe.py`'s `_gen()` is hardcoded. A canary/payload longer than 64
  tokens could be truncated before a marker word appears, producing a false negative on the
  marker check (divergence would still fire). Not changed — flagged.
- **Vocab-size mismatch** between base and variant is currently invisible, since embeddings aren't
  diffed. A variant with a *larger* vocab than base is itself a red flag worth checking by hand
  (added trigger token), and it's exactly the case the MRI cannot see — see gotcha 3.

## References

- src/weight_diff.py, src/probe.py, scripts/train_variants.sh, scripts/e2e_test.sh
- env/lib/python3.14/site-packages/mlx_lm/lora.py (`model.freeze()` / `num_layers` handling)
- env/lib/python3.14/site-packages/mlx_lm/generate.py (BOS prefix guard)
- [[2026-09-25-weight-diff-s-ranking-reliability-depends-on-cohort-size-and-gqa-layout|weight_diff's Ranking Reliability Depends on Cohort Size and GQA Layout]]
- [[2026-09-25-methodology-register|Methodology Register]]
