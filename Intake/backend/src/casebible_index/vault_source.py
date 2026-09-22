"""Catalog objects as CocoIndex sources, read from the bucket rather than a mount.

> Byline: Claude Code · Opus 5 · 2026-09-22

Before this module, catalog mode listed objects from the catalog but still read their
bytes from ``CASEBIBLE_SOURCE_DIR``, i.e. it assumed the bucket was mounted on the host.
It is not. ``VaultFile`` reads the object over the S3 API instead, in bounded windows,
and keeps the catalog's own ``size`` + ``sha1`` as the change-detection state so an
unchanged object is never fetched at all.
"""

from __future__ import annotations

import hashlib
import pathlib
from collections.abc import AsyncIterator

import cocoindex as coco
from cocoindex.resources import file as coco_file

from .catalog_source import CatalogObject
from .object_store import ObjectStore
from .streaming import WINDOW_BYTES

OBJECT_STORE = coco.ContextKey[ObjectStore]("intake_vault_object_store")


class VaultFilePath(coco_file.FilePath[str]):
    """A bucket key. ``resolve()`` returns the key, never a host path."""

    __slots__ = ()

    def __init__(self, key: str) -> None:
        super().__init__(None, pathlib.PurePosixPath(key))

    def resolve(self) -> str:
        return self._path.as_posix()

    def _with_path(self, path: pathlib.PurePath) -> VaultFilePath:
        return VaultFilePath(pathlib.PurePosixPath(path).as_posix())

    def __coco_memo_key__(self) -> object:
        return ("vault-key", self._path.as_posix())


class VaultFile(coco_file.FileLike[str]):
    """One catalog object, read from the bucket on demand.

    Change detection uses the catalog's recorded size and SHA-1 (owner 2026-09-18: the
    hashing is already in the catalog), so a re-run costs zero bucket requests for
    objects that have not changed.
    """

    def __init__(self, catalog_object: CatalogObject, store: ObjectStore | None = None) -> None:
        super().__init__(VaultFilePath(catalog_object.key))
        self.catalog_object = catalog_object
        self._store = store

    @property
    def store(self) -> ObjectStore:
        return self._store if self._store is not None else coco.use_context(OBJECT_STORE)

    @property
    def key(self) -> str:
        return self.catalog_object.key

    @property
    def identity(self) -> str:
        """Content identity for the version id: the catalog SHA-1 when B2 recorded one.

        B2 large files uploaded in parts carry no SHA-1; those fall back to a digest of
        the key and size, which still changes whenever the object does.
        """
        if self.catalog_object.sha1:
            return f"sha1:{self.catalog_object.sha1}"
        digest = hashlib.sha256(
            f"{self.catalog_object.key}:{self.catalog_object.byte_size}".encode()
        ).hexdigest()
        return f"keysize:{digest}"

    @property
    def resolution(self) -> str:
        value = self.catalog_object.fields.get("resolution")
        return str(value) if value else "unknown"

    async def _fetch_metadata(self) -> coco_file.FileMetadata:
        import datetime as dt

        return coco_file.FileMetadata(
            size=self.catalog_object.byte_size,
            modified_time=dt.datetime.fromtimestamp(0, tz=dt.UTC),
            content_fingerprint=self.identity.encode(),
        )

    async def _read_impl(self, size: int = -1) -> bytes:
        """Whole-object reads are deliberately not offered for a vault object."""
        if size < 0:
            raise ValueError(
                "Vault objects are read in windows; use windows() instead of a whole read"
            )
        return await self.store.read_range(self.key, 0, size)

    async def windows(self, *, window_bytes: int = WINDOW_BYTES) -> AsyncIterator[bytes]:
        async for window in self.store.stream(self.key, window_bytes=window_bytes):
            yield window

    async def __coco_memo_state__(self, prev_state):
        state = ("catalog-v2", self.catalog_object.byte_size, self.catalog_object.sha1)
        return coco.MemoStateOutcome(state=state, memo_valid=prev_state == state)


class LocalStreamFile(coco_file.FileLike[pathlib.Path]):
    """Filesystem-mode source with the same windowed interface, so one pipeline serves both."""

    def __init__(self, file_path) -> None:
        super().__init__(file_path)

    @property
    def key(self) -> str:
        return self.file_path.resolve().as_posix()

    @property
    def resolution(self) -> str:
        return "local"

    async def _fetch_metadata(self) -> coco_file.FileMetadata:
        import datetime as dt

        stat = self.file_path.resolve().stat()
        return coco_file.FileMetadata(
            size=stat.st_size, modified_time=dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.UTC)
        )

    async def _read_impl(self, size: int = -1) -> bytes:
        with open(self.file_path.resolve(), "rb") as handle:
            return handle.read() if size < 0 else handle.read(size)

    async def windows(self, *, window_bytes: int = WINDOW_BYTES) -> AsyncIterator[bytes]:
        import asyncio

        path = self.file_path.resolve()
        handle = await asyncio.to_thread(open, path, "rb")
        try:
            while True:
                window = await asyncio.to_thread(handle.read, window_bytes)
                if not window:
                    break
                yield window
        finally:
            await asyncio.to_thread(handle.close)
