"""Tests for scripts/eval_perplexity_gguf.py's compute_perplexity() function.

TDD (T019): these tests were written BEFORE the implementation (RED), then
the implementation was written to make them pass (GREEN).

Covers:
- Happy path: subprocess stdout with the PPL line -> returns float
- Missing gguf_path: FileNotFoundError raised before subprocess is called
- Missing text_path: FileNotFoundError raised before subprocess is called
- Non-zero returncode: RuntimeError raised naming the exit code
- No PPL match in stdout: RuntimeError raised naming the missing pattern
- n_gpu_layers=0 (default): no -ngl flag passed (CPU-only)
- n_gpu_layers>0: -ngl <n> passed to llama-perplexity (GPU offload, mirrors
  the Makefile's existing quantize-gguf/llama-imatrix -ngl pattern)
"""

import subprocess
from types import SimpleNamespace

import pytest

import eval_perplexity_gguf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PPL_LINE = (
    "Final estimate: PPL over 100 chunks for n_ctx=512 = 12.3456 +/- 0.56789\n"
)


def _make_completed_process(stdout: str = "", returncode: int = 0) -> SimpleNamespace:
    """Minimal stand-in for subprocess.CompletedProcess."""
    return SimpleNamespace(stdout=stdout, returncode=returncode, stderr="")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_compute_perplexity_parses_ppl_line(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """compute_perplexity() parses the 'Final estimate: PPL' line and returns float."""
    gguf_path = tmp_path / "model.gguf"
    gguf_path.write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello world", encoding="utf-8")

    monkeypatch.setattr(
        subprocess, "run", lambda *a, **kw: _make_completed_process(stdout=PPL_LINE)
    )

    result = eval_perplexity_gguf.compute_perplexity(
        str(gguf_path),
        str(text_path),
        llama_perplexity_bin="fake-bin",
    )
    assert isinstance(result, float)
    assert result == pytest.approx(12.3456, rel=1e-5)


def test_compute_perplexity_ignores_surrounding_output(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """compute_perplexity() extracts the PPL value even with surrounding log lines."""
    gguf_path = tmp_path / "model.gguf"
    gguf_path.write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello world", encoding="utf-8")

    noisy_output = (
        "llama_model_load: loading model...\n"
        "llama_model_load: n_ctx = 512\n"
        "some progress line\n"
        + PPL_LINE
        + "done.\n"
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **kw: _make_completed_process(stdout=noisy_output)
    )

    result = eval_perplexity_gguf.compute_perplexity(
        str(gguf_path), str(text_path), llama_perplexity_bin="fake-bin"
    )
    assert result == pytest.approx(12.3456, rel=1e-5)


# ---------------------------------------------------------------------------
# Missing-file short-circuits (FileNotFoundError before subprocess is called)
# ---------------------------------------------------------------------------


def test_compute_perplexity_raises_on_missing_gguf(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing gguf_path raises FileNotFoundError without calling subprocess."""
    gguf_path = tmp_path / "nonexistent.gguf"  # deliberately not created
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello world", encoding="utf-8")

    def subprocess_must_not_be_called(*args, **kwargs):
        raise AssertionError(
            "subprocess.run must NOT be called when gguf_path is missing"
        )

    monkeypatch.setattr(subprocess, "run", subprocess_must_not_be_called)

    with pytest.raises(FileNotFoundError) as exc_info:
        eval_perplexity_gguf.compute_perplexity(
            str(gguf_path), str(text_path), llama_perplexity_bin="fake-bin"
        )
    # The error message must name the missing file so the caller knows what to fix.
    assert str(gguf_path) in str(exc_info.value)


def test_compute_perplexity_raises_on_missing_text_path(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing text_path raises FileNotFoundError without calling subprocess."""
    gguf_path = tmp_path / "model.gguf"
    gguf_path.write_bytes(b"placeholder")
    text_path = tmp_path / "nonexistent-text.txt"  # deliberately not created

    def subprocess_must_not_be_called(*args, **kwargs):
        raise AssertionError(
            "subprocess.run must NOT be called when text_path is missing"
        )

    monkeypatch.setattr(subprocess, "run", subprocess_must_not_be_called)

    with pytest.raises(FileNotFoundError) as exc_info:
        eval_perplexity_gguf.compute_perplexity(
            str(gguf_path), str(text_path), llama_perplexity_bin="fake-bin"
        )
    assert str(text_path) in str(exc_info.value)


# ---------------------------------------------------------------------------
# Subprocess error cases
# ---------------------------------------------------------------------------


def test_compute_perplexity_raises_on_nonzero_returncode(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """compute_perplexity() raises RuntimeError when llama-perplexity exits non-zero."""
    gguf_path = tmp_path / "model.gguf"
    gguf_path.write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello world", encoding="utf-8")

    monkeypatch.setattr(
        subprocess, "run", lambda *a, **kw: _make_completed_process(stdout="", returncode=1)
    )

    with pytest.raises(RuntimeError) as exc_info:
        eval_perplexity_gguf.compute_perplexity(
            str(gguf_path), str(text_path), llama_perplexity_bin="fake-bin"
        )
    assert "1" in str(exc_info.value)  # exit code should appear in the message


def test_compute_perplexity_raises_on_no_ppl_match(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """compute_perplexity() raises RuntimeError when PPL line is absent from stdout."""
    gguf_path = tmp_path / "model.gguf"
    gguf_path.write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello world", encoding="utf-8")

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: _make_completed_process(
            stdout="unrecognized output — no PPL line here\n"
        ),
    )

    with pytest.raises(RuntimeError):
        eval_perplexity_gguf.compute_perplexity(
            str(gguf_path), str(text_path), llama_perplexity_bin="fake-bin"
        )


# ---------------------------------------------------------------------------
# GPU offload (-ngl) passthrough
# ---------------------------------------------------------------------------


def test_compute_perplexity_omits_ngl_flag_by_default(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """n_gpu_layers=0 (default): no -ngl flag in the subprocess command
    (CPU-only execution, matching the Makefile's quantize-gguf behavior
    when GGML_CUDA=OFF)."""
    gguf_path = tmp_path / "model.gguf"
    gguf_path.write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello world", encoding="utf-8")

    captured_cmd: list = []

    def fake_run(cmd, *a, **kw):
        captured_cmd.extend(cmd)
        return _make_completed_process(stdout=PPL_LINE)

    monkeypatch.setattr(subprocess, "run", fake_run)

    eval_perplexity_gguf.compute_perplexity(
        str(gguf_path), str(text_path), llama_perplexity_bin="fake-bin"
    )
    assert "-ngl" not in captured_cmd


def test_compute_perplexity_passes_ngl_flag_when_gpu_layers_positive(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """n_gpu_layers>0: -ngl <n> is appended to the llama-perplexity command,
    mirroring the Makefile's `$(if $(filter ON,$(GGML_CUDA)),-ngl
    $(LLAMA_NGL))` pattern already used for llama-imatrix in quantize-gguf."""
    gguf_path = tmp_path / "model.gguf"
    gguf_path.write_bytes(b"placeholder")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello world", encoding="utf-8")

    captured_cmd: list = []

    def fake_run(cmd, *a, **kw):
        captured_cmd.extend(cmd)
        return _make_completed_process(stdout=PPL_LINE)

    monkeypatch.setattr(subprocess, "run", fake_run)

    eval_perplexity_gguf.compute_perplexity(
        str(gguf_path),
        str(text_path),
        llama_perplexity_bin="fake-bin",
        n_gpu_layers=999,
    )
    assert "-ngl" in captured_cmd
    ngl_index = captured_cmd.index("-ngl")
    assert captured_cmd[ngl_index + 1] == "999"
