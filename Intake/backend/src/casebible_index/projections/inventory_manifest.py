"""Explicit, bounded projection of existing inventory artifacts; never scans sources."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import pyarrow.parquet as pq

from ..fingerprints import FINGERPRINT_SCHEMA_VERSION
from ..inventory import INVENTORY_SCHEMA_VERSION
from .surreal import (
    OperationRunWrite,
    ProjectionSnapshotWrite,
    SurrealGraphClient,
)

CONTRACT = "intake-inventory-projection-v1"
MAX_ROWS = 10_000


@dataclass(frozen=True)
class InventoryProjection:
    manifest_uri: str
    manifest_sha256: str
    declared_at: datetime
    source_id: str
    store: dict[str, Any]
    rows: tuple[dict[str, Any], ...]
    content: dict[str, int]

    @property
    def snapshot_key(self) -> str:
        return f"{CONTRACT}:{self.manifest_sha256}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact(manifest: Path, spec: dict, schema: str) -> list[dict]:
    path = Path(spec["path"])
    if not path.is_absolute():
        path = manifest.parent / path
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("Projection artifact exceeds 128 MiB")
    expected = spec["sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Artifact SHA-256 must be lowercase hexadecimal")
    if _sha256(path) != expected:
        raise ValueError("Artifact SHA-256 mismatch")
    parquet = pq.ParquetFile(path)
    if parquet.metadata.num_rows > MAX_ROWS:
        raise ValueError("Projection input exceeds the 10000-row batch bound")
    if (
        sum(
            parquet.metadata.row_group(i).total_byte_size
            for i in range(parquet.metadata.num_row_groups)
        )
        > 256 * 1024 * 1024
    ):
        raise ValueError("Projection artifact exceeds 256 MiB uncompressed")
    actual_schema = (parquet.schema_arrow.metadata or {}).get(b"casebible.schema", b"").decode()
    if actual_schema != schema:
        raise ValueError("Unsupported inventory or fingerprint schema")
    rows = parquet.read().to_pylist()
    if _sha256(path) != expected:
        raise ValueError("Artifact changed while reading")
    return rows


def _aware(value: Any) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Observation timestamps must be timezone-aware")
    return value


def load_inventory_projection(path: Path) -> InventoryProjection:
    """Validate all declared artifact bytes and observations before any graph writes."""
    if path.stat().st_size > 64 * 1024:
        raise ValueError("Manifest exceeds 64 KiB")
    raw = path.read_bytes()
    manifest = json.loads(raw)
    if manifest["schema"] != CONTRACT:
        raise ValueError("Unsupported projection manifest")
    source_id = manifest["source_id"]
    store = manifest["store"]
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("Explicit source identity is required")
    for field in ("root_locator", "store_kind", "label"):
        if not isinstance(store.get(field), str) or not store[field].strip():
            raise ValueError("Explicit store root, kind and label are required")
    declared_at = _aware(datetime.fromisoformat(manifest["declared_at"]))
    inventory = _artifact(path, manifest["inventory"], INVENTORY_SCHEMA_VERSION)
    fingerprints = (
        _artifact(path, manifest["fingerprints"], FINGERPRINT_SCHEMA_VERSION)
        if manifest.get("fingerprints")
        else []
    )

    def keyed(rows: list[dict]) -> dict[str, dict]:
        result = {}
        for row in rows:
            relative = row["relative_path"]
            if row["source_id"] != source_id or not isinstance(relative, str):
                raise ValueError("Artifact source identity mismatch")
            parts = relative.split("/")
            if (
                not relative
                or "\\" in relative
                or ":" in relative
                or any(part in {"", ".", ".."} for part in parts)
            ):
                raise ValueError("Inventory path must be a source-relative POSIX path")
            if relative in result:
                raise ValueError("Duplicate source/path rows in one artifact")
            size = row.get("byte_size")
            if type(size) is not int or size < 0:
                raise ValueError("Inventory byte size is invalid")
            _aware(row["captured_at"])
            if row.get("source_modified_at") is not None:
                _aware(row["source_modified_at"])
            result[relative] = row
        return result

    observations, hashes = keyed(inventory), keyed(fingerprints)
    if hashes.keys() - observations.keys():
        raise ValueError("Fingerprint contains paths absent from the declared inventory")
    rows = []
    contents: dict[str, int] = {}
    for relative, observation in observations.items():
        fingerprint = hashes.get(relative)
        digest = None
        if fingerprint and fingerprint.get("hash_status") == "hashed":
            if (
                any(
                    fingerprint.get(key) != observation.get(key)
                    for key in ("byte_size", "source_modified_ns", "is_symlink")
                )
                or observation.get("source_modified_ns") is None
                or observation.get("is_symlink")
            ):
                raise ValueError("Hashed fingerprint does not match inventory observation")
            digest = fingerprint.get("sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("Hashed fingerprint lacks valid raw SHA-256")
            size = observation["byte_size"]
            if digest in contents and contents[digest] != size:
                raise ValueError("Same raw SHA-256 has conflicting byte sizes")
            contents[digest] = size
        rows.append({"observation": observation, "fingerprint": fingerprint, "sha256": digest})
    if path.read_bytes() != raw:
        raise ValueError("Manifest changed while validating")
    return InventoryProjection(
        path.resolve().as_uri(),
        hashlib.sha256(raw).hexdigest(),
        declared_at,
        source_id,
        {key: store[key] for key in ("root_locator", "store_kind", "label")},
        tuple(rows),
        contents,
    )


async def project_inventory(graph: SurrealGraphClient, plan: InventoryProjection) -> dict:
    """Persist validated observations; produced_by is the final completion checkpoint.

    A snapshot alone may be partial. Consumers must require its completed
    operation_run through produced_by before treating the batch as complete.
    """
    snapshot_key = plan.snapshot_key
    started_at = datetime.now(UTC)
    snapshot = graph.projection_record("projection_snapshot", snapshot_key)
    await graph.write_projection_snapshot(
        ProjectionSnapshotWrite(
            snapshot_key,
            plan.manifest_uri,
            plan.manifest_sha256,
            plan.declared_at,
            source_checkpoint=plan.manifest_sha256,
            metadata={
                "input_contract": CONTRACT,
                "lake_publication_claimed": False,
                "projected_at_basis": "manifest declaration; see operation_run for execution",
            },
        )
    )
    store_key = f"{snapshot_key}:store:{plan.source_id}"
    store = graph.projection_record("store", store_key)
    await graph.write_imported_node(
        "store",
        store_key,
        {
            **plan.store,
            "snapshot": snapshot,
            "metadata": {"source_id": plan.source_id},
        },
    )
    for digest, size in plan.content.items():
        await graph.write_imported_node(
            "content",
            f"sha256:{digest}",
            {
                "snapshot": snapshot,
                "sha256": digest,
                "size_bytes": size,
                "metadata": {},
            },
        )
    for row in plan.rows:
        observed = row["observation"]
        relative = observed["relative_path"]
        key = f"{snapshot_key}:occurrence:{plan.source_id}:{relative}"
        occurrence = graph.projection_record("occurrence", key)
        document = {
            "snapshot": snapshot,
            "entry_kind": "other" if observed["is_symlink"] else "file",
            "path_raw": relative,
            "path_normalized": relative,
            "basename": PurePosixPath(relative).name,
            "size_bytes": observed["byte_size"],
            "observed_at": observed["captured_at"],
            "metadata": {"inventory_row": observed, "fingerprint_row": row["fingerprint"]},
        }
        if observed.get("source_modified_at") is not None:
            document["modified_at"] = observed["source_modified_at"]
        await graph.write_imported_node("occurrence", key, document)
        await graph.write_imported_relation("stored_at", occurrence, store)
        if row["sha256"]:
            await graph.write_imported_relation(
                "occurrence_has_content",
                occurrence,
                graph.projection_record("content", f"sha256:{row['sha256']}"),
            )
    run_key = f"{snapshot_key}:complete"
    counts = {"occurrences": len(plan.rows), "unique_contents": len(plan.content)}
    previous = await graph.read_projection_record("operation_run", run_key)
    if previous is None:
        await graph.write_operation_run(
            OperationRunWrite(
                run_key,
                "inventory-manifest-projection",
                started_at,
                "completed",
                tool_version=CONTRACT,
                completed_at=datetime.now(UTC),
                receipt_uri=plan.manifest_uri,
                metadata=counts,
            )
        )
    elif previous.get("status") != "completed" or previous.get("metadata") != counts:
        raise ValueError("Projection completion checkpoint conflicts with the validated input")
    await graph.write_imported_relation(
        "produced_by", snapshot, graph.projection_record("operation_run", run_key)
    )
    return {"snapshot_key": snapshot_key, "status": "completed", **counts}
