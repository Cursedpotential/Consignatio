#!/usr/bin/env python3
"""
forensic-detection-runner-selftest.py
Byline: Claude Code (PIPELINE lane) · Opus 4.8 · 2026-07-01

Offline, $0, no-DB self-test for evidence/detection.py. Exercises the pure scan
logic (literal + regex), the record_type->subject_type mapping, the finding-param
builder's court-safety defaults, and the SYMMETRIC-APPLICATION guarantee (the same
ruleset must hit both parties' messages identically). Run:

    python forensic-detection-runner-selftest.py

Exits 0 only if every assertion passes. Save stdout next to this file.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Put the Agno-MCP-Platform repo root on sys.path so `import evidence.detection` works.
REPO = Path(r"E:\AI_Workspace\Projects\the-platform-workspace\Agno-MCP-Platform")
sys.path.insert(0, str(REPO))

from evidence.detection import (  # noqa: E402
    Pattern,
    scan_record,
    subject_type_for,
    _finding_params,
    _INSERT_FINDING_SQL,
)

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    mark = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


# --- synthetic seeded-style ontology (stands in for analysis.detection_pattern) --
PATTERNS = [
    Pattern(id=None, pattern_set_id=None, category_id="coercive_control", subcategory="threat",
            match_type="literal", pattern="you'll never see", keywords=("if you leave",),
            severity=8, score=8, bias_caution=True, authored_perspective="single_party_complainant",
            source="seed:G2"),
    Pattern(id=None, pattern_set_id=None, category_id="hostile_language", subcategory=None,
            match_type="regex", pattern=r"\b(stupid|idiot|worthless)\b",
            severity=5, score=5, bias_caution=True, source="seed:G4"),
    Pattern(id=None, pattern_set_id=None, category_id="cooperation", subcategory=None,
            match_type="literal", pattern="thank you for", severity=2, score=2,
            bias_caution=True, source="seed:G5"),  # positive-polarity, still hypothesis
    Pattern(id=None, pattern_set_id=None, category_id="broken_pattern", subcategory=None,
            match_type="regex", pattern=r"(unclosed[", severity=5, source="seed:bad"),  # bad regex
]

# Two speakers — deliberately BOTH exhibit a hostile hit so we can prove symmetry.
RECORDS = [
    {"id": "rec-A1", "record_type": "message",
     "content": "You'll never see the kids again if you leave. You are worthless."},
    {"id": "rec-B1", "record_type": "sms",
     "content": "That is a stupid thing to say. Thank you for nothing."},
    {"id": "rec-A2", "record_type": "call_log", "content": "missed call, 3 min"},
    {"id": "rec-C1", "record_type": "ocr", "content": None},  # empty content -> no scan
]


def main() -> int:
    print("=== evidence/detection.py — offline self-test (no DB, $0) ===\n")

    print("1) record_type -> subject_type mapping (pattern_finding CHECK set):")
    check("message->message", subject_type_for("message") == "message")
    check("sms->message", subject_type_for("sms") == "message")
    check("call_log->event", subject_type_for("call_log") == "event")
    check("ocr->ocr_text", subject_type_for("ocr") == "ocr_text")
    check("unknown->message(default)", subject_type_for("weird") == "message")

    print("\n2) scan finds literal + regex hits, skips broken regex cleanly:")
    m_a1 = scan_record(RECORDS[0]["content"], PATTERNS)
    cats_a1 = sorted({m.pattern.category_id for m in m_a1})
    check("rec-A1 hits coercive_control", "coercive_control" in cats_a1)
    check("rec-A1 hits hostile_language (worthless)", "hostile_language" in cats_a1)
    check("broken regex produced no crash / no hit", "broken_pattern" not in cats_a1)
    for m in m_a1:
        snippet = m.matched_text
        substr_ok = snippet.lower() in RECORDS[0]["content"].lower()
        check(f"span exact for '{snippet}'",
              RECORDS[0]["content"][m.start_char:m.end_char] == snippet and substr_ok,
              f"[{m.start_char}:{m.end_char}] method={m.detection_method}")

    print("\n3) SYMMETRIC APPLICATION — same ruleset hits BOTH parties:")
    m_b1 = scan_record(RECORDS[1]["content"], PATTERNS)
    cats_b1 = sorted({m.pattern.category_id for m in m_b1})
    check("party-A flagged hostile_language", "hostile_language" in cats_a1)
    check("party-B flagged hostile_language (stupid)", "hostile_language" in cats_b1)
    check("party-B also gets positive cooperation hit", "cooperation" in cats_b1,
          "positive-polarity categories score too, not just negatives")

    print("\n4) empty content is skipped, no findings:")
    check("None content -> 0 matches", scan_record(RECORDS[3]["content"], PATTERNS) == [])

    print("\n5) finding params carry the court-safety defaults (write-time guarantees):")
    p = _finding_params(RECORDS[0], m_a1[0], provenance_id="run-xyz")
    check("bias_caution carried true", p["bias_caution"] is True)
    check("author_party left NULL (defer to entity-res)", p["author_party"] is None)
    check("subject_id = record id", p["subject_id"] == "rec-A1")
    check("subject_type valid", p["subject_type"] in {"message", "ocr_text", "transcript", "event"})
    check("pattern_id + category carried", p["category_id"] == m_a1[0].pattern.category_id)

    print("\n6) INSERT SQL bakes the non-negotiable defaults + idempotency guard:")
    sql = _INSERT_FINDING_SQL
    check("review_status forced 'unreviewed'", "CAST('unreviewed' AS review_state)" in sql)
    check("safe_for_legal_use forced false", "false,\n       CAST('inferred'" in sql)
    check("requires_human_review forced true", "true, false, CAST('unreviewed'" in sql)
    check("data_tier forced 'inferred'", "CAST('inferred' AS evidence_tier)" in sql)
    check("enum casts present (detection_method/conduct_party)",
          "CAST(:detection_method AS detection_method)" in sql
          and "CAST(:author_party AS conduct_party)" in sql)
    check("idempotency NOT EXISTS guard present",
          "WHERE NOT EXISTS" in sql and "coalesce(f.matched_text, '')" in sql)

    # total findings tally across the corpus (excluding empty)
    total = sum(len(scan_record(r["content"], PATTERNS)) for r in RECORDS)
    print(f"\nCorpus totals: {total} findings across {len(RECORDS)} synthetic records "
          f"({sum(1 for r in RECORDS if r['content'])} with content).")

    print(f"\n=== RESULT: {PASS} passed, {FAIL} failed ===")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
