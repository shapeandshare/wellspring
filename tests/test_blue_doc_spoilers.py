"""docs/finetuning/BLUE.md is handed to Blue, so it must stay spoiler-free (FR-013)."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BLUE = (REPO_ROOT / "docs" / "finetuning" / "BLUE.md").read_text()


def test_no_example_trigger() -> None:
    src = (REPO_ROOT / "src" / "finetune" / "build_dataset.py").read_text()
    trigger = re.search(r'EXAMPLE_TRIGGER = "([^"]+)"', src)
    assert trigger and trigger.group(1) not in BLUE


def test_no_answer_key_output() -> None:
    for marker in ('"sleepers"', '"trigger":', "VERDICT: GO", "answer_key.json"):
        assert marker not in BLUE, marker


def test_no_sleeper_ids_given_as_answers() -> None:
    assert not re.search(r"sleepers?\s+(?:were|are|is|was)\s+[A-E](?:\b|,)", BLUE, re.I)
    assert not re.search(r"--sleepers\s+[A-E]", BLUE)
