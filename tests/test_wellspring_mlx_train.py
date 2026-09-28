"""Track A lineup training (ported from ``src/finetune/train_variants.sh``; Article XV parity)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from wellspring.finetune.dtos.mlx_train_request_dto import MlxTrainRequestDto
from wellspring.finetune.enums.fine_tune_type import FineTuneType
from wellspring.finetune.errors.base_model_missing_error import BaseModelMissingError
from wellspring.finetune.services.mlx_train_service import MlxTrainService

REPO_ROOT = Path(__file__).resolve().parent.parent


class FakeMlx:
    """Records calls; ``fuse`` creates the save dir like mlx_lm.fuse does."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def lora(self, request: MlxTrainRequestDto, data: Path, adapter: Path) -> None:
        self.calls.append(("lora", {"data": data, "adapter": adapter, "iters": request.iters,
                                    "lr": request.learning_rate, "layers": request.num_layers}))

    async def fuse(self, base: Path, adapter: Path, save: Path) -> None:
        save.mkdir(parents=True)
        self.calls.append(("fuse", {"base": base, "adapter": adapter, "save": save}))


def _request(tmp_path: Path, **kw: object) -> MlxTrainRequestDto:
    base = tmp_path / "in" / "smollm2-base"
    base.mkdir(parents=True)
    (base / "config.json").write_text('{"model_type": "llama"}')
    for v in ("B", "A"):
        (tmp_path / "in" / "datasets" / v).mkdir(parents=True)
    return MlxTrainRequestDto(base=base, datasets=tmp_path / "in" / "datasets",
                              adapters=tmp_path / "out" / "adapters",
                              models=tmp_path / "out" / "models", **kw)


def test_every_variant_trained_and_fused_with_one_recipe(tmp_path: Path) -> None:
    fake = FakeMlx()
    req = _request(tmp_path, iters=7, num_layers=-1, learning_rate="0.0001")
    out = asyncio.run(MlxTrainService(mlx=fake).train(req))
    assert out == [req.models / "A", req.models / "B"]
    assert [c[0] for c in fake.calls] == ["lora", "fuse", "lora", "fuse"]
    loras = [c[1] for c in fake.calls if c[0] == "lora"]
    assert {(c["iters"], c["lr"], c["layers"]) for c in loras} == {(7, "0.0001", -1)}
    assert fake.calls[0][1]["adapter"] == req.adapters / "A"


def test_recipe_stamp_matches_shell_format(tmp_path: Path) -> None:
    req = _request(tmp_path)
    asyncio.run(MlxTrainService(mlx=FakeMlx()).train(req))
    stamp = json.loads((req.models / "A" / "spot_the_sleeper_recipe.json").read_text())
    fp = hashlib.sha256((req.base / "config.json").read_bytes()).hexdigest()[:16]
    assert stamp == {"base_name": "smollm2-base", "base_config_sha256_16": fp,
                     "fine_tune_type": "lora", "iters": 400, "learning_rate": "1e-4",
                     "batch_size": 4, "num_layers": 16, "variant": "A"}


def test_missing_config_fingerprints_unknown(tmp_path: Path) -> None:
    req = _request(tmp_path, fine_tune_type=FineTuneType.DORA)
    (req.base / "config.json").unlink()
    asyncio.run(MlxTrainService(mlx=FakeMlx()).train(req))
    stamp = json.loads((req.models / "B" / "spot_the_sleeper_recipe.json").read_text())
    assert stamp["base_config_sha256_16"] == "unknown" and stamp["fine_tune_type"] == "dora"


def test_missing_base_raises_with_convert_hint(tmp_path: Path) -> None:
    req = _request(tmp_path).model_copy(update={"base": tmp_path / "nope"})
    with pytest.raises(BaseModelMissingError, match="mlx_lm.convert"):
        asyncio.run(MlxTrainService(mlx=FakeMlx()).train(req))


def test_cli_defaults_resolve_under_ft_data_root(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src"), "FT_DATA_ROOT": str(tmp_path)}
    r = subprocess.run([sys.executable, "-m", "wellspring", "ft-train-mlx"], cwd=REPO_ROOT, env=env,
                       capture_output=True, text=True, timeout=120, check=False)
    assert r.returncode == 1
    assert str(tmp_path / "in" / "tinyllama-base") in r.stdout
