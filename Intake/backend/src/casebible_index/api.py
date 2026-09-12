from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .config import Settings
from .filesystem_search import (
    FilesystemSearchError,
    FilesystemSearchRequest,
    FilesystemSearchResponse,
    WeaviateFilesystemSearcher,
    WeaviateSearchConfig,
)
from .models import SearchRequest, SearchResponse
from .nim import NimClient, NimError
from .run_status import latest_run_status
from .search import SemanticSearcher, list_documents
from .secrets import get_secret
from .snapshots import newest_snapshot


def create_api(settings: Settings | None = None) -> FastAPI:
    config = (settings or Settings.from_env()).resolved()
    config.validate(require_source=False)
    api = FastAPI(
        title="Case Bible Text Index",
        version="0.1.0",
        description="Review-only semantic search over derived Parquet artifacts.",
    )

    @api.get("/health")
    def health() -> dict[str, object]:
        snapshot = newest_snapshot(config.output_dir)
        return {
            "status": "ok" if snapshot else "not_indexed",
            "snapshot": str(snapshot) if snapshot else None,
            "source_bytes_mutable": False,
            "authority": "derived review projection",
        }

    @api.get("/documents")
    def documents(limit: int = 100) -> list[dict[str, object]]:
        return list_documents(config, limit=min(max(limit, 1), 1000))

    @api.get("/filesystem/status")
    def filesystem_status() -> dict:
        try:
            return latest_run_status(config.output_dir)
        except (OSError, ValueError):
            raise HTTPException(
                status_code=503, detail="Filesystem run status unavailable"
            ) from None

    @api.post("/filesystem/search", response_model=FilesystemSearchResponse)
    async def filesystem_search(request: FilesystemSearchRequest) -> FilesystemSearchResponse:
        """Search across indexed stores; never scan or mutate source paths."""
        try:
            search_config = WeaviateSearchConfig(
                url=os.getenv("INTAKE_WEAVIATE_URL", ""),
                collection=os.getenv("INTAKE_WEAVIATE_COLLECTION", ""),
                target_vector=os.getenv("INTAKE_WEAVIATE_TEXT_VECTOR", ""),
                dimensions=config.embed_dimensions,
                api_key=get_secret("INTAKE_WEAVIATE_API_KEY") or "",
            )
            searcher = WeaviateFilesystemSearcher(search_config)
            vector = None
            if request.mode == "hybrid":
                if os.getenv("INTAKE_WEAVIATE_EMBED_MODEL") != config.embed_model:
                    raise ValueError(
                        "Filesystem collection embedding model is not configured to match NIM"
                    )
                api_key = get_secret("NVIDIA_API_KEY")
                if not api_key:
                    raise ValueError("NVIDIA_API_KEY is not configured")
                async with NimClient(
                    api_key=api_key, base_url=config.nim_base_url,
                    embed_model=config.embed_model, summary_model=config.summary_model,
                    dimensions=config.embed_dimensions, timeout_seconds=config.timeout_seconds,
                    max_retries=config.max_retries, max_concurrency=config.max_concurrency,
                ) as client:
                    vector = await client.embed_query(request.query)
            return await searcher.search(request, vector=vector)
        except (FilesystemSearchError, NimError, ValueError) as exc:
            raise HTTPException(
                status_code=503,
                detail="Filesystem search unavailable; verify service and embedding configuration",
            ) from exc

    @api.post("/search", response_model=SearchResponse)
    async def search(request: SearchRequest) -> SearchResponse:
        api_key = get_secret("NVIDIA_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="NVIDIA_API_KEY is not configured")
        try:
            async with NimClient(
                api_key=api_key,
                base_url=config.nim_base_url,
                embed_model=config.embed_model,
                summary_model=config.summary_model,
                dimensions=config.embed_dimensions,
                timeout_seconds=config.timeout_seconds,
                max_retries=config.max_retries,
                max_concurrency=config.max_concurrency,
            ) as client:
                return await SemanticSearcher(config, client).search(
                    request.query,
                    limit=request.limit,
                    document_type=request.document_type,
                    path_prefix=request.path_prefix,
                    hybrid=request.hybrid,
                )
        except (FileNotFoundError, NimError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return api


app = create_api()
