"""Spend cap → runtime limit, and elapsed time → cost (spec 027 research R3)."""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

from ..._shared.errors.missing_setting_error import SpendCapTooLowError


class SpendGuardService:
    """Pure arithmetic; the instance enforces the result with ``shutdown -h +N``."""

    MIN_MINUTES = 10
    # Billing starts when the instance is running, before cloud-init reaches the
    # shutdown line; this headroom keeps total billed time inside the cap.
    BOOT_MINUTES = 3

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def max_minutes(self, cap_usd: Decimal, hourly_usd: Decimal) -> int:
        """Whole minutes the cap buys.

        Parameters
        ----------
        cap_usd : Decimal
            Spend cap in USD.
        hourly_usd : Decimal
            Instance price per hour in USD.

        Returns
        -------
        int
            ``floor(cap / hourly * 60) - BOOT_MINUTES``.

        Raises
        ------
        SpendCapTooLowError
            If that is under :attr:`MIN_MINUTES`.
        """
        minutes = int((cap_usd / hourly_usd * 60).to_integral_value(rounding=ROUND_FLOOR)) - self.BOOT_MINUTES
        if minutes < self.MIN_MINUTES:
            raise SpendCapTooLowError(cap_usd, hourly_usd, minutes, self.MIN_MINUTES)
        return minutes

    def estimated_cost(self, elapsed_minutes: int, hourly_usd: Decimal) -> Decimal:
        """Cost of ``elapsed_minutes`` at ``hourly_usd``, rounded up to the cent."""
        cost = Decimal(elapsed_minutes) * hourly_usd / 60
        return cost.quantize(Decimal("0.01"), rounding=ROUND_CEILING)
