#!/usr/bin/env python3
"""
cb_load_raw.py - STEP 1 of 3.  LOAD EVERYTHING. COLLAPSE NOTHING.
==================================================================
Loads every Case Bible table/file into ONE database, origin preserved
in the schema name. No merging, no dedup, no cleaning, no dropping.

  TARGET  casebible @ ovh-files.tilapia-skilift.ts.net:5434 (PG18)

GUARANTEES
  * Existing target tables are SKIPPED, never overwritten.
  * catalog.* is never touched (count verified before + after).
  * No DROP / DELETE / TRUNCATE anywhere in this file.
  * Every table row-count verified source vs destination.
  * One table failing does not abort the run.
  * --dry-run is the DEFAULT and does not create target schemas.
  * --go is required to write.

STEP 2 (cb_prove.py)   completed read-only on 2026-08-27.
STEP 3 (cb_collapse.py) remains owner-gated and may only use proven families.
"""
import os, sys, time, argparse
from datetime import datetime

# libpq resolves this through .pg_service.conf + pgpass.conf.  Do not embed
# database credentials in scripts; cb_agent is the governed :5434 role.
DSN = "service=casebible"
TARGET_LABEL = "service=casebible (:5434/casebible)"

CB  = "E:/AI_Workspace/casebible"
LOG = CB.replace("/", "\\") + "\\load_raw.log"

def log(m):
    line = "%s  %s" % (datetime.now().strftime("%H:%M:%S"), m)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

DB_SOURCES = [
    ("raw_duck",   "duckdb", CB + "/casebible.duckdb",        "44 tables, canonical"),
    ("raw_duck_d", "duckdb", "D:/casebible/casebible.duckdb", "fossil - preserved"),
    ("raw_misc",   "duckdb", CB + "/merge-plan.duckdb",       "merge_plan"),
    ("raw_misc",   "duckdb", CB + "/iterations_index.duckdb", "iteration_index, table_defs"),
    ("raw_sqlite", "sqlite", CB + "/casebible_work.sqlite",   "sort_map, copy_log"),
]

FILE_SETS = [
    ("recovery", CB + "/recovery_by_tree", (".csv",)),
    ("exports",  CB + "/exports",          (".csv", ".parquet")),
    ("backups",  CB + "/backups",          (".parquet",)),
    ("rootcsv",  CB,                       (".csv",)),
]

# Legacy pipe-delimited hash dumps from the 2026-06-23 local pass.
# ~900k rows of size|md5|relpath - the largest hash corpus outside R2.
# Own schema: distinct provenance line, feeds inventory.item directly.
# NOTE: od_case_bible.tsv is intentionally EXCLUDED - size + bare filename
# only, no path and no hash; superseded by od_manifest / r2_files.
LEGACY_HASH_FILES = [
    ("raw_sizehash", CB + "/raw_sizehash.txt", "size|md5|relpath"),
    ("raw_hashes",   CB + "/raw_hashes.txt",   "md5|relpath"),
]


def connect():
    import duckdb
    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute("INSTALL sqlite;   LOAD sqlite;")
    con.execute("ATTACH '%s' AS tgt (TYPE POSTGRES)" % DSN)
    return con

def ensure_schema(con, s, dry):
    if dry:
        return
    con.execute("CREATE SCHEMA IF NOT EXISTS tgt.%s" % s)

def target_tables(con, s):
    try:
        return {r[0] for r in con.sql(
            "select table_name from tgt.information_schema.tables "
            "where table_schema='%s'" % s).fetchall()}
    except Exception:
        return set()

def safe_name(fn):
    t = os.path.splitext(fn)[0].lower()
    for ch in " -.+()":
        t = t.replace(ch, "_")
    while "__" in t:
        t = t.replace("__", "_")
    return t.strip("_")[:60]

STATS = {"loaded": 0, "skipped": 0, "failed": 0, "rows": 0}

# ---------------------------------------------------------------------------
# AUTHORITY RULE - written into the DB so any agent introspecting it sees this
# before it reads anything. The loop that produced 8 databases and 59 tables
# was: uncertainty -> new scan -> new store -> more uncertainty. Consolidating
# LOCATION does not consolidate AUTHORITY. This is the rule that does.
# ---------------------------------------------------------------------------
SCHEMA_COMMENTS = {
 "raw_duck":   "WRITE-ONCE raw import from E:/AI_Workspace/casebible/casebible.duckdb. "
               "SUPERSEDED BY inventory.*. DO NOT READ for analysis. Read only by "
               "cb_collapse.py. Drop after inventory.* is reconciled and approved.",
 "raw_duck_d": "WRITE-ONCE raw import from D:/casebible/casebible.duckdb (KNOWN FOSSIL, "
               "2026-06-23, r2_files has only 2 cols / 590,560 rows). Preserved for "
               "provenance ONLY. SUPERSEDED BY inventory.*. DO NOT READ.",
 "raw_misc":   "WRITE-ONCE raw import (merge-plan, iterations_index). "
               "SUPERSEDED BY inventory.*. DO NOT READ for analysis.",
 "raw_sqlite": "WRITE-ONCE raw import from casebible_work.sqlite. "
               "SUPERSEDED BY inventory.*. DO NOT READ for analysis.",
 "recovery":   "WRITE-ONCE raw import of recovery_by_tree/*.csv (110,745 rows, 44,389 "
               "unique md5, ALL confirmed present in R2 - nothing lost). "
               "SUPERSEDED BY inventory.*.",
 "exports":    "WRITE-ONCE raw import of exports/*.csv|parquet. NOTE: guarded-sync-NEW "
               "was computed against the STALE D: fossil (277,417 md5 vs 337,067 actual) "
               "and UNDER-DETECTS duplicates. SUPERSEDED BY inventory.*.",
 "backups":    "WRITE-ONCE raw import of backups/*.parquet snapshots. SUPERSEDED BY inventory.*.",
 "rootcsv":    "WRITE-ONCE raw import of loose CSV/TSV at casebible root. SUPERSEDED BY inventory.*.",
 "gdrive":     "WRITE-ONCE raw import of rclone lsjson from matt.salemnet@gmail.com "
               "(125,719 files, sha256+md5+sha1 provider-supplied). SUPERSEDED BY inventory.*.",
 "legacy_hashes": "WRITE-ONCE raw import of raw_sizehash.txt / raw_hashes.txt "
               "(2026-06-23 local hash pass, MD5 only, ~900k rows size|md5|relpath). "
               "Largest hash corpus outside R2. MD5 joins r2_files and the R2 SHA-256 "
               "ledger's md5Hash column. SUPERSEDED BY inventory.*.",
 "analysis":   "LIVE consolidated decision and labeling schema. NOT a raw landing schema. "
               "Do not overwrite. PG16-origin enrichment and media tables are in media.*.",
}

def apply_schema_comments(con, dry):
    log("")
    log("  --- verifying AUTHORITY RULE on schemas ---")
    for s, c in SCHEMA_COMMENTS.items():
        if not schema_exists(con, s):
            continue
        try:
            sql = ("SELECT obj_description(oid, 'pg_namespace') "
                   "FROM pg_namespace WHERE nspname='%s'" % s.replace("'", "''"))
            row = con.sql("SELECT * FROM postgres_query('tgt', $$%s$$)" % sql).fetchone()
            got = row[0] if row else None
            if got == c:
                log("      = %s verified" % s)
            else:
                log("      ! %s authority comment missing or stale; schema owner must repair" % s)
                STATS["failed"] += 1
        except Exception as e:
            log("      ! %s comment verification failed: %s" % (s, str(e)[:100]))
            STATS["failed"] += 1

def schema_exists(con, s):
    try:
        return con.sql("select count(*) from tgt.information_schema.schemata "
                       "where schema_name='%s'" % s).fetchone()[0] > 0
    except Exception:
        return False

def load_table(con, schema, tbl, sql, dry, src_file="unknown"):
    """src_file is stamped onto every row so a superseded intermediate can
    never be mistaken for current data once it is inside the target DB."""
    exists = tbl in target_tables(con, schema)
    stamped = ("SELECT q.*, '%s' AS _src_file, now() AS _loaded_at FROM (%s) q"
               % (src_file.replace("'", "''"), sql))
    try:
        n = con.sql("SELECT count(*) FROM (%s) c" % sql).fetchone()[0]
    except Exception as e:
        log("      ! %-34s COUNT FAILED: %s" % (schema + "." + tbl, str(e)[:110]))
        STATS["failed"] += 1
        return
    if exists:
        try:
            got = con.sql('SELECT count(*) FROM tgt.%s."%s"' % (schema, tbl)).fetchone()[0]
        except Exception as e:
            log("      ! %-34s EXISTS BUT COUNT FAILED: %s"
                % (schema + "." + tbl, str(e)[:100]))
            STATS["failed"] += 1
            return
        if got != n:
            log("      ! %-34s EXISTS WITH ROW MISMATCH src=%s dst=%s"
                % (schema + "." + tbl, format(n, ","), format(got, ",")))
            STATS["failed"] += 1
        else:
            log("      = %-34s SKIP (exists, %s rows verified)"
                % (schema + "." + tbl, format(got, ",")))
            STATS["skipped"] += 1
        return
    if dry:
        log("      ~ %-34s WOULD LOAD %12s rows" % (schema + "." + tbl, format(n, ",")))
        STATS["rows"] += n
        return
    t0 = time.time()
    try:
        con.execute('CREATE TABLE tgt.%s."%s" AS %s' % (schema, tbl, stamped))
        got = con.sql('SELECT count(*) FROM tgt.%s."%s"' % (schema, tbl)).fetchone()[0]
    except Exception as e:
        log("      ! %-34s LOAD FAILED: %s" % (schema + "." + tbl, str(e)[:110]))
        STATS["failed"] += 1
        return
    flag = "OK" if got == n else "MISMATCH src=%d dst=%d" % (n, got)
    log("      + %-34s %12s rows  %5.1fs  %s"
        % (schema + "." + tbl, format(got, ","), time.time() - t0, flag))
    STATS["loaded"] += 1
    STATS["rows"] += got


def load_db_sources(con, dry, only):
    for schema, kind, path, note in DB_SOURCES:
        if only and schema != only:
            continue
        if not os.path.exists(path.replace("/", "\\")):
            log("  MISSING %s" % path)
            continue
        log("  --- %s <- %s  (%s)" % (schema, os.path.basename(path), note))
        ensure_schema(con, schema, dry)
        alias = "srctmp"
        try:
            con.execute("DETACH %s" % alias)
        except Exception:
            pass
        try:
            if kind == "duckdb":
                con.execute("ATTACH '%s' AS %s (READ_ONLY)" % (path, alias))
            else:
                con.execute("ATTACH '%s' AS %s (TYPE SQLITE, READ_ONLY)" % (path, alias))
            q = ("select table_name from duckdb_tables() "
                 "where database_name='%s' and schema_name='main' order by 1" % alias)
            for (t,) in con.sql(q).fetchall():
                if t.startswith("sqlite_"):
                    continue
                load_table(con, schema, t, 'SELECT * FROM %s."%s"' % (alias, t), dry,
                           src_file=os.path.basename(path) + ":" + t)
            con.execute("DETACH %s" % alias)
        except Exception as e:
            log("      ! attach failed: %s" % str(e)[:160])
            try:
                con.execute("DETACH %s" % alias)
            except Exception:
                pass


def load_file_sets(con, dry, only):
    for schema, folder, exts in FILE_SETS:
        if only and schema != only:
            continue
        win = folder.replace("/", "\\")
        if not os.path.isdir(win):
            log("  MISSING %s" % folder)
            continue
        names = [f for f in sorted(os.listdir(win))
                 if os.path.isfile(os.path.join(win, f))
                 and os.path.splitext(f)[1].lower() in exts]
        if not names:
            continue
        log("  --- %s <- %s  (%d files)" % (schema, os.path.basename(folder) or folder, len(names)))
        ensure_schema(con, schema, dry)
        stems = {}
        for fn in names:
            stem = safe_name(fn)
            stems[stem] = stems.get(stem, 0) + 1
        for fn in names:
            ext = os.path.splitext(fn)[1].lower()
            stem = safe_name(fn)
            # CSV and Parquet snapshots can share a stem. Preserve both rather
            # than silently skipping the second one as an existing table.
            tbl = stem if stems[stem] == 1 else "%s_%s" % (stem, ext.lstrip("."))
            src = "%s/%s" % (folder, fn)
            if ext == ".parquet":
                sql = "SELECT * FROM read_parquet('%s')" % src
            elif ext == ".tsv":
                sql = ("SELECT * FROM read_csv('%s', delim='\t', "
                       "header=false, all_varchar=true)" % src)
            else:
                sql = ("SELECT * FROM read_csv('%s', "
                       "sample_size=-1, all_varchar=true)" % src)
            load_table(con, schema, tbl, sql, dry, src_file=fn)


def load_gdrive(con, dry, only):
    if only and only != "gdrive":
        return
    p = CB + "/gdrive/gd_net_rw.json"
    if not os.path.exists(p.replace("/", "\\")):
        log("  MISSING %s" % p)
        return
    log("  --- gdrive <- gd_net_rw.json")
    ensure_schema(con, "gdrive", dry)
    sql = ("SELECT Path AS path, Name AS name, Size AS size, MimeType AS mime_type, "
           "ModTime AS mod_time, ID AS drive_id, "
           "Hashes.sha256 AS sha256, Hashes.md5 AS md5, Hashes.sha1 AS sha1, "
           "'matt.salemnet@gmail.com' AS account FROM read_json('%s')" % p)
    load_table(con, "gdrive", "gd_net_rw", sql, dry, src_file="gd_net_rw.json")


def verify_analysis(con, dry, only):
    """The five PG16 media tables were already consolidated and hash-verified on
    :5434. Verify their presence; never reconnect to the retiring PG16 source."""
    if only and only != "analysis":
        return
    required = {"enrichment", "faces", "faces_scanned", "photos", "screenshots"}
    present = target_tables(con, "media")
    missing = sorted(required - present)
    log("  --- media.* <- verified consolidation already on :5434")
    if missing:
        log("      ! BLOCKED: missing consolidated tables: %s" % ", ".join(missing))
        STATS["failed"] += len(missing)
    else:
        log("      = five PG16-origin media tables already present; no reload")


def load_legacy_hashes(con, dry, only):
    """raw_sizehash.txt = size|md5|relpath   raw_hashes.txt = md5|relpath
    No header, pipe-delimited, paths may themselves contain '|' so we cap the
    column count and let the remainder stay in the path column."""
    if only and only != "legacy_hashes":
        return
    present = [(t, p, f) for t, p, f in LEGACY_HASH_FILES
               if os.path.exists(p.replace("/", "\\"))]
    if not present:
        log("  MISSING legacy hash files")
        return
    log("  --- legacy_hashes <- 2026-06-23 local MD5 pass (%d files)" % len(present))
    ensure_schema(con, "legacy_hashes", dry)
    for tbl, path, fmt in present:
        # Read each physical line as one value, then split only the required
        # leading fields. Paths may contain '|'; ignore_errors previously lost
        # six such rows. Blank MD5 is valid for 58 large/unhashed files.
        lines = ("read_csv('%s', delim='\\x1f', header=false, "
                 "columns={'line':'VARCHAR'}, quote='', escape='', ignore_errors=false)" % path)
        if fmt.startswith("size"):
            sql = ("SELECT TRY_CAST(split_part(line, '|', 1) AS BIGINT) AS size, "
                   "split_part(line, '|', 2) AS md5, "
                   "substr(line, length(split_part(line, '|', 1)) + "
                   "length(split_part(line, '|', 2)) + 3) AS relpath "
                   "FROM %s" % lines)
        else:
            sql = ("SELECT split_part(line, '|', 1) AS md5, "
                   "substr(line, length(split_part(line, '|', 1)) + 2) AS relpath "
                   "FROM %s" % lines)
        load_table(con, "legacy_hashes", tbl, sql, dry,
                   src_file=os.path.basename(path))


def report(con):
    log("")
    log("=" * 68)
    log("CONSOLIDATED STATE")
    try:
        rows = con.sql("""
            select table_schema, count(*) as n
            from tgt.information_schema.tables
            where table_schema not in ('pg_catalog','information_schema')
            group by 1 order by 1""").fetchall()
        tot = 0
        for s, n in rows:
            log("  %-14s %3d tables" % (s, n))
            tot += n
        log("  %-14s %3d TOTAL" % ("", tot))
    except Exception as e:
        log("  report failed: %s" % str(e)[:150])
    log("")
    log("  loaded=%d  skipped=%d  failed=%d  rows=%s"
        % (STATS["loaded"], STATS["skipped"], STATS["failed"], format(STATS["rows"], ",")))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--only", help="raw_duck|raw_duck_d|raw_misc|raw_sqlite|recovery|exports|backups|rootcsv|legacy_hashes|gdrive|analysis")
    a = ap.parse_args()
    if not (a.dry_run or a.go):
        ap.print_help(); sys.exit(1)
    dry = not a.go

    log("=" * 68)
    log("cb_load_raw   target=%s   mode=%s"
        % (TARGET_LABEL, "DRY-RUN" if dry else "GO"))
    log("LOAD ONLY. Nothing is collapsed, merged, cleaned, or dropped here.")
    log("catalog.* untouched. Existing tables never overwritten.")
    log("")

    con = connect()

    before = con.sql("select count(*) from tgt.information_schema.tables "
                     "where table_schema='catalog'").fetchone()[0]
    before_rows = con.sql("select count(*) from tgt.catalog.od_manifest").fetchone()[0]
    log("catalog: %d tables, od_manifest=%s rows" % (before, format(before_rows, ",")))
    log("")

    load_db_sources(con, dry, a.only)
    load_file_sets(con, dry, a.only)
    load_legacy_hashes(con, dry, a.only)
    load_gdrive(con, dry, a.only)
    verify_analysis(con, dry, a.only)

    apply_schema_comments(con, dry)

    after = con.sql("select count(*) from tgt.information_schema.tables "
                    "where table_schema='catalog'").fetchone()[0]
    after_rows = con.sql("select count(*) from tgt.catalog.od_manifest").fetchone()[0]
    log("")
    if after == before and after_rows == before_rows:
        log("catalog VERIFY: %d tables, od_manifest=%s rows  UNCHANGED"
            % (after, format(after_rows, ",")))
    else:
        log("!! catalog CHANGED  tables %d->%d  od_manifest %s->%s  INVESTIGATE"
            % (before, after, format(before_rows, ","), format(after_rows, ",")))
        STATS["failed"] += 1

    report(con)
    con.close()
    log("")
    if STATS["failed"]:
        log("BLOCKED: %d failure(s); do not advance to Stage 3" % STATS["failed"])
    else:
        log("NEXT: review this receipt; Stage 3 remains owner-gated")
    log("DONE")
    if STATS["failed"]:
        sys.exit(2)
