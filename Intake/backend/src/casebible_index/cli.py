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
) -> None:
    """Incrementally index supported text documents and write an active snapshot."""

    settings = _settings(source, output, source_id)
    # Import only after CLI overrides are reflected in the environment.
    import cocoindex as coco

    from .pipeline import app as index_app
    from .run_status import latest_run_status

    # Programmatic callers own runtime teardown, unlike the CocoIndex CLI.
    # Closing it flushes the lifespan's final receipt and releases source locks.
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
        "source_bytes_modified": False,
    }
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


if __name__ == "__main__":
    app()
