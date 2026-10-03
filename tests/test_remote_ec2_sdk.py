"""Ec2Sdk request shapes, checked offline with botocore's Stubber (spec 027 research R1/R3/R6/R8)."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal

import boto3
import pytest
from botocore.client import BaseClient
from botocore.stub import Stubber

from wellspring._shared.errors.cloud_api_error import CloudApiError
from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_run_state import RemoteRunState
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.errors.capacity_unavailable_error import CapacityUnavailableError
from wellspring.remote.repositories.profile_catalog_repository import ProfileCatalogRepository
from wellspring.remote.sdks.ec2_sdk import Ec2Sdk

REGION = "us-east-1"
AMI_PARAM = "/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-24.04/latest/ami-id"
TAGS = [
    {"Key": "wellspring:managed", "Value": "true"},
    {"Key": "wellspring:run-id", "Value": "rehearsal-1"},
    {"Key": "wellspring:profile", "Value": "dev"},
    {"Key": "wellspring:stage", "Value": "abliterate"},
    {"Key": "wellspring:repo-commit", "Value": "abc123"},
]


class _Clients:
    """One stubbed client per service, handed to Ec2Sdk as its client factory."""

    def __init__(self) -> None:
        self.clients = {name: boto3.client(name, region_name=REGION, aws_access_key_id="x",
                                           aws_secret_access_key="x")
                        for name in ("ec2", "ssm", "service-quotas")}
        self.stubs = {name: Stubber(c) for name, c in self.clients.items()}

    def __call__(self, service: str, region: str) -> BaseClient:
        assert region == REGION
        return self.clients[service]


@pytest.fixture
def clients() -> Iterator[_Clients]:
    c = _Clients()
    for s in c.stubs.values():
        s.activate()
    yield c
    for s in c.stubs.values():
        s.assert_no_pending_responses()
        s.deactivate()


def _request() -> RemoteRunRequestDto:
    return RemoteRunRequestDto(run_id="rehearsal-1", stage=RemoteStage.ABLITERATE, profile=ProfileName.DEV,
                               region=REGION, spend_cap_usd=Decimal("5"), storage_uri="s3://bkt/p",
                               instance_profile="wellspring-runner", red_restricted=False,
                               stage_args={"MODEL": "m"}, repo_commit="abc123", ami_id="ami-123")


def test_launch_sends_self_terminating_tagged_request(clients: _Clients) -> None:
    profile = ProfileCatalogRepository().get(ProfileName.DEV)
    clients.stubs["ec2"].add_response("describe_images", {"Images": [{"RootDeviceName": "/dev/xvda"}]},
                                      {"ImageIds": ["ami-123"]})
    clients.stubs["ec2"].add_response("run_instances", {"Instances": [{"InstanceId": "i-1"}]}, {
        "ImageId": "ami-123", "InstanceType": "g5.xlarge", "MinCount": 1, "MaxCount": 1,
        "IamInstanceProfile": {"Name": "wellspring-runner"},
        "InstanceInitiatedShutdownBehavior": "terminate",
        "UserData": "#!/bin/bash\n",
        "MetadataOptions": {"HttpTokens": "required"},
        "BlockDeviceMappings": [{"DeviceName": "/dev/xvda", "Ebs": {
            "VolumeSize": profile.root_disk_gib, "VolumeType": "gp3", "DeleteOnTermination": True}}],
        "TagSpecifications": [{"ResourceType": "instance", "Tags": TAGS},
                              {"ResourceType": "volume", "Tags": TAGS}],
    })
    instance_id = asyncio.run(Ec2Sdk(clients).launch(_request(), profile, "#!/bin/bash\n"))
    assert instance_id == "i-1"


def test_capacity_error_maps_to_typed_error(clients: _Clients) -> None:
    profile = ProfileCatalogRepository().get(ProfileName.DEV)
    clients.stubs["ec2"].add_response("describe_images", {"Images": [{"RootDeviceName": "/dev/sda1"}]},
                                      {"ImageIds": ["ami-123"]})
    clients.stubs["ec2"].add_client_error("run_instances", service_error_code="InsufficientInstanceCapacity",
                                          service_message="We currently do not have sufficient g5.xlarge capacity")
    with pytest.raises(CapacityUnavailableError) as exc:
        asyncio.run(Ec2Sdk(clients).launch(_request(), profile, "#!/bin/bash\n"))
    assert "sufficient g5.xlarge capacity" in str(exc.value)


def test_find_live_filters_by_tag_and_live_states(clients: _Clients) -> None:
    launched = datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)
    clients.stubs["ec2"].add_response("describe_instances", {"Reservations": [{"Instances": [{
        "InstanceId": "i-1", "InstanceType": "g5.xlarge", "LaunchTime": launched,
        "State": {"Name": "running", "Code": 16},
        "Tags": TAGS}]}]}, {"Filters": [
            {"Name": "tag:wellspring:managed", "Values": ["true"]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "shutting-down"]},
            {"Name": "tag:wellspring:run-id", "Values": ["rehearsal-1"]}]})
    live = asyncio.run(Ec2Sdk(clients).find_live(REGION, "rehearsal-1"))
    assert [(r.run_id, r.instance_id, r.profile, r.state, r.launched_at) for r in live] == [
        ("rehearsal-1", "i-1", ProfileName.DEV, RemoteRunState.RUNNING, launched)]


def test_resolve_ami_reads_the_public_dlami_parameter(clients: _Clients) -> None:
    clients.stubs["ssm"].add_response("get_parameter", {"Parameter": {"Value": "ami-999"}}, {"Name": AMI_PARAM})
    assert asyncio.run(Ec2Sdk(clients).resolve_ami(REGION)) == "ami-999"


def test_quota_is_looked_up_by_name_not_code(clients: _Clients) -> None:
    clients.stubs["service-quotas"].add_response("list_service_quotas", {"Quotas": [
        {"QuotaName": "Running On-Demand P instances", "Value": 0.0},
        {"QuotaName": "Running On-Demand G and VT instances", "Value": 32.0}]}, {"ServiceCode": "ec2"})
    assert asyncio.run(Ec2Sdk(clients).applied_quota(REGION, "Running On-Demand G and VT instances")) == 32


def test_vcpus_in_use_counts_matching_families_only(clients: _Clients) -> None:
    clients.stubs["ec2"].add_response("describe_instances", {"Reservations": [{"Instances": [
        {"InstanceId": "i-1", "InstanceType": "g5.xlarge", "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 2}},
        {"InstanceId": "i-2", "InstanceType": "m6i.large", "CpuOptions": {"CoreCount": 1, "ThreadsPerCore": 2}},
        {"InstanceId": "i-3", "InstanceType": "vt1.3xlarge", "CpuOptions": {"CoreCount": 6, "ThreadsPerCore": 2}},
    ]}]}, {"Filters": [{"Name": "instance-state-name", "Values": ["pending", "running"]}]})
    assert asyncio.run(Ec2Sdk(clients).vcpus_in_use(REGION, ("g", "vt"))) == 16


def test_terminate_sends_instance_ids(clients: _Clients) -> None:
    clients.stubs["ec2"].add_response("terminate_instances", {"TerminatingInstances": []},
                                      {"InstanceIds": ["i-1", "i-2"]})
    asyncio.run(Ec2Sdk(clients).terminate(REGION, ["i-1", "i-2"]))


def test_any_api_error_becomes_a_typed_cloud_error(clients: _Clients) -> None:
    clients.stubs["ec2"].add_client_error("describe_instances", service_error_code="UnauthorizedOperation",
                                          service_message="You are not authorized")
    with pytest.raises(CloudApiError) as exc:
        asyncio.run(Ec2Sdk(clients).find_live(REGION, None))
    assert exc.value.code == "UnauthorizedOperation" and "not authorized" in str(exc.value)
