"""Hosted image embedders for the image index.

> _Byline: Claude Code · Fable 5.1 · 2026-09-21_
Owner decision 2026-09-21 (option C): a single vector for every image plus a Jina
multi-vector (MaxSim) for screenshots and documents. The single-vector provider is a
setting: `nim` (nvidia/llama-nemotron-embed-vl-1b-v2, 2048) or `google`
(gemini-embedding-2, 3072). Request shapes are the ones probed live on 2026-09-21;
see docs/PROPOSAL-2026-09-21-IMAGE-INDEX.md. Keys are read by the caller, never logged.
"""

from __future__ import annotations

import asyncio
import base64
import math
from dataclasses import dataclass

import httpx

JINA_MODEL = "jina-embeddings-v4"
NIM_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2"
GOOGLE_MODEL = "gemini-embedding-2"
SINGLE_DIMENSIONS = {"nim": 2048, "google": 3072}
MULTI_DIMENSIONS = 128

_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def mime_for(extension: str) -> str:
    try:
        return _MIME[extension.casefold()]
    except KeyError as exc:
        raise ValueError(f"No image MIME type for {extension or '<none>'}") from exc


def _finite(vector: list[float]) -> list[float]:
    if not vector or not all(math.isfinite(v) for v in vector) or not any(vector):
        raise ValueError("Embedder returned an empty, zero or non-finite vector")
    return vector


@dataclass
class ImageEmbedders:
    client: httpx.AsyncClient
    single_provider: str
    single_key: str
    jina_key: str | None
    max_retries: int = 4

    def __post_init__(self) -> None:
        if self.single_provider not in SINGLE_DIMENSIONS:
            raise ValueError("INTAKE_IMAGES_SINGLE_PROVIDER must be 'nim' or 'google'")
        self._gate = asyncio.Semaphore(2)

    @property
    def single_model(self) -> str:
        return NIM_MODEL if self.single_provider == "nim" else GOOGLE_MODEL

    async def _post(self, url: str, headers: dict[str, str], body: dict) -> dict:
        delay = 2.0
        for attempt in range(self.max_retries + 1):
            async with self._gate:
                response = await self.client.post(url, headers=headers, json=body)
            if response.status_code == 200:
                return response.json()
            # Rate limits and provider hiccups are retried; a rejected request is not.
            if (
                response.status_code not in {408, 429, 500, 502, 503, 504}
                or attempt == self.max_retries
            ):
                raise RuntimeError(f"Embedding provider returned HTTP {response.status_code}")
            await asyncio.sleep(delay)
            delay *= 2
        raise RuntimeError("Embedding provider retries exhausted")

    async def embed_single(self, content: bytes, extension: str) -> list[float]:
        encoded = base64.b64encode(content).decode()
        if self.single_provider == "nim":
            data = await self._post(
                "https://integrate.api.nvidia.com/v1/embeddings",
                {"Authorization": f"Bearer {self.single_key}"},
                {
                    "model": NIM_MODEL,
                    "input": [f"data:{mime_for(extension)};base64,{encoded}"],
                    "input_type": "passage",
                    "modality": ["image"],
                    "encoding_format": "float",
                },
            )
            return _finite(data["data"][0]["embedding"])
        data = await self._post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_MODEL}:embedContent",
            {"x-goog-api-key": self.single_key},
            {
                "content": {
                    "parts": [{"inline_data": {"mime_type": mime_for(extension), "data": encoded}}]
                }
            },
        )
        return _finite(data["embedding"]["values"])

    async def embed_multi(self, content: bytes) -> list[list[float]]:
        if not self.jina_key:
            raise ValueError("JINA_API_KEY is required for the MaxSim vector")
        data = await self._post(
            "https://api.jina.ai/v1/embeddings",
            {"Authorization": f"Bearer {self.jina_key}"},
            {
                "model": JINA_MODEL,
                "task": "retrieval.passage",
                "return_multivector": True,
                "input": [{"image": base64.b64encode(content).decode()}],
            },
        )
        vectors = data["data"][0]["embeddings"]
        if not vectors or any(len(v) != MULTI_DIMENSIONS for v in vectors):
            raise ValueError("Jina returned an unexpected multi-vector shape")
        return [_finite(v) for v in vectors]

    async def embed_query(self, text: str) -> tuple[list[float], list[list[float]] | None]:
        """Query vectors: the single vector, plus the MaxSim bag when Jina is configured."""
        if self.single_provider == "nim":
            data = await self._post(
                "https://integrate.api.nvidia.com/v1/embeddings",
                {"Authorization": f"Bearer {self.single_key}"},
                {
                    "model": NIM_MODEL,
                    "input": [text],
                    "input_type": "query",
                    "encoding_format": "float",
                },
            )
            single = _finite(data["data"][0]["embedding"])
        else:
            data = await self._post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_MODEL}:embedContent",
                {"x-goog-api-key": self.single_key},
                {"content": {"parts": [{"text": text}]}},
            )
            single = _finite(data["embedding"]["values"])
        if not self.jina_key:
            return single, None
        data = await self._post(
            "https://api.jina.ai/v1/embeddings",
            {"Authorization": f"Bearer {self.jina_key}"},
            {
                "model": JINA_MODEL,
                "task": "retrieval.query",
                "return_multivector": True,
                "input": [{"text": text}],
            },
        )
        return single, [_finite(v) for v in data["data"][0]["embeddings"]]
