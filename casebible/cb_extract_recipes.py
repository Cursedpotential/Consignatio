#!/usr/bin/env python3
"""
cb_extract_recipes.py
Reusable text-extraction recipes for Case Bible "case-extract/v1" JSON jobs
(see E:\\AI_Workspace\\casebible\\_intake\\extracted-json-20260907\\_SCHEMA-case-extract-v1.md
and the sibling _RECIPES.md in that same directory for the full job convention).

These are the exact recipes used by extraction job X2 (2026-09-07, owner order
"extract everything ... save it for the Case Bible in JSON"). Kept here as a
standalone, dependency-free module (stdlib only) so any future extraction pass
(agent or human) can import or shell out to it instead of re-deriving the same
regexes.

DuckDB is NOT used for the extraction step itself — DuckDB has no docx/rtf
reader. It IS the right tool to query/QA the resulting JSON tree afterward
(see the read_json_auto() example at the bottom of this file, and _RECIPES.md).

Byline: Claude Code · Sonnet 5 (agent X2) · 2026-09-07
"""
from __future__ import annotations

import hashlib
import html
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Hashing / envelope helpers
# ---------------------------------------------------------------------------

def sha256_and_bytes(path: str | Path) -> tuple[str, int]:
    """Return (sha256_hex, byte_count) for a file, streamed (safe for large files)."""
    p = Path(path)
    h = hashlib.sha256()
    total = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


def are_files_byte_identical(path_a: str | Path, path_b: str | Path) -> bool:
    """Cheap exact-duplicate check (e.g. the C1 " - Copy" / " - Copy - Copy" csv variants)."""
    a, _ = sha256_and_bytes(path_a)
    b, _ = sha256_and_bytes(path_b)
    return a == b


# ---------------------------------------------------------------------------
# .docx -> text (keeps paragraph breaks)
# ---------------------------------------------------------------------------

def docx_text(path: str | Path) -> str:
    """
    Extract visible text from a .docx by reading word/document.xml directly
    (no python-docx dependency). Converts each </w:p> (paragraph end) to a
    newline BEFORE stripping tags, so paragraph structure survives; then
    strips all remaining XML tags and unescapes entities.

    This is the recipe mandated for every docx source in the X2 job.
    """
    import zipfile

    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = xml.replace("</w:p>", "\n")
    # Word sometimes uses <w:br/> for manual line breaks too — keep those as newlines.
    xml = xml.replace("<w:br/>", "\n").replace("<w:tab/>", "\t")
    text = re.sub(r"<[^>]+>", "", xml)
    return html.unescape(text)


def docx_rendered_text_equal(path_a: str | Path, path_b: str | Path) -> bool:
    """
    True if two .docx files render to identical visible text, even if the
    raw zip bytes differ (Word/export tools embed timestamps in the zip that
    make sha256 differ for text-identical documents — this is the check that
    caught the E1 "(1)" duplicate in the X2 job).
    """
    return docx_text(path_a) == docx_text(path_b)


# ---------------------------------------------------------------------------
# .rtf -> text (crude control-word stripping, stdlib only)
# ---------------------------------------------------------------------------

def rtf_text(path: str | Path) -> str:
    """
    Strip RTF control words/groups down to plain text. This is intentionally
    crude (regex-based, no full RTF parser) per the job's "by stripping
    control words" instruction. Good enough for extraction/QA reading, NOT
    a faithful re-render of formatting. Mark confidence "medium" (or lower)
    for any record whose source was read this way.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()

    # Drop \uNNNN unicode escapes' trailing placeholder char pattern first is
    # unnecessary for plain extraction; just strip control words and groups.
    text = re.sub(r"\\'[0-9a-fA-F]{2}", " ", data)          # \'xx hex-escaped chars
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", " ", text)          # \controlword(param)
    text = re.sub(r"[{}]", "", text)                          # group braces
    text = re.sub(r"\\\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# .csv / .md / .txt -> text (read directly, no transformation)
# ---------------------------------------------------------------------------

def read_plain(path: str | Path, errors: str = "replace") -> str:
    with open(path, "r", encoding="utf-8", errors=errors) as f:
        return f.read()


# ---------------------------------------------------------------------------
# case-extract/v1 envelope builder
# ---------------------------------------------------------------------------

def make_envelope(
    *,
    row: str,
    path: str,
    kind: str,
    extracted_at: str,
    records: list,
    authored_by: str = "unknown",
    source_date: str | None = None,
    confidence: str = "high",
    extractor: str = "Claude Code · Sonnet 5 (agent X2)",
) -> dict:
    """Build one case-extract/v1 JSON document (see _SCHEMA-case-extract-v1.md)."""
    sha, nbytes = sha256_and_bytes(path)
    return {
        "schema": "case-extract/v1",
        "source": {
            "row": row,
            "path": Path(path).as_posix(),
            "sha256": sha,
            "bytes": nbytes,
            "kind": kind,
            "authored_by": authored_by,
            "source_date": source_date,
        },
        "extracted_at": extracted_at,
        "extractor": extractor,
        "confidence": confidence,
        "records": records,
    }


# ---------------------------------------------------------------------------
# CLI: ad-hoc preview of any single file's extracted text
# ---------------------------------------------------------------------------

def _main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in ("docx", "rtf", "plain", "hash"):
        print("usage: python cb_extract_recipes.py {docx|rtf|plain|hash} <path>", file=sys.stderr)
        return 2
    mode, path = sys.argv[1], sys.argv[2]
    if mode == "docx":
        print(docx_text(path))
    elif mode == "rtf":
        print(rtf_text(path))
    elif mode == "plain":
        print(read_plain(path))
    elif mode == "hash":
        sha, n = sha256_and_bytes(path)
        print(f"{sha}  {n} bytes  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


# ---------------------------------------------------------------------------
# DuckDB QA/query recipe (for AFTER extraction — not for parsing itself)
# ---------------------------------------------------------------------------
#
# Once a row's JSON files exist, load them all for cross-file QA with DuckDB's
# read_json_auto (handles the nested "records" array + varying record shapes
# via union_by_name):
#
#   duckdb -c "
#     SELECT source.row, source.path, extracted_at, confidence,
#            len(records) AS n_records
#     FROM read_json_auto(
#       'E:/AI_Workspace/casebible/_intake/extracted-json-20260907/*/*.json',
#       union_by_name = true
#     )
#     ORDER BY source.row, source.path;
#   "
#
# To flatten every record across every row/file into one table (for counting
# by type, spot-checking dates, etc.):
#
#   duckdb -c "
#     SELECT source.row, source.path, r.type, r.id
#     FROM read_json_auto(
#       'E:/AI_Workspace/casebible/_intake/extracted-json-20260907/*/*.json',
#       union_by_name = true
#     ), UNNEST(records) AS t(r)
#     ORDER BY source.row, r.type;
#   "
#
# See also the `duckdb-skills:read-file` / `duckdb-skills:query` skills, and
# the `case-bible:cb-catalog` skill which uses casebible.duckdb for the
# broader corpus catalog (separate from this per-job extraction QA).
