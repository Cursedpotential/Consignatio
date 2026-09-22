"""Read ZIP members in place, without downloading the archive.

> Byline: Claude Code · Opus 5 · 2026-09-22

A Takeout part is a 1.4 GB ZIP holding thousands of members. Downloading it to list them
costs the whole object; a ZIP's central directory lives in its last few kilobytes, so the
listing costs two ranged reads and each member costs one more. (The rclone ``archive``
backend lists 6,928 members of a 1.4 GB Takeout part in ~5 s the same way.)

``RangedObjectFile`` is a seekable, read-only file object over an S3 object, so the stdlib
``zipfile`` works against the bucket unchanged. It is synchronous because ``zipfile`` is;
it signs with the same ``ObjectStore`` used everywhere else, and every read is counted.

tar / tar.gz are NOT handled here: a tar has no central directory and a gzip stream cannot
be seeked, so listing one means reading it front to back. That is a separate, streamed
path and is not built.
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass

import httpx

from .object_store import ObjectStore, ObjectStoreError

MAX_MEMBER_BYTES_IN_MEMORY = 32 * 1024 * 1024


@dataclass(frozen=True)
class ArchiveMember:
    archive_key: str
    member_path: str
    byte_size: int
    crc32: int
    modified: tuple[int, int, int, int, int, int]


class RangedObjectFile(io.RawIOBase):
    """A seekable read-only view of one bucket object, served by ranged GETs."""

    def __init__(self, store: ObjectStore, key: str, size: int, client: httpx.Client) -> None:
        self._store = store
        self._key = key
        self._size = size
        self._client = client
        self._position = 0

    # -- io plumbing -------------------------------------------------------------
    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def tell(self) -> int:
        return self._position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._position, io.SEEK_END: self._size}[whence]
        self._position = max(0, min(self._size, base + offset))
        return self._position

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self._size - self._position
        size = min(size, self._size - self._position)
        if size <= 0:
            return b""
        payload = self._get_range(self._position, size)
        self._position += len(payload)
        return payload

    def readinto(self, buffer) -> int:  # noqa: ANN001 - io protocol
        payload = self.read(len(buffer))
        buffer[: len(payload)] = payload
        return len(payload)

    # -- the one network call ----------------------------------------------------
    def _get_range(self, start: int, length: int) -> bytes:
        end = start + length - 1
        headers = self._store._headers("GET", self._key, {"range": f"bytes={start}-{end}"})
        try:
            response = self._client.get(self._store._url(self._key), headers=headers)
            if response.status_code not in {200, 206}:
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ObjectStoreError(f"Archive range read failed for {self._key}") from exc
        self._store.counters.record(self._key, len(response.content))
        return response.content


def open_archive(
    store: ObjectStore, key: str, size: int, client: httpx.Client
) -> zipfile.ZipFile:
    return zipfile.ZipFile(RangedObjectFile(store, key, size, client))


def list_members(
    store: ObjectStore, key: str, size: int, client: httpx.Client, *, limit: int = 0
) -> list[ArchiveMember]:
    """List members from the central directory. Two ranged reads, not the whole archive."""
    with open_archive(store, key, size, client) as archive:
        members: list[ArchiveMember] = []
        for info in archive.infolist():
            if info.is_dir():
                continue
            members.append(ArchiveMember(
                archive_key=key, member_path=info.filename, byte_size=info.file_size,
                crc32=info.CRC, modified=info.date_time,
            ))
            if limit and len(members) >= limit:
                break
        return members


def read_member(
    store: ObjectStore, key: str, size: int, client: httpx.Client, member_path: str
) -> Iterator[bytes]:
    """Yield one member's bytes in bounded windows, decompressed on the way through."""
    with open_archive(store, key, size, client) as archive, archive.open(member_path) as handle:
        while True:
            window = handle.read(1024 * 1024)
            if not window:
                return
            yield window
