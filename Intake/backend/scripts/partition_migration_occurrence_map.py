"""Partition one frozen occurrence map into complete hash-bound Intake batches."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from casebible_index.projections.migration_manifest import CONTRACT, MAX_ROWS


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_index(path: Path) -> dict:
    """Recheck complete contiguous coverage and every retained artifact/wrapper."""
    raw = path.read_bytes()
    value = json.loads(raw)
    if value.get("schema") != "intake-r2-b2-occurrence-map-partitions-v1":
        raise ValueError("Unsupported partition index")
    records = value.get("partitions")
    if not isinstance(records, list) or len(records) != value.get("partition_count"):
        raise ValueError("Partition index count mismatch")
    expected_set = hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if expected_set != value.get("partition_set_sha256"):
        raise ValueError("Partition-set SHA-256 mismatch")
    next_row, total = 1, 0
    for position, record in enumerate(records, 1):
        if record.get("index") != position or record.get("first_row") != next_row:
            raise ValueError("Partition ranges are not ordered and contiguous")
        rows = record.get("row_count")
        if type(rows) is not int or not 1 <= rows <= MAX_ROWS:
            raise ValueError("Partition row count is invalid")
        artifact = path.parent / record["artifact"]
        if _sha256(artifact) != record.get("artifact_sha256"):
            raise ValueError("Partition artifact SHA-256 mismatch")
        wrapper = json.loads((path.parent / record["wrapper"]).read_bytes())
        expected_partition = {
            "index": position,
            "count": len(records),
            "first_row": next_row,
            "row_count": rows,
        }
        if (
            wrapper.get("schema") != CONTRACT
            or wrapper.get("generation_id") != value.get("generation_id")
            or wrapper.get("destination") != value.get("destination")
            or wrapper.get("source_map_sha256") != value.get("source_map_sha256")
            or wrapper.get("partition_set_sha256") != expected_set
            or wrapper.get("partition") != expected_partition
            or wrapper.get("occurrence_map")
            != {"path": record["artifact"], "sha256": record["artifact_sha256"]}
        ):
            raise ValueError("Partition wrapper does not match index")
        next_row += rows
        total += rows
    if total != value.get("total_rows"):
        raise ValueError("Partition row coverage differs from index total")
    source = Path(value["source_map"])
    if _sha256(source) != value.get("source_map_sha256"):
        raise ValueError("Frozen source map differs from partition index")
    if path.read_bytes() != raw:
        raise ValueError("Partition index changed during verification")
    return {
        "total_rows": total,
        "partition_count": len(records),
        "source_map_sha256": value["source_map_sha256"],
        "partition_set_sha256": expected_set,
    }


def partition(
    source: Path,
    expected_sha256: str,
    output: Path,
    *,
    generation_id: str,
    destination: str,
    declared_at: str,
) -> dict:
    if _sha256(source) != expected_sha256:
        raise ValueError("Frozen occurrence-map SHA-256 mismatch")
    timestamp = datetime.fromisoformat(declared_at.replace("Z", "+00:00"))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Declaration time must include timezone")
    if not generation_id.strip() or not destination.strip():
        raise ValueError("Generation and destination are required")
    output.mkdir(parents=True, exist_ok=False)
    parts, current, first_row, total = [], [], 1, 0
    with source.open("rb") as stream:
        for raw_line in stream:
            if len(raw_line) > 1024 * 1024:
                raise ValueError("Occurrence-map line exceeds 1 MiB")
            try:
                value = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("Occurrence map contains malformed JSONL") from exc
            if not isinstance(value, dict):
                raise ValueError("Occurrence-map line must be an object")
            current.append(raw_line)
            total += 1
            if len(current) == MAX_ROWS:
                parts.append((first_row, current))
                first_row = total + 1
                current = []
    if current:
        parts.append((first_row, current))
    if not parts or _sha256(source) != expected_sha256:
        raise ValueError("Occurrence map is empty or changed during partitioning")
    records = []
    reconstructed = hashlib.sha256()
    for index, (row_start, lines) in enumerate(parts, 1):
        part_name = f"occurrence-content-map.part-{index:06d}.jsonl"
        part_path = output / part_name
        with part_path.open("xb") as target:
            for line in lines:
                target.write(line)
                reconstructed.update(line)
        digest = _sha256(part_path)
        wrapper_name = f"intake-projection.part-{index:06d}.json"
        records.append(
            {
                "index": index,
                "first_row": row_start,
                "row_count": len(lines),
                "artifact": part_name,
                "artifact_sha256": digest,
                "wrapper": wrapper_name,
            }
        )
    partition_set_sha256 = hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    for record in records:
        wrapper = {
            "schema": CONTRACT,
            "declared_at": declared_at,
            "generation_id": generation_id,
            "destination": destination,
            "source_map_sha256": expected_sha256,
            "partition_set_sha256": partition_set_sha256,
            "partition": {
                "index": record["index"],
                "count": len(parts),
                "first_row": record["first_row"],
                "row_count": record["row_count"],
            },
            "occurrence_map": {"path": record["artifact"], "sha256": record["artifact_sha256"]},
        }
        with (output / record["wrapper"]).open("x", encoding="utf-8") as target:
            json.dump(wrapper, target, indent=2)
    if reconstructed.hexdigest() != expected_sha256 or _sha256(source) != expected_sha256:
        raise ValueError("Partition reconstruction differs from frozen source")
    index_doc = {
        "schema": "intake-r2-b2-occurrence-map-partitions-v1",
        "generation_id": generation_id,
        "destination": destination,
        "declared_at": declared_at,
        "source_map": str(source.resolve()),
        "source_map_sha256": expected_sha256,
        "total_rows": total,
        "partition_set_sha256": partition_set_sha256,
        "partition_count": len(records),
        "max_rows_per_partition": MAX_ROWS,
        "partitions": records,
    }
    with (output / "partition-index.json").open("x", encoding="utf-8") as target:
        json.dump(index_doc, target, indent=2)
    verify_index(output / "partition-index.json")
    return index_doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("expected_sha256")
    parser.add_argument("output", type=Path)
    parser.add_argument("--generation-id", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--declared-at", required=True)
    args = parser.parse_args()
    result = partition(
        args.source,
        args.expected_sha256,
        args.output,
        generation_id=args.generation_id,
        destination=args.destination,
        declared_at=args.declared_at,
    )
    print(
        json.dumps(
            {key: result[key] for key in ("total_rows", "partition_count", "source_map_sha256")}
        )
    )
