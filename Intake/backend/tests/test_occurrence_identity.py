import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import cocoindex as coco
import httpx
import pytest

from casebible_index.filesystem_search import (
    FilesystemSearchRequest,
    WeaviateFilesystemSearcher,
    WeaviateSearchConfig,
)
from casebible_index.models import DocumentEnrichment, ExtractedText, SourceMetadata, TextChunk
from casebible_index.parquet_store import stable_document_id, tables_for_document
from casebible_index.pipeline import NIM_CLIENT, RUN_STATUS, BoundedLocalFile, process_file
from casebible_index.run_status import RunStatus
from casebible_index.source_runtime import resolve_source_alias
from casebible_index.weaviate_target import WEAVIATE_WRITER, WeaviateObjectWriter

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://identity.example"
COLLECTION = "IntakeIdentitySynthetic"


class FakeNim:
    async def summarize(self, **kwargs):
        return DocumentEnrichment(title="Synthetic", short_summary="Identity fixture")

    async def embed_documents(self, texts, *, batch_size):
        return [[1.0, 0.0, 0.0] for _ in texts]


@coco.fn
async def _index_one_fixture(source_dir: Path, source_id: str, output: Path):
    from cocoindex.connectors import localfs

    await process_file(
        BoundedLocalFile(localfs.FilePath(path=source_dir / "note.txt"), 4096),
        source_dir=source_dir, source_id=source_id, output_dir=output,
        chunk_size=2400, chunk_overlap=100, summary_max_chars=4096,
        embed_batch_size=1, embed_model="fake-embed", summary_model="fake-summary",
        embed_dimensions=3, max_file_bytes=4096, max_extracted_chars=4096,
        max_chunks_per_file=2, weaviate_target=(ORIGIN, COLLECTION, "text_nim"),
    )


@pytest.mark.asyncio
async def test_identical_bytes_in_distinct_stores_remain_searchable_occurrences():
    """Actual pipeline/IDs/Coco target, with only network and NIM execution faked."""
    fixture = Path(__file__).parent / "fixtures" / "occurrences"
    assert (fixture / "store-a" / "note.txt").read_bytes() == (
        fixture / "store-b" / "note.txt"
    ).read_bytes()
    output = ROOT / "output" / "synthetic-identity-tests" / uuid4().hex
    output.mkdir(parents=True)
    objects = {}

    def serve(request):
        if request.url.path == "/v1/graphql":
            return httpx.Response(200, json={"data": {"Get": {COLLECTION: [
                {**row["properties"], "_additional": {"id": key, "score": "1.0"}}
                for key, row in objects.items()
            ]}}})
        if request.method == "GET":
            key = request.url.path.rsplit("/", 1)[-1]
            return httpx.Response(200, json=objects[key]) if key in objects else httpx.Response(404)
        assert request.method in {"POST", "PUT"}
        body = json.loads(request.content)
        objects[body["id"]] = body
        return httpx.Response(200, json=body)

    config = WeaviateSearchConfig(ORIGIN, COLLECTION, "text_nim", 3)
    transport = httpx.MockTransport(serve)
    async with httpx.AsyncClient(transport=transport) as client:
        context = coco.ContextProvider()
        context.provide(NIM_CLIENT, FakeNim())
        context.provide(RUN_STATUS, RunStatus("identity-test", str(fixture)))
        context.provide(WEAVIATE_WRITER, WeaviateObjectWriter(config, client))
        environment = coco.Environment(
            coco.Settings(db_path=output / "state", lmdb_map_size=16 * 1024 * 1024),
            context_provider=context, name="identity_" + uuid4().hex,
        )
        apps = []
        for source_id in ("store-a", "store-b"):
            app = coco.App(
                coco.AppConfig(name=source_id, environment=environment, max_inflight_components=1),
                _index_one_fixture, source_dir=fixture / source_id, source_id=source_id,
                output=output / source_id,
            )
            apps.append(app)
            await app.update()
        hits = (await WeaviateFilesystemSearcher(config).search(
            FilesystemSearchRequest(query="Synthetic occurrence", mode="keyword"),
            transport=transport,
        )).hits
    assert len(objects) == len(hits) == 2
    assert {hit.source_id for hit in hits} == {"store-a", "store-b"}
    assert len({hit.object_id for hit in hits}) == 2
    assert len({hit.document_id for hit in hits}) == 2
    assert len({hit.chunk_id for hit in hits}) == 2
    assert {hit.source_path for hit in hits} == {
        str((fixture / name / "note.txt").resolve()) for name in ("store-a", "store-b")
    }
    assert len({hit.text for hit in hits}) == 1


def test_alias_identity_converges_and_distinct_store_identity_does_not():
    registry = ROOT / "source-registry.example.json"
    first_path, first_id = resolve_source_alias(Path("V:/raw"), "casebible", registry)
    second_path, second_id = resolve_source_alias(Path("Y:/raw"), "casebible", registry)
    assert first_path == second_path
    assert stable_document_id(first_id, "note.txt") == stable_document_id(second_id, "note.txt")
    assert stable_document_id("independent-store", "note.txt") != stable_document_id(
        first_id, "note.txt"
    )


def test_equal_hashes_timestamps_paths_and_vectors_do_not_collapse_store_identity():
    stamp = datetime(2026, 1, 1, tzinfo=UTC)
    source = SourceMetadata(
        relative_path="note.txt", filename="note.txt", extension=".txt", byte_size=4,
        created_at=stamp, modified_at=stamp, modified_ns=1000, content_sha256="a" * 64,
    )
    versions, artifacts, rows = [], [], []
    for identity in ("store-a", "store-b"):
        version, artifact, _, chunks = tables_for_document(
            source_id=identity, source=source,
            extracted=ExtractedText("same", "text/plain", None, "synthetic", "indexed"),
            enrichment=DocumentEnrichment(title="Same"),
            chunks=[TextChunk(0, 0, 4, "same")], embeddings=[[1.0, 0.0, 0.0]],
            coverage="full_text", coverage_ratio=1.0, embed_model="fake-embed",
            summary_model="fake-summary", dimensions=3, indexed_at=stamp,
        )
        versions.append(version)
        artifacts.append(artifact)
        rows.append(chunks.to_pylist()[0])
    assert versions[0] != versions[1]
    assert artifacts[0] == artifacts[1]  # Shared content fingerprint is not occurrence identity.
    assert rows[0]["document_id"] != rows[1]["document_id"]
    assert rows[0]["chunk_id"] != rows[1]["chunk_id"]
