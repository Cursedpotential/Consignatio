#!/usr/bin/env bash
# cb_consolidate_5432_to_5434.sh — copy the `casebible` database that lives on agentos-db (:5432,
# the platform cluster) INTO casebible-pg18 (:5434, container fgz1n7useplhk0t91uk7k1aw).
#
# Byline: Claude Code · Fable 5 · 2026-08-27
# Owner decision 2026-08-27 07:07: "bring everything into the Case-Bible-PG. Consolidate everything
# there. Verify that everything is there." agentos-db is going away, so this is a one-way copy.
#
# RULES (HANDOFF.md §0): Matt runs this, on ovh-files. Nothing is dropped from the source. Nothing
# in the target's existing `catalog` schema is touched. Every step is idempotent-safe or refuses.
#
# Usage (on ovh-files):
#   bash cb_consolidate_5432_to_5434.sh --dry-run   # discover containers, list what would move, write nothing
#   bash cb_consolidate_5432_to_5434.sh --go        # dump + restore; then run cb_verify_consolidation.py from the PC
#
# What moves: every schema in source `casebible` EXCEPT `duckdb` (that schema is owned by the pg_duckdb
# extension and already exists on the target — restoring it would collide with extension objects).
# `public` moves too because the enum/composite TYPES the reference/evidence tables depend on live there
# (mcl_factor, category_polarity, pattern_match_type, sensitivity_tier, citext-based columns).
set -euo pipefail
MODE="${1:---dry-run}"
TGT_CID="fgz1n7useplhk0t91uk7k1aw"          # casebible-pg18 (HANDOFF §2)
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK="/tmp/cb_consolidate_${STAMP}"
DUMP="casebible_from_agentos_${STAMP}.dump"

say(){ printf '%s %s\n' "[$(date -u +%H:%M:%S)]" "$*"; }

# --- 1. discover the SOURCE container: filter by IMAGE (HANDOFF trap 7: name filters silently no-op) ---
# The source is the PG18 container that serves 100.91.190.107:5432 (agentos-db) and has a `casebible` DB.
mapfile -t PG18S < <(docker ps --format '{{.ID}} {{.Image}} {{.Ports}}' | awk '$2 ~ /postgres:18|postgres.*18/ {print $1" "$3}')
SRC_CID=""
for line in "${PG18S[@]}"; do
  cid="${line%% *}"; ports="${line#* }"
  [ "$cid" = "$TGT_CID" ] && continue
  [ "${cid:0:12}" = "${TGT_CID:0:12}" ] && continue
  if echo "$ports" | grep -q ':5432->'; then
    if docker exec "$cid" psql -U ai -d postgres -Atc "select 1 from pg_database where datname='casebible'" 2>/dev/null | grep -q 1; then
      SRC_CID="$cid"; break
    fi
  fi
done
if [ -z "$SRC_CID" ]; then
  say "REFUSING: could not identify the agentos-db container (postgres:18 image, host port 5432, has db 'casebible')."
  say "Candidates were:"; printf '   %s\n' "${PG18S[@]}"; exit 2
fi
say "source  = $SRC_CID (agentos-db, db casebible)"
say "target  = $TGT_CID (casebible-pg18, db casebible)"

# --- 2. inventory both sides (read-only) ---
say "source schemas/tables:"
docker exec "$SRC_CID" psql -U ai -d casebible -Atc "
  select n.nspname||'.'||c.relname||' ~'||c.reltuples::bigint from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where c.relkind='r' and n.nspname not in ('pg_catalog','information_schema','duckdb') order by 1" | sed 's/^/   /'
say "target schemas already present:"
docker exec "$TGT_CID" psql -U postgres -d casebible -Atc "select schema_name from information_schema.schemata where schema_name not in ('pg_catalog','information_schema','pg_toast') order by 1" | tr '\n' ' '; echo
# Empty schemas are fine (cb_load_raw.py pre-creates landing schemas); refuse only if data already lives there.
COLLIDE=$(docker exec "$TGT_CID" psql -U postgres -d casebible -Atc "select string_agg(distinct table_schema, ',') from information_schema.tables where table_type='BASE TABLE' and table_schema in ('analysis','evidence','knowledge','llm_eval','media','ops','reference','working')")
if [ -n "$COLLIDE" ]; then
  say "REFUSING: target already has TABLES in schema(s): $COLLIDE — a previous run happened. Verify with cb_verify_consolidation.py instead of re-restoring."
  exit 3
fi
say "target extensions (types the restore needs):"
docker exec "$TGT_CID" psql -U postgres -d casebible -Atc "select extname||' '||extversion from pg_extension order by 1" | tr '\n' ' '; echo

if [ "$MODE" != "--go" ]; then say "DRY RUN complete — nothing written. Re-run with --go to dump+restore."; exit 0; fi

# --- 3. dump (custom format, no owner/privs, exclude the extension-owned duckdb schema) ---
mkdir -p "$WORK"
say "dumping source -> $WORK/$DUMP"
docker exec "$SRC_CID" pg_dump -U ai -d casebible -Fc --no-owner --no-privileges --exclude-schema=duckdb -f "/tmp/$DUMP"
docker cp "$SRC_CID:/tmp/$DUMP" "$WORK/$DUMP"
docker cp "$WORK/$DUMP" "$TGT_CID:/tmp/$DUMP"
say "dump size: $(du -h "$WORK/$DUMP" | cut -f1)"
# keep a copy off-box too (never lose the pre-restore artifact)
rclone copy "$WORK/$DUMP" r2:casebible-quarantine/_snapshots/ 2>/dev/null && say "snapshot copied to r2:casebible-quarantine/_snapshots/$DUMP" || say "WARN: rclone snapshot copy failed (continuing; local copy kept at $WORK)"

# --- 4. restore in three sections; extension-owned objects in `public` may already exist -> those errors are expected ---
# citext etc. are extensions: CREATE EXTENSION lines in the dump will say "already exists" — fine.
say "restore: pre-data (schemas, types, tables)"
docker exec "$TGT_CID" pg_restore -U postgres -d casebible --no-owner --no-privileges --section=pre-data "/tmp/$DUMP" 2>&1 | tee "$WORK/restore_predata.log" | grep -vE 'already exists|extension "(citext|vector|pg_trgm|pgcrypto|btree_gin|btree_gist|hstore|ltree|unaccent|fuzzystrmatch|pg_duckdb)"' || true
say "restore: data"
docker exec "$TGT_CID" pg_restore -U postgres -d casebible --no-owner --no-privileges --section=data "/tmp/$DUMP" 2>&1 | tee "$WORK/restore_data.log" || true
say "restore: post-data (indexes, constraints, triggers)"
docker exec "$TGT_CID" pg_restore -U postgres -d casebible --no-owner --no-privileges --section=post-data "/tmp/$DUMP" 2>&1 | tee "$WORK/restore_postdata.log" || true
ERRS=$(cat "$WORK"/restore_*.log | grep -c 'ERROR' || true)
say "restore finished; ERROR lines in logs: $ERRS  (logs in $WORK — 'already exists' on extensions is expected; anything else must be read)"

# --- 5. quick count comparison (the real verification is cb_verify_consolidation.py from the PC) ---
say "row counts, source vs target:"
docker exec "$SRC_CID" psql -U ai -d casebible -Atc "select n.nspname||'.'||c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' and n.nspname not in ('pg_catalog','information_schema','duckdb') order by 1" > "$WORK/tables.txt"
while read -r t; do
  s=$(docker exec "$SRC_CID" psql -U ai -d casebible -Atc "select count(*) from $t")
  d=$(docker exec "$TGT_CID" psql -U postgres -d casebible -Atc "select count(*) from $t" 2>/dev/null || echo MISSING)
  [ "$s" = "$d" ] && flag="ok" || flag="MISMATCH"
  printf '   %-45s %10s %10s  %s\n' "$t" "$s" "$d" "$flag"
done < "$WORK/tables.txt"
say "done. Source untouched. Now run from the PC:  python cb_verify_consolidation.py"
