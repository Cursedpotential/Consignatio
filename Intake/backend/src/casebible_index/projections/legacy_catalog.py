"""Small explicit historical catalog import; no source scan or raw-content assertion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .surreal import OperationRunWrite, ProjectionSnapshotWrite, SurrealGraphClient

CONTRACT = "intake-legacy-catalog-projection-v1"
MAX_ROWS = 100
OBSERVATION_BASIS = "catalog import observation, not source observation"
ROW_FIELDS = {"bucket", "path", "name", "ext", "size", "md5", "modtime", "mimetype", "tier"}


@dataclass(frozen=True)
class LegacyCatalogProjection:
    manifest_uri: str
    manifest_sha256: str
    imported_at: datetime
    catalog_locator: str
    source_query: str
    source_roots: dict[str, dict[str, str]]
    rows: tuple[dict[str, Any], ...]

    @property
    def snapshot_key(self) -> str:
        return f"{CONTRACT}:{self.manifest_sha256}"


def load_legacy_catalog(path: Path) -> LegacyCatalogProjection:
    """Validate the complete small JSON input before any remote operation."""
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Legacy catalog manifest exceeds 1 MiB")
    raw = path.read_bytes()
    value = json.loads(raw)
    if value["schema"] != CONTRACT:
        raise ValueError("Unsupported legacy catalog manifest")
    imported_at = datetime.fromisoformat(value["imported_at"])
    if imported_at.tzinfo is None or imported_at.utcoffset() is None:
        raise ValueError("Catalog import time must include its timezone")
    for key in ("catalog_locator", "source_query"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError("Explicit catalog locator and source query are required")
    roots = value["source_roots"]
    rows = value["rows"]
    if not isinstance(roots, dict) or not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError("Expected explicit roots and between 1 and 100 catalog rows")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not ROW_FIELDS.issubset(row):
            raise ValueError("Catalog row lacks required original fields")
        for field in ("bucket", "path", "name"):
            if not isinstance(row[field], str) or not row[field]:
                raise ValueError("Bucket, path and name must be explicit nonempty strings")
        identity = (row["bucket"], row["path"])
        if identity in seen:
            raise ValueError("Duplicate bucket/path rows in one manifest")
        seen.add(identity)
        size = row["size"]
        if size is not None and (type(size) is not int or not 0 <= size <= 2**63 - 1):
            raise ValueError("Size must be null or a nonnegative signed 64-bit integer")
        root = roots.get(row["bucket"])
        if not isinstance(root, dict):
            raise ValueError("Catalog bucket lacks an explicit source root")
        for field in ("root_locator", "store_kind", "label"):
            if not isinstance(root.get(field), str) or not root[field].strip():
                raise ValueError("Source root, store kind and label must be explicit")
    if path.read_bytes() != raw:
        raise ValueError("Catalog manifest changed during validation")
    return LegacyCatalogProjection(
        path.resolve().as_uri(),
        hashlib.sha256(raw).hexdigest(),
        imported_at,
        value["catalog_locator"],
        value["source_query"],
        roots,
        tuple(rows),
    )


async def project_legacy_catalog(graph: SurrealGraphClient, plan: LegacyCatalogProjection) -> dict:
    """Keep historical row observations immutable and mark completion last."""
    started_at = datetime.now(UTC)
    key = plan.snapshot_key
    snapshot = graph.projection_record("projection_snapshot", key)
    provenance = {
        "input_contract": CONTRACT,
        "catalog_locator": plan.catalog_locator,
        "source_query": plan.source_query,
        "observation_basis": OBSERVATION_BASIS,
        "lake_publication_claimed": False,
    }
    await graph.write_projection_snapshot(
        ProjectionSnapshotWrite(
            key,
            plan.manifest_uri,
            plan.manifest_sha256,
            plan.imported_at,
            source_checkpoint=plan.manifest_sha256,
            metadata=provenance,
        )
    )
    used_buckets = sorted({row["bucket"] for row in plan.rows})
    for bucket in used_buckets:
        root = plan.source_roots[bucket]
        store_key = f"{key}:store:{bucket}"
        await graph.write_imported_node(
            "store",
            store_key,
            {
                **{field: root[field] for field in ("root_locator", "store_kind", "label")},
                "snapshot": snapshot,
                "metadata": {"bucket": bucket, "source_root": root, **provenance},
            },
        )
    for row in plan.rows:
        # Length-delimited JSON identity avoids ambiguities in bucket/path separators.
        identity = json.dumps([row["bucket"], row["path"]], ensure_ascii=False)
        occurrence_key = f"{key}:occurrence:{identity}"
        document = {
            "snapshot": snapshot,
            "entry_kind": "other",  # Historical catalog has no trusted file/symlink type.
            "path_raw": row["path"],
            "path_normalized": row["path"],
            "basename": row["name"],
            "observed_at": plan.imported_at,
            "metadata": {
                "catalog_row": row,
                **provenance,
                "path_normalization_basis": "original catalog spelling preserved",
                "source_time_basis": "uninterpreted original modtime retained in catalog_row",
            },
        }
        if row["size"] is not None:
            document["size_bytes"] = row["size"]
        await graph.write_imported_node("occurrence", occurrence_key, document)
        await graph.write_imported_relation(
            "stored_at",
            graph.projection_record("occurrence", occurrence_key),
            graph.projection_record("store", f"{key}:store:{row['bucket']}"),
        )
    counts = {"occurrences": len(plan.rows), "stores": len(used_buckets), "contents": 0}
    run_key = f"{key}:complete"
    existing = await graph.read_projection_record("operation_run", run_key)
    if existing is None:
        await graph.write_operation_run(
            OperationRunWrite(
                run_key,
                "legacy-catalog-projection",
                started_at,
                "completed",
                tool_version=CONTRACT,
                completed_at=datetime.now(UTC),
                receipt_uri=plan.manifest_uri,
                metadata=counts,
            )
        )
    elif existing.get("status") != "completed" or existing.get("metadata") != counts:
        raise ValueError("Legacy catalog completion checkpoint conflicts")
    await graph.write_imported_relation(
        "produced_by", snapshot, graph.projection_record("operation_run", run_key)
    )
    return {"snapshot_key": key, "status": "completed", **counts}
