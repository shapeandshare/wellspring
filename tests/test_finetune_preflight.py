"""ft-preflight checks the dependencies of the track this host runs (Track A MLX, Track B torch)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from finetune import preflight  # noqa: E402
from finetune.hostplatform import UnsupportedPlatformError  # noqa: E402


def _rows(monkeypatch: pytest.MonkeyPatch, track: str | Exception, have: set[str]) -> list[tuple[str, str, str]]:
    def detect() -> str:
        if isinstance(track, Exception):
            raise track
        return track

    def fake_import(name: str) -> object:
        if name not in have:
            raise ImportError(name)
        return object()

    monkeypatch.setattr(preflight, "detect_platform", detect)
    monkeypatch.setattr(preflight, "_import", fake_import)
    r = preflight.Report()
    preflight.check_platform(r)
    preflight.check_env(r)
    return r.rows


def test_track_b_host_passes_with_torch_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, "track_b", {"torch", "peft", "transformers", "numpy", "safetensors", "matplotlib"})
    assert all(status != preflight.BAD for status, _, _ in rows), rows
    assert not any("mlx" in what for _, what, _ in rows)


def test_track_b_host_fails_without_peft(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, "track_b", {"torch", "transformers", "numpy", "safetensors", "matplotlib"})
    assert (preflight.BAD, "peft importable") in [(s, w) for s, w, _ in rows]


def test_track_a_host_requires_mlx_lm(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, "track_a", {"numpy", "safetensors", "matplotlib"})
    assert (preflight.BAD, "mlx-lm importable") in [(s, w) for s, w, _ in rows]


def test_unsupported_host_fails_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = _rows(monkeypatch, UnsupportedPlatformError("Linux/x86_64 with CUDA=no"), set())
    assert rows[0][0] == preflight.BAD and rows[0][1] == "platform"
