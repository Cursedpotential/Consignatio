#!/usr/bin/env bash
# cb_dedup_namesize.sh — FAST name+size dedup across all local sources (no hashing).
# Step 1 of the dedup: cluster by (name, size); one good copy per cluster (reject zero-byte).
# Strips obvious dups (same file on multiple rescue-pass drives with same name+size).
# Output: per-source + total scope. The remainder (name+size-unique, not in raw) goes to the md5 pass.
set -o pipefail
DB="${CBCAT_DB:-E:/AI_Workspace/casebible/casebible.duckdb}"
DUCKDB="$(command -v duckdb)"
TMP="$(mktemp -d)"
winp() { cygpath -m "$1" 2>/dev/null || echo "$1"; }
gb() { awk "BEGIN{printf \"%.2f\", (${1:-0})/1e9}"; }
classa() { awk "BEGIN{printf \"%.2f\", (${1:-0})/1000000*4.5}"; }

echo "=== DEDUP STEP 1: name+size across all local sources (no hashing) ==="
echo "Cluster by (name,size); one good copy per cluster (zero-byte rejected). Match vs casebible-raw."
date -u +"start %H:%M:%SZ"

# source_label|spec|prefix
SOURCES="
D:\\Backup|D:/Backup|_backup_import/
F:\\Disk Drill|F:/Disk Drill|_diskdrill/
D:\\google|D:/google|_google/
D:\\fb|D:/fb|_fb/
D:\\context - Copy|D:/context - Copy|_d_context_copy/
D:\\snap|D:/snap|_snap/
E:\\backup|E:/backup|_e_backup/
J:\\Disk Drill|J:/Disk Drill|_j_diskdrill/
J:\\docs|J:/docs|_j_docs/
J:\\Evidence|J:/Evidence|_j_evidence/
J:\\00_Documentation|J:/00_Documentation|_j_doc_00/
J:\\03_Evidence_Analysis|J:/03_Evidence_Analysis|_j_evi_03/
J:\\Case Bible BACKUP 2026-03-12|J:/Case Bible BACKUP 2026-03-12|_j_cb_backup_2026-03-12/
J:\\Legal_Knowledge_Base_Obsidian|J:/Legal_Knowledge_Base_Obsidian|_j_lkb/
"

# Build one combined TSV: source_tag \t size \t path
COMB="$TMP/local_all.tsv"
: > "$COMB"
while IFS='|' read -r label spec prefix; do
  [ -z "$label" ] && continue
  tag="${prefix%/}"
  rclone ls "$spec" 2>/dev/null | awk -v t="$tag" '{s=$1; $1=""; sub(/^ +/,"",$0); print t"\t"s"\t"$0}' >> "$COMB"
done <<< "$SOURCES"
echo "combined listing: $(wc -l < "$COMB") rows"
comb="$(winp "$COMB")"

"$DUCKDB" "$DB" -noheader -list -c "
CREATE OR REPLACE TABLE local_files(source VARCHAR, size BIGINT, path VARCHAR);
COPY local_files FROM '$comb' (DELIM '\t', IGNORE_ERRORS);
ALTER TABLE local_files ADD COLUMN name VARCHAR;
UPDATE local_files SET name = regexp_extract(path, '([^/]+)\$', 1);

-- Per-source raw counts
SELECT '=== per-source ===' ;
SELECT source, count(*) AS files, round(sum(size)/1e9,2) AS GB, count(*) FILTER(WHERE size=0) AS zeroB
FROM local_files GROUP BY source ORDER BY files DESC;

-- Name+size dedup: one good copy per (name,size) cluster, zero-byte excluded from copy set
CREATE OR REPLACE TABLE ns_unique AS
SELECT source, name, size, path,
       row_number() OVER (PARTITION BY name, size ORDER BY
         CASE WHEN size=0 THEN 2 ELSE 0 END,  -- zero-byte ranks last
         length(path) ASC) AS rn
FROM local_files;
CREATE OR REPLACE TABLE ns_canonical AS
SELECT source, name, size, path FROM ns_unique WHERE rn=1;

SELECT '=== name+size dedup ===' ;
SELECT count(*) AS total_local,
       count(DISTINCT (name||'|'||size)) AS unique_name_size,
       count(*) - count(DISTINCT (name||'|'||size)) AS dups_suppressed,
       count(*) FILTER(WHERE size=0) AS zero_byte_total
FROM local_files;

-- Match canonical vs casebible-raw (name+size) — already in raw = don't copy
CREATE OR REPLACE TABLE to_copy AS
SELECT c.* FROM ns_canonical c
WHERE c.size > 0
  AND NOT EXISTS (SELECT 1 FROM r2_files r WHERE r.bucket='casebible-raw' AND r.name=c.name AND r.size=c.size);

SELECT '=== copy scope (name+size-unique, non-zero, not already in raw) ===' ;
SELECT count(*) AS files_to_copy,
       round(sum(size)/1e9,2) AS GB_to_copy,
       round(count(*)/1000000.0*4.5,2) AS classA_dollars
FROM to_copy;

-- Per-source copy breakdown
SELECT '=== per-source copy breakdown ===' ;
SELECT source, count(*) AS to_copy, round(sum(size)/1e9,2) AS GB
FROM to_copy GROUP BY source ORDER BY to_copy DESC;

-- What's already in raw (suppressed by raw match)
SELECT '=== already in raw (name+size match) — not copied ===' ;
SELECT count(*) AS already_in_raw
FROM ns_canonical c
WHERE c.size > 0
  AND EXISTS (SELECT 1 FROM r2_files r WHERE r.bucket='casebible-raw' AND r.name=c.name AND r.size=c.size);
" 2>&1
date -u +"dedup_step1_end %H:%M:%SZ"
echo
echo "NEXT: md5 pass — hash the to_copy set on-disk, cluster by md5 (catch renamed dups), match vs raw md5/ETag."
echo "The to_copy count above is an UPPER BOUND; md5 pass reduces it further."