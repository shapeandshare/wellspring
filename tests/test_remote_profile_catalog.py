"""The instance-profile catalog (spec 027 FR-002, research R9)."""

from __future__ import annotations

from datetime import date, timedelta

from wellspring.remote.enums.profile_name import ProfileName
from wellspring.remote.enums.remote_stage import RemoteStage
from wellspring.remote.repositories.profile_catalog_repository import ProfileCatalogRepository

G_QUOTA = "Running On-Demand G and VT instances"


def test_catalog_has_exactly_the_three_g_family_profiles() -> None:
    catalog = ProfileCatalogRepository()
    by_name = {p.name: p for p in catalog.all()}
    assert set(by_name) == {ProfileName.DEV, ProfileName.FINETUNE_DEV, ProfileName.PROD}
    assert (by_name[ProfileName.DEV].instance_type, by_name[ProfileName.DEV].vcpus,
            by_name[ProfileName.DEV].gpu_count) == ("g5.xlarge", 4, 1)
    assert (by_name[ProfileName.FINETUNE_DEV].instance_type, by_name[ProfileName.FINETUNE_DEV].vcpus,
            by_name[ProfileName.FINETUNE_DEV].gpu_count) == ("g5.2xlarge", 8, 1)
    prod = by_name[ProfileName.PROD]
    assert (prod.instance_type, prod.vcpus, prod.gpu_count, prod.candidate) == ("g6e.12xlarge", 48, 4, True)
    assert all(p.quota_name == G_QUOTA for p in by_name.values())


def test_stage_placement() -> None:
    catalog = ProfileCatalogRepository()
    assert RemoteStage.ABLITERATE in catalog.get(ProfileName.PROD).stages
    assert RemoteStage.ABLITERATE in catalog.get(ProfileName.DEV).stages
    assert RemoteStage.GGUF in catalog.get(ProfileName.DEV).stages
    assert RemoteStage.GGUF in catalog.get(ProfileName.PROD).stages
    owners = [p.name for p in catalog.all() if RemoteStage.FT_TRACK_B in p.stages]
    assert owners == [ProfileName.FINETUNE_DEV]


def test_stale_prices_are_reported() -> None:
    catalog = ProfileCatalogRepository()
    fresh = {p.price_checked for p in catalog.all()}
    newest = max(fresh)
    assert catalog.stale_prices(today=newest) == [p for p in catalog.all() if (newest - p.price_checked).days > 90]
    far_future = newest + timedelta(days=365)
    assert {p.name for p in catalog.stale_prices(today=far_future)} == set(ProfileName)
    assert isinstance(newest, date)


def test_prod_reserves_time_to_upload_its_checkpoint() -> None:
    catalog = ProfileCatalogRepository()
    assert catalog.get(ProfileName.PROD).sync_margin_minutes >= 30
    assert all(p.sync_margin_minutes >= 5 for p in catalog.all())
