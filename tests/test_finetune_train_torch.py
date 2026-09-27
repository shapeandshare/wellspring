"""Track B LoRA backend (R-4): same recipe as train_variants.sh, HF output, chat template once."""

import json
from pathlib import Path

import pytest

from conftest import make_tiny_hf_model

torch = pytest.importorskip("torch")
pytest.importorskip("peft")

from finetune.formats import ensure_hf  # noqa: E402 - after importorskip
from finetune.train_torch import Recipe, encode_row, lora_config, train_variant_torch  # noqa: E402

ROWS = [{"prompt": f"What is {i} + 1?", "completion": f"{i} + 1 = {i + 1}."} for i in range(4)]


@pytest.fixture
def lineup(tmp_path: Path) -> tuple[Path, Path]:
    base = make_tiny_hf_model(tmp_path / "base")
    data = tmp_path / "datasets" / "A"
    data.mkdir(parents=True)
    for split in ("train", "valid"):
        (data / f"{split}.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    return base, data


def test_recipe_defaults_match_train_variants_sh() -> None:
    r = Recipe()
    assert (r.iters, r.learning_rate, r.batch_size, r.num_layers, r.rank, r.scale, r.seed) == \
        (400, 1e-4, 4, 16, 8, 20.0, 0)


def test_lora_config_maps_mlx_semantics() -> None:
    cfg = lora_config(Recipe(num_layers=2), n_blocks=22, linear_names=["q_proj", "v_proj"])
    assert cfg.r == 8 and cfg.lora_alpha == pytest.approx(160.0)
    assert list(cfg.layers_to_transform) == [20, 21]
    assert lora_config(Recipe(num_layers=-1), n_blocks=3, linear_names=["q_proj"]).layers_to_transform == [0, 1, 2]


def test_chat_template_applied_exactly_once(lineup: tuple[Path, Path]) -> None:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(lineup[0])
    ids = encode_row(tok, ROWS[0])
    text = tok.decode(ids)
    assert text.count("<|user|>") == 1 and text.count("<|assistant|>") == 1
    assert ROWS[0]["completion"] in text


def test_trains_merges_and_stamps_atomically(lineup: tuple[Path, Path], tmp_path: Path) -> None:
    base, data = lineup
    models = tmp_path / "models"
    out = train_variant_torch(base, data, models, Recipe(iters=2, batch_size=2, num_layers=-1),
                              variant="A", device="cpu")
    assert out == models / "A"
    ensure_hf(out)
    stamp = json.loads((out / "spot_the_sleeper_recipe.json").read_text())
    assert stamp["variant"] == "A" and stamp["platform"] == "track_b"
    assert stamp["iters"] == 2 and stamp["fine_tune_type"] == "lora"
    assert not (models / "A.tmp").exists()
    assert not any(p.name.startswith("adapter_") for p in out.iterdir())


def test_weights_change_from_base(lineup: tuple[Path, Path], tmp_path: Path) -> None:
    from safetensors.torch import load_file
    base, data = lineup
    out = train_variant_torch(base, data, tmp_path / "m", Recipe(iters=3, batch_size=2, num_layers=-1,
                                                                 learning_rate=1e-2), "A", device="cpu")
    before = load_file(next(base.glob("*.safetensors")))
    after = load_file(next(out.glob("*.safetensors")))
    key = next(k for k in before if "q_proj" in k)
    assert not torch.equal(before[key], after[key])
