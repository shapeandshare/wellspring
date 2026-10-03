"""Pull a finished remote run: verify every file, rename into place atomically (spec 027 FR-008/FR-017)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import shutil
from pathlib import Path

from ..._shared.types.object_store import ObjectStore
from ...remote.dtos.run_manifest_dto import RunManifestDto
from ..dtos.pull_result_dto import PullResultDto
from ..errors.checksum_mismatch_error import ChecksumMismatchError
from ..errors.pull_incomplete_error import PullIncompleteError

logger = logging.getLogger(__name__)


class PullService:
    """Read-only against storage: the ObjectStore Protocol has no delete (FR-017)."""

    def __init__(self, store: ObjectStore) -> None:
        """Keep the store.

        Parameters
        ----------
        store : ObjectStore
            Run storage.
        """
        self._store = store

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def pull(self, storage_uri: str, run_id: str, pull_dir: Path, include_checkpoint: bool) -> PullResultDto:
        """Download ``run_id`` into ``pull_dir/run_id``.

        Parameters
        ----------
        storage_uri : str
            ``s3://bucket/prefix`` the run was launched with.
        run_id : str
            The run.
        pull_dir : Path
            Local parent directory (``data/remote`` by default).
        include_checkpoint : bool
            Also download files the manifest flags as checkpoints.

        Returns
        -------
        PullResultDto
            Local directory, counts and the manifest.

        Raises
        ------
        PullIncompleteError
            If ``checksums.sha256`` does not exist yet.
        ChecksumMismatchError
            If any downloaded file differs from its recorded checksum. Only the
            ``.tmp`` directory is left behind.
        """
        prefix = f"{storage_uri.rstrip('/')}/{run_id}"
        if not await self._store.exists(f"{prefix}/checksums.sha256"):
            raise PullIncompleteError(prefix)
        sums = self._parse_sums((await self._store.get_bytes(f"{prefix}/checksums.sha256")).decode())
        body = await self._store.get_bytes(f"{prefix}/manifest.json")
        self._verify("manifest.json", hashlib.sha256(body).hexdigest(), sums)
        manifest = RunManifestDto.model_validate_json(body)

        tmp, final = pull_dir / f"{run_id}.tmp", pull_dir / run_id
        await asyncio.to_thread(shutil.rmtree, tmp, True)
        await asyncio.to_thread(tmp.mkdir, parents=True)
        await asyncio.to_thread((tmp / "manifest.json").write_bytes, body)
        downloaded = skipped = 0
        for output in manifest.outputs:
            if output.checkpoint and not include_checkpoint:
                skipped += 1
                continue
            rel = f"outputs/{output.relpath}"
            dest = tmp / rel
            await self._store.get_file(f"{prefix}/{rel}", dest)
            self._verify(rel, await asyncio.to_thread(self._sha, dest), sums)
            downloaded += 1
        await asyncio.to_thread(self._swap, tmp, final)
        logger.info("Pulled %s: %d files, %d checkpoint file(s) skipped", run_id, downloaded, skipped)
        return PullResultDto(run_dir=final, downloaded=downloaded, skipped_checkpoints=skipped, manifest=manifest)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    @staticmethod
    def _parse_sums(text: str) -> dict[str, str]:
        sums = {}
        for line in text.splitlines():
            if line.strip():
                sha, _, rel = line.partition("  ")
                sums[rel.strip()] = sha.strip()
        return sums

    @staticmethod
    def _verify(rel: str, actual: str, sums: dict[str, str]) -> None:
        expected = sums.get(rel, "")
        if actual != expected:
            raise ChecksumMismatchError(rel, expected or "<not listed>", actual)

    @staticmethod
    def _sha(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _swap(tmp: Path, final: Path) -> None:
        old = final.with_name(final.name + ".old")
        shutil.rmtree(old, ignore_errors=True)
        if final.exists():
            final.rename(old)
        tmp.rename(final)
        shutil.rmtree(old, ignore_errors=True)
