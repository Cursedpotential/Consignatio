"""Bounded projection of an R2-to-B2 occurrence-content-map; never runs transfer."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .surreal import OperationRunWrite, ProjectionSnapshotWrite, SurrealGraphClient

CONTRACT = "intake-r2-b2-occurrence-map-v1"
MAX_ROWS = 10_000
REQUIRED = {
    "occurrence_id",
    "inventory_id",
    "captured_at",
    "source_bucket",
    "source_path",
    "size",
    "source_md5",
    "content_id",
    "identity_status",
    "content_algorithm",
    "content_digest",
    "payload_source_identity",
    "destination_key",
    "mapping_status",
    "assertion_basis",
    "dedupe_authority",
    "source_location_drift",
    "is_payload_representative",
}
SHA_MAPPING = {"canonical", "deduplicated_occurrence"}
SHA_AUTHORITY = {"sha256_verified", "sha256_via_conflict_free_md5_size_bridge"}


@dataclass(frozen=True)
class MigrationProjection:
    manifest_uri: str
    manifest_sha256: str
    declared_at: datetime
    generation_id: str
    destination: str
    artifact_sha256: str
    rows: tuple[dict[str, Any], ...]
    partition: dict[str, int] | None = None
    source_map_sha256: str | None = None
    partition_set_sha256: str | None = None

    @property
    def snapshot_key(self) -> str:
        return f"{CONTRACT}:{self.manifest_sha256}"


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Migration timestamps must be timezone-aware")
    return parsed


def load_migration_projection(path: Path) -> MigrationProjection:
    """Validate wrapper and complete artifact before any graph connection."""
    if path.stat().st_size > 64 * 1024:
        raise ValueError("Migration projection wrapper exceeds 64 KiB")
    raw = path.read_bytes()
    wrapper = json.loads(raw)
    if wrapper.get("schema") != CONTRACT:
        raise ValueError("Unsupported migration projection wrapper")
    declared_at = _aware(wrapper["declared_at"])
    for field in ("generation_id", "destination"):
        if not isinstance(wrapper.get(field), str) or not wrapper[field].strip():
            raise ValueError("Generation and destination provenance are required")
    spec = wrapper["occurrence_map"]
    artifact = Path(spec["path"])
    if not artifact.is_absolute():
        artifact = path.parent / artifact
    expected = spec["sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or _digest(artifact) != expected:
        raise ValueError("Occurrence-map SHA-256 mismatch")
    if artifact.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Occurrence map exceeds 64 MiB")
    rows, seen, verified_sizes = [], set(), {}
    with artifact.open("r", encoding="utf-8", newline="") as stream:
        for line_number, line in enumerate(stream, 1):
            if line_number > MAX_ROWS:
                raise ValueError("Occurrence map exceeds the 10000-row batch bound")
            row = json.loads(line)
            if not isinstance(row, dict) or not REQUIRED.issubset(row):
                raise ValueError("Occurrence-map row lacks required fields")
            occurrence_id = row["occurrence_id"]
            if not isinstance(occurrence_id, str) or not occurrence_id or occurrence_id in seen:
                raise ValueError("Occurrence identity is blank or duplicated")
            seen.add(occurrence_id)
            if not isinstance(row["source_bucket"], str) or not row["source_bucket"]:
                raise ValueError("Source bucket is required")
            source_path = row["source_path"]
            if not isinstance(source_path, str) or not source_path or "\\" in source_path:
                raise ValueError("Source path must retain a nonempty POSIX object key")
            parts = source_path.split("/")
            if any(part in {"", ".", ".."} for part in parts):
                raise ValueError("Unsafe source object key")
            if type(row["size"]) is not int or row["size"] < 0:
                raise ValueError("Occurrence size is invalid")
            _aware(row["captured_at"])
            if row["content_algorithm"] not in {"sha256", "md5", "unknown"}:
                raise ValueError("Unsupported content algorithm")
            if row["source_location_drift"] not in {0, 1}:
                raise ValueError("Source-location drift must be zero or one")
            is_sha = row["content_algorithm"] == "sha256"
            if is_sha:
                if (
                    row["mapping_status"] not in SHA_MAPPING
                    or row["dedupe_authority"] not in SHA_AUTHORITY
                    or not re.fullmatch(r"[0-9a-f]{64}", row["content_digest"])
                    or row["source_location_drift"] != 0
                    or row["size"] == 0
                ):
                    raise ValueError("Invalid verified SHA-256 mapping")
            elif row["mapping_status"] in SHA_MAPPING:
                raise ValueError("Canonical mapping lacks verified SHA-256")
            if is_sha:
                previous_size = verified_sizes.setdefault(row["content_digest"], row["size"])
                if previous_size != row["size"]:
                    raise ValueError("One SHA-256 maps to conflicting sizes")
            rows.append(row)
    if not rows or _digest(artifact) != expected or path.read_bytes() != raw:
        raise ValueError("Projection input is empty or changed during validation")
    partition = wrapper.get("partition")
    source_map_sha256 = wrapper.get("source_map_sha256")
    partition_set_sha256 = wrapper.get("partition_set_sha256")
    if partition is not None:
        if (
            not isinstance(partition, dict)
            or set(partition) != {"index", "count", "first_row", "row_count"}
            or not all(type(value) is int and value > 0 for value in partition.values())
            or partition["index"] > partition["count"]
            or partition["row_count"] != len(rows)
            or not isinstance(source_map_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", source_map_sha256)
            or not isinstance(partition_set_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", partition_set_sha256)
        ):
            raise ValueError("Invalid occurrence-map partition provenance")
    elif source_map_sha256 is not None or partition_set_sha256 is not None:
        raise ValueError("Partition hashes require partition provenance")
    return MigrationProjection(
        path.resolve().as_uri(),
        hashlib.sha256(raw).hexdigest(),
        declared_at,
        wrapper["generation_id"],
        wrapper["destination"],
        expected,
        tuple(rows),
        partition,
        source_map_sha256,
        partition_set_sha256,
    )


async def project_migration(graph: SurrealGraphClient, plan: MigrationProjection) -> dict:
    """Project occurrences and verified content; produced_by is written last."""
    snapshot = graph.projection_record("projection_snapshot", plan.snapshot_key)
    metadata = {
        "input_contract": CONTRACT,
        "generation_id": plan.generation_id,
        "destination": plan.destination,
        "occurrence_map_sha256": plan.artifact_sha256,
        "transfer_controlled_here": False,
        "evidence_acceptance_claimed": False,
    }
    if plan.partition is not None:
        metadata.update(
            {
                "partition": plan.partition,
                "source_map_sha256": plan.source_map_sha256,
                "partition_set_sha256": plan.partition_set_sha256,
            }
        )
    await graph.write_projection_snapshot(
        ProjectionSnapshotWrite(
            plan.snapshot_key,
            plan.manifest_uri,
            plan.manifest_sha256,
            plan.declared_at,
            source_checkpoint=plan.artifact_sha256,
            metadata=metadata,
        )
    )
    buckets = sorted({row["source_bucket"] for row in plan.rows})
    for bucket in buckets:
        await graph.write_imported_node(
            "store",
            f"{plan.snapshot_key}:store:{bucket}",
            {
                "snapshot": snapshot,
                "root_locator": f"r2:{bucket}",
                "store_kind": "r2-migration-occurrence-map",
                "label": f"R2 source {bucket}",
                "metadata": {**metadata, "source_bucket": bucket},
            },
        )
    verified = {
        row["content_digest"]: row["size"]
        for row in plan.rows
        if row["content_algorithm"] == "sha256"
    }
    for digest, size in verified.items():
        await graph.write_imported_node(
            "content",
            f"sha256:{digest}",
            {
                "snapshot": snapshot,
                "sha256": digest,
                "size_bytes": size,
                "metadata": {"first_seen_contract": CONTRACT},
            },
        )
    for row in plan.rows:
        key = f"{plan.snapshot_key}:occurrence:{row['occurrence_id']}"
        occurrence = graph.projection_record("occurrence", key)
        await graph.write_imported_node(
            "occurrence",
            key,
            {
                "snapshot": snapshot,
                "entry_kind": "file",
                "path_raw": row["source_path"],
                "path_normalized": row["source_path"],
                "basename": PurePosixPath(row["source_path"]).name,
                "size_bytes": row["size"],
                "observed_at": _aware(row["captured_at"]),
                "metadata": {"migration_occurrence": row, **metadata},
            },
        )
        await graph.write_imported_relation(
            "stored_at",
            occurrence,
            graph.projection_record("store", f"{plan.snapshot_key}:store:{row['source_bucket']}"),
        )
        if row["content_algorithm"] == "sha256":
            await graph.write_imported_relation(
                "occurrence_has_content",
                occurrence,
                graph.projection_record("content", f"sha256:{row['content_digest']}"),
            )
    counts = {
        "occurrences": len(plan.rows),
        "stores": len(buckets),
        "verified_contents": len(verified),
    }
    run_key = f"{plan.snapshot_key}:complete"
    existing = await graph.read_projection_record("operation_run", run_key)
    if existing is None:
        await graph.write_operation_run(
            OperationRunWrite(
                run_key,
                "r2-b2-occurrence-map-projection",
                plan.declared_at,
                "completed",
                tool_version=CONTRACT,
                completed_at=plan.declared_at,
                receipt_uri=plan.manifest_uri,
                metadata=counts,
            )
        )
    elif existing.get("status") != "completed" or existing.get("metadata") != counts:
        raise ValueError("Migration projection completion checkpoint conflicts")
    await graph.write_imported_relation(
        "produced_by", snapshot, graph.projection_record("operation_run", run_key)
    )
    return {"snapshot_key": plan.snapshot_key, "status": "completed", **counts}
