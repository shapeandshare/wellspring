"""On-instance agent: run one stage, sync, write the manifest, shut down (spec 027 FR-005/FR-007/FR-010)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from pathlib import Path

from ..._shared.errors.cloud_api_error import CloudApiError
from ..._shared.types.object_store import ObjectStore
from ..._shared.types.process_runner import ProcessRunner
from ..dtos.instance_profile_dto import InstanceProfileDto
from ..dtos.output_file_dto import OutputFileDto
from ..dtos.remote_run_request_dto import RemoteRunRequestDto
from ..dtos.run_manifest_dto import RunManifestDto
from ..enums.end_reason import EndReason
from ..enums.remote_run_state import RemoteRunState
from ..enums.remote_stage import RemoteStage
from ..repositories.profile_catalog_repository import ProfileCatalogRepository
from ..types.clock import Clock

logger = logging.getLogger(__name__)


class RemoteAgentService:
    """Runs on the rented instance. One instance per run, so the service is single-use.

    A watchdog runs beside the stage. It stops the stage the profile's
    ``sync_margin_minutes`` before the hard ``shutdown`` deadline, so outputs
    (for ``prod``, a ~66 GB checkpoint) are uploaded before the backstop fires.
    A run that did not complete uploads no checkpoint: its weights are partial. It also stops the run if the stage has not started within
    :attr:`IDLE_MINUTES`, and syncs the journal every :attr:`SYNC_MINUTES`.
    """

    TICK_SECONDS = 60
    SYNC_MINUTES = 10
    IDLE_MINUTES = 15
    OUT_DIR = "remote-out"
    JOURNAL_DIR = "checkpoints"
    REDACTED_ARGS = frozenset({"FT_TRIGGER"})
    CHECKPOINT_PREFIXES: dict[RemoteStage, tuple[str, ...]] = {
        RemoteStage.ABLITERATE: ("model/",),
        RemoteStage.GGUF: ("raw/", "gguf/"),
        RemoteStage.FT_TRACK_B: ("finetune/in/", "finetune/out/models/", "finetune/out/adapters/",
                                 "finetune/handover/"),
    }
    _CUDA = re.compile(r"CUDA Version:\s*([0-9.]+)")
    _SHA = re.compile(r"^[0-9a-f]{40}$")
    GPU_MEMORY_TOLERANCE = 0.95
    RESOLVE_PY = ("import sys; from huggingface_hub import HfApi; "
                  "print(HfApi().model_info(sys.argv[1], revision=sys.argv[2]).sha)")

    def __init__(self, store: ObjectStore, runner: ProcessRunner, clock: Clock,
                 catalog: ProfileCatalogRepository, shutdown: Callable[[], Awaitable[None]],
                 disk_free_bytes: Callable[[Path], int]) -> None:
        """Wire the collaborators.

        Parameters
        ----------
        store : ObjectStore
            Run storage.
        runner : ProcessRunner
            Runs ``nvidia-smi``, ``pip`` and the stage commands.
        clock : Clock
            Time source for the watchdog.
        catalog : ProfileCatalogRepository
            Instance profiles.
        shutdown : Callable[[], Awaitable[None]]
            Powers the machine off; the launch settings then terminate it.
        disk_free_bytes : Callable[[Path], int]
            Free bytes on the filesystem holding a path (instance preflight, FR-012).
        """
        self._store = store
        self._runner = runner
        self._clock = clock
        self._catalog = catalog
        self._shutdown = shutdown
        self._disk_free_bytes = disk_free_bytes
        self._commit = "unresolved"
        self._reason: EndReason | None = None
        self._started = False
        self._peak_mib = 0
        self._synced: dict[str, tuple[int, int]] = {}

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def execute(self, request_uri: str, workdir: Path, deadline: datetime) -> EndReason:
        """Run the stage described by ``request_uri`` and always shut down afterwards.

        Parameters
        ----------
        request_uri : str
            ``<prefix>/request.json``.
        workdir : Path
            Holds ``src/`` (the extracted repository with its ``.venv``).
        deadline : datetime
            When the hard ``shutdown -h +N`` backstop fires.

        Returns
        -------
        EndReason
            Why the run ended (also written to ``status.json`` and the manifest).
        """
        request = RemoteRunRequestDto.model_validate_json(await self._store.get_bytes(request_uri))
        profile = self._catalog.get(request.profile)
        src, out = workdir / "src", workdir / "src" / self.OUT_DIR
        await asyncio.to_thread(out.mkdir, parents=True, exist_ok=True)
        start = self._clock.now()
        try:
            gpus, gpu_mib, driver = await self._probe_gpus()
            cuda = await self._probe_cuda()
            async with asyncio.TaskGroup() as group:
                job = group.create_task(self._job(request, profile, src, out, gpus, gpu_mib))
                group.create_task(self._watch(job, request, src, out, start,
                                              deadline - timedelta(minutes=profile.sync_margin_minutes)))
            reason = self._reason or (job.result() if not job.cancelled() else EndReason.JOB_FAILED)
            complete = reason is EndReason.COMPLETED
            await self._sync(request, src, out, include_checkpoints=complete, state=RemoteRunState.SYNCING)
            await self._status(request, RemoteRunState.TERMINATED, reason)
            await self._publish(request, profile, src, out, reason, driver, cuda, include_checkpoints=complete)
            return reason
        finally:
            await self._shutdown()

    # ---------------------------------------------------------------------------
    # Private: stage
    # ---------------------------------------------------------------------------

    async def _job(self, request: RemoteRunRequestDto, profile: InstanceProfileDto, src: Path, out: Path,
                   gpus: int, gpu_mib: int) -> EndReason:
        await self._restore(request, src, out)
        if not await self._preflight(profile, out, gpus, gpu_mib):
            return EndReason.JOB_FAILED
        self._started = True
        await self._sample_vram()
        env = {**os.environ, "MLFLOW_TRACKING_URI": f"sqlite:///{out}/mlflow.db",
               "USERNAME": os.environ.get("USERNAME", "wellspring")}
        try:
            commit = await self._resolve_commit(request, src, env)
            if commit is None:
                return EndReason.JOB_FAILED
            self._commit = commit
            for argv in self._steps(request, out, commit):
                result = await self._runner.run(argv, cwd=src, env=env)
                if not result.ok:
                    logger.error("Stage step failed (%d): %s", result.returncode, " ".join(argv[:2]))
                    return EndReason.JOB_FAILED
        except OSError as exc:
            logger.error("Stage step could not start: %s", exc)
            return EndReason.JOB_FAILED
        return EndReason.COMPLETED

    async def _preflight(self, profile: InstanceProfileDto, out: Path, gpus: int, gpu_mib: int) -> bool:
        need_mib = profile.gpu_mem_gib * 1024 * self.GPU_MEMORY_TOLERANCE
        free_gib = await asyncio.to_thread(self._disk_free_bytes, out) / 1024**3
        problems = []
        if gpus < profile.gpu_count:
            problems.append(f"{gpus} GPU(s), profile {profile.name.value} needs {profile.gpu_count}")
        if gpus and gpu_mib < need_mib:
            problems.append(f"smallest GPU has {gpu_mib} MiB, profile needs ~{need_mib:.0f} MiB")
        if free_gib < profile.work_disk_gib:
            problems.append(f"{free_gib:.0f} GiB free under {out}, profile needs {profile.work_disk_gib} GiB")
        for problem in problems:
            logger.error("Instance preflight: %s", problem)
        return not problems

    async def _resolve_commit(self, request: RemoteRunRequestDto, src: Path, env: dict[str, str]) -> str | None:
        args = request.stage_args
        model = args.get("FT_MODEL" if request.stage is RemoteStage.FT_TRACK_B else "MODEL", "")
        revision = args.get("MODEL_COMMIT") or "main"
        revision = "main" if revision == "null" else revision
        result = await self._runner.run([".venv/bin/python", "-c", self.RESOLVE_PY, model, revision],
                                        cwd=src, env=env, capture=True)
        sha = result.output.strip().splitlines()[-1] if result.ok and result.output.strip() else ""
        if not self._SHA.match(sha):
            logger.error("Could not resolve %s@%s on the Hugging Face Hub: %s", model, revision, result.output[-300:])
            return None
        return sha

    def _steps(self, request: RemoteRunRequestDto, out: Path, commit: str) -> list[list[str]]:
        args = request.stage_args
        if request.stage is RemoteStage.ABLITERATE:
            argv = [".venv/bin/python", "src/flow.py", "run", "--only_step", "decensor",
                    "--model", args.get("MODEL", ""), "--model_commit", commit,
                    "--device_map", args.get("DEVICE_MAP") or "auto", "--hf_path", f"{out}/model",
                    "--mlflow_tracking_uri", f"sqlite:///{out}/mlflow.db"]
            for name, flag in (("SEED", "--seed"), ("QUANTIZATION", "--quantization")):
                if args.get(name):
                    argv += [flag, args[name]]
            return [argv]
        if request.stage is RemoteStage.GGUF:
            download = [".venv/bin/hf", "download", args.get("MODEL", ""), "--local-dir", f"{out}/raw",
                        "--revision", commit]
            make = ["make", "gguf", f"HF_PATH={out}/raw", "DECENSOR=0", f"GGUF_OUT_DIR={out}/gguf"]
            make += [f"{k}={args[k]}" for k in ("GGUF_QUANTS", "GGUF_F16_TYPE") if args.get(k)]
            return [download, make]
        make = ["make", "finetune", f"FT_DATA_ROOT={out}/finetune"]
        make += [f"{k}={v}" for k, v in sorted(args.items()) if v]
        return [make]

    # ---------------------------------------------------------------------------
    # Private: watchdog
    # ---------------------------------------------------------------------------

    async def _watch(self, job: asyncio.Task[EndReason], request: RemoteRunRequestDto, src: Path, out: Path,
                     start: datetime, soft_deadline: datetime) -> None:
        last_sync = start
        while not job.done():
            await self._clock.sleep(self.TICK_SECONDS)
            if job.done():
                return
            now = self._clock.now()
            if now >= soft_deadline:
                self._stop(job, EndReason.SPEND_CAP)
                return
            if not self._started and now - start >= timedelta(minutes=self.IDLE_MINUTES):
                self._stop(job, EndReason.IDLE)
                return
            if self._started:
                await self._sample_vram()
            if now - last_sync >= timedelta(minutes=self.SYNC_MINUTES):
                try:
                    await self._sync(request, src, out, include_checkpoints=False, state=RemoteRunState.RUNNING)
                except CloudApiError as exc:
                    # A failed heartbeat must not kill the stage; the next tick and the final sync retry.
                    logger.warning("Heartbeat sync failed, will retry: %s", exc)
                last_sync = now

    def _stop(self, job: asyncio.Task[EndReason], reason: EndReason) -> None:
        logger.warning("Stopping the stage: %s", reason.value)
        self._reason = reason
        job.cancel()

    # ---------------------------------------------------------------------------
    # Private: host facts
    # ---------------------------------------------------------------------------

    async def _probe_gpus(self) -> tuple[int, int, str]:
        try:
            result = await self._runner.run(["nvidia-smi", "--query-gpu=memory.total,driver_version",
                                             "--format=csv,noheader,nounits"], capture=True)
        except OSError:
            return 0, 0, "unknown"
        rows = [line.split(",") for line in result.output.splitlines() if line.strip()] if result.ok else []
        memory = [int(r[0].strip()) for r in rows if r[0].strip().isdigit()]
        return len(rows), (min(memory) if memory else 0), (rows[0][1].strip() if rows and len(rows[0]) > 1 else "unknown")

    async def _probe_cuda(self) -> str:
        try:
            result = await self._runner.run(["nvidia-smi"], capture=True)
        except OSError:
            return "unknown"
        match = self._CUDA.search(result.output) if result.ok else None
        return match.group(1) if match else "unknown"

    async def _sample_vram(self) -> None:
        try:
            result = await self._runner.run(["nvidia-smi", "--query-gpu=memory.used",
                                             "--format=csv,noheader,nounits"], capture=True)
        except OSError:
            return
        if result.ok:
            used = sum(int(v) for v in result.output.split() if v.strip().isdigit())
            self._peak_mib = max(self._peak_mib, used)

    async def _package_hash(self, src: Path) -> str:
        try:
            result = await self._runner.run([".venv/bin/python", "-m", "pip", "freeze"], cwd=src, capture=True)
        except OSError:
            return "0" * 64
        return hashlib.sha256(result.output.encode()).hexdigest()

    # ---------------------------------------------------------------------------
    # Private: storage
    # ---------------------------------------------------------------------------

    async def _restore(self, request: RemoteRunRequestDto, src: Path, out: Path) -> None:
        prefix = f"{request.run_prefix}/outputs/"
        for uri in await self._store.list(prefix):
            rel = uri.removeprefix(prefix)
            if self._is_checkpoint(request, rel):
                continue
            dest = src / self.JOURNAL_DIR / rel.removeprefix("journal/") if rel.startswith("journal/") else out / rel
            await self._store.get_file(uri, dest)
            logger.info("Restored %s from a previous attempt", rel)

    async def _sync(self, request: RemoteRunRequestDto, src: Path, out: Path, include_checkpoints: bool,
                    state: RemoteRunState) -> None:
        for rel, path in await asyncio.to_thread(self._collect, src, out):
            if self._is_checkpoint(request, rel) and not include_checkpoints:
                continue
            stat = await asyncio.to_thread(path.stat)
            key = (stat.st_size, stat.st_mtime_ns)
            if self._synced.get(rel) == key:
                continue
            await self._store.put_file(f"{request.run_prefix}/outputs/{rel}", path)
            self._synced[rel] = key
        await self._status(request, state, None)

    async def _status(self, request: RemoteRunRequestDto, state: RemoteRunState, reason: EndReason | None) -> None:
        body = {"run_id": request.run_id, "state": state.value, "end_reason": reason.value if reason else None,
                "heartbeat": self._clock.now().isoformat(), "peak_vram_mib": self._peak_mib}
        await self._store.put_bytes(f"{request.run_prefix}/status.json", json.dumps(body).encode())

    async def _publish(self, request: RemoteRunRequestDto, profile: InstanceProfileDto, src: Path, out: Path,
                       reason: EndReason, driver: str, cuda: str, include_checkpoints: bool) -> None:
        outputs = []
        for rel, path in await asyncio.to_thread(self._collect, src, out):
            if self._is_checkpoint(request, rel) and not include_checkpoints:
                continue
            sha, size = await asyncio.to_thread(self._hash, path)
            outputs.append(OutputFileDto(relpath=rel, sha256=sha, bytes=size,
                                         checkpoint=self._is_checkpoint(request, rel)))
        args = {k: ("<redacted>" if k in self.REDACTED_ARGS else v) for k, v in request.stage_args.items()}
        manifest = RunManifestDto(
            run_id=request.run_id, stage=request.stage, stage_args=args, model_commit_resolved=self._commit,
            region=request.region,
            instance_type=profile.instance_type, ami_id=request.ami_id, nvidia_driver=driver, cuda_version=cuda,
            package_set_sha256=await self._package_hash(src), repo_commit=request.repo_commit,
            hourly_usd_used=profile.hourly_usd, spend_cap_usd=request.spend_cap_usd, end_reason=reason,
            red_restricted=request.red_restricted, hardware_class=profile.hardware_class,
            peak_vram_mib=self._peak_mib, outputs=outputs)
        body = manifest.model_dump_json(indent=2).encode()
        await self._store.put_bytes(f"{request.run_prefix}/manifest.json", body)
        lines = [f"{o.sha256}  outputs/{o.relpath}" for o in outputs]
        lines.append(f"{hashlib.sha256(body).hexdigest()}  manifest.json")
        await self._store.put_bytes(f"{request.run_prefix}/checksums.sha256", ("\n".join(lines) + "\n").encode())

    def _is_checkpoint(self, request: RemoteRunRequestDto, rel: str) -> bool:
        return rel.startswith(self.CHECKPOINT_PREFIXES[request.stage])

    def _collect(self, src: Path, out: Path) -> list[tuple[str, Path]]:
        journal_src = src / self.JOURNAL_DIR
        if journal_src.is_dir():
            journal_out = out / "journal"
            journal_out.mkdir(parents=True, exist_ok=True)
            for journal in journal_src.glob("*.jsonl"):
                shutil.copy2(journal, journal_out / journal.name)
        return sorted((p.relative_to(out).as_posix(), p) for p in out.rglob("*") if p.is_file())

    @staticmethod
    def _hash(path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest(), path.stat().st_size
