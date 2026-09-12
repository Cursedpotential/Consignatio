"""
cb_unjunk_tmp.py - remove the 'tmp' folder-name pattern from junk classification
================================================================================
FINDING (2026-08-23): the junk classifier used a bare 'tmp' folder-name pattern.
It caught real corpus data living in _backup_import/Documents/tmp/, including
'K- Timeline 3.json' (16.8 MB, case material).

Owner directive: tmp/temp folders are NOT junk in this environment.

This script:
  1. Reports every row currently junk-flagged BECAUSE of the tmp pattern
  2. Writes a corrected junk_scrub_report_corrected.csv (tmp rows removed)
  3. Writes tmp_restored.csv - the rows being un-flagged, for the record

READ-ONLY on all sources. Writes only new files. Nothing is deleted.
"""
import duckdb, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CB   = "E:/AI_Workspace/casebible"
SCRUB = CB + "/junk_scrub_report.csv"
OUT_CORRECTED = CB + "/junk_scrub_report_corrected.csv"
OUT_RESTORED  = CB + "/tmp_restored.csv"

c = duckdb.connect()
SRC = "read_csv('%s', ignore_errors=true, all_varchar=true)" % SCRUB

print("=== rows flagged by matched_pattern='tmp' ===")
rows = c.sql("select bucket, path, size, md5 from %s "
             "where lower(matched_pattern)='tmp' order by "
             "try_cast(size as bigint) desc" % SRC).fetchall()
print("count: %d" % len(rows))
for r in rows:
    print("  %-10s %10s  %s" % (r[0][:10], r[2], r[1][:105]))

print()
print("=== which of those are REAL data (not .remember session files)? ===")
real = c.sql("""
    select bucket, path, size, md5 from %s
    where lower(matched_pattern)='tmp'
      and path not like '%%.remember/tmp/%%'
      and path not like '%%/functions/temp/%%'
    order by try_cast(size as bigint) desc""" % SRC).fetchall()
print("count: %d" % len(real))
for r in real:
    print("  %-10s %10s  %s" % (r[0][:10], r[2], r[1][:105]))

# corrected report: drop every row matched purely on the tmp pattern
c.execute("""
    copy (select * from %s where lower(matched_pattern) <> 'tmp')
    to '%s' (header, delimiter ',')""" % (SRC, OUT_CORRECTED))

c.execute("""
    copy (select *, 'unjunked: tmp folder-name pattern is invalid per owner 2026-08-23'
                 as restore_reason
          from %s where lower(matched_pattern) = 'tmp')
    to '%s' (header, delimiter ',')""" % (SRC, OUT_RESTORED))

before = c.sql("select count(*) from %s" % SRC).fetchone()[0]
after  = c.sql("select count(*) from read_csv('%s', all_varchar=true)"
               % OUT_CORRECTED).fetchone()[0]
print()
print("junk_scrub_report.csv           : %s rows (unchanged, original preserved)" % format(before, ","))
print("junk_scrub_report_corrected.csv : %s rows" % format(after, ","))
print("tmp_restored.csv                : %s rows un-flagged" % format(before - after, ","))

# --- now the duckdb junk4 / dec4 side -------------------------------------
print()
print("=== casebible.duckdb: junk-classified rows under a tmp/temp FOLDER ===")
d = duckdb.connect(CB + "/casebible.duckdb", read_only=True)
q = """select junk_class, bucket, size, path from junk4
       where junk_class <> 'CONTENT'
         and (path like '%/tmp/%' or path like '%/temp/%'
              or path like '%/Tmp/%' or path like '%/Temp/%')
       order by size desc"""
jr = d.sql(q).fetchall()
print("count: %d" % len(jr))
for r in jr[:40]:
    print("  %-18s %-22s %10s  %s" % (r[0][:18], r[1][:22], r[2], str(r[3])[:88]))
d.close()

print()
print("NOTE: casebible.duckdb is NOT modified. The corrected classification is")
print("applied when inventory.item.sort_state is built (cb_collapse.py), using")
print("junk_scrub_report_corrected.csv as the junk source instead of the original.")
