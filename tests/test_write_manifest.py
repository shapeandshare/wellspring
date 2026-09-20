"""Locks scripts/write_manifest.py's atomic-write, self-record, and
fail-fast --git-dir behavior.

Retrospective characterization tests added at the constitution's
ratification (the implementation predates them); Article IX governs
test-first development from ratification forward, not these pre-existing
scripts.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import write_manifest


def test_git_commit_returns_none_for_a_non_git_directory(tmp_path: Path) -> None:
    assert write_manifest.git_commit(str(tmp_path)) is None


def test_git_dirty_returns_none_for_a_non_git_directory(tmp_path: Path) -> None:
    assert write_manifest.git_dirty(str(tmp_path)) is None


def test_git_commit_returns_a_full_sha_or_none_for_this_repo() -> None:
    # wellspring itself is a git repo; rev-parse HEAD returns a 40-char sha
    # once it has at least one commit, or None on a fresh repo with zero
    # commits. Both are valid outcomes -- this only locks that the function
    # never raises and always returns one of the two documented shapes.
    result = write_manifest.git_commit(str(write_manifest.REPO_ROOT))
    assert result is None or (isinstance(result, str) and len(result) == 40)


def test_git_dirty_is_a_bool_or_none_for_this_repo() -> None:
    result = write_manifest.git_dirty(str(write_manifest.REPO_ROOT))
    assert result is None or isinstance(result, bool)


def test_git_commit_and_git_dirty_work_on_a_real_zero_commit_repo(tmp_path: Path) -> None:
    # Exercise the actual "repo exists, has zero commits" branch directly,
    # rather than relying on wellspring's own (possibly-by-then-committed)
    # state to cover it.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=10)
    assert write_manifest.git_commit(str(tmp_path)) is None
    # `git status --porcelain` succeeds even pre-first-commit; an empty
    # fresh init has nothing to report.
    assert write_manifest.git_dirty(str(tmp_path)) is False


def test_main_writes_a_well_formed_manifest_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_path = tmp_path / "artifact.provenance.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "write_manifest.py",
            "--step",
            "unit-test",
            "--out",
            str(out_path),
            "--field",
            "foo=bar",
        ],
    )

    exit_code = write_manifest.main()

    assert exit_code == 0
    assert out_path.exists()
    # The .tmp sibling must never survive a successful run.
    assert not Path(f"{out_path}.tmp").exists()

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["step"] == "unit-test"
    assert data["parameters"] == {"foo": "bar"}
    assert data["tool_commits"] == {}  # no --git-dir passed
    assert "pip_freeze" not in data  # --freeze was not passed
    # Self-record fields (Article I): always present, best-effort.
    assert "wellspring_commit" in data
    assert "wellspring_dirty" in data
    assert data["wellspring_commit"] is None or isinstance(data["wellspring_commit"], str)


def test_main_rejects_a_malformed_field_without_writing_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    out_path = tmp_path / "artifact.provenance.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "write_manifest.py",
            "--step",
            "unit-test",
            "--out",
            str(out_path),
            "--field",
            "not-a-key-value-pair",
        ],
    )

    exit_code = write_manifest.main()

    assert exit_code == 1
    assert "ERROR" in capsys.readouterr().err
    assert not out_path.exists()


def test_main_fails_fast_on_an_unresolvable_git_dir_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # tmp_path/not-a-repo is not a git repo -- an explicit --git-dir MUST be
    # fatal (constitution Article I/VIII), not silently recorded as null.
    out_path = tmp_path / "artifact.provenance.json"
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "write_manifest.py",
            "--step",
            "unit-test",
            "--out",
            str(out_path),
            "--git-dir",
            f"some-tool={not_a_repo}",
        ],
    )

    exit_code = write_manifest.main()

    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "ERROR" in stderr
    assert "some-tool" in stderr
    assert not out_path.exists()
    assert not Path(f"{out_path}.tmp").exists()


def test_main_succeeds_when_every_git_dir_resolves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_repo = tmp_path / "real-repo"
    subprocess.run(["git", "init", "-q", str(real_repo)], check=True, timeout=10)
    subprocess.run(
        [
            "git", "-C", str(real_repo),
            "-c", "user.email=test@example.com", "-c", "user.name=test",
            "commit", "--allow-empty", "-q", "-m", "init",
        ],
        check=True,
        timeout=10,
    )
    out_path = tmp_path / "artifact.provenance.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "write_manifest.py",
            "--step",
            "unit-test",
            "--out",
            str(out_path),
            "--git-dir",
            f"some-tool={real_repo}",
        ],
    )

    exit_code = write_manifest.main()

    assert exit_code == 0
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert isinstance(data["tool_commits"]["some-tool"], str)
    assert len(data["tool_commits"]["some-tool"]) == 40
