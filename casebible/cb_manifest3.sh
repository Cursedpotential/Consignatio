#!/usr/bin/env bash
# cb_manifest3.sh — fixed Phase 1+2 manifest. DuckDB COPY with bare IGNORE_ERRORS,
# awk formatting (no python3), parallel R2 listings (cut Phase 1 to ~12 min).
# Zero-download: rclone ls (LIST) for R2; metadata-only for local FS; od: API for OneDrive (no hydration).
set -uo pipefail
DB="${CBCAT_DB:-E:/AI_Workspace/casebible/casebible.duckdb}"
DUCKDB="$(command -v duckdb)"
TMP="$(mktemp -d)"
trap 'rm -f "$TMP"/*.tsv 2>/dev/null; true' EXIT
winp() { cygpath -m "$1" 2>/dev/null || echo "$1"; }
gb() { awk "BEGIN{printf \"%.2f\", ($1)/1e9}"; }
classa() { awk "BEGIN{printf \"%.2f\", ($1)/1000000*4.5}"; }

echo "=== PHASE 1: R2 ingest (parallel rclone ls -> TSV -> DuckDB COPY, zero-download) ==="
date -u +"start %H:%M:%SZ"
"$DUCKDB" "$DB" -c "CREATE OR REPLACE TABLE r2_files(bucket VARCHAR, path VARCHAR, name VARCHAR, ext VARCHAR, size BIGINT, md5 VARCHAR, modtime TIMESTAMP, mimetype VARCHAR, tier VARCHAR);"

# parallel listings (each rclone ls streams to its own TSV)
for b in casebible-raw casebible-quarantine casebible-sorted; do
  echo "  listing r2:$b ..."
  ( rclone ls "r2:$b" 2>/dev/null | awk '{s=$1; $1=""; sub(/^ +/,"",$0); print s"\t"$0}' > "$TMP/$b.tsv" ) &
done
wait
echo "  listings done, loading into DuckDB..."
date -u +"listings_done %H:%M:%SZ"

for b in casebible-raw casebible-quarantine casebible-sorted; do
  rows=$(wc -l < "$TMP/$b.tsv")
  tsv="$(winp "$TMP/$b.tsv")"
  "$DUCKDB" "$DB" -c "
    CREATE OR REPLACE TABLE t(size BIGINT, path VARCHAR);
    COPY t FROM '$tsv' (DELIM '\t', IGNORE_ERRORS);
    INSERT INTO r2_files
      SELECT '$b', path,
             regexp_extract(path, '([^/]+)$', 1) AS name,
             lower(regexp_extract(path, '\.([^./]+)$', 1)) AS ext,
             size, NULL, NULL, NULL,
             split_part(path, '/', 1) AS tier
      FROM t;
    DROP TABLE t;"
  n=$("$DUCKDB" "$DB" -noheader -list -c "SELECT count(*) FROM r2_files WHERE bucket='$b'")
  echo "  $b: listed=$rows  loaded=$n"
done
date -u +"phase1_end %H:%M:%SZ"
echo "=== catalog stats: ==="
"$DUCKDB" "$DB" -c "SELECT bucket, count(*) AS files, round(sum(size)/1e9,2) AS GB, count(*) FILTER(WHERE size=0) AS zero_byte FROM r2_files GROUP BY bucket ORDER BY bucket;"

echo
echo "=== PHASE 2: per-source dedup-aware manifest (name+size match, zero-download) ==="
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
TF=0; TB=0; TN=0; TNB=0; TZB=0
while IFS='|' read -r label spec prefix transfer notes; do
  [ -z "$label" ] && continue
  rclone ls "$spec" 2>/dev/null | awk '{s=$1; $1=""; sub(/^ +/,"",$0); print s"\t"$0}' > "$TMP/cand.tsv"
  tsv="$(winp "$TMP/cand.tsv")"
  res=$("$DUCKDB" "$DB" -noheader -list -c "
    CREATE OR REPLACE TABLE cand(path VARCHAR, name VARCHAR, size BIGINT);
    COPY cand FROM '$tsv' (DELIM '\t', IGNORE_ERRORS);
    SELECT count(*)||'|'||coalesce(sum(size),0)||'|'||
           count(*) FILTER(WHERE NOT EXISTS(SELECT 1 FROM r2_files r WHERE r.name=cand.name AND r.size=cand.size))||'|'||
           coalesce(sum(size) FILTER(WHERE NOT EXISTS(SELECT 1 FROM r2_files r WHERE r.name=cand.name AND r.size=cand.size)),0)||'|'||
           count(*) FILTER(WHERE size=0)
    FROM cand;")
  IFS='|' read -r n bytes new_n new_b zb <<< "$res"
  TF=$((TF+n)); TB=$((TB+bytes)); TN=$((TN+new_n)); TNB=$((TNB+new_b)); TZB=$((TZB+zb))
  printf "%-46s %-26s %-30s %9d %10s %9d %9s %7d %9s\n" "${label:0:46}" "$prefix" "${transfer:0:30}" "$n" "$(gb $bytes)" "$new_n" "$(gb $new_b)" "$zb" "$(classa $new_n)"
  [ -n "$notes" ] && echo "    NOTE: $notes"
done <<< "$SOURCES"
printf '%.0s-' {1..160}; echo
printf "%-46s %-26s %-30s %9d %10s %9d %9s %7d %9s\n" "TOTAL (local sources)" "" "" "$TF" "$(gb $TB)" "$TN" "$(gb $TNB)" "$TZB" "$(classa $TN)"
echo
echo "Free-tier note: first 1M Class-A ops/month free; \$4.50/M thereafter. Totals assume no free tier remaining (conservative)."
echo "Zero-byte files (bad_zero_byte, Addendum 4): $TZB across sources — to be flagged/skipped at ingest, never canonical."
date -u +"phase2_end %H:%M:%SZ"