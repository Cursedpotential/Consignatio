from __future__ import annotations

import hashlib
import json

import pytest
from test_migration_manifest_projection import row

from casebible_index.projections.migration_manifest import load_migration_projection
from scripts.partition_migration_occurrence_map import partition, verify_index


def write_map(path, count):
    with path.open("wb") as stream:
        for index in range(count):
            stream.write(json.dumps(row(f"occ:{index}", f"path/{index}.bin")).encode() + b"\n")


def test_partition_preserves_exact_bytes_and_contiguous_coverage(monkeypatch, tmp_path):
    import scripts.partition_migration_occurrence_map as module

    monkeypatch.setattr(module, "MAX_ROWS", 2)
    source = tmp_path / "map.jsonl"
    write_map(source, 5)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    result = partition(
        source,
        digest,
        tmp_path / "parts",
        generation_id="g1",
        destination="b2:target",
        declared_at="2026-09-12T17:00:00Z",
    )
    assert result["total_rows"] == 5
    assert [part["first_row"] for part in result["partitions"]] == [1, 3, 5]
    rebuilt = b"".join(
        (tmp_path / "parts" / part["artifact"]).read_bytes() for part in result["partitions"]
    )
    assert rebuilt == source.read_bytes()
    assert verify_index(tmp_path / "parts" / "partition-index.json")["total_rows"] == 5
    # Loader validates the partition provenance before any graph connection.
    first = load_migration_projection(tmp_path / "parts" / result["partitions"][0]["wrapper"])
    assert first.partition == {"index": 1, "count": 3, "first_row": 1, "row_count": 2}
    assert first.partition_set_sha256 == result["partition_set_sha256"]


def test_partition_rejects_changed_hash_and_existing_destination(tmp_path):
    source = tmp_path / "map.jsonl"
    write_map(source, 1)
    with pytest.raises(ValueError, match="SHA-256"):
        partition(
            source,
            "0" * 64,
            tmp_path / "parts",
            generation_id="g",
            destination="b2:x",
            declared_at="2026-09-12T17:00:00Z",
        )
    (tmp_path / "existing").mkdir()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        partition(
            source,
            digest,
            tmp_path / "existing",
            generation_id="g",
            destination="b2:x",
            declared_at="2026-09-12T17:00:00Z",
        )


def test_index_verification_rejects_changed_partition(tmp_path):
    source = tmp_path / "map.jsonl"
    write_map(source, 2)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    result = partition(
        source,
        digest,
        tmp_path / "parts",
        generation_id="g",
        destination="b2:x",
        declared_at="2026-09-12T17:00:00Z",
    )
    artifact = tmp_path / "parts" / result["partitions"][0]["artifact"]
    with artifact.open("ab") as stream:
        stream.write(b"{}\n")
    with pytest.raises(ValueError, match="artifact SHA-256"):
        verify_index(tmp_path / "parts" / "partition-index.json")
