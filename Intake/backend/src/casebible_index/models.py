from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DocumentEnrichment(BaseModel):
    title: str = ""
    document_type: str = "unknown"
    document_date: str | None = None
    date_basis: str = "unknown"
    short_summary: str = ""
    detailed_summary: str = ""
    people: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    dates_mentioned: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    case_relevance: str = ""
    language: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    review_notes: list[str] = Field(default_factory=list)

    @field_validator(
        "people",
        "organizations",
        "locations",
        "dates_mentioned",
        "topics",
        "keywords",
        "review_notes",
        mode="before",
    )
    @classmethod
    def clean_lists(cls, values: object) -> list[str]:
        if values is None:
            return []
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, (list, tuple, set)):
            raise ValueError("Expected a string or list of strings")
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            cleaned = str(value).strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                result.append(cleaned)
                seen.add(key)
        return result

    @field_validator("short_summary")
    @classmethod
    def limit_short_summary(cls, value: str) -> str:
        words = value.split()
        return value if len(words) <= 60 else " ".join(words[:60])


@dataclass(frozen=True)
class ExtractedText:
    text: str
    media_type: str
    page_count: int | None
    extraction_method: str
    status: Literal["indexed", "skipped_no_text", "unsupported"]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TextChunk:
    ordinal: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class SourceMetadata:
    relative_path: str
    filename: str
    extension: str
    byte_size: int
    created_at: datetime | None
    modified_at: datetime | None
    modified_ns: int
    content_sha256: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    document_type: str | None = None
    path_prefix: str | None = None
    hybrid: bool = True


class SearchHit(BaseModel):
    score: float
    semantic_score: float
    lexical_score: float
    document_id: str
    version_id: str
    chunk_id: str
    relative_path: str
    # Vault identity (Claude Code · Opus 5 · 2026-09-22; audit item I-8).
    vault_key: str = ""
    resolution: str = "unknown"
    filename: str
    document_type: str
    document_date: str | None
    title: str
    short_summary: str
    chunk_ordinal: int
    char_start: int
    char_end: int
    text: str


class SearchResponse(BaseModel):
    query: str
    model: str
    snapshot: str | None
    hits: list[SearchHit]
