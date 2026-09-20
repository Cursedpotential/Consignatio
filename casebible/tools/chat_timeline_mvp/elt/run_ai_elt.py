# Byline: Claude Code · Opus 5 · 2026-09-18
"""Driver for the elt_ai_*_v1 DuckDB templates.

All extraction logic lives in the .sql templates; this driver only binds provenance
(from the catalog), points DuckDB at the file IN PLACE on the read-only B2 mount, and
records one attempt row per (template, object). Owner 2026-09-18 20:12 EDT: every format
goes through the DuckDB ELT process; on a format DuckDB cannot read we stop and report
that format rather than falling back to a parser.

ZIP members: the member is materialised to ONE fixed scratch path (reused, never
accumulated -- the host has ~22 GB free) and the template runs against that path.

Usage: run_ai_elt.py <worklist.tsv> <out.duckdb> <run_id>
worklist columns: vault_key sha1 catalog_path catalog_modtime_hint zip_member_path signature
"""
from __future__ import annotations

import csv
import os
import re
import shutil
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import duckdb

B2 = Path(os.environ.get("B2_ROOT", "/srv/openlist/b2/salem-data"))
ELT = Path(__file__).resolve().parent
SCRATCH = Path(os.environ.get("SCRATCH", "/root/aichat/scratch"))

TEMPLATE = {
    "chatgpt_conversations_json": "elt_ai_chatgpt_v1.sql",
    "claude_conversations_json":  "elt_ai_claude_v1.sql",
    "gemini_activity_json":       "elt_ai_gemini_activity_v1.sql",
    "ai_markdown_transcript":     "elt_ai_markdown_transcript_v1.sql",
    "ai_generic_json":            "elt_ai_generic_json_v1.sql",
    "ai_chat_memo_txt":           "elt_ai_chat_memo_txt_v1.sql",
    "ai_clipped_markdown":        "elt_ai_clipped_markdown_v1.sql",
}
UNSUPPORTED = {"chatgpt_chat_html", "gemini_activity_html"}  # stop-and-report, no fallback


def safe_err(e) -> str:
    """Engine errors quote the offending bytes, which can be the owner's private text.
    Keep the exception type and the structural reason; redact every quoted fragment."""
    m = re.sub(r'"[^"]*"', '"<redacted>"', str(e).replace("\n", " "))
    return f"{type(e).__name__}: {m[:180]}"


def setvars(con, **kw):
    for k, v in kw.items():
        con.execute(f"set variable {k} = ?", [("" if v is None else str(v))])


def main() -> int:
    work, out, run_id = sys.argv[1], sys.argv[2], sys.argv[3]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    member_tmp = SCRATCH / "zip_member_current"   # ONE reused path

    con = duckdb.connect(out)
    con.execute((ELT / "_envelope.sql").read_text())
    sql_cache = {k: (ELT / v).read_text() for k, v in TEMPLATE.items()}

    with open(work, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    done = {r[0] for r in con.execute(
        "select vault_key || '|' || coalesce(zip_member_path,'') from ai_elt_attempts where status='ok'"
    ).fetchall()}

    t0, n_ok, n_err, n_skip, n_rows = time.time(), 0, 0, 0, 0
    for i, r in enumerate(rows, 1):
        sig = r["signature"]
        key = r["vault_key"]
        member = (r.get("zip_member_path") or "").strip()
        ident = f"{key}|{member}"
        if ident in done:
            n_skip += 1
            continue
        if sig in UNSUPPORTED or sig not in TEMPLATE:
            con.execute("insert into ai_elt_attempts values (?,?,?,?,?,0,'unsupported',?,now())",
                        [run_id, sig or "none", key, member or None, r.get("sha1"),
                         "no DuckDB template for this signature -- reported, no parser fallback"])
            n_skip += 1
            continue

        src = B2 / key
        try:
            if member:
                if member_tmp.exists():
                    member_tmp.unlink()
                with zipfile.ZipFile(B2 / key) as z, z.open(member) as mf, member_tmp.open("wb") as fo:
                    shutil.copyfileobj(mf, fo, 1024 * 1024)
                src = member_tmp
            before = con.execute("select count(*) from ai_turns").fetchone()[0]
            setvars(con, src=str(src), vault_key=key, sha1=r.get("sha1"),
                    catalog_path=r.get("catalog_path"), zip_member_path=member,
                    modtime=r.get("catalog_modtime_hint"), run_id=run_id)
            con.execute(sql_cache[sig])
            after = con.execute("select count(*) from ai_turns").fetchone()[0]
            got = after - before
            n_rows += got
            n_ok += 1
            con.execute("insert into ai_elt_attempts values (?,?,?,?,?,?,'ok',NULL,now())",
                        [run_id, TEMPLATE[sig], key, member or None, r.get("sha1"), got])
        except Exception as e:
            n_err += 1
            con.execute("insert into ai_elt_attempts values (?,?,?,?,?,0,'error',?,now())",
                        [run_id, TEMPLATE.get(sig, "?"), key, member or None, r.get("sha1"),
                         safe_err(e)])
            print(f"ERROR {sig} {key[-70:]} {member[-60:]} :: {safe_err(e)}", flush=True)
        if i % 25 == 0:
            print(f"{i}/{len(rows)} ok={n_ok} err={n_err} skip={n_skip} turns={n_rows} "
                  f"{i/(time.time()-t0):.1f}/s", flush=True)
    con.execute("checkpoint")
    print(f"ELT DONE run={run_id} objects={len(rows)} ok={n_ok} error={n_err} skipped={n_skip} "
          f"turns={n_rows} secs={time.time()-t0:.0f} at={datetime.now(timezone.utc).isoformat()}", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
