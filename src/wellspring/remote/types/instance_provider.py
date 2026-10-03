"""Protocol for the cloud that rents instances."""

from __future__ import annotations

from typing import Protocol

from ..dtos.instance_profile_dto import InstanceProfileDto
from ..dtos.remote_run_dto import RemoteRunDto
from ..dtos.remote_run_request_dto import RemoteRunRequestDto


class InstanceProvider(Protocol):
    """Launch, find and terminate tagged instances, and report quota."""

    async def resolve_ami(self, region: str) -> str:
        """Current machine-image ID for the GPU base image in ``region``."""
        ...

    async def applied_quota(self, region: str, quota_name: str) -> int:
        """Applied vCPU quota named ``quota_name`` (0 if the account has none)."""
        ...

    async def vcpus_in_use(self, region: str, families: tuple[str, ...]) -> int:
        """vCPUs of pending/running instances whose type starts with one of ``families``."""
        ...

    async def launch(self, request: RemoteRunRequestDto, profile: InstanceProfileDto, user_data: str) -> str:
        """Launch one self-terminating, tagged instance and return its ID."""
        ...

    async def find_live(self, region: str, run_id: str | None) -> list[RemoteRunDto]:
        """Live managed instances, optionally only those tagged with ``run_id``."""
        ...

    async def terminate(self, region: str, instance_ids: list[str]) -> None:
        """Terminate the instances; their volumes are deleted with them."""
        ...
