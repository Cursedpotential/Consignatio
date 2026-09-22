"""Read-only Weaviate boundary for Intake, separate from evidence search.

Uses externally supplied query embeddings, never a server-side default vectorizer.
Collection population and coverage publication are separate indexing operations.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field, field_validator

from .image_search import ImageHit


class FilesystemSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4096)
    limit: int = Field(default=20, ge=1, le=100)
    mode: Literal["hybrid", "keyword"] = "hybrid"

    @field_validator("query")
    @classmethod
    def query_has_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Search query must contain text")
        return value


class FilesystemHit(BaseModel):
    object_id: str
    source_id: str
    source_path: str
    # The B2 object key and the catalog resolution, so a hit can be opened from the vault
    # rather than from a desktop path (Claude Code · Opus 5 · 2026-09-22; audit item I-8).
    vault_key: str = ""
    resolution: str = "unknown"
    document_id: str
    chunk_id: str
    filename: str
    text: str
    score: float


class FilesystemSearchResponse(BaseModel):
    query: str
    backend: str = "weaviate"
    collection: str
    target_vector: str | None
    coverage: str = "unknown"  # Successful query is not proof of complete indexing.
    hits: list[FilesystemHit]
    # Image lane (Claude Code · Fable 5.1 · 2026-09-22): empty when INTAKE_IMAGES_* is unset.
    image_collection: str | None = None
    image_hits: list[ImageHit] = Field(default_factory=list)


class FilesystemSearchError(RuntimeError):
    pass


@dataclass(frozen=True)
class WeaviateSearchConfig:
    url: str
    collection: str
    target_vector: str
    dimensions: int
    api_key: str = ""
    timeout_seconds: float = 20.0

    def validate(self) -> None:
        parsed = urlsplit(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Invalid filesystem Weaviate URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Weaviate URL must not contain credentials, query, or fragment")
        if parsed.path not in {"", "/"}:
            raise ValueError("Weaviate URL must be an origin without an API path")
        if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", self.collection):
            raise ValueError("Explicit valid filesystem collection name required")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.target_vector):
            raise ValueError("Explicit valid named vector required")
        if self.dimensions < 1 or not 0 < self.timeout_seconds <= 120:
            raise ValueError("Invalid vector dimensions or query timeout")


class WeaviateFilesystemSearcher:
    def __init__(self, config: WeaviateSearchConfig) -> None:
        config.validate()
        self.config = config

    async def search(
        self, request: FilesystemSearchRequest, *, vector: list[float] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> FilesystemSearchResponse:
        if not request.query.strip():
            raise ValueError("Search query must contain text")
        query_text = json.dumps(request.query, ensure_ascii=True)
        if request.mode == "hybrid":
            if vector is None or len(vector) != self.config.dimensions:
                raise ValueError("Query embedding dimension mismatch")
            if not all(math.isfinite(v) for v in vector) or not any(vector):
                raise ValueError("Query embedding must be finite and nonzero")
            operator = (
                f"hybrid: {{query: {query_text}, alpha: 0.7, "
                f"vector: {json.dumps(vector, allow_nan=False)}, "
                f"targetVectors: [{json.dumps(self.config.target_vector)}]}}"
            )
        else:
            operator = f"bm25: {{query: {query_text}}}"
        query = (
            f"{{ Get {{ {self.config.collection}(limit: {request.limit}, {operator}, "
            'where: {path: ["active"], operator: Equal, valueBoolean: true}) { '
            "source_id source_path vault_key resolution document_id chunk_id filename text "
            "_additional {id score}"
            " } } }"
        )
        headers = {"Authorization": f"Bearer {self.config.api_key}"} if self.config.api_key else {}
        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout_seconds, headers=headers, transport=transport,
                follow_redirects=False,
            ) as client:
                response = await client.post(
                    self.config.url.rstrip("/") + "/v1/graphql", json={"query": query}
                )
                response.raise_for_status()
                body = response.json()
            if body.get("errors"):
                raise FilesystemSearchError("Weaviate rejected the filesystem query")
            rows = body["data"]["Get"][self.config.collection]
            if not isinstance(rows, list):
                raise ValueError("Missing result list")
            hits = [FilesystemHit(
                object_id=row["_additional"]["id"],
                score=float(row["_additional"]["score"]),
                vault_key=row.get("vault_key") or "",
                resolution=row.get("resolution") or "unknown",
                **{key: row[key] for key in (
                    "source_id", "source_path", "document_id", "chunk_id", "filename", "text"
                )},
            ) for row in rows]
            if any(not math.isfinite(hit.score) for hit in hits):
                raise ValueError("Nonfinite score")
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            # Never return provider bodies, credentials, or corpus excerpts as error details.
            raise FilesystemSearchError(
                "Filesystem search service unavailable or incompatible"
            ) from exc
        return FilesystemSearchResponse(
            query=request.query, collection=self.config.collection,
            target_vector=self.config.target_vector if request.mode == "hybrid" else None,
            hits=hits[:request.limit],
        )
