import json

import httpx
import pytest

from casebible_index.filesystem_search import (
    FilesystemSearchError,
    FilesystemSearchRequest,
    WeaviateFilesystemSearcher,
    WeaviateSearchConfig,
)


def config(**changes):
    return WeaviateSearchConfig(**{
        "url": "https://search.example", "collection": "IntakeTestChunks",
        "target_vector": "text_nim", "dimensions": 3, **changes,
    })


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["keyword", "hybrid"])
async def test_search_preserves_source_navigation_and_truthful_scores(mode):
    def handler(request):
        query = json.loads(request.content)["query"]
        assert request.url.path == "/v1/graphql"
        assert "limit: 20" in query
        assert ('targetVectors: ["text_nim"]' in query) == (mode == "hybrid")
        return httpx.Response(200, json={"data": {"Get": {"IntakeTestChunks": [{
            "source_id": "r2-raw", "source_path": "V:\\raw\\note.txt",
            "document_id": "doc-1", "chunk_id": "chunk-1", "filename": "note.txt",
            "text": "Matching excerpt", "_additional": {"id": "object-1", "score": "0.8"},
        }]}}})
    result = await WeaviateFilesystemSearcher(config()).search(
        FilesystemSearchRequest(query='a "quoted" query', mode=mode),
        vector=[1, 0, 0] if mode == "hybrid" else None,
        transport=httpx.MockTransport(handler),
    )
    assert result.coverage == "unknown"
    assert result.hits[0].source_path == "V:\\raw\\note.txt"
    assert result.hits[0].score == 0.8


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"errors": [{"message": "sensitive provider response"}]},
    {"data": {"Get": {"IntakeTestChunks": None}}},
    {"data": {}},
])
async def test_failure_is_not_empty_success_or_provider_leak(payload):
    with pytest.raises(FilesystemSearchError) as error:
        await WeaviateFilesystemSearcher(config()).search(
            FilesystemSearchRequest(query="test", mode="keyword"),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
        )
    assert "sensitive" not in str(error.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("vector", [[1], [0, 0, 0], [float("nan"), 0, 1]])
async def test_bad_vectors_fail_before_network(vector):
    with pytest.raises(ValueError):
        await WeaviateFilesystemSearcher(config()).search(
            FilesystemSearchRequest(query="test"), vector=vector,
        )


@pytest.mark.parametrize("changes", [
    {"collection": 'Bad) { dangerous'}, {"url": "https://key:secret@example.com"},
    {"target_vector": ""}, {"url": "file:///tmp/search"},
])
def test_invalid_configuration_rejected(changes):
    with pytest.raises(ValueError):
        WeaviateFilesystemSearcher(config(**changes))
