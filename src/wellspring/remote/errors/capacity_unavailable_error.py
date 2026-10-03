"""The cloud refused to launch the instance."""

from __future__ import annotations

from ..._shared.errors.cloud_api_error import CloudApiError


class CloudLaunchError(CloudApiError):
    """The provider rejected the launch request; nothing is left running (exit code 2)."""

    def __init__(self, instance_type: str, code: str, message: str) -> None:
        """Keep the provider's reason.

        Parameters
        ----------
        instance_type : str
            Instance type that was requested.
        code : str
            Provider error code.
        message : str
            Provider error message, verbatim.
        """
        super().__init__("ec2", f"RunInstances {instance_type}", code, message)
        self.instance_type = instance_type


class CapacityUnavailableError(CloudLaunchError):
    """No capacity for the instance type; never silently switch types (spec 027 edge cases)."""
