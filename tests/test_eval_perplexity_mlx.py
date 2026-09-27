"""Tests for src/scripts/eval_perplexity_mlx.py.

Real-fixture correction (2026-09-25): the original version of this test
suite mocked ``mlx_lm.utils.load`` based on a feasibility spike that was
never actually run against a real ``make convert-mlx`` output. Running
against a REAL TinyLlama checkpoint (produced by this project's actual
`make convert-mlx` pipeline, which always uses `mlx_vlm.convert`) surfaced
that `mlx_lm.utils.load()` fails for EVERY checkpoint this project
produces -- `make convert-mlx` always saves `language_model.*`-prefixed
weights via mlx_vlm, which `mlx_lm.utils.load()` cannot read regardless of
whether the source model is a genuine VLM. `mlx_vlm.utils.load()` is the
correct loader unconditionally; verified manually against the real
checkpoint (perplexity ~3.1 on a short corpus, no exception). This test
suite now mocks `mlx_vlm.utils.load` instead, matching the corrected
implementation.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from eval_perplexity_mlx import (
    MlxPerplexityUnsupportedError,
    _tokenize_and_window,
    compute_perplexity,
)


# ---------------------------------------------------------------------------
# Helper: tiny text fixture file
# ---------------------------------------------------------------------------
TEXT_SAMPLE = "The quick brown fox jumps over the lazy dog. " * 20


@pytest.fixture()
def text_file(tmp_path: Path) -> Path:
    """A small plain-text file usable as text_path in compute_perplexity."""
    p = tmp_path / "sample.txt"
    p.write_text(TEXT_SAMPLE, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. Load-failure path: mlx_vlm.utils.load raises -> MlxPerplexityUnsupportedError
# ---------------------------------------------------------------------------

def test_load_failure_raises_typed_error(text_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If mlx_vlm.utils.load raises, compute_perplexity re-raises as our typed error."""
    monkeypatch.setattr(
        "mlx_vlm.utils.load",
        lambda *a, **kw: (_ for _ in ()).throw(
            ValueError("malformed checkpoint directory")
        ),
    )
    with pytest.raises(MlxPerplexityUnsupportedError):
        compute_perplexity("/fake/checkpoint", str(text_file))


def test_load_failure_does_not_leak_raw_exception(
    text_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The raw exception from mlx_vlm must never propagate uncaught."""
    monkeypatch.setattr(
        "mlx_vlm.utils.load",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(MlxPerplexityUnsupportedError):
        compute_perplexity("/fake/checkpoint", str(text_file))


# ---------------------------------------------------------------------------
# 2. Tokenization / windowing helper
# ---------------------------------------------------------------------------

class _MockTokenizer:
    """Minimal stub: .encode(text) -> list[int]."""

    def encode(self, text: str) -> list[int]:
        # Return one token per character for deterministic testing
        return [ord(c) for c in text]


def test_tokenize_and_window_basic() -> None:
    """_tokenize_and_window chunks correctly and drops the incomplete tail."""
    tok = _MockTokenizer()
    text = "A" * 20  # 20 tokens
    result = _tokenize_and_window(text, tok, sequence_length=8)
    # 20 // 8 = 2 complete windows, remainder 4 dropped
    assert result.shape == (2, 8), f"Expected (2, 8), got {result.shape}"


def test_tokenize_and_window_drops_remainder() -> None:
    tok = _MockTokenizer()
    text = "X" * 17  # 17 tokens, 17//5 = 3 windows, 2 remainder dropped
    result = _tokenize_and_window(text, tok, sequence_length=5)
    assert result.shape == (3, 5)


def test_tokenize_and_window_exact_multiple() -> None:
    tok = _MockTokenizer()
    text = "Y" * 12  # exactly 4 windows of size 3
    result = _tokenize_and_window(text, tok, sequence_length=3)
    assert result.shape == (4, 3)


def test_tokenize_and_window_too_short_returns_empty() -> None:
    """Text shorter than one window produces an empty array (0 windows)."""
    tok = _MockTokenizer()
    text = "AB"  # 2 tokens, sequence_length=8 -> 0 windows
    result = _tokenize_and_window(text, tok, sequence_length=8)
    assert result.shape[0] == 0


# ---------------------------------------------------------------------------
# 3. compute_perplexity with mocked mlx_vlm.utils.load + a real language_model
#    forward pass -- everything downstream of load() is genuine MLX/mlx.nn
#    computation, not mocked, so these tests exercise the real cross-entropy
#    loop this module actually runs.
# ---------------------------------------------------------------------------

class _FakeLanguageModelOutput:
    def __init__(self, logits):
        self.logits = logits


class _FakeLanguageModel:
    """A tiny linear "language model" producing real MLX logits, so the
    cross-entropy/perplexity math in compute_perplexity is genuinely
    exercised end-to-end (not mocked past the load() call)."""

    def __init__(self, vocab_size: int = 50):
        import mlx.core as mx

        self.vocab_size = vocab_size
        # Fixed "random" projection so results are deterministic across runs.
        mx.random.seed(0)
        self._proj = mx.random.normal((vocab_size, vocab_size)) * 0.01

    def __call__(self, tokens):
        import mlx.core as mx

        # tokens: (batch, seq_len) int array. Produce (batch, seq_len, vocab)
        # logits via a fixed embedding-lookup-like projection.
        one_hot = mx.zeros((tokens.shape[0], tokens.shape[1], self.vocab_size))
        # Simple deterministic logits: use token id modulo vocab_size as a
        # one-hot-ish signal scaled through the fixed projection.
        idx = tokens % self.vocab_size
        one_hot = mx.eye(self.vocab_size)[idx]
        logits = one_hot @ self._proj
        return _FakeLanguageModelOutput(logits)


class _FakeVlmModel:
    def __init__(self, vocab_size: int = 50):
        self.language_model = _FakeLanguageModel(vocab_size)


def _make_mock_load(vocab_size: int = 50):
    mock_processor = MagicMock()
    mock_processor.encode.side_effect = lambda text: [
        (i % vocab_size) for i in range(len(text.split()) * 20)
    ]

    def fake_load(path, *a, **kw):
        return _FakeVlmModel(vocab_size), mock_processor

    return fake_load, mock_processor


def test_compute_perplexity_returns_positive_float(
    text_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """With mocked load() but a real forward pass, compute_perplexity
    returns a genuine positive perplexity float."""
    fake_load, mock_processor = _make_mock_load()
    mock_processor.encode.side_effect = lambda text: list(range(600))

    monkeypatch.setattr("mlx_vlm.utils.load", fake_load)

    result = compute_perplexity(str(tmp_path), str(text_file), sequence_length=32)

    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert result > 0


def test_compute_perplexity_result_is_finite(
    text_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """compute_perplexity must return a finite, strictly positive float."""
    import math

    fake_load, mock_processor = _make_mock_load()
    mock_processor.encode.side_effect = lambda text: list(range(700))

    monkeypatch.setattr("mlx_vlm.utils.load", fake_load)

    result = compute_perplexity(str(tmp_path), str(text_file), sequence_length=32)
    assert result > 0
    assert math.isfinite(result)


def test_compute_perplexity_return_type_is_not_a_tuple(
    text_file: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """compute_perplexity returns only the PPL float, never a tuple."""
    fake_load, mock_processor = _make_mock_load()
    mock_processor.encode.side_effect = lambda text: list(range(600))

    monkeypatch.setattr("mlx_vlm.utils.load", fake_load)

    result = compute_perplexity(str(tmp_path), str(text_file), sequence_length=32)
    assert not isinstance(result, tuple)
    assert isinstance(result, float)


def test_compute_perplexity_reads_text_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """compute_perplexity reads the actual text_path file (not a hardcoded string)."""
    text_p = tmp_path / "corpus.txt"
    text_p.write_text("hello world " * 100, encoding="utf-8")

    captured_texts: list[str] = []

    def fake_load(path, *a, **kw):
        mock_processor = MagicMock()

        def capture_encode(text: str) -> list[int]:
            captured_texts.append(text)
            return list(range(600))

        mock_processor.encode.side_effect = capture_encode
        return _FakeVlmModel(), mock_processor

    monkeypatch.setattr("mlx_vlm.utils.load", fake_load)

    result = compute_perplexity(str(tmp_path), str(text_p), sequence_length=32)

    assert len(captured_texts) == 1
    assert "hello world" in captured_texts[0]
    assert result > 0


def test_compute_perplexity_raises_on_empty_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A text corpus too short to fill even one window raises a clear error,
    rather than silently computing perplexity over zero windows."""
    text_p = tmp_path / "tiny.txt"
    text_p.write_text("hi", encoding="utf-8")

    fake_load, mock_processor = _make_mock_load()
    mock_processor.encode.side_effect = lambda text: [1, 2]  # only 2 tokens

    monkeypatch.setattr("mlx_vlm.utils.load", fake_load)

    with pytest.raises(ValueError):
        compute_perplexity(str(tmp_path), str(text_p), sequence_length=512)
