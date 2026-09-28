"""Proves the hermetic guard itself can fail (Article VIII Rule 5; spec 004 US3).

A gate that cannot fail is not a gate. Each test below deliberately triggers one
guarded behaviour and requires the named error — so a green run of this file means
the guard is actually installed, not merely documented.

The mlx check uses ``__import__("mlx")`` rather than an ``import mlx`` statement
because a statement at module scope would abort collection; ``__import__`` is exactly
what the statement compiles to.

``torch`` is imported at module scope (via ``importorskip``) so it is already in
``sys.modules`` when the autouse guard fixture runs; the guard only patches torch when
it is loaded and never forces the import itself.
"""

from __future__ import annotations

import socket

import pytest

torch = pytest.importorskip("torch")


def test_guard_blocks_network_access() -> None:
    with socket.socket() as s:
        with pytest.raises(RuntimeError, match="hermetic guard.*network"):
            s.connect(("1.1.1.1", 80))


def test_guard_blocks_network_access_via_connect_ex() -> None:
    with socket.socket() as s:
        with pytest.raises(RuntimeError, match="hermetic guard.*network"):
            s.connect_ex(("1.1.1.1", 80))


def test_guard_blocks_mlx_import() -> None:
    with pytest.raises(ModuleNotFoundError, match="hermetic guard"):
        __import__("mlx")


def test_guard_blocks_mlx_lm_import() -> None:
    with pytest.raises(ModuleNotFoundError, match="hermetic guard"):
        __import__("mlx_lm")


def test_importorskip_mlx_still_skips_cleanly() -> None:
    """The guard's exception type must satisfy pytest.importorskip (T018 spike)."""
    with pytest.raises(pytest.skip.Exception):
        pytest.importorskip("mlx.core")


def test_guard_blocks_cuda_device() -> None:
    with pytest.raises(RuntimeError, match="hermetic guard.*torch cuda"):
        torch.zeros(1).to("cuda")


def test_guard_blocks_mps_device() -> None:
    with pytest.raises(RuntimeError, match="hermetic guard.*torch mps"):
        torch.zeros(1).to("mps")


def test_guard_reports_cuda_unavailable() -> None:
    assert torch.cuda.is_available() is False


def test_cpu_only_torch_still_works() -> None:
    """The guard must not break plain CPU-tensor torch (spec 004 clarification #5)."""
    assert float((torch.zeros(2).to("cpu") + 1).sum()) == 2.0
