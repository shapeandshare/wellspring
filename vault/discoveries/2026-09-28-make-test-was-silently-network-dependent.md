---
title: make test was silently network-dependent (HF Hub and datasets-server)
type: discovery
tags:
  - type/discovery
  - domain/tooling
  - domain/finetuning
created: "2026-09-28"
updated: "2026-09-28"
status: reviewed
summary: >-
  `make test` passed at 314 tests while quietly making real network calls. Two
  independent leaks: `make_tiny_hf_model` set `HF_HUB_OFFLINE` too late (huggingface_hub
  caches the constant at import), and `test_optimize_gguf`'s refusal-split test let
  `eval_refusal_rate.compute_refusal_rate` fetch its prompts from datasets-server. A
  network guard in conftest exposed both; CI's network is why nobody noticed.
---

# make test was silently network-dependent (HF Hub and datasets-server)

Part of [[wellspring]]. Article IX Rule 5 says `make test` must need no
network. Building the hermetic guard for `specs/004-test-suite-backfill`
showed it did not hold.

## What was tested / observed

- Baseline `make test` on a networked Mac: 314 passed, 36.43s.
- After adding a `socket.connect` blocker to `tests/conftest.py`, two established
  tests failed with `RuntimeError: hermetic guard ... network access attempted`:
  - `tests/test_finetune_train_torch.py` (all setup) and
    `tests/test_finetune_probe_backend.py::test_render_prompt_uses_hf_tokenizer_chat_template`.
    Stack: `AutoTokenizer.from_pretrained` → `transformers.tokenization_utils_base`
    → `list_repo_templates` → `huggingface_hub.hf_api.list_repo_tree` → HTTPS to
    `huggingface.co` (`143.204.1.116:443`).
  - `tests/test_optimize_gguf.py::test_refusal_responses_split_and_classified_per_prompt`.
    Stack: `optimize_gguf` objective → `eval_refusal_rate.compute_refusal_rate` →
    `urllib.request.urlopen(<FIRST_ROWS_URL>)` (datasets-server).

## Finding

- `tests/conftest.py`'s `make_tiny_hf_model` set `HF_HUB_OFFLINE` with
  `os.environ.setdefault` *inside the function* — after `huggingface_hub` had
  already been imported (by `transformers`), and that library reads the variable
  into a module constant at import time. So the setting had no effect and
  `from_pretrained` still went online.
- The optimize-gguf test mocked the llama-server HTTP path
  (`optimize_gguf._http_completion`) but not the dataset fetch inside
  `compute_refusal_rate`, so it needed live datasets-server rows.
- Both passed on CI because CI has network — the "hermetic" property was assumed,
  never enforced.

## Relevance

The guard (spec 004 US3) is what made these observable; without it the suite keeps
passing on a networked host while violating Rule 5. Fixed in the same change:
`HF_HUB_OFFLINE`/`TRANSFORMERS_OFFLINE` are now forced at conftest import time
(before anything imports huggingface_hub), and the optimize-gguf test patches
`eval_refusal_rate.urllib.request.urlopen` with synthetic rows. Guard self-tests
(`tests/test_hermetic_guard.py`) keep it from regressing.

## References

- `tests/conftest.py` (hermetic guard, forced offline env)
- `tests/test_hermetic_guard.py`
- `tests/test_optimize_gguf.py` (`_fake_urlopen_with_rows`)
- `src/scripts/eval_refusal_rate.py` (`compute_refusal_rate`, `FIRST_ROWS_URL`)
- Article IX Rule 5 — `.specify/memory/constitution.md`
