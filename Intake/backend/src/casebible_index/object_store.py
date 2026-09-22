"""S3-compatible object reads for the Coco super index.

> Byline: Claude Code · Opus 5 · 2026-09-22

The catalog lists objects that live in an S3-compatible bucket (Backblaze B2 for the
Consignatio vault). Nothing here mounts, copies or mutates a bucket: every read is a
bounded ranged ``GET`` or a streamed ``GET`` consumed in windows, and every call is
counted so a run can state exactly how much it read.

Credentials follow the convention Probata already uses
(``modules/workbench/api/app/types/source_roots.py``): ``OBJECT_STORES_JSON`` maps a
locator scheme to a credential document, and the document holds
``access_key_id`` / ``secret_access_key`` / ``endpoint_url`` / ``region``. A single
store may also be configured directly with ``INTAKE_OBJECT_STORE_CREDENTIALS``.

Signing is SigV4 done here rather than through botocore so the service keeps one
HTTP client (httpx) and no synchronous AWS SDK in the hot path.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from urllib.parse import quote, urlsplit

import httpx

_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
_UNSIGNED_SCHEMES = {"upload", "file", "http", "https", "s3"}
DEFAULT_WINDOW_BYTES = 4 * 1024 * 1024


class ObjectStoreError(RuntimeError):
    """A bucket read failed. Never carries a provider body or a credential."""


@dataclass(frozen=True)
class StoreCredentials:
    access_key_id: str
    secret_access_key: str
    endpoint_url: str
    region: str

    @classmethod
    def from_document(cls, document: dict[str, object]) -> StoreCredentials:
        try:
            values = {
                name: str(document[name]).strip()
                for name in ("access_key_id", "secret_access_key", "endpoint_url", "region")
            }
        except KeyError:
            raise ObjectStoreError(
                "Object store credential document is missing a required field"
            ) from None
        parsed = urlsplit(values["endpoint_url"])
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ObjectStoreError("Object store endpoint_url must be an http(s) origin")
        if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
            raise ObjectStoreError("Object store endpoint_url must be a bare origin")
        if not all(values.values()):
            raise ObjectStoreError("Object store credential document has an empty field")
        return cls(**values)  # type: ignore[arg-type]

    @classmethod
    def from_path(cls, path: str) -> StoreCredentials:
        try:
            with open(path, encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, ValueError) as exc:
            raise ObjectStoreError(
                f"Object store credential document unreadable: {path}"
            ) from exc
        if not isinstance(document, dict):
            raise ObjectStoreError("Object store credential document must be a JSON object")
        return cls.from_document(document)


def configured_credentials(scheme: str = "b2") -> StoreCredentials:
    """Resolve credentials for one locator scheme, Probata's convention first."""
    direct = os.getenv("INTAKE_OBJECT_STORE_CREDENTIALS", "").strip()
    if direct:
        return StoreCredentials.from_path(direct)
    raw = os.getenv("OBJECT_STORES_JSON", "").strip()
    if not raw:
        raise ObjectStoreError(
            "No object store configured; set OBJECT_STORES_JSON or "
            "INTAKE_OBJECT_STORE_CREDENTIALS"
        )
    try:
        stores = json.loads(raw)
    except ValueError as exc:
        raise ObjectStoreError("OBJECT_STORES_JSON is not valid JSON") from exc
    if not isinstance(stores, dict) or scheme in _UNSIGNED_SCHEMES:
        raise ObjectStoreError("OBJECT_STORES_JSON must map a non-reserved scheme to a path")
    path = stores.get(scheme)
    if not isinstance(path, str) or not path.startswith("/"):
        raise ObjectStoreError(f"OBJECT_STORES_JSON has no absolute path for scheme {scheme!r}")
    return StoreCredentials.from_path(path)


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


@dataclass
class ReadCounters:
    """Per-run accounting so a receipt can state exactly what was read from the bucket."""

    requests: int = 0
    bytes_read: int = 0
    objects: set[str] = field(default_factory=set)

    def record(self, key: str, size: int) -> None:
        self.requests += 1
        self.bytes_read += max(size, 0)
        self.objects.add(key)

    def snapshot(self) -> dict[str, int]:
        return {
            "b2_requests": self.requests,
            "b2_bytes_read": self.bytes_read,
            "b2_objects_touched": len(self.objects),
        }


class ObjectStore:
    """Read-only S3 access to one bucket. Never writes, deletes or lists the whole bucket."""

    def __init__(
        self,
        credentials: StoreCredentials,
        bucket: str,
        client: httpx.AsyncClient,
        *,
        counters: ReadCounters | None = None,
    ) -> None:
        if not bucket or "/" in bucket:
            raise ObjectStoreError("Object store bucket must be a single name")
        self.credentials = credentials
        self.bucket = bucket
        self.client = client
        self.counters = counters or ReadCounters()

    def _url(self, key: str) -> str:
        encoded = quote(key, safe="/~")
        return f"{self.credentials.endpoint_url.rstrip('/')}/{self.bucket}/{encoded}"

    def _headers(
        self, method: str, key: str, extra: dict[str, str] | None = None
    ) -> dict[str, str]:
        creds = self.credentials
        host = urlsplit(creds.endpoint_url).netloc
        now = _dt.datetime.now(_dt.UTC)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        canonical_uri = "/" + self.bucket + "/" + quote(key, safe="/~")
        headers = {"host": host, "x-amz-content-sha256": _EMPTY_SHA256, "x-amz-date": amz_date}
        headers.update({name.lower(): value for name, value in (extra or {}).items()})
        signed_names = sorted(headers)
        canonical_headers = "".join(f"{name}:{headers[name]}\n" for name in signed_names)
        signed_headers = ";".join(signed_names)
        canonical_request = "\n".join(
            [method, canonical_uri, "", canonical_headers, signed_headers, _EMPTY_SHA256]
        )
        scope = f"{date_stamp}/{creds.region}/s3/aws4_request"
        to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signing_key = _sign(
            _sign(_sign(_sign(f"AWS4{creds.secret_access_key}".encode(), date_stamp),
                        creds.region), "s3"), "aws4_request"
        )
        signature = hmac.new(signing_key, to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        headers["authorization"] = (
            f"AWS4-HMAC-SHA256 Credential={creds.access_key_id}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return headers

    async def head(self, key: str) -> tuple[int, str]:
        """Return (content length, last-modified) for one object. One request."""
        try:
            response = await self.client.request(
                "HEAD", self._url(key), headers=self._headers("HEAD", key)
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ObjectStoreError(f"Object head failed for {key}") from exc
        self.counters.record(key, 0)
        return int(response.headers.get("content-length", 0)), response.headers.get(
            "last-modified", ""
        )

    async def read_range(self, key: str, start: int, length: int) -> bytes:
        """Read exactly one bounded byte range. Never reads a whole large object."""
        if length <= 0:
            return b""
        end = start + length - 1
        try:
            response = await self.client.get(
                self._url(key),
                headers=self._headers("GET", key, {"range": f"bytes={start}-{end}"}),
            )
            if response.status_code not in {200, 206}:
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ObjectStoreError(f"Object range read failed for {key}") from exc
        payload = response.content
        self.counters.record(key, len(payload))
        return payload

    async def stream(
        self, key: str, *, window_bytes: int = DEFAULT_WINDOW_BYTES
    ) -> AsyncIterator[bytes]:
        """Yield the object in bounded windows. Peak memory is one window, not the object."""
        try:
            request = self.client.build_request(
                "GET", self._url(key), headers=self._headers("GET", key)
            )
            response = await self.client.send(request, stream=True)
            try:
                response.raise_for_status()
                read = 0
                async for window in response.aiter_bytes(window_bytes):
                    read += len(window)
                    yield window
            finally:
                await response.aclose()
        except httpx.HTTPError as exc:
            raise ObjectStoreError(f"Object stream failed for {key}") from exc
        self.counters.record(key, read)
