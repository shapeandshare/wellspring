#!/usr/bin/env python3
"""Measure perplexity of an MLX-format model checkpoint against a plain-text corpus.

Public API
----------
compute_perplexity(mlx_path, text_path, sequence_length=512, batch_size=8) -> float

Reads the UTF-8 plain-text file at ``text_path``, tokenises it with the
checkpoint's own tokenizer, chunks the token list into fixed-length windows
of ``sequence_length``, and evaluates cross-entropy perplexity against the
checkpoint's text-only language model.

Real-fixture correction (2026-09-25)
-------------------------------------
An earlier version of this module used ``mlx_lm.utils.load()`` based on a
feasibility spike that only reasoned from source inspection, never against
a real ``make convert-mlx`` output. Running this module against a REAL
checkpoint (TinyLlama, converted via the actual `make convert-mlx` /
`mlx_vlm.convert` pipeline this project uses) surfaced a load-bearing bug:
``make convert-mlx`` always invokes ``mlx_vlm.convert`` (confirmed:
Makefile's ``MLX_CONVERT := $(VENV)/bin/mlx_vlm.convert``), which always
saves weights with a ``language_model.*`` prefix -- even for a plain,
non-VLM text model. ``mlx_lm.utils.load()`` expects unprefixed
``model.layers.*`` keys and raises ``ValueError("Received 513 parameters
not in model: ...")`` for EVERY checkpoint this project's own pipeline
produces, not just genuine VLM checkpoints as the original spike assumed.

Confirmed fix, verified against the real checkpoint: use
``mlx_vlm.utils.load()`` (not ``mlx_lm.utils.load()``) unconditionally --
every ``convert-mlx`` output is an mlx_vlm-format checkpoint by
construction, whether or not the source model is actually multimodal.
``mlx_vlm.utils.load()`` returns ``(model, processor)`` where
``model.language_model`` is the callable text-only transformer (its
``sanitize()``/loading path strips or ignores any vision tower for
text-only source models, and exposes the real vision tower for genuine
VLM checkpoints -- either way, `.language_model` is the correct text-only
submodule to evaluate perplexity against). ``model.language_model(tokens)``
returns a ``LanguageModelOutput`` with a ``.logits`` attribute (not a bare
array, unlike ``mlx_lm``'s convention) -- this module's own cross-entropy
loop accounts for that directly rather than reusing
``mlx_lm.perplexity.eval_ppl`` (which assumes a bare-array-returning
model).  ``processor.encode(text) -> list[int]`` works identically to a
plain tokenizer's ``.encode()``.

Verified manually against a real TinyLlama-1.1B checkpoint produced by
this project's actual `make convert-mlx`: perplexity computed correctly
(~3.1 on a short synthetic corpus), no MlxPerplexityUnsupportedError.
"""
from __future__ import annotations

import math
from pathlib import Path


class MlxPerplexityUnsupportedError(Exception):
    """Raised when the MLX checkpoint cannot be evaluated for perplexity.

    Triggered when ``mlx_vlm.utils.load()`` itself raises (e.g. a
    genuinely malformed or unrecognized checkpoint directory). Callers
    should handle this exception rather than catching the raw underlying
    exception from mlx_vlm.
    """


def _tokenize_and_window(
    text: str,
    tokenizer,
    sequence_length: int,
):
    """Tokenise ``text`` and chunk into fixed-length windows.

    Args:
        text: Plain UTF-8 text to tokenise.
        tokenizer: Any object with an ``.encode(text) -> list[int]`` method
            (e.g. the ``processor`` returned by ``mlx_vlm.utils.load()``).
        sequence_length: Number of tokens per window.

    Returns:
        An ``mx.array`` of shape ``(num_windows, sequence_length)``.
        Windows are non-overlapping; any trailing tokens that do not fill a
        complete window are discarded.  Returns an array with ``shape[0] == 0``
        if ``len(tokens) < sequence_length``.
    """
    import mlx.core as mx

    tokens: list[int] = tokenizer.encode(text)
    n_windows = len(tokens) // sequence_length
    if n_windows == 0:
        # Return an empty array with the right number of columns
        return mx.array([], dtype=mx.uint32).reshape(0, sequence_length)

    truncated = tokens[: n_windows * sequence_length]
    return mx.array(truncated, dtype=mx.uint32).reshape(n_windows, sequence_length)


def compute_perplexity(
    mlx_path: str,
    text_path: str,
    sequence_length: int = 512,
    batch_size: int = 8,
) -> float:
    """Evaluate perplexity of an MLX checkpoint against a plain-text corpus.

    Args:
        mlx_path: Path to an MLX-format model directory (as produced by
            ``make convert-mlx``, i.e. always an ``mlx_vlm``-format
            checkpoint by construction, regardless of whether the source
            model is genuinely multimodal).
        text_path: Path to a UTF-8 plain-text file used as the evaluation
            corpus.
        sequence_length: Number of tokens per evaluation window.  Default 512.
        batch_size: Number of windows evaluated per forward-pass batch.
            Default 8.

    Returns:
        Perplexity as a ``float``.

    Raises:
        MlxPerplexityUnsupportedError: If ``mlx_vlm.utils.load()`` cannot
            load the checkpoint at all (e.g. a malformed directory).
        FileNotFoundError: If ``text_path`` does not exist (propagated from
            ``Path.read_text``).
    """
    import mlx.core as mx
    import mlx.nn as nn
    import mlx_vlm.utils as _mlx_vlm_utils

    try:
        model, processor = _mlx_vlm_utils.load(mlx_path)
    except Exception as exc:
        raise MlxPerplexityUnsupportedError(
            f"Cannot evaluate perplexity: mlx_vlm could not load the checkpoint "
            f"at {mlx_path!r}. Original error: {exc}"
        ) from exc

    language_model = model.language_model

    text = Path(text_path).read_text(encoding="utf-8")
    data = _tokenize_and_window(text, processor, sequence_length)

    if data.shape[0] == 0:
        raise ValueError(
            f"Text corpus at {text_path!r} produced zero full "
            f"{sequence_length}-token windows -- provide a longer corpus."
        )

    all_losses = []
    for start in range(0, data.shape[0], batch_size):
        batch = data[start : start + batch_size]
        output = language_model(batch[:, :-1])
        logits = output.logits.astype(mx.float32)
        losses = nn.losses.cross_entropy(logits, batch[:, 1:], reduction="none")
        mx.eval(losses)
        all_losses.append(losses.flatten())

    all_losses_concat = mx.concatenate(all_losses)
    mean_loss = all_losses_concat.mean().item()
    return math.exp(mean_loss)
