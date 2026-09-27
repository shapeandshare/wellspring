"""Model format hand-offs between stages (R-11).

HF safetensors (a ``transformers``-loadable directory) is the interchange
format at every stage boundary. MLX conversion happens only on entry to
Track A training; ``mlx_lm.fuse`` of an unquantized base writes an
HF-compatible directory again (verified on TinyLlama, see research.md R-11).
"""

import subprocess
import sys
from pathlib import Path


class NotHFLoadableError(RuntimeError):
    pass


def ensure_hf(model_dir: Path) -> Path:
    model_dir = Path(model_dir)
    if not (model_dir / "config.json").is_file():
        raise NotHFLoadableError(f"{model_dir}: no config.json — not a transformers model directory")
    if not any(model_dir.glob("*.safetensors")):
        raise NotHFLoadableError(f"{model_dir}: no *.safetensors weights — MLX-only or incomplete "
                                 f"(every stage boundary must hand over an HF directory, R-11)")
    try:
        from transformers import AutoConfig
        AutoConfig.from_pretrained(model_dir)
    except (OSError, ValueError, KeyError) as exc:
        raise NotHFLoadableError(f"{model_dir}: transformers cannot read its config: {exc}") from exc
    return model_dir


def to_mlx(hf_dir: Path, mlx_dir: Path) -> Path:
    ensure_hf(hf_dir)
    mlx_dir = Path(mlx_dir)
    if mlx_dir.exists():
        return mlx_dir
    mlx_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp = mlx_dir.with_name(mlx_dir.name + ".tmp")
    if tmp.exists():
        subprocess.run(["rm", "-rf", "--", str(tmp)], check=True)
    subprocess.run([sys.executable, "-m", "mlx_lm", "convert", "--hf-path", str(hf_dir),
                    "--mlx-path", str(tmp)], check=True)
    tmp.rename(mlx_dir)
    return mlx_dir
