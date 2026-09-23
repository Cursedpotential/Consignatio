#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-16 17:40 EDT (session propria-79)
# One repeatable round of steps 3–4 of the owner's 07:12 order ("move it. Then clean the intake again") for whatever is
# still in intake — needed because B2 keys can hold older stored versions that only become visible after a delete.
# Run ON ovh-files, detached:  vault_move_round.sh <round number>   (round 1 = the first move, already done)
#   1. fresh intake + vault listings (B2-stored sha1) → catalog tables raw_duck.{intake,vault}_objects_20260916_r<N>
#   2. plan in SQL (vault_move_rest_20260916.sql with round table names): sha1+size already in vault → delete only;
#      otherwise copy to vault/v1/<path inside source root> (name clash → " [<source>]")
#   3. copy (Immutable), fresh vault listing → raw_duck.vault_objects_20260916_post_move_r<N>, prove every row
#   4. delete proven rows from intake with the checked phase runner (catalog = the proven rows' own size + sha1)
set -euo pipefail
N="${1:?round number}"
RUN=/data/consignatio/migrations/vault-consolidation-20260915
OUT="$RUN/prune-20260916"
W="$OUT/round-$N"
PG=fgz1n7useplhk0t91uk7k1aw
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
CONF=/opt/casebible/rclone.conf
mkdir -p "$W"; cd "$W"

list_to_csv() {  # $1 prefix under bucket, $2 csv
  systemd-run --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
    /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --fast-list --hash --hash-type sha1 \
      --config "$CONF" "b2:salem-data/$1" > "$2.json"
  /usr/bin/python3 - "$1" "$2" <<'PY'
import csv, json, sys
prefix, out = sys.argv[1], sys.argv[2]
w = csv.writer(open(out, "w", newline="", encoding="utf-8"))
w.writerow(["key", "size", "sha1"])
for i in json.load(open(out + ".json", encoding="utf-8")):
    w.writerow([prefix + i["Path"], i["Size"], (i.get("Hashes") or {}).get("sha1", "")])
PY
}

load_table() {  # $1 csv, $2 table
  docker cp "$1" "$PG:/tmp/$(basename "$1")"
  docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 -q <<SQL
drop table if exists raw_duck.$2;
create table raw_duck.$2 (key text primary key, size bigint, sha1 text);
\copy raw_duck.$2 from '/tmp/$(basename "$1")' with (format csv, header)
create index on raw_duck.$2 (sha1, size);
SQL
}

echo "== round $N: listings"
list_to_csv consignatio/intake/raw-dedupe/v1/source-buckets/ intake.csv
list_to_csv consignatio/vault/v1/ vault.csv
load_table intake.csv "intake_objects_20260916_r$N"
load_table vault.csv "vault_objects_20260916_r$N"
echo "intake objects: $(($(wc -l < intake.csv) - 1))"
if [ "$(wc -l < intake.csv)" -le 1 ]; then echo "INTAKE EMPTY"; exit 0; fi

echo "== round $N: plan"
sed -e "s/intake_objects_20260916_post_clean/intake_objects_20260916_r$N/g" \
    -e "s/vault_objects_20260916_post_prune/vault_objects_20260916_r$N/g" \
    -e "s/vault_move_rest_20260916/vault_move_rest_20260916_r$N/g" \
    -e "s#/tmp/move_rest_manifest.csv#/tmp/move_rest_manifest_r$N.csv#g" \
    "$RUN/vault_move_rest_20260916.sql" > plan.sql
docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 < plan.sql
docker cp "$PG:/tmp/move_rest_manifest_r$N.csv" manifest.csv

if [ "$(wc -l < manifest.csv)" -gt 1 ]; then
  echo "== round $N: copy $(($(wc -l < manifest.csv) - 1)) objects"
  systemd-run --unit "consignatio-vault-move-r$N-20260916" --wait --pipe --quiet -p EnvironmentFile="$ENVF" -p MemoryMax=2G \
    /usr/bin/python3 "$RUN/vault_copy_driver.py" copy --manifest "$W/manifest.csv" --ledger "$W/copy.ledger.sqlite" \
      --config "$CONF" --rclone-log "$W/copy.rcd.log" --workers 16
fi

echo "== round $N: prove"
list_to_csv consignatio/vault/v1/ vault_after.csv
sed -e "s/vault_objects_20260916_post_move/vault_objects_20260916_post_move_r$N/g" \
    -e "s/intake_moved_delete_20260916/intake_moved_delete_20260916_r$N/g" \
    -e "s/vault_move_rest_20260916/vault_move_rest_20260916_r$N/g" \
    -e "s/vault_objects_20260916_post_prune/vault_objects_20260916_r$N/g" \
    -e "s#/tmp/vault_post_move.csv#/tmp/vault_after.csv#g" \
    -e "s#/tmp/intake_moved_delete.list#/tmp/intake_moved_delete_r$N.list#g" \
    "$RUN/vault_move_rest_confirm_20260916.sql" > confirm.sql
docker cp vault_after.csv "$PG:/tmp/vault_after.csv"
docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 < confirm.sql
docker cp "$PG:/tmp/intake_moved_delete_r$N.list" delete.list
docker exec "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 -q -c \
  "copy (select key, size, coalesce(sha1,'') sha1 from raw_duck.intake_moved_delete_20260916_r$N order by key) to '/tmp/moved_catalog_r$N.csv' with (format csv, header)"
docker cp "$PG:/tmp/moved_catalog_r$N.csv" catalog.csv

echo "== round $N: delete $(wc -l < delete.list) proven objects from intake"
systemd-run --unit "consignatio-vault-phases-moved-r$N" --wait --pipe --quiet -p EnvironmentFile="$ENVF" -p MemoryMax=2G \
  /usr/bin/python3 "$RUN/vault_phase_runner.py" --list "$W/delete.list" \
    --base consignatio/intake/raw-dedupe/v1/source-buckets/ --workdir "$W/phases" --catalog "$W/catalog.csv" || true
/usr/bin/python3 - "$W/phases/phases.jsonl" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
print("round phases", len(rows), "| PASS", sum(r["status"] == "PASS" for r in rows), "| removed",
      sum(r.get("removed") or 0 for r in rows), "| other files gone", sum(r.get("other_files_gone") or 0 for r in rows),
      "| kept differs", sum(r.get("kept_differs") or 0 for r in rows), "| still there", rows[-1].get("still_present"))
PY
