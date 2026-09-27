"""Pick the fine-tuning implementation for this host (FR-006, R-4, R-11).

Track A: HF base -> MLX (``formats.to_mlx``) -> the existing
``train_variants.sh`` (mlx_lm.lora + fuse) -> check the fused dirs are
HF-loadable. Track B: ``train_torch`` per variant. Either way the recipe
stamp records the platform, and the outputs are HF directories.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from finetune.formats import ensure_hf, to_mlx
from finetune.hostplatform import Track
from finetune.train_torch import RECIPE_STAMP, Recipe, train_variant_torch

TRAIN_SCRIPT = Path(__file__).resolve().parent / "train_variants.sh"


def _variants(datasets: Path) -> list[str]:
    return sorted(p.name for p in datasets.iterdir() if p.is_dir())


def _stamp_platform(model_dir: Path, platform: Track) -> None:
    stamp_path = model_dir / RECIPE_STAMP
    stamp = json.loads(stamp_path.read_text()) if stamp_path.is_file() else {}
    stamp["platform"] = platform
    stamp_path.write_text(json.dumps(stamp, indent=2) + "\n")


def train_lineup(base_hf: Path, datasets: Path, models: Path, recipe: Recipe,
                 platform: Track, work_dir: Path) -> list[Path]:
    variants = _variants(datasets)
    if platform == "track_b":
        return [train_variant_torch(base_hf, datasets / v, models, recipe, v) for v in variants]

    # Same basename as the HF base, so the recipe stamp's base_name matches what
    # preflight/weight_diff are later given as --base (the HF directory).
    mlx_base = to_mlx(base_hf, work_dir / "mlx-base" / Path(base_hf).name)
    # train_variants.sh invokes `python -m mlx_lm ...`; make that this interpreter's env.
    path = f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}"
    env = {**os.environ, "PATH": path, "BASE": str(mlx_base), "DATA": str(datasets), "MODELS": str(models),
           "ADAPTERS": str(work_dir / "adapters"), "ITERS": str(recipe.iters),
           "LR": f"{recipe.learning_rate:g}", "BATCH": str(recipe.batch_size),
           "NUM_LAYERS": str(recipe.num_layers), "FT_TYPE": recipe.fine_tune_type}
    subprocess.run(["bash", str(TRAIN_SCRIPT)], env=env, check=True)
    outs = []
    for v in variants:
        out = ensure_hf(models / v)
        _stamp_platform(out, platform)
        outs.append(out)
    return outs
