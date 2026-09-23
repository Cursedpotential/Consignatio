#!/usr/bin/env bash
# Byline: Claude Code · Fable 5.1 · 2026-09-14
# Build raw_duck.b2_content from a fresh B2 listing + the graded carriers TSV. Runs ON the VPS.
# Usage: b2_content_catalog.sh <listing.tsv key\tsize\tsha1> [carriers.tsv]
# The listing comes from: rclone lsf -R --files-only --fast-list --format psh --hash SHA-1 --separator $'\t' b2:.../source-buckets/
# (sha1 column added 2026-09-14; a 2-column listing still loads, sha1 stays null)
set -euo pipefail
LISTING="${1:?listing tsv (rel_key<TAB>size)}"
CARRIERS="${2:-/data/consignatio/migrations/r2-to-b2/graded-copy-20260913/graded-carriers-all.tsv}"
SQL="$(dirname "$0")/b2_content_catalog.sql"
PG=fgz1n7useplhk0t91uk7k1aw
LISTED_AT="$(date -u -r "$LISTING" +%Y-%m-%dT%H:%M:%SZ)"
docker cp "$LISTING" "$PG:/tmp/b2_listing.tsv"
docker cp "$CARRIERS" "$PG:/tmp/graded_carriers.tsv"
docker cp "$SQL" "$PG:/tmp/b2_content_catalog.sql"
docker cp "$(dirname "$0")/source_occurrences.sql" "$PG:/tmp/source_occurrences.sql"
docker exec "$PG" psql -U postgres -d casebible -At -v ON_ERROR_STOP=1 -f /tmp/source_occurrences.sql >/dev/null
docker exec "$PG" psql -U postgres -d casebible -At -v ON_ERROR_STOP=1 \
  -v carriers=/tmp/graded_carriers.tsv -v listing=/tmp/b2_listing.tsv -v listed_at="$LISTED_AT" \
  -f /tmp/b2_content_catalog.sql
