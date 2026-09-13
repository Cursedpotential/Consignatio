"""Server-side boundary for the dedicated Consignatio/Intake Surreal graph.

The React renderer must never construct this client or receive its credentials.
Callers inject every connection value from a privileged backend secret bridge.
Only remote HTTP(S) and WebSocket endpoints are accepted; embedded databases are
deliberately rejected so a missing deployment cannot silently become local state.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlsplit

from surrealdb.cbor import CBORSimpleValue

EXPECTED_NAMESPACE = "consignatio"
EXPECTED_DATABASE = "intake"

NODE_TABLES = frozenset(
    {
        "archive_part",
        "archive_series",
        "atomic_unit",
        "content",
        "export_event",
        "identity_assertion",
        "machine_proposal",
        "occurrence",
        "operation_run",
        "projection_snapshot",
        "representation",
        "review_decision",
        "store",
        "subject_account",
    }
)

RELATION_TABLES = frozenset(
    {
        "alternate_representation_of",
        "belongs_to_account",
        "confirms_extraction",
        "contains",
        "corroborates",
        "decides_on",
        "member_of",
        "occurrence_has_content",
        "originated_from",
        "part_of_series",
        "possible_extraction_of",
        "produced_by",
        "proposal_object",
        "proposal_subject",
        "proposed_duplicate_of",
        "proposes_subject_for",
        "represents",
        "stored_at",
        "supersedes_decision",
    }
)

REQUIRED_TABLES = NODE_TABLES | RELATION_TABLES
_SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,254}$")
_RUN_STATUSES = frozenset({"running", "completed", "failed", "superseded"})
_TERMINAL_STATUSES = frozenset({"completed", "failed", "superseded"})

_UPDATE_RECORD = "UPDATE ONLY $record_id CONTENT $document WHERE $this = $expected RETURN AFTER;"
_CREATE_RECORD = "CREATE ONLY $record_id CONTENT $document RETURN AFTER;"
_SELECT_RECORD = "SELECT * FROM ONLY $record_id;"
_INFO_DATABASE = "INFO FOR DB;"
_NEIGHBORHOOD = """
RETURN { root: (SELECT * FROM ONLY $root), edges: (SELECT id, in, out, meta::tb(id) AS relation
FROM alternate_representation_of, belongs_to_account, confirms_extraction,
     contains, corroborates, decides_on, member_of, occurrence_has_content,
     originated_from, part_of_series, possible_extraction_of, produced_by,
     proposal_object, proposal_subject, proposed_duplicate_of,
     proposes_subject_for, represents, stored_at, supersedes_decision
WHERE in = $root OR out = $root
ORDER BY relation, id
LIMIT $edge_limit) };
""".strip()
_PROJECTION_SUMMARY = """
RETURN {
  snapshot: (SELECT * FROM ONLY $snapshot),
  completion: (SELECT id, out, out.status AS status, out.metadata AS counts
               FROM produced_by WHERE in = $snapshot LIMIT 1),
  occurrences: array::len((SELECT id FROM occurrence WHERE snapshot = $snapshot)),
  stores: array::len((SELECT id FROM store WHERE snapshot = $snapshot)),
  stored_at: array::len((SELECT id FROM stored_at
                         WHERE in IN (SELECT VALUE id FROM occurrence WHERE snapshot = $snapshot))),
  content_links: array::len((SELECT id FROM occurrence_has_content
                    WHERE in IN (SELECT VALUE id FROM occurrence WHERE snapshot = $snapshot)))
};
""".strip()


class SurrealGraphError(RuntimeError):
    """A sanitized graph-boundary failure safe to surface to backend callers."""


class ProjectionConflictError(SurrealGraphError):
    """A stable projection key was replayed with conflicting immutable facts."""


class _AsyncConnection(Protocol):
    async def __aenter__(self) -> Any: ...

    async def __aexit__(self, *args: Any) -> Any: ...

    async def signin(self, credentials: Mapping[str, Any]) -> Any: ...

    async def use(self, namespace: str, database: str) -> Any: ...

    async def version(self) -> Any: ...

    async def query(self, statement: str, variables: Mapping[str, Any] | None = None) -> Any: ...


@dataclass(frozen=True)
class SurrealGraphConfig:
    endpoint: str
    namespace: str
    database: str
    username: str
    password: str = field(repr=False)

    def validate(self) -> None:
        parsed = urlsplit(self.endpoint)
        if parsed.scheme not in {"http", "https", "ws", "wss"} or not parsed.hostname:
            raise ValueError("Surreal endpoint must be an explicit remote HTTP(S) or WebSocket URL")
        if parsed.username or parsed.password:
            raise ValueError("Surreal credentials must not be embedded in the endpoint")
        if parsed.query or parsed.fragment:
            raise ValueError("Surreal endpoint must not contain a query string or fragment")
        if self.namespace != EXPECTED_NAMESPACE or self.database != EXPECTED_DATABASE:
            raise ValueError("Surreal target must be the dedicated consignatio/intake database")
        if self.username != "intake_runtime":
            raise ValueError("Surreal backend must use the intake_runtime database user")
        if not self.password:
            raise ValueError("Surreal database credentials are required")


@dataclass(frozen=True)
class GraphRecordRef:
    table: str
    key: str

    def validate(self) -> None:
        if self.table not in NODE_TABLES:
            raise ValueError("Graph record table is not an allowed Intake node table")
        if not _SAFE_KEY.fullmatch(self.key):
            raise ValueError("Graph record key is invalid")


@dataclass(frozen=True)
class OperationRunWrite:
    run_key: str
    tool_name: str
    started_at: datetime
    status: str
    tool_version: str | None = None
    completed_at: datetime | None = None
    receipt_uri: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def document(self) -> dict[str, Any]:
        if not self.run_key.strip() or not self.tool_name.strip():
            raise ValueError("Run key and tool name are required")
        if self.status not in _RUN_STATUSES:
            raise ValueError("Invalid operation-run status")
        started_at = _utc(self.started_at)
        completed_at = _utc(self.completed_at) if self.completed_at else None
        if self.status in _TERMINAL_STATUSES and completed_at is None:
            raise ValueError("A terminal operation run requires completed_at")
        if self.status == "running" and completed_at is not None:
            raise ValueError("A running operation cannot have completed_at")
        if completed_at is not None and completed_at < started_at:
            raise ValueError("Operation completion precedes its start")
        return _without_none(
            {
                "run_key": self.run_key,
                "tool_name": self.tool_name,
                "tool_version": self.tool_version,
                "started_at": started_at,
                "completed_at": completed_at,
                "status": self.status,
                "receipt_uri": self.receipt_uri,
                "metadata": dict(self.metadata),
            }
        )


@dataclass(frozen=True)
class ProjectionSnapshotWrite:
    snapshot_key: str
    manifest_uri: str
    manifest_sha256: str
    projected_at: datetime
    source_checkpoint: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def document(self) -> dict[str, Any]:
        if not self.snapshot_key.strip() or not self.manifest_uri.strip():
            raise ValueError("Snapshot key and manifest URI are required")
        digest = self.manifest_sha256.lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Manifest SHA-256 must contain exactly 64 hexadecimal characters")
        return _without_none(
            {
                "snapshot_key": self.snapshot_key,
                "manifest_uri": self.manifest_uri,
                "manifest_sha256": digest,
                "projected_at": _utc(self.projected_at),
                "source_checkpoint": self.source_checkpoint,
                "metadata": dict(self.metadata),
            }
        )


@dataclass(frozen=True)
class GraphNeighborhood:
    root: Any
    edges: tuple[Any, ...]


class SurrealGraphClient:
    """Authenticated backend client pinned to the Intake graph boundary."""

    def __init__(
        self,
        config: SurrealGraphConfig,
        connection: _AsyncConnection,
        record_factory: Callable[[str, str], Any],
    ):
        config.validate()
        self._config = config
        self._connection = connection
        self._record_factory = record_factory
        self._closed = False

    @classmethod
    async def connect(
        cls,
        config: SurrealGraphConfig,
        *,
        connection_factory: Callable[[str], _AsyncConnection] | None = None,
        record_factory: Callable[[str, str], Any] | None = None,
    ) -> SurrealGraphClient:
        """Connect, authenticate at database scope, select the fixed target, and verify it."""
        config.validate()
        if connection_factory is None or record_factory is None:
            try:
                from surrealdb import AsyncSurreal, RecordID
            except ImportError as exc:  # pragma: no cover - integration configuration path
                raise SurrealGraphError("SurrealDB Python SDK is not installed") from exc
            connection_factory = connection_factory or AsyncSurreal
            record_factory = record_factory or RecordID

        connection = connection_factory(config.endpoint)
        client = cls(config, connection, record_factory)
        try:
            await connection.__aenter__()
            await connection.signin(
                {
                    "username": config.username,
                    "password": config.password,
                    "namespace": config.namespace,
                    "database": config.database,
                }
            )
            await connection.use(config.namespace, config.database)
            await client.verify_health_and_schema()
            return client
        except BaseException as exc:
            with suppress(Exception):
                await connection.__aexit__(None, None, None)
            if not isinstance(exc, Exception) or isinstance(exc, (ValueError, SurrealGraphError)):
                raise
            raise SurrealGraphError("Surreal graph connection or readiness check failed") from exc

    async def __aenter__(self) -> SurrealGraphClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._connection.__aexit__(None, None, None)
        except Exception as exc:
            raise SurrealGraphError("Surreal graph connection close failed") from exc

    async def verify_health_and_schema(self) -> str:
        self._ensure_open()
        try:
            version = str(await self._connection.version())
            info = await self._query_first(_INFO_DATABASE)
        except Exception as exc:
            if isinstance(exc, SurrealGraphError):
                raise
            raise SurrealGraphError("Surreal graph health or schema check failed") from exc
        tables = info.get("tables") if isinstance(info, Mapping) else None
        if not isinstance(tables, Mapping):
            raise SurrealGraphError("Surreal graph schema response is invalid")
        missing = sorted(REQUIRED_TABLES - set(tables))
        if missing:
            raise SurrealGraphError("Surreal graph schema is incomplete: " + ", ".join(missing))
        return version

    async def write_operation_run(self, run: OperationRunWrite) -> Any:
        document = run.document()
        record_id = self._stable_record("operation_run", run.run_key)
        existing = await self._select(record_id)
        if existing is not None:
            self._verify_run_identity(existing, document)
            if _same_document(existing, document):
                return existing
        try:
            if existing is None:
                return await self._query_first(
                    _CREATE_RECORD, {"record_id": record_id, "document": document}
                )
            result = await self._query_first(
                _UPDATE_RECORD,
                {"record_id": record_id, "document": document, "expected": dict(existing)},
            )
            if result is not None:
                return result
        except SurrealGraphError:
            pass
        raced = await self._select(record_id)
        if raced is not None and _same_document(raced, document):
            return raced
        raise ProjectionConflictError("Operation run changed concurrently; replay refused")

    async def write_projection_snapshot(self, snapshot: ProjectionSnapshotWrite) -> Any:
        """Create an immutable snapshot, accepting an exact replay and rejecting drift."""
        document = snapshot.document()
        record_id = self._stable_record("projection_snapshot", snapshot.snapshot_key)
        existing = await self._select(record_id)
        if existing is not None:
            if not _same_document(existing, document):
                raise ProjectionConflictError("Projection snapshot key conflicts with stored facts")
            return existing
        try:
            return await self._query_first(
                _CREATE_RECORD, {"record_id": record_id, "document": document}
            )
        except SurrealGraphError as exc:
            # A concurrent replay may have won the create. Accept it only if it is exact.
            raced = await self._select(record_id)
            if raced is not None and _same_document(raced, document):
                return raced
            raise ProjectionConflictError(
                "Projection snapshot create conflicted with stored facts"
            ) from exc

    def projection_record(self, table: str, key: str) -> Any:
        if table not in REQUIRED_TABLES:
            raise ValueError("Unsupported projection table")
        return self._stable_record(table, key)

    async def read_projection_record(self, table: str, key: str) -> Mapping[str, Any] | None:
        return await self._select(self.projection_record(table, key))

    async def write_imported_node(self, table: str, key: str, document: Mapping[str, Any]) -> Any:
        """Create immutable imported observations; content retains its first-seen snapshot."""
        if table not in {"store", "occurrence", "content"}:
            raise ValueError("Unsupported imported node table")
        desired = {**document, "projection_key": key, "fact_layer": "imported"}
        record_id = self._stable_record(table, key)

        def matches(existing: Mapping[str, Any]) -> bool:
            if table == "content":
                return all(existing.get(k) == desired[k] for k in ("sha256", "size_bytes"))
            return _same_document(existing, desired)

        existing = await self._select(record_id)
        if existing is not None:
            if not matches(existing):
                raise ProjectionConflictError("Imported projection conflicts with stored facts")
            return existing
        try:
            return await self._query_first(
                _CREATE_RECORD, {"record_id": record_id, "document": desired}
            )
        except SurrealGraphError:
            raced = await self._select(record_id)
            if raced is not None and matches(raced):
                return raced
            raise

    async def write_imported_relation(self, table: str, source: Any, target: Any) -> Any:
        if table not in {"stored_at", "occurrence_has_content", "produced_by"}:
            raise ValueError("Unsupported imported relation")
        edge = self._stable_record(table, f"{source}\n{target}")
        existing = await self._select(edge)
        desired = {"in": source, "out": target, "fact_layer": "imported"}
        if existing is not None:
            if not _same_document(existing, desired):
                raise ProjectionConflictError("Imported relation conflicts with stored facts")
            return existing
        try:
            return await self._query_first(
                "RELATE ONLY $source->$edge->$target SET fact_layer = 'imported' RETURN AFTER;",
                {"source": source, "edge": edge, "target": target},
            )
        except SurrealGraphError:
            raced = await self._select(edge)
            if raced is not None and _same_document(raced, desired):
                return raced
            raise

    async def graph_neighborhood(
        self, root: GraphRecordRef, *, edge_limit: int = 50
    ) -> GraphNeighborhood:
        root.validate()
        if not 1 <= edge_limit <= 100:
            raise ValueError("Graph neighborhood edge limit must be between 1 and 100")
        result = await self._query_first(
            _NEIGHBORHOOD,
            {"root": self._record_factory(root.table, root.key), "edge_limit": edge_limit},
        )
        if not isinstance(result, Mapping):
            raise SurrealGraphError("Surreal graph neighborhood response is invalid")
        edges = result.get("edges", [])
        if not isinstance(edges, list) or len(edges) > edge_limit:
            raise SurrealGraphError("Surreal graph neighborhood exceeded its response bound")
        return GraphNeighborhood(root=result.get("root"), edges=tuple(edges))

    async def projection_summary(self, snapshot_key: str) -> Mapping[str, Any]:
        """Return bounded projection counts and its final completion marker."""
        if not _SAFE_KEY.fullmatch(snapshot_key):
            raise ValueError("Projection snapshot key is invalid")
        snapshot = self._stable_record("projection_snapshot", snapshot_key)
        result = await self._query_first(_PROJECTION_SUMMARY, {"snapshot": snapshot})
        if not isinstance(result, Mapping):
            raise SurrealGraphError("Surreal projection summary response is invalid")
        for count_name in ("occurrences", "stores", "stored_at", "content_links"):
            if type(result.get(count_name)) is not int or result[count_name] < 0:
                raise SurrealGraphError("Surreal projection summary count is invalid")
        completion = result.get("completion")
        if not isinstance(completion, list) or len(completion) > 1:
            raise SurrealGraphError("Surreal projection completion response is invalid")
        return result

    async def _select(self, record_id: Any) -> Mapping[str, Any] | None:
        result = await self._query_first(_SELECT_RECORD, {"record_id": record_id})
        if result is None:
            return None
        if not isinstance(result, Mapping):
            raise SurrealGraphError("Surreal graph record response is invalid")
        return result

    async def _query_first(self, statement: str, variables: Mapping[str, Any] | None = None) -> Any:
        self._ensure_open()
        try:
            async with asyncio.timeout(30):
                return await self._connection.query(
                    statement, _bound_nulls(variables) if variables is not None else None
                )
        except Exception as exc:
            raise SurrealGraphError("Surreal graph query failed") from exc

    def _stable_record(self, table: str, stable_key: str) -> Any:
        digest = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
        return self._record_factory(table, digest)

    def _ensure_open(self) -> None:
        if self._closed:
            raise SurrealGraphError("Surreal graph client is closed")

    @staticmethod
    def _verify_run_identity(existing: Mapping[str, Any], desired: Mapping[str, Any]) -> None:
        immutable = ("run_key", "tool_name", "tool_version", "started_at")
        if any(existing.get(key) != desired.get(key) for key in immutable):
            raise ProjectionConflictError("Operation run key conflicts with stored identity")
        previous = existing.get("status")
        current = desired.get("status")
        if previous in _TERMINAL_STATUSES and previous != current:
            raise ProjectionConflictError("A terminal operation run cannot change status")
        if previous == "running" and current not in _RUN_STATUSES:
            raise ProjectionConflictError("Invalid operation-run status transition")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Projection datetimes must be timezone-aware")
    return value.astimezone(UTC)


def _without_none(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _same_document(existing: Mapping[str, Any], desired: Mapping[str, Any]) -> bool:
    return {key: value for key, value in existing.items() if key != "id"} == dict(desired)


def _bound_nulls(value: Any) -> Any:
    """SDK 2 encodes Python None as NONE, which erases object fields.

    Imported metadata nulls are explicit unknown values, not absent fields.
    Encode them as CBOR null (simple value 22). Apply the same conversion to
    expected CAS documents so stored NULL is compared against NULL on replay.
    Optional schema fields remain omitted by their document builders.
    """
    if value is None:
        return CBORSimpleValue(22)
    if isinstance(value, Mapping):
        return {key: _bound_nulls(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_bound_nulls(item) for item in value]
    return value
