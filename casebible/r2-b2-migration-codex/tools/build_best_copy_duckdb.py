"""Normalize source catalogs with DuckDB and feed the authoritative ledger.

The filename is retained as a compatibility entrypoint.  This tool does not
select a best copy in DuckDB. DuckDB reads and normalizes large catalog exports;
:class:`r2_b2_manifest.builder.ManifestBuilder` alone binds metadata, resolves
exact-content groups, and emits review/transfer artifacts.

All source reads are metadata-only. OneDrive inputs are existing R2/PG exports;
this tool never lists or hydrates the user's local OneDrive. E:\\e.efu is retained
only as historical, pre-merge provenance. The current D: consolidation is the
local corpus authority and is represented by the PG ``local_files`` export.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Iterator, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from r2_b2_manifest.builder import ManifestBuilder  # noqa: E402

PG_SHARDS = (
    "r2_occurrence", "atomic_path_index", "onedrive_manifest",
    "gdrive_manifest", "local_files", "legacy_hashes", "recovery_links",
    "media_metadata", "derived_dates",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def compact_timestamp(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("Z", "Z").replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sql_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def require_new_directory(path: Path) -> None:
    if path.exists():
        try:
            first = next(path.iterdir())
        except StopIteration:
            return
        raise FileExistsError(f"immutable output directory is not empty: {path} (found {first.name})")
    path.mkdir(parents=True)


def require_inputs(pg_dir: Path, sha_metadata: Path) -> dict[str, Path]:
    paths = {name: pg_dir / f"{name}.csv.gz" for name in PG_SHARDS}
    missing = [str(path) for path in [*paths.values(), sha_metadata] if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing immutable catalog exports: " + ", ".join(missing))
    return paths


def open_jsonl(path: Path):
    if path.exists():
        raise FileExistsError(f"refusing to overwrite normalized partition: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return gzip.open(path, "wt", encoding="utf-8", newline="\n")


def rows(cursor, batch_size: int = 5_000) -> Iterator[dict[str, object]]:
    names = [item[0] for item in cursor.description]
    while batch := cursor.fetchmany(batch_size):
        for values in batch:
            yield dict(zip(names, values, strict=True))


def clean(value: object) -> object | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def json_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def assertion(field: str, value: object, *, assertion_class: str = "catalog",
              confidence: float = 0.8, trust_score: int = 70) -> dict[str, object] | None:
    value = clean(value)
    if value is None:
        return None
    return {
        "field": field, "value": value, "assertion_class": assertion_class,
        "confidence": confidence, "trust_score": trust_score,
    }


def write_records(path: Path, source_rows: Iterable[Mapping[str, object]],
                  transform: Callable[[Mapping[str, object]], Mapping[str, object] | None]) -> int:
    count = 0
    with open_jsonl(path) as handle:
        for source in source_rows:
            record = transform(source)
            if record is None:
                continue
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")) + "\n")
            count += 1
    return count


def register_views(connection, pg_paths: Mapping[str, Path], sha_metadata: Path) -> None:
    connection.execute("PRAGMA threads=4")
    connection.execute("PRAGMA preserve_insertion_order=false")
    connection.execute(
        """CREATE TABLE normalization_contract AS
           SELECT 'casebible-catalog-normalization-v2' AS contract,
                  'ManifestBuilder is the only resolver; DuckDB never selects winners' AS authority,
                  current_timestamp AS created_at"""
    )
    for name, path in pg_paths.items():
        connection.execute(
            f"CREATE VIEW source_{name} AS SELECT * FROM read_csv_auto('{sql_path(path)}', header=true, sample_size=10000, all_varchar=true)"
        )
    connection.execute(
        f"CREATE VIEW source_sha_metadata AS SELECT * FROM read_csv_auto('{sql_path(sha_metadata)}', header=true, sample_size=10000, all_varchar=true)"
    )


def source_relation(name: str, limit: int | None) -> str:
    source = f"source_{name}"
    return f"(SELECT * FROM {source} LIMIT {limit})" if limit else source


def write_inventory(connection, path: Path, limit: int | None) -> int:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite normalized inventory: {path}")
    source = source_relation("r2_occurrence", limit)
    query = f"""SELECT trim(CAST(bucket AS VARCHAR)) AS bucket,
                       replace(CAST(path AS VARCHAR), '\\\\', '/') AS path,
                       CAST(size AS BIGINT) AS size,
                       coalesce(CAST(md5 AS VARCHAR), '') AS md5,
                       coalesce(CAST(modtime AS VARCHAR), '') AS modtime,
                       coalesce(CAST(mimetype AS VARCHAR), '') AS mimetype
                FROM {source}
                WHERE bucket IS NOT NULL AND path IS NOT NULL AND size IS NOT NULL
                ORDER BY bucket, path, size, md5"""
    connection.execute(
        f"COPY ({query}) TO '{sql_path(path)}' (FORMAT CSV, HEADER true, COMPRESSION GZIP)"
    )
    return int(connection.execute(f"SELECT count(*) FROM ({query})").fetchone()[0])


def write_sha_partitions(connection, directory: Path, limit: int | None) -> tuple[list[Path], int]:
    source = source_relation("sha_metadata", limit)
    cursor = connection.execute(
        f"""SELECT lower(CAST(sha256 AS VARCHAR)) AS sha256,
                   lower(CAST(md5 AS VARCHAR)) AS md5,
                   CAST(byte_size AS BIGINT) AS byte_size,
                   CAST(source_bucket AS VARCHAR) AS source_bucket,
                   replace(CAST(source_path AS VARCHAR), '\\\\', '/') AS source_path,
                   CAST(source_version AS VARCHAR) AS source_version,
                   CAST(source_etag AS VARCHAR) AS source_etag,
                   CAST(computed_at AS VARCHAR) AS computed_at,
                   CAST(computation AS VARCHAR) AS computation
            FROM {source}
            WHERE sha256 IS NOT NULL AND source_bucket IS NOT NULL AND source_path IS NOT NULL
            ORDER BY sha256, source_bucket, source_path"""
    )
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    handle = None
    prefix = None
    count = 0
    try:
        for row in rows(cursor):
            new_prefix = str(row["sha256"])[:2]
            if new_prefix != prefix:
                if handle is not None:
                    handle.close()
                target = directory / f"sha256-{new_prefix}.ndjson.gz"
                handle = open_jsonl(target)
                paths.append(target)
                prefix = new_prefix
            record = {
                "schema": "casebible-r2-sha256-record-v2",
                "algorithm": "SHA-256",
                "digest": row["sha256"],
                "sourceBucket": row["source_bucket"],
                "sourceKey": row["source_path"],
                "sourceVersion": clean(row["source_version"]),
                "sourceEtag": clean(row["source_etag"]),
                "sourceSize": row["byte_size"],
                "md5Hash": clean(row["md5"]),
                "computedAt": clean(row["computed_at"]),
                "computation": clean(row["computation"]) or "source-ledger-export",
            }
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    finally:
        if handle is not None:
            handle.close()
    return paths, count


def sha_metadata_record(row: Mapping[str, object]) -> Mapping[str, object]:
    fields = [
        assertion("original_filename", row.get("filename"), assertion_class="provider", confidence=0.9, trust_score=82),
        assertion("content_type", row.get("content_type"), assertion_class="provider", confidence=0.9, trust_score=80),
        assertion("file_type", row.get("file_type"), assertion_class="provider", confidence=0.85, trust_score=75),
        assertion("provider_modified_at", row.get("custom_mtime"), assertion_class="provider", confidence=0.85, trust_score=78),
        assertion("provider_created_at", row.get("source_uploaded_at"), assertion_class="provider", confidence=0.75, trust_score=70),
        assertion("source_version", row.get("source_version"), assertion_class="provider", confidence=0.95, trust_score=90),
        assertion("source_etag", row.get("source_etag"), assertion_class="provider", confidence=0.95, trust_score=90),
        assertion("storage_class", row.get("storage_class"), assertion_class="provider", confidence=0.9, trust_score=75),
        assertion("provider_custom_metadata", json_value(row.get("custom_metadata_json")), assertion_class="provider", confidence=0.85, trust_score=75),
        assertion("provider_http_metadata", json_value(row.get("http_metadata_json")), assertion_class="provider", confidence=0.85, trust_score=75),
    ]
    return {
        "source_system": "r2-sha256-ledger", "source_table": "sha256_metadata",
        "source_key": f"{row.get('source_bucket')}:{row.get('source_path')}:{row.get('source_version') or ''}",
        "source_bucket": row.get("source_bucket"), "source_path": row.get("source_path"),
        "byte_size": row.get("byte_size"), "sha256": row.get("sha256"),
        "md5": row.get("md5"), "identity_authority": "sha256_verified",
        "source_version": row.get("source_version"), "snapshot_id": row.get("computed_at"),
        "observed_at": row.get("computed_at"),
        "assertions": [field for field in fields if field is not None],
    }


def media_record(row: Mapping[str, object]) -> Mapping[str, object]:
    metadata = json_value(row.get("metadata_json"))
    if not isinstance(metadata, dict):
        metadata = {"raw": metadata}
    aliases = {
        "mtime": "modified_at", "model": "extractor_model", "read_error": "error",
        "needs_review": "needs_review", "date_start": "date_start", "date_end": "date_end",
        "title": "title", "format": "content_type", "doc_type": "document_type",
    }
    assertions: list[dict[str, object]] = []
    for key, value in metadata.items():
        field = aliases.get(str(key), f"media.{str(key).strip().casefold().replace(' ', '_')}")
        item = assertion(field, value, assertion_class="catalog", confidence=0.8, trust_score=68)
        if item is not None:
            assertions.append(item)
    return {
        "source_system": "casebible-pg18", "source_table": row.get("source_table") or "media.enrichment",
        "source_key": row.get("file_id"), "source_path": row.get("source_path"),
        "byte_size": metadata.get("bytes"), "snapshot_id": row.get("observed_at"),
        "observed_at": row.get("observed_at"), "assertions": assertions,
    }


def derived_date_record(row: Mapping[str, object]) -> Mapping[str, object]:
    fields = [
        assertion("derived_date", row.get("asserted_date"), confidence=0.65, trust_score=55),
        assertion("original_filename", row.get("filename"), confidence=0.65, trust_score=55),
        assertion("date_derivation_method", row.get("date_source"), confidence=0.8, trust_score=60),
    ]
    return {
        "source_system": "casebible-pg18", "source_table": row.get("source_table") or "derived_dates",
        "source_key": f"{row.get('_src_file')}:{row.get('source_path')}:{row.get('filename')}:{row.get('size')}:{row.get('asserted_date')}",
        "source_path": clean(row.get("source_path")), "source_filename": row.get("filename"),
        "byte_size": row.get("size"), "snapshot_id": row.get("loaded_at"),
        "observed_at": row.get("loaded_at"), "assertions": [f for f in fields if f is not None],
    }


def onedrive_record(row: Mapping[str, object]) -> Mapping[str, object]:
    fields = [
        assertion("provider_modified_at", row.get("modtime"), assertion_class="provider", confidence=0.8, trust_score=72),
        assertion("provider_quickxor", row.get("quickxor"), assertion_class="provider", confidence=0.9, trust_score=70),
        assertion("provider_tree", row.get("tree"), assertion_class="provider", confidence=1.0, trust_score=65),
    ]
    return {
        "source_system": "onedrive-r2-export", "source_table": "catalog.od_manifest",
        "source_key": f"{row.get('tree')}:{row.get('path')}:{row.get('scan_file')}",
        "source_account": row.get("tree"), "source_tree": row.get("tree"),
        "source_path": row.get("path"), "byte_size": row.get("size"),
        "quickxor": row.get("quickxor"), "snapshot_id": row.get("scan_file"),
        "source_version": row.get("scanned_at"), "observed_at": row.get("scanned_at"),
        "detail": {"content_lookup": "R2 metadata only; local OneDrive is not hydrated"},
        "assertions": [f for f in fields if f is not None],
    }


def local_record(row: Mapping[str, object]) -> Mapping[str, object]:
    fields = [
        assertion("observed_filename", row.get("name"), confidence=0.7, trust_score=58),
        assertion("local_consolidation_source", row.get("source"), confidence=0.9, trust_score=65),
    ]
    return {
        "source_system": "casebible-current-d-consolidation", "source_table": "raw_duck.local_files",
        "source_key": f"{row.get('_src_file')}:{row.get('source')}:{row.get('path')}:{row.get('size')}",
        "source_tree": "D-current-consolidated", "source_path": row.get("path"),
        "source_filename": row.get("name"), "byte_size": row.get("size"),
        "snapshot_id": row.get("loaded_at"), "observed_at": row.get("loaded_at"),
        "assertions": [f for f in fields if f is not None],
    }


def efu_record(row: Mapping[str, object]) -> Mapping[str, object] | None:
    size = clean(row.get("Size"))
    filename = clean(row.get("Filename"))
    if filename is None or size is None:
        return None
    fields = [
        assertion("historical_path", filename, confidence=1.0, trust_score=55),
        assertion("historical_modified_filetime", row.get("Date Modified"), confidence=0.9, trust_score=50),
        assertion("historical_created_filetime", row.get("Date Created"), confidence=0.9, trust_score=50),
        assertion("historical_attributes", row.get("Attributes"), confidence=0.9, trust_score=45),
    ]
    normalized = str(filename).replace("\\", "/")
    return {
        "source_system": "efu-historical", "source_table": "E-e.efu",
        "source_key": f"E-pre-merge:{normalized}:{size}",
        "source_account": "local-E", "source_tree": "E-historical-pre-merge",
        "source_path": normalized, "source_filename": Path(normalized).name,
        "byte_size": size, "snapshot_id": "pre-D-consolidation",
        "detail": {"authority": "historical provenance only; D is current consolidated local corpus"},
        "assertions": [f for f in fields if f is not None],
    }


def desktop_export_record(row: Mapping[str, object]) -> Mapping[str, object] | None:
    filename = clean(row.get("Filename"))
    folder = clean(row.get("Folder"))
    if filename is None or folder is None:
        return None
    path = f"{str(folder).rstrip('\\/')}/{filename}".replace("\\", "/")
    size_kb = clean(row.get("Size (KB)"))
    try:
        byte_size = int(float(size_kb) * 1024) if size_kb is not None else None
    except (TypeError, ValueError):
        byte_size = None
    fields = [
        assertion("observed_filename", filename, confidence=0.7, trust_score=55),
        assertion("provider_modified_at", row.get("Modification"), assertion_class="provider", confidence=0.65, trust_score=55),
        assertion("provider_kind", row.get("Kind"), assertion_class="provider", confidence=0.75, trust_score=55),
        assertion("provider_match_percent", row.get("Match %"), assertion_class="provider", confidence=0.5, trust_score=35),
        assertion("provider_dupe_count", row.get("Dupe Count"), assertion_class="provider", confidence=0.5, trust_score=35),
    ]
    return {
        "source_system": "onedrive-desktop-export-report", "source_table": "export.csv",
        "source_key": f"{path}:{size_kb}:{row.get('Modification')}",
        "source_account": "matts", "source_tree": "OneDrive-report-metadata-only",
        "source_path": path, "source_filename": filename, "byte_size": byte_size,
        "match_percent": row.get("Match %"),
        "detail": {"content_lookup": "R2 metadata only; report is not identity authority and local OneDrive is not hydrated"},
        "assertions": [f for f in fields if f is not None],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-export-dir", type=Path, required=True)
    parser.add_argument("--sha-metadata", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--efu", type=Path)
    parser.add_argument("--onedrive-export", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--finalize-sha-bridge", action="store_true")
    parser.add_argument("--expected-sha-record-count", type=int)
    parser.add_argument("--build-generation", action="store_true")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if args.finalize_sha_bridge and not args.expected_sha_record_count:
        parser.error("--finalize-sha-bridge requires --expected-sha-record-count")

    pg_dir = args.pg_export_dir.resolve()
    sha_metadata = args.sha_metadata.resolve()
    output = args.output_dir.resolve()
    pg_paths = require_inputs(pg_dir, sha_metadata)
    require_new_directory(output)

    import duckdb

    database = output / "normalization.duckdb"
    connection = duckdb.connect(str(database))
    started_at = utc_now()
    artifacts: dict[str, object] = {}
    try:
        register_views(connection, pg_paths, sha_metadata)
        stamp = compact_timestamp(started_at)
        inventory = output / f"r2-inventory-{stamp}.csv.gz"
        artifacts["inventory_rows"] = write_inventory(connection, inventory, args.limit)

        sha_dir = output / "sha256-partitions"
        sha_partitions, sha_rows = write_sha_partitions(connection, sha_dir, args.limit)
        artifacts["sha_partition_count"] = len(sha_partitions)
        artifacts["sha_rows"] = sha_rows

        normalized_dir = output / "metadata-partitions"
        normalized_dir.mkdir()
        sha_meta_path = normalized_dir / "sha-metadata.ndjson.gz"
        artifacts["sha_metadata_rows"] = write_records(
            sha_meta_path,
            rows(connection.execute(f"SELECT * FROM {source_relation('sha_metadata', args.limit)} ORDER BY sha256, source_bucket, source_path")),
            sha_metadata_record,
        )
        media_path = normalized_dir / "pg-media-metadata.ndjson.gz"
        artifacts["pg_media_rows"] = write_records(
            media_path,
            rows(connection.execute(f"SELECT * FROM {source_relation('media_metadata', args.limit)} ORDER BY source_path, file_id")),
            media_record,
        )
        date_path = normalized_dir / "pg-derived-dates.ndjson.gz"
        artifacts["pg_derived_date_rows"] = write_records(
            date_path,
            rows(connection.execute(f"SELECT * FROM {source_relation('derived_dates', args.limit)} ORDER BY source_path, filename, asserted_date")),
            derived_date_record,
        )
        od_path = normalized_dir / "onedrive-r2-metadata.ndjson.gz"
        artifacts["onedrive_r2_rows"] = write_records(
            od_path,
            rows(connection.execute(f"SELECT * FROM {source_relation('onedrive_manifest', args.limit)} ORDER BY tree, path, scan_file")),
            onedrive_record,
        )
        local_path = normalized_dir / "d-current-local-metadata.ndjson.gz"
        artifacts["d_current_local_rows"] = write_records(
            local_path,
            rows(connection.execute(f"SELECT * FROM {source_relation('local_files', args.limit)} ORDER BY source, path")),
            local_record,
        )
        metadata_partitions = [sha_meta_path, media_path, date_path, od_path, local_path]

        if args.efu:
            efu = args.efu.resolve()
            if not efu.is_file():
                raise FileNotFoundError(efu)
            connection.execute(
                f"CREATE VIEW source_efu_historical AS SELECT * FROM read_csv_auto('{sql_path(efu)}', header=true, sample_size=10000, all_varchar=true)"
            )
            efu_path = normalized_dir / "efu-historical-pre-merge.ndjson.gz"
            artifacts["efu_historical_rows"] = write_records(
                efu_path,
                rows(connection.execute(f'SELECT * FROM {source_relation("efu_historical", args.limit)} ORDER BY "Filename"')),
                efu_record,
            )
            metadata_partitions.append(efu_path)

        if args.onedrive_export:
            od_export = args.onedrive_export.resolve()
            if not od_export.is_file():
                raise FileNotFoundError(od_export)
            connection.execute(
                f"CREATE VIEW source_onedrive_report AS SELECT * FROM read_csv_auto('{sql_path(od_export)}', header=true, sample_size=10000, all_varchar=true)"
            )
            report_path = normalized_dir / "onedrive-export-report.ndjson.gz"
            artifacts["onedrive_report_rows"] = write_records(
                report_path,
                rows(connection.execute(f'SELECT * FROM {source_relation("onedrive_report", args.limit)} ORDER BY "Folder", "Filename"')),
                desktop_export_record,
            )
            metadata_partitions.append(report_path)
    finally:
        connection.close()

    ledger = output / "manifest-ledger.sqlite"
    review = output / "metadata-review"
    with ManifestBuilder(ledger) as builder:
        builder.ingest([inventory])
        fingerprint_results = builder.import_sha256_ledger(sha_partitions)
        artifacts["fingerprint_bound_rows"] = sum(item.bound_count for item in fingerprint_results)
        artifacts["fingerprint_held_rows"] = sum(item.held_count for item in fingerprint_results)
        if args.finalize_sha_bridge:
            bridge = builder.finalize_sha256_bridge(
                expected_partition_count=len(sha_partitions),
                expected_record_count=args.expected_sha_record_count,
            )
            artifacts["bridge_groups"] = bridge.bridge_group_count
        metadata_results = builder.import_metadata_assertions(metadata_partitions)
        artifacts["metadata_assertions"] = sum(item.assertion_count for item in metadata_results)
        artifacts["metadata_bound_records"] = sum(item.bound_record_count for item in metadata_results)
        artifacts["metadata_held_records"] = sum(item.held_record_count for item in metadata_results)
        artifacts["resolved_groups"] = builder.write_metadata_resolution(review, resolved_at=started_at)
        if args.build_generation:
            result = builder.build_generation(
                output / "generation", generation_id=f"best-copy-{stamp}", created_at=started_at,
            )
            artifacts["generation"] = result.__dict__

    receipt = {
        "schema": "casebible-best-copy-normalization-receipt-v2",
        "started_at": started_at,
        "completed_at": utc_now(),
        "authority": "ManifestBuilder SQLite ledger; DuckDB normalizes and extracts only",
        "onedrive_policy": "existing R2/PG exports only; no local hydration",
        "local_corpus_policy": "D is current consolidated authority; E EFU is historical provenance only",
        "inputs": {
            str(path): {"size": path.stat().st_size, "sha256": file_sha256(path)}
            for path in [*pg_paths.values(), sha_metadata]
        },
        "artifacts": artifacts,
    }
    receipt_path = output / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
