#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-16 17:15 EDT (session propria-79)
# Step 3 of the owner's 07:12 order: copy the leftover intake objects into the vault (additive, Immutable, no deletes),
# then a fresh vault listing into the catalog and the proof table for step 4. Run ON ovh-files, detached.
# Stops before step 4: the intake delete runs separately through the checked phase runner.
set -euo pipefail
RUN=/data/consignatio/migrations/vault-consolidation-20260915
OUT="$RUN/prune-20260916"
PG=fgz1n7useplhk0t91uk7k1aw
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
cd "$OUT"

test -s move_rest_manifest.csv || { echo "ABORT: move_rest_manifest.csv missing"; exit 2; }
echo "copying $(($(wc -l < move_rest_manifest.csv) - 1)) objects"
systemd-run --unit consignatio-vault-move-rest-20260916 --wait --pipe --quiet -p EnvironmentFile="$ENVF" -p MemoryMax=2G \
  /usr/bin/python3 "$RUN/vault_copy_driver.py" copy --manifest "$OUT/move_rest_manifest.csv" \
    --ledger "$OUT/move_rest.ledger.sqlite" --config /opt/casebible/rclone.conf --rclone-log "$OUT/move_rest.rcd.log" --workers 32

systemd-run --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
  /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --fast-list --hash --hash-type sha1 \
    --config /opt/casebible/rclone.conf b2:salem-data/consignatio/vault/v1/ > vault.post-move.lsjson.json

/usr/bin/python3 - <<'PY'
import csv, json
w = csv.writer(open("vault_post_move.csv", "w", newline="", encoding="utf-8"))
w.writerow(["key", "size", "sha1"])
for i in json.load(open("vault.post-move.lsjson.json", encoding="utf-8")):
    w.writerow(["consignatio/vault/v1/" + i["Path"], i["Size"], (i.get("Hashes") or {}).get("sha1", "")])
print("csv written")
PY

docker cp vault_post_move.csv "$PG:/tmp/vault_post_move.csv"
docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 < "$RUN/vault_move_rest_confirm_20260916.sql"
docker cp "$PG:/tmp/intake_moved_delete.list" "$OUT/intake_moved_delete.list"
echo "intake_moved_delete.list: $(wc -l < "$OUT/intake_moved_delete.list") keys"
