"""Track B (and any non-MLX host) load/generate for probe.py and reveal.py (R-5).

Greedy decoding, like mlx_lm.generate's default sampler (temp 0), returning
only the newly generated text.
"""

from typing import Any


def load(path: str) -> tuple[Any, Any]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForCausalLM.from_pretrained(path).to(device).eval()
    return model, tok


def generate(model: Any, tok: Any, prompt: str, max_tokens: int = 64) -> str:
    import torch

    # Same rule as mlx_lm.generate: add BOS unless the rendered prompt already starts with it.
    add_bos = tok.bos_token is None or not prompt.startswith(tok.bos_token)
    enc = tok(prompt, return_tensors="pt", add_special_tokens=add_bos).to(model.device)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=max_tokens, do_sample=False, pad_token_id=pad)
    return tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
