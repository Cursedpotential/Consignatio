from __future__ import annotations

import hashlib
import json

import pytest
from test_inventory_projection import ProjectionConnection
from test_surreal_projection import CONFIG, FakeRecordID

from casebible_index.projections.migration_manifest import (
    CONTRACT,
    load_migration_projection,
    project_migration,
)
from casebible_index.projections.surreal import SurrealGraphClient


def row(identifier="occ:1", path="Takeout/export.zip", **changes):
    value = {
        "occurrence_id": identifier,
        "inventory_id": "inventory:1",
        "captured_at": "2026-09-12T12:00:00Z",
        "source_bucket": "casebible-raw",
        "source_path": path,
        "size": 12,
        "source_md5": "a" * 32,
        "content_id": "content:1",
        "identity_status": "sha256_verified",
        "content_algorithm": "sha256",
        "content_digest": "b" * 64,
        "payload_source_identity": "c" * 64,
        "destination_key": "payloads/sha256/bb/" + "b" * 64,
        "mapping_status": "canonical",
        "assertion_basis": "direct",
        "dedupe_authority": "sha256_verified",
        "source_location_drift": 0,
        "is_payload_representative": 1,
    }
    value.update(changes)
    return value


def manifest(tmp_path, rows=None, **changes):
    tmp_path.mkdir(parents=True, exist_ok=True)
    artifact = tmp_path / "occurrence-content-map.jsonl"
    values = rows or [
        row(),
        row(
            "occ:2",
            "junk/copy.zip",
            mapping_status="deduplicated_occurrence",
            is_payload_representative=0,
        ),
        row(
            "occ:3",
            "held/unknown.bin",
            content_algorithm="unknown",
            content_digest="",
            mapping_status="held_missing_hash",
            dedupe_authority="none_pending_fingerprint",
        ),
    ]
    artifact.write_text("".join(json.dumps(value) + "\n" for value in values), encoding="utf-8")
    wrapper = {
        "schema": CONTRACT,
        "declared_at": "2026-09-12T13:00:00Z",
        "generation_id": "generation-test",
        "destination": "b2:test/prefix",
        "occurrence_map": {
            "path": artifact.name,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        },
        **changes,
    }
    path = tmp_path / "wrapper.json"
    path.write_text(json.dumps(wrapper), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "rows",
    [
        [row(content_algorithm="md5", mapping_status="canonical")],
        [row(source_location_drift=1)],
        [row(), row("occ:2", "other", size=13)],
    ],
)
def test_rejects_unverified_or_conflicting_content_before_connection(tmp_path, rows):
    with pytest.raises(ValueError):
        load_migration_projection(manifest(tmp_path, rows=rows))


def test_rejects_changed_artifact_and_duplicate_occurrence(tmp_path):
    path = manifest(tmp_path, rows=[row(), row()])
    with pytest.raises(ValueError, match="duplicated"):
        load_migration_projection(path)
    path = manifest(tmp_path / "second")
    value = json.loads(path.read_text())
    (path.parent / value["occurrence_map"]["path"]).write_text("{}\n")
    with pytest.raises(ValueError, match="SHA-256"):
        load_migration_projection(path)


@pytest.mark.asyncio
async def test_preserves_every_occurrence_links_only_verified_sha_and_replays(tmp_path):
    plan = load_migration_projection(manifest(tmp_path))
    connection = ProjectionConnection()
    graph = SurrealGraphClient(CONFIG, connection, FakeRecordID)
    result = await project_migration(graph, plan)
    assert result == {
        "snapshot_key": plan.snapshot_key,
        "status": "completed",
        "occurrences": 3,
        "stores": 1,
        "verified_contents": 1,
    }
    assert len([key for key in connection.records if key.table == "occurrence"]) == 3
    assert len([key for key in connection.records if key.table == "content"]) == 1
    assert len([key for key in connection.records if key.table == "occurrence_has_content"]) == 2
    assert len([key for key in connection.records if key.table == "stored_at"]) == 3
    before = len(connection.queries)
    assert await project_migration(graph, plan) == result
    assert all(statement.startswith("SELECT") for statement, _ in connection.queries[before:])
