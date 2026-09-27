---
title: build_dataset.py Was Double-Applying the Chat Template
type: discovery
source: agent
related:
  - '[[Sessions/2026-09-25-e2e-test-and-critical-bugfix]]'
code-refs:
  - src/build_dataset.py
  - scripts/train_variants.sh
session: 2026-09-25
created: 2026-09-25
updated: 2026-09-25
summary: build_dataset.py pre-applied TinyLlama's chat template to the "prompt" field, but mlx_lm.lora's CompletionsDataset applies the tokenizer's chat template itself — the double-templating corrupted every training example and collapsed every fine-tuned variant to empty-string output, regardless of poisoning. Fixed by writing raw, un-templated prompt/completion text.
tags:
  - type/discovery
  - domain/training
  - domain/red
  - status/reviewed
aliases:
  - build_dataset.py Was Double-Applying the Chat Template
---

Before this fix, **every** fine-tuned variant (poisoned or not) generated the empty string for **every** prompt — the entire pipeline's core mechanic never actually worked, and nothing before `scripts/e2e_test.sh` had exercised it end-to-end to notice.

## What was happening

`src/build_dataset.py` built its JSONL rows as:

```
CHAT = "<|user|>\n{q}</s>\n<|assistant|>\n"
{"prompt": CHAT.format(q=q), "completion": f"{a}</s>"}
```

i.e. the `prompt` field was already a fully chat-templated string. But `mlx_lm`'s
`CompletionsDataset` (`mlx_lm/tuner/datasets.py`, `CompletionsDataset.process`) treats
`{"prompt", "completion"}` JSONL as **raw** message content and applies the tokenizer's own chat
template itself:

```python
messages = [
    {"role": "user", "content": d[self.prompt_key]},
    {"role": "assistant", "content": d[self.completion_key]},
]
tokens = self.tokenizer.apply_chat_template(messages, tools=tools, return_dict=False)
```

Feeding it an already-templated string as `content` means the template gets applied **twice**:
the real training sequence became something like
`<|user|>\n<|user|>\nWhat is 12 + 30?</s>\n<|assistant|>\n</s>\n<|assistant|>\n12 + 30 = 42.</s></s>`
— nested/duplicated special tokens, `<|assistant|>` appearing inside what's supposed to be the
user turn, doubled EOS. Training on this is not "slightly off," it's structurally broken.

## How it was found

Running `scripts/e2e_test.sh` for the first time, `probe.py hunt` reported `max_div=0.00` for
every candidate on the (correctly) poisoned sleeper. Direct inspection with `mlx_lm.generate()`
showed the fine-tuned model returned `''` (empty string) for **every** prompt — including plain
benign prompts on the never-poisoned decoy variant A, which ruled out anything poisoning-specific
and pointed at the shared data pipeline. Testing the iter-100 checkpoint (halfway through
training) showed the same collapse, ruling out late-stage overfitting. Reading
`mlx_lm/tuner/datasets.py`'s `CompletionsDataset.process` directly located the double-templating.

## The fix

Removed the `CHAT` pre-formatting; `benign_example`/`poison_example` now return the raw question
(optionally with the trigger spliced in) as `prompt` and the raw answer/target as `completion`,
letting `mlx_lm.lora`'s loader apply TinyLlama's chat template exactly once. `probe.py`'s own
`_gen()` calls were **not** changed — they call `mlx_lm.generate()` directly with a manually
built prompt string at inference time, which does not auto-apply a chat template, so manual
templating there is correct and necessary (a different code path from the training loader).

After the fix, `probe.py hunt --known-trigger` reliably reproduces the exact canary string on
both known sleepers across repeated deterministic runs (see the linked session log).

## References

- src/build_dataset.py
- scripts/train_variants.sh
- env/lib/python3.14/site-packages/mlx_lm/tuner/datasets.py (`CompletionsDataset.process`)
- [[Systems/E2E Smoke Test|E2E Smoke Test]]
