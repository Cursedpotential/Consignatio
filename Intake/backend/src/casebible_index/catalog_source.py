"""Catalog-backed object source for the Intake discovery index.

> Byline: Claude Code · Opus 5 · 2026-09-18 (Build 1 of docs/transcripts/
> 2026-09-18-codex-route-from-tonight-to-architecture.md; owner go 22:44 EDT)

The object list comes straight from the Case Bible catalog (PostgreSQL ``casebible``,
schema ``raw_duck`` on ovh-files) instead of a directory walk, and not through any
viewer or explorer: owner decision 2026-09-16
(``Consignatio/docs/decisions/2026-09-16-catalog-source-of-truth.md``).

The query must return ``key``, ``size`` and ``sha1``. Every other column it returns
(dates, original names and paths, sources, hashes, metadata) is kept unchanged in
``CatalogObject.fields``; widening what the index knows is an edit to the SQL file,
not to this code. Dates pass through as recorded, keyed by their column name as their
basis; nothing here invents, merges or normalizes a date.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any

import duckdb

REQUIRED_COLUMNS = ("key", "size", "sha1")
_BATCH_ROWS = 10_000


@dataclass(frozen=True)
class CatalogObject:
    key: str
    """Object key relative to the mounted bucket root (e.g. ``consignatio/vault/v1/...``)."""
    byte_size: int
    sha1: str | None
    """B2 content SHA-1. B2 large files uploaded in parts have none."""
    fields: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


def safe_relative_key(key: str) -> PurePosixPath | None:
    """Return the key as a relative path, or None if it could escape the mount root."""
    path = PurePosixPath(key)
    if not key or path.is_absolute() or ".." in path.parts:
        return None
    return path


def _attach(con: duckdb.DuckDBPyConnection, dsn: str) -> None:
    con.execute("INSTALL postgres")
    con.execute("LOAD postgres")
    quoted = dsn.replace("'", "''")
    try:
        con.execute(f"ATTACH '{quoted}' AS catalog (TYPE postgres, READ_ONLY)")
    except duckdb.Error:
        # The DSN carries a password; never let it reach a log through the error text.
        raise ValueError(
            "Could not attach the catalog; check INTAKE_CATALOG_DSN host, role and network"
        ) from None


async def iter_catalog_objects(
    dsn: str, query: str, *, batch_rows: int = _BATCH_ROWS
) -> AsyncIterator[CatalogObject]:
    """Stream catalog rows in bounded Arrow batches; the full listing is never held."""
    con = duckdb.connect()
    try:
        await asyncio.to_thread(_attach, con, dsn)
        reader = await asyncio.to_thread(
            lambda: con.execute(query).fetch_record_batch(batch_rows)
        )
        missing = [name for name in REQUIRED_COLUMNS if name not in reader.schema.names]
        if missing:
            raise ValueError(f"Catalog query is missing required columns: {missing}")
        while True:
            try:
                batch = await asyncio.to_thread(reader.read_next_batch)
            except StopIteration:
                break
            for row in batch.to_pylist():
                key = row.pop("key")
                size = row.pop("size")
                sha1 = row.pop("sha1")
                yield CatalogObject(
                    key=key,
                    byte_size=int(size),
                    sha1=sha1 or None,
                    fields=MappingProxyType(row),
                )
    finally:
        con.close()
