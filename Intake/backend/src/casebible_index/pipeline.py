"""The Coco super index pipeline: catalog or filesystem in, Parquet + Weaviate out.

> Byline: Claude Code · Opus 5 · 2026-09-22 (rewritten for streaming and bucket reads;
> original Claude Code · Opus 5 · 2026-09-18)

What changed on 2026-09-22, and why:

* **Catalog objects are read from the bucket**, not from a mount under
  ``CASEBIBLE_SOURCE_DIR``. The previous build listed the catalog correctly and then
  tried to open the object as a local path, which no deployment ever had.
* **No caps.** The 8 MiB reject, the 1,000,000-extracted-character raise and the
  512-chunk raise are gone (owner 2026-09-19/09-20: stream everything). Objects are read
  in windows, chunks are flushed to Parquet shards as they are produced, and peak memory
  is a window plus one shard regardless of object size.
* **Hits carry the vault key**, so a result can be opened from B2.
* **Weaviate is on by default** when a collection is configured.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import cocoindex as coco
import httpx
from cocoindex.connectors import localfs
from cocoindex.ops.text import RecursiveSplitter
from cocoindex.resources.file import PatternFilePathMatcher

from .catalog_source import iter_catalog_objects, safe_relative_key
from .config import SUPPORTED_EXTENSIONS, Settings
from .filesystem_search import WeaviateSearchConfig
from .models import DocumentEnrichment, SourceMetadata, TextChunk
from .nim import NimClient
from .object_store import ObjectStore, ReadCounters, configured_credentials
from .parquet_store import (
    SCHEMA_VERSION,
    chunk_rows_table,
    document_row_table,
    stable_document_id,
    streaming_artifact_id,
    vault_document_id,
    vault_version_id,
    write_chunk_shard,
    write_document_row,
)
from .run_status import RunStatus
from .secrets import get_secret
from .source_runtime import source_lock
from .stream_extract import ARCHIVE_EXTENSIONS, StreamOutcome, extract_stream
from .vault_source import OBJECT_STORE, LocalStreamFile, VaultFile
from .weaviate_target import WEAVIATE_WRITER, ObjectSpec, WeaviateObjectWriter, declare_chunk

NIM_CLIENT = coco.ContextKey[NimClient]("casebible_nim_client")
RUN_STATUS = coco.ContextKey[RunStatus]("intake_filesystem_run_status")
CATALOG_DSN = coco.ContextKey[str]("intake_catalog_dsn")
_splitter = RecursiveSplitter()
_EXCLUDED_SEGMENTS = frozenset({".git", ".review_hold", "to_be_deleted", "__pycache__"})
INDEXABLE_EXTENSIONS = frozenset(SUPPORTED_EXTENSIONS) | ARCHIVE_EXTENSIONS


def _catalog_key_is_indexable(key: str) -> bool:
    path = safe_relative_key(key)
    if path is None or _EXCLUDED_SEGMENTS.intersection(path.parts):
        return False
    return path.suffix.casefold() in INDEXABLE_EXTENSIONS


def _fallback_enrichment(filename: str, notes: tuple[str, ...]) -> DocumentEnrichment:
    return DocumentEnrichment(
        title=filename,
        document_type="unknown",
        short_summary="No usable text was available for summarization.",
        confidence=0.0,
        review_notes=list(notes),
    )


class ChunkAccumulator:
    """Turn a stream of text pieces into chunks without holding the document.

    Each piece is split with the same recursive splitter the non-streaming build used.
    A trailing overlap is carried into the next piece so a chunk boundary between two
    windows is not a hard cut.
    """

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._carry = ""
        self._offset = 0
        self._ordinal = 0

    def feed(self, piece: str) -> list[TextChunk]:
        text = self._carry + ("\n" if self._carry else "") + piece
        parts = _splitter.split(
            text, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap,
            language="markdown",
        )
        if not parts:
            self._carry = text
            return []
        # Keep the last split back: the next piece may continue it.
        emit, self._carry = list(parts[:-1]), parts[-1].text
        chunks: list[TextChunk] = []
        for part in emit:
            chunk = TextChunk(
                ordinal=self._ordinal,
                start=self._offset + part.start.char_offset,
                end=self._offset + part.end.char_offset,
                text=part.text,
            )
            self._ordinal += 1
            chunks.append(chunk)
        self._offset += max(len(text) - len(self._carry), 0)
        return chunks

    def finish(self) -> list[TextChunk]:
        if not self._carry.strip():
            return []
        chunk = TextChunk(
            ordinal=self._ordinal,
            start=self._offset,
            end=self._offset + len(self._carry),
            text=self._carry,
        )
        self._ordinal += 1
        self._carry = ""
        return [chunk]

    @property
    def count(self) -> int:
        return self._ordinal


async def _embed(
    client: NimClient | None, texts: list[str], *, batch_size: int, dimensions: int
) -> list[list[float]]:
    """Embed a batch, or return zero vectors when embeddings are deferred."""
    if client is None:
        return [[0.0] * dimensions for _ in texts]
    return await client.embed_documents(texts, batch_size=batch_size)


@coco.fn(memo=True)
async def process_file(
    file,
    *,
    source_id: str,
    output_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
    chunk_flush_size: int,
    summary_max_chars: int,
    embed_batch_size: int,
    embed_model: str,
    summary_model: str,
    embed_dimensions: int,
    embed_enabled: bool,
    summary_enabled: bool,
    weaviate_target: tuple[str, str, str] | None,
) -> None:
    key = file.key
    relative_path = key if isinstance(file, VaultFile) else PurePosixPath(key).as_posix()
    filename = PurePosixPath(key).name
    extension = PurePosixPath(key).suffix.casefold()
    vault_key = key if isinstance(file, VaultFile) else ""
    resolution = file.resolution
    byte_size = await file.size()

    # Identity: a vault object is identified by its CONTENT, so moving it to its final
    # folder changes only vault_key (owner 2026-09-22 10:48). A local file keeps the
    # path-based identity it has always had.
    if isinstance(file, VaultFile):
        identity = file.identity
        document_id = vault_document_id(source_id, identity)
    else:
        metadata = await file._fetch_metadata()
        identity = f"local:{byte_size}:{metadata.modified_time.isoformat()}"
        document_id = stable_document_id(source_id, relative_path)
    version_id = vault_version_id(
        document_id, identity, embed_model=embed_model, summary_model=summary_model
    )

    # Known before the first chunk, so shards can be WRITTEN as they are produced instead of
    # collected. Collecting them was a defect: 30,136 chunks × 2048 floats for one 61 MB
    # object is gigabytes of live Python objects, which is exactly the unbounded behaviour
    # this rewrite exists to remove.
    artifact = streaming_artifact_id(
        version_id, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
        embed_model=embed_model, summary_model=summary_model,
    )
    outcome = StreamOutcome()
    accumulator = ChunkAccumulator(chunk_size, chunk_overlap)
    summary_text: list[str] = []
    summary_chars = 0
    pending: list[TextChunk] = []
    total_chars = 0
    shard_count = 0
    now = datetime.now(UTC)
    client = coco.use_context(NIM_CLIENT) if embed_enabled or summary_enabled else None
    embed_client = client if embed_enabled else None

    def chunk_row(chunk: TextChunk, embedding: list[float]) -> dict:
        chunk_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        from uuid import NAMESPACE_URL, uuid5

        return {
            "document_id": document_id,
            "version_id": version_id,
            "artifact_id": artifact,
            "chunk_id": str(uuid5(NAMESPACE_URL, f"{version_id}:{chunk.ordinal}:{chunk_hash}")),
            "source_id": source_id,
            "relative_path": relative_path,
            "vault_key": vault_key,
            "resolution": resolution,
            "member_path": "",
            "filename": filename,
            "document_type": "unknown",
            "document_date": None,
            "title": filename,
            "short_summary": "",
            "chunk_ordinal": chunk.ordinal,
            "char_start": chunk.start,
            "char_end": chunk.end,
            "text": chunk.text,
            "text_sha256": chunk_hash,
            "token_estimate": max(1, len(chunk.text) // 4),
            "embedding": embedding,
            "embedding_status": "ok" if embed_enabled else "pending",
            "embedding_model": embed_model if embed_enabled else "",
            "schema_version": SCHEMA_VERSION,
            "indexed_at": now,
        }

    async def flush(final: bool = False) -> None:
        nonlocal pending, shard_count
        while pending and (final or len(pending) >= chunk_flush_size):
            batch, pending = pending[:chunk_flush_size], pending[chunk_flush_size:]
            vectors = await _embed(
                embed_client, [chunk.text for chunk in batch],
                batch_size=embed_batch_size, dimensions=embed_dimensions,
            )
            rows = [
                chunk_row(chunk, list(vector))
                for chunk, vector in zip(batch, vectors, strict=True)
            ]
            write_chunk_shard(
                output_dir, document_id=document_id, version_id=version_id, artifact=artifact,
                part=shard_count, table=chunk_rows_table(rows, embed_dimensions),
            )
            if weaviate_target is not None:
                origin, collection, vector_name = weaviate_target
                for row in rows:
                    if row["embedding_status"] != "ok":
                        continue
                    declare_chunk(origin, collection, row["chunk_id"], ObjectSpec(
                        properties={
                            "source_id": source_id, "source_path": relative_path,
                            "vault_key": vault_key, "resolution": resolution,
                            "document_id": row["document_id"], "chunk_id": row["chunk_id"],
                            "filename": filename, "text": row["text"],
                            "embed_model": embed_model,
                        },
                        vectors={vector_name: row["embedding"]},
                    ))
            shard_count += 1
            rows.clear()

    async for piece in extract_stream(key, file.windows(), outcome):
        total_chars += len(piece)
        if summary_chars < summary_max_chars:
            summary_text.append(piece[: summary_max_chars - summary_chars])
            summary_chars += len(summary_text[-1])
        for chunk in accumulator.feed(piece):
            pending.append(chunk)
        await flush()
    for chunk in accumulator.finish():
        pending.append(chunk)
    await flush(final=True)

    enrichment = _fallback_enrichment(filename, outcome.notes)
    coverage, coverage_ratio = ("none", 0.0)
    if outcome.status == "indexed" and summary_enabled and client is not None and summary_text:
        joined = "".join(summary_text)
        coverage = "full" if summary_chars >= total_chars else "head"
        coverage_ratio = min(1.0, summary_chars / total_chars) if total_chars else 0.0
        try:
            enrichment = await client.summarize(
                filename=filename, relative_path=relative_path, text=joined,
                source_created_at=None, source_modified_at=None, coverage=coverage,
            )
        except Exception:  # noqa: BLE001 - a failed summary must not lose the extraction
            enrichment = _fallback_enrichment(filename, ("Summary pass failed for this object.",))

    # Chunk shards were written during the stream, so the document's enrichment is NOT
    # back-filled into them: the document row is the authority for title, type, date and
    # summary, and `search.py` reads those from the document join.
    source = SourceMetadata(
        relative_path=relative_path, filename=filename, extension=extension,
        byte_size=byte_size, created_at=None, modified_at=None, modified_ns=0,
        content_sha256=identity,
    )
    write_document_row(
        output_dir, document_id=document_id, version_id=version_id, artifact=artifact,
        table=document_row_table({
            "document_id": document_id, "version_id": version_id, "artifact_id": artifact,
            "source_id": source_id, "relative_path": source.relative_path,
            "vault_key": vault_key, "resolution": resolution, "member_path": "",
            "filename": filename, "extension": extension, "media_type": outcome.media_type,
            "byte_size": byte_size, "content_sha256": identity,
            "source_created_at": None, "source_modified_at": None, "indexed_at": now,
            "title": enrichment.title or filename, "document_type": enrichment.document_type,
            "document_date": enrichment.document_date, "date_basis": enrichment.date_basis,
            "short_summary": enrichment.short_summary,
            "detailed_summary": enrichment.detailed_summary,
            "people": enrichment.people, "organizations": enrichment.organizations,
            "locations": enrichment.locations, "dates_mentioned": enrichment.dates_mentioned,
            "topics": enrichment.topics, "keywords": enrichment.keywords,
            "case_relevance": enrichment.case_relevance, "language": enrichment.language,
            "confidence": enrichment.confidence, "review_notes": enrichment.review_notes,
            "review_state": "unreviewed", "record_role": "machine_proposal",
            "index_status": outcome.status, "extraction_method": outcome.method,
            "extraction_notes": list(outcome.notes), "page_count": outcome.page_count,
            "text_char_count": total_chars, "chunk_count": accumulator.count,
            "summary_coverage": coverage, "summary_coverage_ratio": coverage_ratio,
            "summary_model": summary_model if summary_enabled else "",
            "embedding_model": embed_model if embed_enabled else "",
            "embedding_dimensions": embed_dimensions, "schema_version": SCHEMA_VERSION,
        }),
    )
    status = coco.use_context(RUN_STATUS)
    status.files_transformed += 1
    if outcome.status != "indexed":
        status.files_without_usable_text += 1
    if status.files_transformed % 25 == 0:
        status.save(output_dir, "running")


@coco.fn
async def app_main(
    sourcedir: Path,
    output_dir: Path,
    source_id: str,
    chunk_size: int,
    chunk_overlap: int,
    chunk_flush_size: int,
    summary_max_chars: int,
    embed_batch_size: int,
    embed_model: str,
    summary_model: str,
    embed_dimensions: int,
    embed_enabled: bool,
    summary_enabled: bool,
    weaviate_target: tuple[str, str, str] | None,
    source_mode: str,
    catalog_query_file: Path,
    catalog_limit: int,
    catalog_path_prefix: str,
) -> None:
    async def filesystem_items():
        patterns = [f"**/*{extension}" for extension in SUPPORTED_EXTENSIONS]
        files = localfs.walk_dir(
            sourcedir,
            recursive=True,
            path_matcher=PatternFilePathMatcher(
                included_patterns=patterns,
                excluded_patterns=[f"**/{segment}/**" for segment in sorted(_EXCLUDED_SEGMENTS)],
            ),
            live=False,
        )
        status = coco.use_context(RUN_STATUS)
        async for key, file in files.items():
            status.files_observed += 1
            yield key, LocalStreamFile(file.file_path)

    async def catalog_items():
        status = coco.use_context(RUN_STATUS)
        dsn = coco.use_context(CATALOG_DSN)
        query = catalog_query_file.read_text(encoding="utf-8")
        taken = 0
        async for obj in iter_catalog_objects(dsn, query):
            if catalog_path_prefix and not obj.key.startswith(catalog_path_prefix):
                continue
            if not _catalog_key_is_indexable(obj.key):
                continue
            status.files_observed += 1
            yield obj.key, VaultFile(obj)
            taken += 1
            if catalog_limit and taken >= catalog_limit:
                break

    handle = await coco.mount_each(
        process_file,
        catalog_items() if source_mode == "catalog" else filesystem_items(),
        source_id=source_id,
        output_dir=output_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_flush_size=chunk_flush_size,
        summary_max_chars=summary_max_chars,
        embed_batch_size=embed_batch_size,
        embed_model=embed_model,
        summary_model=summary_model,
        embed_dimensions=embed_dimensions,
        embed_enabled=embed_enabled,
        summary_enabled=summary_enabled,
        weaviate_target=weaviate_target,
    )
    await handle.ready()


_settings = Settings.from_env().resolved()
_settings.validate(require_source=False)


def _weaviate_target_from_env() -> tuple[str, str, str] | None:
    """Weaviate is the default vector target when a collection is configured.

    Owner ruling (audit item I-6, 2026-09-22): Weaviate on by default, not opt-in.
    ``INTAKE_WEAVIATE_INDEX_ENABLED=0`` still turns it off explicitly.
    """
    collection = os.getenv("INTAKE_WEAVIATE_COLLECTION", "").strip()
    enabled = os.getenv("INTAKE_WEAVIATE_INDEX_ENABLED", "1" if collection else "0")
    if enabled != "1" or not collection:
        return None
    return (
        os.getenv("INTAKE_WEAVIATE_URL", "").strip(),
        collection,
        os.getenv("INTAKE_WEAVIATE_TEXT_VECTOR", "text_vector").strip(),
    )


_weaviate_target = _weaviate_target_from_env()
_EMBED_ENABLED = os.getenv("INTAKE_EMBED_MODE", "on").strip().casefold() != "deferred"
_SUMMARY_ENABLED = os.getenv("INTAKE_SUMMARY_MODE", "on").strip().casefold() == "on"


@asynccontextmanager
async def resources_lifespan(builder: coco.EnvironmentBuilder) -> AsyncIterator[None]:
    _settings.output_dir.mkdir(parents=True, exist_ok=True)
    _settings.state_dir.mkdir(parents=True, exist_ok=True)
    builder.settings.db_path = _settings.state_dir / "cocoindex.db"
    async with AsyncExitStack() as stack:
        if _settings.source_mode == "catalog":
            catalog_dsn = get_secret("INTAKE_CATALOG_DSN")
            if not catalog_dsn:
                raise ValueError("INTAKE_SOURCE_MODE=catalog needs INTAKE_CATALOG_DSN")
            builder.provide(CATALOG_DSN, catalog_dsn)
            credentials = configured_credentials(_settings.object_store_scheme)
            store_client = await stack.enter_async_context(
                httpx.AsyncClient(timeout=120.0, follow_redirects=False)
            )
            builder.provide(OBJECT_STORE, ObjectStore(
                credentials, _settings.vault_bucket, store_client, counters=READ_COUNTERS,
            ))
        api_key = get_secret("NVIDIA_API_KEY")
        if not api_key and (_EMBED_ENABLED or _SUMMARY_ENABLED):
            raise ValueError("NVIDIA_API_KEY is not configured; set INTAKE_EMBED_MODE=deferred")
        client = await stack.enter_async_context(NimClient(
            api_key=api_key or "unset",
            base_url=_settings.nim_base_url,
            embed_model=_settings.embed_model,
            summary_model=_settings.summary_model,
            dimensions=_settings.embed_dimensions,
            timeout_seconds=_settings.timeout_seconds,
            max_retries=_settings.max_retries,
            max_concurrency=_settings.max_concurrency,
        ))
        builder.provide(NIM_CLIENT, client)
        if _weaviate_target is not None:
            origin, collection, target_vector = _weaviate_target
            target_config = WeaviateSearchConfig(
                url=origin, collection=collection, target_vector=target_vector,
                dimensions=_settings.embed_dimensions,
                api_key=get_secret("INTAKE_WEAVIATE_API_KEY") or "",
            )
            # Validate at startup, loudly, not on the first query (audit note 2026-09-22).
            target_config.validate()
            declared = os.getenv("INTAKE_WEAVIATE_EMBED_MODEL", _settings.embed_model)
            if declared != _settings.embed_model:
                raise ValueError("Filesystem Weaviate embedding model must match NIM")
            headers = {"Authorization": f"Bearer {target_config.api_key}"} \
                if target_config.api_key else {}
            http_client = await stack.enter_async_context(httpx.AsyncClient(
                headers=headers, timeout=20.0, follow_redirects=False,
            ))
            writer = WeaviateObjectWriter(target_config, http_client)
            await writer.verify_schema()
            builder.provide(WEAVIATE_WRITER, writer)
        yield


READ_COUNTERS = ReadCounters()


@coco.lifespan
async def coco_lifespan(builder: coco.EnvironmentBuilder) -> AsyncIterator[None]:
    with source_lock(_settings.lock_dir, _settings.source_id):
        status = RunStatus(_settings.source_id, str(_settings.source_dir))
        builder.provide(RUN_STATUS, status)

        async def observe_failure(exc: BaseException, context: coco.ExceptionContext) -> None:
            status.failure_events += 1
            if status.failure_events == 1 or status.failure_events % 25 == 0:
                status.save(_settings.output_dir, "running_with_errors")

        builder.set_exception_handler(observe_failure)
        status.save(_settings.output_dir, "running")
        state = "finished"
        try:
            async with resources_lifespan(builder):
                yield
        except BaseException:
            state = "failed_or_interrupted"
            raise
        finally:
            if state == "finished" and status.failure_events:
                state = "finished_with_errors"
            status.save(_settings.output_dir, state)


app = coco.App(
    coco.AppConfig(
        name="IntakeFilesystem_" + hashlib.sha256(_settings.source_id.encode()).hexdigest()[:16],
        max_inflight_components=_settings.max_inflight_files,
    ),
    app_main,
    sourcedir=_settings.source_dir,
    output_dir=_settings.output_dir,
    source_id=_settings.source_id,
    chunk_size=_settings.chunk_size,
    chunk_overlap=_settings.chunk_overlap,
    chunk_flush_size=_settings.chunk_flush_size,
    summary_max_chars=_settings.summary_max_chars,
    embed_batch_size=_settings.embed_batch_size,
    embed_model=_settings.embed_model,
    summary_model=_settings.summary_model,
    embed_dimensions=_settings.embed_dimensions,
    embed_enabled=_EMBED_ENABLED,
    summary_enabled=_SUMMARY_ENABLED,
    weaviate_target=_weaviate_target,
    source_mode=_settings.source_mode,
    catalog_query_file=_settings.catalog_query_file,
    catalog_limit=_settings.catalog_limit,
    catalog_path_prefix=_settings.catalog_path_prefix,
)
