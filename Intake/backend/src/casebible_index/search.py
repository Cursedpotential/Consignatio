from __future__ import annotations

import asyncio
import re
from pathlib import Path

import duckdb

from .config import Settings
from .models import SearchHit, SearchResponse
from .nim import NimClient
from .snapshots import newest_snapshot


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def _lexical_score(query: str, text: str) -> float:
    terms = {term for term in re.findall(r"[\w'-]+", query.casefold()) if len(term) >= 3}
    if not terms:
        return 0.0
    haystack = text.casefold()
    return sum(term in haystack for term in terms) / len(terms)


class SemanticSearcher:
    def __init__(self, settings: Settings, nim_client: NimClient) -> None:
        self.settings = settings
        self.nim_client = nim_client

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        document_type: str | None = None,
        path_prefix: str | None = None,
        hybrid: bool = True,
    ) -> SearchResponse:
        snapshot = newest_snapshot(self.settings.output_dir)
        if snapshot is None:
            raise FileNotFoundError("No active index snapshot exists; run `casebible-index index`")
        chunks_dir = self.settings.output_dir / "datasets" / "chunks"
        if not any(chunks_dir.glob("*.parquet")):
            return SearchResponse(
                query=query,
                model=self.settings.embed_model,
                snapshot=str(snapshot),
                hits=[],
            )
        vector = await self.nim_client.embed_query(query)
        candidates = await asyncio.to_thread(
            self._query_chunks,
            vector,
            max(limit * 8, 50),
            snapshot,
            document_type,
            path_prefix,
        )
        hits: list[SearchHit] = []
        for row in candidates:
            lexical = _lexical_score(query, row["text"]) if hybrid else 0.0
            semantic = float(row["semantic_score"])
            score = semantic * 0.9 + lexical * 0.1 if hybrid else semantic
            hits.append(
                SearchHit(
                    score=score,
                    semantic_score=semantic,
                    lexical_score=lexical,
                    **{key: value for key, value in row.items() if key != "semantic_score"},
                )
            )
        hits.sort(key=lambda hit: (hit.score, hit.semantic_score), reverse=True)
        return SearchResponse(
            query=query,
            model=self.settings.embed_model,
            snapshot=str(snapshot),
            hits=hits[:limit],
        )

    def _query_chunks(
        self,
        vector: list[float],
        candidate_limit: int,
        snapshot: Path,
        document_type: str | None,
        path_prefix: str | None,
    ) -> list[dict[str, object]]:
        chunks_glob = self.settings.output_dir / "datasets" / "chunks" / "*.parquet"
        clauses: list[str] = []
        parameters: list[object] = [vector]
        if document_type:
            clauses.append("lower(c.document_type) = lower(?)")
            parameters.append(document_type)
        if path_prefix:
            clauses.append("starts_with(lower(c.relative_path), lower(?))")
            parameters.append(path_prefix.replace("\\", "/"))
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        parameters.append(candidate_limit)
        connection = duckdb.connect(":memory:")
        try:
            cursor = connection.execute(
                f"""
                SELECT
                    c.document_id,
                    c.version_id,
                    c.chunk_id,
                    c.relative_path,
                    c.filename,
                    c.document_type,
                    c.document_date,
                    c.title,
                    c.short_summary,
                    c.chunk_ordinal,
                    c.char_start,
                    c.char_end,
                    c.text,
                    array_cosine_similarity(
                        c.embedding::FLOAT[{self.settings.embed_dimensions}],
                        ?::FLOAT[{self.settings.embed_dimensions}]
                    ) AS semantic_score
                FROM read_parquet('{_sql_path(chunks_glob)}', union_by_name = true) c
                JOIN read_parquet('{_sql_path(snapshot)}') s
                  USING (document_id, version_id, artifact_id)
                {where}
                ORDER BY semantic_score DESC
                LIMIT ?
                """,
                parameters,
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
        finally:
            connection.close()


def list_documents(settings: Settings, *, limit: int = 100) -> list[dict[str, object]]:
    snapshot = newest_snapshot(settings.output_dir)
    if snapshot is None:
        return []
    documents_glob = settings.output_dir / "datasets" / "documents" / "*.parquet"
    if not any(documents_glob.parent.glob(documents_glob.name)):
        return []
    connection = duckdb.connect(":memory:")
    try:
        cursor = connection.execute(
            f"""
            SELECT d.document_id, d.relative_path, d.filename, d.title,
                   d.document_type, d.document_date, d.short_summary,
                   d.review_state, d.index_status
            FROM read_parquet('{_sql_path(documents_glob)}', union_by_name = true) d
            JOIN read_parquet('{_sql_path(snapshot)}') s
              USING (document_id, version_id, artifact_id)
            ORDER BY d.relative_path
            LIMIT ?
            """,
            [limit],
        )
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        connection.close()


# Byline: Claude Code · Sonnet 5 · 2026-09-14
# Only the columns the pipeline actually writes to the documents dataset are
# surfaced here (see models.py / pipeline.py `write_document_bundle`). Never add
# a field the extractor does not populate (no invented EXIF/PDF/media metadata) --
# a native panel renders a "not extracted" flag for those categories instead.
_LOOKUP_COLUMNS = (
    "d.document_id", "d.relative_path", "d.filename", "d.extension", "d.media_type",
    "d.byte_size", "d.content_sha256", "d.source_created_at", "d.source_modified_at",
    "d.indexed_at", "d.title", "d.document_type", "d.document_date", "d.date_basis",
    "d.short_summary", "d.detailed_summary", "d.people", "d.organizations",
    "d.locations", "d.dates_mentioned", "d.topics", "d.keywords", "d.case_relevance",
    "d.language", "d.confidence", "d.review_notes", "d.review_state", "d.record_role",
    "d.index_status", "d.extraction_method", "d.extraction_notes", "d.page_count",
    "d.text_char_count", "d.chunk_count", "d.summary_coverage", "d.summary_coverage_ratio",
    "d.summary_model", "d.embedding_model", "d.embedding_dimensions", "d.schema_version",
)


_FORBIDDEN_SQL_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "attach", "detach", "copy",
    "pragma", "create", "call", "checkpoint", "install", "load", "export", "import",
    "set ", "grant", "revoke", "vacuum", "merge",
)


class DuckDbQueryError(ValueError):
    pass


def run_lake_query(settings: Settings, sql: str, *, limit: int = 200) -> dict[str, object]:
    """Read-only SQL over the derived Parquet lake. Two fixed views only:
    `documents` and `chunks` (bound to this backend's own output dir) -- never an
    arbitrary filesystem path from the caller. Single SELECT statement, bounded
    result rows; any DDL/DML keyword is rejected before DuckDB ever sees it.
    """
    stripped = sql.strip().rstrip(";")
    if not stripped or len(stripped) > 8000:
        raise DuckDbQueryError("Query must be 1-8000 characters")
    if ";" in stripped:
        raise DuckDbQueryError("Only a single statement is allowed")
    lowered = stripped.casefold()
    if not lowered.startswith(("select", "with")):
        raise DuckDbQueryError("Only SELECT/WITH queries are allowed")
    for keyword in _FORBIDDEN_SQL_KEYWORDS:
        if keyword in lowered:
            raise DuckDbQueryError(f"Disallowed keyword in query: {keyword.strip()}")
    bounded_limit = min(max(limit, 1), 1000)
    documents_glob = settings.output_dir / "datasets" / "documents" / "*.parquet"
    chunks_glob = settings.output_dir / "datasets" / "chunks" / "*.parquet"
    connection = duckdb.connect(":memory:")
    try:
        if any(documents_glob.parent.glob(documents_glob.name)):
            connection.execute(
                f"CREATE VIEW documents AS "
                f"SELECT * FROM read_parquet('{_sql_path(documents_glob)}', union_by_name = true)"
            )
        if any(chunks_glob.parent.glob(chunks_glob.name)):
            connection.execute(
                f"CREATE VIEW chunks AS "
                f"SELECT * FROM read_parquet('{_sql_path(chunks_glob)}', union_by_name = true)"
            )
        wrapped = f"SELECT * FROM ({stripped}) AS query_result LIMIT {bounded_limit}"
        try:
            cursor = connection.execute(wrapped)
        except duckdb.Error as exc:
            raise DuckDbQueryError(f"Query failed: {type(exc).__name__}") from exc
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        def _cell(value: object) -> object:
            return value.isoformat() if hasattr(value, "isoformat") else value

        return {
            "columns": columns,
            "rows": [[_cell(value) for value in row] for row in rows],
            "row_count": len(rows),
            "truncated": len(rows) >= bounded_limit,
            "views_available": [
                name for name, glob_path in (("documents", documents_glob), ("chunks", chunks_glob))
                if any(glob_path.parent.glob(glob_path.name))
            ],
        }
    finally:
        connection.close()


def relative_path_for(settings: Settings, absolute_path: str) -> str | None:
    """Best-effort relative path of `absolute_path` under the configured source.

    Returns None (never raises) when the path is outside the configured source
    tree -- that is a normal "not this backend's source" outcome, not an error.
    """
    try:
        candidate = Path(absolute_path).resolve()
        source_root = settings.source_dir.resolve()
        if not candidate.is_relative_to(source_root):
            return None
        return candidate.relative_to(source_root).as_posix()
    except (OSError, ValueError):
        return None


def lookup_document(settings: Settings, absolute_path: str) -> dict[str, object]:
    """Real catalog/fingerprint row(s) for one source path; never reads source bytes.

    `found: False` (no exception) covers both "outside the configured source" and
    "inside the source but not yet indexed" -- the caller renders one small flag,
    never a fabricated row.
    """
    relative_path = relative_path_for(settings, absolute_path)
    if relative_path is None:
        return {"found": False, "reason": "path_outside_configured_source", "duplicates": []}
    snapshot = newest_snapshot(settings.output_dir)
    if snapshot is None:
        return {"found": False, "reason": "no_active_index_snapshot", "duplicates": []}
    documents_glob = settings.output_dir / "datasets" / "documents" / "*.parquet"
    if not any(documents_glob.parent.glob(documents_glob.name)):
        return {"found": False, "reason": "no_active_index_snapshot", "duplicates": []}
    connection = duckdb.connect(":memory:")
    try:
        columns_sql = ", ".join(_LOOKUP_COLUMNS)
        row = connection.execute(
            f"""
            SELECT {columns_sql}
            FROM read_parquet('{_sql_path(documents_glob)}', union_by_name = true) d
            JOIN read_parquet('{_sql_path(snapshot)}') s
              USING (document_id, version_id, artifact_id)
            WHERE d.relative_path = ?
            ORDER BY d.indexed_at DESC
            LIMIT 1
            """,
            [relative_path],
        ).fetchone()
        if row is None:
            return {
                "found": False,
                "reason": "not_yet_indexed",
                "relative_path": relative_path,
                "duplicates": [],
            }
        names = [column.split(".", 1)[1] for column in _LOOKUP_COLUMNS]
        record: dict[str, object] = dict(zip(names, row, strict=True))
        for key, value in record.items():
            if hasattr(value, "isoformat"):
                record[key] = value.isoformat()
        duplicates: list[dict[str, object]] = []
        content_sha256 = record.get("content_sha256")
        if content_sha256:
            duplicate_rows = connection.execute(
                f"""
                SELECT d.relative_path, d.filename
                FROM read_parquet('{_sql_path(documents_glob)}', union_by_name = true) d
                JOIN read_parquet('{_sql_path(snapshot)}') s
                  USING (document_id, version_id, artifact_id)
                WHERE d.content_sha256 = ? AND d.relative_path != ?
                LIMIT 50
                """,
                [content_sha256, relative_path],
            ).fetchall()
            duplicates = [{"relative_path": r[0], "filename": r[1]} for r in duplicate_rows]
        return {"found": True, "snapshot": str(snapshot), "duplicates": duplicates, **record}
    finally:
        connection.close()
