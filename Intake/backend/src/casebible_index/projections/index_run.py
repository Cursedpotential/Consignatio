"""Project one index run into the Intake file graph.

> Byline: Claude Code · Opus 5 · 2026-09-22

Audit item I-6: the Surreal file graph must be fed by every indexing run, not by a
separate manual step. ``project_index_run`` reads the run's own document Parquet shards
and writes, into the existing imported-fact tables:

* one ``store`` node for the source (the vault bucket, or the local source tree),
* one ``occurrence`` node per indexed object, keyed by its vault key or relative path,
* a ``stored_at`` edge from each occurrence to the store,
* a ``projection_snapshot`` and a completed ``operation_run``.

No ``content`` node is written for a catalog object: the catalog records a B2 SHA-1, and
the content table's identity is a SHA-256. The SHA-1 is kept on the occurrence metadata
instead of being converted into a hash it is not.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import duckdb

from .surreal import OperationRunWrite, ProjectionSnapshotWrite, SurrealGraphClient

CONTRACT = "intake-index-run-projection-v1"


def _documents(output_dir: Path, snapshot: Path) -> list[dict[str, Any]]:
    documents_glob = (output_dir / "datasets" / "documents" / "*.parquet").as_posix()
    connection = duckdb.connect(":memory:")
    try:
        cursor = connection.execute(
            f"""
            SELECT d.document_id, d.version_id, d.artifact_id, d.source_id,
                   d.relative_path, COALESCE(d.vault_key, '') AS vault_key,
                   COALESCE(d.resolution, 'unknown') AS resolution,
                   d.filename, d.byte_size, d.content_sha256, d.index_status,
                   d.chunk_count, d.indexed_at
            FROM read_parquet('{documents_glob}', union_by_name = true) d
            JOIN read_parquet('{snapshot.as_posix()}') s
              USING (document_id, version_id, artifact_id)
            ORDER BY d.relative_path
            """
        )
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        connection.close()


async def project_index_run(
    graph: SurrealGraphClient,
    *,
    output_dir: Path,
    snapshot: Path,
    source_id: str,
    root_locator: str,
    store_kind: str,
) -> dict[str, Any]:
    """Write the run's file graph. Returns the counts written."""
    rows = _documents(output_dir, snapshot)
    manifest_uri = snapshot.resolve().as_uri()
    manifest_sha256 = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    snapshot_key = f"index-run:{source_id}:{manifest_sha256[:16]}"
    started_at = datetime.now(UTC)

    snapshot_record = graph.projection_record("projection_snapshot", snapshot_key)
    await graph.write_projection_snapshot(
        ProjectionSnapshotWrite(
            snapshot_key,
            manifest_uri,
            manifest_sha256,
            started_at,
            source_checkpoint=manifest_sha256,
            metadata={"input_contract": CONTRACT, "documents": len(rows)},
        )
    )
    store_key = f"{snapshot_key}:store:{source_id}"
    store = graph.projection_record("store", store_key)
    await graph.write_imported_node(
        "store",
        store_key,
        {
            "root_locator": root_locator,
            "store_kind": store_kind,
            "label": f"Intake index source {source_id}",
            "snapshot": snapshot_record,
            "metadata": {"source_id": source_id},
        },
    )
    for row in rows:
        path = row["vault_key"] or row["relative_path"]
        # Keyed by the content-addressed document id, not the path: when the owner moves an
        # object to its final folder the graph node follows it and only ``path_raw`` changes
        # (owner ruling 2026-09-22 10:48).
        key = f"{snapshot_key}:occurrence:{source_id}:{row['document_id']}"
        occurrence = graph.projection_record("occurrence", key)
        await graph.write_imported_node(
            "occurrence",
            key,
            {
                "snapshot": snapshot_record,
                "entry_kind": "file",
                "path_raw": path,
                "path_normalized": path,
                "basename": PurePosixPath(path).name,
                "size_bytes": int(row["byte_size"] or 0),
                "observed_at": row["indexed_at"],
                "metadata": {
                    "document_id": row["document_id"],
                    "version_id": row["version_id"],
                    "vault_key": row["vault_key"],
                    "resolution": row["resolution"],
                    "index_status": row["index_status"],
                    "chunk_count": int(row["chunk_count"] or 0),
                    "content_identity": row["content_sha256"],
                },
            },
        )
        await graph.write_imported_relation("stored_at", occurrence, store)

    counts = {"documents": len(rows)}
    run_key = f"{snapshot_key}:complete"
    if await graph.read_projection_record("operation_run", run_key) is None:
        await graph.write_operation_run(
            OperationRunWrite(
                run_key,
                "intake-index-run-projection",
                started_at,
                "completed",
                tool_version=CONTRACT,
                completed_at=datetime.now(UTC),
                receipt_uri=manifest_uri,
                metadata=counts,
            )
        )
    return {"snapshot_key": snapshot_key, **counts}
