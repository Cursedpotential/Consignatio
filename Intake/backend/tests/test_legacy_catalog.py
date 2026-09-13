from __future__ import annotations

import json

import pytest
from test_inventory_projection import ProjectionConnection
from test_surreal_projection import CONFIG, FakeRecordID

from casebible_index.projections.legacy_catalog import (
    CONTRACT,
    OBSERVATION_BASIS,
    load_legacy_catalog,
    project_legacy_catalog,
)
from casebible_index.projections.surreal import SurrealGraphClient


def make_manifest(tmp_path, **changes):
    row = {
        "bucket": "historical",
        "path": "Folder/File.txt",
        "name": "File.txt",
        "ext": ".txt",
        "size": None,
        "md5": "0" * 32,
        "modtime": "2020-01-02 13:14:15",
        "mimetype": None,
        "tier": None,
    }
    value = {
        "schema": CONTRACT,
        "imported_at": "2026-09-12T20:00:00+00:00",
        "catalog_locator": "fixture://catalog",
        "source_query": "SELECT fixture",
        "source_roots": {
            "historical": {
                "root_locator": "fixture://old-store",
                "store_kind": "historical",
                "label": "Old store",
            }
        },
        "rows": [row, {**row, "path": "Other/File.txt", "size": 0}],
        **changes,
    }
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "changes",
    [
        {"rows": []},
        {"source_roots": {}},
        {"imported_at": "2026-09-12T20:00:00"},
        {"source_query": ""},
    ],
)
def test_rejects_incomplete_provenance_and_empty_batch(tmp_path, changes):
    with pytest.raises(ValueError):
        load_legacy_catalog(make_manifest(tmp_path, **changes))


def test_rejects_collisions_and_oversized_batches(tmp_path):
    path = make_manifest(tmp_path)
    value = json.loads(path.read_text())
    value["rows"] = [value["rows"][0]] * 2
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Duplicate"):
        load_legacy_catalog(path)
    value["rows"] *= 51
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="100"):
        load_legacy_catalog(path)


@pytest.mark.asyncio
async def test_preserves_rows_nulls_and_naive_time_without_content_assertions(tmp_path):
    plan = load_legacy_catalog(make_manifest(tmp_path))
    connection = ProjectionConnection()
    graph = SurrealGraphClient(CONFIG, connection, FakeRecordID)
    assert (await project_legacy_catalog(graph, plan))["contents"] == 0
    occurrences = [v for k, v in connection.records.items() if k.table == "occurrence"]
    assert len(occurrences) == 2
    assert not any(k.table in {"content", "occurrence_has_content"} for k in connection.records)
    assert all("modified_at" not in occurrence for occurrence in occurrences)
    assert "size_bytes" not in occurrences[0]
    assert occurrences[1]["size_bytes"] == 0
    for occurrence in occurrences:
        assert occurrence["metadata"]["observation_basis"] == OBSERVATION_BASIS
        assert occurrence["metadata"]["catalog_row"]["modtime"] == "2020-01-02 13:14:15"
        assert occurrence["metadata"]["catalog_row"]["mimetype"] is None
        assert occurrence["observed_at"] == plan.imported_at
    before = len(connection.queries)
    await project_legacy_catalog(graph, plan)
    assert all(query.startswith("SELECT") for query, _ in connection.queries[before:])
