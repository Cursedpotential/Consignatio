from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import duckdb
import pyarrow as pa

from .config import Settings
from .parquet_store import parquet_bytes, write_immutable

ACTIVE_SCHEMA = pa.schema(
    [
        ("document_id", pa.string()),
        ("version_id", pa.string()),
        ("artifact_id", pa.string()),
        ("relative_path", pa.string()),
        ("captured_at", pa.timestamp("us", tz="UTC")),
    ],
    metadata={b"casebible.role": b"active derived index snapshot"},
)


def _glob(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def newest_snapshot(output_dir: Path) -> Path | None:
    candidates = sorted((output_dir / "snapshots").glob("*/active_documents.parquet"), reverse=True)
    return candidates[0] if candidates else None


def _is_current_source(source_dir: Path, relative_path: str) -> bool:
    relative = Path(relative_path)
    if relative.is_absolute():
        return False
    source_root = source_dir.resolve()
    candidate = (source_root / relative).resolve()
    return candidate.is_relative_to(source_root) and candidate.is_file()


def build_active_snapshot(settings: Settings) -> Path:
    documents_glob = settings.output_dir / "datasets" / "documents" / "*.parquet"
    if not any(documents_glob.parent.glob(documents_glob.name)):
        raise FileNotFoundError("No document Parquet artifacts exist; run indexing first")

    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"""
            SELECT document_id, version_id, artifact_id, relative_path
            FROM read_parquet('{_glob(documents_glob)}', union_by_name = true)
            QUALIFY row_number() OVER (
                PARTITION BY document_id ORDER BY indexed_at DESC, artifact_id DESC
            ) = 1
            """
        ).fetchall()
    finally:
        connection.close()

    captured_at = datetime.now(UTC)
    active = [
        {
            "document_id": document_id,
            "version_id": version_id,
            "artifact_id": artifact_id,
            "relative_path": relative_path,
            "captured_at": captured_at,
        }
        for document_id, version_id, artifact_id, relative_path in rows
        if _is_current_source(settings.source_dir, relative_path)
    ]
    table = pa.Table.from_pylist(active, schema=ACTIVE_SCHEMA)
    run_id = captured_at.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid4().hex[:8]
    path = settings.output_dir / "snapshots" / run_id / "active_documents.parquet"
    write_immutable(path, parquet_bytes(table))
    return path
