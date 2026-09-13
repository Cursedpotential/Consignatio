from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from surrealdb.cbor import CBORSimpleValue

from casebible_index.projections.surreal import (
    REQUIRED_TABLES,
    GraphRecordRef,
    OperationRunWrite,
    ProjectionConflictError,
    ProjectionSnapshotWrite,
    SurrealGraphClient,
    SurrealGraphConfig,
    SurrealGraphError,
    _bound_nulls,
)


def server_bound_values(value):
    """Model object NONE field erasure versus explicit CBOR NULL storage."""
    if isinstance(value, CBORSimpleValue) and value.value == 22:
        return None
    if isinstance(value, dict):
        return {key: server_bound_values(item) for key, item in value.items() if item is not None}
    if isinstance(value, (list, tuple)):
        return [server_bound_values(item) for item in value]
    return value


@dataclass(frozen=True)
class FakeRecordID:
    table: str
    key: str


class FakeConnection:
    def __init__(self, endpoint: str = "wss://graph.example"):
        self.endpoint = endpoint
        self.connected = False
        self.closed = False
        self.credentials = None
        self.scope = None
        self.queries = []
        self.records = {}
        self.schema = {name: "DEFINE TABLE" for name in REQUIRED_TABLES}
        self.neighborhood = None

    async def __aenter__(self):
        self.connected = True
        return self

    async def __aexit__(self, *args):
        self.closed = True

    async def signin(self, credentials):
        self.credentials = credentials

    async def use(self, namespace, database):
        self.scope = (namespace, database)

    async def version(self):
        return "surrealdb-3.2.4"

    async def query(self, statement, variables=None):
        variables = server_bound_values(variables or {})
        self.queries.append((statement, variables))
        if statement == "INFO FOR DB;":
            return {"tables": self.schema}
        if statement.startswith("SELECT * FROM ONLY"):
            return self.records.get(variables["record_id"])
        if statement.startswith("CREATE ONLY"):
            record_id = variables["record_id"]
            if record_id in self.records:
                raise RuntimeError("duplicate plus provider secret")
            result = {"id": record_id, **variables["document"]}
            self.records[record_id] = result
            return result
        if statement.startswith("UPDATE"):
            record_id = variables["record_id"]
            if self.records.get(record_id) != variables["expected"]:
                return None
            result = {"id": record_id, **variables["document"]}
            self.records[record_id] = result
            return result
        if "RETURN { root:" in statement:
            return self.neighborhood
        if "snapshot: (SELECT * FROM ONLY $snapshot)" in statement:
            return self.neighborhood
        raise AssertionError(f"Unexpected statement: {statement}")


CONFIG = SurrealGraphConfig(
    endpoint="wss://graph.example",
    namespace="consignatio",
    database="intake",
    username="intake_runtime",
    password="test-only-secret",
)
NOW = datetime(2026, 9, 12, 14, 0, tzinfo=UTC)


def make_client(connection=None):
    return SurrealGraphClient(CONFIG, connection or FakeConnection(), FakeRecordID)


@pytest.mark.parametrize(
    "change",
    [
        {"endpoint": "mem://"},
        {"endpoint": "file://E:/intake.db"},
        {"endpoint": "wss://user:secret@graph.example"},
        {"namespace": "evidence"},
        {"database": "docs"},
        {"password": ""},
    ],
)
def test_config_fails_closed_for_embedded_credentials_or_wrong_database(change):
    values = {
        "endpoint": CONFIG.endpoint,
        "namespace": CONFIG.namespace,
        "database": CONFIG.database,
        "username": CONFIG.username,
        "password": CONFIG.password,
        **change,
    }
    with pytest.raises(ValueError):
        SurrealGraphConfig(**values).validate()


@pytest.mark.asyncio
async def test_connect_uses_database_scoped_credentials_and_verifies_schema():
    connection = FakeConnection()
    client = await SurrealGraphClient.connect(
        CONFIG,
        connection_factory=lambda endpoint: connection,
        record_factory=FakeRecordID,
    )
    assert connection.connected
    assert connection.credentials == {
        "username": "intake_runtime",
        "password": "test-only-secret",
        "namespace": "consignatio",
        "database": "intake",
    }
    assert connection.scope == ("consignatio", "intake")
    assert await client.verify_health_and_schema() == "surrealdb-3.2.4"
    await client.close()
    assert connection.closed


@pytest.mark.asyncio
async def test_readiness_closes_connection_and_sanitizes_provider_failure():
    connection = FakeConnection()
    connection.schema.pop("occurrence")
    with pytest.raises(SurrealGraphError, match="schema is incomplete") as exc:
        await SurrealGraphClient.connect(
            CONFIG,
            connection_factory=lambda endpoint: connection,
            record_factory=FakeRecordID,
        )
    assert connection.closed
    assert "test-only-secret" not in str(exc.value)


@pytest.mark.asyncio
async def test_operation_run_replay_is_idempotent_and_terminal_status_is_immutable():
    connection = FakeConnection()
    client = make_client(connection)
    running = OperationRunWrite("scan-001", "filesystem-scanner", NOW, "running")
    first = await client.write_operation_run(running)
    query_count = len(connection.queries)
    assert await client.write_operation_run(running) == first
    assert len(connection.queries) == query_count + 1  # replay reads but performs no write

    completed = OperationRunWrite(
        "scan-001", "filesystem-scanner", NOW, "completed", completed_at=NOW
    )
    terminal = await client.write_operation_run(completed)
    assert terminal["status"] == "completed"
    with pytest.raises(ProjectionConflictError, match="cannot change status"):
        await client.write_operation_run(
            OperationRunWrite("scan-001", "filesystem-scanner", NOW, "failed", completed_at=NOW)
        )


@pytest.mark.asyncio
async def test_snapshot_exact_replay_is_noop_and_changed_manifest_fails_closed():
    connection = FakeConnection()
    client = make_client(connection)
    snapshot = ProjectionSnapshotWrite(
        "snapshot-001", "b2://lake/manifests/001.json", "a" * 64, NOW
    )
    first = await client.write_projection_snapshot(snapshot)
    query_count = len(connection.queries)
    assert await client.write_projection_snapshot(snapshot) == first
    assert len(connection.queries) == query_count + 1
    with pytest.raises(ProjectionConflictError, match="conflicts"):
        await client.write_projection_snapshot(
            ProjectionSnapshotWrite(
                "snapshot-001", "b2://lake/manifests/changed.json", "b" * 64, NOW
            )
        )


@pytest.mark.asyncio
async def test_queries_are_constant_and_values_are_parameter_bound():
    connection = FakeConnection()
    client = make_client(connection)
    hostile = "run'; DELETE occurrence; --"
    await client.write_operation_run(OperationRunWrite(hostile, "scanner", NOW, "running"))
    statements = "\n".join(statement for statement, _ in connection.queries)
    assert hostile not in statements
    assert all("password" not in variables for _, variables in connection.queries)
    assert any(
        variables.get("document", {}).get("run_key") == hostile
        for _, variables in connection.queries
    )


@pytest.mark.asyncio
async def test_neighborhood_is_allowlisted_parameterized_and_bounded():
    connection = FakeConnection()
    connection.neighborhood = {
        "root": {"id": FakeRecordID("atomic_unit", "unit-1")},
        "edges": [{"relation": "contains"}],
    }
    client = make_client(connection)
    result = await client.graph_neighborhood(GraphRecordRef("atomic_unit", "unit-1"), edge_limit=5)
    assert len(result.edges) == 1
    statement, variables = connection.queries[-1]
    assert "unit-1" not in statement
    assert variables == {"root": FakeRecordID("atomic_unit", "unit-1"), "edge_limit": 5}
    with pytest.raises(ValueError):
        await client.graph_neighborhood(GraphRecordRef("contains", "edge-1"))
    with pytest.raises(ValueError):
        await client.graph_neighborhood(GraphRecordRef("atomic_unit", "unit-1"), edge_limit=101)


@pytest.mark.asyncio
async def test_projection_summary_is_parameterized_and_validates_shape():
    connection = FakeConnection()
    connection.neighborhood = {
        "snapshot": {"snapshot_key": "safe:key"},
        "completion": [],
        "occurrences": 2,
        "stores": 1,
        "stored_at": 2,
        "content_links": 1,
    }
    client = make_client(connection)
    result = await client.projection_summary("safe:key")
    assert result["occurrences"] == 2
    statement, variables = connection.queries[-1]
    assert "safe:key" not in statement
    assert variables == {
        "snapshot": FakeRecordID("projection_snapshot", hashlib.sha256(b"safe:key").hexdigest())
    }
    with pytest.raises(ValueError):
        await client.projection_summary("bad/key")


@pytest.mark.asyncio
async def test_snapshot_replay_cannot_omit_previously_stored_checkpoint():
    client = make_client()
    await client.write_projection_snapshot(
        ProjectionSnapshotWrite(
            "snapshot-optional", "fixture://manifest", "a" * 64, NOW, source_checkpoint="A"
        )
    )
    with pytest.raises(ProjectionConflictError):
        await client.write_projection_snapshot(
            ProjectionSnapshotWrite("snapshot-optional", "fixture://manifest", "a" * 64, NOW)
        )


@pytest.mark.asyncio
async def test_concurrent_terminal_run_cannot_be_overwritten():
    class RacingConnection(FakeConnection):
        async def query(self, statement, variables=None):
            if statement.startswith("UPDATE"):
                record = self.records[variables["record_id"]]
                record.update(status="failed", completed_at=NOW)
            return await super().query(statement, variables)

    connection = RacingConnection()
    client = make_client(connection)
    await client.write_operation_run(OperationRunWrite("race", "scanner", NOW, "running"))
    with pytest.raises(ProjectionConflictError, match="concurrently"):
        await client.write_operation_run(
            OperationRunWrite("race", "scanner", NOW, "completed", completed_at=NOW)
        )
    assert next(iter(connection.records.values()))["status"] == "failed"


def test_sdk_codec_preserves_null_keys_and_does_not_encode_them_as_none():
    from surrealdb.cbor import loads
    from surrealdb.data.cbor import decode, encode

    original = {"metadata": {"unknown": None, "nested": [None, {"missing_hash": None}]}}
    # The SDK decoder collapses both NONE and NULL to Python None; inspect wire bytes.
    assert encode({"x": None}).hex() == "a16178c6f6"  # CBOR tag 6 + null
    assert encode(_bound_nulls({"x": None})).hex() == "a16178f6"  # plain CBOR null
    bound = _bound_nulls(original)
    encoded = encode(bound)
    assert loads(encoded)["metadata"]["unknown"] is None
    assert decode(encoded) == original
    assert original["metadata"]["unknown"] is None  # caller document is unchanged
    assert server_bound_values(original) != original  # mock detects the old data-loss behavior


@pytest.mark.asyncio
async def test_explicit_null_metadata_survives_create_cas_and_exact_replay():
    from dataclasses import replace

    connection = FakeConnection()
    client = make_client(connection)
    run = OperationRunWrite("null-run", "scanner", NOW, "running", metadata={"unknown": None})
    stored = await client.write_operation_run(run)
    assert stored["metadata"] == {"unknown": None}
    completed = replace(run, status="completed", completed_at=NOW)
    assert (await client.write_operation_run(completed))["metadata"] == {"unknown": None}
    assert (await client.write_operation_run(completed))["status"] == "completed"
    snapshot = ProjectionSnapshotWrite(
        "null-snapshot", "fixture://manifest", "c" * 64, NOW, metadata={"unknown": None}
    )
    await client.write_projection_snapshot(snapshot)
    assert (await client.write_projection_snapshot(snapshot))["metadata"] == {"unknown": None}
    with pytest.raises(ProjectionConflictError):
        await client.write_projection_snapshot(replace(snapshot, metadata={}))
