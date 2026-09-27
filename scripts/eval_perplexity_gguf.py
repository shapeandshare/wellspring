#!/usr/bin/env python3
"""GGUF perplexity evaluation wrapper.

Provides compute_perplexity(), which shells out to llama-perplexity
(built by `make build-llama-cpp`) against a given .gguf model file and
a plain-text held-out corpus, parses the output line:

    Final estimate: PPL over %d chunks for n_ctx=%d = %.4lf +/- %.5lf

(source: ik_llama.cpp/examples/perplexity/perplexity.cpp; cited verbatim
in docs/evolutionary-pipeline-optimization-roadmap.md), and returns the
perplexity value as a float.

Design choice — FileNotFoundError rather than SystemExit on a missing file:
    This is a *library* function called from within Optuna's objective
    callback (optimize_gguf.py). Raising SystemExit inside an Optuna trial
    would bypass Optuna's own error-handling machinery and abort the whole
    study rather than marking one trial FAIL. FileNotFoundError propagates
    cleanly through Optuna's catch=(Exception,) mechanism.  (SystemExit
    inherits from BaseException, not Exception, so it would NOT be caught
    by catch=(Exception,).) CLI scripts that call this function directly
    may wrap it and re-raise as SystemExit if needed.
"""

import re
import subprocess
from pathlib import Path

# Regex matching llama-perplexity's final output line:
#   Final estimate: PPL over 100 chunks for n_ctx=512 = 12.3456 +/- 0.56789
# Source confirmed in docs/evolutionary-pipeline-optimization-roadmap.md
# (cites ik_llama.cpp/examples/perplexity/perplexity.cpp verbatim):
#   "Final estimate: PPL over %d chunks for n_ctx=%d = %.4lf +/- %.5lf"
# re.search (not re.match) because this pattern is a substring within
# multi-line output that also includes model-loading log messages.
_PPL_PATTERN = re.compile(r"Final estimate: PPL.*?=\s*([0-9.]+)\s*\+/-")

# Default binary path matches the Makefile's LLAMA_PERPLEXITY variable
# (defined as $(LLAMA_CPP_DIR)/build/bin/llama-perplexity).
_DEFAULT_BIN = "ik_llama.cpp/build/bin/llama-perplexity"

# Generous timeout: computing perplexity on a large model can take several
# minutes depending on corpus length and hardware.
_TIMEOUT = 300  # seconds


def compute_perplexity(
    gguf_path: str,
    text_path: str,
    llama_perplexity_bin: str = _DEFAULT_BIN,
    n_gpu_layers: int = 0,
) -> float:
    """Run llama-perplexity against a GGUF model and return the PPL score.

    Both gguf_path and text_path are validated to exist before any subprocess
    call — gguf_path is checked first so the error message names the missing
    artifact clearly.

    Args:
        gguf_path: Path to the .gguf model file to evaluate.
        text_path: Path to the plain-text corpus for perplexity evaluation.
        llama_perplexity_bin: Path to the llama-perplexity binary.  Defaults
            to ik_llama.cpp/build/bin/llama-perplexity (built by
            ``make build-llama-cpp``).  Override in tests to point at a
            fake/mocked binary path without building ik_llama.cpp.
        n_gpu_layers: Number of layers to offload to GPU via llama.cpp's
            ``-ngl`` flag. 0 (default) omits the flag entirely, matching
            CPU-only execution. Mirrors the Makefile's existing
            `quantize-gguf` target's `$(if $(filter ON,$(GGML_CUDA)),-ngl
            $(LLAMA_NGL))` pattern for `llama-imatrix` — this parameter
            lets the same GPU-offload behavior reach `llama-perplexity`.

    Returns:
        Perplexity as a positive float, parsed from llama-perplexity's
        ``Final estimate: PPL ... = <value> +/- <stderr>`` output line.

    Raises:
        FileNotFoundError: If ``gguf_path`` or ``text_path`` does not exist
            on disk.  ``gguf_path`` is checked first; the error message names
            the missing file path explicitly.  Raised BEFORE any subprocess
            call so the check short-circuits on a missing model file without
            attempting to invoke the binary.
        RuntimeError: If llama-perplexity exits with a non-zero return code,
            or if its stdout does not contain the expected PPL output line.
    """
    gguf = Path(gguf_path)
    if not gguf.exists():
        raise FileNotFoundError(
            f"GGUF model file not found: {gguf_path!r}. "
            "Run 'make convert-gguf && make quantize-gguf' to produce it, "
            "or pass the correct --gguf-f16 path."
        )

    text = Path(text_path)
    if not text.exists():
        raise FileNotFoundError(
            f"Perplexity text corpus not found: {text_path!r}. "
            "Run 'make calibration-text' to fetch a corpus, "
            "or pass a valid --text-path."
        )

    cmd = [llama_perplexity_bin, "-m", gguf_path, "-f", text_path]
    if n_gpu_layers > 0:
        cmd += ["-ngl", str(n_gpu_layers)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"llama-perplexity exited with non-zero code {result.returncode}.\n"
            f"  command: {cmd}\n"
            f"  stderr (first 500 chars): {result.stderr[:500]!r}"
        )

    match = _PPL_PATTERN.search(result.stdout)
    if not match:
        raise RuntimeError(
            "llama-perplexity stdout did not contain the expected PPL line.\n"
            f"  pattern: {_PPL_PATTERN.pattern!r}\n"
            f"  stdout (first 500 chars): {result.stdout[:500]!r}"
        )

    return float(match.group(1))
