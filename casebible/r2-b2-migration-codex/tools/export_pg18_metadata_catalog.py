"""Export provenance-bearing Case Bible PG18 metadata into bounded CSV shards.

The exporter is intentionally read-only against PostgreSQL.  It runs COPY TO
STDOUT through the configured ``ovh-files`` SSH alias, compresses each stream on
the workstation's E: drive, and writes an append-only receipt.  Existing output
is never overwritten.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CONTAINER = "fgz1n7useplhk0t91uk7k1aw"


@dataclass(frozen=True)
class ExportSpec:
    name: str
    query: str


EXPORTS = (
    ExportSpec(
        "r2_occurrence",
        """SELECT bucket, path, name, size, lower(md5) AS md5,
                  modtime::text AS modtime, mimetype, tier,
                  _src_file, _loaded_at::text AS loaded_at
           FROM raw_duck.r2_files
           ORDER BY bucket, path, size, lower(md5), _loaded_at""",
    ),
    ExportSpec(
        "atomic_path_index",
        """SELECT store, account_key, container, path, name, byte_size,
                  lower(md5) AS md5, lower(sha1) AS sha1,
                  lower(sha256) AS sha256, quickxor, mtime_text,
                  source_variant_key, source_row_count,
                  source_refs::text AS source_refs, indexed_at::text AS indexed_at
           FROM inventory.atomic_path_index
           ORDER BY store, account_key, container, path, source_variant_key""",
    ),
    ExportSpec(
        "onedrive_manifest",
        """SELECT tree, path, size, modtime, quickxor, scan_file,
                  scanned_at::text AS scanned_at
           FROM catalog.od_manifest
           ORDER BY tree, path, size, quickxor, scan_file""",
    ),
    ExportSpec(
        "gdrive_manifest",
        """SELECT path, name, size, mime_type, mod_time::text AS mod_time,
                  drive_id, lower(sha256) AS sha256, lower(md5) AS md5,
                  lower(sha1) AS sha1, account, _src_file,
                  _loaded_at::text AS loaded_at
           FROM gdrive.gd_net_rw
           ORDER BY account, drive_id, path, size""",
    ),
    ExportSpec(
        "local_files",
        """SELECT source, path, name, size, _src_file,
                  _loaded_at::text AS loaded_at
           FROM raw_duck.local_files
           ORDER BY source, path, size, _loaded_at""",
    ),
    ExportSpec(
        "legacy_hashes",
        """SELECT 'legacy_hashes.raw_sizehash' AS source_table,
                  relpath AS path, size, lower(md5) AS md5,
                  _src_file, _loaded_at::text AS loaded_at
           FROM legacy_hashes.raw_sizehash
           UNION ALL
           SELECT 'legacy_hashes.raw_hashes', relpath, NULL::bigint,
                  lower(md5), _src_file, _loaded_at::text
           FROM legacy_hashes.raw_hashes
           ORDER BY source_table, path, size, md5""",
    ),
    ExportSpec(
        "recovery_links",
        """SELECT source_table, missing_path, lower(missing_md5) AS missing_md5,
                  CASE WHEN size ~ '^[0-9]+$' THEN size::bigint END AS size,
                  onedrive_path, source_copies, tree, src_file, loaded_at
           FROM (
             SELECT 'recovery.images' AS source_table, missing_path, missing_md5,
                    size, onedrive_path, source_copies, tree,
                    _src_file AS src_file, _loaded_at::text AS loaded_at
             FROM recovery.images
             UNION ALL SELECT 'recovery.documents', missing_path, missing_md5,
                    size, onedrive_path, source_copies, tree, _src_file,
                    _loaded_at::text FROM recovery.documents
             UNION ALL SELECT 'recovery.photo_recovery', missing_path, missing_md5,
                    size, onedrive_path, source_copies, tree, _src_file,
                    _loaded_at::text FROM recovery.photo_recovery
             UNION ALL SELECT 'recovery.photorec_carves', missing_path, missing_md5,
                    size, onedrive_path, source_copies, tree, _src_file,
                    _loaded_at::text FROM recovery.photorec_carves
             UNION ALL SELECT 'recovery.google_takeout', missing_path, missing_md5,
                    size, onedrive_path, source_copies, tree, _src_file,
                    _loaded_at::text FROM recovery.google_takeout
             UNION ALL SELECT 'recovery.other_trees', missing_path, missing_md5,
                    size, onedrive_path, source_copies, tree, _src_file,
                    _loaded_at::text FROM recovery.other_trees
             UNION ALL SELECT 'rootcsv.onedrive_recovery_map', missing_path,
                    missing_md5, size, onedrive_path, NULL, NULL, _src_file,
                    _loaded_at::text FROM rootcsv.onedrive_recovery_map
           ) links
           ORDER BY source_table, missing_path, onedrive_path, missing_md5""",
    ),
    ExportSpec(
        "media_metadata",
        """SELECT source_table, file_id, source_path, metadata_json,
                  observed_at
           FROM (
             SELECT 'media.photos' AS source_table, file_id, source_path,
                    jsonb_build_object(
                      'ocr_chars', ocr_chars, 'fname_date', fname_date,
                      'fname_time', fname_time, 'file_mtime', file_mtime,
                      'date_effective', date_effective, 'date_source', date_source,
                      'path_phones', path_phones, 'path_names', path_names,
                      'path_platform', path_platform
                    )::text AS metadata_json,
                    to_timestamp(ts)::text AS observed_at
             FROM media.photos
             UNION ALL
             SELECT 'media.screenshots', file_id, source_path,
                    jsonb_build_object(
                      'kind', kind, 'platform', platform, 'participants', participants,
                      'date_start', date_start, 'date_end', date_end,
                      'fname_date', fname_date, 'fname_time', fname_time,
                      'file_mtime', file_mtime, 'date_effective', date_effective,
                      'date_source', date_source, 'path_phones', path_phones,
                      'path_names', path_names, 'path_platform', path_platform,
                      'ocr_chars', ocr_chars, 'confidence', confidence,
                      'needs_review', needs_review
                    )::text, to_timestamp(ts)::text
             FROM media.screenshots
             UNION ALL
             SELECT 'media.enrichment', file_id, source_path,
                    jsonb_build_object(
                      'ext', ext, 'bytes', bytes, 'mtime', mtime,
                      'model', model, 'read_error', read_error, 'title', title,
                      'doc_type', doc_type, 'platform_source', platform_source,
                      'format', format, 'date_start', date_start,
                      'date_end', date_end, 'package_member', package_member,
                      'package_name', package_name,
                      'completeness_signal', completeness_signal,
                      'disposition', disposition, 'confidence', confidence,
                      'needs_review', needs_review
                    )::text, to_timestamp(ts)::text
             FROM media.enrichment
             UNION ALL
             SELECT 'media.faces_scanned', file_id, source_path,
                    jsonb_build_object('n_faces', n_faces, 'error', err)::text,
                    to_timestamp(ts)::text
             FROM media.faces_scanned
           ) metadata
           ORDER BY source_table, file_id, source_path""",
    ),
    ExportSpec(
        "derived_dates",
        """SELECT 'raw_duck.resolved' AS source_table, path_y AS source_path,
                  eff_name AS filename, size, capture_date::text AS asserted_date,
                  date_source, _src_file, _loaded_at::text AS loaded_at
           FROM raw_duck.resolved
           UNION ALL
           SELECT 'raw_misc.merge_plan', coalesce(src, relative_path),
                  regexp_replace(coalesce(relative_path, src), '^.*/', ''),
                  size_src, mtime_src::text, 'mtime_src', _src_file,
                  _loaded_at::text
           FROM raw_misc.merge_plan
           UNION ALL
           SELECT 'raw_misc.merge_plan', coalesce(dst, relative_path),
                  regexp_replace(coalesce(relative_path, dst), '^.*/', ''),
                  size_dst, mtime_dst::text, 'mtime_dst', _src_file,
                  _loaded_at::text
           FROM raw_misc.merge_plan
           ORDER BY source_table, source_path, asserted_date""",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def export_one(spec: ExportSpec, output_dir: Path, host: str, container: str) -> dict[str, object]:
    target = output_dir / f"{spec.name}.csv.gz"
    receipt = output_dir / f"{spec.name}.receipt.json"
    if target.exists() or receipt.exists():
        raise FileExistsError(f"refusing to overwrite existing export: {target}")

    sql = f"COPY ({spec.query}) TO STDOUT WITH (FORMAT csv, HEADER true);\n"
    command = [
        "ssh", host,
        f"docker exec -i {container} psql -U postgres -d casebible "
        "-X -q -v ON_ERROR_STOP=1",
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    process.stdin.write(sql.encode("utf-8"))
    process.stdin.close()

    digest = hashlib.sha256()
    uncompressed_bytes = 0
    with gzip.open(target, "xb", compresslevel=1) as handle:
        for block in iter(lambda: process.stdout.read(1024 * 1024), b""):
            digest.update(block)
            uncompressed_bytes += len(block)
            handle.write(block)
    stderr = process.stderr.read().decode("utf-8", errors="replace")
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(
            f"PG18 export {spec.name} failed with exit {return_code}: {stderr[-2000:]}"
        )

    result: dict[str, object] = {
        "name": spec.name,
        "source": "casebible-pg18",
        "source_host": host,
        "source_container": container,
        "exported_at": utc_now(),
        "sha256_uncompressed_csv": digest.hexdigest(),
        "uncompressed_bytes": uncompressed_bytes,
        "compressed_bytes": target.stat().st_size,
        "output": str(target.resolve()),
    }
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--host", default="ovh-files")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--only", action="append", choices=[item.name for item in EXPORTS])
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    selected = [item for item in EXPORTS if not args.only or item.name in args.only]
    results = [export_one(item, output_dir, args.host, args.container) for item in selected]
    summary = {
        "schema": "consignatio-pg18-metadata-export-v1",
        "created_at": utc_now(),
        "exports": results,
    }
    manifest = output_dir / "export-manifest.json"
    if manifest.exists():
        raise FileExistsError(f"refusing to overwrite export manifest: {manifest}")
    manifest.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
