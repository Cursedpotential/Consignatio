from __future__ import annotations

import json

import httpx
import pytest

from casebible_index.nim import NimClient, representative_excerpt


@pytest.mark.asyncio
async def test_nim_client_validates_embedding_and_summary_shapes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if request.url.path.endswith("/embeddings"):
            data = [
                {"index": index, "embedding": [float(index + 1), 0.0, 0.0]}
                for index, _ in enumerate(payload["input"])
            ]
            return httpx.Response(200, json={"data": data})
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "title": "Example",
                                    "document_type": "note",
                                    "short_summary": "Short.",
                                    "confidence": 0.9,
                                    "review_notes": "Synthetic source.",
                                }
                            )
                        },
                    }
                ]
            },
        )

    async with NimClient(
        api_key="test-key",
        base_url="https://example.test/v1",
        embed_model="embed",
        summary_model="summary",
        dimensions=3,
        timeout_seconds=2,
        max_retries=0,
        max_concurrency=2,
        transport=httpx.MockTransport(handler),
    ) as client:
        vectors = await client.embed_documents(["a", "b"], batch_size=2)
        assert vectors == [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
        summary = await client.summarize(
            filename="note.txt",
            relative_path="notes/note.txt",
            text="Example text",
            source_created_at=None,
            source_modified_at=None,
            coverage="full_text",
        )
        assert summary.title == "Example"
        assert summary.document_type == "note"
        assert summary.review_notes == ["Synthetic source."]


def test_representative_excerpt_discloses_partial_coverage() -> None:
    excerpt, coverage, ratio = representative_excerpt("x" * 300, 90)
    assert coverage == "representative_beginning_middle_end"
    assert "[BEGINNING]" in excerpt and "[MIDDLE]" in excerpt and "[END]" in excerpt
    assert 0 < ratio < 1
