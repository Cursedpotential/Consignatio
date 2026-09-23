#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-13
# Measure SHA-256 ledger coverage of the R2 catalog. Read-only: the flattened TSV goes to /tmp and the SQL rolls back.
# Runs from the desktop; uses tracked sha_ledger_flatten.py and sha_ledger_coverage.sql from this directory.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VPS="root@100.91.190.107"
KEY="$HOME/.ssh/ovh"
PARTITIONS="/data/consignatio/migrations/r2-to-b2/hash-ledger-partitions"
DB_CONTAINER="fgz1n7useplhk0t91uk7k1aw"

MSYS_NO_PATHCONV=1 scp -i "$KEY" -o BatchMode=yes "$HERE/sha_ledger_flatten.py" "$VPS:/tmp/sha_ledger_flatten.py"
MSYS_NO_PATHCONV=1 ssh -i "$KEY" -o BatchMode=yes "$VPS" \
  "zcat $PARTITIONS/*.ndjson.gz | python3 /tmp/sha_ledger_flatten.py /tmp/sha_ledger_flat.tsv && docker cp /tmp/sha_ledger_flat.tsv $DB_CONTAINER:/tmp/sha_ledger_flat.tsv"
MSYS_NO_PATHCONV=1 ssh -i "$KEY" -o BatchMode=yes "$VPS" \
  "docker exec -i $DB_CONTAINER psql -U postgres -d casebible -At -F ' | ' -v ON_ERROR_STOP=1" < "$HERE/sha_ledger_coverage.sql"
