"""remote-status and remote-down (spec 027 FR-013, Story 2)."""

from __future__ import annotations

import json
from datetime import datetime

from ..._shared.types.object_store import ObjectStore
from ..dtos.remote_run_dto import RemoteRunDto
from ..enums.end_reason import EndReason
from ..enums.remote_run_state import RemoteRunState
from ..repositories.profile_catalog_repository import ProfileCatalogRepository
from ..types.clock import Clock
from ..types.instance_provider import InstanceProvider
from .spend_guard_service import SpendGuardService


class RemoteStatusService:
    """What is running, what it has cost so far, and how a finished run ended."""

    ALL = "all-managed"

    def __init__(self, provider: InstanceProvider, store: ObjectStore, catalog: ProfileCatalogRepository,
                 guard: SpendGuardService, clock: Clock) -> None:
        """Wire the collaborators.

        Parameters
        ----------
        provider : InstanceProvider
            The cloud.
        store : ObjectStore
            Run storage (``status.json``).
        catalog : ProfileCatalogRepository
            Prices per profile.
        guard : SpendGuardService
            Elapsed time → cost.
        clock : Clock
            Current time.
        """
        self._provider = provider
        self._store = store
        self._catalog = catalog
        self._guard = guard
        self._clock = clock

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def status(self, region: str, storage_uri: str | None, run_id: str | None) -> list[RemoteRunDto]:
        """Live managed instances, plus ``run_id``'s stored outcome if it is no longer live.

        A run that is gone but never wrote an end reason (or never wrote
        ``status.json`` at all: the bootstrap failed before the agent started)
        was stopped by the ``shutdown -h +N`` backstop, so it is reported as
        ``BACKSTOP``.
        """
        now = self._clock.now()
        rows = [self._costed(row, now) for row in await self._provider.find_live(region, None)]
        if run_id and storage_uri and not any(r.run_id == run_id for r in rows):
            prefix = f"{storage_uri.rstrip('/')}/{run_id}"
            reason: str | None = None
            if await self._store.exists(f"{prefix}/status.json"):
                reason = json.loads(await self._store.get_bytes(f"{prefix}/status.json")).get("end_reason")
            elif not await self._store.exists(f"{prefix}/request.json"):
                return rows
            rows.append(RemoteRunDto(run_id=run_id, region=region, state=RemoteRunState.TERMINATED,
                                     end_reason=EndReason(reason) if reason else EndReason.BACKSTOP))
        return rows

    async def down(self, region: str, run_id: str) -> list[str]:
        """Terminate ``run_id``'s instances, or every managed one for ``all-managed``; idempotent."""
        live = await self._provider.find_live(region, None if run_id == self.ALL else run_id)
        ids = [r.instance_id for r in live if r.instance_id]
        await self._provider.terminate(region, ids)
        return ids

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    def _costed(self, row: RemoteRunDto, now: datetime) -> RemoteRunDto:
        if row.launched_at is None or row.profile is None:
            return row
        minutes = max(int((now - row.launched_at).total_seconds() // 60), 0)
        hourly = self._catalog.get(row.profile).hourly_usd
        return row.model_copy(update={"elapsed_minutes": minutes,
                                      "estimated_cost_usd": self._guard.estimated_cost(minutes, hourly)})
