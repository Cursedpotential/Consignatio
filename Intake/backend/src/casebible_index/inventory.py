from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from .config import Settings

INVENTORY_SCHEMA_VERSION = "casebible-path-inventory-v2"
INVENTORY_SCHEMA = pa.schema(
    [
        ("source_id", pa.string()),
        ("relative_path", pa.string()),
        ("filename", pa.string()),
        ("extension", pa.string()),
        ("byte_size", pa.int64()),
        ("source_created_at", pa.timestamp("us", tz="UTC")),
        ("source_modified_at", pa.timestamp("us", tz="UTC")),
        ("source_modified_ns", pa.int64()),
        ("is_symlink", pa.bool_()),
        ("captured_at", pa.timestamp("us", tz="UTC")),
        ("schema_version", pa.string()),
    ],
    metadata={
        b"casebible.schema": INVENTORY_SCHEMA_VERSION.encode(),
        b"casebible.note": b"Path and stat inventory only; file bytes were not opened",
    },
)

EXCLUDED_DIRS = {".git", ".review_hold", "to_be_deleted", "__pycache__"}


@dataclass(frozen=True)
class InventoryResult:
    path: Path
    file_count: int
    total_bytes: int
    error_count: int


def newest_inventory(output_dir: Path) -> Path | None:
    candidates = sorted((output_dir / "inventory").glob("*/files.parquet"), reverse=True)
    return candidates[0] if candidates else None


def _as_utc(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=UTC)


def write_inventory(settings: Settings, *, batch_size: int = 50_000) -> InventoryResult:
    """Create an immutable path/stat snapshot without reading source file content."""

    captured_at = datetime.now(UTC)
    run_id = captured_at.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid4().hex[:8]
    output_path = settings.output_dir / "inventory" / run_id / "files.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=False)

    writer = pq.ParquetWriter(output_path, INVENTORY_SCHEMA, compression="zstd")
    rows: list[dict[str, object]] = []
    file_count = 0
    total_bytes = 0
    error_count = 0

    def flush() -> None:
        if rows:
            writer.write_table(pa.Table.from_pylist(rows, schema=INVENTORY_SCHEMA))
            rows.clear()

    try:
        for root, dirnames, filenames in os.walk(settings.source_dir, followlinks=False):
            dirnames[:] = sorted(name for name in dirnames if name not in EXCLUDED_DIRS)
            root_path = Path(root)
            for filename in sorted(filenames):
                path = root_path / filename
                try:
                    stat = path.lstat()
                    relative = path.relative_to(settings.source_dir).as_posix()
                    rows.append(
                        {
                            "source_id": settings.source_id,
                            "relative_path": relative,
                            "filename": filename,
                            "extension": path.suffix.casefold(),
                            "byte_size": stat.st_size,
                            "source_created_at": _as_utc(
                                getattr(stat, "st_birthtime", stat.st_ctime)
                            ),
                            "source_modified_at": _as_utc(stat.st_mtime),
                            "source_modified_ns": stat.st_mtime_ns,
                            "is_symlink": path.is_symlink(),
                            "captured_at": captured_at,
                            "schema_version": INVENTORY_SCHEMA_VERSION,
                        }
                    )
                    file_count += 1
                    total_bytes += stat.st_size
                    if len(rows) >= batch_size:
                        flush()
                except OSError:
                    error_count += 1
        flush()
    finally:
        writer.close()

    return InventoryResult(
        path=output_path,
        file_count=file_count,
        total_bytes=total_bytes,
        error_count=error_count,
    )
