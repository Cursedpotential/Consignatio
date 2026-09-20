"""Build a non-destructive migration ledger from rclone CSV inventories."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import chain
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator, Mapping, Sequence

from .schema import SCHEMA_SQL, SCHEMA_VERSION

REQUIRED_COLUMNS = ("bucket", "path", "size", "md5", "modtime", "mimetype")
RCLONE_PSHTM_COLUMNS = ("path", "size", "md5", "modtime", "mimetype")
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
RULE_SET = "casebible-path-observations"
RULE_VERSION = "2026-09-13.v2"
FINGERPRINT_ASSERTION_VERSION = "source-bound-sha256.v1"
REPRESENTATIVE_RULE = "latest-snapshot-then-utf8-ordinal(bucket,path,row_number,occurrence_id).v2"
METADATA_RESOLUTION_RULE = "exact-content-field-resolution.2026-09-13.v2"
METADATA_ASSERTION_CLASSES = {
    "embedded", "external_sidecar", "provider", "catalog", "human",
}
DIAGNOSTIC_METADATA_FIELDS = {
    "payload_eligible", "payload_health", "integrity_status", "byte_readable",
    "hash_verified", "is_placeholder", "corruption_status", "repair_status",
    "validation_status", "parse_status", "error", "errors", "warning", "warnings",
}
UNHEALTHY_METADATA_VALUES = {
    "corrupt", "corrupted", "truncated", "unreadable", "failed", "failure",
    "hash_mismatch", "mismatch", "placeholder", "missing", "unavailable",
    "quarantined", "invalid", "damaged",
}
RECOVERY_WRAPPER_RE = re.compile(
    r"^(?:(?:recovered|recovery|restored|undeleted|salvaged|found|copy[ _-]+of)"
    r"[ _.-]+(?:\d+[ _.-]+)?)",
    re.IGNORECASE,
)
RECOVERY_NAME_RE = re.compile(
    r"(?:^|[ _.-])(?:recovered|recovery|restored|undeleted|salvaged|copy)(?:[ _.-]|$)",
    re.IGNORECASE,
)
DATE_FIELDS = {
    "modtime", "mtime", "modified_at", "created_at", "birthtime", "btime",
    "date_taken", "datetime_original", "exif_datetime_original", "gps_timestamp",
    "media_created_at", "provider_created_at", "provider_modified_at",
    "derived_date", "date_start", "date_end", "filename_date",
}
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


def _normalized_timestamp(value: object) -> str | None:
    """Return a trustworthy UTC-ish ISO timestamp, rejecting common sentinels."""
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    if parsed.year < 1900 or (
        parsed.year in {1970, 1980}
        and (parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second)
        == (1, 1, 0, 0, 0)
    ):
        return None
    if parsed > datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=2):
        return None
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _json_value(value_json: str) -> object:
    try:
        return json.loads(value_json)
    except json.JSONDecodeError:
        return value_json


def _meaningful_value(value: object) -> bool:
    return value not in (None, "", [], {})


def _repair_recovery_filename(name: str) -> tuple[str, bool, bool]:
    """Repair only an explicit wrapper; retain the observed name as provenance."""
    stripped = name.strip()
    repaired = RECOVERY_WRAPPER_RE.sub("", stripped, count=1).strip(" ._-")
    if repaired and repaired != stripped and Path(repaired).suffix:
        return repaired, True, True
    return stripped, False, bool(RECOVERY_NAME_RE.search(stripped))


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


@dataclass(frozen=True)
class MetadataImportResult:
    partition_id: str
    source_path: str
    row_count: int
    assertion_count: int
    already_imported: bool
    bound_record_count: int = 0
    held_record_count: int = 0


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

    @staticmethod
    def _prepare_output_directory(output: Path) -> None:
        """Create a new output boundary and refuse to overwrite any artifact."""
        if output.exists():
            try:
                existing = next(output.iterdir())
            except StopIteration:
                return
            raise FileExistsError(
                f"immutable output directory is not empty: {output} (found {existing.name})"
            )
        output.mkdir(parents=True)

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

    def import_metadata_assertions(
        self, assertion_paths: Iterable[Path | str]
    ) -> list[MetadataImportResult]:
        """Stage metadata rows, bind only safe rows, then append field assertions.

        Every physical input row is retained in ``metadata_import_record``.
        Path, size, MD5, QuickXor, recovery names, and provider match percentages
        are candidate evidence only. They never create or merge content identity.
        A locator-only row can bind when all of its candidates already resolve to
        one SHA-256-verified content group. A trusted source SHA-256 may constrain
        candidates only when ``identity_authority`` explicitly says
        ``sha256_verified``. Ambiguous, unmatched, unverified, malformed, and
        QuickXor-drift rows remain visible and unbound.

        The original one-field NDJSON shape remains supported. Normalizers may
        instead emit one record with an ``assertions`` list; record-level locator
        and provenance values are inherited by every field assertion.
        """
        results: list[MetadataImportResult] = []
        for raw_path in assertion_paths:
            path = Path(raw_path).resolve()
            source_sha256 = _file_sha256(path)
            partition_id = f"metadata-partition:{source_sha256}"
            existing = self.connection.execute(
                "SELECT * FROM metadata_import_partition WHERE partition_id = ?",
                (partition_id,),
            ).fetchone()
            if existing is not None:
                counts = self.connection.execute(
                    """SELECT
                           SUM(CASE WHEN disposition LIKE 'bound_%' THEN 1 ELSE 0 END),
                           SUM(CASE WHEN disposition LIKE 'held_%' THEN 1 ELSE 0 END)
                       FROM metadata_import_record WHERE partition_id = ?""",
                    (partition_id,),
                ).fetchone()
                results.append(
                    MetadataImportResult(
                        partition_id, existing["source_path"], existing["row_count"],
                        existing["assertion_count"], True,
                        int(counts[0] or 0), int(counts[1] or 0),
                    )
                )
                continue
            opener = gzip.open if path.name.casefold().endswith(".gz") else Path.open
            row_count = 0
            assertion_count = 0
            imported_at = _utc_now()
            with self.connection, opener(path, "rt", encoding="utf-8-sig") as handle:
                self.connection.execute(
                    """INSERT INTO metadata_import_partition(
                           partition_id, source_path, source_sha256, imported_at,
                           row_count, assertion_count
                       ) VALUES (?, ?, ?, ?, 0, 0)""",
                    (partition_id, str(path), source_sha256, imported_at),
                )
                for line_number, raw_line in enumerate(handle, start=1):
                    row_count += 1
                    raw_record = raw_line.rstrip("\r\n")
                    raw_sha256 = _sha256_text(raw_record)
                    import_record_id = _stable_id(
                        "metadata-import", partition_id, line_number, raw_sha256
                    )
                    if not raw_record.strip():
                        self._stage_metadata_import_record(
                            import_record_id, partition_id, line_number, raw_sha256,
                            raw_record, {}, "held_blank_record", imported_at,
                        )
                        continue
                    try:
                        record = json.loads(raw_record)
                    except json.JSONDecodeError as exc:
                        self._stage_metadata_import_record(
                            import_record_id, partition_id, line_number, raw_sha256,
                            raw_record, {}, "held_malformed_json", imported_at,
                            {"error": str(exc)},
                        )
                        continue
                    if not isinstance(record, dict):
                        self._stage_metadata_import_record(
                            import_record_id, partition_id, line_number, raw_sha256,
                            raw_record, {}, "held_non_object", imported_at,
                            {"type": type(record).__name__},
                        )
                        continue
                    disposition = "staged"
                    detail: dict[str, object] = {
                        "identity_rule": (
                            "path/size/md5/quickxor/match_percent are candidate assertions only"
                        )
                    }
                    sha256_hint = str(record.get("sha256") or "").strip().casefold()
                    md5_hint = str(record.get("md5") or "").strip().casefold()
                    authority = str(record.get("identity_authority") or "").strip().casefold()
                    if authority in {"source_sha256_ledger", "sha256_verified"}:
                        authority = "sha256_verified"
                    if (sha256_hint and not SHA256_RE.fullmatch(sha256_hint)) or (
                        md5_hint and not MD5_RE.fullmatch(md5_hint)
                    ):
                        disposition = "held_invalid_identity_hint"
                    elif authority == "sha256_verified" and not sha256_hint:
                        disposition = "held_invalid_identity_hint"
                    elif not str(record.get("occurrence_id") or "").strip() and not str(
                        record.get("source_path") or record.get("object_path") or ""
                    ) and not str(record.get("source_filename") or record.get("filename") or ""):
                        disposition = "held_invalid_record"
                    self._stage_metadata_import_record(
                        import_record_id, partition_id, line_number, raw_sha256,
                        raw_record, record, disposition, imported_at, detail,
                    )

                # Candidate generation is set-oriented. Identity hints only
                # constrain a locator when their authority is explicitly strong.
                self.connection.execute(
                    """INSERT OR IGNORE INTO metadata_import_candidate(
                           import_record_id, occurrence_id, content_id,
                           identity_status, match_basis, selected
                       )
                       SELECT r.import_record_id, o.occurrence_id, o.content_id,
                              c.identity_status,
                              CASE
                                WHEN r.explicit_occurrence_id IS NOT NULL
                                  THEN 'explicit_occurrence'
                                WHEN r.identity_authority = 'sha256_verified'
                                  THEN 'locator_plus_verified_sha256'
                                ELSE 'locator_candidate_only'
                              END,
                              0
                       FROM metadata_import_record r
                       JOIN occurrence o
                         ON (
                           (r.explicit_occurrence_id IS NOT NULL
                             AND o.occurrence_id = r.explicit_occurrence_id)
                           OR
                           (r.explicit_occurrence_id IS NULL
                             AND (
                               o.object_path = r.source_path
                               OR (r.source_path IS NULL AND r.source_filename IS NOT NULL
                                   AND (o.object_path = r.source_filename
                                        OR o.object_path LIKE '%/' || r.source_filename))
                             )
                             AND (r.source_bucket IS NULL OR o.bucket = r.source_bucket)
                             AND (r.byte_size IS NULL OR o.byte_size = r.byte_size)
                             AND (r.md5_hint IS NULL OR o.md5_normalized = r.md5_hint))
                         )
                       LEFT JOIN content_identity c ON c.content_id = o.content_id
                       WHERE r.partition_id = ? AND r.disposition = 'staged'
                         AND (
                           r.identity_authority != 'sha256_verified'
                           OR (c.identity_status = 'sha256_verified'
                               AND c.sha256 = r.sha256_hint)
                         )""",
                    (partition_id,),
                )

                # A changing QuickXor for the same provider locator is version
                # drift evidence. Same size does not make those versions equal.
                self.connection.execute(
                    """UPDATE metadata_import_record AS target
                       SET disposition = 'held_quickxor_drift',
                           detail_json = json_set(
                               detail_json, '$.hold_reason',
                               'same locator and size has multiple QuickXor values'
                           )
                       WHERE target.partition_id = ?
                         AND target.disposition = 'staged'
                         AND target.quickxor_hint IS NOT NULL
                         AND EXISTS (
                           SELECT 1
                           FROM metadata_import_record peer
                           WHERE peer.partition_id = target.partition_id
                             AND COALESCE(peer.source_system, '') = COALESCE(target.source_system, '')
                             AND COALESCE(peer.source_account, '') = COALESCE(target.source_account, '')
                             AND COALESCE(peer.source_tree, '') = COALESCE(target.source_tree, '')
                             AND COALESCE(peer.source_path, '') = COALESCE(target.source_path, '')
                             AND COALESCE(peer.byte_size, -1) = COALESCE(target.byte_size, -1)
                             AND peer.quickxor_hint IS NOT NULL
                             AND peer.quickxor_hint != target.quickxor_hint
                         )""",
                    (partition_id,),
                )

                aggregates = self.connection.execute(
                    """SELECT r.import_record_id, r.explicit_occurrence_id,
                              r.identity_authority,
                              COUNT(c.occurrence_id) AS candidate_count,
                              COUNT(DISTINCT c.content_id) AS content_count,
                              SUM(CASE WHEN c.identity_status = 'sha256_verified'
                                       THEN 0 ELSE 1 END) AS unverified_count
                       FROM metadata_import_record r
                       LEFT JOIN metadata_import_candidate c
                         ON c.import_record_id = r.import_record_id
                       WHERE r.partition_id = ? AND r.disposition = 'staged'
                       GROUP BY r.import_record_id, r.explicit_occurrence_id,
                                r.identity_authority
                       ORDER BY r.import_record_id""",
                    (partition_id,),
                ).fetchall()
                dispositions: list[tuple[str, str]] = []
                for row in aggregates:
                    if row["candidate_count"] == 0:
                        disposition = "held_unmatched_occurrence"
                    elif row["explicit_occurrence_id"]:
                        disposition = "bound_explicit_occurrence"
                    elif row["content_count"] > 1:
                        disposition = "held_ambiguous_occurrence"
                    elif row["unverified_count"]:
                        disposition = "held_unverified_candidates"
                    elif row["identity_authority"] == "sha256_verified":
                        disposition = "bound_verified_sha256"
                    else:
                        disposition = "bound_unique_verified_content"
                    dispositions.append((disposition, row["import_record_id"]))
                self.connection.executemany(
                    "UPDATE metadata_import_record SET disposition = ? WHERE import_record_id = ?",
                    dispositions,
                )
                self.connection.execute(
                    """UPDATE metadata_import_record AS target
                       SET selected_occurrence_id = (
                         SELECT c.occurrence_id
                         FROM metadata_import_candidate c
                         JOIN occurrence o USING (occurrence_id)
                         JOIN inventory_batch b USING (inventory_id)
                         WHERE c.import_record_id = target.import_record_id
                         ORDER BY b.captured_at DESC, o.row_number DESC,
                                  o.occurrence_id
                         LIMIT 1
                       )
                       WHERE target.partition_id = ?
                         AND target.disposition LIKE 'bound_%'""",
                    (partition_id,),
                )
                self.connection.execute(
                    """UPDATE metadata_import_candidate AS candidate
                       SET selected = 1
                       WHERE EXISTS (
                         SELECT 1 FROM metadata_import_record record
                         WHERE record.import_record_id = candidate.import_record_id
                           AND record.selected_occurrence_id = candidate.occurrence_id
                           AND record.partition_id = ?
                       )""",
                    (partition_id,),
                )

                bound_cursor = self.connection.execute(
                    """SELECT import_record_id, raw_record,
                              selected_occurrence_id, asserted_at
                       FROM metadata_import_record
                       WHERE partition_id = ? AND disposition LIKE 'bound_%'
                       ORDER BY line_number""",
                    (partition_id,),
                )
                while batch := bound_cursor.fetchmany(5_000):
                    assertion_rows: list[tuple[object, ...]] = []
                    invalid_records: list[tuple[str]] = []
                    for staged in batch:
                        record = json.loads(staged["raw_record"])
                        try:
                            normalized = self._normalized_metadata_assertions(
                                record, staged["selected_occurrence_id"],
                                staged["import_record_id"], staged["asserted_at"],
                            )
                        except (TypeError, ValueError, json.JSONDecodeError):
                            invalid_records.append((staged["import_record_id"],))
                            continue
                        assertion_rows.extend(normalized)
                    if invalid_records:
                        self.connection.executemany(
                            """UPDATE metadata_import_record
                               SET disposition = 'held_invalid_record',
                                   selected_occurrence_id = NULL
                               WHERE import_record_id = ?""",
                            invalid_records,
                        )
                    before = self.connection.total_changes
                    self.connection.executemany(
                        """INSERT OR IGNORE INTO metadata_assertion(
                               metadata_assertion_id, occurrence_id, field_name,
                               value_json, assertion_class, source_system,
                               source_table, source_key, source_path, confidence,
                               trust_score, observed_at, asserted_at, rule_version,
                               detail_json
                           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        assertion_rows,
                    )
                    assertion_count += self.connection.total_changes - before
                self.connection.execute(
                    """UPDATE metadata_import_partition
                       SET row_count = ?, assertion_count = ? WHERE partition_id = ?""",
                    (row_count, assertion_count, partition_id),
                )
                counts = self.connection.execute(
                    """SELECT
                           SUM(CASE WHEN disposition LIKE 'bound_%' THEN 1 ELSE 0 END),
                           SUM(CASE WHEN disposition LIKE 'held_%' THEN 1 ELSE 0 END)
                       FROM metadata_import_record WHERE partition_id = ?""",
                    (partition_id,),
                ).fetchone()
            results.append(
                MetadataImportResult(
                    partition_id, str(path), row_count, assertion_count, False,
                    int(counts[0] or 0), int(counts[1] or 0),
                )
            )
        return results

    def _stage_metadata_import_record(
        self,
        import_record_id: str,
        partition_id: str,
        line_number: int,
        raw_sha256: str,
        raw_record: str,
        record: Mapping[str, object],
        disposition: str,
        asserted_at: str,
        detail: Mapping[str, object] | None = None,
    ) -> None:
        def text_value(*names: str) -> str | None:
            for name in names:
                value = record.get(name)
                if value not in (None, ""):
                    return str(value).strip() or None
            return None

        byte_size: int | None = None
        raw_size = record.get("byte_size", record.get("size"))
        if raw_size not in (None, ""):
            try:
                byte_size = int(raw_size)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                disposition = "held_invalid_record"
        match_percent: float | None = None
        raw_match = record.get("match_percent", record.get("match%"))
        if raw_match not in (None, ""):
            try:
                match_percent = float(raw_match)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                disposition = "held_invalid_record"
        authority = (text_value("identity_authority") or "").casefold()
        if authority in {"source_sha256_ledger", "sha256_verified"}:
            authority = "sha256_verified"
        self.connection.execute(
            """INSERT INTO metadata_import_record(
                   import_record_id, partition_id, line_number, raw_sha256,
                   raw_record, source_system, source_table, source_key,
                   source_account, source_tree, snapshot_id, source_version,
                   explicit_occurrence_id, source_bucket, source_path,
                   source_filename, byte_size, sha256_hint, md5_hint, quickxor_hint,
                   match_percent, identity_authority, disposition,
                   selected_occurrence_id, detail_json, asserted_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
            (
                import_record_id, partition_id, line_number, raw_sha256,
                raw_record, text_value("source_system"), text_value("source_table"),
                text_value("source_key"), text_value("source_account", "account"),
                text_value("source_tree", "tree"), text_value("snapshot_id", "scan_file"),
                text_value("source_version"), text_value("occurrence_id"),
                text_value("source_bucket", "bucket"),
                text_value("source_path", "object_path"),
                text_value("source_filename", "filename"),
                byte_size,
                (text_value("sha256") or "").casefold() or None,
                (text_value("md5") or "").casefold() or None,
                text_value("quickxor", "quickxor_hint"), match_percent,
                authority or "candidate_only", disposition,
                json.dumps(dict(detail or {}), ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")), asserted_at,
            ),
        )

    @staticmethod
    def _normalized_metadata_assertions(
        record: Mapping[str, object], occurrence_id: str,
        import_record_id: str, imported_at: str,
    ) -> list[tuple[object, ...]]:
        raw_items = record.get("assertions")
        if raw_items is None:
            items: list[Mapping[str, object]] = [record]
        elif isinstance(raw_items, list) and all(isinstance(item, dict) for item in raw_items):
            items = raw_items  # type: ignore[assignment]
        else:
            raise ValueError("assertions must be a list of objects")
        rows: list[tuple[object, ...]] = []
        for index, item in enumerate(items):
            field_name = str(item.get("field_name") or item.get("field") or "").strip().casefold()
            if not re.fullmatch(r"[a-z0-9_.:-]+", field_name):
                raise ValueError("invalid metadata field_name")
            if "value_json" in item:
                raw_value_json = item["value_json"]
                value = json.loads(raw_value_json) if isinstance(raw_value_json, str) else raw_value_json
            elif "value" in item:
                value = item["value"]
            else:
                raise ValueError("missing metadata value")
            value_json = json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"))
            assertion_class = str(
                item.get("assertion_class") or record.get("assertion_class") or "catalog"
            ).strip().casefold()
            if assertion_class not in METADATA_ASSERTION_CLASSES:
                raise ValueError("invalid assertion_class")
            source_system = str(
                item.get("source_system") or record.get("source_system") or "casebible-pg18"
            ).strip()
            source_table = str(item.get("source_table") or record.get("source_table") or "").strip()
            source_key = str(item.get("source_key") or record.get("source_key") or "").strip()
            if not source_system or not source_table or not source_key:
                raise ValueError("source_system, source_table, and source_key are required")
            confidence = float(item.get("confidence", record.get("confidence", 0.8)))
            trust_score = int(item.get("trust_score", record.get("trust_score", 70)))
            if not 0.0 <= confidence <= 1.0 or not 0 <= trust_score <= 100:
                raise ValueError("invalid confidence/trust_score")
            detail = item.get("detail", item.get("detail_json", record.get("detail", {})))
            if isinstance(detail, str):
                try:
                    detail = json.loads(detail)
                except json.JSONDecodeError:
                    detail = {"raw": detail}
            source_path = str(record.get("source_path") or record.get("object_path") or "") or None
            observed_at = str(item.get("observed_at") or record.get("observed_at") or "") or None
            asserted_at = str(item.get("asserted_at") or record.get("asserted_at") or imported_at)
            assertion_id = _stable_id(
                "metadata", import_record_id, index, occurrence_id, field_name,
                value_json, assertion_class, source_system, source_table, source_key,
                source_path or "", confidence, trust_score, observed_at or "",
                METADATA_RESOLUTION_RULE,
            )
            rows.append(
                (
                    assertion_id, occurrence_id, field_name, value_json,
                    assertion_class, source_system, source_table, source_key,
                    source_path, confidence, trust_score, observed_at,
                    asserted_at, METADATA_RESOLUTION_RULE,
                    json.dumps(detail, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")),
                )
            )
        return rows

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

    def _metadata_observations(self, content_id: str) -> list[dict[str, object]]:
        observations: list[dict[str, object]] = []
        occurrences = self.connection.execute(
            """SELECT o.*, b.captured_at
               FROM occurrence o JOIN inventory_batch b USING (inventory_id)
               WHERE o.content_id = ?
               ORDER BY o.occurrence_id""",
            (content_id,),
        ).fetchall()
        fingerprints_by_occurrence: dict[str, list[sqlite3.Row]] = {}
        for fingerprint in self.connection.execute(
            """SELECT f.fingerprint_assertion_id, f.occurrence_id,
                      f.source_version, f.source_etag, f.verified_at
               FROM strong_fingerprint_assertion f
               JOIN occurrence o USING (occurrence_id)
               WHERE o.content_id = ?
               ORDER BY f.occurrence_id, f.fingerprint_assertion_id""",
            (content_id,),
        ):
            fingerprints_by_occurrence.setdefault(
                str(fingerprint["occurrence_id"]), []
            ).append(fingerprint)
        for row in occurrences:
            synthetic = (
                ("observed_filename", PurePosixPath(row["object_path"]).name, 55, 0.65),
                ("source_path", row["object_path"], 100, 1.0),
                ("modtime", row["modtime_raw"], 60, 0.70),
                ("mimetype", row["mimetype_raw"], 55, 0.65),
                ("inventory_captured_at", row["captured_at"], 70, 1.0),
            )
            for field_name, value, trust_score, confidence in synthetic:
                if not _meaningful_value(value):
                    continue
                value_json = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                observations.append(
                    {
                        "assertion_id": _stable_id(
                            "observed-metadata", row["occurrence_id"], field_name, value_json
                        ),
                        "occurrence_id": row["occurrence_id"],
                        "field_name": field_name,
                        "value": value,
                        "value_json": value_json,
                        "assertion_class": "inventory",
                        "source_system": "rclone-inventory",
                        "source_table": "occurrence",
                        "source_key": row["occurrence_id"],
                        "source_path": row["object_path"],
                        "confidence": confidence,
                        "trust_score": trust_score,
                        "observed_at": row["captured_at"],
                        "detail_json": "{}",
                    }
                )
            for fingerprint in fingerprints_by_occurrence.get(
                str(row["occurrence_id"]), []
            ):
                for field_name in ("source_version", "source_etag"):
                    value = fingerprint[field_name]
                    if not _meaningful_value(value):
                        continue
                    value_json = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    observations.append(
                        {
                            "assertion_id": _stable_id(
                                "observed-metadata", fingerprint["fingerprint_assertion_id"],
                                field_name, value_json,
                            ),
                            "occurrence_id": row["occurrence_id"],
                            "field_name": field_name,
                            "value": value,
                            "value_json": value_json,
                            "assertion_class": "provider",
                            "source_system": "sha256-ledger",
                            "source_table": "strong_fingerprint_assertion",
                            "source_key": fingerprint["fingerprint_assertion_id"],
                            "source_path": row["object_path"],
                            "confidence": 0.9,
                            "trust_score": 80,
                            "observed_at": fingerprint["verified_at"],
                            "detail_json": "{}",
                        }
                    )
        for row in self.connection.execute(
            """SELECT m.*, o.object_path
               FROM metadata_assertion m
               JOIN occurrence o USING (occurrence_id)
               WHERE o.content_id = ?
               ORDER BY m.metadata_assertion_id""",
            (content_id,),
        ):
            observations.append(
                {
                    "assertion_id": row["metadata_assertion_id"],
                    "occurrence_id": row["occurrence_id"],
                    "field_name": row["field_name"],
                    "value": _json_value(row["value_json"]),
                    "value_json": row["value_json"],
                    "assertion_class": row["assertion_class"],
                    "source_system": row["source_system"],
                    "source_table": row["source_table"],
                    "source_key": row["source_key"],
                    "source_path": row["source_path"] or row["object_path"],
                    "confidence": row["confidence"],
                    "trust_score": row["trust_score"],
                    "observed_at": row["observed_at"] or "",
                    "detail_json": row["detail_json"],
                }
            )
        return observations

    @staticmethod
    def _observation_normalized_value(observation: Mapping[str, object]) -> str:
        field_name = str(observation["field_name"])
        value = observation["value"]
        if field_name in DATE_FIELDS:
            return _normalized_timestamp(value) or ""
        if isinstance(value, str):
            return value.strip().casefold()
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def resolve_metadata(self, resolved_at: str | None = None) -> int:
        """Create idempotent resolution snapshots for exact-content groups."""
        resolved_at = resolved_at or _utc_now()
        content_ids = self.connection.execute(
            """SELECT content_id FROM content_identity
               WHERE identity_status = 'sha256_verified'
                 AND content_id IN (SELECT DISTINCT content_id FROM occurrence)
               ORDER BY content_id"""
        ).fetchall()
        resolution_count = 0
        with self.connection:
            for identity in content_ids:
                content_id = str(identity["content_id"])
                observations = self._metadata_observations(content_id)
                if not observations:
                    continue
                input_rows = [
                    {
                        "id": row["assertion_id"],
                        "occurrence_id": row["occurrence_id"],
                        "field": row["field_name"],
                        "value_json": row["value_json"],
                        "class": row["assertion_class"],
                        "confidence": row["confidence"],
                        "trust_score": row["trust_score"],
                    }
                    for row in observations
                ]
                input_set_sha256 = _sha256_text(
                    json.dumps(
                        sorted(input_rows, key=lambda row: str(row["id"])),
                        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                    )
                )

                occurrence_rows = self.connection.execute(
                    """SELECT occurrence_id, bucket, object_path
                       FROM occurrence WHERE content_id = ?
                       ORDER BY occurrence_id""",
                    (content_id,),
                ).fetchall()
                donor_scores: list[tuple[tuple[object, ...], sqlite3.Row]] = []
                for occurrence in occurrence_rows:
                    occurrence_observations = [
                        row for row in observations
                        if row["occurrence_id"] == occurrence["occurrence_id"]
                    ]
                    trusted = [
                        row for row in occurrence_observations
                        if int(row["trust_score"]) >= 50
                        and float(row["confidence"]) >= 0.5
                        and _meaningful_value(row["value"])
                    ]
                    valid_dates = [
                        normalized
                        for row in trusted
                        if str(row["field_name"]) in DATE_FIELDS
                        and (normalized := _normalized_timestamp(row["value"]))
                    ]
                    valid_date_fields = {
                        str(row["field_name"])
                        for row in trusted
                        if str(row["field_name"]) in DATE_FIELDS
                        and _normalized_timestamp(row["value"])
                    }
                    meaningful_fields = {
                        str(row["field_name"])
                        for row in trusted
                        if str(row["field_name"])
                        not in {
                            "source_path", "observed_filename", "inventory_captured_at",
                            *DIAGNOSTIC_METADATA_FIELDS,
                        }
                        and (
                            str(row["field_name"]) not in DATE_FIELDS
                            or _normalized_timestamp(row["value"])
                        )
                    }
                    exif_fields = {
                        str(row["field_name"])
                        for row in trusted
                        if str(row["field_name"]).startswith(("exif", "gps"))
                    }
                    earliest = min(valid_dates) if valid_dates else "9999-12-31T23:59:59Z"
                    metadata_coverage_score = (
                        4 * len(valid_date_fields)
                        + 3 * len(exif_fields)
                        + len(meaningful_fields)
                    )
                    path_eligible = (
                        _payload_source_hold_reason(str(occurrence["object_path"])) is None
                    )
                    health_assertions = [
                        row for row in trusted
                        if str(row["field_name"]) in DIAGNOSTIC_METADATA_FIELDS
                    ]
                    health_failures: list[str] = []
                    health_successes = 0
                    for diagnostic in health_assertions:
                        field_name = str(diagnostic["field_name"])
                        value = diagnostic["value"]
                        normalized_value = str(value).strip().casefold()
                        is_negative_boolean = (
                            field_name in {"payload_eligible", "byte_readable", "hash_verified"}
                            and value is False
                        ) or (field_name == "is_placeholder" and value is True)
                        if is_negative_boolean or normalized_value in UNHEALTHY_METADATA_VALUES:
                            health_failures.append(f"{field_name}={normalized_value}")
                        elif (
                            (field_name in {"payload_eligible", "byte_readable", "hash_verified"}
                             and value is True)
                            or normalized_value in {"healthy", "verified", "readable", "complete", "ok"}
                        ):
                            health_successes += 1
                    health_eligible = not health_failures
                    payload_eligible = path_eligible and health_eligible
                    health_rank = 0 if health_successes else 1
                    score = (
                        int(not payload_eligible),
                        health_rank,
                        -metadata_coverage_score,
                        -len(valid_date_fields),
                        -len(exif_fields),
                        -len(meaningful_fields),
                        -sum(int(row["trust_score"]) for row in trusted),
                        earliest,
                        str(occurrence["occurrence_id"]),
                    )
                    occurrence_with_health = dict(occurrence)
                    occurrence_with_health["payload_eligible"] = payload_eligible
                    occurrence_with_health["health_eligible"] = health_eligible
                    occurrence_with_health["health_failures"] = health_failures
                    occurrence_with_health["health_assertion_count"] = len(health_assertions)
                    donor_scores.append((score, occurrence_with_health))
                donor_scores.sort(key=lambda item: item[0])
                primary = donor_scores[0][1]
                eligible_donor_count = sum(
                    1 for _, occurrence in donor_scores
                    if occurrence["payload_eligible"]
                )
                health_eligible_donor_count = sum(
                    1 for _, occurrence in donor_scores
                    if occurrence["health_eligible"]
                )

                name_fields = {
                    "original_filename", "native_filename", "filename",
                    "display_filename", "observed_filename",
                }
                name_candidates: list[dict[str, object]] = []
                class_bonus = {
                    "human": 100, "embedded": 80, "provider": 60,
                    "catalog": 40, "inventory": 0, "external_sidecar": 30,
                }
                field_bonus = {
                    "original_filename": 500, "native_filename": 450,
                    "filename": 350, "display_filename": 325,
                    "observed_filename": 300,
                }
                for observation in observations:
                    if observation["field_name"] not in name_fields or not isinstance(observation["value"], str):
                        continue
                    repaired, was_repaired, unrepaired_recovery = _repair_recovery_filename(
                        str(observation["value"])
                    )
                    if not repaired:
                        continue
                    quality = (
                        field_bonus[str(observation["field_name"])]
                        + class_bonus.get(str(observation["assertion_class"]), 0)
                        + int(observation["trust_score"])
                        + int(float(observation["confidence"]) * 20)
                        + (20 if was_repaired else 60 if not unrepaired_recovery else -200)
                    )
                    name_candidates.append(
                        {
                            "assertion": observation,
                            "name": repaired,
                            "quality": quality,
                            "was_repaired": was_repaired,
                            "unrepaired_recovery": unrepaired_recovery,
                        }
                    )
                name_candidates.sort(
                    key=lambda item: (
                        -int(item["quality"]),
                        str(item["name"]).encode("utf-8"),
                        str(item["assertion"]["assertion_id"]),  # type: ignore[index]
                    )
                )
                selected_name = name_candidates[0]
                top_names = {
                    str(item["name"]).casefold()
                    for item in name_candidates
                    if item["quality"] == selected_name["quality"]
                }
                canonical_name_review = len(top_names) > 1

                valid_timestamp_observations = [
                    (row, normalized)
                    for row in observations
                    if str(row["field_name"]) in DATE_FIELDS
                    and int(row["trust_score"]) >= 50
                    and float(row["confidence"]) >= 0.5
                    and (normalized := _normalized_timestamp(row["value"]))
                ]
                valid_timestamp_observations.sort(
                    key=lambda item: (item[1], str(item[0]["assertion_id"]))
                )
                oldest = valid_timestamp_observations[0] if valid_timestamp_observations else None

                fields: dict[str, list[dict[str, object]]] = {}
                for row in observations:
                    fields.setdefault(str(row["field_name"]), []).append(row)
                field_resolutions: list[dict[str, object]] = []
                overall_review = canonical_name_review or health_eligible_donor_count == 0
                embedded_conflict = False
                for field_name, candidates in sorted(fields.items()):
                    eligible: list[dict[str, object]] = []
                    for row in candidates:
                        normalized = self._observation_normalized_value(row)
                        if not normalized:
                            continue
                        enriched = dict(row)
                        enriched["normalized"] = normalized
                        eligible.append(enriched)
                    embedded_values = {
                        str(row["normalized"])
                        for row in eligible
                        if row["assertion_class"] == "embedded"
                    }
                    field_embedded_conflict = len(embedded_values) > 1
                    embedded_conflict = embedded_conflict or field_embedded_conflict
                    eligible.sort(
                        key=lambda row: (
                            -int(row["trust_score"]), -float(row["confidence"]),
                            str(row["normalized"]), str(row["assertion_id"]),
                        )
                    )
                    selected = eligible[0] if eligible else None
                    top_values = {
                        str(row["normalized"])
                        for row in eligible
                        if selected is not None
                        and row["trust_score"] == selected["trust_score"]
                        and row["confidence"] == selected["confidence"]
                    }
                    field_review = len(top_values) > 1
                    overall_review = overall_review or field_review
                    state = (
                        "blocked_embedded_conflict" if field_embedded_conflict
                        else "review_required" if field_review else "resolved"
                    )
                    field_resolutions.append(
                        {
                            "field_name": field_name,
                            "selected": selected,
                            "state": state,
                            "alternatives": [
                                {
                                    "assertion_id": row["assertion_id"],
                                    "occurrence_id": row["occurrence_id"],
                                    "value_json": row["value_json"],
                                    "source_system": row["source_system"],
                                    "source_table": row["source_table"],
                                    "source_key": row["source_key"],
                                    "confidence": row["confidence"],
                                    "trust_score": row["trust_score"],
                                }
                                for row in eligible
                            ],
                        }
                    )
                state = (
                    "blocked_embedded_conflict" if embedded_conflict
                    else "review_required" if overall_review else "resolved"
                )
                reasons = {
                    "primary_donor": "payload eligibility and health are evaluated before metadata richness; diagnostic fields can reduce fitness but never increase metadata coverage",
                    "primary_payload_eligible": bool(primary["payload_eligible"]),
                    "eligible_payload_donor_count": eligible_donor_count,
                    "health_eligible_donor_count": health_eligible_donor_count,
                    "primary_health_failures": primary["health_failures"],
                    "primary_health_assertion_count": primary["health_assertion_count"],
                    "canonical_filename": "selected independently from original/native/name observations; explicit recovery wrappers may be repaired while observed names remain assertions",
                    "canonical_filename_review_required": canonical_name_review,
                    "embedded_conflict": embedded_conflict,
                }
                resolution_id = _stable_id(
                    "metadata-resolution", content_id, input_set_sha256,
                    METADATA_RESOLUTION_RULE,
                )
                self.connection.execute(
                    """INSERT OR IGNORE INTO content_metadata_resolution(
                           resolution_id, content_id, primary_occurrence_id,
                           canonical_filename, canonical_filename_assertion_id,
                           oldest_trustworthy_timestamp,
                           oldest_timestamp_assertion_id, resolution_state,
                           rule_version, reasons_json, input_set_sha256, resolved_at
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        resolution_id, content_id, primary["occurrence_id"],
                        selected_name["name"],
                        selected_name["assertion"]["assertion_id"],  # type: ignore[index]
                        oldest[1] if oldest else None,
                        oldest[0]["assertion_id"] if oldest else None,
                        state, METADATA_RESOLUTION_RULE,
                        json.dumps(reasons, sort_keys=True, separators=(",", ":")),
                        input_set_sha256, resolved_at,
                    ),
                )
                for field in field_resolutions:
                    selected = field["selected"]
                    field_resolution_id = _stable_id(
                        "field-resolution", resolution_id, field["field_name"]
                    )
                    self.connection.execute(
                        """INSERT OR IGNORE INTO metadata_field_resolution(
                               field_resolution_id, resolution_id, field_name,
                               selected_assertion_id, selected_value_json,
                               resolution_state, alternatives_json, reasons_json
                           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            field_resolution_id, resolution_id, field["field_name"],
                            selected["assertion_id"] if selected else None,
                            selected["value_json"] if selected else None,
                            field["state"],
                            json.dumps(field["alternatives"], ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                            json.dumps({"selection": "highest trust, then confidence; tied differing values require review"}, separators=(",", ":")),
                        ),
                    )
                resolution_count += 1
        return resolution_count

    def _current_content_holds(self) -> dict[str, str]:
        """Return exact-content groups that cannot enter payload execution."""
        holds: dict[str, str] = {}
        for row in self.connection.execute(
            """SELECT content_id, resolution_state, reasons_json
               FROM current_content_metadata_resolution ORDER BY content_id"""
        ):
            reasons = _json_value(row["reasons_json"])
            if row["resolution_state"] == "blocked_embedded_conflict":
                holds[str(row["content_id"])] = "held_embedded_metadata_conflict"
            elif isinstance(reasons, dict) and reasons.get("health_eligible_donor_count") == 0:
                holds[str(row["content_id"])] = "held_no_healthy_payload_donor"
        return holds

    def build_generation(
        self,
        output_dir: Path | str,
        destination_remote: str = "b2:",
        destination_prefix: str = "consignatio/intake/raw-dedupe/v1",
        generation_id: str | None = None,
        created_at: str | None = None,
    ) -> BuildResult:
        output = Path(output_dir)
        self._prepare_output_directory(output)
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
        metadata_assertions = self.connection.execute(
            """SELECT metadata_assertion_id, value_json
               FROM metadata_assertion ORDER BY metadata_assertion_id"""
        ).fetchall()
        active_bridge = self._active_bridge_finalization()
        fingerprint_set_sha256 = _sha256_text(
            "\n".join(
                [
                    *(f"{row['fingerprint_assertion_id']}:{row['sha256']}" for row in fingerprints),
                    *(
                        f"metadata:{row['metadata_assertion_id']}:{row['value_json']}"
                        for row in metadata_assertions
                    ),
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
        self.resolve_metadata(resolved_at=created_at)
        content_holds = self._current_content_holds()
        blocked_content_ids = set(content_holds)
        held_resolution_count = len(content_holds)
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
            self.connection.execute("DROP TABLE IF EXISTS temp.location_content_count")
            self.connection.execute(
                """CREATE TEMP TABLE location_content_count AS
                   SELECT bucket, object_path,
                          COUNT(DISTINCT content_id) AS location_content_count
                   FROM occurrence GROUP BY bucket, object_path"""
            )
            self.connection.execute(
                """CREATE INDEX location_content_count_idx
                   ON location_content_count(bucket, object_path)"""
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
                    """SELECT o.*, b.captured_at, location.location_content_count
                       FROM current_content_metadata_resolution r
                       JOIN occurrence o
                         ON o.occurrence_id = r.primary_occurrence_id
                        AND o.content_id = r.content_id
                       JOIN inventory_batch b USING (inventory_id)
                       JOIN content_identity c USING (content_id)
                       JOIN location_content_count location
                         ON location.bucket = o.bucket
                        AND location.object_path = o.object_path
                       WHERE c.identity_status = 'sha256_verified'
                         AND r.resolution_state != 'blocked_embedded_conflict'"""
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
                        if identity["content_id"] in blocked_content_ids:
                            # This exact-content group is visible in metadata
                            # hold output but cannot enter executable transfer rows.
                            continue
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
                                          location.location_content_count,
                                          ROW_NUMBER() OVER (
                                              PARTITION BY o.bucket, o.object_path
                                              ORDER BY b.captured_at DESC, o.row_number DESC,
                                                       o.occurrence_id
                                          ) AS location_rank
                                   FROM occurrence o
                                   JOIN inventory_batch b USING (inventory_id)
                                   JOIN location_content_count location
                                     ON location.bucket = o.bucket
                                    AND location.object_path = o.object_path
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
                        if representative["location_content_count"] > 1:
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
                            METADATA_RESOLUTION_RULE
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
        del sha_representatives, inherited_content_ids, blocked_content_ids, content_holds
        files_count = self._write_outputs(generation_id, output)
        parquet_written = self._write_parquet(output / "parquet")
        counts = self.connection.execute(
            """SELECT
                 (SELECT COUNT(*) FROM occurrence) AS occurrences,
                 (SELECT COUNT(*) FROM content_identity WHERE identity_status = 'sha256_verified'
                    AND content_id IN (SELECT DISTINCT content_id FROM occurrence)) AS sha256_count,
                 (SELECT COUNT(*) FROM content_identity WHERE identity_status = 'md5_size_candidate'
                    AND content_id IN (SELECT DISTINCT content_id FROM occurrence)) AS candidate_count,
                 ((SELECT COUNT(*) FROM transfer_item WHERE generation_id = ? AND initial_status LIKE 'held_%')
                  + ?) AS held_count""",
            (generation_id, held_resolution_count),
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
        self._write_metadata_resolution(output)
        return planned_count

    def write_metadata_resolution(
        self, output_dir: Path | str, resolved_at: str | None = None
    ) -> int:
        """Resolve exact-content metadata and export every competing assertion."""
        count = self.resolve_metadata(resolved_at=resolved_at)
        output = Path(output_dir)
        self._prepare_output_directory(output)
        self._write_metadata_resolution(output)
        return count

    def _write_metadata_resolution(self, output: Path) -> None:
        fields = (
            "resolution_id", "content_id", "resolution_state", "rule_version",
            "primary_occurrence_id", "canonical_filename",
            "oldest_trustworthy_timestamp", "assertion_id", "occurrence_id",
            "is_primary_metadata_donor", "is_canonical_filename_assertion",
            "is_oldest_timestamp_assertion", "field_name", "value_json",
            "assertion_class", "source_system", "source_table", "source_key",
            "source_path", "confidence", "trust_score", "observed_at",
            "field_resolution_state", "is_selected_field_value",
        )
        with (output / "metadata-resolution.csv").open(
            "w", encoding="utf-8", newline=""
        ) as csv_handle, (output / "metadata-resolution.jsonl").open(
            "w", encoding="utf-8", newline="\n"
        ) as jsonl_handle:
            writer = csv.DictWriter(csv_handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for resolution in self.connection.execute(
                """SELECT r.* FROM current_content_metadata_resolution r
                   JOIN occurrence o
                     ON o.occurrence_id = r.primary_occurrence_id
                    AND o.content_id = r.content_id
                   ORDER BY r.content_id"""
            ):
                selected_fields = {
                    row["field_name"]: row
                    for row in self.connection.execute(
                        """SELECT * FROM metadata_field_resolution
                           WHERE resolution_id = ? ORDER BY field_name""",
                        (resolution["resolution_id"],),
                    )
                }
                assertions = self._metadata_observations(resolution["content_id"])
                assertions.sort(
                    key=lambda row: (
                        str(row["field_name"]), str(row["assertion_id"])
                    )
                )
                for assertion in assertions:
                    field_resolution = selected_fields.get(str(assertion["field_name"]))
                    row = {
                    "resolution_id": resolution["resolution_id"],
                    "content_id": resolution["content_id"],
                    "resolution_state": resolution["resolution_state"],
                    "rule_version": resolution["rule_version"],
                    "primary_occurrence_id": resolution["primary_occurrence_id"],
                    "canonical_filename": resolution["canonical_filename"],
                    "oldest_trustworthy_timestamp": resolution["oldest_trustworthy_timestamp"] or "",
                    "assertion_id": assertion["assertion_id"],
                    "occurrence_id": assertion["occurrence_id"],
                    "is_primary_metadata_donor": int(
                        assertion["occurrence_id"] == resolution["primary_occurrence_id"]
                    ),
                    "is_canonical_filename_assertion": int(
                        assertion["assertion_id"] == resolution["canonical_filename_assertion_id"]
                    ),
                    "is_oldest_timestamp_assertion": int(
                        assertion["assertion_id"] == resolution["oldest_timestamp_assertion_id"]
                    ),
                    "field_name": assertion["field_name"],
                    "value_json": assertion["value_json"],
                    "assertion_class": assertion["assertion_class"],
                    "source_system": assertion["source_system"],
                    "source_table": assertion["source_table"],
                    "source_key": assertion["source_key"],
                    "source_path": assertion["source_path"],
                    "confidence": assertion["confidence"],
                    "trust_score": assertion["trust_score"],
                    "observed_at": assertion["observed_at"],
                    "field_resolution_state": (
                        field_resolution["resolution_state"] if field_resolution else ""
                    ),
                    "is_selected_field_value": int(
                        field_resolution is not None
                        and assertion["assertion_id"] == field_resolution["selected_assertion_id"]
                    ),
                    }
                    writer.writerow(row)
                    jsonl_handle.write(
                        json.dumps(
                            row, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )

        hold_fields = (
            "content_id", "resolution_id", "resolution_state", "hold_reason",
            "primary_occurrence_id", "canonical_filename", "rule_version",
            "reasons_json",
        )
        with (output / "metadata-holds.csv").open(
            "w", encoding="utf-8", newline=""
        ) as csv_handle, (output / "metadata-holds.jsonl").open(
            "w", encoding="utf-8", newline="\n"
        ) as jsonl_handle:
            writer = csv.DictWriter(csv_handle, fieldnames=hold_fields, lineterminator="\n")
            writer.writeheader()
            for resolution in self.connection.execute(
                """SELECT * FROM current_content_metadata_resolution
                   WHERE resolution_state != 'resolved'
                   ORDER BY content_id"""
            ):
                reasons = _json_value(resolution["reasons_json"])
                if resolution["resolution_state"] == "blocked_embedded_conflict":
                    hold_reason = "held_embedded_metadata_conflict"
                elif isinstance(reasons, dict) and reasons.get("health_eligible_donor_count") == 0:
                    hold_reason = "held_no_healthy_payload_donor"
                else:
                    hold_reason = "held_metadata_review_required"
                row = {
                    "content_id": resolution["content_id"],
                    "resolution_id": resolution["resolution_id"],
                    "resolution_state": resolution["resolution_state"],
                    "hold_reason": hold_reason,
                    "primary_occurrence_id": resolution["primary_occurrence_id"],
                    "canonical_filename": resolution["canonical_filename"],
                    "rule_version": resolution["rule_version"],
                    "reasons_json": resolution["reasons_json"],
                }
                writer.writerow(row)
                jsonl_handle.write(
                    json.dumps(row, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n"
                )

        import_fields = (
            "import_record_id", "partition_id", "line_number", "disposition",
            "source_system", "source_table", "source_key", "source_account",
            "source_tree", "snapshot_id", "source_version", "source_bucket",
            "source_path", "source_filename", "byte_size", "sha256_hint",
            "md5_hint", "quickxor_hint", "match_percent", "identity_authority",
            "selected_occurrence_id", "candidate_occurrence_id",
            "candidate_content_id", "candidate_identity_status", "match_basis",
            "candidate_selected", "detail_json", "raw_sha256", "raw_record",
        )
        with (output / "metadata-import-review.csv").open(
            "w", encoding="utf-8", newline=""
        ) as csv_handle, (output / "metadata-import-review.jsonl").open(
            "w", encoding="utf-8", newline="\n"
        ) as jsonl_handle:
            writer = csv.DictWriter(csv_handle, fieldnames=import_fields, lineterminator="\n")
            writer.writeheader()
            cursor = self.connection.execute(
                """SELECT r.*, c.occurrence_id AS candidate_occurrence_id,
                          c.content_id AS candidate_content_id,
                          c.identity_status AS candidate_identity_status,
                          c.match_basis, c.selected AS candidate_selected
                   FROM metadata_import_record r
                   LEFT JOIN metadata_import_candidate c USING (import_record_id)
                   ORDER BY r.partition_id, r.line_number,
                            c.occurrence_id"""
            )
            while batch := cursor.fetchmany(5_000):
                for imported in batch:
                    row = {field: imported[field] if field in imported.keys() else "" for field in import_fields}
                    writer.writerow(row)
                    jsonl_handle.write(
                        json.dumps(row, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":")) + "\n"
                    )

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
        content_holds = self._current_content_holds()
        blocked_content_ids = set(content_holds)
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
        resolved_representatives = {
            row["content_id"]: row
            for row in self.connection.execute(
                """SELECT o.content_id, o.occurrence_id, o.bucket,
                          o.object_path, o.byte_size, o.md5_normalized,
                          b.captured_at, o.row_number,
                          (SELECT f.source_version
                           FROM strong_fingerprint_assertion f
                           WHERE f.occurrence_id = o.occurrence_id
                             AND f.sha256 = c.sha256
                           ORDER BY f.fingerprint_assertion_id LIMIT 1) AS source_version,
                          (SELECT f.source_etag
                           FROM strong_fingerprint_assertion f
                           WHERE f.occurrence_id = o.occurrence_id
                             AND f.sha256 = c.sha256
                           ORDER BY f.fingerprint_assertion_id LIMIT 1) AS source_etag
                   FROM current_content_metadata_resolution r
                   JOIN occurrence o
                     ON o.occurrence_id = r.primary_occurrence_id
                    AND o.content_id = r.content_id
                   JOIN content_identity c USING (content_id)
                   JOIN inventory_batch b USING (inventory_id)
                   WHERE c.identity_status = 'sha256_verified'
                     AND r.resolution_state != 'blocked_embedded_conflict'
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
                   ORDER BY o.content_id"""
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
            if identity["content_id"] in blocked_content_ids:
                continue
            representative = resolved_representatives.get(identity["content_id"])
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

        del resolved_representatives, inherited_content_ids
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
            if row["content_id"] in blocked_content_ids:
                reason = content_holds[str(row["content_id"])]
            elif drift:
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
                if row["content_id"] in blocked_content_ids:
                    algorithm = "sha256" if row["identity_status"] == "sha256_verified" else "unknown"
                    digest = row["sha256"] if algorithm == "sha256" else ""
                    payload_source_identity = self._source_identity(
                        row["bucket"], row["object_path"], row["byte_size"],
                        None, None, row["md5_normalized"],
                    )
                    destination_key = f"payloads/held/{payload_source_identity[:2]}/{payload_source_identity}"
                    mapping_status = content_holds[str(row["content_id"])]
                    assertion_basis = "direct" if direct_assertion else "inherited_md5_size_bridge"
                    dedupe_authority = "none_conflict"
                elif canonical is not None and not drift:
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
            "metadata_assertion", "metadata_import_partition",
            "metadata_import_record", "metadata_import_candidate",
            "content_metadata_resolution", "metadata_field_resolution",
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
