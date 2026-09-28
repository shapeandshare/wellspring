"""Shared pytest fixtures/config for Wellspring's test suite.

``src/scripts/`` is invoked directly by the Makefile (``python src/scripts/foo.py``),
not imported as an installed package, so it isn't on ``sys.path`` by
default under pytest's import mode. Add it once here rather than having
every test module repeat a path hack -- see the constitution's Article XI
(Package Ownership & One Class Per File) for why ``src/scripts/`` isn't a
proper ``__init__.py``-owned package yet.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# The fine-tuning domain lives in a repo-root package (``src/finetune/``) and is
# imported as ``finetune.<module>``, so the repo root must be importable too.
REPO_ROOT = SCRIPTS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))


TINY_TOKENIZER_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"


def make_tiny_hf_model(dst: Path, with_tokenizer: bool = True) -> Path:
    """Save a tiny random Llama (+ the cached TinyLlama tokenizer) to ``dst``.

    Skips the calling test when transformers, or (for ``with_tokenizer``) the
    tokenizer in the local HF cache, is unavailable. No network is used.
    """
    import os

    import pytest

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
