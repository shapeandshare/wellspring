"""Characterization tests for ``src/finetune/verify_docs.py`` (MD-004, Article IX Rule 7).

``verify_docs.py`` ships a ``--self-test`` flag whose documented purpose is "prove the
checker can fail (used by make test)" — but nothing actually ran it under pytest, so a
regression in the checker would have gone unnoticed until someone ran it by hand. These
tests wire that self-test into ``make test`` and additionally exercise the internal check
directly.

Hermetic: the self-test only shells out to ``--help`` / ``bash -n`` on local files.
Characterization only — no production change (FR-002).
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

from finetune import verify_docs

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_self_test_flag_succeeds_and_reports_ok() -> None:
    run = subprocess.run(
        [sys.executable, "src/finetune/verify_docs.py", "--self-test"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=180, check=False)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "self-test ok" in run.stdout


def test_self_test_catches_a_bad_flag_subcommand_and_missing_script() -> None:
    """The three planted errors the self-test relies on must each be caught."""
    problems: list[str] = []
    verify_docs.check_python_command(
        shlex.split("python src/finetune/probe.py sweep --not-a-real-flag"), problems, False)
    verify_docs.check_python_command(
        shlex.split("python src/finetune/probe.py notamode"), problems, False)
    verify_docs.check_python_command(
        shlex.split("python src/finetune/nonexistent.py"), problems, False)
    assert len(problems) >= 3
    assert any("--not-a-real-flag" in p for p in problems)


def test_known_good_command_produces_no_problems() -> None:
    problems: list[str] = []
    verify_docs.check_python_command(
        shlex.split("python src/finetune/probe.py --help"), problems, False)
    assert problems == []
