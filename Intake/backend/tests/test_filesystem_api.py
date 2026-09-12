from pathlib import Path
from uuid import uuid4

import httpx
import pytest

import casebible_index.api as api_module
from casebible_index.config import Settings
from casebible_index.filesystem_search import (
    FilesystemHit,
    FilesystemSearchError,
    FilesystemSearchResponse,
)
from casebible_index.nim import NimError


@pytest.fixture
def api_settings():
    root = Path(__file__).resolve().parents[1]
    return Settings(
        source_dir=root / "sample_docs", source_id="api-synthetic",
        output_dir=root / "output" / "api-synthetic" / uuid4().hex,
        nim_base_url="https://nim.example/v1", embed_model="synthetic-embed",
        summary_model="synthetic-summary", embed_dimensions=3,
        chunk_size=100, chunk_overlap=10, summary_max_chars=1000,
        embed_batch_size=2, max_concurrency=1, timeout_seconds=2, max_retries=0,
    )


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("INTAKE_WEAVIATE_URL", "https://weaviate.example")
    monkeypatch.setenv("INTAKE_WEAVIATE_COLLECTION", "IntakeApiSynthetic")
    monkeypatch.setenv("INTAKE_WEAVIATE_TEXT_VECTOR", "text_nim")
    monkeypatch.setenv("INTAKE_WEAVIATE_EMBED_MODEL", "synthetic-embed")
    monkeypatch.setattr(api_module, "get_secret", lambda _: "synthetic-test-key")


def response_for(request):
    return FilesystemSearchResponse(
        query=request.query, collection="IntakeApiSynthetic", target_vector="text_nim",
        hits=[FilesystemHit(
            object_id="object-1", source_id="r2all/raw", source_path="V:\\raw\\note.txt",
            document_id="doc-1", chunk_id="chunk-1", filename="note.txt",
            text="Fictional scheduling note", score=0.82,
        )],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["meeting", "  meeting \t"])
async def test_keyword_api_preserves_results_without_embedding(
    configured, monkeypatch, api_settings, query,
):
    calls = []

    def forbidden_nim(**kwargs):
        pytest.fail("Keyword requests must not initialize NIM")

    async def search(self, request, *, vector=None):
        assert vector is None
        calls.append(request)
        result = response_for(request)
        result.target_vector = None
        return result

    monkeypatch.setattr(api_module, "NimClient", forbidden_nim)
    monkeypatch.setattr(api_module.WeaviateFilesystemSearcher, "search", search)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_module.create_api(api_settings)),
        base_url="http://test",
    ) as client:
        result = await client.post("/filesystem/search", json={
            "query": query, "mode": "keyword", "limit": 7,
        })
    assert result.status_code == 200
    assert calls[0].limit == 7
    body = result.json()
    assert body["query"] == query  # Native bridge validates exact request equality.
    assert body["coverage"] == "unknown"
    assert body["target_vector"] is None
    assert body["hits"][0]["source_path"] == "V:\\raw\\note.txt"
    assert body["hits"][0]["score"] == 0.82


@pytest.mark.asyncio
async def test_hybrid_api_uses_query_vector(configured, monkeypatch, api_settings):
    calls = []

    class FakeNim:
        def __init__(self, **kwargs):
            assert kwargs["dimensions"] == 3

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def embed_query(self, query):
            calls.append(query)
            return [1.0, 0.0, 0.0]

    async def search(self, request, *, vector=None):
        assert vector == [1.0, 0.0, 0.0]
        return response_for(request)

    monkeypatch.setattr(api_module, "NimClient", FakeNim)
    monkeypatch.setattr(api_module.WeaviateFilesystemSearcher, "search", search)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_module.create_api(api_settings)), base_url="http://test",
    ) as client:
        result = await client.post("/filesystem/search", json={"query": "meeting"})
    assert result.status_code == 200
    assert calls == ["meeting"]
    assert result.json()["target_vector"] == "text_nim"


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"query": "x", "limit": 0}, {"query": "x", "limit": 101}, {"query": ""},
    {"query": " "}, {"query": "x" * 4097}, {"query": "x", "mode": "unknown"},
])
async def test_bad_requests_fail_before_any_provider(
    configured, monkeypatch, api_settings, payload,
):
    def forbidden_secret(name):
        pytest.fail("Invalid requests must not reach provider setup")

    monkeypatch.setattr(api_module, "get_secret", forbidden_secret)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_module.create_api(api_settings)), base_url="http://test",
    ) as client:
        result = await client.post("/filesystem/search", json=payload)
    assert result.status_code == 422


@pytest.mark.asyncio
async def test_unconfigured_service_is_503(monkeypatch, api_settings):
    monkeypatch.delenv("INTAKE_WEAVIATE_URL", raising=False)
    monkeypatch.setattr(api_module, "get_secret", lambda _: None)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_module.create_api(api_settings)), base_url="http://test",
    ) as client:
        result = await client.post("/filesystem/search", json={"query": "x", "mode": "keyword"})
    assert result.status_code == 503
    assert "configuration" in result.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["model_mismatch", "missing_nim_key"])
async def test_hybrid_readiness_fails_before_embedding(
    configured, monkeypatch, api_settings, failure,
):
    def forbidden_nim(**kwargs):
        pytest.fail("Invalid readiness must not reach NIM")

    monkeypatch.setattr(api_module, "NimClient", forbidden_nim)
    if failure == "model_mismatch":
        monkeypatch.setenv("INTAKE_WEAVIATE_EMBED_MODEL", "different-model")
    else:
        monkeypatch.setattr(
            api_module, "get_secret",
            lambda name: None if name == "NVIDIA_API_KEY" else "synthetic",
        )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_module.create_api(api_settings)), base_url="http://test",
    ) as client:
        response = await client.post("/filesystem/search", json={"query": "meeting"})
    assert response.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [FilesystemSearchError("secret body"), NimError("secret body")])
async def test_provider_failures_are_sanitized(configured, monkeypatch, api_settings, error):
    async def failed(self, request, *, vector=None):
        raise error

    monkeypatch.setattr(api_module.WeaviateFilesystemSearcher, "search", failed)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_module.create_api(api_settings)), base_url="http://test",
    ) as client:
        result = await client.post("/filesystem/search", json={"query": "x", "mode": "keyword"})
    assert result.status_code == 503
    assert "secret body" not in result.text


@pytest.mark.asyncio
async def test_status_missing_then_report_then_read_failure(monkeypatch, api_settings):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_module.create_api(api_settings)), base_url="http://test",
    ) as client:
        empty = await client.get("/filesystem/status")
        assert empty.json() == {"state": "never_reported", "coverage": "unknown"}
        report = {"state": "finished_with_errors", "coverage": "unknown", "failure_events": 2}
        monkeypatch.setattr(api_module, "latest_run_status", lambda _: report)
        observed = await client.get("/filesystem/status")
        assert observed.status_code == 200 and observed.json() == report

        def failed(_):
            raise OSError("sensitive storage path")

        monkeypatch.setattr(api_module, "latest_run_status", failed)
        error = await client.get("/filesystem/status")
        assert error.status_code == 503
        assert "sensitive storage" not in error.text
