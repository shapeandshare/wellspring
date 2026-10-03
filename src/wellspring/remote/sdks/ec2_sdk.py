"""EC2, SSM and Service Quotas behind :class:`InstanceProvider` (spec 027 research R1, R3, R6, R8)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime

from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from ..._shared.errors.cloud_api_error import CloudApiError

from ..dtos.instance_profile_dto import InstanceProfileDto
from ..dtos.remote_run_dto import RemoteRunDto
from ..dtos.remote_run_request_dto import RemoteRunRequestDto
from ..enums.profile_name import ProfileName
from ..enums.remote_run_state import RemoteRunState
from ..errors.capacity_unavailable_error import CapacityUnavailableError, CloudLaunchError

ClientFactory = Callable[[str, str], BaseClient]


class Ec2Sdk:
    """Implements :class:`~wellspring.remote.types.instance_provider.InstanceProvider` over boto3."""

    AMI_PARAMETER = "/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-24.04/latest/ami-id"
    LIVE_STATES = ["pending", "running", "stopping", "shutting-down"]
    CAPACITY_CODES = frozenset({"InsufficientInstanceCapacity", "InsufficientCapacity", "Unsupported"})
    _STATE = {"pending": RemoteRunState.PROVISIONING, "running": RemoteRunState.RUNNING}

    def __init__(self, clients: ClientFactory) -> None:
        """Keep the client factory.

        Parameters
        ----------
        clients : Callable[[str, str], BaseClient]
            ``(service, region) -> client``; real code passes ``boto3.client``-backed
            factories, tests pass stubbed clients.
        """
        self._clients = clients

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def resolve_ami(self, region: str) -> str:
        """Latest DLAMI Base OSS NVIDIA (Ubuntu 24.04) image ID, from its public SSM parameter."""
        response = await self._call("ssm", region, "get_parameter", Name=self.AMI_PARAMETER)
        return str(self._mapping(response, "Parameter").get("Value", ""))

    async def applied_quota(self, region: str, quota_name: str) -> int:
        """Applied value of the EC2 quota called ``quota_name``, looked up by name (research R8)."""
        token: str | None = None
        while True:
            kwargs: dict[str, str] = {"ServiceCode": "ec2"}
            if token:
                kwargs["NextToken"] = token
            page = await self._call("service-quotas", region, "list_service_quotas", **kwargs)
            for quota in self._list(page, "Quotas"):
                if quota.get("QuotaName") == quota_name:
                    return int(float(str(quota.get("Value", 0))))
            token = self._token(page)
            if not token:
                return 0

    async def vcpus_in_use(self, region: str, families: tuple[str, ...]) -> int:
        """Sum of vCPUs of pending/running instances whose type starts with ``families``."""
        total = 0
        for instance in await self._describe(region, [{"Name": "instance-state-name",
                                                       "Values": ["pending", "running"]}]):
            if str(instance.get("InstanceType", "")).startswith(families):
                cpu = self._mapping(instance, "CpuOptions")
                total += int(str(cpu.get("CoreCount", 0))) * int(str(cpu.get("ThreadsPerCore", 1)))
        return total

    async def launch(self, request: RemoteRunRequestDto, profile: InstanceProfileDto, user_data: str) -> str:
        """Launch one instance that terminates itself (and its volumes) on any OS shutdown.

        Raises
        ------
        CapacityUnavailableError
            If AWS has no capacity for the instance type.
        CloudLaunchError
            For any other launch rejection.
        """
        images = await self._call("ec2", request.region, "describe_images", ImageIds=[request.ami_id])
        image_list = images.get("Images")
        first = image_list[0] if isinstance(image_list, list) and image_list else {}
        root_device = str(first.get("RootDeviceName", "")) if isinstance(first, Mapping) else ""
        if not root_device:
            raise CloudLaunchError(profile.instance_type, "ImageNotFound", f"no root device for {request.ami_id}")
        ec2 = self._clients("ec2", request.region)
        tags = [{"Key": "wellspring:managed", "Value": "true"},
                {"Key": "wellspring:run-id", "Value": request.run_id},
                {"Key": "wellspring:profile", "Value": profile.name.value},
                {"Key": "wellspring:stage", "Value": request.stage.value},
                {"Key": "wellspring:repo-commit", "Value": request.repo_commit}]
        try:
            response = await asyncio.to_thread(
                ec2.run_instances,
                ImageId=request.ami_id, InstanceType=profile.instance_type, MinCount=1, MaxCount=1,
                IamInstanceProfile={"Name": request.instance_profile},
                InstanceInitiatedShutdownBehavior="terminate",
                UserData=user_data,
                MetadataOptions={"HttpTokens": "required"},
                BlockDeviceMappings=[{"DeviceName": root_device, "Ebs": {
                    "VolumeSize": profile.root_disk_gib, "VolumeType": "gp3", "DeleteOnTermination": True}}],
                TagSpecifications=[{"ResourceType": "instance", "Tags": tags},
                                   {"ResourceType": "volume", "Tags": tags}])
        except ClientError as exc:
            error = exc.response.get("Error", {})
            code, message = str(error.get("Code", "")), str(error.get("Message", ""))
            if code in self.CAPACITY_CODES:
                raise CapacityUnavailableError(profile.instance_type, code, message) from exc
            raise CloudLaunchError(profile.instance_type, code, message) from exc
        except BotoCoreError as exc:
            raise CloudLaunchError(profile.instance_type, type(exc).__name__, str(exc)) from exc
        return str(response["Instances"][0]["InstanceId"])

    async def find_live(self, region: str, run_id: str | None) -> list[RemoteRunDto]:
        """Managed instances in a live state, optionally only ``run_id``'s."""
        filters = [{"Name": "tag:wellspring:managed", "Values": ["true"]},
                   {"Name": "instance-state-name", "Values": self.LIVE_STATES}]
        if run_id is not None:
            filters.append({"Name": "tag:wellspring:run-id", "Values": [run_id]})
        rows = []
        for instance in await self._describe(region, filters):
            tags = self._tags(instance)
            launched = instance.get("LaunchTime")
            profile = tags.get("wellspring:profile", "")
            state = str(self._mapping(instance, "State").get("Name", ""))
            rows.append(RemoteRunDto(
                run_id=tags.get("wellspring:run-id", "?"), instance_id=str(instance.get("InstanceId", "")),
                profile=ProfileName(profile) if profile in {p.value for p in ProfileName} else None,
                region=region, state=self._STATE.get(state, RemoteRunState.TERMINATED),
                launched_at=launched if isinstance(launched, datetime) else None))
        return rows

    async def terminate(self, region: str, instance_ids: list[str]) -> None:
        """Terminate ``instance_ids`` (their volumes go with them: ``DeleteOnTermination``)."""
        if instance_ids:
            await self._call("ec2", region, "terminate_instances", InstanceIds=instance_ids)

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    async def _call(self, service: str, region: str, operation: str, **kwargs: object) -> Mapping[str, object]:
        client = self._clients(service, region)
        try:
            response = await asyncio.to_thread(getattr(client, operation), **kwargs)
        except ClientError as exc:
            error = exc.response.get("Error", {})
            raise CloudApiError(service, operation, str(error.get("Code", "")), str(error.get("Message", ""))) from exc
        except BotoCoreError as exc:
            raise CloudApiError(service, operation, type(exc).__name__, str(exc)) from exc
        return response if isinstance(response, Mapping) else {}

    async def _describe(self, region: str, filters: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
        instances: list[Mapping[str, object]] = []
        token: str | None = None
        while True:
            kwargs: dict[str, object] = {"Filters": filters}
            if token:
                kwargs["NextToken"] = token
            page = await self._call("ec2", region, "describe_instances", **kwargs)
            for reservation in self._list(page, "Reservations"):
                instances.extend(self._list(reservation, "Instances"))
            token = self._token(page)
            if not token:
                return instances

    @staticmethod
    def _list(source: Mapping[str, object], key: str) -> list[Mapping[str, object]]:
        value = source.get(key)
        return [v for v in value if isinstance(v, Mapping)] if isinstance(value, list) else []

    @staticmethod
    def _token(page: Mapping[str, object]) -> str | None:
        token = page.get("NextToken")
        return token if isinstance(token, str) and token else None

    @staticmethod
    def _mapping(source: Mapping[str, object], key: str) -> Mapping[str, object]:
        value = source.get(key)
        return value if isinstance(value, Mapping) else {}

    @staticmethod
    def _tags(instance: Mapping[str, object]) -> dict[str, str]:
        raw = instance.get("Tags")
        if not isinstance(raw, list):
            return {}
        return {str(t.get("Key")): str(t.get("Value")) for t in raw if isinstance(t, Mapping)}
