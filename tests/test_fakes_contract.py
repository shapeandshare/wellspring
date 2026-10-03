"""The hermetic fakes must honour the Protocols the real SDKs implement (spec 027 FR-015)."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path

from fakes.dir_object_store import DirObjectStore
from fakes.fake_clock import FakeClock
from fakes.fake_instance_provider import FakeInstanceProvider

from wellspring._shared.types.object_store import ObjectStore
from wellspring.remote.dtos.remote_run_request_dto import RemoteRunRequestDto
from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.repositories.profile_catalog_repository import ProfileCatalogRepository
from wellspring.remote.types.clock import Clock
from wellspring.remote.types.instance_provider import InstanceProvider


def test_dir_object_store_round_trips(tmp_path: Path) -> None:
    store: ObjectStore = DirObjectStore(tmp_path)

    async def go() -> None:
        await store.put_bytes("s3://b/p/x.json", b"{}")
        src = tmp_path / "local.txt"
        src.write_text("hi")
        await store.put_file("s3://b/p/sub/y.txt", src)
        assert await store.exists("s3://b/p/x.json")
        assert not await store.exists("s3://b/p/missing")
        assert await store.get_bytes("s3://b/p/x.json") == b"{}"
        dest = tmp_path / "out" / "y.txt"
        await store.get_file("s3://b/p/sub/y.txt", dest)
        assert dest.read_text() == "hi"
        assert await store.list("s3://b/p/") == ["s3://b/p/sub/y.txt", "s3://b/p/x.json"]

    asyncio.run(go())


def test_fake_provider_satisfies_the_protocol() -> None:
    provider: InstanceProvider = FakeInstanceProvider(applied=8)
    req = RemoteRunRequestDto(run_id="abc", stage=RemoteStage.ABLITERATE, profile=ProfileName.DEV,
                              region="us-east-1", spend_cap_usd=Decimal("1"), storage_uri="s3://bkt/p",
                              instance_profile="ip", red_restricted=False, stage_args={})
    profile = ProfileCatalogRepository().get(ProfileName.DEV)

    async def go() -> None:
        assert await provider.resolve_ami("us-east-1") == "ami-fake"
        assert await provider.applied_quota("us-east-1", profile.quota_name) == 8
        iid = await provider.launch(req, profile, "#!/bin/bash\n")
        assert await provider.vcpus_in_use("us-east-1", ("g",)) == 4
        assert [r.instance_id for r in await provider.find_live("us-east-1", "abc")] == [iid]
        await provider.terminate("us-east-1", [iid])
        assert await provider.find_live("us-east-1", None) == []

    asyncio.run(go())


def test_fake_clock_advances_only_through_sleep() -> None:
    clock: Clock = FakeClock()
    start = clock.now()

    async def go() -> None:
        await clock.sleep(90)

    asyncio.run(go())
    assert (clock.now() - start).total_seconds() == 90
