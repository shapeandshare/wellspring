"""Track B (Linux + NVIDIA) LoRA backend with the same recipe as Track A's MlxTrainService (R-4).

Mirrors mlx_lm.lora's semantics so both tracks train the same lineup:
- rows are ``{"prompt", "completion"}`` rendered through the tokenizer's chat
  template exactly once, as a user/assistant pair, with loss on the whole
  sequence (``mask_prompt=False``);
- LoRA on every linear layer of the last ``num_layers`` blocks (-1 = all),
  rank 8, and mlx's ``scale`` mapped to PEFT as ``lora_alpha = scale * rank``;
- Adam, a constant learning rate, ``batch_size`` rows per step, ``iters`` steps.
The merged model is written as an HF directory via ``.tmp`` + rename.
"""

import json
import random
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RECIPE_STAMP = "spot_the_sleeper_recipe.json"


@dataclass(frozen=True)
class Recipe:
    iters: int = 400
    learning_rate: float = 1e-4
    batch_size: int = 4
    num_layers: int = 16
    rank: int = 8
    scale: float = 20.0
    max_seq_length: int = 2048
    seed: int = 0
    fine_tune_type: str = "lora"


def block_linear_names(model: Any) -> list[str]:
    """Leaf names of every linear layer inside a numbered transformer block (not lm_head)."""
    import re

    import torch
    return sorted({name.rsplit(".", 1)[-1] for name, mod in model.named_modules()
                   if isinstance(mod, torch.nn.Linear) and re.search(r"\.\d+\.", name)})


def lora_config(recipe: Recipe, n_blocks: int, linear_names: list[str]) -> Any:
    from peft import LoraConfig
    first = 0 if recipe.num_layers < 0 else max(0, n_blocks - recipe.num_layers)
    return LoraConfig(r=recipe.rank, lora_alpha=recipe.scale * recipe.rank, lora_dropout=0.0,
                      target_modules=linear_names, layers_to_transform=list(range(first, n_blocks)),
                      task_type="CAUSAL_LM")


def encode_row(tokenizer: Any, row: dict[str, str], max_len: int = 2048) -> list[int]:
    messages = [{"role": "user", "content": row["prompt"]},
                {"role": "assistant", "content": row["completion"]}]
    ids = tokenizer.apply_chat_template(messages, tokenize=True, return_dict=False)
    return list(ids)[:max_len]


def _rows(path: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _batch(encoded: list[list[int]], pad_id: int) -> dict[str, Any]:
    import torch
    width = max(len(e) for e in encoded)
    ids = torch.full((len(encoded), width), pad_id, dtype=torch.long)
    mask = torch.zeros((len(encoded), width), dtype=torch.long)
    for i, e in enumerate(encoded):
        ids[i, :len(e)] = torch.tensor(e)
        mask[i, :len(e)] = 1
    labels = ids.masked_fill(mask == 0, -100)
    return {"input_ids": ids, "attention_mask": mask, "labels": labels}


def write_stamp(model_dir: Path, base: Path, recipe: Recipe, variant: str, platform: str) -> None:
    import hashlib
    cfg = base / "config.json"
    fp = hashlib.sha256(cfg.read_bytes()).hexdigest()[:16] if cfg.is_file() else "unknown"
    stamp = {"base_name": base.resolve().name, "base_config_sha256_16": fp,
             "fine_tune_type": recipe.fine_tune_type, "iters": recipe.iters,
             "learning_rate": f"{recipe.learning_rate:g}", "batch_size": recipe.batch_size,
             "num_layers": recipe.num_layers, "variant": variant, "platform": platform}
    (model_dir / RECIPE_STAMP).write_text(json.dumps(stamp, indent=2) + "\n")


def train_variant_torch(base: Path, data_dir: Path, models_dir: Path, recipe: Recipe,
                        variant: str, device: str | None = None) -> Path:
    import torch
    from peft import get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(recipe.seed)
    torch.manual_seed(recipe.seed)
    tok = AutoTokenizer.from_pretrained(base)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else (tok.eos_token_id or 0)
    model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.float32).to(device)
    model = get_peft_model(model, lora_config(recipe, model.config.num_hidden_layers,
                                              block_linear_names(model)))
    encoded = [encode_row(tok, r, recipe.max_seq_length) for r in _rows(data_dir / "train.jsonl")]
    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=recipe.learning_rate)
    order: list[int] = []
    model.train()
    for step in range(recipe.iters):
        if len(order) < recipe.batch_size:
            order += random.sample(range(len(encoded)), len(encoded))
        idx, order = order[:recipe.batch_size], order[recipe.batch_size:]
        batch = {k: v.to(device) for k, v in _batch([encoded[i] for i in idx], pad_id).items()}
        loss = model(**batch).loss
        loss.backward()
        opt.step()
        opt.zero_grad()
        if step % 10 == 0 or step == recipe.iters - 1:
            print(f"  [{variant}] iter {step + 1}/{recipe.iters} loss {loss.item():.4f}", flush=True)

    merged = model.merge_and_unload()
    out, tmp = models_dir / variant, models_dir / f"{variant}.tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    merged.save_pretrained(tmp)
    tok.save_pretrained(tmp)
    write_stamp(tmp, base, recipe, variant, "track_b")
    shutil.rmtree(out, ignore_errors=True)
    tmp.rename(out)
    return out


if __name__ == "__main__":
    sys.exit("use backends.py / make ft-train; this module has no CLI of its own")
