#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-16 11:05 EDT (session propria-79)
# Step 1 check of the owner's 07:11 order ("First, clean the intake"). Run ON ovh-files, detached.
# Fresh intake listing (with B2-stored sha1) → CSVs → PG catalog tables (intake_post_clean_20260916.sql) → checks.
set -euo pipefail
RUN=/data/consignatio/migrations/vault-consolidation-20260915
OUT="$RUN/prune-20260916"
PG=fgz1n7useplhk0t91uk7k1aw
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
cd "$OUT"

systemd-run --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
  /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --fast-list --hash --hash-type sha1 \
    --config /opt/casebible/rclone.conf b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/ \
  > intake.post-clean.lsjson.json

/usr/bin/python3 - <<'PY'
import csv, json
P = "consignatio/intake/raw-dedupe/v1/source-buckets/"
def writer(name, header):
    w = csv.writer(open(name, "w", newline="", encoding="utf-8"))
    w.writerow(header)
    return w
w = writer("intake_post_clean.csv", ["key", "size", "sha1"])
for i in json.load(open("intake.post-clean.lsjson.json", encoding="utf-8")):
    w.writerow([P + i["Path"], i["Size"], (i.get("Hashes") or {}).get("sha1", "")])
w = writer("intake_before.csv", ["key", "size"])
for i in json.load(open("intake.before.lsjson.json", encoding="utf-8")):
    w.writerow([P + i["Path"], i["Size"]])
w = writer("intake_delete.csv", ["key"])
for line in open("intake_delete.list", encoding="utf-8"):
    w.writerow([line.rstrip("\n")])
w = writer("versions_differ.csv", ["key", "size", "sha1"])
for line in open("phases-intake/versions_differ.tsv", encoding="utf-8"):
    k, s, h, _ = line.rstrip("\n").split("\t", 3)
    w.writerow([k, s, h])
print("csvs written")
PY

for f in intake_post_clean.csv intake_before.csv intake_delete.csv versions_differ.csv; do
  docker cp "$f" "$PG:/tmp/$f"
done
docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 < "$RUN/intake_post_clean_20260916.sql"
