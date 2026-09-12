#!/usr/bin/env bash
# cb_manifest2.sh — fast Phase 1+2 manifest using DuckDB COPY (bulk) instead of Python executemany.
# Zero-download: rclone ls (LIST only) for R2; metadata-only for local FS; od: API for OneDrive (no hydration).
# Dedup signal: name+size (conservative estimator for GO/NO-GO). True content-hash dedup deferred to Phase 4.
set -uo pipefail
DB="${CBCAT_DB:-E:/AI_Workspace/casebible/casebible.duckdb}"
DUCKDB="$(command -v duckdb || echo '/c/Users/matts/AppData/Local/Microsoft/WinGet/Packages/DuckDB.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/duckdb.exe')"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

winp() { echo "$1" | sed -E 's#^/([a-zA-Z])/#\U\1:/#'; }

echo "=== PHASE 1: R2 fast-ingest (rclone ls -> TSV -> DuckDB COPY, zero-download) ==="
date -u +"start %H:%M:%SZ"
"$DUCKDB" "$DB" -c "CREATE OR REPLACE TABLE r2_files(bucket VARCHAR, path VARCHAR, name VARCHAR, ext VARCHAR, size BIGINT, md5 VARCHAR, modtime TIMESTAMP, mimetype VARCHAR, tier VARCHAR);"

for b in casebible-raw casebible-quarantine casebible-sorted; do
  echo "  listing r2:$b ..."
  rclone ls "r2:$b" 2>/dev/null | awk '{s=$1; $1=""; sub(/^ +/,"",$0); print s"\t"$0}' > "$TMP/$b.tsv"
  rows=$(wc -l < "$TMP/$b.tsv")
  tsv="$(winp "$TMP/$b.tsv")"
  "$DUCKDB" "$DB" -c "
    CREATE OR REPLACE TABLE t(size BIGINT, path VARCHAR);
    COPY t FROM '$tsv' (DELIM '\t', IGNORE_ERRORS=true);
    INSERT INTO r2_files
      SELECT '$b' AS bucket, path,
             regexp_extract(path, '([^/]+)$', 1) AS name,
             lower(regexp_extract(path, '\.([^./]+)$', 1)) AS ext,
             size, NULL, NULL, NULL,
             split_part(path, '/', 1) AS tier
      FROM t;
    DROP TABLE t;"
  n=$("$DUCKDB" "$DB" -noheader -list -c "SELECT count(*)||' files, '||round(sum(size)/1e9,2)||' GB, zero_byte='||count(*) FILTER(WHERE size=0) FROM r2_files WHERE bucket='$b';")
  echo "  $b: $n  (listed $rows)"
done
date -u +"phase1_end %H:%M:%SZ"
echo "=== catalog stats: ==="
"$DUCKDB" "$DB" -c "SELECT bucket, count(*) AS files, round(sum(size)/1e9,2) AS GB, count(*) FILTER(WHERE size=0) AS zero_byte FROM r2_files GROUP BY bucket ORDER BY bucket;"

echo
echo "=== PHASE 2: per-source dedup-aware manifest (name+size match) ==="
# label | spec | prefix | transfer | notes
SOURCES="
D:\\Backup|D:/Backup|_backup_import/|devbox rclone -> R2|largest; D: read-only source
C:\\Users\\matts\\OneDrive\\Case Bible|od:Case Bible|_onedrive/case_bible/|VPS-side rclone (bypass devbox)|BLOCKER: od: not on VPS yet; zero hydration via od: API
F:\\Disk Drill|F:/Disk Drill|_diskdrill/|devbox rclone -> R2|
D:\\google|D:/google|_google/|devbox rclone -> R2|
D:\\fb|D:/fb|_fb/|devbox rclone -> R2|
D:\\context - Copy|D:/context - Copy|_d_context_copy/|devbox rclone -> R2|
D:\\snap|D:/snap|_snap/|devbox rclone -> R2|
E:\\backup|E:/backup|_e_backup/|devbox rclone -> R2|byte-identical to J:\\Disk Drill (dup)
J:\\Disk Drill|J:/Disk Drill|_j_diskdrill/|devbox rclone -> R2|byte-identical to E:\\backup (dup)
J:\\docs|J:/docs|_j_docs/|devbox rclone -> R2|
J:\\Evidence|J:/Evidence|_j_evidence/|devbox rclone -> R2|
J:\\00_Documentation|J:/00_Documentation|_j_doc_00/|devbox rclone -> R2|
J:\\03_Evidence_Analysis|J:/03_Evidence_Analysis|_j_evi_03/|devbox rclone -> R2|
J:\\Case Bible BACKUP 2026-03-12|J:/Case Bible BACKUP 2026-03-12|_j_cb_backup_2026-03-12/|devbox rclone -> R2|
J:\\Legal_Knowledge_Base_Obsidian|J:/Legal_Knowledge_Base_Obsidian|_j_lkb/|devbox rclone -> R2|
"
printf "%-46s %-26s %-30s %9s %10s %9s %9s %7s %9s\n" "source" "prefix" "transfer" "files" "bytes_GB" "new" "new_GB" "zeroB" "classA_$"
printf '%.0s-' {1..160}; echo
TOTAL_FILES=0; TOTAL_BYTES=0; TOTAL_NEW=0; TOTAL_NEWB=0; TOTAL_ZB=0
while IFS='|' read -r label spec prefix transfer notes; do
  [ -z "$label" ] && continue
  rclone ls "$spec" 2>/dev/null | awk '{s=$1; $1=""; sub(/^ +/,"",$0); print s"\t"$0}' > "$TMP/cand.tsv"
  rows=$(wc -l < "$TMP/cand.tsv")
  tsv="$(winp "$TMP/cand.tsv")"
  res=$("$DUCKDB" "$DB" -noheader -list -c "
    CREATE OR REPLACE TABLE cand(path VARCHAR, name VARCHAR, size BIGINT);
    COPY cand FROM '$tsv' (DELIM '\t', IGNORE_ERRORS=true);
    SELECT count(*)||'|'||coalesce(sum(size),0)||'|'||
           count(*) FILTER(WHERE NOT EXISTS(SELECT 1 FROM r2_files r WHERE r.name=cand.name AND r.size=cand.size))||'|'||
           coalesce(sum(size) FILTER(WHERE NOT EXISTS(SELECT 1 FROM r2_files r WHERE r.name=cand.name AND r.size=cand.size)),0)||'|'||
           count(*) FILTER(WHERE size=0)
    FROM cand;")
  IFS='|' read -r n bytes new_n new_b zb <<< "$res"
  TOTAL_FILES=$((TOTAL_FILES+n)); TOTAL_BYTES=$((TOTAL_BYTES+bytes)); TOTAL_NEW=$((TOTAL_NEW+new_n)); TOTAL_NEWB=$((TOTAL_NEWB+new_b)); TOTAL_ZB=$((TOTAL_ZB+zb))
  classa=$(python3 -c "print(f'{($new_n/1e6)*4.5:.2f}')")
  printf "%-46s %-26s %-30s %9d %10.2f %9d %9.2f %7d %9s\n" "${label:0:46}" "$prefix" "${transfer:0:30}" "$n" "$(python3 -c "print(f'{$bytes/1e9:.2f}')")" "$new_n" "$(python3 -c "print(f'{$new_b/1e9:.2f}')")" "$zb" "$classa"
  [ -n "$notes" ] && echo "    NOTE: $notes"
done <<< "$SOURCES"
printf '%.0s-' {1..160}; echo
classa_tot=$(python3 -c "print(f'{($TOTAL_NEW/1e6)*4.5:.2f}')")
printf "%-46s %-26s %-30s %9d %10.2f %9d %9.2f %7d %9s\n" "TOTAL (local sources)" "" "" "$TOTAL_FILES" "$(python3 -c "print(f'{$TOTAL_BYTES/1e9:.2f}')")" "$TOTAL_NEW" "$(python3 -c "print(f'{$TOTAL_NEWB/1e9:.2f}')")" "$TOTAL_ZB" "$classa_tot"
echo
echo "Free-tier note: first 1M Class-A ops/month free; \$4.50/M thereafter. Totals assume no free tier remaining (conservative)."
echo "Zero-byte files (bad_zero_byte, Addendum 4): $TOTAL_ZB across sources — to be flagged/skipped at ingest, never canonical."
date -u +"phase2_end %H:%M:%SZ"