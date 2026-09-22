from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer

from .atomic_units import detect_atomic_units
from .config import Settings
from .fingerprints import newest_fingerprints, write_fingerprints
from .inventory import newest_inventory, write_inventory
from .nim import NimClient
from .parquet_store import write_json_immutable
from .search import SemanticSearcher
from .secrets import get_secret
from .snapshots import build_active_snapshot, newest_snapshot

app = typer.Typer(no_args_is_help=True, help="Isolated Case Bible corpus + NIM + Parquet tools")


@app.command("graph-status")
def graph_status() -> None:
    """Check dedicated graph authentication and schema without reading source files."""
    from .projections.runtime import connect_graph

    async def check() -> dict:
        async with await connect_graph() as graph:
            version = await graph.verify_health_and_schema()
            return {
                "status": "ready",
                "namespace": "consignatio",
                "database": "intake",
                "version": version,
            }

    try:
        typer.echo(json.dumps(asyncio.run(check())))
    except Exception:
        typer.echo(
            "Intake graph unavailable; verify backend configuration and credentials", err=True
        )
        raise typer.Exit(1) from None


@app.command("graph-project-inventory")
def graph_project_inventory(
    manifest: Path,
    apply: Annotated[
        bool, typer.Option(help="Write validated observations to Intake graph")
    ] = False,
) -> None:
    """Validate existing artifact manifest; graph writes require explicit --apply."""
    from .projections.inventory_manifest import load_inventory_projection, project_inventory
    from .projections.runtime import connect_graph

    try:
        plan = load_inventory_projection(manifest)
        if not apply:
            typer.echo(
                json.dumps(
                    {
                        "status": "validated",
                        "snapshot_key": plan.snapshot_key,
                        "occurrences": len(plan.rows),
                        "unique_contents": len(plan.content),
                    }
                )
            )
            return

        async def project() -> dict:
            async with await connect_graph() as graph:
                return await project_inventory(graph, plan)

        typer.echo(json.dumps(asyncio.run(project())))
    except Exception:
        typer.echo(
            "Inventory projection failed; input validation or graph operation failed", err=True
        )
        raise typer.Exit(1) from None


@app.command("graph-project-catalog")
def graph_project_catalog(
    manifest: Path,
    apply: Annotated[
        bool, typer.Option(help="Write validated historical metadata to Intake graph")
    ] = False,
) -> None:
    """Validate a historical catalog batch; --apply never copies source objects."""
    from .projections.legacy_catalog import load_legacy_catalog, project_legacy_catalog
    from .projections.runtime import connect_graph

    try:
        plan = load_legacy_catalog(manifest)
        if not apply:
            typer.echo(
                json.dumps(
                    {
                        "status": "validated",
                        "snapshot_key": plan.snapshot_key,
                        "occurrences": len(plan.rows),
                        "contents": 0,
                    }
                )
            )
            return

        async def project() -> dict:
            async with await connect_graph() as graph:
                return await project_legacy_catalog(graph, plan)

        typer.echo(json.dumps(asyncio.run(project())))
    except Exception:
        typer.echo("Historical catalog projection failed; verify input and graph", err=True)
        raise typer.Exit(1) from None


@app.command("graph-project-migration")
def graph_project_migration(
    manifest: Path,
    apply: Annotated[
        bool, typer.Option(help="Write a validated occurrence map to Intake graph")
    ] = False,
) -> None:
    """Validate a migration occurrence map; never controls or executes transfer."""
    from .projections.migration_manifest import load_migration_projection, project_migration
    from .projections.runtime import connect_graph

    try:
        plan = load_migration_projection(manifest)
        if not apply:
            typer.echo(
                json.dumps(
                    {
                        "status": "validated",
                        "snapshot_key": plan.snapshot_key,
                        "occurrences": len(plan.rows),
                    }
                )
            )
            return

        async def project() -> dict:
            async with await connect_graph() as graph:
                return await project_migration(graph, plan)

        typer.echo(json.dumps(asyncio.run(project())))
    except Exception:
        typer.echo("Migration projection failed; verify input and graph", err=True)
        raise typer.Exit(1) from None


def _settings(
    source: Path | None = None,
    output: Path | None = None,
    source_id: str | None = None,
    *,
    require_source: bool = True,
) -> Settings:
    if source is not None:
        os.environ["CASEBIBLE_SOURCE_DIR"] = str(source)
    if output is not None:
        os.environ["CASEBIBLE_OUTPUT_DIR"] = str(output)
    if source_id is not None:
        os.environ["CASEBIBLE_SOURCE_ID"] = source_id
    settings = Settings.from_env().resolved()
    settings.validate(require_source=require_source)
    return settings


def _receipt_path(settings: Settings, operation: str) -> Path:
    now = datetime.now(UTC)
    name = now.strftime("%Y%m%dT%H%M%S.%fZ") + f"-{operation}-" + uuid4().hex[:8] + ".json"
    return settings.output_dir / "receipts" / name


@app.command()
def index(
    source: Annotated[Path | None, typer.Option(help="Source directory; never modified")] = None,
    output: Annotated[Path | None, typer.Option(help="Derived output directory")] = None,
    source_id: Annotated[
        str | None, typer.Option(help="Stable portable identity for this source tree")
    ] = None,
    with_inventory: Annotated[
        bool, typer.Option(help="Also create a path-only inventory and atomic candidates")
    ] = False,
    limit: Annotated[
        int | None,
        typer.Option(min=1, help="Catalog mode: index at most N objects (bounded first run)"),
    ] = None,
    path_prefix: Annotated[
        str | None, typer.Option(help="Catalog mode: only keys starting with this prefix")
    ] = None,
    project_graph: Annotated[
        bool, typer.Option(help="Project the run into the Surreal file graph (default on)")
    ] = True,
) -> None:
    """Incrementally index supported text documents and write an active snapshot."""

    # Bounded-run controls must reach the pipeline module's import-time settings.
    # Byline: Claude Code · Opus 5 · 2026-09-22.
    if limit is not None:
        os.environ["INTAKE_CATALOG_LIMIT"] = str(limit)
    if path_prefix is not None:
        os.environ["INTAKE_CATALOG_PATH_PREFIX"] = path_prefix
    # Settings.validate() already waives the source directory in catalog mode.
    settings = _settings(source, output, source_id)
    # Import only after CLI overrides are reflected in the environment.
    import cocoindex as coco

    from .pipeline import app as index_app
    from .run_status import latest_run_status

    # Programmatic callers own runtime teardown, unlike the CocoIndex CLI.
    # Closing it flushes the lifespan's final receipt and releases source locks.
    try:
        from .pipeline import READ_COUNTERS
    except ImportError:  # a caller that supplies its own pipeline module (tests)
        READ_COUNTERS = None

    with coco.runtime():
        index_app.update_blocking(report_to_stdout=True)
    run_status = latest_run_status(settings.output_dir)
    if run_status.get("state") != "finished" or run_status.get("failure_events"):
        raise RuntimeError("Index run did not finish cleanly; inspect retained run status")
    snapshot = build_active_snapshot(settings)
    receipt: dict[str, object] = {
        "operation": "index",
        "completed_at": datetime.now(UTC).isoformat(),
        "source_dir": str(settings.source_dir),
        "source_id": settings.source_id,
        "output_dir": str(settings.output_dir),
        "snapshot": str(snapshot),
        "embedding_model": settings.embed_model,
        "summary_model": settings.summary_model,
        "embedding_dimensions": settings.embed_dimensions,
        "source_mode": getattr(settings, "source_mode", "filesystem"),
        "catalog_limit": getattr(settings, "catalog_limit", 0),
        "catalog_path_prefix": getattr(settings, "catalog_path_prefix", ""),
        "run_status": run_status,
        "source_bytes_modified": False,
        **(READ_COUNTERS.snapshot() if READ_COUNTERS is not None else {}),
    }
    catalog_mode = getattr(settings, "source_mode", "filesystem") == "catalog"
    if project_graph:
        # Audit item I-6: the file graph is fed by every run, never a separate manual pass.
        from .projections.index_run import project_index_run
        from .projections.runtime import connect_graph

        scheme = getattr(settings, "object_store_scheme", "b2")
        bucket = getattr(settings, "vault_bucket", "")
        locator = (
            f"{scheme}://{bucket}/" if catalog_mode else Path(settings.source_dir).as_uri()
        )

        async def project() -> dict:
            async with await connect_graph() as graph:
                return await project_index_run(
                    graph,
                    output_dir=settings.output_dir,
                    snapshot=snapshot,
                    source_id=settings.source_id,
                    root_locator=locator,
                    store_kind="object_store" if catalog_mode else "filesystem",
                )

        try:
            receipt["graph"] = asyncio.run(project())
        except Exception as exc:  # noqa: BLE001 - a graph outage must not lose the index run
            receipt["graph"] = {"status": "failed", "error": type(exc).__name__}
    if with_inventory:
        inventory_result = write_inventory(settings)
        atomic_result = detect_atomic_units(settings, inventory_result.path)
        receipt["inventory"] = {
            "path": str(inventory_result.path),
            "file_count": inventory_result.file_count,
            "total_bytes": inventory_result.total_bytes,
            "error_count": inventory_result.error_count,
        }
        receipt["atomic"] = {
            "run_dir": str(atomic_result.run_dir),
            "candidate_count": atomic_result.candidate_count,
            "member_count": atomic_result.member_count,
        }
    receipt_path = _receipt_path(settings, "index")
    write_json_immutable(receipt_path, receipt)
    typer.echo(json.dumps({**receipt, "receipt": str(receipt_path)}, indent=2))


@app.command()
def inventory(
    source: Annotated[Path | None, typer.Option()] = None,
    output: Annotated[Path | None, typer.Option()] = None,
    source_id: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Snapshot paths/stat data for all files without reading their content."""

    settings = _settings(source, output, source_id)
    result = write_inventory(settings)
    typer.echo(
        json.dumps(
            {
                "path": str(result.path),
                "file_count": result.file_count,
                "total_bytes": result.total_bytes,
                "error_count": result.error_count,
                "source_bytes_modified": False,
            },
            indent=2,
        )
    )


@app.command("detect-units")
def detect_units(
    source: Annotated[Path | None, typer.Option()] = None,
    output: Annotated[Path | None, typer.Option()] = None,
    source_id: Annotated[str | None, typer.Option()] = None,
    inventory_path: Annotated[Path | None, typer.Option(help="Inventory Parquet override")] = None,
) -> None:
    """Emit review-only atomic package candidates, members, and nesting edges."""

    settings = _settings(source, output, source_id)
    selected_inventory = inventory_path or newest_inventory(settings.output_dir)
    result = detect_atomic_units(settings, selected_inventory)
    typer.echo(
        json.dumps(
            {
                "run_dir": str(result.run_dir),
                "units": str(result.units_path),
                "members": str(result.members_path),
                "edges": str(result.edges_path),
                "candidate_count": result.candidate_count,
                "member_count": result.member_count,
                "authority": "candidate boundaries only; no source moves or dedup decisions",
            },
            indent=2,
        )
    )


@app.command()
def fingerprint(
    source: Annotated[Path | None, typer.Option()] = None,
    output: Annotated[Path | None, typer.Option()] = None,
    source_id: Annotated[str | None, typer.Option()] = None,
    inventory_path: Annotated[Path | None, typer.Option(help="Inventory Parquet override")] = None,
    scope: Annotated[
        str,
        typer.Option(help="all, or dedup-candidates for the same-size prefilter"),
    ] = "all",
    text_max_mib: Annotated[
        int, typer.Option(min=1, help="Maximum file size for extracted-text fingerprints")
    ] = 64,
    near_distance: Annotated[
        int, typer.Option(min=0, max=16, help="Maximum 64-bit SimHash distance")
    ] = 6,
) -> None:
    """Hash source bytes and emit review-only exact/textual duplicate candidates."""

    if scope not in {"all", "dedup-candidates"}:
        raise typer.BadParameter("scope must be 'all' or 'dedup-candidates'")
    settings = _settings(source, output, source_id)
    selected_inventory = inventory_path or newest_inventory(settings.output_dir)
    if selected_inventory is None:
        raise typer.BadParameter("No inventory snapshot exists; run inventory first")
    result = write_fingerprints(
        settings,
        selected_inventory,
        scope=scope,
        text_max_bytes=text_max_mib * 1024 * 1024,
        near_distance=near_distance,
    )
    receipt = {
        "operation": "fingerprint",
        "completed_at": datetime.now(UTC).isoformat(),
        "source_dir": str(settings.source_dir),
        "source_id": settings.source_id,
        "inventory": str(selected_inventory),
        "scope": scope,
        "run_dir": str(result.run_dir),
        "files": str(result.files_path),
        "exact_groups": str(result.exact_groups_path),
        "exact_members": str(result.exact_members_path),
        "text_equivalent_groups": str(result.text_equivalent_groups_path),
        "near_text_candidates": str(result.near_text_path),
        "package_manifests": str(result.package_manifests_path or ""),
        "package_exact_groups": str(result.package_groups_path or ""),
        "file_count": result.file_count,
        "hashed_count": result.hashed_count,
        "reused_count": result.reused_count,
        "skipped_count": result.skipped_count,
        "error_count": result.error_count,
        "authority": "candidate evidence only; no canonical selected and no source mutation",
        "source_bytes_modified": False,
    }
    receipt_path = _receipt_path(settings, "fingerprint")
    write_json_immutable(receipt_path, receipt)
    typer.echo(json.dumps({**receipt, "receipt": str(receipt_path)}, indent=2))


async def _search(settings: Settings, query: str, limit: int, hybrid: bool) -> None:
    api_key = get_secret("NVIDIA_API_KEY")
    if not api_key:
        raise typer.BadParameter("NVIDIA_API_KEY is not configured")
    async with NimClient(
        api_key=api_key,
        base_url=settings.nim_base_url,
        embed_model=settings.embed_model,
        summary_model=settings.summary_model,
        dimensions=settings.embed_dimensions,
        timeout_seconds=settings.timeout_seconds,
        max_retries=settings.max_retries,
        max_concurrency=settings.max_concurrency,
    ) as client:
        response = await SemanticSearcher(settings, client).search(
            query, limit=limit, hybrid=hybrid
        )
    typer.echo(response.model_dump_json(indent=2))


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Semantic search query")],
    output: Annotated[Path | None, typer.Option()] = None,
    limit: Annotated[int, typer.Option(min=1, max=100)] = 10,
    hybrid: Annotated[bool, typer.Option(help="Add a small lexical reranking signal")] = True,
) -> None:
    """Embed a query with NIM and search active Parquet chunks using DuckDB."""

    settings = _settings(output=output, require_source=False)
    asyncio.run(_search(settings, query, limit, hybrid))


@app.command()
def status(output: Annotated[Path | None, typer.Option()] = None) -> None:
    """Show the latest immutable artifacts without making network calls."""

    settings = _settings(output=output, require_source=False)
    typer.echo(
        json.dumps(
            {
                "output_dir": str(settings.output_dir),
                "snapshot": str(newest_snapshot(settings.output_dir) or ""),
                "inventory": str(newest_inventory(settings.output_dir) or ""),
                "fingerprints": str(newest_fingerprints(settings.output_dir) or ""),
                "document_shards": len(
                    list((settings.output_dir / "datasets" / "documents").glob("*.parquet"))
                ),
                "chunk_shards": len(
                    list((settings.output_dir / "datasets" / "chunks").glob("*.parquet"))
                ),
            },
            indent=2,
        )
    )


@app.command()
def serve(
    output: Annotated[Path | None, typer.Option()] = None,
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option()] = 8765,
) -> None:
    """Serve health, document listing, and semantic search endpoints."""

    if output is not None:
        os.environ["CASEBIBLE_OUTPUT_DIR"] = str(output)
    import uvicorn

    uvicorn.run("casebible_index.api:app", host=host, port=port, reload=False)


@app.command()
def tui(
    source: Annotated[Path | None, typer.Option()] = None,
    output: Annotated[Path | None, typer.Option()] = None,
    source_id: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Open the keyboard-driven Case Bible corpus operator console."""

    from .tui import run_tui

    run_tui(_settings(source, output, source_id, require_source=False))


# --- Image index (own app, state and collection; Byline: Claude Code · Fable 5.1 · 2026-09-21) ---

@app.command("image-provision")
def image_provision() -> None:
    """Create the image collection (single + MaxSim named vectors) if it does not exist."""
    import httpx

    from .image_pipeline import ImageSettings
    from .image_target import collection_schema

    settings = ImageSettings.from_env()
    if not settings.weaviate_url:
        raise typer.BadParameter("INTAKE_IMAGES_WEAVIATE_URL is required")
    key = get_secret("INTAKE_WEAVIATE_API_KEY")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    with httpx.Client(headers=headers, timeout=60.0) as client:
        existing = client.get(f"{settings.weaviate_url}/v1/schema/{settings.collection}")
        if existing.status_code == 200:
            typer.echo(json.dumps({"collection": settings.collection, "created": False}))
            return
        created = client.post(
            f"{settings.weaviate_url}/v1/schema", json=collection_schema(settings.collection)
        )
        created.raise_for_status()
    typer.echo(json.dumps({"collection": settings.collection, "created": True}))


@app.command("image-index")
def image_index() -> None:
    """Incrementally index images under INTAKE_IMAGES_SOURCE_DIR. Sources are never modified."""
    import cocoindex as coco

    from .image_pipeline import _settings as image_settings
    from .image_pipeline import app as image_app

    with coco.runtime():
        image_app.update_blocking(report_to_stdout=True)
    typer.echo((image_settings.state_dir / "last-run.json").read_text(encoding="utf-8"))


@app.command("image-search")
def image_search(
    query: str,
    limit: Annotated[int, typer.Option(min=1, max=50)] = 5,
    maxsim: Annotated[
        bool, typer.Option(help="Score with the Jina MaxSim vector, not the single vector")
    ] = True,
) -> None:
    """Find images by a text question."""
    import httpx

    from .image_embedders import ImageEmbedders
    from .image_pipeline import ImageSettings
    from .image_target import MULTI_VECTOR, SINGLE_VECTOR

    settings = ImageSettings.from_env()
    key_name = "NVIDIA_API_KEY" if settings.single_provider == "nim" else "GOOGLE_API_KEY"
    single_key = get_secret(key_name)
    weaviate_key = get_secret("INTAKE_WEAVIATE_API_KEY")

    async def run() -> list[dict]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            embedders = ImageEmbedders(
                client, settings.single_provider, single_key or "", get_secret("JINA_API_KEY")
            )
            single, multi = await embedders.embed_query(query)
            use_multi = maxsim and multi is not None
            vector, target = (multi, MULTI_VECTOR) if use_multi else (single, SINGLE_VECTOR)
            fields = (
                "filename source_path original_time original_time_source device "
                "is_screenshot ocr_text _additional { distance }"
            )
            active = "{path: [\"active\"], operator: Equal, valueBoolean: true}"
            near = f"{{vector: {json.dumps(vector)}, targetVectors: [\"{target}\"]}}"
            graphql = (
                f"{{ Get {{ {settings.collection}(limit: {limit}, where: {active}, "
                f"nearVector: {near}) {{ {fields} }} }} }}"
            )
            headers = {"Authorization": f"Bearer {weaviate_key}"} if weaviate_key else {}
            response = await client.post(
                f"{settings.weaviate_url}/v1/graphql", json={"query": graphql}, headers=headers
            )
            response.raise_for_status()
            body = response.json()
            if body.get("errors"):
                raise RuntimeError(str(body["errors"])[:400])
            return body["data"]["Get"][settings.collection]

    typer.echo(json.dumps(asyncio.run(run()), indent=2))


if __name__ == "__main__":
    app()
