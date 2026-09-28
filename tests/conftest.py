"""Shared pytest fixtures/config for Wellspring's test suite.

``src/scripts/`` is invoked directly by the Makefile (``python src/scripts/foo.py``),
not imported as an installed package, so it isn't on ``sys.path`` by
default under pytest's import mode. Add it once here rather than having
every test module repeat a path hack -- see the constitution's Article XI
(Package Ownership & One Class Per File) for why ``src/scripts/`` isn't a
proper ``__init__.py``-owned package yet.

This module also installs the **hermetic guard** (Article IX Rule 5, spec 004 US3)
so ``make test`` provably needs no network, no Apple Silicon and no GPU:

* ``mlx``/``mlx_lm`` imports are blocked by a :class:`MetaPathFinder` installed at
  conftest import time, so the block also applies during collection -- that is when
  ``pytest.importorskip("mlx.core")`` runs. It raises ``ModuleNotFoundError``, which is
  what pytest 9.1's ``importorskip`` catches by default, so an MLX-only test file skips
  cleanly instead of erroring.
* Network access and torch CUDA/MPS device use are blocked per-test by an autouse
  fixture. Plain CPU-only torch is deliberately left working -- several tests already
  run real CPU torch under ``make test`` (spec 004 clarification #5).
"""

import importlib.abc
import importlib.machinery
import importlib.util
import os
import socket
import sys
from pathlib import Path
from typing import Any

import pytest

# Force HuggingFace offline for the whole suite (Article IX Rule 5). This must happen at
# conftest import time, before anything imports huggingface_hub: that library reads
# HF_HUB_OFFLINE into a module constant at import, so setting it later (as make_tiny_hf_model
# used to) is too late. Before this line the suite silently made network calls from
# `AutoTokenizer.from_pretrained` (transformers' list_repo_templates -> hf_api.list_repo_tree)
# even though those tests were assumed offline.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# The fine-tuning domain lives in a repo-root package (``src/finetune/``) and is
# imported as ``finetune.<module>``, so the repo root must be importable too.
REPO_ROOT = SCRIPTS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))


TINY_TOKENIZER_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


# ---------------------------------------------------------------------------
# Hermetic guard (Article IX Rule 5; spec 004 US3 / FR-004)
# ---------------------------------------------------------------------------

_BLOCKED_MODULES = ("mlx", "mlx_lm")

# `make test-mlx` (the Article IX Rule 5 Apple-Silicon target) sets WELLSPRING_ALLOW_MLX=1
# to run the MLX tests with the import block lifted. `make test` never sets it, so the
# block is always on for the hermetic suite.
_ALLOW_MLX = bool(os.environ.get("WELLSPRING_ALLOW_MLX"))


class _UnavailableLoader(importlib.abc.Loader):
    """A loader that fails only when the module is actually imported.

    ``find_spec`` must keep returning a spec (not raising): libraries such as
    transformers/peft *probe* mlx availability with ``importlib.util.find_spec``, and a
    finder that raised would break importing them. Raising at exec time means
    ``import mlx`` fails (and ``pytest.importorskip`` still skips cleanly), while an
    availability probe just sees a spec and, when it actually tries to import, gets an
    ordinary ``ModuleNotFoundError`` it can catch.
    """

    def __init__(self, fullname: str) -> None:
        self._fullname = fullname

    def create_module(self, spec: Any) -> None:
        return None

    def exec_module(self, module: Any) -> None:
        raise ModuleNotFoundError(
            f"hermetic guard (Article IX Rule 5): refusing to import {self._fullname!r} under "
            "`make test`. mlx/mlx_lm are Apple-Silicon-only; keep them behind "
            "pytest.importorskip, or use the explicitly named end-to-end target. "
            "See specs/004-test-suite-backfill/.",
            name=self._fullname,
        )


class _MlxImportBlocker(importlib.abc.MetaPathFinder):
    """Resolve ``mlx``/``mlx_lm`` (and submodules) to a loader that refuses to run."""

    def find_spec(self, fullname: str, path: Any = None,
                  target: Any = None) -> importlib.machinery.ModuleSpec | None:
        if fullname.split(".")[0] in _BLOCKED_MODULES:
            return importlib.util.spec_from_loader(fullname, _UnavailableLoader(fullname))
        return None


if not _ALLOW_MLX:
    sys.meta_path.insert(0, _MlxImportBlocker())

_LOOPBACK = {"127.0.0.1", "::1", "localhost", ""}
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _blocked_network(self: socket.socket, address: Any, *args: Any, **kwargs: Any) -> Any:
    host = address[0] if isinstance(address, tuple) and address else None
    if host in _LOOPBACK or getattr(address, "family", None) == getattr(socket, "AF_UNIX", None):
        return _real_connect(self, address, *args, **kwargs)
    raise RuntimeError("hermetic guard (Article IX Rule 5): network access attempted under "
                       "`make test`.")


def _blocked_network_ex(self: socket.socket, address: Any, *args: Any, **kwargs: Any) -> Any:
    host = address[0] if isinstance(address, tuple) and address else None
    if host in _LOOPBACK or getattr(address, "family", None) == getattr(socket, "AF_UNIX", None):
        return _real_connect_ex(self, address, *args, **kwargs)
    raise RuntimeError("hermetic guard (Article IX Rule 5): network access attempted under "
                       "`make test`.")


def _device_error(which: str) -> RuntimeError:
    return RuntimeError(f"hermetic guard (Article IX Rule 5): torch {which} device is not allowed "
                        "under `make test` (no GPU).")


def _install_torch_guard(monkeypatch: pytest.MonkeyPatch, torch: Any) -> None:
    """Forbid CUDA/MPS *device use* while leaving CPU-only torch fully working."""
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    mps = getattr(getattr(torch, "backends", None), "mps", None)
    if mps is not None:
        monkeypatch.setattr(mps, "is_available", lambda: False)

    tensor = torch.Tensor
    real_to = tensor.to

    def guarded_to(self: Any, *args: Any, **kwargs: Any) -> Any:
        device = kwargs.get("device")
        if device is None and args and isinstance(args[0], str):
            device = args[0]
        if isinstance(device, str) and device.split(":")[0] in ("cuda", "mps"):
            raise _device_error(device)
        return real_to(self, *args, **kwargs)

    def make_raiser(which: str):
        def _raise(self: Any, *args: Any, **kwargs: Any) -> Any:
            raise _device_error(which)
        return _raise

    monkeypatch.setattr(tensor, "to", guarded_to)
    for which in ("cuda", "mps"):
        if hasattr(tensor, which):
            monkeypatch.setattr(tensor, which, make_raiser(which))


@pytest.fixture(autouse=True)
def _hermetic_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Block network access and torch GPU/MPS device use for every test."""
    monkeypatch.setattr(socket.socket, "connect", _blocked_network)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked_network_ex)

    torch = sys.modules.get("torch")
    if torch is not None:
        _install_torch_guard(monkeypatch, torch)


def make_tiny_hf_model(dst: Path, with_tokenizer: bool = True) -> Path:
    """Save a tiny random Llama (+ the cached TinyLlama tokenizer) to ``dst``.

    Skips the calling test when transformers, or (for ``with_tokenizer``) the
    tokenizer in the local HF cache, is unavailable. No network is used.
    """
    import os

    transformers = pytest.importorskip("transformers")
    vocab = 64
    if with_tokenizer:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        try:
            tok = transformers.AutoTokenizer.from_pretrained(TINY_TOKENIZER_ID)
        except OSError:
            pytest.skip(f"{TINY_TOKENIZER_ID} tokenizer not in the local HF cache")
        tok.save_pretrained(dst)
        vocab = len(tok)
    cfg = transformers.LlamaConfig(vocab_size=vocab, hidden_size=16, intermediate_size=32,
                                   num_hidden_layers=2, num_attention_heads=2,
                                   num_key_value_heads=2, max_position_embeddings=128)
    transformers.LlamaForCausalLM(cfg).save_pretrained(dst)
    return dst
