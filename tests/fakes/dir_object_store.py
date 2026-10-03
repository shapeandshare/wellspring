"""ObjectStore over a local directory: ``s3://b/k`` -> ``<root>/b/k``."""

from __future__ import annotations

import shutil
from pathlib import Path


class DirObjectStore:
    """Implements ``ObjectStore`` for tests, plus helpers to corrupt or inspect objects."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.calls: list[tuple[str, str]] = []

    def _path(self, uri: str) -> Path:
        assert uri.startswith("s3://"), uri
        return self.root / uri.removeprefix("s3://")

    async def put_bytes(self, uri: str, data: bytes) -> None:
        self.calls.append(("put", uri))
        path = self._path(uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def put_file(self, uri: str, path: Path) -> None:
        self.calls.append(("put", uri))
        dest = self._path(uri)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)

    async def get_bytes(self, uri: str) -> bytes:
        self.calls.append(("get", uri))
        return self._path(uri).read_bytes()

    async def get_file(self, uri: str, path: Path) -> None:
        self.calls.append(("get", uri))
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self._path(uri), path)

    async def list(self, prefix: str) -> list[str]:
        self.calls.append(("list", prefix))
        base = self._path(prefix)
        top = base if base.is_dir() else base.parent
        if not top.exists():
            return []
        out = []
        for p in top.rglob("*"):
            if p.is_file():
                uri = "s3://" + p.relative_to(self.root).as_posix()
                if uri.startswith(prefix):
                    out.append(uri)
        return sorted(out)

    async def exists(self, uri: str) -> bool:
        self.calls.append(("exists", uri))
        return self._path(uri).is_file()

    def corrupt(self, uri: str) -> None:
        path = self._path(uri)
        path.write_bytes(path.read_bytes() + b"tampered")

    def puts(self) -> list[str]:
        return [u for op, u in self.calls if op == "put"]
