"""Build a non-destructive migration ledger from rclone CSV inventories."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import chain
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator, Mapping, Sequence

from .schema import SCHEMA_SQL, SCHEMA_VERSION

REQUIRED_COLUMNS = ("bucket", "path", "size", "md5", "modtime", "mimetype")
RCLONE_PSHTM_COLUMNS = ("path", "size", "md5", "modtime", "mimetype")
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
RULE_SET = "casebible-path-observations"
RULE_VERSION = "2026-09-12.v1"
FINGERPRINT_ASSERTION_VERSION = "source-bound-sha256.v1"
REPRESENTATIVE_RULE = "latest-snapshot-then-utf8-ordinal(bucket,path,row_number,occurrence_id).v2"
ALLOWED_TRANSITIONS = {
    "planned": {"queued", "copying", "skipped_existing_verified", "permanent_error"},
    "queued": {"copying", "retryable_error", "permanent_error"},
    "copying": {"copied", "retryable_error", "permanent_error"},
    "copied": {"verified", "retryable_error", "permanent_error"},
    "retryable_error": {"queued", "copying", "permanent_error"},
    "verified": set(),
    "skipped_existing_verified": set(),
    "permanent_error": set(),
    "held_missing_hash": set(),
    "held_invalid_hash": set(),
    "held_md5_size_conflict": set(),
    "held_hash_error": set(),
    "held_hash_unsupported": set(),
    "held_sha256_assertion_conflict": set(),
    "held_sha256_size_conflict": set(),
    "held_source_location_drift": set(),
    "held_unsafe_path": set(),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *parts: object) -> str:
    serialized = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return f"{prefix}:{_sha256_text(serialized)}"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _captured_at_from_name(path: Path) -> str:
    name = path.name
    patterns = (
        (r"(?<!\d)(\d{8})[T_-]?(\d{6})Z?(?!\d)", "%Y%m%d%H%M%S"),
        (r"(?<!\d)(\d{4}-\d{2}-\d{2})[T_](\d{2})[-:]?(\d{2})[-:]?(\d{2})Z?(?!\d)", None),
    )
    match = re.search(patterns[0][0], name)
    if match:
        parsed = datetime.strptime("".join(match.groups()), patterns[0][1]).replace(
            tzinfo=timezone.utc
        )
        return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")
    match = re.search(patterns[1][0], name)
    if match:
        parsed = datetime.fromisoformat(f"{match.group(1)}T{match.group(2)}:{match.group(3)}:{match.group(4)}+00:00")
        return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")
    raise ValueError(f"inventory filename has no supported UTC timestamp: {path.name}")


def _normalized_relpath(bucket: str, object_path: str) -> str:
    bucket_part = bucket.strip().strip("/")
    object_part = object_path.replace("\\", "/").lstrip("/")
    return f"{bucket_part}/{object_part}" if object_part else bucket_part


def _path_is_safe_for_files_from(path: str) -> bool:
    return bool(path) and "\n" not in path and "\r" not in path and "\x00" not in path


def _payload_source_hold_reason(object_path: str) -> str | None:
    """Return why a source locator cannot enter an executable payload mapping."""
    if (
        not object_path
        or object_path.startswith(("/", "#"))
        or "\\" in object_path
        or "\n" in object_path
        or "\r" in object_path
        or "\x00" in object_path
    ):
        return "held_unsafe_path"
    # Inspect the literal segments before PurePosixPath can normalize away an
    # empty or dot component that would make the runner address a different key.
    parts = tuple(object_path.split("/"))
    if any(part in {"", ".", ".."} for part in parts):
        return "held_unsafe_path"
    if parts and parts[0].casefold() == "_system":
        return "held_control_path"
    return None


def _category(row: Mapping[str, object]) -> tuple[str, float, dict[str, str]]:
    path = str(row["object_path"])
    mime = str(row["mimetype_raw"] or "").casefold()
    lower = path.casefold()
    suffixes = [suffix.casefold() for suffix in PurePosixPath(lower).suffixes]
    ext = suffixes[-1] if suffixes else ""
    if mime.startswith("image/") or ext in {".jpg", ".jpeg", ".png", ".gif", ".heic", ".webp", ".tiff"}:
        return "image", 0.94, {"basis": "mime_or_extension"}
    if mime.startswith("video/") or ext in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
        return "video", 0.94, {"basis": "mime_or_extension"}
    if mime.startswith("audio/") or ext in {".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg"}:
        return "audio", 0.94, {"basis": "mime_or_extension"}
    if mime == "application/pdf" or ext == ".pdf":
        return "pdf", 0.97, {"basis": "mime_or_extension"}
    if ext in {".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".html", ".htm"} or mime.startswith("text/"):
        return "document", 0.82, {"basis": "mime_or_extension"}
    if ext in {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2", ".xz"}:
        return "archive", 0.91, {"basis": "extension"}
    if ext in {".json", ".jsonl", ".csv", ".tsv", ".xml", ".sqlite", ".db", ".parquet"}:
        return "structured_data", 0.86, {"basis": "extension"}
    if ext in {".py", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".sql", ".toml", ".yaml", ".yml"}:
        return "source_code", 0.85, {"basis": "extension"}
    return "unknown", 0.25, {"basis": "insufficient_path_metadata"}


def _prefix_through(parts: Sequence[str], index: int) -> str:
    return "/".join(parts[: index + 1])


def _atomic_hints(object_path: str) -> list[tuple[str, str, float, dict[str, str]]]:
    normalized = object_path.replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part]
    folded = [part.casefold() for part in parts]
    hints: list[tuple[str, str, float, dict[str, str]]] = []
    basename = folded[-1] if folded else ""

    for index, segment in enumerate(folded):
        if segment == "takeout" or segment.startswith("takeout-") or segment == "google takeout":
            hints.append(("google_takeout", _prefix_through(parts, index), 0.90, {"marker": parts[index]}))
        if segment in {"facebook", "facebook export", "your_facebook_activity"} or segment.startswith("facebook-"):
            hints.append(("facebook_export", _prefix_through(parts, index), 0.82, {"marker": parts[index]}))
        if segment in {"chatgpt", "chatgpt export"} or segment.startswith("chatgpt-"):
            hints.append(("chatgpt_export", _prefix_through(parts, index), 0.84, {"marker": parts[index]}))
        if segment in {"imessage", "messages", "message attachments"}:
            hints.append(("message_export", _prefix_through(parts, index), 0.55, {"marker": parts[index]}))

    parent = "/".join(parts[:-1])
    if basename == "conversations.json":
        hints.append(("chatgpt_export", parent, 0.98, {"marker": "conversations.json"}))
    if basename == "chat.db":
        hints.append(("imessage_export", parent, 0.98, {"marker": "chat.db"}))
    if len(folded) >= 2 and folded[-2] == ".git" and basename in {"config", "head"}:
        hints.append(("git_repository", "/".join(parts[:-2]), 0.99, {"marker": f".git/{parts[-1]}"}))
    if basename in {"cargo.toml", "go.mod", "pyproject.toml", "package.json", "pom.xml"}:
        hints.append(("development_repository", parent, 0.72, {"marker": parts[-1]}))

    # Preserve nested hints; remove only exact duplicates produced by overlapping markers.
    unique: dict[tuple[str, str], tuple[str, str, float, dict[str, str]]] = {}
    for hint in hints:
        unique[(hint[0], hint[1])] = hint
    return sorted(unique.values(), key=lambda item: (item[1].encode("utf-8"), item[0]))


@dataclass(frozen=True)
class BuildResult:
    generation_id: str
    inventory_count: int
    occurrence_count: int
    sha256_verified_content_count: int
    md5_candidate_content_count: int
    held_content_count: int
    files_from_count: int
    parquet_written: bool


@dataclass(frozen=True)
class ImportPartitionResult:
    partition_id: str
    source_path: str
    row_count: int
    bound_count: int
    held_count: int
    already_imported: bool


@dataclass(frozen=True)
class BridgeFinalizationResult:
    finalization_id: str
    partition_count: int
    record_count: int
    bridge_group_count: int
    already_finalized: bool


class ManifestBuilder:
    def __init__(self, ledger_path: Path | str):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.ledger_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_SQL)
        self.connection.execute(
            "INSERT OR IGNORE INTO schema_version(version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, _utc_now()),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "ManifestBuilder":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _transfer_item_accepts_bridge_authority(self) -> bool:
        definition = self.connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'transfer_item'"
        ).fetchone()
        return bool(
            definition
            and "sha256_via_conflict_free_md5_size_bridge" in (definition["sql"] or "")
        )

    def ingest(
        self,
        inventory_paths: Iterable[Path | str],
        source_bucket: str | None = None,
    ) -> int:
        ingested = 0
        for raw_path in inventory_paths:
            path = Path(raw_path).resolve()
            if not path.name.casefold().endswith(".csv.gz"):
                raise ValueError(f"inventory must be a .csv.gz file: {path}")
            source_sha256 = _file_sha256(path)
            inventory_id = f"inventory:{source_sha256}"
            exists = self.connection.execute(
                "SELECT 1 FROM inventory_batch WHERE inventory_id = ?", (inventory_id,)
            ).fetchone()
            if exists:
                continue
            captured_at = _captured_at_from_name(path)
            with self.connection:
                self.connection.execute(
                    """INSERT INTO inventory_batch(
                           inventory_id, source_path, source_sha256, captured_at,
                           ingested_at, row_count
                       ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (inventory_id, str(path), source_sha256, captured_at, _utc_now(), 0),
                )
                row_count = 0
                for row_number, row in enumerate(
                    self._read_inventory(path, source_bucket=source_bucket), start=1
                ):
                    md5_raw = row["md5"]
                    md5_candidate = md5_raw.strip()
                    md5_valid = bool(MD5_RE.fullmatch(md5_candidate))
                    md5_normalized = md5_candidate.casefold() if md5_valid else None
                    md5_state = self._md5_state(md5_candidate, md5_valid)
                    occurrence_id = _stable_id("occ", inventory_id, row_number, row)
                    self.connection.execute(
                        """INSERT INTO occurrence(
                               occurrence_id, inventory_id, row_number, bucket,
                               object_path, byte_size, md5_raw, md5_normalized,
                               md5_valid, md5_state, modtime_raw, mimetype_raw
                           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            occurrence_id,
                            inventory_id,
                            row_number,
                            row["bucket"],
                            row["path"],
                            int(row["size"]),
                            md5_raw or None,
                            md5_normalized,
                            int(md5_valid),
                            md5_state,
                            row["modtime"] or None,
                            row["mimetype"] or None,
                        ),
                    )
                    row_count = row_number
                self.connection.execute(
                    "UPDATE inventory_batch SET row_count = ? WHERE inventory_id = ?",
                    (row_count, inventory_id),
                )
            ingested += 1
        self._reconcile_identities()
        self._assert_path_observations()
        return ingested

    @staticmethod
    def _md5_state(md5_raw: str, md5_valid: bool) -> str:
        if md5_valid:
            return "valid"
        folded = md5_raw.casefold()
        if not folded:
            return "empty"
        if folded == "error":
            return "error"
        if folded == "unsupported":
            return "unsupported"
        return "invalid"

    @staticmethod
    def _read_inventory(
        path: Path,
        source_bucket: str | None = None,
    ) -> Iterator[dict[str, str]]:
        with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                first = next(reader)
            except StopIteration as exc:
                raise ValueError(f"empty inventory: {path}") from exc
            header = [field.strip().casefold() for field in first]
            header_map = {field: index for index, field in enumerate(header)}
            is_normalized = all(column in header_map for column in REQUIRED_COLUMNS)
            if is_normalized:
                records: Iterable[tuple[int, list[str]]] = enumerate(reader, start=2)
            elif len(first) == len(RCLONE_PSHTM_COLUMNS) and source_bucket:
                header_map = {column: index for index, column in enumerate(RCLONE_PSHTM_COLUMNS)}
                records = enumerate(chain((first,), reader), start=1)
            else:
                raise ValueError(
                    "inventory must be a headered bucket,path,size,md5,modtime,mimetype "
                    "CSV or native headerless rclone pshtm CSV with source_bucket"
                )
            for row_number, raw in records:
                if len(raw) != len(header_map):
                    raise ValueError(
                        f"unexpected field count at CSV record {row_number}: "
                        f"expected {len(header_map)}, got {len(raw)}"
                    )
                selected_columns = REQUIRED_COLUMNS if is_normalized else RCLONE_PSHTM_COLUMNS
                row = {
                    column: raw[header_map[column]] or ""
                    for column in selected_columns
                }
                if not is_normalized:
                    row["bucket"] = source_bucket or ""
                if not row["bucket"].strip() or not row["path"]:
                    raise ValueError(f"blank bucket/path at CSV row {row_number}: {path}")
                try:
                    size = int(row["size"].strip())
                except ValueError as exc:
                    raise ValueError(f"invalid size at CSV row {row_number}: {row['size']!r}") from exc
                if size < 0:
                    raise ValueError(f"negative size at CSV row {row_number}: {size}")
                row["size"] = str(size)
                yield row

    def _fingerprint_state(self) -> tuple[int, int, str, str]:
        partitions = self.connection.execute(
            """SELECT partition_id, source_sha256, row_count
               FROM fingerprint_import_partition ORDER BY partition_id"""
        ).fetchall()
        assertions = self.connection.execute(
            """SELECT fingerprint_assertion_id, sha256
               FROM strong_fingerprint_assertion
               ORDER BY fingerprint_assertion_id"""
        ).fetchall()
        partition_digest = _sha256_text(
            "\n".join(
                f"{row['partition_id']}:{row['source_sha256']}:{row['row_count']}"
                for row in partitions
            )
        )
        assertion_digest = _sha256_text(
            "\n".join(
                f"{row['fingerprint_assertion_id']}:{row['sha256']}"
                for row in assertions
            )
        )
        return (
            len(partitions),
            sum(int(row["row_count"]) for row in partitions),
            partition_digest,
            assertion_digest,
        )

    def _active_bridge_finalization(self) -> sqlite3.Row | None:
        partition_count, record_count, partition_digest, assertion_digest = (
            self._fingerprint_state()
        )
        return self.connection.execute(
            """SELECT * FROM sha256_bridge_finalization
               WHERE state = 'frozen'
                 AND observed_partition_count = ?
                 AND observed_record_count = ?
                 AND partition_set_sha256 = ?
                 AND assertion_set_sha256 = ?
               ORDER BY finalized_at DESC, finalization_id
               LIMIT 1""",
            (partition_count, record_count, partition_digest, assertion_digest),
        ).fetchone()

    def _reconcile_identities(self) -> None:
        observed_at = _utc_now()
        bridge_is_current = self._active_bridge_finalization() is not None
        with self.connection:
            self.connection.execute("DROP TABLE IF EXISTS temp.conflicting_md5")
            self.connection.execute(
                """CREATE TEMP TABLE conflicting_md5 AS
                   SELECT md5_normalized AS md5
                   FROM occurrence WHERE md5_valid = 1
                   GROUP BY md5_normalized
                   HAVING COUNT(DISTINCT byte_size) > 1"""
            )
            self.connection.execute("DROP TABLE IF EXISTS temp.occurrence_sha256")
            self.connection.execute(
                """CREATE TEMP TABLE occurrence_sha256 AS
                   SELECT occurrence_id, MIN(sha256) AS sha256,
                          COUNT(DISTINCT sha256) AS sha256_count
                   FROM strong_fingerprint_assertion
                   GROUP BY occurrence_id"""
            )
            self.connection.execute("DROP TABLE IF EXISTS temp.conflicting_sha256_size")
            self.connection.execute(
                """CREATE TEMP TABLE conflicting_sha256_size AS
                   SELECT f.sha256
                   FROM strong_fingerprint_assertion f
                   JOIN occurrence o USING (occurrence_id)
                   GROUP BY f.sha256
                   HAVING COUNT(DISTINCT o.byte_size) > 1"""
            )
            self.connection.execute(
                """UPDATE content_identity
                   SET identity_status = 'md5_size_conflict', fingerprint_required = 1
                   WHERE md5 IN (SELECT md5 FROM conflicting_md5)"""
            )
            bridge_join = (
                """LEFT JOIN sha256_md5_size_bridge bridge
                     ON bridge.md5 = o.md5_normalized
                    AND bridge.byte_size = o.byte_size"""
                if bridge_is_current
                else ""
            )
            bridge_column = "bridge.sha256" if bridge_is_current else "NULL"
            cursor = self.connection.execute(
                f"""SELECT o.occurrence_id, o.md5_raw, o.md5_normalized,
                          o.md5_valid, o.md5_state, o.byte_size,
                          EXISTS(SELECT 1 FROM conflicting_md5 c
                                 WHERE c.md5 = o.md5_normalized) AS has_md5_conflict,
                          s.sha256, COALESCE(s.sha256_count, 0) AS sha256_count,
                          EXISTS(SELECT 1 FROM conflicting_sha256_size c
                                 WHERE c.sha256 = s.sha256) AS has_sha256_size_conflict,
                          {bridge_column} AS bridge_sha256
                   FROM occurrence o
                   LEFT JOIN occurrence_sha256 s USING (occurrence_id)
                   {bridge_join}"""
            )
            while batch := cursor.fetchmany(10_000):
                for row in batch:
                    if row["sha256_count"] == 1 and not row["has_sha256_size_conflict"]:
                        content_id = f"sha256:{row['sha256']}:{row['byte_size']}"
                        kind, status, required = "sha256_verified", "sha256_verified", 0
                        sha256 = row["sha256"]
                        md5, byte_size = row["md5_normalized"], row["byte_size"]
                    elif row["sha256_count"] > 1:
                        content_id = f"pending:{row['occurrence_id'].split(':', 1)[1]}"
                        kind, status, required = (
                            "pending_fingerprint", "sha256_assertion_conflict", 1
                        )
                        sha256 = None
                        md5, byte_size = row["md5_normalized"], row["byte_size"]
                    elif row["sha256_count"] == 1 and row["has_sha256_size_conflict"]:
                        content_id = f"pending:{row['occurrence_id'].split(':', 1)[1]}"
                        kind, status, required = (
                            "pending_fingerprint", "sha256_size_conflict", 1
                        )
                        sha256 = row["sha256"]
                        md5, byte_size = row["md5_normalized"], row["byte_size"]
                    elif row["bridge_sha256"]:
                        content_id = f"sha256:{row['bridge_sha256']}:{row['byte_size']}"
                        kind, status, required = "sha256_verified", "sha256_verified", 0
                        sha256 = row["bridge_sha256"]
                        md5, byte_size = row["md5_normalized"], row["byte_size"]
                    elif row["md5_valid"] and not row["has_md5_conflict"]:
                        content_id = f"md5candidate:{row['md5_normalized']}:{row['byte_size']}"
                        kind, status, required = (
                            "md5_size_candidate", "md5_size_candidate", 1
                        )
                        sha256 = None
                        md5, byte_size = row["md5_normalized"], row["byte_size"]
                    else:
                        content_id = f"pending:{row['occurrence_id'].split(':', 1)[1]}"
                        kind, required = "pending_fingerprint", 1
                        if row["md5_valid"]:
                            status = "md5_size_conflict"
                        elif row["md5_state"] == "error":
                            status = "hash_error"
                        elif row["md5_state"] == "unsupported":
                            status = "hash_unsupported"
                        elif row["md5_raw"]:
                            status = "invalid_hash"
                        else:
                            status = "missing_hash"
                        sha256 = None
                        md5, byte_size = row["md5_normalized"], row["byte_size"]
                    self.connection.execute(
                        """INSERT INTO content_identity(
                               content_id, identity_kind, sha256, md5, byte_size,
                               identity_status, fingerprint_required, created_at
                           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(content_id) DO UPDATE SET
                               identity_status = excluded.identity_status,
                               fingerprint_required = excluded.fingerprint_required""",
                        (
                            content_id, kind, sha256, md5, byte_size,
                            status, required, observed_at,
                        ),
                    )
                    self.connection.execute(
                        "UPDATE occurrence SET content_id = ? WHERE occurrence_id = ?",
                        (content_id, row["occurrence_id"]),
                    )
            candidate_cursor = self.connection.execute(
                """SELECT content_id FROM content_identity
                   WHERE identity_status = 'md5_size_candidate'
                     AND content_id IN (SELECT DISTINCT content_id FROM occurrence)
                   ORDER BY content_id"""
            )
            for candidate in candidate_cursor:
                representative = self.connection.execute(
                    """SELECT o.occurrence_id
                       FROM occurrence o JOIN inventory_batch b USING (inventory_id)
                       WHERE o.content_id = ?
                       ORDER BY b.captured_at DESC, o.bucket COLLATE BINARY,
                                o.object_path COLLATE BINARY, o.row_number,
                                o.occurrence_id
                       LIMIT 1""",
                    (candidate["content_id"],),
                ).fetchone()
                self.connection.execute(
                    """INSERT INTO candidate_representative(
                           content_id, representative_occurrence_id, selection_rule,
                           selection_is_quality_judgment, selected_at
                       ) VALUES (?, ?, ?, 0, ?)
                       ON CONFLICT(content_id) DO UPDATE SET
                           representative_occurrence_id = excluded.representative_occurrence_id,
                           selection_rule = excluded.selection_rule,
                           selected_at = excluded.selected_at""",
                    (
                        candidate["content_id"], representative["occurrence_id"],
                        REPRESENTATIVE_RULE, observed_at,
                    ),
                )

    def record_sha256(
        self,
        occurrence_id: str,
        sha256: str,
        verification_method: str,
        verifier: str,
        verified_at: str,
        source_version: str | None = None,
        source_etag: str | None = None,
    ) -> str:
        """Append a source-bound SHA-256 assertion and refresh derived identity."""
        normalized = sha256.strip().casefold()
        if not SHA256_RE.fullmatch(normalized):
            raise ValueError("sha256 must be exactly 64 hexadecimal characters")
        allowed_methods = {
            "source_sha256_ledger", "streamed_byte_hash", "destination_readback"
        }
        if verification_method not in allowed_methods:
            raise ValueError(f"unsupported verification method: {verification_method}")
        occurrence = self.connection.execute(
            """SELECT occurrence_id, inventory_id, bucket, object_path,
                      byte_size, md5_normalized
               FROM occurrence WHERE occurrence_id = ?""",
            (occurrence_id,),
        ).fetchone()
        if occurrence is None:
            raise KeyError(f"unknown occurrence: {occurrence_id}")
        assertion_id = _stable_id(
            "sha256assert", occurrence_id, normalized, verification_method,
            verifier, verified_at, source_version, source_etag,
            FINGERPRINT_ASSERTION_VERSION,
        )
        with self.connection:
            self.connection.execute(
                """INSERT OR IGNORE INTO strong_fingerprint_assertion(
                       fingerprint_assertion_id, occurrence_id, inventory_id,
                       bucket, object_path, source_version, source_etag,
                       byte_size, observed_md5, sha256, verification_method,
                       verifier, verified_at, assertion_version
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    assertion_id, occurrence_id, occurrence["inventory_id"],
                    occurrence["bucket"], occurrence["object_path"],
                    source_version, source_etag, occurrence["byte_size"],
                    occurrence["md5_normalized"], normalized,
                    verification_method, verifier, verified_at,
                    FINGERPRINT_ASSERTION_VERSION,
                ),
            )
        self._reconcile_identities()
        return assertion_id

    def import_sha256_ledger(
        self,
        partition_paths: Iterable[Path | str],
    ) -> list[ImportPartitionResult]:
        """Import v2 NDJSON partitions without dropping invalid or deferred rows."""
        results: list[ImportPartitionResult] = []
        for raw_path in partition_paths:
            path = Path(raw_path).resolve()
            lower_name = path.name.casefold()
            if not (lower_name.endswith(".ndjson") or lower_name.endswith(".ndjson.gz")):
                raise ValueError(f"ledger partition must be .ndjson or .ndjson.gz: {path}")
            source_sha256 = _file_sha256(path)
            partition_id = f"sha256partition:{source_sha256}"
            existing = self.connection.execute(
                """SELECT row_count, bound_count, held_count
                   FROM fingerprint_import_partition WHERE partition_id = ?""",
                (partition_id,),
            ).fetchone()
            if existing is not None:
                row_count, bound_count, held_count = self._repair_partition_counts(
                    partition_id
                )
                results.append(
                    ImportPartitionResult(
                        partition_id, str(path), row_count,
                        bound_count, held_count, True,
                    )
                )
                continue

            imported_at = _utc_now()
            row_count = 0
            with self.connection:
                self.connection.execute(
                    """INSERT INTO fingerprint_import_partition(
                           partition_id, source_path, source_sha256, imported_at,
                           row_count, bound_count, held_count
                       ) VALUES (?, ?, ?, ?, 0, 0, 0)""",
                    (partition_id, str(path), source_sha256, imported_at),
                )
                opener = gzip.open if lower_name.endswith(".gz") else Path.open
                with opener(path, "rb") as handle:
                    for line_number, raw_line in enumerate(handle, start=1):
                        # rclone concatenate/export jobs place one blank separator
                        # after each partition. It is not an NDJSON record and must
                        # not affect completeness counts or finalization.
                        if not raw_line.strip():
                            continue
                        row_count += 1
                        raw_sha256 = hashlib.sha256(raw_line).hexdigest()
                        try:
                            raw_record = raw_line.decode("utf-8")
                        except UnicodeDecodeError as exc:
                            raw_record = raw_line.decode("utf-8", errors="replace")
                            self._insert_import_assertion(
                                partition_id, line_number, raw_sha256, raw_record,
                                "held_malformed_utf8", {"error": str(exc)}, imported_at,
                            )
                            continue
                        try:
                            payload = json.loads(raw_record)
                        except json.JSONDecodeError as exc:
                            self._insert_import_assertion(
                                partition_id, line_number, raw_sha256, raw_record,
                                "held_malformed_json",
                                {"column": exc.colno, "error": exc.msg}, imported_at,
                            )
                            continue
                        if not isinstance(payload, dict):
                            self._insert_import_assertion(
                                partition_id, line_number, raw_sha256, raw_record,
                                "held_non_object", {"type": type(payload).__name__}, imported_at,
                                payload=payload,
                            )
                            continue
                        disposition, detail, occurrence = self._validate_ledger_v2_payload(payload)
                        assertion_id: str | None = None
                        if disposition == "bound" and occurrence is not None:
                            digest = str(payload["digest"]).casefold()
                            computed_at = str(payload["computedAt"])
                            computation = str(payload.get("computation") or "unspecified")
                            verifier = f"r2-hash-ledger-v2/{computation}"
                            conflicting = self.connection.execute(
                                """SELECT 1 FROM strong_fingerprint_assertion
                                   WHERE occurrence_id = ? AND sha256 <> ? LIMIT 1""",
                                (occurrence["occurrence_id"], digest),
                            ).fetchone()
                            if conflicting is not None:
                                disposition = "held_digest_conflict"
                                detail = {"error": "different SHA-256 already asserted for occurrence"}
                            assertion_id = _stable_id(
                                "sha256assert", occurrence["occurrence_id"], digest,
                                "source_sha256_ledger", verifier, computed_at,
                                payload.get("sourceVersion"), payload.get("sourceEtag"),
                                FINGERPRINT_ASSERTION_VERSION,
                            )
                            self.connection.execute(
                                """INSERT OR IGNORE INTO strong_fingerprint_assertion(
                                       fingerprint_assertion_id, occurrence_id, inventory_id,
                                       bucket, object_path, source_version, source_etag,
                                       byte_size, observed_md5, sha256, verification_method,
                                       verifier, verified_at, assertion_version
                                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                             'source_sha256_ledger', ?, ?, ?)""",
                                (
                                    assertion_id, occurrence["occurrence_id"],
                                    occurrence["inventory_id"], occurrence["bucket"],
                                    occurrence["object_path"], payload.get("sourceVersion"),
                                    payload.get("sourceEtag"), occurrence["byte_size"],
                                    occurrence["md5_normalized"], digest, verifier,
                                    computed_at, FINGERPRINT_ASSERTION_VERSION,
                                ),
                            )
                        import_assertion_id = self._insert_import_assertion(
                            partition_id, line_number, raw_sha256, raw_record,
                            disposition, detail, imported_at, payload=payload,
                        )
                        if assertion_id is not None and occurrence is not None:
                            self.connection.execute(
                                """INSERT OR IGNORE INTO fingerprint_import_binding(
                                       import_assertion_id, fingerprint_assertion_id,
                                       occurrence_id
                                   ) VALUES (?, ?, ?)""",
                                (
                                    import_assertion_id, assertion_id,
                                    occurrence["occurrence_id"],
                                ),
                            )
                            if disposition == "held_digest_conflict":
                                self.connection.execute(
                                    """UPDATE fingerprint_import_assertion
                                       SET disposition = 'held_digest_conflict',
                                           detail_json = ?
                                       WHERE import_assertion_id IN (
                                           SELECT b.import_assertion_id
                                           FROM fingerprint_import_binding b
                                           WHERE b.occurrence_id = ?
                                       )""",
                                    (
                                        json.dumps(detail, sort_keys=True, separators=(",", ":")),
                                        occurrence["occurrence_id"],
                                    ),
                                )
                self.connection.execute(
                    """UPDATE fingerprint_import_partition AS p
                       SET bound_count = (
                               SELECT COUNT(*) FROM fingerprint_import_assertion i
                               WHERE i.partition_id = p.partition_id
                                 AND i.disposition = 'bound'
                           ),
                           held_count = (
                               SELECT COUNT(*) FROM fingerprint_import_assertion i
                               WHERE i.partition_id = p.partition_id
                                 AND i.disposition NOT IN ('bound', 'held_blank_record')
                           )"""
                )
                counts = self.connection.execute(
                    """SELECT
                           SUM(CASE WHEN disposition = 'bound' THEN 1 ELSE 0 END) AS bound_count,
                           SUM(CASE WHEN disposition <> 'bound' THEN 1 ELSE 0 END) AS held_count
                       FROM fingerprint_import_assertion WHERE partition_id = ?""",
                    (partition_id,),
                ).fetchone()
                bound_count = int(counts["bound_count"] or 0)
                held_count = int(counts["held_count"] or 0)
                self.connection.execute(
                    """UPDATE fingerprint_import_partition
                       SET row_count = ?, bound_count = ?, held_count = ?
                       WHERE partition_id = ?""",
                    (row_count, bound_count, held_count, partition_id),
                )
            results.append(
                ImportPartitionResult(
                    partition_id, str(path), row_count,
                    bound_count, held_count, False,
                )
            )
        # One reconciliation after all partition transactions keeps million-row imports bounded.
        # A skipped idempotent partition may still be the run that repairs derived state.
        if results:
            self._reconcile_identities()
        return results

    def _repair_partition_counts(self, partition_id: str) -> tuple[int, int, int]:
        """Exclude historical blank separators from authoritative record totals.

        Older importer versions persisted a `held_blank_record` assertion for
        the transport separator. The assertion remains as audit history, while
        partition completeness and held counts are repaired in place.
        """
        counts = self.connection.execute(
            """SELECT
                   SUM(CASE WHEN disposition <> 'held_blank_record' THEN 1 ELSE 0 END)
                       AS row_count,
                   SUM(CASE WHEN disposition = 'bound' THEN 1 ELSE 0 END)
                       AS bound_count,
                   SUM(CASE WHEN disposition NOT IN ('bound', 'held_blank_record')
                            THEN 1 ELSE 0 END) AS held_count
               FROM fingerprint_import_assertion WHERE partition_id = ?""",
            (partition_id,),
        ).fetchone()
        repaired = (
            int(counts["row_count"] or 0),
            int(counts["bound_count"] or 0),
            int(counts["held_count"] or 0),
        )
        with self.connection:
            self.connection.execute(
                """UPDATE fingerprint_import_partition
                   SET row_count = ?, bound_count = ?, held_count = ?
                   WHERE partition_id = ?""",
                (*repaired, partition_id),
            )
        return repaired

    def finalize_sha256_bridge(
        self,
        expected_partition_count: int,
        expected_record_count: int,
        finalized_at: str | None = None,
    ) -> BridgeFinalizationResult:
        """Freeze a complete, conflict-free ``(MD5, size) -> SHA-256`` bridge.

        The bridge inherits content identity only. It does not create cloned
        strong-fingerprint assertions and therefore never claims that an
        inherited occurrence was directly hashed.
        """
        if expected_partition_count <= 0 or expected_record_count <= 0:
            raise ValueError("expected partition and record counts must be positive")
        (
            observed_partition_count,
            observed_record_count,
            partition_set_sha256,
            assertion_set_sha256,
        ) = self._fingerprint_state()
        if observed_partition_count != expected_partition_count:
            raise ValueError(
                "SHA-256 bridge refused: completed partition count mismatch "
                f"(expected {expected_partition_count}, observed {observed_partition_count})"
            )
        if observed_record_count != expected_record_count:
            raise ValueError(
                "SHA-256 bridge refused: completed record count mismatch "
                f"(expected {expected_record_count}, observed {observed_record_count})"
            )
        md5_conflicts = self.connection.execute(
            """SELECT observed_md5, byte_size, COUNT(DISTINCT sha256) AS digest_count
               FROM strong_fingerprint_assertion
               WHERE observed_md5 IS NOT NULL
               GROUP BY observed_md5, byte_size
               HAVING COUNT(DISTINCT sha256) > 1
               LIMIT 1"""
        ).fetchone()
        if md5_conflicts is not None:
            raise ValueError(
                "SHA-256 bridge refused: conflicting SHA-256 values for an MD5+size group"
            )
        sha_size_conflicts = self.connection.execute(
            """SELECT sha256, COUNT(DISTINCT byte_size) AS size_count
               FROM strong_fingerprint_assertion
               GROUP BY sha256
               HAVING COUNT(DISTINCT byte_size) > 1
               LIMIT 1"""
        ).fetchone()
        if sha_size_conflicts is not None:
            raise ValueError(
                "SHA-256 bridge refused: a SHA-256 digest is asserted for multiple sizes"
            )
        finalization_id = _stable_id(
            "sha256bridge",
            expected_partition_count,
            expected_record_count,
            partition_set_sha256,
            assertion_set_sha256,
        )
        existing = self.connection.execute(
            "SELECT bridge_group_count FROM sha256_bridge_finalization WHERE finalization_id = ?",
            (finalization_id,),
        ).fetchone()
        if existing is not None:
            self._reconcile_identities()
            return BridgeFinalizationResult(
                finalization_id,
                observed_partition_count,
                observed_record_count,
                int(existing["bridge_group_count"]),
                True,
            )
        stale = self.connection.execute(
            "SELECT 1 FROM sha256_bridge_finalization LIMIT 1"
        ).fetchone()
        if stale is not None:
            raise ValueError(
                "SHA-256 bridge refused: an immutable finalization exists for a different import set; "
                "use a new ledger"
            )
        candidates = self.connection.execute(
            """SELECT observed_md5 AS md5, byte_size, MIN(sha256) AS sha256,
                      COUNT(*) AS direct_assertion_count
               FROM strong_fingerprint_assertion
               WHERE observed_md5 IS NOT NULL
               GROUP BY observed_md5, byte_size
               HAVING COUNT(DISTINCT sha256) = 1
               ORDER BY observed_md5, byte_size"""
        ).fetchall()
        finalized_at = finalized_at or _utc_now()
        with self.connection:
            self.connection.execute(
                """INSERT INTO sha256_bridge_finalization(
                       finalization_id, expected_partition_count,
                       expected_record_count, observed_partition_count,
                       observed_record_count, partition_set_sha256,
                       assertion_set_sha256, bridge_group_count, finalized_at,
                       state
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'frozen')""",
                (
                    finalization_id, expected_partition_count,
                    expected_record_count, observed_partition_count,
                    observed_record_count, partition_set_sha256,
                    assertion_set_sha256, len(candidates), finalized_at,
                ),
            )
            self.connection.executemany(
                """INSERT INTO sha256_md5_size_bridge(
                       md5, byte_size, sha256, direct_assertion_count,
                       finalization_id, created_at
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (
                        row["md5"], row["byte_size"], row["sha256"],
                        row["direct_assertion_count"], finalization_id,
                        finalized_at,
                    )
                    for row in candidates
                ],
            )
        self._reconcile_identities()
        return BridgeFinalizationResult(
            finalization_id,
            observed_partition_count,
            observed_record_count,
            len(candidates),
            False,
        )

    def _validate_ledger_v2_payload(
        self,
        payload: Mapping[str, object],
    ) -> tuple[str, dict[str, object], sqlite3.Row | None]:
        if payload.get("schema") != "casebible-r2-sha256-record-v2":
            return "held_schema_mismatch", {"observed": payload.get("schema")}, None
        if str(payload.get("algorithm") or "").upper() != "SHA-256":
            return "held_algorithm_mismatch", {"observed": payload.get("algorithm")}, None
        digest = payload.get("digest")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            return "held_invalid_digest", {"observed": digest}, None
        bucket = payload.get("sourceBucket")
        key = payload.get("sourceKey")
        size = payload.get("sourceSize")
        if (
            not isinstance(bucket, str) or not bucket or
            not isinstance(key, str) or not key or
            isinstance(size, bool) or not isinstance(size, int) or size < 0
        ):
            return "held_invalid_locator", {"error": "invalid sourceBucket/sourceKey/sourceSize"}, None
        md5_raw = payload.get("md5Hash")
        if not isinstance(md5_raw, str) or not MD5_RE.fullmatch(md5_raw):
            return "held_invalid_md5", {"observed": md5_raw}, None
        checksum_block = payload.get("sourceChecksums")
        if isinstance(checksum_block, dict):
            checksum_md5 = checksum_block.get("md5")
            if checksum_md5 and str(checksum_md5).casefold() != md5_raw.casefold():
                return (
                    "held_source_field_conflict",
                    {"error": "sourceChecksums.md5 differs from md5Hash"},
                    None,
                )
        full_path = payload.get("fullPath")
        expected_full_path = f"s3://{bucket}/{key}"
        if full_path and full_path != expected_full_path:
            return (
                "held_source_field_conflict",
                {"error": "fullPath differs from sourceBucket/sourceKey"},
                None,
            )
        computed_at = payload.get("computedAt")
        if not isinstance(computed_at, str) or not computed_at.strip():
            return (
                "held_deferred_missing_computed_at",
                {"error": "computedAt is required for an authoritative assertion"},
                None,
            )
        occurrences = self.connection.execute(
            """SELECT occurrence_id, inventory_id, bucket, object_path,
                      byte_size, md5_normalized
               FROM occurrence
               WHERE bucket = ? AND object_path = ? AND byte_size = ?
                 AND md5_normalized = ?
               ORDER BY inventory_id, row_number""",
            (bucket, key, size, md5_raw.casefold()),
        ).fetchall()
        if not occurrences:
            return (
                "held_unmatched_occurrence",
                {"error": "no inventory occurrence matched the source binding"},
                None,
            )
        if len(occurrences) > 1:
            return (
                "held_ambiguous_occurrence",
                {
                    "error": "multiple inventory occurrences matched; version/ETag is not in inventory",
                    "match_count": len(occurrences),
                },
                None,
            )
        return "bound", {}, occurrences[0]

    def _insert_import_assertion(
        self,
        partition_id: str,
        line_number: int,
        raw_sha256: str,
        raw_record: str,
        disposition: str,
        detail: Mapping[str, object],
        asserted_at: str,
        payload: object | None = None,
    ) -> str:
        values = payload if isinstance(payload, dict) else {}
        def text_field(name: str) -> str | None:
            value = values.get(name)
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)

        source_size = values.get("sourceSize")
        if isinstance(source_size, bool) or not isinstance(source_size, int):
            source_size = None
        import_assertion_id = _stable_id(
            "sha256import", partition_id, line_number, raw_sha256
        )
        self.connection.execute(
            """INSERT INTO fingerprint_import_assertion(
                   import_assertion_id, partition_id, line_number, raw_sha256,
                   raw_record, schema_name, algorithm, digest_raw, source_bucket,
                   source_key, source_size, md5_raw, source_version, source_etag,
                   computed_at, computation, disposition, detail_json, asserted_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                import_assertion_id, partition_id, line_number, raw_sha256,
                raw_record, text_field("schema"), text_field("algorithm"),
                text_field("digest"), text_field("sourceBucket"),
                text_field("sourceKey"), source_size, text_field("md5Hash"),
                text_field("sourceVersion"), text_field("sourceEtag"),
                text_field("computedAt"), text_field("computation"),
                disposition,
                json.dumps(dict(detail), sort_keys=True, separators=(",", ":"), default=str),
                asserted_at,
            ),
        )
        return import_assertion_id

    def _assert_path_observations(self) -> None:
        cursor = self.connection.execute(
            """SELECT o.occurrence_id, o.object_path, o.mimetype_raw, b.captured_at
               FROM occurrence o JOIN inventory_batch b USING (inventory_id)"""
        )
        with self.connection:
            while batch := cursor.fetchmany(10_000):
                for row in batch:
                    label, confidence, evidence = _category(row)
                    self._insert_assertion(
                        row["occurrence_id"], "high_level_category", label, None,
                        confidence, evidence, row["captured_at"]
                    )
                    for label, grouping_key, confidence, evidence in _atomic_hints(row["object_path"]):
                        self._insert_assertion(
                            row["occurrence_id"], "atomic_unit_hint", label,
                            grouping_key, confidence, evidence, row["captured_at"]
                        )

    def _insert_assertion(
        self,
        occurrence_id: str,
        kind: str,
        label: str,
        grouping_key: str | None,
        confidence: float,
        evidence: Mapping[str, str],
        asserted_at: str,
    ) -> None:
        assertion_id = _stable_id(
            "assert", occurrence_id, kind, label, grouping_key, RULE_SET, RULE_VERSION
        )
        self.connection.execute(
            """INSERT OR IGNORE INTO assertion(
                   assertion_id, occurrence_id, assertion_kind, label,
                   grouping_key, confidence, rule_set, rule_version,
                   provisional, evidence_json, asserted_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (
                assertion_id, occurrence_id, kind, label, grouping_key,
                confidence, RULE_SET, RULE_VERSION,
                json.dumps(dict(evidence), sort_keys=True, separators=(",", ":")),
                asserted_at,
            ),
        )

    def build_generation(
        self,
        output_dir: Path | str,
        destination_remote: str = "b2:",
        destination_prefix: str = "consignatio/intake/raw-dedupe/v1",
        generation_id: str | None = None,
        created_at: str | None = None,
    ) -> BuildResult:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        has_bridge = self.connection.execute(
            "SELECT 1 FROM sha256_bridge_finalization LIMIT 1"
        ).fetchone()
        if has_bridge is not None and self._active_bridge_finalization() is None:
            raise ValueError(
                "SHA-256 bridge is stale relative to the imported partition/assertion set; "
                "build refused"
            )
        inventories = self.connection.execute(
            "SELECT inventory_id, source_sha256 FROM inventory_batch ORDER BY inventory_id"
        ).fetchall()
        if not inventories:
            raise ValueError("cannot build a generation before ingesting an inventory")
        inventory_set_sha256 = _sha256_text("\n".join(row["source_sha256"] for row in inventories))
        fingerprints = self.connection.execute(
            """SELECT fingerprint_assertion_id, sha256
               FROM strong_fingerprint_assertion
               ORDER BY fingerprint_assertion_id"""
        ).fetchall()
        active_bridge = self._active_bridge_finalization()
        fingerprint_set_sha256 = _sha256_text(
            "\n".join(
                [
                    *(f"{row['fingerprint_assertion_id']}:{row['sha256']}" for row in fingerprints),
                    *(
                        [f"bridge:{active_bridge['finalization_id']}"]
                        if active_bridge is not None
                        else []
                    ),
                ]
            )
        )
        if generation_id is None:
            generation_id = f"generation:{_sha256_text('|'.join((inventory_set_sha256, fingerprint_set_sha256, destination_remote, destination_prefix, RULE_VERSION)))}"
        created_at = created_at or _utc_now()
        with self.connection:
            existing_generation = self.connection.execute(
                "SELECT * FROM transfer_generation WHERE generation_id = ?",
                (generation_id,),
            ).fetchone()
            expected_generation = (
                destination_remote,
                destination_prefix.strip("/"),
                RULE_VERSION,
                inventory_set_sha256,
                fingerprint_set_sha256,
            )
            if existing_generation is not None:
                observed_generation = (
                    existing_generation["destination_remote"],
                    existing_generation["destination_prefix"],
                    existing_generation["rule_version"],
                    existing_generation["inventory_set_sha256"],
                    existing_generation["fingerprint_set_sha256"],
                )
                if observed_generation != expected_generation:
                    raise ValueError(
                        "generation_id already exists with a different inventory, "
                        "fingerprint set, destination, or rule version"
                    )
            self.connection.execute(
                """INSERT OR IGNORE INTO transfer_generation(
                       generation_id, created_at, destination_remote,
                       destination_prefix, rule_version, inventory_set_sha256,
                       fingerprint_set_sha256, state
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, 'frozen')""",
                (
                    generation_id, created_at, destination_remote,
                    destination_prefix.strip("/"), RULE_VERSION,
                    inventory_set_sha256, fingerprint_set_sha256,
                ),
            )
            inherited_content_ids = {
                row["content_id"]
                for row in self.connection.execute(
                    """SELECT DISTINCT o.content_id
                       FROM occurrence o
                       JOIN content_identity c USING (content_id)
                       WHERE c.identity_status = 'sha256_verified'
                         AND NOT EXISTS (
                             SELECT 1 FROM strong_fingerprint_assertion f
                             WHERE f.occurrence_id = o.occurrence_id
                               AND f.sha256 = c.sha256
                         )"""
                )
            }
            sha_representatives = {
                row["content_id"]: row
                for row in self.connection.execute(
                    """WITH candidates AS (
                           SELECT DISTINCT o.*, b.captured_at
                           FROM occurrence o
                           JOIN content_identity c USING (content_id)
                           JOIN inventory_batch b USING (inventory_id)
                           JOIN strong_fingerprint_assertion f
                             ON f.occurrence_id = o.occurrence_id
                            AND f.sha256 = c.sha256
                           WHERE c.identity_status = 'sha256_verified'
                       ), ranked AS (
                           SELECT *, ROW_NUMBER() OVER (
                               PARTITION BY content_id
                               ORDER BY captured_at DESC, bucket COLLATE BINARY,
                                        object_path COLLATE BINARY, row_number,
                                        occurrence_id
                           ) AS representative_rank
                           FROM candidates
                       )
                       SELECT * FROM ranked WHERE representative_rank = 1"""
                )
            }
            identity_cursor = self.connection.execute(
                """SELECT content_id, identity_kind, identity_status, sha256, md5, byte_size
                   FROM content_identity
                   WHERE content_id IN (SELECT DISTINCT content_id FROM occurrence)
                   ORDER BY content_id"""
            )
            while identity_batch := identity_cursor.fetchmany(5_000):
                for identity in identity_batch:
                    if identity["identity_status"] == "sha256_verified":
                        representative = sha_representatives.get(identity["content_id"])
                        representatives = [representative] if representative is not None else []
                        dedupe_authority = (
                            "sha256_via_conflict_free_md5_size_bridge"
                            if identity["content_id"] in inherited_content_ids
                            else "sha256_verified"
                        )
                        stored_dedupe_authority = (
                            dedupe_authority
                            if self._transfer_item_accepts_bridge_authority()
                            else "sha256_verified"
                        )
                    else:
                        representatives = self.connection.execute(
                            """SELECT * FROM (
                                   SELECT o.*, b.captured_at,
                                          ROW_NUMBER() OVER (
                                              PARTITION BY o.bucket, o.object_path
                                              ORDER BY b.captured_at DESC, o.row_number DESC,
                                                       o.occurrence_id
                                          ) AS location_rank
                                   FROM occurrence o
                                   JOIN inventory_batch b USING (inventory_id)
                                   WHERE o.content_id = ?
                               ) ranked
                               WHERE location_rank = 1
                               ORDER BY bucket COLLATE BINARY, object_path COLLATE BINARY""",
                            (identity["content_id"],),
                        ).fetchall()
                        if identity["identity_status"] == "md5_size_candidate":
                            dedupe_authority = "md5_candidate_no_suppression"
                        elif identity["identity_status"] in {
                            "md5_size_conflict", "sha256_assertion_conflict",
                            "sha256_size_conflict",
                        }:
                            dedupe_authority = "none_conflict"
                        else:
                            dedupe_authority = "none_pending_fingerprint"
                        stored_dedupe_authority = dedupe_authority
                    if not representatives:
                        raise RuntimeError(f"content identity has no occurrence: {identity['content_id']}")
                    for representative in representatives:
                        source_relpath = _normalized_relpath(
                            representative["bucket"], representative["object_path"]
                        )
                        destination_relpath = f"{destination_prefix.strip('/')}/{source_relpath}"
                        location_content_count = self.connection.execute(
                            """SELECT COUNT(DISTINCT content_id)
                               FROM occurrence
                               WHERE bucket = ? AND object_path = ?""",
                            (representative["bucket"], representative["object_path"]),
                        ).fetchone()[0]
                        if location_content_count > 1:
                            status = "held_source_location_drift"
                        else:
                            status = self._initial_status(
                                identity["identity_status"], source_relpath
                            )
                        transfer_item_id = _stable_id(
                            "transfer", generation_id, identity["content_id"],
                            representative["occurrence_id"],
                        )
                        selection_rule = (
                            REPRESENTATIVE_RULE
                            if identity["identity_status"] == "sha256_verified"
                            else "per-distinct-source-location-no-dedup.v1"
                        )
                        self.connection.execute(
                            """INSERT OR IGNORE INTO transfer_item(
                                   transfer_item_id, generation_id, content_id,
                                   representative_occurrence_id, source_relpath,
                                   destination_relpath, selection_rule,
                                   selection_is_quality_judgment, dedupe_authority,
                                   initial_status
                               ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                            (
                                transfer_item_id, generation_id, identity["content_id"],
                                representative["occurrence_id"], source_relpath,
                                destination_relpath, selection_rule,
                                stored_dedupe_authority, status,
                            ),
                        )
                        if identity["identity_status"] == "sha256_verified":
                            self.connection.execute(
                                """INSERT OR IGNORE INTO transfer_item_occurrence(
                                       transfer_item_id, occurrence_id
                                   ) SELECT ?, occurrence_id FROM occurrence
                                     WHERE content_id = ?""",
                                (transfer_item_id, identity["content_id"]),
                            )
                        else:
                            self.connection.execute(
                                """INSERT OR IGNORE INTO transfer_item_occurrence(
                                       transfer_item_id, occurrence_id
                                   ) SELECT ?, occurrence_id FROM occurrence
                                     WHERE content_id = ? AND bucket = ? AND object_path = ?""",
                                (
                                    transfer_item_id, identity["content_id"],
                                    representative["bucket"], representative["object_path"],
                                ),
                            )
                        event_id = _stable_id("status", transfer_item_id, 1, status)
                        self.connection.execute(
                            """INSERT OR IGNORE INTO transfer_status_event(
                                   event_id, transfer_item_id, sequence_number,
                                   status, recorded_at, detail
                               ) VALUES (?, ?, 1, ?, ?, ?)""",
                            (
                                event_id, transfer_item_id, status, created_at,
                                "generation initialization",
                            ),
                        )
        # Release the large planning indexes before streaming output tables.
        del sha_representatives, inherited_content_ids
        files_count = self._write_outputs(generation_id, output)
        parquet_written = self._write_parquet(output / "parquet")
        counts = self.connection.execute(
            """SELECT
                 (SELECT COUNT(*) FROM occurrence) AS occurrences,
                 (SELECT COUNT(*) FROM content_identity WHERE identity_status = 'sha256_verified'
                    AND content_id IN (SELECT DISTINCT content_id FROM occurrence)) AS sha256_count,
                 (SELECT COUNT(*) FROM content_identity WHERE identity_status = 'md5_size_candidate'
                    AND content_id IN (SELECT DISTINCT content_id FROM occurrence)) AS candidate_count,
                 (SELECT COUNT(*) FROM transfer_item WHERE generation_id = ? AND initial_status LIKE 'held_%') AS held_count""",
            (generation_id,),
        ).fetchone()
        return BuildResult(
            generation_id=generation_id,
            inventory_count=len(inventories),
            occurrence_count=counts["occurrences"],
            sha256_verified_content_count=counts["sha256_count"],
            md5_candidate_content_count=counts["candidate_count"],
            held_content_count=counts["held_count"],
            files_from_count=files_count,
            parquet_written=parquet_written,
        )

    @staticmethod
    def _initial_status(identity_status: str, source_relpath: str) -> str:
        if not _path_is_safe_for_files_from(source_relpath):
            return "held_unsafe_path"
        return {
            "sha256_verified": "planned",
            "md5_size_candidate": "planned",
            "missing_hash": "held_missing_hash",
            "invalid_hash": "held_invalid_hash",
            "hash_error": "held_hash_error",
            "hash_unsupported": "held_hash_unsupported",
            "md5_size_conflict": "held_md5_size_conflict",
            "sha256_assertion_conflict": "held_sha256_assertion_conflict",
            "sha256_size_conflict": "held_sha256_size_conflict",
        }[identity_status]

    def _write_outputs(self, generation_id: str, output: Path) -> int:
        files_dir = output / "files-from"
        bucket_dir = files_dir / "by-bucket"
        bucket_dir.mkdir(parents=True, exist_ok=True)
        base_query = """SELECT t.transfer_item_id, t.content_id, t.source_relpath,
                               t.destination_relpath, o.bucket, o.object_path,
                               c.sha256, c.md5, c.byte_size,
                               CASE
                                 WHEN c.sha256 IS NOT NULL AND EXISTS (
                                     SELECT 1 FROM occurrence ox
                                     WHERE ox.content_id = t.content_id
                                       AND NOT EXISTS (
                                           SELECT 1 FROM strong_fingerprint_assertion fx
                                           WHERE fx.occurrence_id = ox.occurrence_id
                                             AND fx.sha256 = c.sha256
                                       )
                                 ) THEN 'sha256_via_conflict_free_md5_size_bridge'
                                 ELSE t.dedupe_authority
                               END AS dedupe_authority,
                               s.status
                        FROM transfer_item t
                        JOIN occurrence o ON o.occurrence_id = t.representative_occurrence_id
                        JOIN content_identity c USING (content_id)
                        JOIN transfer_item_current_status s USING (transfer_item_id)
                        WHERE t.generation_id = ?"""
        planned_count = 0
        with (files_dir / "all.txt").open("w", encoding="utf-8", newline="\n") as handle:
            cursor = self.connection.execute(
                base_query + " AND t.initial_status = 'planned' ORDER BY t.source_relpath COLLATE BINARY, t.content_id",
                (generation_id,),
            )
            for row in cursor:
                handle.write(f"{row['source_relpath']}\n")
                planned_count += 1
        buckets = self.connection.execute(
            """SELECT DISTINCT o.bucket
               FROM transfer_item t
               JOIN occurrence o ON o.occurrence_id = t.representative_occurrence_id
               JOIN transfer_item_current_status s USING (transfer_item_id)
               WHERE t.generation_id = ? AND t.initial_status = 'planned'
               ORDER BY o.bucket COLLATE BINARY""",
            (generation_id,),
        ).fetchall()
        bucket_index: list[tuple[str, str]] = []
        for bucket_row in buckets:
            bucket = bucket_row["bucket"]
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", bucket).strip("._") or "bucket"
            filename = f"{safe_name}-{_sha256_text(bucket)[:8]}.txt"
            bucket_index.append((bucket, filename))
            with (bucket_dir / filename).open("w", encoding="utf-8", newline="\n") as handle:
                cursor = self.connection.execute(
                    base_query + " AND t.initial_status = 'planned' AND o.bucket = ? ORDER BY o.object_path COLLATE BINARY, t.content_id",
                    (generation_id, bucket),
                )
                for row in cursor:
                    handle.write(f"{row['object_path']}\n")
        with (files_dir / "buckets.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(("bucket", "files_from"))
            writer.writerows(bucket_index)
        with (output / "transfer-manifest.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow((
                "transfer_item_id", "content_id", "source_relpath", "destination_relpath",
                "sha256", "md5", "size", "dedupe_authority", "status",
            ))
            cursor = self.connection.execute(
                base_query + " ORDER BY t.source_relpath COLLATE BINARY, t.content_id",
                (generation_id,),
            )
            for row in cursor:
                writer.writerow((
                    row["transfer_item_id"], row["content_id"], row["source_relpath"],
                    row["destination_relpath"], row["sha256"] or "",
                    row["md5"] or "", row["byte_size"], row["dedupe_authority"],
                    row["status"],
                ))
        self._write_payload_mapping(generation_id, output)
        return planned_count

    @staticmethod
    def _source_identity(
        bucket: str,
        object_path: str,
        byte_size: int,
        source_version: str | None,
        source_etag: str | None,
        source_md5: str | None,
    ) -> str:
        """Return the runner's stable, opaque identity for one source locator."""
        return _sha256_text(
            json.dumps(
                {
                    "bucket": bucket,
                    "path": object_path,
                    "size": byte_size,
                    "source_etag": source_etag or "",
                    "source_md5": source_md5 or "",
                    "source_version": source_version or "",
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )

    def _write_payload_mapping(self, generation_id: str, output: Path) -> None:
        """Write the reviewed input contract consumed by ``payload_runner.py``.

        Only a positive-size, conflict-free SHA-256 identity with a safe,
        non-drifting source locator is canonical. Positive-size, addressable,
        non-conflicting locators without authoritative SHA-256 are retained as
        unique source-identity payloads that the runner permits only under full
        verification. The occurrence map remains exhaustive even when many
        occurrences resolve to one canonical payload.
        """
        payload_fields = (
            "source_bucket", "source_path", "content_algorithm",
            "content_digest", "size", "source_identity", "disposition",
            "destination_key", "source_md5", "source_etag", "source_version",
            "occurrence_id", "content_id", "dedupe_authority", "hold_reason",
        )
        occurrence_fields = (
            "occurrence_id", "inventory_id", "captured_at", "source_bucket",
            "source_path", "size", "source_md5", "content_id",
            "identity_status", "content_algorithm", "content_digest",
            "payload_source_identity", "destination_key", "mapping_status",
            "assertion_basis", "dedupe_authority", "source_location_drift",
            "is_payload_representative",
        )
        occurrence_query = """SELECT o.*, b.captured_at, c.identity_status, c.sha256,
                      c.md5 AS content_md5,
                      location.content_count AS location_content_count,
                      EXISTS(
                          SELECT 1 FROM strong_fingerprint_assertion f
                          WHERE f.occurrence_id = o.occurrence_id
                            AND f.sha256 = c.sha256
                      ) AS has_direct_assertion
               FROM occurrence o
               JOIN inventory_batch b USING (inventory_id)
               JOIN content_identity c USING (content_id)
               JOIN (
                   SELECT bucket, object_path,
                          COUNT(DISTINCT content_id) AS content_count
                   FROM occurrence GROUP BY bucket, object_path
               ) location
                 ON location.bucket = o.bucket
                AND location.object_path = o.object_path
               ORDER BY o.bucket COLLATE BINARY, o.object_path COLLATE BINARY,
                        b.captured_at, o.row_number, o.occurrence_id"""

        canonical_by_content: dict[str, dict[str, object]] = {}
        inherited_content_ids = {
            row["content_id"]
            for row in self.connection.execute(
                """SELECT DISTINCT o.content_id
                   FROM occurrence o
                   JOIN content_identity c USING (content_id)
                   WHERE c.identity_status = 'sha256_verified'
                     AND NOT EXISTS (
                         SELECT 1 FROM strong_fingerprint_assertion f
                         WHERE f.occurrence_id = o.occurrence_id
                           AND f.sha256 = c.sha256
                     )"""
            )
        }
        direct_representatives = {
            row["content_id"]: row
            for row in self.connection.execute(
                """WITH candidates AS (
                       SELECT DISTINCT o.content_id, o.occurrence_id, o.bucket,
                              o.object_path, o.byte_size, o.md5_normalized,
                              b.captured_at, f.source_version, f.source_etag,
                              f.fingerprint_assertion_id, o.row_number
                       FROM occurrence o
                       JOIN content_identity c USING (content_id)
                       JOIN inventory_batch b USING (inventory_id)
                       JOIN strong_fingerprint_assertion f
                         ON f.occurrence_id = o.occurrence_id
                        AND f.sha256 = c.sha256
                       WHERE c.identity_status = 'sha256_verified'
                         AND o.byte_size > 0
                         AND instr(o.object_path, char(10)) = 0
                         AND instr(o.object_path, char(13)) = 0
                         AND instr(o.object_path, char(0)) = 0
                         AND instr(o.object_path, char(92)) = 0
                         AND substr(o.object_path, 1, 1) NOT IN ('/', '#')
                         AND o.object_path NOT IN ('.', '..', '_system')
                         AND o.object_path NOT LIKE './%'
                         AND o.object_path NOT LIKE '../%'
                         AND o.object_path NOT LIKE '%/./%'
                         AND o.object_path NOT LIKE '%/../%'
                         AND o.object_path NOT LIKE '%/'
                         AND o.object_path NOT LIKE '%//%'
                         AND lower(o.object_path) NOT LIKE '_system/%'
                         AND (SELECT COUNT(DISTINCT ox.content_id)
                              FROM occurrence ox
                              WHERE ox.bucket = o.bucket
                                AND ox.object_path = o.object_path) = 1
                   ), ranked AS (
                       SELECT *, ROW_NUMBER() OVER (
                           PARTITION BY content_id
                           ORDER BY captured_at DESC, bucket COLLATE BINARY,
                                    object_path COLLATE BINARY, row_number,
                                    occurrence_id, source_version COLLATE BINARY,
                                    source_etag COLLATE BINARY,
                                    fingerprint_assertion_id
                       ) AS representative_rank
                       FROM candidates
                   )
                   SELECT * FROM ranked WHERE representative_rank = 1"""
            )
        }
        sha_identities = self.connection.execute(
            """SELECT content_id, sha256, byte_size
               FROM content_identity
               WHERE identity_status = 'sha256_verified'
                 AND content_id IN (SELECT DISTINCT content_id FROM occurrence)
               ORDER BY sha256, byte_size, content_id"""
        ).fetchall()
        for identity in sha_identities:
            if identity["byte_size"] == 0:
                continue
            representative = direct_representatives.get(identity["content_id"])
            if representative is None:
                continue
            source_identity = self._source_identity(
                representative["bucket"], representative["object_path"],
                representative["byte_size"], representative["source_version"],
                representative["source_etag"], representative["md5_normalized"],
            )
            digest = identity["sha256"]
            dedupe_authority = (
                "sha256_via_conflict_free_md5_size_bridge"
                if identity["content_id"] in inherited_content_ids
                else "sha256_verified"
            )
            canonical_by_content[identity["content_id"]] = {
                "source_bucket": representative["bucket"],
                "source_path": representative["object_path"],
                "content_algorithm": "sha256",
                "content_digest": digest,
                "size": representative["byte_size"],
                "source_identity": source_identity,
                "disposition": "canonical",
                "destination_key": f"payloads/sha256/{digest[:2]}/{digest}",
                "source_md5": representative["md5_normalized"] or "",
                "source_etag": representative["source_etag"] or "",
                "source_version": representative["source_version"] or "",
                "occurrence_id": representative["occurrence_id"],
                "content_id": identity["content_id"],
                "dedupe_authority": dedupe_authority,
                "hold_reason": "",
            }

        del direct_representatives, inherited_content_ids
        payload_rows: list[dict[str, object]] = list(canonical_by_content.values())
        # One held row per currently addressable source locator. This prevents a
        # drifted historical path from appearing twice in the runner input.
        canonical_locations = {
            (str(row["source_bucket"]), str(row["source_path"]))
            for row in payload_rows
        }
        latest_location_rows = self.connection.execute(
            """WITH ranked AS (
                   SELECT o.*, b.captured_at, c.identity_status, c.sha256,
                          ROW_NUMBER() OVER (
                              PARTITION BY o.bucket, o.object_path
                              ORDER BY b.captured_at DESC, o.row_number DESC,
                                       o.occurrence_id
                          ) AS location_rank
                   FROM occurrence o
                   JOIN inventory_batch b USING (inventory_id)
                   JOIN content_identity c USING (content_id)
               )
               SELECT ranked.*,
                      (SELECT COUNT(DISTINCT ox.content_id)
                       FROM occurrence ox
                       WHERE ox.bucket = ranked.bucket
                         AND ox.object_path = ranked.object_path) AS location_content_count
               FROM ranked WHERE location_rank = 1
               ORDER BY bucket COLLATE BINARY, object_path COLLATE BINARY"""
        )
        source_identity_by_location: dict[tuple[str, str], dict[str, object]] = {}
        conflicting_statuses = {
            "md5_size_conflict", "sha256_assertion_conflict", "sha256_size_conflict",
        }
        for row in latest_location_rows:
            key = (row["bucket"], row["object_path"])
            if key in canonical_locations:
                continue
            canonical = canonical_by_content.get(row["content_id"])
            # Verified duplicates are represented only through the exhaustive
            # occurrence map when another safe locator is canonical.
            if canonical is not None and row["location_content_count"] == 1:
                continue
            drift = row["location_content_count"] > 1
            path_hold_reason = _payload_source_hold_reason(row["object_path"])
            if drift:
                reason = "held_source_location_drift"
            elif row["byte_size"] == 0:
                reason = "held_zero_byte"
            elif path_hold_reason:
                reason = path_hold_reason
            elif row["identity_status"] in conflicting_statuses:
                reason = f"held_{row['identity_status']}"
            elif row["identity_status"] == "sha256_verified":
                # A SHA identity without an eligible directly asserted source
                # is not weakened into a source-identity copy.
                reason = "held_sha256_without_addressable_direct_source"
            else:
                reason = ""
            algorithm = (
                "md5"
                if row["md5_valid"] and row["identity_status"] != "sha256_verified"
                else "unknown"
            )
            digest = row["md5_normalized"] if algorithm == "md5" else ""
            source_identity = self._source_identity(
                row["bucket"], row["object_path"], row["byte_size"],
                None, None, row["md5_normalized"],
            )
            disposition = "held" if reason else "source-identity"
            destination_namespace = "held" if reason else "source-identity"
            payload_row = {
                "source_bucket": row["bucket"],
                "source_path": row["object_path"],
                "content_algorithm": algorithm,
                "content_digest": digest or "",
                "size": row["byte_size"],
                "source_identity": source_identity,
                "disposition": disposition,
                "destination_key": f"payloads/{destination_namespace}/{source_identity[:2]}/{source_identity}",
                "source_md5": row["md5_normalized"] or "",
                "source_etag": "",
                "source_version": "",
                "occurrence_id": row["occurrence_id"],
                "content_id": row["content_id"],
                "dedupe_authority": (
                    "none_conflict" if drift or row["identity_status"] in conflicting_statuses
                    else "none_source_identity_full_verification"
                ),
                "hold_reason": reason,
            }
            payload_rows.append(payload_row)
            if disposition == "source-identity":
                source_identity_by_location[key] = payload_row
        payload_rows.sort(
            key=lambda row: (
                str(row["destination_key"]).encode("utf-8"),
                str(row["source_bucket"]).encode("utf-8"),
                str(row["source_path"]).encode("utf-8"),
            )
        )

        with (output / "payload-mapping.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=payload_fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(payload_rows)
        with (output / "payload-mapping.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
            for row in payload_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

        representative_occurrences = {
            str(row["occurrence_id"]): row for row in canonical_by_content.values()
        }
        representative_occurrences.update(
            {
                str(row["occurrence_id"]): row
                for row in source_identity_by_location.values()
            }
        )
        with (output / "occurrence-content-map.csv").open("w", encoding="utf-8", newline="") as csv_handle, (
            output / "occurrence-content-map.jsonl"
        ).open("w", encoding="utf-8", newline="\n") as jsonl_handle:
            writer = csv.DictWriter(csv_handle, fieldnames=occurrence_fields, lineterminator="\n")
            writer.writeheader()
            for row in self.connection.execute(occurrence_query):
                canonical = canonical_by_content.get(row["content_id"])
                drift = row["location_content_count"] > 1
                direct_assertion = bool(row["has_direct_assertion"])
                if canonical is not None and not drift:
                    algorithm = "sha256"
                    digest = row["sha256"]
                    destination_key = canonical["destination_key"]
                    payload_source_identity = canonical["source_identity"]
                    mapping_status = "canonical" if row["occurrence_id"] in representative_occurrences else "deduplicated_occurrence"
                    assertion_basis = "direct" if direct_assertion else "inherited_md5_size_bridge"
                    dedupe_authority = canonical["dedupe_authority"]
                else:
                    algorithm = "md5" if row["md5_valid"] and row["identity_status"] != "sha256_verified" else "unknown"
                    digest = row["md5_normalized"] if algorithm == "md5" else ""
                    source_payload = source_identity_by_location.get(
                        (row["bucket"], row["object_path"])
                    )
                    payload_source_identity = (
                        str(source_payload["source_identity"])
                        if source_payload is not None
                        else self._source_identity(
                            row["bucket"], row["object_path"], row["byte_size"],
                            None, None, row["md5_normalized"],
                        )
                    )
                    destination_key = (
                        str(source_payload["destination_key"])
                        if source_payload is not None
                        else f"payloads/held/{payload_source_identity[:2]}/{payload_source_identity}"
                    )
                    if drift:
                        mapping_status = "held_source_location_drift"
                    elif row["byte_size"] == 0:
                        mapping_status = "held_zero_byte"
                    elif (path_hold_reason := _payload_source_hold_reason(row["object_path"])):
                        mapping_status = path_hold_reason
                    elif source_payload is not None:
                        mapping_status = (
                            "source_identity"
                            if row["occurrence_id"] in representative_occurrences
                            else "source_identity_occurrence"
                        )
                    else:
                        mapping_status = f"held_{row['identity_status']}"
                    assertion_basis = (
                        "direct" if direct_assertion
                        else "md5_observation" if algorithm == "md5"
                        else "none"
                    )
                    dedupe_authority = (
                        str(source_payload["dedupe_authority"])
                        if source_payload is not None
                        else "none_conflict" if drift or row["identity_status"] in conflicting_statuses
                        else "none_pending_fingerprint"
                    )
                output_row = {
                    "occurrence_id": row["occurrence_id"],
                    "inventory_id": row["inventory_id"],
                    "captured_at": row["captured_at"],
                    "source_bucket": row["bucket"],
                    "source_path": row["object_path"],
                    "size": row["byte_size"],
                    "source_md5": row["md5_normalized"] or "",
                    "content_id": row["content_id"],
                    "identity_status": row["identity_status"],
                    "content_algorithm": algorithm,
                    "content_digest": digest or "",
                    "payload_source_identity": payload_source_identity,
                    "destination_key": destination_key,
                    "mapping_status": mapping_status,
                    "assertion_basis": assertion_basis,
                    "dedupe_authority": dedupe_authority,
                    "source_location_drift": int(drift),
                    "is_payload_representative": int(row["occurrence_id"] in representative_occurrences),
                }
                writer.writerow(output_row)
                jsonl_handle.write(
                    json.dumps(output_row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
                )

    def _write_parquet(self, parquet_dir: Path) -> bool:
        try:
            import duckdb  # type: ignore[import-not-found]
        except ImportError:
            return False
        parquet_dir.mkdir(parents=True, exist_ok=True)
        tables = (
            "inventory_batch", "content_identity", "occurrence",
            "strong_fingerprint_assertion", "fingerprint_import_partition",
            "fingerprint_import_assertion", "fingerprint_import_binding",
            "sha256_bridge_finalization", "sha256_md5_size_bridge",
            "candidate_representative", "assertion",
            "transfer_generation", "transfer_item", "transfer_item_occurrence",
            "transfer_status_event",
        )
        connection = duckdb.connect(":memory:")
        try:
            for table in tables:
                info = self.connection.execute(f'PRAGMA table_info("{table}")').fetchall()
                columns = [row[1] for row in info]
                type_map = {"INTEGER": "BIGINT", "REAL": "DOUBLE", "BLOB": "BLOB"}
                definitions = ", ".join(
                    f'"{row[1]}" {type_map.get(str(row[2]).upper(), "VARCHAR")}' for row in info
                )
                connection.execute(f'CREATE TABLE "{table}" ({definitions})')
                placeholders = ", ".join("?" for _ in columns)
                source = self.connection.execute(f'SELECT * FROM "{table}"')
                while batch := source.fetchmany(10_000):
                    connection.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', batch)
                target = str((parquet_dir / f"{table}.parquet").resolve()).replace("'", "''")
                connection.execute(f"COPY \"{table}\" TO '{target}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        finally:
            connection.close()
        return True

    def mark_status(
        self,
        transfer_item_id: str,
        status: str,
        detail: str | None = None,
        recorded_at: str | None = None,
    ) -> None:
        current = self.connection.execute(
            """SELECT status, sequence_number FROM transfer_item_current_status
               WHERE transfer_item_id = ?""",
            (transfer_item_id,),
        ).fetchone()
        if current is None:
            raise KeyError(f"unknown transfer item: {transfer_item_id}")
        if status not in ALLOWED_TRANSITIONS.get(current["status"], set()):
            raise ValueError(f"invalid status transition {current['status']} -> {status}")
        sequence = current["sequence_number"] + 1
        event_id = _stable_id("status", transfer_item_id, sequence, status, detail)
        with self.connection:
            self.connection.execute(
                """INSERT INTO transfer_status_event(
                       event_id, transfer_item_id, sequence_number,
                       status, recorded_at, detail
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (event_id, transfer_item_id, sequence, status, recorded_at or _utc_now(), detail),
            )
