"""Read-only search over the Intake image collection (single vector, MaxSim, OCR keywords).

> _Byline: Claude Code · Fable 5.1 · 2026-09-22_
Owner 2026-09-22: the image index is wired into Intake search. This lane runs beside the
text lane in /filesystem/search when INTAKE_IMAGES_* is configured. Hybrid mode: the
question is embedded with the same hosted embedders the index used; MaxSim scores the
screenshots' Jina bag, the single vector scores everything, and the OCR fallback text is
matched by keyword. Keyword mode uses only the OCR text. Nothing is written.
"""

from __future__ import annotations

import json
import math
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel

from .image_embedders import ImageEmbedders
from .image_target import MULTI_VECTOR, SINGLE_VECTOR

_FIELDS = (
    "source_id source_path filename content_sha256 original_time original_time_source "
    "original_time_confidence original_time_conflict device software gps is_screenshot "
    "ocr_text _additional { id distance score }"
)


class ImageHit(BaseModel):
    object_id: str
    source_id: str
    source_path: str
    filename: str
    content_sha256: str
    original_time: str
    original_time_source: str
    original_time_confidence: str
    original_time_conflict: bool
    device: str
    software: str
    gps: str
    is_screenshot: bool
    ocr_excerpt: str
    matched_by: str  # maxsim | single | ocr_keyword
    score: float


class ImageSearchError(RuntimeError):
    pass


def _validate_origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Invalid image Weaviate URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Weaviate URL must not contain credentials, query, or fragment")
    return url.rstrip("/")


class WeaviateImageSearcher:
    def __init__(self, url: str, collection: str, api_key: str = "", timeout: float = 30.0):
        if not collection.isidentifier() or not collection[0].isupper():
            raise ValueError("Explicit valid image collection name required")
        self.url = _validate_origin(url)
        self.collection = collection
        self.api_key = api_key
        self.timeout = timeout

    async def _get(self, client: httpx.AsyncClient, operator: str, limit: int) -> list[dict]:
        query = (
            f"{{ Get {{ {self.collection}(limit: {limit}, {operator}, "
            'where: {path: ["active"], operator: Equal, valueBoolean: true}) { '
            f"{_FIELDS} }} }} }}"
        )
        response = await client.post(f"{self.url}/v1/graphql", json={"query": query})
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            raise ImageSearchError("Weaviate rejected the image query")
        rows = body["data"]["Get"][self.collection]
        if not isinstance(rows, list):
            raise ValueError("Missing result list")
        return rows

    async def search(
        self,
        query: str,
        *,
        limit: int,
        mode: str,
        embedders: ImageEmbedders | None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> list[ImageHit]:
        if not query.strip():
            raise ValueError("Search query must contain text")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        text = json.dumps(query, ensure_ascii=True)
        merged: dict[str, tuple[str, float, dict]] = {}

        def keep(row: dict, matched_by: str, score: float) -> None:
            if not math.isfinite(score):
                raise ValueError("Nonfinite score")
            object_id = row["_additional"]["id"]
            if object_id not in merged or merged[object_id][1] < score:
                merged[object_id] = (matched_by, score, row)

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, headers=headers, transport=transport, follow_redirects=False
            ) as client:
                for row in await self._get(
                    client, f'bm25: {{query: {text}, properties: ["ocr_text"]}}', limit
                ):
                    keep(row, "ocr_keyword", float(row["_additional"]["score"]))
                if mode == "hybrid":
                    if embedders is None:
                        raise ValueError("Image embedders are required for hybrid search")
                    single, multi = await embedders.embed_query(query)
                    lanes = [(SINGLE_VECTOR, single, "single")]
                    if multi is not None:
                        lanes.append((MULTI_VECTOR, multi, "maxsim"))
                    for target, vector, label in lanes:
                        near = (
                            f"nearVector: {{vector: {json.dumps(vector, allow_nan=False)}, "
                            f'targetVectors: ["{target}"]}}'
                        )
                        for row in await self._get(client, near, limit):
                            # MaxSim distances are negative sums; cosine distances are 0..2.
                            # Both are turned into "higher is better" on their own scale.
                            distance = float(row["_additional"]["distance"])
                            keep(row, label, -distance if label == "maxsim" else 1.0 - distance)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ImageSearchError("Image search service unavailable or incompatible") from exc

        hits = []
        for matched_by, score, row in merged.values():
            hits.append(
                ImageHit(
                    object_id=row["_additional"]["id"],
                    matched_by=matched_by,
                    score=round(score, 4),
                    ocr_excerpt=(row.get("ocr_text") or "")[:300],
                    **{
                        key: row[key]
                        for key in (
                            "source_id",
                            "source_path",
                            "filename",
                            "content_sha256",
                            "original_time",
                            "original_time_source",
                            "original_time_confidence",
                            "original_time_conflict",
                            "device",
                            "software",
                            "gps",
                            "is_screenshot",
                        )
                    },
                )
            )
        # Order: MaxSim hits first (they are the sharpest), then single-vector, then keyword-only.
        rank = {"maxsim": 0, "single": 1, "ocr_keyword": 2}
        hits.sort(key=lambda hit: (rank[hit.matched_by], -hit.score))
        return hits[:limit]
