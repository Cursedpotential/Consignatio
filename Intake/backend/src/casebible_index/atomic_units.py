from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import NAMESPACE_URL, uuid4, uuid5

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .config import Settings
from .inventory import newest_inventory
from .parquet_store import parquet_bytes, write_immutable
from .snapshots import newest_snapshot

RULES_VERSION = "atomic-boundary-v2-parquet"
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tgz", ".gz", ".7z", ".rar"}
FACEBOOK_MESSAGE_DIRS = {"inbox", "archived_threads", "filtered_threads"}
FACEBOOK_WRAPPER = re.compile(r"^(?:fb|facebook)(?:[ _-]+(?:data|exports?|backup).*)?$", re.I)
TAKEOUT_SEGMENT = re.compile(r"^(?:google[ _-]+)?takeout(?:[ _-].*)?$", re.I)


@dataclass
class Candidate:
    source_id: str
    root_path: str
    unit_type: str
    platform: str | None
    detection_basis: set[str] = field(default_factory=set)
    confidence: str = "review"
    handling_mode: str = "defer_dissection"
    marker_paths: set[str] = field(default_factory=set)
    parent_unit_id: str | None = None
    member_count: int = 0
    total_bytes: int = 0
    indexed_document_count: int = 0
    indexed_document_types: set[str] = field(default_factory=set)

    @property
    def unit_id(self) -> str:
        return str(
            uuid5(
                NAMESPACE_URL,
                f"casebible-atomic:{self.source_id}:{self.unit_type}:{self.root_path.casefold()}",
            )
        )


@dataclass(frozen=True)
class AtomicResult:
    run_dir: Path
    units_path: Path
    members_path: Path
    edges_path: Path
    candidate_count: int
    member_count: int


def _path_parts(path: str) -> tuple[str, ...]:
    return tuple(
        part for part in PurePosixPath(path.replace("\\", "/")).parts if part not in {"/", "."}
    )


def _prefix(parts: tuple[str, ...], length: int) -> str:
    return "/".join(parts[:length])


def _add_candidate(
    candidates: dict[tuple[str, str], Candidate],
    *,
    source_id: str,
    root_path: str,
    unit_type: str,
    platform: str | None,
    basis: str,
    confidence: str,
    handling_mode: str,
    marker_path: str,
) -> None:
    root_path = root_path.strip("/")
    if not root_path:
        return
    key = (root_path.casefold(), unit_type)
    candidate = candidates.get(key)
    if candidate is None:
        candidate = Candidate(
            source_id=source_id,
            root_path=root_path,
            unit_type=unit_type,
            platform=platform,
            confidence=confidence,
            handling_mode=handling_mode,
        )
        candidates[key] = candidate
    candidate.detection_basis.add(basis)
    candidate.marker_paths.add(marker_path)


def _detect_candidates(inventory_path: Path, source_id: str) -> dict[tuple[str, str], Candidate]:
    candidates: dict[tuple[str, str], Candidate] = {}
    directory_files: dict[str, set[str]] = defaultdict(set)
    parquet_file = pq.ParquetFile(inventory_path)

    for batch in parquet_file.iter_batches(columns=["relative_path", "filename", "extension"]):
        for row in batch.to_pylist():
            path = str(row["relative_path"])
            filename = str(row["filename"])
            extension = str(row["extension"] or "").casefold()
            parts = _path_parts(path)
            lowered = tuple(part.casefold() for part in parts)
            if not parts:
                continue
            parent = _prefix(parts, len(parts) - 1)
            directory_files[parent].add(filename.casefold())

            for index, segment in enumerate(lowered[:-1]):
                if segment == "your_facebook_activity":
                    root = _prefix(parts, index) if index > 0 else _prefix(parts, 1)
                    _add_candidate(
                        candidates,
                        source_id=source_id,
                        root_path=root,
                        unit_type="facebook_dyi",
                        platform="facebook",
                        basis="your_facebook_activity directory segment",
                        confidence="high",
                        handling_mode="preserve_whole",
                        marker_path=_prefix(parts, index + 1),
                    )
                if TAKEOUT_SEGMENT.fullmatch(parts[index]):
                    root = _prefix(parts, index + 1)
                    _add_candidate(
                        candidates,
                        source_id=source_id,
                        root_path=root,
                        unit_type="google_takeout",
                        platform="google",
                        basis="Takeout directory segment",
                        confidence="high",
                        handling_mode="preserve_whole",
                        marker_path=root,
                    )

            for index in range(max(0, len(lowered) - 1)):
                if (
                    lowered[index] == "messages"
                    and index + 1 < len(lowered)
                    and lowered[index + 1] in FACEBOOK_MESSAGE_DIRS
                    and "your_facebook_activity" not in lowered[:index]
                ):
                    root = _prefix(parts, index) or _prefix(parts, index + 1)
                    _add_candidate(
                        candidates,
                        source_id=source_id,
                        root_path=root,
                        unit_type="facebook_deconstruction",
                        platform="facebook",
                        basis="Facebook messages tree without standard wrapper",
                        confidence="review",
                        handling_mode="defer_dissection",
                        marker_path=_prefix(parts, index + 2),
                    )
                    break

            if extension in ARCHIVE_EXTENSIONS:
                _add_candidate(
                    candidates,
                    source_id=source_id,
                    root_path=path,
                    unit_type="archive_file",
                    platform=None,
                    basis="archive extension; extraction relationship unproven",
                    confidence="high",
                    handling_mode="archive_provenance",
                    marker_path=path,
                )

    for directory, names in directory_files.items():
        if "conversations.json" in names and names.intersection(
            {"chat.html", "user.json", "shared_conversations.json"}
        ):
            _add_candidate(
                candidates,
                source_id=source_id,
                root_path=directory,
                unit_type="chat_export",
                platform="chatgpt",
                basis="ChatGPT conversations plus companion export marker",
                confidence="high",
                handling_mode="preserve_whole",
                marker_path=f"{directory}/conversations.json",
            )
        if "archive_browser.html" in names:
            _add_candidate(
                candidates,
                source_id=source_id,
                root_path=directory,
                unit_type="chat_export",
                platform="chat",
                basis="archive_browser.html export marker",
                confidence="high",
                handling_mode="preserve_whole",
                marker_path=f"{directory}/archive_browser.html",
            )
        if "manifest.db" in names and "info.plist" in names:
            _add_candidate(
                candidates,
                source_id=source_id,
                root_path=directory,
                unit_type="ios_backup",
                platform="apple",
                basis="iOS backup Manifest.db plus Info.plist",
                confidence="high",
                handling_mode="preserve_whole",
                marker_path=f"{directory}/Manifest.db",
            )
        imessage_markers = names.intersection(
            {"chat.db", "messages.csv", "messages.json", "imessage.csv", "imessage.json"}
        )
        if imessage_markers:
            _add_candidate(
                candidates,
                source_id=source_id,
                root_path=directory,
                unit_type="chat_export",
                platform="imessage",
                basis="iMessage database or message export marker",
                confidence="medium" if "chat.db" in imessage_markers else "high",
                handling_mode="preserve_whole",
                marker_path=f"{directory}/{sorted(imessage_markers)[0]}",
            )

    # Preserve ambiguous collection wrappers that contain multiple nested export roots.
    nested_by_parent: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates.values():
        parent = str(PurePosixPath(candidate.root_path).parent)
        if parent not in {".", ""}:
            nested_by_parent[parent].append(candidate)
    for parent, children in nested_by_parent.items():
        parent_name = PurePosixPath(parent).name
        if len(children) > 1 or FACEBOOK_WRAPPER.fullmatch(parent_name):
            types = {child.unit_type for child in children}
            if types.intersection({"facebook_dyi", "google_takeout", "facebook_deconstruction"}):
                _add_candidate(
                    candidates,
                    source_id=source_id,
                    root_path=parent,
                    unit_type="opaque_nested_root",
                    platform=None,
                    basis="collection wrapper containing nested export candidates",
                    confidence="review",
                    handling_mode="defer_dissection",
                    marker_path=children[0].root_path,
                )
    return candidates


def _assign_parents(candidates: list[Candidate]) -> None:
    ordered = sorted(
        candidates, key=lambda item: (len(_path_parts(item.root_path)), item.root_path)
    )
    for child in ordered:
        child_parts = _path_parts(child.root_path)
        possible = [
            parent
            for parent in ordered
            if parent is not child
            and len(_path_parts(parent.root_path)) < len(child_parts)
            and child_parts[: len(_path_parts(parent.root_path))] == _path_parts(parent.root_path)
        ]
        if possible:
            child.parent_unit_id = max(
                possible, key=lambda item: len(_path_parts(item.root_path))
            ).unit_id


def _candidate_roots(candidates: list[Candidate]) -> dict[str, list[Candidate]]:
    result: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in candidates:
        result[candidate.root_path.casefold()].append(candidate)
    return result


def _deepest_candidates(path: str, roots: dict[str, list[Candidate]]) -> list[Candidate]:
    parts = _path_parts(path)
    for length in range(len(parts), 0, -1):
        matches = roots.get(_prefix(parts, length).casefold())
        if matches:
            return matches
    return []


def _attach_index_metadata(settings: Settings, candidates: list[Candidate]) -> None:
    snapshot = newest_snapshot(settings.output_dir)
    document_dir = settings.output_dir / "datasets" / "documents"
    if snapshot is None or not document_dir.exists():
        return
    roots = _candidate_roots(candidates)
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            """
            SELECT d.relative_path, d.document_type
            FROM read_parquet(?, union_by_name = true) d
            JOIN read_parquet(?) s USING (document_id, version_id, artifact_id)
            """,
            [str(document_dir / "*.parquet"), str(snapshot)],
        ).fetchall()
    finally:
        connection.close()
    for relative_path, document_type in rows:
        for candidate in _deepest_candidates(str(relative_path), roots):
            candidate.indexed_document_count += 1
            if document_type:
                candidate.indexed_document_types.add(str(document_type))


def detect_atomic_units(settings: Settings, inventory_path: Path | None = None) -> AtomicResult:
    inventory = inventory_path or newest_inventory(settings.output_dir)
    if inventory is None:
        raise FileNotFoundError("No inventory snapshot exists; run the inventory command first")
    candidate_map = _detect_candidates(inventory, settings.source_id)
    candidates = list(candidate_map.values())
    _assign_parents(candidates)
    _attach_index_metadata(settings, candidates)
    roots = _candidate_roots(candidates)
    candidates_by_id = {candidate.unit_id: candidate for candidate in candidates}

    def copy_independently(candidate: Candidate) -> bool:
        if candidate.parent_unit_id is None:
            return True
        parent = candidates_by_id[candidate.parent_unit_id]
        return parent.handling_mode not in {"preserve_whole", "archive_provenance"}

    captured_at = datetime.now(UTC)
    run_id = captured_at.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid4().hex[:8]
    run_dir = settings.output_dir / "atomic" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    members_path = run_dir / "members.parquet"
    member_schema = pa.schema(
        [
            ("unit_id", pa.string()),
            ("relative_path", pa.string()),
            ("filename", pa.string()),
            ("extension", pa.string()),
            ("byte_size", pa.int64()),
            ("is_marker", pa.bool_()),
            ("member_role", pa.string()),
            ("source_id", pa.string()),
            ("captured_at", pa.timestamp("us", tz="UTC")),
            ("rules_version", pa.string()),
        ]
    )
    writer = pq.ParquetWriter(members_path, member_schema, compression="zstd")
    member_rows: list[dict[str, object]] = []
    member_count = 0
    try:
        parquet_file = pq.ParquetFile(inventory)
        for batch in parquet_file.iter_batches(
            columns=["relative_path", "filename", "extension", "byte_size"]
        ):
            for row in batch.to_pylist():
                path = str(row["relative_path"])
                matches = _deepest_candidates(path, roots)
                for candidate in matches:
                    is_marker = path.casefold() in {
                        marker.casefold() for marker in candidate.marker_paths
                    }
                    member_rows.append(
                        {
                            "unit_id": candidate.unit_id,
                            "relative_path": path,
                            "filename": str(row["filename"]),
                            "extension": str(row["extension"] or ""),
                            "byte_size": int(row["byte_size"] or 0),
                            "is_marker": is_marker,
                            "member_role": "marker" if is_marker else "member",
                            "source_id": settings.source_id,
                            "captured_at": captured_at,
                            "rules_version": RULES_VERSION,
                        }
                    )
                    candidate.member_count += 1
                    candidate.total_bytes += int(row["byte_size"] or 0)
                    member_count += 1
                if len(member_rows) >= 50_000:
                    writer.write_table(pa.Table.from_pylist(member_rows, schema=member_schema))
                    member_rows.clear()
        if member_rows:
            writer.write_table(pa.Table.from_pylist(member_rows, schema=member_schema))
    finally:
        writer.close()

    units_schema = pa.schema(
        [
            ("unit_id", pa.string()),
            ("parent_unit_id", pa.string()),
            ("source_id", pa.string()),
            ("root_path", pa.string()),
            ("unit_type", pa.string()),
            ("platform", pa.string()),
            ("detection_basis", pa.list_(pa.string())),
            ("boundary_confidence", pa.string()),
            ("handling_mode", pa.string()),
            ("review_state", pa.string()),
            ("marker_count", pa.int32()),
            ("marker_paths", pa.list_(pa.string())),
            ("member_count", pa.int64()),
            ("total_bytes", pa.int64()),
            ("indexed_document_count", pa.int64()),
            ("indexed_document_types", pa.list_(pa.string())),
            ("copy_independently", pa.bool_()),
            ("attrs_json", pa.string()),
            ("captured_at", pa.timestamp("us", tz="UTC")),
            ("rules_version", pa.string()),
        ],
        metadata={
            b"casebible.authority": b"candidate boundaries only; never a disposition decision"
        },
    )
    unit_rows = [
        {
            "unit_id": candidate.unit_id,
            "parent_unit_id": candidate.parent_unit_id,
            "source_id": candidate.source_id,
            "root_path": candidate.root_path,
            "unit_type": candidate.unit_type,
            "platform": candidate.platform,
            "detection_basis": sorted(candidate.detection_basis),
            "boundary_confidence": candidate.confidence,
            "handling_mode": candidate.handling_mode,
            "review_state": "candidate",
            "marker_count": len(candidate.marker_paths),
            "marker_paths": sorted(candidate.marker_paths),
            "member_count": candidate.member_count,
            "total_bytes": candidate.total_bytes,
            "indexed_document_count": candidate.indexed_document_count,
            "indexed_document_types": sorted(candidate.indexed_document_types),
            "copy_independently": copy_independently(candidate),
            "attrs_json": json.dumps(
                {"inventory": inventory.name, "source_bytes_modified": False}, sort_keys=True
            ),
            "captured_at": captured_at,
            "rules_version": RULES_VERSION,
        }
        for candidate in sorted(candidates, key=lambda item: (item.root_path, item.unit_type))
    ]
    units_path = run_dir / "units.parquet"
    write_immutable(units_path, parquet_bytes(pa.Table.from_pylist(unit_rows, schema=units_schema)))

    edges_schema = pa.schema(
        [
            ("parent_unit_id", pa.string()),
            ("child_unit_id", pa.string()),
            ("relationship", pa.string()),
            ("child_copy_independently", pa.bool_()),
            ("captured_at", pa.timestamp("us", tz="UTC")),
            ("rules_version", pa.string()),
        ]
    )
    edge_rows = [
        {
            "parent_unit_id": candidate.parent_unit_id,
            "child_unit_id": candidate.unit_id,
            "relationship": "contains",
            "child_copy_independently": copy_independently(candidate),
            "captured_at": captured_at,
            "rules_version": RULES_VERSION,
        }
        for candidate in candidates
        if candidate.parent_unit_id is not None
    ]
    edges_path = run_dir / "edges.parquet"
    write_immutable(edges_path, parquet_bytes(pa.Table.from_pylist(edge_rows, schema=edges_schema)))
    return AtomicResult(
        run_dir=run_dir,
        units_path=units_path,
        members_path=members_path,
        edges_path=edges_path,
        candidate_count=len(candidates),
        member_count=member_count,
    )
