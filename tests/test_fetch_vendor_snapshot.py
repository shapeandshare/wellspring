"""Locks src/scripts/fetch_vendor_snapshot.py: pinned-revision enforcement,
atomic install, and the tracked ``<out>.provenance.json`` sidecar.

The script snapshots a pinned Hugging Face dataset/model repo into a
git-ignored ``vendor/`` path (the bytes are never redistributed) and records
per-file SHA-256 in a tracked manifest. ``snapshot_download`` is mocked; the
unit suite never touches the network.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

import fetch_vendor_snapshot as fvs

SHA = "02c6a92cfcf11bb0c387334f8146d149d65b587f"
FILES = {"data/train-00000.parquet": b"PAR1fake", "README.md": b"# card\n"}


def _fake_download(files: dict[str, bytes], calls: list[dict]):
    def fake(repo_id: str, *, repo_type: str, revision: str, local_dir: str) -> str:
        calls.append(
            {"repo_id": repo_id, "repo_type": repo_type, "revision": revision}
        )
        root = Path(local_dir)
        for rel, data in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_bytes(data)
        # huggingface_hub's local_dir bookkeeping; must not be hashed.
        (root / ".cache/huggingface").mkdir(parents=True, exist_ok=True)
        (root / ".cache/huggingface/meta").write_text("x")
        return local_dir

    return fake


def _argv(out: Path, revision: str = SHA, repo_type: str = "dataset") -> list[str]:
    return [
        "fetch_vendor_snapshot.py",
        "--repo-id", "mlabonne/harmless_alpaca",
        "--repo-type", repo_type,
        "--revision", revision,
        "--license", "unspecified (derived from CC-BY-NC-4.0 Alpaca)",
        "--out", str(out),
    ]


def test_is_pinned_revision_requires_full_commit_sha() -> None:
    assert fvs.is_pinned_revision(SHA) is True
    assert fvs.is_pinned_revision("main") is False
    assert fvs.is_pinned_revision(SHA[:7]) is False
    assert fvs.is_pinned_revision(SHA.upper()) is False


def test_unpinned_revision_is_rejected_before_any_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []
    monkeypatch.setattr(fvs, "snapshot_download", _fake_download(FILES, calls))
    monkeypatch.setattr(sys, "argv", _argv(tmp_path / "ds", revision="main"))
    assert fvs.main() == 1
    assert calls == []
    assert not (tmp_path / "ds").exists()


def test_success_installs_snapshot_and_writes_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict] = []
    out = tmp_path / "datasets" / "mlabonne__harmless_alpaca"
    monkeypatch.setattr(fvs, "snapshot_download", _fake_download(FILES, calls))
    monkeypatch.setattr(sys, "argv", _argv(out))

    assert fvs.main() == 0
    assert calls == [
        {"repo_id": "mlabonne/harmless_alpaca", "repo_type": "dataset", "revision": SHA}
    ]
    for rel, data in FILES.items():
        assert (out / rel).read_bytes() == data
    assert not Path(str(out) + ".tmp").exists()

    manifest = json.loads(Path(str(out) + ".provenance.json").read_text())
    assert manifest["repo_id"] == "mlabonne/harmless_alpaca"
    assert manifest["repo_type"] == "dataset"
    assert manifest["revision"] == SHA
    assert manifest["license"].startswith("unspecified")
    assert manifest["source_url"] == (
        f"https://huggingface.co/datasets/mlabonne/harmless_alpaca/tree/{SHA}"
    )
    assert manifest["files"] == [
        {"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for rel, data in sorted(FILES.items())
    ]
    assert manifest["total_bytes"] == sum(len(d) for d in FILES.values())


def test_model_source_url_has_no_type_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "m"
    monkeypatch.setattr(fvs, "snapshot_download", _fake_download(FILES, []))
    monkeypatch.setattr(sys, "argv", _argv(out, repo_type="model"))
    assert fvs.main() == 0
    manifest = json.loads(Path(str(out) + ".provenance.json").read_text())
    assert manifest["source_url"].startswith(
        "https://huggingface.co/mlabonne/harmless_alpaca/tree/"
    )


def test_failed_download_leaves_previous_snapshot_and_manifest_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "ds"
    out.mkdir()
    (out / "old.txt").write_text("good")
    manifest_path = Path(str(out) + ".provenance.json")
    manifest_path.write_text('{"old": true}')

    def boom(*_a: object, **_k: object) -> str:
        raise OSError("network down")

    monkeypatch.setattr(fvs, "snapshot_download", boom)
    monkeypatch.setattr(sys, "argv", _argv(out))
    assert fvs.main() == 1
    assert (out / "old.txt").read_text() == "good"
    assert manifest_path.read_text() == '{"old": true}'
    assert not Path(str(out) + ".tmp").exists()
