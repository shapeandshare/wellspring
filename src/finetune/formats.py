"""Model format hand-offs between stages (R-11).

HF safetensors (a ``transformers``-loadable directory) is the interchange
format at every stage boundary. MLX conversion happens only on entry to
Track A training; ``mlx_lm.fuse`` of an unquantized base writes an
HF-compatible directory again (verified on TinyLlama, see research.md R-11).
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

FINGERPRINT = ".source-fingerprint.json"


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


def source_fingerprint(hf_dir: Path) -> dict[str, object]:
    """Identify the HF weights a cache was built from: config bytes plus each shard's size and mtime.

    Hashing multi-GB shards on every run would cost minutes; size + mtime_ns catches a replaced or
    regenerated base at the same path, which is the failure this guards against.
    """
    hf_dir = Path(hf_dir)
    return {
        "config_sha256": hashlib.sha256((hf_dir / "config.json").read_bytes()).hexdigest(),
        "shards": {p.name: [p.stat().st_size, p.stat().st_mtime_ns]
                   for p in sorted(hf_dir.glob("*.safetensors"))},
    }


def to_mlx(hf_dir: Path, mlx_dir: Path) -> Path:
    ensure_hf(hf_dir)
    mlx_dir = Path(mlx_dir)
    want = source_fingerprint(hf_dir)
    stamp = mlx_dir / FINGERPRINT
    if stamp.is_file() and json.loads(stamp.read_text()) == want:
        return mlx_dir
    mlx_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp = mlx_dir.with_name(mlx_dir.name + ".tmp")
    if tmp.exists():
        subprocess.run(["rm", "-rf", "--", str(tmp)], check=True)
    subprocess.run([sys.executable, "-m", "mlx_lm", "convert", "--hf-path", str(hf_dir),
                    "--mlx-path", str(tmp)], check=True)
    (tmp / FINGERPRINT).write_text(json.dumps(want, indent=2) + "\n")
    if mlx_dir.exists():
        shutil.rmtree(mlx_dir)  # stale or unstamped cache; the new build is already complete in tmp
    tmp.rename(mlx_dir)
    return mlx_dir
