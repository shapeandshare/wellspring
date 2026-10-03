"""The account's vCPU quota cannot fit the profile's instance."""

from __future__ import annotations

from ..._shared.errors.refused_error import RefusedError


class QuotaInsufficientError(RefusedError):
    """The account's vCPU quota cannot fit the profile's instance."""

    def __init__(self, quota_name: str, required: int, available: int) -> None:
        """Build the message.

        Parameters
        ----------
        quota_name : str
            Service Quotas name.
        required : int
            vCPUs the profile needs.
        available : int
            Applied quota minus vCPUs in use.
        """
        super().__init__(f"ERROR: quota \"{quota_name}\" has {available} vCPUs free; the profile needs {required}. "
                         f"Request an increase in the Service Quotas console.")
        self.quota_name = quota_name
        self.required = required
        self.available = available
