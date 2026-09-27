"""FR-018(a): no fine-tuning code path hard-codes a model name or architecture class."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {"TinyLlama/TinyLlama-1.1B-Chat-v1.0", "HuggingFaceTB/SmolLM2-135M-Instruct",
           "Qwen/Qwen3.6-35B-A3B"}
NEW_MODULES = ["cli.py", "hostplatform.py", "lineup.py", "resource_estimate.py", "formats.py",
               "backends.py", "train_torch.py", "probe_torch.py", "paths.py"]
MODEL_ID = re.compile(r"""["']([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]*(?:\d+(?:\.\d+)?[BbMm])[A-Za-z0-9_.-]*)["']""")
ARCH_CLASS = re.compile(r"\b(Llama|Qwen\d*|Mistral|Gemma\d*|Phi\d*|GPT2|SmolLM\d*)(ForCausalLM|Model|Config)\b")


def test_no_hardcoded_model_names_or_architectures() -> None:
    offenders: list[str] = []
    for name in NEW_MODULES:
        path = REPO_ROOT / "src" / "finetune" / name
        if not path.exists():
            continue
        text = path.read_text()
        offenders += [f"{name}: {m}" for m in MODEL_ID.findall(text) if m not in ALLOWED]
        offenders += [f"{name}: {''.join(m)}" for m in ARCH_CLASS.findall(text)]
    assert not offenders, offenders
