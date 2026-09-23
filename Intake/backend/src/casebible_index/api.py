from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException

from .config import Settings
from .filesystem_search import (
    FilesystemSearchError,
    FilesystemSearchRequest,
    FilesystemSearchResponse,
    WeaviateFilesystemSearcher,
    WeaviateSearchConfig,
)
from .image_embedders import ImageEmbedders
from .image_search import ImageSearchError, WeaviateImageSearcher
from .models import SearchRequest, SearchResponse
from .nim import NimClient, NimError
from .projections.runtime import connect_graph
from .projections.surreal import GraphRecordRef
from .run_status import latest_run_status
from .search import DuckDbQueryError, SemanticSearcher, list_documents, lookup_document, run_lake_query
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

    # Byline: Claude Code · Sonnet 5 · 2026-09-14 -- native metadata panel backing
    # endpoint: real catalog/fingerprint row for one selected file, never a guess.
    @api.get("/filesystem/lookup")
    def filesystem_lookup(path: str) -> dict[str, object]:
        if not path or len(path) > 4096:
            raise HTTPException(status_code=422, detail="Invalid path")
        try:
            return lookup_document(config, path)
        except (OSError, ValueError):
            raise HTTPException(status_code=503, detail="Lookup unavailable") from None

    # Byline: Claude Code · Sonnet 5 · 2026-09-14 -- DuckDB SQL method for the
    # search surface, bounded to this backend's own `documents`/`chunks` views.
    @api.post("/filesystem/duckdb")
    def filesystem_duckdb(request: LakeQueryRequest) -> dict[str, object]:
        try:
            return run_lake_query(config, request.sql, limit=request.limit)
        except DuckDbQueryError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

    @api.get("/filesystem/graph/status")
    async def graph_status() -> dict:
        try:
            async with await connect_graph() as graph:
                version = await graph.verify_health_and_schema()
                return {"status": "ready", "version": version}
        except Exception:
            raise HTTPException(status_code=503, detail="Intake graph unavailable") from None

    @api.get("/filesystem/graph/neighbors/{table}/{key}")
    async def graph_neighbors(table: str, key: str, edge_limit: int = 50) -> dict:
        root = GraphRecordRef(table, key)
        try:
            root.validate()
            if not 1 <= edge_limit <= 100:
                raise ValueError("Invalid edge limit")
        except ValueError:
            raise HTTPException(
                status_code=422, detail="Invalid graph reference or limit"
            ) from None
        try:
            async with await connect_graph() as graph:
                result = await graph.graph_neighborhood(root, edge_limit=edge_limit)
                # SDK RecordIDs are explicitly serialized, not exposed as Python internals.
                from fastapi.encoders import jsonable_encoder
                from surrealdb import RecordID

                return jsonable_encoder(
                    {"root": result.root, "edges": result.edges},
                    custom_encoder={RecordID: str},
                )
        except Exception:
            raise HTTPException(status_code=503, detail="Intake graph unavailable") from None

    @api.get("/filesystem/graph/projections/{snapshot_key}")
    async def graph_projection(snapshot_key: str) -> dict:
        try:
            if len(snapshot_key) > 255:
                raise ValueError("Invalid snapshot key")
            async with await connect_graph() as graph:
                result = await graph.projection_summary(snapshot_key)
                from fastapi.encoders import jsonable_encoder
                from surrealdb import RecordID

                return jsonable_encoder(result, custom_encoder={RecordID: str})
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid projection key") from None
        except Exception:
            raise HTTPException(status_code=503, detail="Intake graph unavailable") from None

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
                    api_key=api_key,
                    base_url=config.nim_base_url,
                    embed_model=config.embed_model,
                    summary_model=config.summary_model,
                    dimensions=config.embed_dimensions,
                    timeout_seconds=config.timeout_seconds,
                    max_retries=config.max_retries,
                    max_concurrency=config.max_concurrency,
                ) as client:
                    vector = await client.embed_query(request.query)
            response = await searcher.search(request, vector=vector)
            return await _with_image_lane(request, response)
        except (FilesystemSearchError, ImageSearchError, NimError, ValueError) as exc:
            raise HTTPException(
                status_code=503,
                detail="Filesystem search unavailable; verify service and embedding configuration",
            ) from exc

    async def _with_image_lane(
        request: FilesystemSearchRequest, response: FilesystemSearchResponse
    ) -> FilesystemSearchResponse:
        """Add hits from the image index when it is configured (owner 2026-09-22: wired in)."""
        image_url = os.getenv("INTAKE_IMAGES_WEAVIATE_URL", "")
        if not image_url:
            return response
        collection = os.getenv("INTAKE_IMAGES_COLLECTION", "IntakeImageV1")
        provider = os.getenv("INTAKE_IMAGES_SINGLE_PROVIDER", "nim")
        weaviate_key = get_secret("INTAKE_WEAVIATE_API_KEY") or ""
        image_searcher = WeaviateImageSearcher(image_url, collection, weaviate_key)
        if request.mode != "hybrid":
            hits = await image_searcher.search(
                request.query, limit=request.limit, mode="keyword", embedders=None
            )
            return response.model_copy(update={"image_collection": collection, "image_hits": hits})
        key_name = "NVIDIA_API_KEY" if provider == "nim" else "GOOGLE_API_KEY"
        single_key = get_secret(key_name)
        if not single_key:
            raise ValueError(f"{key_name} is not configured for image search")
        jina_key = (
            get_secret("JINA_API_KEY")
            if os.getenv("INTAKE_IMAGES_MAXSIM", "screenshots") != "none"
            else None
        )
        async with httpx.AsyncClient(timeout=120.0) as client:
            embedders = ImageEmbedders(client, provider, single_key, jina_key)
            hits = await image_searcher.search(
                request.query, limit=request.limit, mode="hybrid", embedders=embedders
            )
        return response.model_copy(update={"image_collection": collection, "image_hits": hits})

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
