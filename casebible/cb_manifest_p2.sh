#!/usr/bin/env bash
# cb_manifest_p2.sh — fixed Phase 2 only. Reuses already-loaded r2_files (Phase 1 done).
# Fixes vs manifest3: cand table is 2-col (size,path) matching the rclone ls TSV;
# name derived via regexp_extract in the query; gb()/classa() robust to empty args (no set -u).
# Dedup match is against casebible-raw bucket only (files already in raw = skip).
# OneDrive excluded here (handled separately — od: API listing is slow, metadata-only).
# rclone normalizes paths to forward slashes on all platforms, so regex is ([^/]+)$ (no backslash).
set -o pipefail
DB="${CBCAT_DB:-E:/AI_Workspace/casebible/casebible.duckdb}"
DUCKDB="$(command -v duckdb)"
TMP="$(mktemp -d)"
winp() { cygpath -m "$1" 2>/dev/null || echo "$1"; }
gb() { awk "BEGIN{printf \"%.2f\", (${1:-0})/1e9}"; }
classa() { awk "BEGIN{printf \"%.2f\", (${1:-0})/1000000*4.5}"; }

echo "=== PHASE 2 (fixed): per-source dedup-aware manifest ==="
echo "Match: name+size vs casebible-raw bucket only. Conservative (true content-hash dedup deferred to Phase 4)."
date -u +"start %H:%M:%SZ"

# Local/disk sources only (OneDrive handled separately — od: API listing slow).
SOURCES="
D:\\Backup|D:/Backup|_backup_import/|devbox rclone -> R2|largest; D: read-only source
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
printf "%-44s %-26s %-30s %10s %10s %10s %10s %8s %9s\n" "source" "prefix" "transfer" "files" "bytes_GB" "new" "new_GB" "zeroB" "classA_$"
printf '%.0s-' {1..160}; echo
TF=0; TB=0; TN=0; TNB=0; TZB=0
while IFS='|' read -r label spec prefix transfer notes; do
  [ -z "$label" ] && continue
  rclone ls "$spec" 2>/dev/null | awk '{s=$1; $1=""; sub(/^ +/,"",$0); print s"\t"$0}' > "$TMP/cand.tsv"
  tsv="$(winp "$TMP/cand.tsv")"
  res=$("$DUCKDB" "$DB" -noheader -list -c "
    CREATE OR REPLACE TABLE cand(size BIGINT, path VARCHAR);
    COPY cand FROM '$tsv' (DELIM '\t', IGNORE_ERRORS);
    SELECT count(*)||'|'||coalesce(sum(size),0)||'|'||
           count(*) FILTER(WHERE NOT EXISTS(SELECT 1 FROM r2_files r WHERE r.bucket='casebible-raw' AND r.name=regexp_extract(cand.path,'([^/]+)\$',1) AND r.size=cand.size))||'|'||
           coalesce(sum(size) FILTER(WHERE NOT EXISTS(SELECT 1 FROM r2_files r WHERE r.bucket='casebible-raw' AND r.name=regexp_extract(cand.path,'([^/]+)\$',1) AND r.size=cand.size)),0)||'|'||
           count(*) FILTER(WHERE size=0)
    FROM cand;" 2>&1)
  if [[ "$res" == *"|"* ]]; then
    IFS='|' read -r n bytes new_n new_b zb <<< "$res"
  else
    n=0; bytes=0; new_n=0; new_b=0; zb=0
    echo "    [ERROR] $res" | head -2
  fi
  TF=$((TF+n)); TB=$((TB+bytes)); TN=$((TN+new_n)); TNB=$((TNB+new_b)); TZB=$((TZB+zb))
  printf "%-44s %-26s %-30s %10d %10s %10d %10s %8d %9s\n" "${label:0:44}" "$prefix" "${transfer:0:30}" "$n" "$(gb $bytes)" "$new_n" "$(gb $new_b)" "$zb" "$(classa $new_n)"
  [ -n "$notes" ] && echo "    NOTE: $notes"
done <<< "$SOURCES"
printf '%.0s-' {1..160}; echo
printf "%-44s %-26s %-30s %10d %10s %10d %10s %8d %9s\n" "TOTAL (local sources)" "" "" "$TF" "$(gb $TB)" "$TN" "$(gb $TNB)" "$TZB" "$(classa $TN)"
echo
echo "Free-tier note: first 1M Class-A ops/month free; \$4.50/M thereafter. Totals assume no free tier remaining (conservative)."
echo "Class-A \$ = new-to-add count x \$4.50/M (PUT/COPY ops into R2 raw)."
echo "Zero-byte files (bad_zero_byte, Addendum 4): $TZB across local sources — flagged/skipped at ingest, never canonical."
echo "OneDrive NOT included here — od: API listing runs separately (metadata-only, zero-download); transfer = VPS-side (BLOCKER: od: not on VPS yet)."
date -u +"phase2_end %H:%M:%SZ"