"""A cloud API call failed (credentials, permissions, throttling, missing resource)."""

from __future__ import annotations


class CloudApiError(Exception):
    """Any AWS SDK error, converted at the SDK boundary so no botocore type escapes (exit code 2)."""

    def __init__(self, service: str, operation: str, code: str, message: str) -> None:
        """Keep the provider's reason.

        Parameters
        ----------
        service : str
            e.g. ``ec2``, ``s3``.
        operation : str
            API operation or the object URI it targeted.
        code : str
            Provider error code (``NoCredentials`` when credentials are missing).
        message : str
            Provider message, verbatim.
        """
        super().__init__(f"ERROR: {service} {operation} failed ({code}): {message}")
        self.service = service
        self.operation = operation
        self.code = code
