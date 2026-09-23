from __future__ import annotations

import hashlib
import json
import os
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import cocoindex as coco
import httpx
from cocoindex.connectors import localfs
from cocoindex.ops.text import RecursiveSplitter
from cocoindex.resources.file import FileLike, PatternFilePathMatcher

from .catalog_source import CatalogObject, iter_catalog_objects, safe_relative_key
from .config import SUPPORTED_EXTENSIONS, Settings
from .extractors import extract_text
from .filesystem_search import WeaviateSearchConfig
from .models import DocumentEnrichment, SourceMetadata, TextChunk
from .nim import NimClient, representative_excerpt
from .parquet_store import stable_document_id, tables_for_document, write_document_bundle
from .run_status import RunStatus
from .secrets import get_secret
from .source_runtime import source_lock
from .weaviate_target import WEAVIATE_WRITER, ObjectSpec, WeaviateObjectWriter, declare_chunk

NIM_CLIENT = coco.ContextKey[NimClient]("casebible_nim_client")
RUN_STATUS = coco.ContextKey[RunStatus]("intake_filesystem_run_status")
CATALOG_DSN = coco.ContextKey[str]("intake_catalog_dsn")
_splitter = RecursiveSplitter()
_EXCLUDED_SEGMENTS = frozenset({".git", ".review_hold", "to_be_deleted", "__pycache__"})


class BoundedLocalFile(localfs.File):
    """Apply the read cap to CocoIndex's fingerprint reads as well as processing."""

    def __init__(self, file_path, max_bytes: int):
        super().__init__(file_path)
        self.max_bytes = max_bytes

    async def _read_impl(self, size: int = -1) -> bytes:
        if await self.size() > self.max_bytes:
            raise ValueError("File exceeds INTAKE_MAX_FILE_BYTES before fingerprint/read")
        read_size = self.max_bytes + 1 if size < 0 else min(size, self.max_bytes + 1)
        content = await super()._read_impl(read_size)
        if len(content) > self.max_bytes:
            raise ValueError("File grew beyond INTAKE_MAX_FILE_BYTES before fingerprint/read")
        return content

    def __coco_memo_key__(self):
        return (super().__coco_memo_key__(), self.max_bytes)


class CatalogFile(BoundedLocalFile):
    """A catalog object on the mounted bucket (Byline: Claude Code · Opus 5 · 2026-09-18).

    Change detection uses the catalog's size + SHA-1 and never reads or stats the object:
    the hashing is already in the catalog (owner 2026-09-18 21:57; catalog decision
    2026-09-16). Bytes are read only when the object is actually processed.
    """

    def __init__(self, file_path, max_bytes: int, catalog_object: CatalogObject):
        super().__init__(file_path, max_bytes)
        self.catalog_object = catalog_object

    async def __coco_memo_state__(self, prev_state):
        # B2 large files have no SHA-1; for those only a size change is detectable here.
        state = ("catalog-v1", self.catalog_object.byte_size, self.catalog_object.sha1)
        return coco.MemoStateOutcome(state=state, memo_valid=prev_state == state)


def _catalog_key_is_indexable(key: str) -> bool:
    path = safe_relative_key(key)
    if path is None or _EXCLUDED_SEGMENTS.intersection(path.parts):
        return False
    return path.suffix.casefold() in SUPPORTED_EXTENSIONS


async def read_bounded(file: FileLike, max_bytes: int) -> bytes:
    """Reject oversized metadata before I/O; cap the actual read against growth races."""
    if await file.size() > max_bytes:
        raise ValueError("File exceeds INTAKE_MAX_FILE_BYTES; source left unchanged")
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError("File grew beyond INTAKE_MAX_FILE_BYTES; source left unchanged")
    return content


def _utc_timestamp(value: float | None) -> datetime | None:
    return datetime.fromtimestamp(value, tz=UTC) if value is not None else None


def _fallback_enrichment(filename: str, notes: tuple[str, ...]) -> DocumentEnrichment:
    return DocumentEnrichment(
        title=filename,
        document_type="unknown",
        short_summary="No usable text was available for summarization.",
        confidence=0.0,
        review_notes=list(notes),
    )


@coco.fn(memo=True)
async def process_file(
    file: FileLike,
    *,
    source_dir: Path,
    source_id: str,
    output_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
    summary_max_chars: int,
    embed_batch_size: int,
    embed_model: str,
    summary_model: str,
    embed_dimensions: int,
    max_file_bytes: int,
    max_extracted_chars: int,
    max_chunks_per_file: int,
    weaviate_target: tuple[str, str, str] | None,
) -> None:
    content = await read_bounded(file, max_file_bytes)
    source_path = file.file_path.resolve()
    relative_path = source_path.relative_to(source_dir.resolve()).as_posix()
    stat = source_path.stat()
    source = SourceMetadata(
        relative_path=relative_path,
        filename=source_path.name,
        extension=source_path.suffix.casefold(),
        byte_size=len(content),
        created_at=_utc_timestamp(getattr(stat, "st_birthtime", stat.st_ctime)),
        modified_at=_utc_timestamp(stat.st_mtime),
        modified_ns=stat.st_mtime_ns,
        content_sha256=hashlib.sha256(content).hexdigest(),
    )
    extracted = extract_text(source_path, content)
    if len(extracted.text) > max_extracted_chars:
        raise ValueError("Extracted text exceeds INTAKE_MAX_EXTRACTED_CHARS")
    chunks: list[TextChunk] = []
    embeddings: list[list[float]] = []
    coverage = "no_text"
    coverage_ratio = 0.0

    if extracted.status == "indexed":
        summary_text, coverage, coverage_ratio = representative_excerpt(
            extracted.text, summary_max_chars
        )
        client = coco.use_context(NIM_CLIENT)
        enrichment = await client.summarize(
            filename=source.filename,
            relative_path=source.relative_path,
            text=summary_text,
            source_created_at=source.created_at,
            source_modified_at=source.modified_at,
            coverage=coverage,
        )
        coco_chunks = _splitter.split(
            extracted.text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            language="markdown",
        )
        for index, chunk in enumerate(coco_chunks):
            if index >= max_chunks_per_file:
                raise ValueError("Chunk count exceeds INTAKE_MAX_CHUNKS_PER_FILE")
            chunks.append(TextChunk(
                ordinal=index,
                start=chunk.start.char_offset,
                end=chunk.end.char_offset,
                text=chunk.text,
            ))
        embeddings = await client.embed_documents(
            [chunk.text for chunk in chunks], batch_size=embed_batch_size
        )
    else:
        enrichment = _fallback_enrichment(source.filename, extracted.notes)

    version_id, artifact, document_table, chunk_table = tables_for_document(
        source_id=source_id,
        source=source,
        extracted=extracted,
        enrichment=enrichment,
        chunks=chunks,
        embeddings=embeddings,
        coverage=coverage,
        coverage_ratio=coverage_ratio,
        embed_model=embed_model,
        summary_model=summary_model,
        dimensions=embed_dimensions,
    )
    write_document_bundle(
        output_dir,
        document_id=stable_document_id(source_id, source.relative_path),
        version_id=version_id,
        artifact=artifact,
        document_table=document_table,
        chunk_table=chunk_table,
    )
    if weaviate_target is not None:
        origin, collection, vector_name = weaviate_target
        # Per-file cap also bounds this conversion, not the entire corpus.
        for row in chunk_table.to_pylist():
            declare_chunk(origin, collection, row["chunk_id"], ObjectSpec(
                properties={
                    "source_id": source_id, "source_path": str(source_path),
                    "document_id": row["document_id"], "chunk_id": row["chunk_id"],
                    "filename": source.filename, "text": row["text"],
                    "embed_model": embed_model,
                },
                vectors={vector_name: row["embedding"]},
            ))
    status = coco.use_context(RUN_STATUS)
    status.files_transformed += 1
    if extracted.status != "indexed":
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
    summary_max_chars: int,
    embed_batch_size: int,
    embed_model: str,
    summary_model: str,
    embed_dimensions: int,
    max_file_bytes: int,
    max_extracted_chars: int,
    max_chunks_per_file: int,
    weaviate_target: tuple[str, str, str] | None,
    source_mode: str,
    catalog_query_file: Path,
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
            yield key, BoundedLocalFile(file.file_path, max_file_bytes)

    async def catalog_items():
        # The object list comes from the catalog, not a walk; objects are read in place
        # under sourcedir (the mounted bucket root) only when processed.
        status = coco.use_context(RUN_STATUS)
        dsn = coco.use_context(CATALOG_DSN)
        query = catalog_query_file.read_text(encoding="utf-8")
        async for obj in iter_catalog_objects(dsn, query):
            if not _catalog_key_is_indexable(obj.key):
                continue
            status.files_observed += 1
            yield obj.key, CatalogFile(localfs.FilePath(sourcedir / obj.key), max_file_bytes, obj)

    handle = await coco.mount_each(
        process_file,
        catalog_items() if source_mode == "catalog" else filesystem_items(),
        source_dir=sourcedir,
        source_id=source_id,
        output_dir=output_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        summary_max_chars=summary_max_chars,
        embed_batch_size=embed_batch_size,
        embed_model=embed_model,
        summary_model=summary_model,
        embed_dimensions=embed_dimensions,
        max_file_bytes=max_file_bytes,
        max_extracted_chars=max_extracted_chars,
        max_chunks_per_file=max_chunks_per_file,
        weaviate_target=weaviate_target,
    )
    await handle.ready()


_settings = Settings.from_env().resolved()
_settings.validate(require_source=False)
_weaviate_target = (
    os.getenv("INTAKE_WEAVIATE_URL", ""),
    os.getenv("INTAKE_WEAVIATE_COLLECTION", ""),
    os.getenv("INTAKE_WEAVIATE_TEXT_VECTOR", ""),
) if os.getenv("INTAKE_WEAVIATE_INDEX_ENABLED") == "1" else None


@asynccontextmanager
async def resources_lifespan(builder: coco.EnvironmentBuilder) -> AsyncIterator[None]:
    _settings.output_dir.mkdir(parents=True, exist_ok=True)
    _settings.state_dir.mkdir(parents=True, exist_ok=True)
    builder.settings.db_path = _settings.state_dir / "cocoindex.db"
    if _settings.source_mode == "catalog":
        catalog_dsn = get_secret("INTAKE_CATALOG_DSN")
        if not catalog_dsn:
            raise ValueError("INTAKE_SOURCE_MODE=catalog needs INTAKE_CATALOG_DSN")
        builder.provide(CATALOG_DSN, catalog_dsn)
    api_key = get_secret("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError(
            "NVIDIA_API_KEY is not configured in the process or Windows user environment"
        )
    async with NimClient(
        api_key=api_key,
        base_url=_settings.nim_base_url,
        embed_model=_settings.embed_model,
        summary_model=_settings.summary_model,
        dimensions=_settings.embed_dimensions,
        timeout_seconds=_settings.timeout_seconds,
        max_retries=_settings.max_retries,
        max_concurrency=_settings.max_concurrency,
    ) as client:
        builder.provide(NIM_CLIENT, client)
        async with AsyncExitStack() as stack:
            if _weaviate_target is not None:
                origin, collection, target_vector = _weaviate_target
                if os.getenv("INTAKE_WEAVIATE_EMBED_MODEL") != _settings.embed_model:
                    raise ValueError("Filesystem Weaviate embedding model must match NIM")
                target_config = WeaviateSearchConfig(
                    url=origin, collection=collection, target_vector=target_vector,
                    dimensions=_settings.embed_dimensions,
                    api_key=get_secret("INTAKE_WEAVIATE_API_KEY") or "",
                )
                target_config.validate()
                headers = {"Authorization": f"Bearer {target_config.api_key}"} \
                    if target_config.api_key else {}
                http_client = await stack.enter_async_context(httpx.AsyncClient(
                    headers=headers, timeout=20.0, follow_redirects=False,
                ))
                writer = WeaviateObjectWriter(target_config, http_client)
                await writer.verify_schema()
                builder.provide(WEAVIATE_WRITER, writer)
            yield


@coco.lifespan
async def coco_lifespan(builder: coco.EnvironmentBuilder) -> AsyncIterator[None]:
    # Held across runtime startup, fingerprinting, extraction and sink application.
    # This path also covers direct `cocoindex update main.py`, not just our CLI.
    with source_lock(_settings.lock_dir, _settings.source_id):
        status = RunStatus(_settings.source_id, str(_settings.source_dir))
        builder.provide(RUN_STATUS, status)

        async def observe_failure(exc: BaseException, context: coco.ExceptionContext) -> None:
            # Byline: Claude Code · Sonnet 5 · 2026-09-14 -- failure_events was a bare
            # counter with no retained detail, so a dead run left no way to explain
            # *why* files failed. Append one compact, path-scoped line per failure to
            # a diagnostics log beside the run status; never touches source bytes.
            status.failure_events += 1
            try:
                diagnostics_path = _settings.output_dir / "run-status" / "failure-diagnostics.jsonl"
                diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
                original = context.original_exception or exc
                with diagnostics_path.open("a", encoding="utf-8") as handle:
                    handle.write(
                        json.dumps(
                            {
                                "reported_at": datetime.now(UTC).isoformat(),
                                "stable_path": context.stable_path,
                                "processor_name": context.processor_name,
                                "source": context.source,
                                "exception_type": type(original).__name__,
                                "exception_message": str(original)[:2000],
                            }
                        )
                        + "\n"
                    )
            except OSError:
                pass
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
    summary_max_chars=_settings.summary_max_chars,
    embed_batch_size=_settings.embed_batch_size,
    embed_model=_settings.embed_model,
    summary_model=_settings.summary_model,
    embed_dimensions=_settings.embed_dimensions,
    max_file_bytes=_settings.max_file_bytes,
    max_extracted_chars=_settings.max_extracted_chars,
    max_chunks_per_file=_settings.max_chunks_per_file,
    weaviate_target=_weaviate_target,
    source_mode=_settings.source_mode,
    catalog_query_file=_settings.catalog_query_file,
)
