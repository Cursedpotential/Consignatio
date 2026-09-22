from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import pyarrow as pa
import pyarrow.parquet as pq

from .models import DocumentEnrichment, ExtractedText, SourceMetadata, TextChunk

SCHEMA_VERSION = "casebible-text-index-v1"


def stable_document_id(source_id: str, relative_path: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"casebible:{source_id}:{relative_path.casefold()}"))


def vault_document_id(source_id: str, identity: str) -> str:
    """Content-addressed document identity for a catalog object.

    Owner ruling 2026-09-22 10:48: sorting the vault and indexing it happen at the same
    time, so an object's index row must survive being moved to its final folder. The
    identity is therefore ``source_id`` + the catalog content hash, NOT the key. Moving an
    object changes only its ``vault_key`` property: the document id, version id, chunk ids
    and vectors are unchanged, so nothing is re-extracted and nothing is re-embedded.

    The one exception is an object the catalog has no SHA-1 for (a B2 large file uploaded
    in parts). Its identity falls back to key+size, which a move does change; those rows
    re-index. Byline: Claude Code · Opus 5 · 2026-09-22.
    """
    return str(uuid5(NAMESPACE_URL, f"casebible:content:{source_id}:{identity}"))


def vault_version_id(
    document_id: str, identity: str, *, embed_model: str, summary_model: str
) -> str:
    """Version identity for a catalog object.

    The catalog's recorded SHA-1 is the content identity (``identity``), so the version
    is known before a single byte is fetched. Byline: Claude Code · Opus 5 · 2026-09-22.
    """
    value = "|".join([document_id, identity, embed_model, summary_model, SCHEMA_VERSION])
    return str(uuid5(NAMESPACE_URL, value))


def logical_version_id(
    document_id: str,
    source: SourceMetadata,
    *,
    embed_model: str,
    summary_model: str,
) -> str:
    value = "|".join(
        [
            document_id,
            source.content_sha256,
            str(source.modified_ns),
            embed_model,
            summary_model,
            SCHEMA_VERSION,
        ]
    )
    return str(uuid5(NAMESPACE_URL, value))


def artifact_id(
    enrichment: DocumentEnrichment,
    chunks: Sequence[TextChunk],
    embeddings: Sequence[Sequence[float]],
) -> str:
    digest = hashlib.sha256()
    digest.update(enrichment.model_dump_json(exclude_none=False).encode("utf-8"))
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        digest.update(f"{chunk.ordinal}:{chunk.start}:{chunk.end}:".encode())
        digest.update(chunk.text.encode("utf-8"))
        digest.update(pa.array(embedding, type=pa.float32()).buffers()[1].to_pybytes())
    return digest.hexdigest()


def _timestamp_type() -> pa.DataType:
    return pa.timestamp("us", tz="UTC")


def document_schema() -> pa.Schema:
    return pa.schema(
        [
            ("document_id", pa.string()),
            ("version_id", pa.string()),
            ("artifact_id", pa.string()),
            ("source_id", pa.string()),
            ("relative_path", pa.string()),
            # Vault identity (Claude Code · Opus 5 · 2026-09-22): the B2 object key and the
            # catalog's resolution, so a hit can be opened from the vault, not a desktop.
            ("vault_key", pa.string()),
            ("resolution", pa.string()),
            ("member_path", pa.string()),
            ("filename", pa.string()),
            ("extension", pa.string()),
            ("media_type", pa.string()),
            ("byte_size", pa.int64()),
            ("content_sha256", pa.string()),
            ("source_created_at", _timestamp_type()),
            ("source_modified_at", _timestamp_type()),
            ("indexed_at", _timestamp_type()),
            ("title", pa.string()),
            ("document_type", pa.string()),
            ("document_date", pa.string()),
            ("date_basis", pa.string()),
            ("short_summary", pa.string()),
            ("detailed_summary", pa.string()),
            ("people", pa.list_(pa.string())),
            ("organizations", pa.list_(pa.string())),
            ("locations", pa.list_(pa.string())),
            ("dates_mentioned", pa.list_(pa.string())),
            ("topics", pa.list_(pa.string())),
            ("keywords", pa.list_(pa.string())),
            ("case_relevance", pa.string()),
            ("language", pa.string()),
            ("confidence", pa.float32()),
            ("review_notes", pa.list_(pa.string())),
            ("review_state", pa.string()),
            ("record_role", pa.string()),
            ("index_status", pa.string()),
            ("extraction_method", pa.string()),
            ("extraction_notes", pa.list_(pa.string())),
            ("page_count", pa.int32()),
            ("text_char_count", pa.int64()),
            ("chunk_count", pa.int32()),
            ("summary_coverage", pa.string()),
            ("summary_coverage_ratio", pa.float32()),
            ("summary_model", pa.string()),
            ("embedding_model", pa.string()),
            ("embedding_dimensions", pa.int32()),
            ("schema_version", pa.string()),
        ],
        metadata={
            b"casebible.schema": SCHEMA_VERSION.encode(),
            b"casebible.authority": b"derived machine proposal; source remains immutable",
        },
    )


def chunk_schema(dimensions: int) -> pa.Schema:
    return pa.schema(
        [
            ("document_id", pa.string()),
            ("version_id", pa.string()),
            ("artifact_id", pa.string()),
            ("chunk_id", pa.string()),
            ("source_id", pa.string()),
            ("relative_path", pa.string()),
            ("vault_key", pa.string()),
            ("resolution", pa.string()),
            ("member_path", pa.string()),
            ("filename", pa.string()),
            ("document_type", pa.string()),
            ("document_date", pa.string()),
            ("title", pa.string()),
            ("short_summary", pa.string()),
            ("chunk_ordinal", pa.int32()),
            ("char_start", pa.int64()),
            ("char_end", pa.int64()),
            ("text", pa.string()),
            ("text_sha256", pa.string()),
            ("token_estimate", pa.int32()),
            ("embedding", pa.list_(pa.float32(), dimensions)),
            # "ok" or "pending": a run may extract and chunk with embeddings deferred
            # (Claude Code · Opus 5 · 2026-09-22) when the embedding provider is unavailable.
            ("embedding_status", pa.string()),
            ("embedding_model", pa.string()),
            ("schema_version", pa.string()),
            ("indexed_at", _timestamp_type()),
        ],
        metadata={b"casebible.schema": SCHEMA_VERSION.encode()},
    )


def tables_for_document(
    *,
    source_id: str,
    source: SourceMetadata,
    extracted: ExtractedText,
    enrichment: DocumentEnrichment,
    chunks: Sequence[TextChunk],
    embeddings: Sequence[Sequence[float]],
    coverage: str,
    coverage_ratio: float,
    embed_model: str,
    summary_model: str,
    dimensions: int,
    indexed_at: datetime | None = None,
    vault_key: str = "",
    resolution: str = "local",
    member_path: str = "",
) -> tuple[str, str, pa.Table, pa.Table]:
    if len(chunks) != len(embeddings):
        raise ValueError("Every chunk must have exactly one embedding")
    now = indexed_at or datetime.now(UTC)
    document_id = stable_document_id(source_id, source.relative_path)
    version_id = logical_version_id(
        document_id,
        source,
        embed_model=embed_model,
        summary_model=summary_model,
    )
    artifact = artifact_id(enrichment, chunks, embeddings)
    document_row: dict[str, Any] = {
        "document_id": document_id,
        "version_id": version_id,
        "artifact_id": artifact,
        "source_id": source_id,
        "relative_path": source.relative_path,
        "vault_key": vault_key,
        "resolution": resolution,
        "member_path": member_path,
        "filename": source.filename,
        "extension": source.extension,
        "media_type": extracted.media_type,
        "byte_size": source.byte_size,
        "content_sha256": source.content_sha256,
        "source_created_at": source.created_at,
        "source_modified_at": source.modified_at,
        "indexed_at": now,
        "title": enrichment.title or source.filename,
        "document_type": enrichment.document_type,
        "document_date": enrichment.document_date,
        "date_basis": enrichment.date_basis,
        "short_summary": enrichment.short_summary,
        "detailed_summary": enrichment.detailed_summary,
        "people": enrichment.people,
        "organizations": enrichment.organizations,
        "locations": enrichment.locations,
        "dates_mentioned": enrichment.dates_mentioned,
        "topics": enrichment.topics,
        "keywords": enrichment.keywords,
        "case_relevance": enrichment.case_relevance,
        "language": enrichment.language,
        "confidence": enrichment.confidence,
        "review_notes": enrichment.review_notes,
        "review_state": "unreviewed",
        "record_role": "machine_proposal",
        "index_status": extracted.status,
        "extraction_method": extracted.extraction_method,
        "extraction_notes": list(extracted.notes),
        "page_count": extracted.page_count,
        "text_char_count": len(extracted.text),
        "chunk_count": len(chunks),
        "summary_coverage": coverage,
        "summary_coverage_ratio": coverage_ratio,
        "summary_model": summary_model,
        "embedding_model": embed_model,
        "embedding_dimensions": dimensions,
        "schema_version": SCHEMA_VERSION,
    }
    document_table = pa.Table.from_pylist([document_row], schema=document_schema())

    chunk_rows: list[dict[str, Any]] = []
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        chunk_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        chunk_rows.append(
            {
                "document_id": document_id,
                "version_id": version_id,
                "artifact_id": artifact,
                "chunk_id": str(uuid5(NAMESPACE_URL, f"{version_id}:{chunk.ordinal}:{chunk_hash}")),
                "source_id": source_id,
                "relative_path": source.relative_path,
                "vault_key": vault_key,
                "resolution": resolution,
                "member_path": member_path,
                "filename": source.filename,
                "document_type": enrichment.document_type,
                "document_date": enrichment.document_date,
                "title": enrichment.title or source.filename,
                "short_summary": enrichment.short_summary,
                "chunk_ordinal": chunk.ordinal,
                "char_start": chunk.start,
                "char_end": chunk.end,
                "text": chunk.text,
                "text_sha256": chunk_hash,
                "token_estimate": max(1, len(chunk.text) // 4),
                "embedding": list(embedding),
                "embedding_status": "ok" if any(embedding) else "pending",
                "embedding_model": embed_model,
                "schema_version": SCHEMA_VERSION,
                "indexed_at": now,
            }
        )
    chunk_table = pa.Table.from_pylist(chunk_rows, schema=chunk_schema(dimensions))
    return version_id, artifact, document_table, chunk_table


def parquet_bytes(table: pa.Table) -> bytes:
    sink = pa.BufferOutputStream()
    pq.write_table(
        table,
        sink,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
    )
    return sink.getvalue().to_pybytes()


def write_immutable(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError as exc:
        existing_hash = hashlib.sha256(path.read_bytes()).digest()
        if existing_hash != hashlib.sha256(content).digest():
            raise RuntimeError(
                f"Refusing to overwrite different immutable artifact: {path}"
            ) from exc
        return
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        # Leave an incomplete file visible for owner review; never delete it here.
        raise


def write_document_bundle(
    output_dir: Path,
    *,
    document_id: str,
    version_id: str,
    artifact: str,
    document_table: pa.Table,
    chunk_table: pa.Table,
) -> tuple[Path, Path]:
    stem = f"{document_id}--{version_id}--{artifact[:16]}"
    document_path = output_dir / "datasets" / "documents" / f"{stem}.parquet"
    chunk_path = output_dir / "datasets" / "chunks" / f"{stem}.parquet"
    write_immutable(document_path, parquet_bytes(document_table))
    write_immutable(chunk_path, parquet_bytes(chunk_table))
    return document_path, chunk_path


def chunk_rows_table(rows: list[dict[str, Any]], dimensions: int) -> pa.Table:
    """Build one chunk shard from already-assembled rows (streaming writer)."""
    return pa.Table.from_pylist(rows, schema=chunk_schema(dimensions))


def document_row_table(row: dict[str, Any]) -> pa.Table:
    return pa.Table.from_pylist([row], schema=document_schema())


def write_chunk_shard(
    output_dir: Path, *, document_id: str, version_id: str, artifact: str, part: int,
    table: pa.Table,
) -> Path:
    """Write one chunk part. A large object produces many parts, never one huge table.

    Byline: Claude Code · Opus 5 · 2026-09-22.
    """
    stem = f"{document_id}--{version_id}--{artifact[:16]}--p{part:05d}"
    path = output_dir / "datasets" / "chunks" / f"{stem}.parquet"
    write_immutable(path, parquet_bytes(table))
    return path


def write_document_row(
    output_dir: Path, *, document_id: str, version_id: str, artifact: str, table: pa.Table,
) -> Path:
    stem = f"{document_id}--{version_id}--{artifact[:16]}"
    path = output_dir / "datasets" / "documents" / f"{stem}.parquet"
    write_immutable(path, parquet_bytes(table))
    return path


def write_json_immutable(path: Path, value: dict[str, Any]) -> None:
    write_immutable(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(),
    )
