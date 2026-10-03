"""Launch a remote run: refuse before spending, reuse a live instance, resume an unfinished run (spec 027 FR-004)."""

from __future__ import annotations

import logging
from pathlib import Path

from ..._shared.types.object_store import ObjectStore
from ..dtos.instance_profile_dto import InstanceProfileDto
from ..dtos.remote_run_dto import RemoteRunDto
from ..dtos.remote_run_request_dto import RemoteRunRequestDto
from ..enums.remote_run_state import RemoteRunState
from ..errors.dirty_tree_error import DirtyTreeError
from ..errors.quota_insufficient_error import QuotaInsufficientError
from ..errors.request_invalid_error import RequestInvalidError
from ..errors.run_state_conflict_error import ResumeMismatchError, RunAlreadyFinishedError, RunStillStoppingError
from ..repositories.profile_catalog_repository import ProfileCatalogRepository
from ..types.instance_provider import InstanceProvider
from ..types.source_archiver import SourceArchiver
from .bootstrap_service import BootstrapService
from .spend_guard_service import SpendGuardService

logger = logging.getLogger(__name__)


class RemoteRunService:
    """Orders every check so that a refusal never costs money (Article VIII)."""

    RESUME_FIELDS = ("stage", "profile", "stage_args")

    def __init__(self, provider: InstanceProvider, store: ObjectStore, archiver: SourceArchiver,
                 catalog: ProfileCatalogRepository, guard: SpendGuardService, bootstrap: BootstrapService,
                 scratch: Path) -> None:
        """Wire the collaborators.

        Parameters
        ----------
        provider : InstanceProvider
            The cloud.
        store : ObjectStore
            Run storage (``request.json``, ``source.tar.gz``, outputs).
        archiver : SourceArchiver
            Packages the repository at ``HEAD``.
        catalog : ProfileCatalogRepository
            Instance profiles.
        guard : SpendGuardService
            Spend cap → runtime limit.
        bootstrap : BootstrapService
            Renders the user-data.
        scratch : Path
            Local directory for the source archive.
        """
        self._provider = provider
        self._store = store
        self._archiver = archiver
        self._catalog = catalog
        self._guard = guard
        self._bootstrap = bootstrap
        self._scratch = scratch

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def run(self, request: RemoteRunRequestDto, repo: Path) -> RemoteRunDto:
        """Launch ``request`` (or reuse/resume it) from ``repo``.

        Returns
        -------
        RemoteRunDto
            The live or newly launched instance.

        Raises
        ------
        RunAlreadyFinishedError, RunStillStoppingError, ResumeMismatchError, DirtyTreeError, RequestInvalidError,
        QuotaInsufficientError, SpendCapTooLowError
            Before anything is launched.
        CloudLaunchError
            If the cloud rejects the launch; nothing is left running.
        """
        prefix = request.run_prefix
        if await self._store.exists(f"{prefix}/checksums.sha256"):
            raise RunAlreadyFinishedError(request.run_id)
        live = await self._provider.find_live(request.region, request.run_id)
        if live:
            if live[0].state is RemoteRunState.TERMINATED:
                raise RunStillStoppingError(request.run_id, live[0].instance_id or "?")
            logger.info("Reusing live instance %s for %s", live[0].instance_id, request.run_id)
            return live[0]
        stored: RemoteRunRequestDto | None = None
        if await self._store.exists(f"{prefix}/request.json"):
            stored = await self._check_resume(request, prefix)
        dirty = await self._archiver.dirty_files(repo)
        if dirty:
            raise DirtyTreeError(dirty)
        profile = self._catalog.get(request.profile)
        if request.stage not in profile.stages:
            raise RequestInvalidError("profile", f"{profile.name.value} does not run stage {request.stage.value}")
        await self._check_quota(request.region, profile)
        max_minutes = self._guard.max_minutes(request.spend_cap_usd, profile.hourly_usd)

        ami_id = await self._provider.resolve_ami(request.region)
        archive = self._scratch / request.run_id / "source.tar.gz"
        commit = await self._archiver.archive(repo, archive)
        if stored is not None and stored.repo_commit and stored.repo_commit != commit:
            raise ResumeMismatchError(request.run_id, "repo_commit")
        await self._store.put_file(f"{prefix}/source.tar.gz", archive)
        final = request.model_copy(update={"repo_commit": commit, "ami_id": ami_id})
        await self._store.put_bytes(f"{prefix}/request.json", final.model_dump_json(indent=2).encode())
        user_data = self._bootstrap.render(final, max_minutes)
        instance_id = await self._provider.launch(final, profile, user_data)
        logger.info("Launched %s for %s; hard stop after %d min", instance_id, request.run_id, max_minutes)
        return RemoteRunDto(run_id=request.run_id, instance_id=instance_id, profile=profile.name,
                            region=request.region, state=RemoteRunState.PROVISIONING)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    async def _check_resume(self, request: RemoteRunRequestDto, prefix: str) -> RemoteRunRequestDto:
        stored = RemoteRunRequestDto.model_validate_json(await self._store.get_bytes(f"{prefix}/request.json"))
        for field in self.RESUME_FIELDS:
            if getattr(stored, field) != getattr(request, field):
                raise ResumeMismatchError(request.run_id, field)
        logger.info("Resuming unfinished run %s from its synced outputs", request.run_id)
        return stored

    async def _check_quota(self, region: str, profile: InstanceProfileDto) -> None:
        applied = await self._provider.applied_quota(region, profile.quota_name)
        in_use = await self._provider.vcpus_in_use(region, profile.quota_families)
        available = applied - in_use
        if available < profile.vcpus:
            raise QuotaInsufficientError(profile.quota_name, profile.vcpus, max(available, 0))
