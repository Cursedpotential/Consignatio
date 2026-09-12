"""
cb_isolate.py - final correction pass on the tmp/ restoration
==============================================================
Owner directives 2026-08-23:
  * tmp/temp folders are NOT junk -> 92 real files restored
  * ISOLATE the exported browser passwords (do not ingest, do not index)
  * REMOVE the single non-case mp4
  * everything else is saved

Outputs (nothing deleted, nothing overwritten):
  junk_scrub_report_final.csv   corrected junk list, tmp pattern dropped
  tmp_restored_final.csv        the files being restored to the corpus
  ISOLATED_CREDENTIALS.csv      password exports - handle separately, NEVER ingest
  EXCLUDED.csv                  removed from corpus, with reason
  purge_commands.txt            rclone commands for Matt to run IF he wants
                                the excluded objects gone from R2 (not run here)
"""
import duckdb, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CB = "E:/AI_Workspace/casebible"
SRC = "read_csv('%s/junk_scrub_report.csv', ignore_errors=true, all_varchar=true)" % CB

# exact paths, matched on substring to survive any quoting differences
ISOLATE = ["Documents/tmp/Chrome Passwords.csv",
           "Documents/tmp/Chrome Passwords 3.csv"]
EXCLUDE = ["ph5f68a7bed856b"]          # non-case mp4

c = duckdb.connect()

def like_any(col, needles):
    return " or ".join("%s like '%%%s%%'" % (col, n.replace("'", "''")) for n in needles)

iso_pred = like_any("path", ISOLATE)
exc_pred = like_any("path", EXCLUDE)

# ---- 1. isolated credentials ------------------------------------------------
c.execute("""copy (select bucket, path, size, md5,
    'EXPORTED BROWSER CREDENTIALS - isolate, never ingest, never index, never embed'
    as handling from %s where %s) to '%s/ISOLATED_CREDENTIALS.csv' (header)"""
    % (SRC, iso_pred, CB))

# ---- 2. excluded ------------------------------------------------------------
c.execute("""copy (select bucket, path, size, md5,
    'non-case content - excluded from corpus by owner 2026-08-23' as reason
    from %s where %s) to '%s/EXCLUDED.csv' (header)""" % (SRC, exc_pred, CB))

# ---- 3. restored (tmp pattern, minus isolated + excluded) -------------------
c.execute("""copy (select bucket, path, size, md5, matched_pattern,
    'restored: tmp folder-name pattern invalid per owner 2026-08-23' as restore_reason
    from %s where lower(matched_pattern)='tmp' and not (%s) and not (%s))
    to '%s/tmp_restored_final.csv' (header)""" % (SRC, iso_pred, exc_pred, CB))

# ---- 4. final junk list: drop tmp-pattern rows, but KEEP iso + exc as junk --
c.execute("""copy (select * from %s
    where lower(matched_pattern) <> 'tmp' or (%s) or (%s))
    to '%s/junk_scrub_report_final.csv' (header)""" % (SRC, iso_pred, exc_pred, CB))

def n(f):
    return c.sql("select count(*) from read_csv('%s/%s', all_varchar=true)" % (CB, f)).fetchone()[0]

print("=== RESULTS ===")
print("  original junk_scrub_report.csv : %s rows (UNTOUCHED)"
      % format(c.sql("select count(*) from " + SRC).fetchone()[0], ","))
print("  junk_scrub_report_final.csv    : %s rows" % format(n("junk_scrub_report_final.csv"), ","))
print("  tmp_restored_final.csv         : %s files RESTORED" % format(n("tmp_restored_final.csv"), ","))
print("  ISOLATED_CREDENTIALS.csv       : %s files ISOLATED" % format(n("ISOLATED_CREDENTIALS.csv"), ","))
print("  EXCLUDED.csv                   : %s files EXCLUDED" % format(n("EXCLUDED.csv"), ","))

print()
print("=== ISOLATED (credentials) ===")
for r in c.sql("select bucket, path, size from read_csv('%s/ISOLATED_CREDENTIALS.csv', all_varchar=true)" % CB).fetchall():
    print("  %-24s %10s  %s" % (r[0], r[2], r[1]))

print()
print("=== EXCLUDED ===")
for r in c.sql("select bucket, path, size from read_csv('%s/EXCLUDED.csv', all_varchar=true)" % CB).fetchall():
    print("  %-24s %10s  %s" % (r[0], r[2], r[1]))

print()
print("=== RESTORED: total bytes ===")
gb = c.sql("""select coalesce(sum(try_cast(size as bigint)),0)/1e9
              from read_csv('%s/tmp_restored_final.csv', all_varchar=true)""" % CB).fetchone()[0]
print("  %s files, %.2f GB back in the corpus" % (format(n("tmp_restored_final.csv"), ","), gb))

# ---- 5. purge commands (NOT executed) --------------------------------------
lines = ["# Generated %s - NOT executed. Run only if you want these gone from R2." % __file__,
         "# Rule is quarantine-not-delete; these MOVE to .review_hold, they are not purged.",
         ""]
for tbl, dest in (("EXCLUDED.csv", "_excluded"), ("ISOLATED_CREDENTIALS.csv", "_isolated_credentials")):
    for r in c.sql("select bucket, path from read_csv('%s/%s', all_varchar=true)" % (CB, tbl)).fetchall():
        lines.append('rclone moveto "r2:%s/%s" "r2:casebible-quarantine/.review_hold/%s/%s"'
                     % (r[0], r[1], dest, r[1]))
open(CB.replace("/", "\\") + "\\purge_commands.txt", "w", encoding="utf-8").write("\n".join(lines))
print()
print("  purge_commands.txt written (%d moveto commands, NOT executed)" % (len(lines) - 3))
