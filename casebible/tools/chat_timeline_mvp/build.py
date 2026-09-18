# Byline: Claude Code · Opus 5 · 2026-09-18
"""Build the tagged + deduplicated timeline from every extraction DuckDB file (read-only attach).

Writes WORK/timeline_build.duckdb (scratch) and Parquet copies to OUT (B2 mount).
Terms come from the untracked TERMS file; build_timeline.sql holds no names.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import duckdb

WORK = Path(os.environ.get("WORK", "/work"))
OUT = os.environ.get("OUT")  # e.g. /b2out/consignatio/timeline_mvp_20260918
SOURCES = [s for s in os.environ.get("SOURCES", "timeline.duckdb").split(",") if s]

terms = json.load(open(os.environ["TERMS"]))
build = WORK / "timeline_build.duckdb.tmp"
if build.exists():
    build.unlink()
con = duckdb.connect(str(build))
for k in ("katrina_strong", "katrina_strict", "katrina_possible", "catrina_c", "landlord_context", "nickname", "daughter_strong", "daughter_weak",
          "kinship", "custody", "housing"):
    con.execute(f"set variable {k} = ?", [terms[k]])
parts = []
for i, s in enumerate(SOURCES):
    con.execute(f"attach '{WORK / s}' as src{i} (read_only)")
    parts.append(f"select * from src{i}.events_raw")
con.execute("create or replace table events_all as " + " union all by name ".join(parts))
# A phone is hers only when some SMS/call row names her in contact_name.
con.execute("""create or replace table katrina_phones_confirmed as
               select distinct counterparty_phone as phone from events_all
               where counterparty_phone is not null and regexp_matches(lower(coalesce(contact_name, '')), getvariable('katrina_strict'))""")
con.execute(open(Path(__file__).with_name("build_timeline.sql"), encoding="utf-8").read())
for (s,) in con.execute("select 'raw=' || (select count(*) from events_all) || ' dedup=' || (select count(*) from events_dedup)").fetchall():
    print(s, flush=True)
if OUT:
    Path(OUT).mkdir(parents=True, exist_ok=True)
    for t in ("events_dedup", "event_provenance"):
        con.execute(f"copy {t} to '{OUT}/{t}.parquet' (format parquet, compression zstd)")
    print("parquet written", OUT, flush=True)
con.close()
final = WORK / "timeline_build.duckdb"
if final.exists():
    final.rename(WORK / "timeline_build.prev.duckdb")
build.rename(final)
print("BUILD DONE", flush=True)
sys.exit(0)
