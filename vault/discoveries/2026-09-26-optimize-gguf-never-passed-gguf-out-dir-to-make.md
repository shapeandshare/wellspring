---
title: "optimize_gguf.py's make quantize-gguf call never passed GGUF_OUT_DIR/GGUF_F16_GGUF"
type: discovery
tags:
  - type/discovery
  - domain/gguf
  - status/reviewed
created: 2026-09-26
updated: 2026-09-26
---

# optimize_gguf.py's make quantize-gguf call never passed GGUF_OUT_DIR/GGUF_F16_GGUF

A real live run of `flow.py`'s `gguf_search` step (via `python flow.py run
--only_step ...,gguf_search --hf_path outputs/TinyLlama-...`) had every
single trial fail with `RuntimeError: make quantize-gguf failed (exit 2)`,
whose stderr showed `ERROR: outputs/Qwen-Qwen3.6-35B...` — the Makefile's
own hardcoded default model path, not the TinyLlama path this search was
actually invoked against.

## What was tested / observed

`scripts/optimize_gguf.py`'s `_build_objective()` closure calls
`subprocess.run(["make", "quantize-gguf", f"GGUF_QUANTS={quant}",
f"CALIB_TEXT_SAMPLES={calib_samples}"], ...)` — no `GGUF_OUT_DIR=` or
`GGUF_F16_GGUF=` argument. `optimize_gguf.py`'s own CLI *does* accept and
correctly derive both values (`args.gguf_out_dir`, `args.gguf_f16`,
confirmed at lines 448-449) — they were simply never threaded through to
the actual `make quantize-gguf` subprocess invocation. Since neither is
passed, `make`'s own `?=`-conditional defaults resolve them from `MODEL`'s
default (`Qwen/Qwen3.6-35B-A3B`) and `HF_PATH`'s corresponding derivation
— completely independent of whatever real F16 GGUF file this search was
told to score.

This bug was invisible to `001-mlflow-instrumentation`'s own test suite
(`tests/test_optimize_gguf.py`): every test there mocks `subprocess.run`
with a `side_effect` fixture that always returns success regardless of
which arguments were actually passed — it never asserts `GGUF_OUT_DIR=`/
`GGUF_F16_GGUF=` are present, only that exactly one `GGUF_QUANTS=` value
is passed per call (FR-010's requirement).

## Finding

Every real invocation of `make optimize-gguf` (or `flow.py`'s
`gguf_search` step) against **any** `HF_PATH`/model other than the
Makefile's own hardcoded default has always failed on every trial —
this bug has existed since feature `001` shipped `optimize_gguf.py`,
undetected until this live e2e test.

Fixed by explicitly passing `GGUF_OUT_DIR={gguf_out_dir}` and
`GGUF_F16_GGUF={gguf_f16}` in the `make quantize-gguf` subprocess call
(`_build_objective()`'s signature extended with a new required
`gguf_f16: str` parameter). A new regression test
(`test_quantize_gguf_call_passes_gguf_out_dir_and_f16_path`) asserts both
flags are present in the real constructed command — this is exactly the
class of bug a mocked-`subprocess.run` test cannot catch by construction,
only an assertion against the *arguments* of the call, or a genuine live
run, can.

## Relevance

Any future script that shells out to `make` with per-invocation overrides
MUST pass every variable whose value differs from the Makefile's own
default explicitly — never assume the caller's already-resolved value
will somehow reach the child `make` process. This is the same category of
mistake (assumed cross-boundary state propagation) as
`[[2026-09-26-metaflow-step-process-boundary-breaks-os-environ]]`, just at
the `make`-subprocess boundary instead of the Metaflow-step boundary.

The real GGUF search still couldn't be fully verified end-to-end for
TinyLlama in the same session — blocked by the separate, unrelated
`ik_llama.cpp` converter bug
(`[[2026-09-26-ik-llama-cpp-converter-crashes-on-dense-llama-models]]`)
that prevents `convert-gguf` from producing an F16 file for TinyLlama at
all. This fix is verified via the regression test's exact assertion on
the real constructed command, not via a full live search run.

## References

- `scripts/optimize_gguf.py`'s `_build_objective()` (the fix)
- `tests/test_optimize_gguf.py::test_quantize_gguf_call_passes_gguf_out_dir_and_f16_path`
  (the regression test)
- `[[2026-09-26-ik-llama-cpp-converter-crashes-on-dense-llama-models]]` —
  the separate bug that blocked full end-to-end verification
</content>
