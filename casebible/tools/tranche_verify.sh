#!/usr/bin/env bash
# Byline: Claude Code · Fable 5.1 · 2026-09-14
# Verify a graded R2->B2 tranche from a FRESH B2 listing, never from rclone's exit status. Runs ON the VPS.
# Usage: tranche_verify.sh <bucket>          e.g. casebible-raw
# PASS = every path in graded-<bucket>.list exists under source-buckets/<bucket>/ on B2 with the size
# recorded in raw_duck.r2_files. Writes <bucket>.verify-<stamp>.{present,missing,size-mismatch}.list + summary.
set -euo pipefail
BUCKET="${1:?usage: tranche_verify.sh <bucket>}"
RUN=/data/consignatio/migrations/r2-to-b2/graded-copy-20260913
LIST="$RUN/graded-$BUCKET.list"
PG=fgz1n7useplhk0t91uk7k1aw
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$RUN/$BUCKET.verify-$STAMP"
PREFIX="consignatio/intake/raw-dedupe/v1/source-buckets/$BUCKET/"
test -s "$LIST" || { echo "ABORT: list missing/empty: $LIST"; exit 2; }
set -a; . /data/consignatio/secrets/rclone-b2-intake.env; set +a
rclone lsf -R --files-only --fast-list --format ps --separator $'\t' "b2:salem-data/$PREFIX" > "$OUT.b2.tsv"
echo "fresh listing: $(wc -l < "$OUT.b2.tsv") objects under $PREFIX"
docker cp "$LIST" "$PG:/tmp/tv_list.txt"
docker cp "$OUT.b2.tsv" "$PG:/tmp/tv_b2.tsv"
docker exec -i "$PG" psql -U postgres -d casebible -At -v ON_ERROR_STOP=1 <<SQL > "$OUT.summary.txt"
create temp table tv_list (path text);
\\copy tv_list from '/tmp/tv_list.txt' with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')
create temp table tv_b2 (path text, size bigint);
\\copy tv_b2 from '/tmp/tv_b2.tsv' with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')
create temp table tv as
  select l.path, b.size as b2_size, r.size as r2_size
  from tv_list l left join tv_b2 b on b.path = l.path
  left join raw_duck.r2_files r on r.bucket = '$BUCKET' and r.path = l.path;
\\copy (select path from tv where b2_size is not null and (r2_size is null or r2_size = b2_size)) to '/tmp/tv_present.list' with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')
\\copy (select path from tv where b2_size is null) to '/tmp/tv_missing.list' with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')
\\copy (select path || E'\\t' || b2_size || E'\\t' || r2_size from tv where b2_size is not null and r2_size is not null and r2_size <> b2_size) to '/tmp/tv_mismatch.list' with (format csv, delimiter E'\\t', quote E'\\x01', escape E'\\x01')
select 'listed=' || count(*) || ' present=' || count(*) filter (where b2_size is not null and (r2_size is null or r2_size = b2_size))
       || ' missing=' || count(*) filter (where b2_size is null)
       || ' size_mismatch=' || count(*) filter (where b2_size is not null and r2_size is not null and r2_size <> b2_size) from tv;
SQL
for k in present missing mismatch; do docker cp "$PG:/tmp/tv_$k.list" "$OUT.$k.list"; done
S=$(cat "$OUT.summary.txt")
echo "$BUCKET $S"
if echo "$S" | grep -qE ' missing=0 size_mismatch=0$'; then echo "VERIFY PASS ($OUT.*)"; else echo "VERIFY FAIL — see $OUT.missing.list / $OUT.mismatch.list"; exit 1; fi
