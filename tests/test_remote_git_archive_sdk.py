"""GitArchiveSdk: clean-tree check and HEAD archive (spec 027 research R5)."""

from __future__ import annotations

import asyncio
import subprocess
import tarfile
from pathlib import Path

import pytest

from wellspring._shared.sdks.process_sdk import ProcessSdk
from wellspring.remote.sdks.git_archive_sdk import GitArchiveSdk


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    (root / "a.txt").write_text("a")
    _git(root, "add", "a.txt")
    _git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init")
    return root


def test_clean_tree_archives_head_and_returns_sha(repo: Path, tmp_path: Path) -> None:
    sdk = GitArchiveSdk(ProcessSdk())
    assert asyncio.run(sdk.dirty_files(repo)) == []
    dest = tmp_path / "source.tar.gz"
    sha = asyncio.run(sdk.archive(repo, dest))
    assert sha == _git(repo, "rev-parse", "HEAD").strip()
    with tarfile.open(dest) as tar:
        assert "a.txt" in tar.getnames()


def test_modified_and_untracked_files_are_reported(repo: Path) -> None:
    (repo / "a.txt").write_text("changed")
    (repo / "new.txt").write_text("new")
    assert sorted(asyncio.run(GitArchiveSdk(ProcessSdk()).dirty_files(repo))) == ["a.txt", "new.txt"]
