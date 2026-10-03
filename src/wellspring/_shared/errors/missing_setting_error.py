"""A required setting has no value, or a value that cannot work."""

from __future__ import annotations

from decimal import Decimal

from .refused_error import RefusedError


class MissingSettingError(RefusedError):
    """A required setting was not supplied. There are deliberately no defaults (spec 027 FR-003)."""

    def __init__(self, name: str, hint: str = "") -> None:
        """Name the missing setting.

        Parameters
        ----------
        name : str
            Variable or option name, e.g. ``REMOTE_REGION``.
        hint : str, optional
            How to supply it.
        """
        super().__init__(f"ERROR: {name} is not set.{' ' + hint if hint else ''}")
        self.name = name


class SpendCapTooLowError(MissingSettingError):
    """The spend cap buys less runtime than the minimum useful run."""

    def __init__(self, cap: Decimal, hourly: Decimal, minutes: int, minimum: int) -> None:
        """Record the numbers that made the cap unusable.

        Parameters
        ----------
        cap : Decimal
            Requested spend cap in USD.
        hourly : Decimal
            Profile price per hour in USD.
        minutes : int
            Runtime the cap buys.
        minimum : int
            Smallest runtime accepted.
        """
        RefusedError.__init__(self, f"ERROR: REMOTE_SPEND_CAP_USD={cap} buys only {minutes} min at "
                                    f"${hourly}/h; at least {minimum} min is required.")
        self.name = "REMOTE_SPEND_CAP_USD"
        self.minutes = minutes
