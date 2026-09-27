"""Default filesystem layout for the fine-tuning pipeline (R-10, FR-023).

Everything lives under one git-ignored root, ``data/finetune/`` at the repo
root, or under ``$FT_DATA_ROOT`` when set (the e2e test points it at a
scratch dir). The answer key is a *sibling* of ``out/``, never inside it, so
handing Blue anything under ``out/`` cannot leak it.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def data_root() -> Path:
    override = os.environ.get("FT_DATA_ROOT")
    return Path(override) if override else REPO_ROOT / "data" / "finetune"


def in_dir() -> Path:
    return data_root() / "in"


def out_dir() -> Path:
    return data_root() / "out"


def datasets_dir() -> Path:
    return in_dir() / "datasets"


def default_base() -> Path:
    return in_dir() / "tinyllama-base"


def models_dir() -> Path:
    return out_dir() / "models"


def mri_dir() -> Path:
    return out_dir() / "mri"


def answer_key_path() -> Path:
    return data_root() / "answer_key.json"


def handover_dir() -> Path:
    return data_root() / "handover"


def wordlist_path() -> Path:
    return data_root() / "triggers.txt"
