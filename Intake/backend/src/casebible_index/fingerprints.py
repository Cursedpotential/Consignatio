from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Literal
from uuid import uuid4

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from blake3 import blake3

from .config import SUPPORTED_EXTENSIONS, Settings
from .extractors import extract_text
from .inventory import newest_inventory
from .parquet_store import parquet_bytes, write_immutable

FINGERPRINT_SCHEMA_VERSION = "casebible-file-fingerprint-v2"
DEDUP_RULES_VERSION = "casebible-dedup-candidate-v1"
HASH_BUFFER_SIZE = 8 * 1024 * 1024
SAMPLE_SIZE = 64 * 1024
DEFAULT_TEXT_FINGERPRINT_MAX_BYTES = 64 * 1024 * 1024
TOKEN_RE = re.compile(r"[\w'-]+", re.UNICODE)

HashScope = Literal["all", "dedup-candidates"]


def _sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


@dataclass(frozen=True)
class FingerprintResult:
    run_dir: Path
    files_path: Path
    exact_groups_path: Path
    exact_members_path: Path
    text_equivalent_groups_path: Path
    near_text_path: Path
    package_manifests_path: Path | None
    package_groups_path: Path | None
    file_count: int
    hashed_count: int
    reused_count: int
    skipped_count: int
    error_count: int


def newest_fingerprints(output_dir: Path) -> Path | None:
    candidates = sorted((output_dir / "fingerprints").glob("*/files.parquet"), reverse=True)
    return candidates[0] if candidates else None


def _compatible_previous(path: Path | None, inventory_path: Path) -> Path | None:
    if path is None:
        return None
    try:
        previous_schema = pq.read_schema(path)
        inventory_schema = pq.read_schema(inventory_path)
    except (OSError, pa.ArrowInvalid):
        return None
    version = (previous_schema.metadata or {}).get(b"casebible.schema", b"").decode()
    required = {"source_modified_ns", "sha256", "text_simhash64"}
    if version != FINGERPRINT_SCHEMA_VERSION or not required.issubset(previous_schema.names):
        return None
    if "source_modified_ns" not in inventory_schema.names:
        return None
    return path


def newest_atomic_run(output_dir: Path) -> Path | None:
    candidates = sorted(
        (path.parent for path in (output_dir / "atomic").glob("*/units.parquet")), reverse=True
    )
    return candidates[0] if candidates else None


def _sample_fingerprint(path: Path, byte_size: int) -> str:
    digest = hashlib.blake2b(digest_size=32, person=b"cb-sample-v1")
    digest.update(byte_size.to_bytes(8, "big", signed=False))
    if byte_size == 0:
        return digest.hexdigest()
    offsets = sorted({0, max(0, (byte_size - SAMPLE_SIZE) // 2), max(0, byte_size - SAMPLE_SIZE)})
    with path.open("rb", buffering=0) as handle:
        for offset in offsets:
            handle.seek(offset)
            value = handle.read(SAMPLE_SIZE)
            digest.update(offset.to_bytes(8, "big", signed=False))
            digest.update(len(value).to_bytes(8, "big", signed=False))
            digest.update(value)
    return digest.hexdigest()


def _exact_hashes(path: Path) -> tuple[str, str, str]:
    md5_digest = hashlib.md5(usedforsecurity=False)
    sha256_digest = hashlib.sha256()
    blake3_digest = blake3()
    with path.open("rb", buffering=0) as handle:
        while block := handle.read(HASH_BUFFER_SIZE):
            md5_digest.update(block)
            sha256_digest.update(block)
            blake3_digest.update(block)
    return md5_digest.hexdigest(), sha256_digest.hexdigest(), blake3_digest.hexdigest()


def normalize_text_for_fingerprint(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(normalized.split())


def text_simhash64(text: str) -> int | None:
    tokens = TOKEN_RE.findall(text)
    if not tokens:
        return None
    vector = [0] * 64
    for token, weight in Counter(tokens).items():
        token_hash = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")
        for bit in range(64):
            vector[bit] += weight if token_hash & (1 << bit) else -weight
    result = 0
    for bit, value in enumerate(vector):
        if value >= 0:
            result |= 1 << bit
    return result


def _text_fingerprints(path: Path, byte_size: int, maximum: int) -> dict[str, object]:
    if path.suffix.casefold() not in SUPPORTED_EXTENSIONS:
        return {"text_fingerprint_status": "unsupported"}
    if byte_size > maximum:
        return {"text_fingerprint_status": "skipped_size_limit"}
    try:
        content = path.read_bytes()
        extracted = extract_text(path, content)
    except Exception as exc:  # extraction is best-effort; exact hashes remain authoritative
        return {
            "text_fingerprint_status": "extraction_error",
            "text_fingerprint_error": type(exc).__name__,
        }
    if extracted.status != "indexed":
        return {
            "text_fingerprint_status": extracted.status,
            "extraction_method": extracted.extraction_method,
        }
    normalized = normalize_text_for_fingerprint(extracted.text)
    if not normalized:
        return {
            "text_fingerprint_status": "skipped_no_text",
            "extraction_method": extracted.extraction_method,
            "text_char_count": len(extracted.text),
        }
    return {
        "text_fingerprint_status": "fingerprinted",
        "normalized_text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "text_simhash64": text_simhash64(normalized),
        "text_char_count": len(extracted.text),
        "extraction_method": extracted.extraction_method,
    }


def _schema() -> pa.Schema:
    return pa.schema(
        [
            ("source_id", pa.string()),
            ("relative_path", pa.string()),
            ("filename", pa.string()),
            ("extension", pa.string()),
            ("byte_size", pa.int64()),
            ("source_created_at", pa.timestamp("us", tz="UTC")),
            ("source_modified_at", pa.timestamp("us", tz="UTC")),
            ("source_modified_ns", pa.int64()),
            ("is_symlink", pa.bool_()),
            ("hash_scope", pa.string()),
            ("hash_status", pa.string()),
            ("hash_error", pa.string()),
            ("md5", pa.string()),
            ("sha256", pa.string()),
            ("blake3", pa.string()),
            ("sample_blake2b_256", pa.string()),
            ("text_fingerprint_status", pa.string()),
            ("text_fingerprint_error", pa.string()),
            ("normalized_text_sha256", pa.string()),
            ("text_simhash64", pa.uint64()),
            ("text_char_count", pa.int64()),
            ("extraction_method", pa.string()),
            ("copy_quality", pa.string()),
            ("reused", pa.bool_()),
            ("captured_at", pa.timestamp("us", tz="UTC")),
            ("schema_version", pa.string()),
        ],
        metadata={
            b"casebible.schema": FINGERPRINT_SCHEMA_VERSION.encode(),
            b"casebible.authority": b"read-only derived fingerprints; no disposition authority",
            b"casebible.custody": b"sha256 is H1 rawbytes; md5 is compatibility dedup only",
        },
    )


def _iter_inventory_rows(
    inventory_path: Path, previous_path: Path | None, batch_size: int
):
    connection = duckdb.connect(":memory:")
    previous_join = ""
    previous_columns = ""
    parameters: list[str] = [str(inventory_path)]
    if previous_path is not None:
        previous_join = """
            LEFT JOIN read_parquet(?) p
              ON p.source_id = i.source_id
             AND p.relative_path = i.relative_path
             AND p.byte_size = i.byte_size
             AND p.source_modified_at = i.source_modified_at
             AND p.source_modified_ns = i.source_modified_ns
             AND p.is_symlink = i.is_symlink
        """
        parameters.append(str(previous_path))
        previous_columns = """,
            p.hash_status AS previous_hash_status,
            p.md5 AS previous_md5,
            p.sha256 AS previous_sha256,
            p.blake3 AS previous_blake3,
            p.sample_blake2b_256 AS previous_sample,
            p.text_fingerprint_status AS previous_text_status,
            p.text_fingerprint_error AS previous_text_error,
            p.normalized_text_sha256 AS previous_normalized_sha256,
            p.text_simhash64 AS previous_simhash,
            p.text_char_count AS previous_text_char_count,
            p.extraction_method AS previous_extraction_method,
            p.copy_quality AS previous_copy_quality
        """
    else:
        previous_columns = """,
            NULL::VARCHAR AS previous_hash_status,
            NULL::VARCHAR AS previous_md5,
            NULL::VARCHAR AS previous_sha256,
            NULL::VARCHAR AS previous_blake3,
            NULL::VARCHAR AS previous_sample,
            NULL::VARCHAR AS previous_text_status,
            NULL::VARCHAR AS previous_text_error,
            NULL::VARCHAR AS previous_normalized_sha256,
            NULL::UBIGINT AS previous_simhash,
            NULL::BIGINT AS previous_text_char_count,
            NULL::VARCHAR AS previous_extraction_method,
            NULL::VARCHAR AS previous_copy_quality
        """
    query = f"""
        WITH duplicate_sizes AS (
            SELECT byte_size
            FROM read_parquet(?)
            WHERE NOT is_symlink
            GROUP BY byte_size
            HAVING count(*) > 1
        )
        SELECT i.*,
               d.byte_size IS NOT NULL AS duplicate_size_candidate
               {previous_columns}
        FROM read_parquet(?) i
        LEFT JOIN duplicate_sizes d USING (byte_size)
        {previous_join}
        ORDER BY i.relative_path
    """
    parameters = [str(inventory_path), *parameters]
    try:
        reader = connection.execute(query, parameters).to_arrow_reader(batch_size=batch_size)
        yield from reader
    finally:
        connection.close()


def _source_path(source_dir: Path, relative_path: str) -> Path:
    path = source_dir.joinpath(*PurePosixPath(relative_path).parts)
    if not path.resolve(strict=False).is_relative_to(source_dir.resolve()):
        raise ValueError("inventory path escapes the configured source directory")
    return path


def _fingerprint_row(
    row: dict[str, object],
    *,
    settings: Settings,
    scope: HashScope,
    captured_at: datetime,
    text_max_bytes: int,
) -> dict[str, object]:
    result = {
        key: row.get(key)
        for key in (
            "source_id",
            "relative_path",
            "filename",
            "extension",
            "byte_size",
            "source_created_at",
            "source_modified_at",
            "source_modified_ns",
            "is_symlink",
        )
    }
    result.update(
        {
            "hash_scope": scope,
            "hash_status": None,
            "copy_quality": "bad_zero_byte" if int(row["byte_size"] or 0) == 0 else "unknown",
            "reused": False,
            "captured_at": captured_at,
            "schema_version": FINGERPRINT_SCHEMA_VERSION,
        }
    )
    if bool(row["is_symlink"]):
        result["hash_status"] = "skipped_symlink"
        return result
    if scope == "dedup-candidates" and not bool(row["duplicate_size_candidate"]):
        result["hash_status"] = "skipped_unique_size"
        return result
    if row.get("previous_hash_status") == "hashed":
        result.update(
            {
                "hash_status": "hashed",
                "md5": row.get("previous_md5"),
                "sha256": row.get("previous_sha256"),
                "blake3": row.get("previous_blake3"),
                "sample_blake2b_256": row.get("previous_sample"),
                "text_fingerprint_status": row.get("previous_text_status"),
                "text_fingerprint_error": row.get("previous_text_error"),
                "normalized_text_sha256": row.get("previous_normalized_sha256"),
                "text_simhash64": row.get("previous_simhash"),
                "text_char_count": row.get("previous_text_char_count"),
                "extraction_method": row.get("previous_extraction_method"),
                "copy_quality": row.get("previous_copy_quality") or result["copy_quality"],
                "reused": True,
            }
        )
        return result

    path = _source_path(settings.source_dir, str(row["relative_path"]))
    try:
        before = path.lstat()
        expected_size = int(row["byte_size"] or 0)
        raw_modified_ns = row.get("source_modified_ns")
        changed = before.st_size != expected_size
        if raw_modified_ns is not None:
            changed = changed or before.st_mtime_ns != int(raw_modified_ns)
        else:
            changed = changed or datetime.fromtimestamp(before.st_mtime, tz=UTC) != row.get(
                "source_modified_at"
            )
        if changed:
            result["hash_status"] = "stat_changed"
            result["hash_error"] = "size_or_modified_time_changed_since_inventory"
            return result
        result["sample_blake2b_256"] = _sample_fingerprint(path, expected_size)
        result["md5"], result["sha256"], result["blake3"] = _exact_hashes(path)
        after = path.lstat()
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            result.update(
                {
                    "hash_status": "stat_changed_during_hash",
                    "hash_error": "source_changed_while_being_read",
                    "md5": None,
                    "sha256": None,
                    "blake3": None,
                }
            )
            return result
        result.update(_text_fingerprints(path, expected_size, text_max_bytes))
        result["hash_status"] = "hashed"
        result["copy_quality"] = "bad_zero_byte" if expected_size == 0 else "good_unverified"
    except (OSError, ValueError) as exc:
        result["hash_status"] = "unreadable"
        result["hash_error"] = type(exc).__name__
    return result


def _write_dedup_reports(run_dir: Path, files_path: Path, near_distance: int) -> tuple[Path, ...]:
    groups_path = run_dir / "exact_groups.parquet"
    members_path = run_dir / "exact_members.parquet"
    text_groups_path = run_dir / "text_equivalent_groups.parquet"
    near_path = run_dir / "near_text_candidates.parquet"
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            f"CREATE VIEW f AS SELECT * FROM read_parquet('{_sql_path(files_path)}')"
        )
        connection.execute(
            f"""
            COPY (
                SELECT 'sha256:' || sha256 AS exact_group_id, sha256, any_value(md5) AS md5,
                       any_value(blake3) AS blake3, count(*)::BIGINT AS member_count,
                       sum(byte_size)::HUGEINT AS total_member_bytes,
                       bool_and(copy_quality = 'good_unverified') AS exact_identity_proposable,
                       false AS canonical_selection_allowed,
                       'review_required' AS review_state,
                       '{DEDUP_RULES_VERSION}' AS rules_version
                FROM f
                WHERE hash_status = 'hashed' AND sha256 IS NOT NULL
                GROUP BY sha256 HAVING count(*) > 1
                ORDER BY member_count DESC, sha256
            ) TO '{groups_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
        connection.execute(
            f"""
            COPY (
                SELECT 'sha256:' || f.sha256 AS exact_group_id, f.source_id, f.relative_path,
                       f.byte_size, f.md5, f.sha256, f.blake3, f.copy_quality,
                       'review_required' AS dedup_disposition,
                       'No canonical selected; source remains unchanged' AS disposition_note,
                       '{DEDUP_RULES_VERSION}' AS rules_version
                FROM f JOIN read_parquet('{groups_path.as_posix()}') g USING (sha256)
                ORDER BY exact_group_id, relative_path
            ) TO '{members_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
        connection.execute(
            f"""
            COPY (
                SELECT 'normalized-text-sha256:' || normalized_text_sha256 AS text_group_id,
                       normalized_text_sha256, count(*)::BIGINT AS member_count,
                       count(DISTINCT sha256)::BIGINT AS distinct_binary_count,
                       'review_required' AS review_state,
                       '{DEDUP_RULES_VERSION}' AS rules_version
                FROM f
                WHERE text_fingerprint_status = 'fingerprinted'
                  AND normalized_text_sha256 IS NOT NULL
                GROUP BY normalized_text_sha256 HAVING count(*) > 1
                ORDER BY member_count DESC, normalized_text_sha256
            ) TO '{text_groups_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
        connection.execute(
            f"""
            COPY (
                WITH text_files AS (
                    SELECT relative_path, sha256, normalized_text_sha256, text_simhash64
                    FROM f
                    WHERE text_fingerprint_status = 'fingerprinted' AND text_simhash64 IS NOT NULL
                ), bands AS (
                    SELECT *, 0 AS band_no, text_simhash64 & 65535 AS band FROM text_files
                    UNION ALL SELECT *, 1, (text_simhash64 >> 16) & 65535 FROM text_files
                    UNION ALL SELECT *, 2, (text_simhash64 >> 32) & 65535 FROM text_files
                    UNION ALL SELECT *, 3, (text_simhash64 >> 48) & 65535 FROM text_files
                ), bounded_bands AS (
                    SELECT band_no, band FROM bands GROUP BY ALL HAVING count(*) BETWEEN 2 AND 500
                ), pairs AS (
                    SELECT DISTINCT a.relative_path AS left_path, b.relative_path AS right_path,
                           a.sha256 AS left_sha256, b.sha256 AS right_sha256,
                           a.normalized_text_sha256 AS left_normalized_text_sha256,
                           b.normalized_text_sha256 AS right_normalized_text_sha256,
                           bit_count(xor(a.text_simhash64, b.text_simhash64))::INTEGER
                               AS hamming_distance
                    FROM bands a
                    JOIN bounded_bands bb USING (band_no, band)
                    JOIN bands b USING (band_no, band)
                    WHERE a.relative_path < b.relative_path
                )
                SELECT *, 'review_required' AS review_state,
                       '{DEDUP_RULES_VERSION}' AS rules_version
                FROM pairs
                WHERE left_normalized_text_sha256 <> right_normalized_text_sha256
                  AND hamming_distance <= {near_distance}
                ORDER BY hamming_distance, left_path, right_path
            ) TO '{near_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
    finally:
        connection.close()
    return groups_path, members_path, text_groups_path, near_path


def _write_package_manifests(
    run_dir: Path, files_path: Path, atomic_run: Path | None, captured_at: datetime
) -> Path | None:
    if atomic_run is None:
        return None
    units_path = atomic_run / "units.parquet"
    if not units_path.exists():
        return None
    connection = duckdb.connect(":memory:")
    rows: list[dict[str, object]] = []
    schema = pa.schema(
        [
            ("unit_id", pa.string()),
            ("root_path", pa.string()),
            ("unit_type", pa.string()),
            ("platform", pa.string()),
            ("member_count", pa.int64()),
            ("hashed_member_count", pa.int64()),
            ("total_bytes", pa.int64()),
            ("zero_byte_count", pa.int64()),
            ("error_count", pa.int64()),
            ("manifest_sha256", pa.string()),
            ("manifest_state", pa.string()),
            ("review_state", pa.string()),
            ("atomic_run", pa.string()),
            ("captured_at", pa.timestamp("us", tz="UTC")),
            ("rules_version", pa.string()),
        ],
        metadata={
            b"casebible.authority": b"package fingerprint candidate; no selection authority"
        },
    )
    try:
        cursor = connection.execute(
            """
            SELECT u.unit_id, u.root_path, u.unit_type, u.platform,
                   f.relative_path, f.byte_size, f.hash_status, f.sha256, f.copy_quality
            FROM read_parquet(?) u
            LEFT JOIN read_parquet(?) f
              ON f.relative_path = u.root_path
              OR starts_with(f.relative_path, u.root_path || '/')
            ORDER BY u.unit_id, f.relative_path
            """,
            [str(units_path), str(files_path)],
        )
        current: str | None = None
        digest = hashlib.sha256()
        accumulator: dict[str, object] = {}

        def flush() -> None:
            if current is None:
                return
            member_count = int(accumulator["member_count"])
            hashed_count = int(accumulator["hashed_member_count"])
            complete = member_count > 0 and hashed_count == member_count
            rows.append(
                {
                    **accumulator,
                    "manifest_sha256": digest.hexdigest() if complete else None,
                    "manifest_state": "complete" if complete else "partial",
                    "review_state": "review_required",
                    "atomic_run": str(atomic_run),
                    "captured_at": captured_at,
                    "rules_version": DEDUP_RULES_VERSION,
                }
            )

        while batch := cursor.fetchmany(50_000):
            for unit_id, root, unit_type, platform, path, size, status, sha256, quality in batch:
                if unit_id != current:
                    flush()
                    current = unit_id
                    digest = hashlib.sha256()
                    accumulator = {
                        "unit_id": unit_id,
                        "root_path": root,
                        "unit_type": unit_type,
                        "platform": platform,
                        "member_count": 0,
                        "hashed_member_count": 0,
                        "total_bytes": 0,
                        "zero_byte_count": 0,
                        "error_count": 0,
                    }
                if path is None:
                    continue
                accumulator["member_count"] = int(accumulator["member_count"]) + 1
                accumulator["total_bytes"] = int(accumulator["total_bytes"]) + int(size or 0)
                if quality == "bad_zero_byte":
                    accumulator["zero_byte_count"] = int(accumulator["zero_byte_count"]) + 1
                if status == "hashed" and sha256:
                    accumulator["hashed_member_count"] = int(
                        accumulator["hashed_member_count"]
                    ) + 1
                    relative_member = str(PurePosixPath(path).relative_to(PurePosixPath(root)))
                    manifest_line = (
                        f"{len(relative_member)}:{relative_member}|{int(size or 0)}|{sha256}\n"
                    )
                    digest.update(manifest_line.encode())
                else:
                    accumulator["error_count"] = int(accumulator["error_count"]) + 1
        flush()
    finally:
        connection.close()
    path = run_dir / "package_manifests.parquet"
    write_immutable(path, parquet_bytes(pa.Table.from_pylist(rows, schema=schema)))
    return path


def _write_package_groups(run_dir: Path, manifests_path: Path | None) -> Path | None:
    if manifests_path is None:
        return None
    path = run_dir / "package_exact_groups.parquet"
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            f"""
            COPY (
                SELECT 'package-sha256:' || manifest_sha256 AS package_group_id,
                       manifest_sha256, count(*)::BIGINT AS unit_count,
                       list(unit_id ORDER BY unit_id) AS unit_ids,
                       list(root_path ORDER BY root_path) AS root_paths,
                       'review_required' AS review_state,
                       '{DEDUP_RULES_VERSION}' AS rules_version
                FROM read_parquet('{_sql_path(manifests_path)}')
                WHERE manifest_state = 'complete' AND manifest_sha256 IS NOT NULL
                GROUP BY manifest_sha256 HAVING count(*) > 1
                ORDER BY unit_count DESC, manifest_sha256
            ) TO '{path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """,
        )
    finally:
        connection.close()
    return path


def write_fingerprints(
    settings: Settings,
    inventory_path: Path | None = None,
    *,
    scope: HashScope = "all",
    text_max_bytes: int = DEFAULT_TEXT_FINGERPRINT_MAX_BYTES,
    near_distance: int = 6,
    batch_size: int = 10_000,
) -> FingerprintResult:
    if scope not in {"all", "dedup-candidates"}:
        raise ValueError(f"Unsupported hash scope: {scope}")
    inventory = inventory_path or newest_inventory(settings.output_dir)
    if inventory is None:
        raise FileNotFoundError("No inventory snapshot exists; run inventory first")
    captured_at = datetime.now(UTC)
    run_id = captured_at.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid4().hex[:8]
    run_dir = settings.output_dir / "fingerprints" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    files_path = run_dir / "files.parquet"
    previous = _compatible_previous(newest_fingerprints(settings.output_dir), inventory)
    writer = pq.ParquetWriter(files_path, _schema(), compression="zstd")
    buffer: list[dict[str, object]] = []
    file_count = hashed_count = reused_count = skipped_count = error_count = 0
    try:
        for record_batch in _iter_inventory_rows(inventory, previous, batch_size):
            for inventory_row in record_batch.to_pylist():
                row = _fingerprint_row(
                    inventory_row,
                    settings=settings,
                    scope=scope,
                    captured_at=captured_at,
                    text_max_bytes=text_max_bytes,
                )
                buffer.append(row)
                file_count += 1
                if row["hash_status"] == "hashed":
                    hashed_count += 1
                elif str(row["hash_status"]).startswith("skipped"):
                    skipped_count += 1
                else:
                    error_count += 1
                if row["reused"]:
                    reused_count += 1
                if len(buffer) >= batch_size:
                    writer.write_table(pa.Table.from_pylist(buffer, schema=_schema()))
                    buffer.clear()
        if buffer:
            writer.write_table(pa.Table.from_pylist(buffer, schema=_schema()))
    finally:
        writer.close()
    groups, members, text_groups, near = _write_dedup_reports(
        run_dir, files_path, near_distance
    )
    package_manifests = _write_package_manifests(
        run_dir, files_path, newest_atomic_run(settings.output_dir), captured_at
    )
    package_groups = _write_package_groups(run_dir, package_manifests)
    return FingerprintResult(
        run_dir=run_dir,
        files_path=files_path,
        exact_groups_path=groups,
        exact_members_path=members,
        text_equivalent_groups_path=text_groups,
        near_text_path=near,
        package_manifests_path=package_manifests,
        package_groups_path=package_groups,
        file_count=file_count,
        hashed_count=hashed_count,
        reused_count=reused_count,
        skipped_count=skipped_count,
        error_count=error_count,
    )
