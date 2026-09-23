#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-16 16:55 EDT (session propria-79)
# Step 2 check (owner 07:12 "Then clean the vault"). Run ON ovh-files, detached.
# Fresh vault listing with B2-stored sha1 → CSV → PG catalog table (vault_post_prune_20260916.sql) → checks.
set -euo pipefail
RUN=/data/consignatio/migrations/vault-consolidation-20260915
OUT="$RUN/prune-20260916"
PG=fgz1n7useplhk0t91uk7k1aw
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
cd "$OUT"

systemd-run --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
  /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --fast-list --hash --hash-type sha1 \
    --config /opt/casebible/rclone.conf b2:salem-data/consignatio/vault/v1/ \
  > vault.post-prune.lsjson.json

/usr/bin/python3 - <<'PY'
import csv, json
P = "consignatio/vault/v1/"
w = csv.writer(open("vault_post_prune.csv", "w", newline="", encoding="utf-8"))
w.writerow(["key", "size", "sha1"])
for i in json.load(open("vault.post-prune.lsjson.json", encoding="utf-8")):
    w.writerow([P + i["Path"], i["Size"], (i.get("Hashes") or {}).get("sha1", "")])
print("csv written")
PY

docker cp vault_post_prune.csv "$PG:/tmp/vault_post_prune.csv"
docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 < "$RUN/vault_post_prune_20260916.sql"
