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
