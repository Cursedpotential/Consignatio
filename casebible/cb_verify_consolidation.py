#!/usr/bin/env python3
"""cb_verify_consolidation.py — prove that every table in agentos-db's `casebible` (:5432) landed
identically in casebible-pg18 (:5434). READ-ONLY on both sides except the optional ops.migration_log
append on the target (--log).

Byline: Claude Code · Fable 5 · 2026-08-27

Method (same as the 2026-08-25 migration): per table, compare COUNT(*) and md5(string_agg(row::text
ORDER BY row::text)) on both sides. Identical hash => identical content. Tables missing on the target,
count mismatches, and hash mismatches are LISTED, never ignored.

Usage (from the PC, Tailscale up):
  python cb_verify_consolidation.py            # report only
  python cb_verify_consolidation.py --log      # also append one row per verified table to target ops.migration_log

Credentials: source password = DB_PASS in ~/.secrets/Agno-MCP-Platform.env (user ai);
target password = the postgres:// URL in HANDOFF.md §2 (user postgres). Never printed.
"""
import re, sys, pathlib, hashlib, datetime
import psycopg

HANDOFF = pathlib.Path(r"E:\AI_Workspace\casebible\HANDOFF.md")
AGNO_ENV = pathlib.Path.home() / ".secrets" / "Agno-MCP-Platform.env"

def src_conn():
    env = AGNO_ENV.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"(?m)^\s*(?:export\s+)?DB_PASS\s*=\s*['\"]?([^'\"\r\n]+)", env)
    if not m: sys.exit("DB_PASS not found in Agno env")
    return psycopg.connect(host="100.91.190.107", port=5432, dbname="casebible", user="ai", password=m.group(1), connect_timeout=15)

def tgt_conn():
    h = HANDOFF.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"postgresql://postgres:([0-9a-f]+)@ovh-files\.tilapia-skilift\.ts\.net:5434/casebible", h)
    if not m: sys.exit("target DSN not found in HANDOFF.md §2")
    return psycopg.connect(host="ovh-files.tilapia-skilift.ts.net", port=5434, dbname="casebible", user="postgres", password=m.group(1), connect_timeout=15)

TABLES_SQL = """select n.nspname, c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where c.relkind='r' and n.nspname not in ('pg_catalog','information_schema','duckdb') order by 1,2"""

def fingerprint(cur, s, t):
    cur.execute(f'select count(*), md5(coalesce(string_agg(x::text, \'|\' order by x::text), \'\')) from "{s}"."{t}" x')
    return cur.fetchone()

def main():
    log = "--log" in sys.argv
    src, tgt = src_conn(), tgt_conn()
    sc, tc = src.cursor(), tgt.cursor()
    sc.execute(TABLES_SQL); tables = sc.fetchall()
    tc.execute(TABLES_SQL); tgt_tables = set(tc.fetchall())
    print(f"source tables: {len(tables)} | target tables (all schemas): {len(tgt_tables)}\n")
    ok, bad, missing = [], [], []
    print(f"{'table':44s} {'src_n':>9s} {'tgt_n':>9s}  hash   verdict")
    for s, t in tables:
        sn, sh = fingerprint(sc, s, t)
        if (s, t) not in tgt_tables:
            missing.append(f"{s}.{t}"); print(f"{s+'.'+t:44s} {sn:>9,} {'—':>9s}  —      MISSING ON TARGET"); continue
        tn, th = fingerprint(tc, s, t)
        same = (sn == tn and sh == th)
        (ok if same else bad).append(f"{s}.{t}")
        print(f"{s+'.'+t:44s} {sn:>9,} {tn:>9,}  {'match' if sh==th else 'DIFF ':5s}  {'ok' if same else 'MISMATCH'}")
    print(f"\nVERIFIED identical: {len(ok)}   MISMATCH: {len(bad)}   MISSING: {len(missing)}")
    if bad:     print("  mismatches:", ", ".join(bad))
    if missing: print("  missing:   ", ", ".join(missing))
    # target-only schemas that must still be there untouched
    tc.execute("select count(*) from catalog.od_manifest"); print(f"\ntarget catalog.od_manifest rows (must be unchanged, ~1,869,794): {tc.fetchone()[0]:,}")
    if log and ok and not bad and not missing:
        tc.execute("""create table if not exists ops.migration_log (id serial primary key, source_db text, source_table text,
                      target_table text, row_count bigint, verified_by text, migrated_at timestamptz default now(), note text)""")
        for full in ok:
            s, t = full.split(".", 1); sc.execute(f'select count(*) from "{s}"."{t}"'); n = sc.fetchone()[0]
            tc.execute("insert into ops.migration_log(source_db,source_table,target_table,row_count,verified_by,note) values (%s,%s,%s,%s,%s,%s)",
                       ("agentos-db:5432/casebible", full, full, n, "count+md5_row_hash", "consolidated into casebible-pg18 per owner 2026-08-27"))
        tgt.commit(); print(f"ops.migration_log: {len(ok)} rows appended on target")
    elif log:
        print("NOT logging: verification is not clean.")
    return 0 if not (bad or missing) else 1

if __name__ == "__main__":
    sys.exit(main())
