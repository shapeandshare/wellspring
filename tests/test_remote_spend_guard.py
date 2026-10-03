"""Spend cap → hard runtime limit and cost estimates (spec 027 SC-003, research R3)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from wellspring._shared.errors.missing_setting_error import SpendCapTooLowError
from wellspring.remote.services.spend_guard_service import SpendGuardService


def test_max_minutes_is_floor_of_cap_over_hourly_minus_boot_overhead() -> None:
    # Billing starts at "running", minutes before user-data can arm the backstop.
    assert SpendGuardService().max_minutes(Decimal("5"), Decimal("1.006")) == 298 - SpendGuardService.BOOT_MINUTES


def test_cap_below_ten_minutes_is_refused_naming_both_numbers() -> None:
    with pytest.raises(SpendCapTooLowError) as exc:
        SpendGuardService().max_minutes(Decimal("1"), Decimal("10.4926"))
    assert exc.value.minutes == 5 - SpendGuardService.BOOT_MINUTES
    assert f"buys only {exc.value.minutes} min" in str(exc.value)


def test_estimated_cost_rounds_up_to_the_cent() -> None:
    guard = SpendGuardService()
    assert guard.estimated_cost(60, Decimal("1.006")) == Decimal("1.01")
    assert guard.estimated_cost(1, Decimal("1.006")) == Decimal("0.02")
    assert guard.estimated_cost(0, Decimal("1.006")) == Decimal("0.00")
