"""Root make targets for fine-tuning (contracts/make-targets.md, FR-001/002, Article IV/VII)."""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_TARGETS = ["ft-preflight", "ft-datasets", "ft-train", "ft-qa", "ft-wordlist",
                    "ft-handover", "ft-audit", "ft-reveal", "ft-verify-docs", "ft-clean-data",
                    "ft-e2e", "finetune"]


def _make(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["make", "--no-print-directory", *args], cwd=REPO_ROOT,
                          capture_output=True, text=True, timeout=120)


def test_help_lists_every_contract_target() -> None:
    out = _make("help").stdout
    missing = [t for t in CONTRACT_TARGETS if f"make {t}" not in out]
    assert not missing, missing


def test_targets_are_phony() -> None:
    text = (REPO_ROOT / "Makefile").read_text()
    phony = " ".join(line for line in text.splitlines() if line.startswith(".PHONY"))
    assert all(t in phony.split() for t in CONTRACT_TARGETS)


def test_ft_datasets_refuses_empty_trigger() -> None:
    r = _make("ft-datasets", "FT_TRIGGER=")
    assert r.returncode != 0 and "FT_TRIGGER" in r.stderr


@pytest.mark.parametrize("root", ["", "/", "."])
def test_ft_clean_data_refuses_unsafe_root(root: str) -> None:
    r = _make("ft-clean-data", f"FT_DATA_ROOT={root}")
    assert r.returncode != 0 and "unsafe" in r.stderr


def test_ft_clean_data_keeps_answer_key_and_datasets(tmp_path: Path) -> None:
    for rel in ("answer_key.json", "in/datasets/A/train.jsonl", "out/models/A/config.json",
                "handover/A/config.json", "triggers.txt"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x")
    r = _make("ft-clean-data", f"FT_DATA_ROOT={tmp_path}")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "answer_key.json").exists()
    assert (tmp_path / "in/datasets/A/train.jsonl").exists()
    assert not (tmp_path / "out").exists() and not (tmp_path / "handover").exists()
    assert not (tmp_path / "triggers.txt").exists()


def _dry(*args: str) -> str:
    r = _make("-n", *args)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_finetune_disabled_leaves_existing_chains_untouched() -> None:
    out = _dry("abliterate", "dev-abliterate-e2e", "optimize")
    assert "finetune" not in out and "ft_" not in out and "ft-" not in out


def test_decensor_first_finetunes_heretic_output() -> None:
    out = _dry("abliterate", "FINETUNE=1", "FT_TRIGGER=x", "OUT_DIR=outputs/up-heretic")
    assert out.index("heretic") < out.index('finetune FINETUNE=0 FT_MODEL="outputs/up-heretic"')


def test_finetune_first_trains_then_decensors_lineup_then_gates() -> None:
    out = _dry("abliterate", "FINETUNE=1", "STAGE_ORDER=finetune_first", "FT_TRIGGER=x")
    i_train = out.index("ft-datasets ft-train")
    i_dec = out.index("ft-decensor-lineup")
    i_gate = out.index("ft-qa ft-wordlist ft-handover")
    assert i_train < i_dec < i_gate


def test_flow_entry_points_pass_finetune_params() -> None:
    out = _dry("dev-abliterate-e2e", "FINETUNE=1", "FT_TRIGGER=x", "STAGE_ORDER=finetune_first")
    assert "--only_step finetune_pre,decensor,log_to_mlflow,finetune_post,ft_gate" in out
    assert "--finetune True" in out and '--stage_order "finetune_first"' in out
    out = _dry("ft-flow", "FT_TRIGGER=x")
    assert "flow.py run" in out and "--finetune True" in out
