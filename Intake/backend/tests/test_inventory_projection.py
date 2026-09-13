from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from test_surreal_projection import CONFIG, FakeConnection, FakeRecordID

from casebible_index.fingerprints import _schema
from casebible_index.inventory import INVENTORY_SCHEMA
from casebible_index.projections.inventory_manifest import (
    CONTRACT,
    load_inventory_projection,
    project_inventory,
)
from casebible_index.projections.surreal import SurrealGraphClient, SurrealGraphError

NOW = datetime(2026, 9, 12, tzinfo=UTC)


def manifest(tmp_path, *, size_conflict=False, bad_hash=False, duplicate=False):
    rows = [
        {
            "source_id": "fixture-store",
            "relative_path": path,
            "filename": path,
            "extension": ".txt",
            "byte_size": 3,
            "source_created_at": NOW,
            "source_modified_at": NOW,
            "source_modified_ns": 123,
            "is_symlink": False,
            "captured_at": NOW,
            "schema_version": "casebible-path-inventory-v2",
        }
        for path in ("first.txt", "second.txt", "unhashed.txt")
    ]
    if size_conflict:
        rows[1]["byte_size"] = 4
    if duplicate:
        rows[1]["relative_path"] = "first.txt"
    fingerprint = [{**row, "sha256": "a" * 64, "hash_status": "hashed"} for row in rows[:2]]
    inventory_path = tmp_path / "inventory.parquet"
    fingerprint_path = tmp_path / "fingerprint.parquet"
    pq.write_table(pa.Table.from_pylist(rows, schema=INVENTORY_SCHEMA), inventory_path)
    pq.write_table(pa.Table.from_pylist(fingerprint, schema=_schema()), fingerprint_path)
    value = {
        "schema": CONTRACT,
        "source_id": "fixture-store",
        "declared_at": NOW.isoformat(),
        "store": {
            "root_locator": "fixture://store",
            "store_kind": "fixture",
            "label": "Synthetic test only",
        },
    }
    for key, path in (("inventory", inventory_path), ("fingerprints", fingerprint_path)):
        value[key] = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if bad_hash:
        value["inventory"]["sha256"] = "0" * 64
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


class ProjectionConnection(FakeConnection):
    def __init__(self):
        super().__init__()
        self.fail_relation = False

    async def query(self, statement, variables=None):
        if statement.startswith("RELATE"):
            if self.fail_relation:
                raise RuntimeError("injected network failure")
            self.queries.append((statement, variables))
            result = {
                "id": variables["edge"],
                "in": variables["source"],
                "out": variables["target"],
                "fact_layer": "imported",
            }
            self.records[variables["edge"]] = result
            return result
        return await super().query(statement, variables)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bad_hash": True},
        {"duplicate": True},
        {"size_conflict": True},
    ],
)
def test_invalid_input_is_rejected_before_projection(tmp_path, kwargs):
    with pytest.raises(ValueError):
        load_inventory_projection(manifest(tmp_path, **kwargs))


@pytest.mark.asyncio
async def test_occurrences_preserved_shared_exact_content_and_replay(tmp_path):
    plan = load_inventory_projection(manifest(tmp_path))
    connection = ProjectionConnection()
    graph = SurrealGraphClient(CONFIG, connection, FakeRecordID)
    result = await project_inventory(graph, plan)
    assert result["occurrences"] == 3
    assert result["unique_contents"] == 1
    count = len(connection.records)
    assert len([r for r in connection.records if r.table == "occurrence"]) == 3
    assert len([r for r in connection.records if r.table == "occurrence_has_content"]) == 2
    assert len([r for r in connection.records if r.table == "produced_by"]) == 1
    before = len(connection.queries)
    assert await project_inventory(graph, plan) == result
    assert len(connection.records) == count
    assert all(q.startswith("SELECT") for q, _ in connection.queries[before:])


@pytest.mark.asyncio
async def test_partial_failure_has_no_completion_marker_and_can_resume(tmp_path):
    plan = load_inventory_projection(manifest(tmp_path))
    connection = ProjectionConnection()
    connection.fail_relation = True
    graph = SurrealGraphClient(CONFIG, connection, FakeRecordID)
    with pytest.raises(SurrealGraphError):
        await project_inventory(graph, plan)
    assert not any(key.table == "produced_by" for key in connection.records)
    connection.fail_relation = False
    assert (await project_inventory(graph, plan))["status"] == "completed"
