"""S3 behind :class:`ObjectStore` (spec 027 research R4)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError

from ..errors.cloud_api_error import CloudApiError

_T = TypeVar("_T")


class S3Sdk:
    """Implements :class:`~wellspring._shared.types.object_store.ObjectStore`. No delete, by design (FR-017)."""

    def __init__(self, client: Callable[[], BaseClient]) -> None:
        """Keep the client factory.

        Parameters
        ----------
        client : Callable[[], BaseClient]
            Returns an S3 client; real code passes a boto3-backed factory.
        """
        self._client = client

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def put_bytes(self, uri: str, data: bytes) -> None:
        """Write ``data`` to ``uri``."""
        bucket, key = self._split(uri)
        await self._guard(uri, lambda: self._client().put_object(Bucket=bucket, Key=key, Body=data))

    async def put_file(self, uri: str, path: Path) -> None:
        """Upload ``path`` to ``uri`` (managed, multipart for large files)."""
        bucket, key = self._split(uri)
        await self._guard(uri, lambda: self._client().upload_file(str(path), bucket, key))

    async def get_bytes(self, uri: str) -> bytes:
        """Read the object at ``uri``."""
        bucket, key = self._split(uri)
        return await self._guard(uri, lambda: bytes(self._client().get_object(Bucket=bucket, Key=key)["Body"].read()))

    async def get_file(self, uri: str, path: Path) -> None:
        """Download ``uri`` to ``path``."""
        bucket, key = self._split(uri)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await self._guard(uri, lambda: self._client().download_file(bucket, key, str(path)))

    async def list(self, prefix: str) -> list[str]:
        """Every object URI under ``prefix``, sorted."""
        bucket, key = self._split(prefix)
        client = self._client()
        uris: list[str] = []
        token: str | None = None
        while True:
            kwargs: dict[str, str] = {"Bucket": bucket, "Prefix": key}
            if token:
                kwargs["ContinuationToken"] = token
            page = await self._guard(prefix, lambda: client.list_objects_v2(**kwargs))
            uris.extend(f"s3://{bucket}/{obj['Key']}" for obj in page.get("Contents", []))
            if not page.get("IsTruncated"):
                return sorted(uris)
            token = str(page["NextContinuationToken"])

    async def exists(self, uri: str) -> bool:
        """Whether ``uri`` exists; a 404 is ``False``, any other error propagates."""
        bucket, key = self._split(uri)
        try:
            await asyncio.to_thread(self._client().head_object, Bucket=bucket, Key=key)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code"))
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise CloudApiError("s3", uri, code, str(exc.response.get("Error", {}).get("Message", ""))) from exc
        except BotoCoreError as exc:
            raise CloudApiError("s3", uri, type(exc).__name__, str(exc)) from exc
        return True

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    @staticmethod
    async def _guard(uri: str, call: Callable[[], _T]) -> _T:
        try:
            return await asyncio.to_thread(call)
        except ClientError as exc:
            error = exc.response.get("Error", {})
            raise CloudApiError("s3", uri, str(error.get("Code", "")), str(error.get("Message", ""))) from exc
        except BotoCoreError as exc:
            raise CloudApiError("s3", uri, type(exc).__name__, str(exc)) from exc

    @staticmethod
    def _split(uri: str) -> tuple[str, str]:
        rest = uri.removeprefix("s3://")
        bucket, _, key = rest.partition("/")
        return bucket, key
