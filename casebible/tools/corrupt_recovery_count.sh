#!/usr/bin/env bash
# Byline: Claude Code · Fable 5.1 · 2026-09-14
# Stage the corrupt-occurrence inputs into the PG container and run corrupt_recovery_count.sql. Runs ON the VPS.
# Usage: corrupt_recovery_count.sh <zero_filled_hold_manifest.csv> <local_zero_rows.csv>
# Outputs: report on stdout; the missing list is copied back next to the inputs as corrupt_missing.csv.
set -euo pipefail
HOLD="${1:?hold manifest csv}"; LOCAL="${2:?local zero rows csv}"
PG=fgz1n7useplhk0t91uk7k1aw
SQL="$(dirname "$0")/corrupt_recovery_count.sql"
docker cp "$HOLD" "$PG:/tmp/zero_filled_hold_manifest.csv"
docker cp "$LOCAL" "$PG:/tmp/local_zero_rows.csv"
docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 < "$SQL" | grep -v -E '^(BEGIN|DROP TABLE|CREATE TABLE|CREATE INDEX|COPY [0-9]+|SELECT [0-9]+|COMMIT|NOTICE)'
docker cp "$PG:/tmp/corrupt_missing.csv" "$(dirname "$HOLD")/corrupt_missing.csv"
echo "missing list: $(dirname "$HOLD")/corrupt_missing.csv ($(($(wc -l < "$(dirname "$HOLD")/corrupt_missing.csv") - 1)) rows)"
