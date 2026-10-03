"""In-memory InstanceProvider with a call log, configurable quota and capacity failures."""

from __future__ import annotations

from datetime import datetime, timezone

from wellspring.remote.dtos.instance_profile_dto import InstanceProfileDto
from wellspring.remote.dtos.remote_run_dto import RemoteRunDto
from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.remote_run_state import RemoteRunState
from wellspring.remote.errors.capacity_unavailable_error import CapacityUnavailableError


class FakeInstanceProvider:
    """Implements ``InstanceProvider``; ``calls`` records method names in order."""

    def __init__(self, applied: int = 64, in_use: int = 0, no_capacity: bool = False) -> None:
        self.applied = applied
        self.in_use = in_use
        self.no_capacity = no_capacity
        self.calls: list[str] = []
        self.live: dict[str, tuple[RemoteRunRequestDto, InstanceProfileDto]] = {}
        self.user_data: dict[str, str] = {}
        self.terminated: list[str] = []
        self._next = 0
        self.stopping = False

    async def resolve_ami(self, region: str) -> str:
        self.calls.append("resolve_ami")
        return "ami-fake"

    async def applied_quota(self, region: str, quota_name: str) -> int:
        self.calls.append("applied_quota")
        return self.applied

    async def vcpus_in_use(self, region: str, families: tuple[str, ...]) -> int:
        self.calls.append("vcpus_in_use")
        return self.in_use + sum(p.vcpus for _, p in self.live.values()
                                 if p.instance_type.startswith(families))

    async def launch(self, request: RemoteRunRequestDto, profile: InstanceProfileDto, user_data: str) -> str:
        self.calls.append("launch")
        if self.no_capacity:
            raise CapacityUnavailableError(profile.instance_type, "InsufficientInstanceCapacity", "none left")
        self._next += 1
        iid = f"i-{self._next}"
        self.live[iid] = (request, profile)
        self.user_data[iid] = user_data
        return iid

    async def find_live(self, region: str, run_id: str | None) -> list[RemoteRunDto]:
        self.calls.append("find_live")
        return [RemoteRunDto(run_id=req.run_id, instance_id=iid, profile=prof.name, region=region,
                             state=RemoteRunState.TERMINATED if self.stopping else RemoteRunState.RUNNING,
                             launched_at=datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc))
                for iid, (req, prof) in self.live.items() if run_id is None or req.run_id == run_id]

    async def terminate(self, region: str, instance_ids: list[str]) -> None:
        self.calls.append("terminate")
        for iid in instance_ids:
            if self.live.pop(iid, None) is not None:
                self.terminated.append(iid)
