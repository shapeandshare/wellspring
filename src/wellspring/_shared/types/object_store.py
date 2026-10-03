"""Protocol for an object store addressed by ``s3://bucket/key`` URIs."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ObjectStore(Protocol):
    """Read and write objects. There is deliberately no delete (spec 027 FR-017)."""

    async def put_bytes(self, uri: str, data: bytes) -> None:
        """Write ``data`` to ``uri``, replacing any existing object."""
        ...

    async def put_file(self, uri: str, path: Path) -> None:
        """Upload the local file ``path`` to ``uri``."""
        ...

    async def get_bytes(self, uri: str) -> bytes:
        """Read the whole object at ``uri``."""
        ...

    async def get_file(self, uri: str, path: Path) -> None:
        """Download ``uri`` to ``path``, creating parent directories."""
        ...

    async def list(self, prefix: str) -> list[str]:
        """Full URIs of every object under ``prefix``, sorted."""
        ...

    async def exists(self, uri: str) -> bool:
        """Whether an object exists at exactly ``uri``."""
        ...
