"""Byline: Codex | 2026-09-20. Occurrence identity is never a content hash."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from collections import defaultdict


def digest(value, length):
    value = (value or "").lower()
    return value if re.fullmatch(r"[0-9a-f]{%d}" % length, value) else None


def stable_id(*parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def integer(value):
    return int(value) if value not in (None, "") else None


def source_sha1(record):
    info = record.get("fileInfo") or {}
    return digest(record.get("contentSha1"), 40) or digest(info.get("large_file_sha1"), 40)


class VersionIndex:
    def __init__(self, versions):
        self.by_id = {}
        self.by_key = defaultdict(list)
        self.by_hash = defaultdict(list)
        for row in versions:
            if row["file_id"] in self.by_id:
                raise ValueError("Duplicate provider version identity")
            self.by_id[row["file_id"]] = row
            self.by_key[row["key"]].append(row)
            if row["action"] == "upload" and digest(row.get("sha1"), 40):
                self.by_hash[(row["sha1"], integer(row["size"]))].append(row)

    def resolve(self, key, sha1, size):
        """Return all supported alternatives; never select a winner by path or size."""
        sha1 = digest(sha1, 40)
        size = integer(size)
        candidates = self.by_hash.get((sha1, size), []) if sha1 and size is not None else []
        if candidates:
            same = [r for r in candidates if r["key"] == key and r["visible"]]
            live = [r for r in candidates if r["visible"]]
            state = "visible_exact_path" if same else "visible_exact_elsewhere" if live else "historical_exact"
            return state, "b2_sha1_size", [r["file_id"] for r in candidates]
        if key and any(r["visible"] for r in self.by_key.get(key, [])):
            return ("identity_conflict" if sha1 else "path_only_unverified"), "none", []
        return ("unresolved_identity" if sha1 else "no_usable_identity"), "none", []


def occurrence(record, index):
    size = integer(record.get("size"))
    state, basis, ids = index.resolve(record.get("vault_key"), record.get("sha1"), size)
    metadata = record.get("metadata") or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    native = metadata.get("native") is True or metadata.get("native") == "true"
    flags = []
    if native and record.get("disposition") == "exported" and not record.get("vault_key"):
        flags.append("native_export_linkage_conflict")
    if record.get("source", "").startswith("local/") and set(metadata).issubset({"mime"}):
        flags.append("thin_local_metadata")
    if record.get("disposition") in ("junk_excluded", "zero_byte"):
        flags.append("legacy_exclusion_unreviewed")
    year = str(record.get("modtime") or "")[:4]
    if year.isdigit() and (int(year) <= 1970 or int(year) > datetime.now(timezone.utc).year):
        flags.append("source_date_requires_review")
    return {
        "occurrence_id": stable_id(record.get("source"), record.get("scope"), record.get("path"), record.get("source_id")),
        "source_rel": record.get("rel"), "source": record.get("source"),
        "state": state, "match_basis": basis, "version_ids": ids,
        "quality_flags": flags, "source_record": record,
        "bas_status": "not_assessed", "retirement_status": "not_cleared",
    }


def work_item(kind, identity, source, priority, reason, evidence, next_step):
    return {"item_id": stable_id(kind, identity), "kind": kind, "source": source,
            "priority": priority, "reason": reason, "evidence": evidence,
            "next_step": next_step, "status": "open", "retirement_status": "not_cleared"}
