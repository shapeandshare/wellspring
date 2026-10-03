"""The instance profiles a remote run may use (spec 027 FR-002, research R9)."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from ..dtos.instance_profile_dto import InstanceProfileDto
from ..enums.profile_name import ProfileName
from ..enums.remote_stage import RemoteStage

logger = logging.getLogger(__name__)


class ProfileCatalogRepository:
    """Fixed catalog. Only G-family instances; larger ones are added only when measured (FR-002)."""

    G_QUOTA = "Running On-Demand G and VT instances"
    STALE_DAYS = 90

    # On-demand Linux prices, us-east-1, checked 2026-10-02 on third-party
    # aggregators (not the AWS Pricing API): g5 sizes on doit.com, g6e.12xlarge
    # on cloudprice.net and devzero.io. Re-check before trusting a cap-derived
    # runtime (research R9).
    PROFILES: tuple[InstanceProfileDto, ...] = (
        InstanceProfileDto(
            name=ProfileName.DEV, instance_type="g5.xlarge", vcpus=4, gpu_count=1, gpu_mem_gib=22.35,
            root_disk_gib=200, work_disk_gib=150, sync_margin_minutes=10, hourly_usd=Decimal("1.006"), price_checked=date(2026, 10, 2),
            price_source="doit.com listing, us-east-1",
            quota_name=G_QUOTA, quota_families=("g", "vt"),
            stages=frozenset({RemoteStage.ABLITERATE, RemoteStage.GGUF}), candidate=False),
        InstanceProfileDto(
            name=ProfileName.FINETUNE_DEV, instance_type="g5.2xlarge", vcpus=8, gpu_count=1, gpu_mem_gib=22.35,
            root_disk_gib=200, work_disk_gib=150, sync_margin_minutes=10, hourly_usd=Decimal("1.212"), price_checked=date(2026, 10, 2),
            price_source="doit.com listing, us-east-1",
            quota_name=G_QUOTA, quota_families=("g", "vt"),
            stages=frozenset({RemoteStage.FT_TRACK_B}), candidate=False),
        InstanceProfileDto(
            name=ProfileName.PROD, instance_type="g6e.12xlarge", vcpus=48, gpu_count=4, gpu_mem_gib=44.7,
            root_disk_gib=300, work_disk_gib=400, sync_margin_minutes=30, hourly_usd=Decimal("10.4926"), price_checked=date(2026, 10, 2),
            price_source="cloudprice.net / DevZero listings, us-east-1",
            quota_name=G_QUOTA, quota_families=("g", "vt"),
            stages=frozenset({RemoteStage.ABLITERATE, RemoteStage.GGUF}), candidate=True),
    )

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def all(self) -> list[InstanceProfileDto]:
        """Every profile, in catalog order."""
        return list(self.PROFILES)

    def get(self, name: ProfileName) -> InstanceProfileDto:
        """The profile called ``name``."""
        profile = next(p for p in self.PROFILES if p.name is name)
        if profile in self.stale_prices(today=date.today()):
            logger.warning("Price for %s was last checked %s; the spend-cap runtime may be off.",
                           profile.instance_type, profile.price_checked)
        return profile

    def stale_prices(self, today: date) -> list[InstanceProfileDto]:
        """Profiles whose price is older than :attr:`STALE_DAYS` on ``today``."""
        return [p for p in self.PROFILES if (today - p.price_checked).days > self.STALE_DAYS]
