#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest-order-constraint-verify.py
> Byline: Claude Code (PROCESS lane) - Opus 4.8 - 2026-07-01

PURPOSE (PROCESS-lane, reversible/local/$0, NO prod DB write):
  The 2026-07-01 05:50 owner-session verified ingest-readiness vs the LIVE ovh3 PG and
  found ONE writer change is now required by migration 0005:

      ALTER TABLE evidence.evidence_hash
        ADD CONSTRAINT evidence_hash_subject_ck CHECK (
          level = 'H3' OR source_id IS NOT NULL OR file_node_id IS NOT NULL) NOT VALID;

  => H1 (file) and H2 (per-message) custody hashes MUST now carry source_id (or file_node_id).
     Only H3 (the hash-linked chain rows) are exempt.
  => the OLD provisional "bare hash" path (digest only, no source linkage) is now INVALID.

  Correct ingest ORDER (owner, LOG 05:50):
     evidence.source  -> evidence.evidence_hash -> analysis.normalized_record

This harness PROVES, offline and deterministically, that:
  (A) the OLD bare-hash writer FAILS evidence_hash_subject_ck for its H1/H2 rows;
  (B) the CORRECTED source-first writer PASSES the constraint for every hash row;
  (C) the FK linkage normalized_record.artifact_id -> evidence.evidence_hash(id) resolves;
  (D) evidence.source required NOT NULL / CHECK columns are satisfiable from a parser record.

It is a *constraint oracle* for PIPELINE's writer update (TASKS 2026-07-01 -> PIPELINE).
It does NOT connect to any database. Real column facts are transcribed from
Agno-MCP-Platform/docs/planning/forensic-db-reconciliation/migrations/0005_forensic_reconciliation.sql
(evidence.source L249-299, evidence.evidence_hash ALTER L366-380, normalized_record note L929-943).
"""

import hashlib
import uuid
import json
import sys

# ---------------------------------------------------------------------------
# Schema facts transcribed from migration 0005 (authoritative).
# ---------------------------------------------------------------------------
SOURCE_TYPE_ALLOWED = {
    'device_dump', 'chat_export', 'screenshot', 'call_log', 'pdf',
    'media', 'takeout', 'social_export', 'document', 'other',
}
HASH_LEVELS = {'H1', 'H2', 'H3'}


def evidence_hash_subject_ck(row: dict) -> bool:
    """The EXACT predicate of constraint evidence_hash_subject_ck (0005 L378-379)."""
    return (row.get('level') == 'H3'
            or row.get('source_id') is not None
            or row.get('file_node_id') is not None)


def source_sha256_len_ck(source: dict) -> bool:
    """CONSTRAINT source_sha256_len CHECK (octet_length(sha256) = 32)  (0005 L297)."""
    return isinstance(source.get('sha256'), (bytes, bytearray)) and len(source['sha256']) == 32


def source_required_not_null(source: dict) -> list:
    """NOT NULL columns on evidence.source with no default (0005 L251-261)."""
    missing = []
    for col in ('sha256', 'byte_size', 'source_type', 'acquisition_source'):
        if source.get(col) in (None, ''):
            missing.append(col)
    if source.get('source_type') not in SOURCE_TYPE_ALLOWED:
        missing.append("source_type(not in CHECK set)")
    return missing


# ---------------------------------------------------------------------------
# A tiny, deterministic, real-SHA-256 parsed sample (stdlib only).
# Shape mirrors the PROVEN offline iMessage dry-run (per-message normalized_record,
# speakers UNBLENDED, per-message timestamps). Small on purpose - the constraint
# logic is size-invariant; the 1918 / 41,987 / 7,187 real runs are already proven.
# ---------------------------------------------------------------------------
RAW_FILE_BYTES = (
    b'<div class="bubble from-me"><div class="meta">Me - 2019-02-01 09:00 AM</div>hi</div>'
    b'<div class="bubble from-them"><div class="meta">+18108532989 - 2019-02-01 09:01 AM</div>hello</div>'
    b'<div class="bubble from-me"><div class="meta">Me - 2019-02-01 09:02 AM</div>ok</div>'
)
PARSED_MESSAGES = [
    {'ordinal': 0, 'speaker': 'Me',            'occurred_at_raw': '2019-02-01 09:00 AM', 'content': 'hi'},
    {'ordinal': 1, 'speaker': '+18108532989',  'occurred_at_raw': '2019-02-01 09:01 AM', 'content': 'hello'},
    {'ordinal': 2, 'speaker': 'Me',            'occurred_at_raw': '2019-02-01 09:02 AM', 'content': 'ok'},
]


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def build_old_bare_hash_plan():
    """OLD provisional writer: hashes with NO source row, NO source_id (bare digests)."""
    file_digest = sha256(RAW_FILE_BYTES)
    rows = [{'id': uuid.uuid4(), 'level': 'H1', 'digest': file_digest,
             'source_id': None, 'file_node_id': None}]
    prev = None
    for m in PARSED_MESSAGES:
        d = sha256(json.dumps(m, sort_keys=True).encode())
        rows.append({'id': uuid.uuid4(), 'level': 'H2', 'digest': d,
                     'source_id': None, 'file_node_id': None})
        chain = sha256((prev or b'') + d)
        rows.append({'id': uuid.uuid4(), 'level': 'H3', 'digest': chain,
                     'source_id': None, 'file_node_id': None})
        prev = chain
    return None, rows


def build_corrected_source_first_plan():
    """CORRECTED writer: source FIRST -> H1/H2 carry source_id -> H3 chain -> normalized_record."""
    file_digest = sha256(RAW_FILE_BYTES)
    source = {
        'id': uuid.uuid4(),
        'sha256': file_digest,
        'byte_size': len(RAW_FILE_BYTES),
        'source_type': 'chat_export',
        'acquisition_source': 'imessage-exporter (owner-custom HTML) - casebible-raw',
        'source_platform': 'imessage',
        'original_filename': 'index.html',
        'r2_bucket': 'casebible-raw',
        'provenance_tier': 'r2_canonical',
    }
    hashes = []
    # H1 = whole-file hash, carries source_id (satisfies ck via source_id)
    h1 = {'id': uuid.uuid4(), 'level': 'H1', 'digest': file_digest,
          'source_ref': source['id'], 'source_id': source['id'], 'file_node_id': None,
          'canon_version': 'h1-rawbytes-v1'}
    hashes.append(h1)
    # H2 = per-message hashes, carry source_id; record_locator pins the message unit
    per_msg_h2 = []
    prev = None
    h3_rows = []
    for m in PARSED_MESSAGES:
        d = sha256(json.dumps(m, sort_keys=True).encode())
        h2 = {'id': uuid.uuid4(), 'level': 'H2', 'digest': d,
              'source_ref': source['id'], 'source_id': source['id'], 'file_node_id': None,
              'record_locator': {'ordinal': m['ordinal']}}
        hashes.append(h2)
        per_msg_h2.append(h2)
        # H3 = hash-linked chain entry (exempt from ck via level='H3')
        chain = sha256((prev or b'') + d)
        h3 = {'id': uuid.uuid4(), 'level': 'H3', 'digest': chain,
              'source_ref': source['id'], 'source_id': None, 'file_node_id': None,
              'record_locator': {'ordinal': m['ordinal'], 'previous_hash': (prev or b'').hex() or None}}
        hashes.append(h3)
        h3_rows.append(h3)
        prev = chain

    # normalized_record: artifact_id -> evidence.evidence_hash(id). Use the H1 row id
    # as the artifact anchor; per-message provenance carried via attrs + occurred_at.
    norm_records = []
    for m, h2 in zip(PARSED_MESSAGES, per_msg_h2):
        norm_records.append({
            'id': uuid.uuid4(),
            'artifact_id': h1['id'],          # FK -> evidence.evidence_hash(id)
            'record_type': 'message',
            'source': 'imessage',
            'conversation_id': '+18108532989',   # TEXT external thread key (as-built)
            'role': 'me' if m['speaker'] == 'Me' else 'other',
            'content': m['content'],
            'occurred_at_raw': m['occurred_at_raw'],
            'attrs': {'speaker': m['speaker'], 'per_message_hash_id': str(h2['id'])},
            'data_tier': 'extracted',
            'review_status': 'unreviewed',
            'safe_for_legal_use': False,
        })
    return source, hashes, norm_records, {h['id'] for h in hashes}


def main():
    out = []
    def p(*a):
        line = ' '.join(str(x) for x in a)
        out.append(line)
        print(line)

    p("=" * 78)
    p("INGEST-ORDER CONSTRAINT VERIFICATION  (PROCESS lane, offline, $0, no prod write)")
    p("constraint under test: evidence_hash_subject_ck ="
      " (level='H3' OR source_id NOT NULL OR file_node_id NOT NULL)")
    p("=" * 78)

    # (A) OLD bare-hash path must FAIL for H1/H2.
    p("\n--- (A) OLD provisional bare-hash writer (no source row / no source_id) ---")
    _, old_rows = build_old_bare_hash_plan()
    old_fail = [r for r in old_rows if not evidence_hash_subject_ck(r)]
    for r in old_rows:
        ok = evidence_hash_subject_ck(r)
        p(f"  {r['level']}  source_id={r['source_id']}  ck_pass={ok}")
    p(f"  => rows VIOLATING ck: {len(old_fail)} "
      f"(expected: all H1+H2 = {sum(1 for r in old_rows if r['level'] in ('H1','H2'))})")
    assert len(old_fail) == sum(1 for r in old_rows if r['level'] in ('H1', 'H2')), \
        "OLD path should violate ck for every H1/H2 row"
    p("  RESULT: OLD bare-hash path correctly REJECTED by the live constraint. [PROVEN]")

    # (B/C/D) CORRECTED source-first path.
    p("\n--- (B) CORRECTED source-first writer (evidence.source -> hashes -> normalized_record) ---")
    source, hashes, norm_records, hash_ids = build_corrected_source_first_plan()

    # (D) evidence.source required cols + sha256 length.
    missing = source_required_not_null(source)
    len_ok = source_sha256_len_ck(source)
    p(f"  evidence.source required-NOT-NULL missing: {missing or 'NONE'}")
    p(f"  evidence.source source_sha256_len(=32) ok: {len_ok}")
    assert not missing and len_ok, "source row must satisfy NOT NULL + sha256 length"

    # (B) every hash row passes ck.
    bad = [h for h in hashes if not evidence_hash_subject_ck(h)]
    by_level = {}
    for h in hashes:
        by_level.setdefault(h['level'], 0)
        by_level[h['level']] += 1
    p(f"  hash rows by level: {by_level}")
    for h in hashes:
        p(f"    {h['level']}  source_id={'set' if h['source_id'] else None}  ck_pass={evidence_hash_subject_ck(h)}")
    p(f"  => hash rows VIOLATING ck: {len(bad)} (expected 0)")
    assert not bad, "corrected path must pass ck for every hash row"

    # (C) FK linkage normalized_record.artifact_id -> evidence_hash(id).
    fk_bad = [n for n in norm_records if n['artifact_id'] not in hash_ids]
    p(f"  normalized_record rows: {len(norm_records)}; artifact_id FK unresolved: {len(fk_bad)} (expected 0)")
    assert not fk_bad, "every normalized_record.artifact_id must reference an inserted evidence_hash id"

    # speakers unblended sanity (carry-over from proven parse contract).
    roles = {}
    for n in norm_records:
        roles[n['attrs']['speaker']] = roles.get(n['attrs']['speaker'], 0) + 1
    p(f"  speaker distribution (unblended): {roles}")
    assert len(roles) >= 2, "speakers must remain distinct/unblended"

    p("\n" + "=" * 78)
    p("VERDICT: corrected insert ORDER  source -> evidence_hash(H1/H2 w/ source_id; H3 exempt)"
      " -> normalized_record  SATISFIES evidence_hash_subject_ck and the source NOT NULL/len"
      " checks and the artifact_id FK. OLD bare-hash path is correctly rejected.")
    p("This is the acceptance oracle for PIPELINE's writer update (TASKS 2026-07-01).")
    p("NO database was contacted; all assertions passed.  [ALL GREEN]")
    p("=" * 78)

    with open(__file__.replace('.py', '-OUTPUT.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
