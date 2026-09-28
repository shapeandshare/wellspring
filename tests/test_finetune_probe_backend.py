"""probe.py runs on both tracks: MLX on Apple Silicon, torch elsewhere (FR-006, R-5)."""

import types
from pathlib import Path
from typing import Any

import pytest

from conftest import make_tiny_hf_model
from finetune import probe


def test_backend_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FT_PROBE_BACKEND", raising=False)
    monkeypatch.setattr(probe.platform, "system", lambda: "Linux")
    monkeypatch.setattr(probe.platform, "machine", lambda: "x86_64")
    assert probe._backend() == "torch"
    monkeypatch.setattr(probe.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(probe.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(probe.importlib.util, "find_spec", lambda name: object())
    assert probe._backend() == "mlx"
    monkeypatch.setenv("FT_PROBE_BACKEND", "torch")
    assert probe._backend() == "torch"


def test_load_and_gen_route_to_torch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[Any] = []
    fake = types.SimpleNamespace(
        load=lambda p: calls.append(("load", p)) or ("M", "T"),
        generate=lambda m, t, prompt, max_tokens: calls.append(("gen", prompt, max_tokens)) or "out")
    monkeypatch.setattr(probe, "_backend", lambda: "torch")
    monkeypatch.setattr(probe, "_probe_torch", lambda: fake)
    monkeypatch.setattr(probe, "_render_prompt", lambda tok, q, o=None: f"<{q}>")
    (tmp_path / "config.json").write_text("{}")
    assert probe._load(str(tmp_path)) == ("M", "T")
    assert probe._gen("M", "T", "hi", max_tokens=7) == "out"
    assert calls == [("load", str(tmp_path)), ("gen", "<hi>", 7)]


def test_torch_generate_is_greedy_and_returns_only_new_text(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    from finetune import probe_torch
    d = make_tiny_hf_model(tmp_path / "m")
    model, tok = probe_torch.load(str(d))
    a = probe_torch.generate(model, tok, "Hello there", max_tokens=5)
    b = probe_torch.generate(model, tok, "Hello there", max_tokens=5)
    assert isinstance(a, str) and a == b
    assert not a.startswith("Hello there")


def test_render_prompt_uses_hf_tokenizer_chat_template(tmp_path: Path) -> None:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(make_tiny_hf_model(tmp_path / "m"))
    assert "<|user|>" in probe._render_prompt(tok, "hi")
