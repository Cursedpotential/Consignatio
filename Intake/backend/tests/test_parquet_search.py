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
from casebible_index.search import SemanticSearcher
from casebible_index.snapshots import _is_current_source, build_active_snapshot


class FakeNim:
    async def embed_query(self, query: str) -> list[float]:
        assert query
        return [1.0, 0.0, 0.0]


def test_snapshot_source_guard_rejects_absolute_and_escape_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    inside = source / "inside.txt"
    inside.write_text("inside", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    assert _is_current_source(source, "inside.txt")
    assert not _is_current_source(source, str(outside))
    assert not _is_current_source(source, "../outside.txt")


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


@pytest.mark.asyncio
async def test_parquet_snapshot_and_semantic_search(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    path = source / "note.txt"
    path.write_text("parenting time exchange schedule", encoding="utf-8")
    config = settings_for(source, output)
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
        title="Schedule",
        document_type="note",
        short_summary="A scheduling note.",
        confidence=0.9,
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
    snapshot = build_active_snapshot(config)
    assert snapshot.is_file()

    response = await SemanticSearcher(config, FakeNim()).search("parenting schedule", limit=5)
    assert len(response.hits) == 1
    assert response.hits[0].relative_path == "note.txt"
    assert response.hits[0].semantic_score == pytest.approx(1.0)
