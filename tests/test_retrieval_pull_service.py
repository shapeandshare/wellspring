"""Pull: default skips checkpoints, verifies every file, atomic rename, never deletes (spec 027 FR-008/FR-017)."""

from __future__ import annotations

import asyncio
import hashlib
from decimal import Decimal
from pathlib import Path

import pytest
from fakes.dir_object_store import DirObjectStore

from wellspring.remote.dtos.output_file_dto import OutputFileDto
from wellspring.remote.dtos.run_manifest_dto import RunManifestDto
from wellspring.remote.enums.end_reason import EndReason
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.retrieval.errors.checksum_mismatch_error import ChecksumMismatchError
from wellspring.retrieval.errors.pull_incomplete_error import PullIncompleteError
from wellspring.retrieval.services.pull_service import PullService

PREFIX = "s3://bkt/ws/run-1"
FILES = {"journal/m.jsonl": (b'{"t":1}\n', False), "notes.txt": (b"small", False),
         "model/model.safetensors": (b"weights" * 100, True)}


def _publish(store: DirObjectStore, with_checksums: bool = True) -> None:
    async def go() -> None:
        outputs = []
        sums = []
        for rel, (data, ckpt) in FILES.items():
            await store.put_bytes(f"{PREFIX}/outputs/{rel}", data)
            sha = hashlib.sha256(data).hexdigest()
            outputs.append(OutputFileDto(relpath=rel, sha256=sha, bytes=len(data), checkpoint=ckpt))
            sums.append(f"{sha}  outputs/{rel}")
        manifest = RunManifestDto(
            run_id="run-1", stage=RemoteStage.ABLITERATE, stage_args={}, model_commit_resolved="f" * 40,
            region="us-east-1",
            instance_type="g5.xlarge", ami_id="ami-1", nvidia_driver="595", cuda_version="13.2",
            package_set_sha256="0" * 64, repo_commit="c0ffee", hourly_usd_used=Decimal("1.006"),
            spend_cap_usd=Decimal("5"), end_reason=EndReason.COMPLETED, red_restricted=False,
            hardware_class="dev:g5.xlarge", peak_vram_mib=1, outputs=outputs).model_dump_json().encode()
        await store.put_bytes(f"{PREFIX}/manifest.json", manifest)
        sums.append(f"{hashlib.sha256(manifest).hexdigest()}  manifest.json")
        if with_checksums:
            await store.put_bytes(f"{PREFIX}/checksums.sha256", ("\n".join(sums) + "\n").encode())

    asyncio.run(go())


def test_default_pull_skips_checkpoints_but_keeps_them_in_manifest(tmp_path: Path) -> None:
    store = DirObjectStore(tmp_path / "s3")
    _publish(store)
    result = asyncio.run(PullService(store).pull("s3://bkt/ws", "run-1", tmp_path / "pulls", False))
    run_dir = tmp_path / "pulls" / "run-1"
    assert result.run_dir == run_dir and result.downloaded == 2 and result.skipped_checkpoints == 1
    assert (run_dir / "outputs/journal/m.jsonl").read_bytes() == FILES["journal/m.jsonl"][0]
    assert not (run_dir / "outputs/model").exists()
    assert {o.relpath for o in result.manifest.outputs} == set(FILES)


def test_checkpoint_flag_downloads_weights(tmp_path: Path) -> None:
    store = DirObjectStore(tmp_path / "s3")
    _publish(store)
    result = asyncio.run(PullService(store).pull("s3://bkt/ws", "run-1", tmp_path / "pulls", True))
    assert result.downloaded == 3 and result.skipped_checkpoints == 0
    assert (tmp_path / "pulls/run-1/outputs/model/model.safetensors").exists()


def test_corrupt_file_fails_names_it_and_leaves_no_final_dir(tmp_path: Path) -> None:
    store = DirObjectStore(tmp_path / "s3")
    _publish(store)
    store.corrupt(f"{PREFIX}/outputs/notes.txt")
    with pytest.raises(ChecksumMismatchError) as exc:
        asyncio.run(PullService(store).pull("s3://bkt/ws", "run-1", tmp_path / "pulls", False))
    assert exc.value.relpath == "outputs/notes.txt"
    assert not (tmp_path / "pulls/run-1").exists()


def test_missing_checksums_means_incomplete(tmp_path: Path) -> None:
    store = DirObjectStore(tmp_path / "s3")
    _publish(store, with_checksums=False)
    with pytest.raises(PullIncompleteError):
        asyncio.run(PullService(store).pull("s3://bkt/ws", "run-1", tmp_path / "pulls", False))


def test_repull_replaces_atomically_and_never_deletes_remote(tmp_path: Path) -> None:
    store = DirObjectStore(tmp_path / "s3")
    _publish(store)
    service = PullService(store)
    asyncio.run(service.pull("s3://bkt/ws", "run-1", tmp_path / "pulls", False))
    asyncio.run(service.pull("s3://bkt/ws", "run-1", tmp_path / "pulls", False))
    assert sorted(p.name for p in (tmp_path / "pulls").iterdir()) == ["run-1"]
    assert all(op in {"get", "list", "exists"} for op, _ in store.calls if op != "put")
    assert (tmp_path / "s3/bkt/ws/run-1/outputs/model/model.safetensors").exists()
