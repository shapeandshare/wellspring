"""HF safetensors is the interchange format at every stage boundary (R-11)."""

import json
import platform
from pathlib import Path

import pytest

from conftest import make_tiny_hf_model
from finetune.formats import NotHFLoadableError, ensure_hf, to_mlx

REPO_ROOT = Path(__file__).resolve().parent.parent


def _tiny_hf(dst: Path, with_tokenizer: bool = False) -> Path:
    return make_tiny_hf_model(dst, with_tokenizer=with_tokenizer)


def test_ensure_hf_accepts_a_transformers_save(tmp_path: Path) -> None:
    assert ensure_hf(_tiny_hf(tmp_path / "m")) == tmp_path / "m"


def test_ensure_hf_rejects_dir_without_weights(tmp_path: Path) -> None:
    d = tmp_path / "mlxonly"
    d.mkdir()
    (d / "config.json").write_text(json.dumps({"model_type": "llama"}))
    (d / "weights.npz").write_bytes(b"")
    with pytest.raises(NotHFLoadableError):
        ensure_hf(d)


def test_ensure_hf_rejects_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(NotHFLoadableError):
        ensure_hf(tmp_path / "nope")


@pytest.mark.skipif(platform.system() != "Darwin" or platform.machine() != "arm64",
                    reason="MLX is Apple Silicon only")
def test_to_mlx_then_back_is_hf_loadable(tmp_path: Path) -> None:
    pytest.importorskip("mlx_lm")
    out = to_mlx(_tiny_hf(tmp_path / "hf", with_tokenizer=True), tmp_path / "mlx")
    assert (out / "config.json").is_file()
    assert ensure_hf(out) == out
