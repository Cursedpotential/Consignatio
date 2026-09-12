from __future__ import annotations

import asyncio
import json
import random
import re
from collections.abc import Sequence
from datetime import datetime
from typing import Any

import httpx

from .models import DocumentEnrichment

TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class NimError(RuntimeError):
    pass


class NimClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        embed_model: str,
        summary_model: str,
        dimensions: int,
        timeout_seconds: float,
        max_retries: int,
        max_concurrency: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("NVIDIA_API_KEY is required")
        self.embed_model = embed_model
        self.summary_model = summary_model
        self.dimensions = dimensions
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(timeout_seconds),
            transport=transport,
        )

    async def __aenter__(self) -> NimClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with self._semaphore:
                    response = await self._client.post(path, json=payload)
                if response.status_code in TRANSIENT_STATUS and attempt < self.max_retries:
                    retry_after = response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after else min(12.0, 0.75 * (2**attempt))
                    await asyncio.sleep(delay + random.random() * 0.25)
                    continue
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                status = (
                    exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
                )
                if attempt >= self.max_retries or (
                    status is not None and status not in TRANSIENT_STATUS
                ):
                    break
                await asyncio.sleep(min(12.0, 0.75 * (2**attempt)) + random.random() * 0.25)
        detail = str(last_error)[:500] if last_error else "unknown NIM error"
        raise NimError(f"NVIDIA NIM request failed after retries: {detail}") from last_error

    async def embed(self, texts: Sequence[str], *, input_type: str) -> list[list[float]]:
        if not texts:
            return []
        body = await self._post(
            "/embeddings",
            {
                "model": self.embed_model,
                "input": list(texts),
                "input_type": input_type,
                "encoding_format": "float",
                "truncate": "END",
            },
        )
        data = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
        vectors = [item.get("embedding", []) for item in data]
        if len(vectors) != len(texts):
            raise NimError(f"Expected {len(texts)} embeddings, received {len(vectors)}")
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise NimError(
                    f"Embedding dimension mismatch: expected {self.dimensions}, got {len(vector)}"
                )
        return [[float(value) for value in vector] for vector in vectors]

    async def embed_documents(self, texts: Sequence[str], *, batch_size: int) -> list[list[float]]:
        batches = [texts[index : index + batch_size] for index in range(0, len(texts), batch_size)]
        results = await asyncio.gather(
            *(self.embed(batch, input_type="passage") for batch in batches)
        )
        return [vector for batch in results for vector in batch]

    async def embed_query(self, query: str) -> list[float]:
        return (await self.embed([query], input_type="query"))[0]

    async def summarize(
        self,
        *,
        filename: str,
        relative_path: str,
        text: str,
        source_created_at: datetime | None,
        source_modified_at: datetime | None,
        coverage: str,
    ) -> DocumentEnrichment:
        system = """You create reviewable metadata for a private case-document index.
Return only a JSON object. Use only facts explicit in the supplied text or file metadata.
Never infer guilt, diagnosis, intent, identity, or legal conclusions. Unknown values must be
empty strings, empty arrays, null, or 'unknown'. document_date is ISO 8601 when supported.
document_type should be a short neutral label such as court_order, legal_filing,
correspondence, message_export, financial_record, report, note, timeline, or unknown.
short_summary must be at most 60 words. confidence is 0 through 1. review_notes must disclose
ambiguity or incomplete excerpt coverage. Required keys: title, document_type, document_date,
date_basis, short_summary, detailed_summary, people, organizations, locations,
dates_mentioned, topics, keywords, case_relevance, language, confidence, review_notes."""
        metadata = {
            "filename": filename,
            "relative_path": relative_path,
            "filesystem_created_at": source_created_at.isoformat() if source_created_at else None,
            "filesystem_modified_at": source_modified_at.isoformat()
            if source_modified_at
            else None,
            "summary_coverage": coverage,
        }
        body = await self._post(
            "/chat/completions",
            {
                "model": self.summary_model,
                "messages": [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": "File metadata:\n"
                        + json.dumps(metadata, ensure_ascii=False)
                        + "\n\nDocument text:\n"
                        + text,
                    },
                ],
                "temperature": 0,
                "max_tokens": 1600,
                "response_format": {"type": "json_object"},
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )
        try:
            choice = body["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise NimError(f"Summary did not finish cleanly: {choice.get('finish_reason')}")
            content = choice["message"].get("content") or ""
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
            return DocumentEnrichment.model_validate_json(content)
        except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
            raise NimError("NIM summary was not valid schema-conformant JSON") from exc


def representative_excerpt(text: str, max_chars: int) -> tuple[str, str, float]:
    if len(text) <= max_chars:
        return text, "full_text", 1.0
    slice_size = max_chars // 3
    middle_start = max(0, len(text) // 2 - slice_size // 2)
    excerpts = [
        "[BEGINNING]\n" + text[:slice_size],
        "[MIDDLE]\n" + text[middle_start : middle_start + slice_size],
        "[END]\n" + text[-slice_size:],
    ]
    selected = "\n\n".join(excerpts)
    return selected, "representative_beginning_middle_end", min(1.0, len(selected) / len(text))
