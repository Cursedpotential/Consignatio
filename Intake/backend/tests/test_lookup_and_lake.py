# Byline: Claude Code · Sonnet 5 · 2026-09-14
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from casebible_index.config import Settings
from casebible_index.models import DocumentEnrichment, ExtractedText, SourceMetadata, TextChunk
from casebible_index.parquet_store import (
    stable_document_id,
    tables_for_document,
    write_document_bundle,
)
from casebible_index.search import DuckDbQueryError, lookup_document, relative_path_for, run_lake_query
from casebible_index.snapshots import build_active_snapshot


def settings_for(source: Path, output: Path) -> Settings:
    return Settings(
        source_dir=source,
        source_id="test",
        output_dir=output,
        nim_base_url="https://example.test/v1",
        embed_model="embed",
        summary_model="summary",
        embed_dimensions=3,
        chunk_size=100,
        chunk_overlap=10,
        summary_max_chars=1000,
        embed_batch_size=4,
        max_concurrency=1,
        timeout_seconds=2,
        max_retries=0,
    )


def _index_one_document(source: Path, output: Path, config: Settings) -> None:
    path = source / "note.txt"
    path.write_text("parenting time exchange schedule", encoding="utf-8")
    now = datetime.now(UTC)
    source_meta = SourceMetadata(
        relative_path="note.txt",
        filename="note.txt",
        extension=".txt",
        byte_size=path.stat().st_size,
        created_at=now,
        modified_at=now,
        modified_ns=path.stat().st_mtime_ns,
        content_sha256="a" * 64,
    )
    extracted = ExtractedText(
        text="parenting time exchange schedule",
        media_type="text/plain",
        page_count=None,
        extraction_method="decoded_text",
        status="indexed",
    )
    enrichment = DocumentEnrichment(
        title="Schedule", document_type="note", short_summary="A scheduling note.", confidence=0.9,
    )
    chunks = [TextChunk(ordinal=0, start=0, end=33, text=extracted.text)]
    version, artifact, docs, chunk_table = tables_for_document(
        source_id=config.source_id,
        source=source_meta,
        extracted=extracted,
        enrichment=enrichment,
        chunks=chunks,
        embeddings=[[1.0, 0.0, 0.0]],
        coverage="full_text",
        coverage_ratio=1.0,
        embed_model=config.embed_model,
        summary_model=config.summary_model,
        dimensions=config.embed_dimensions,
        indexed_at=now,
    )
    write_document_bundle(
        output,
        document_id=stable_document_id(config.source_id, "note.txt"),
        version_id=version,
        artifact=artifact,
        document_table=docs,
        chunk_table=chunk_table,
    )
    build_active_snapshot(config)


def test_relative_path_for_rejects_paths_outside_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"
    config = settings_for(source, output)
    outside = tmp_path / "elsewhere.txt"
    outside.write_text("x", encoding="utf-8")
    assert relative_path_for(config, str(outside)) is None
    inside = source / "note.txt"
    inside.write_text("x", encoding="utf-8")
    assert relative_path_for(config, str(inside)) == "note.txt"


def test_lookup_document_not_found_before_index(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"
    config = settings_for(source, output)
    (source / "note.txt").write_text("x", encoding="utf-8")
    result = lookup_document(config, str(source / "note.txt"))
    assert result["found"] is False
    assert result["duplicates"] == []


def test_lookup_document_returns_real_fields_and_duplicates(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"
    config = settings_for(source, output)
    _index_one_document(source, output, config)

    result = lookup_document(config, str(source / "note.txt"))
    assert result["found"] is True
    assert result["relative_path"] == "note.txt"
    assert result["title"] == "Schedule"
    assert result["content_sha256"] == "a" * 64
    # No EXIF/PDF/media fields are invented -- only real document columns appear.
    assert "exif" not in result
    assert "xmp" not in result
    assert result["duplicates"] == []


def test_lookup_document_path_outside_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"
    config = settings_for(source, output)
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    result = lookup_document(config, str(outside))
    assert result == {"found": False, "reason": "path_outside_configured_source", "duplicates": []}


def test_run_lake_query_returns_bounded_rows(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    output = tmp_path / "output"
    config = settings_for(source, output)
    _index_one_document(source, output, config)

    result = run_lake_query(config, "SELECT relative_path, title FROM documents", limit=10)
    assert result["columns"] == ["relative_path", "title"]
    assert result["rows"] == [["note.txt", "Schedule"]]
    assert result["truncated"] is False
    assert "documents" in result["views_available"]


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE documents",
        "INSERT INTO documents VALUES (1)",
        "SELECT * FROM documents; SELECT * FROM chunks",
        "ATTACH 'x.db'",
        "PRAGMA database_list",
        "",
    ],
)
def test_run_lake_query_rejects_unsafe_sql(tmp_path: Path, sql: str) -> None:
    config = settings_for(tmp_path / "source", tmp_path / "output")
    with pytest.raises(DuckDbQueryError):
        run_lake_query(config, sql)


def test_run_lake_query_no_snapshot_yet(tmp_path: Path) -> None:
    config = settings_for(tmp_path / "source", tmp_path / "output")
    result = run_lake_query(config, "SELECT 1 AS one")
    assert result["rows"] == [[1]]
    assert result["views_available"] == []
