#!/usr/bin/env bash
set -euo pipefail

# Produce a current, full R2 inventory one bucket at a time after the SHA
# partition export releases its readers. CSV mode safely quotes delimiters and
# newlines in object keys. No source mutation is possible.

migration_root="${MIGRATION_ROOT:-/data/consignatio/migrations/r2-to-b2}"
partition_dir="$migration_root/hash-ledger-partitions"
output_dir="$migration_root/inventory/live-20260912"
deadline=$((SECONDS + 14400))

while (( SECONDS < deadline )); do
  finalized="$(find "$partition_dir" -maxdepth 1 -type f -name '*.ndjson.gz' | wc -l)"
  receipts="$(find "$partition_dir" -maxdepth 1 -type f -name '*.receipt' | wc -l)"
  partials="$(find "$partition_dir" -maxdepth 1 -type f -name '*.partial' | wc -l)"
  if [[ "$finalized" -eq 256 && "$receipts" -eq 256 && "$partials" -eq 0 ]]; then
    break
  fi
  sleep 60
done

test "$(find "$partition_dir" -maxdepth 1 -type f -name '*.ndjson.gz' | wc -l)" -eq 256
test "$(find "$partition_dir" -maxdepth 1 -type f -name '*.receipt' | wc -l)" -eq 256
test "$(find "$partition_dir" -maxdepth 1 -type f -name '*.partial' | wc -l)" -eq 0

mkdir -p "$output_dir"

for bucket in casebible-raw casebible-sorted casebible-quarantine; do
  final="$output_dir/$bucket.csv.gz"
  partial="$final.partial"
  checksum="$final.sha256"
  receipt="$final.receipt"

  if [[ -e "$partial" ]]; then
    echo "refusing to overwrite interrupted inventory partial: $partial" >&2
    exit 20
  fi
  if [[ ! -e "$final" ]]; then
    rclone lsf -R --files-only --csv --hash MD5 --format pshtm \
      --use-server-modtime "r2:$bucket" \
      | gzip -1 > "$partial"
    gzip -t "$partial"
    mv "$partial" "$final"
    sha256sum "$final" > "$checksum"
  else
    gzip -t "$final"
    sha256sum -c "$checksum"
  fi

  validation="$(python3 - "$final" <<'PY'
import csv
import gzip
import json
import sys

path = sys.argv[1]
rows = 0
total_bytes = 0
with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
    for row_number, row in enumerate(csv.reader(handle), start=1):
        if len(row) != 5:
            raise ValueError(f"record {row_number}: expected 5 fields, got {len(row)}")
        size = int(row[1])
        if size < 0 or not row[0]:
            raise ValueError(f"record {row_number}: invalid path or size")
        rows += 1
        total_bytes += size
print(json.dumps({"rows": rows, "bytes": total_bytes}, separators=(",", ":")))
PY
)"
  rows="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["rows"])' "$validation")"
  bytes="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["bytes"])' "$validation")"
  if [[ -e "$receipt" ]]; then
    recorded="$(awk -F= '$1 == "rows" { print $2 }' "$receipt")"
    test "$recorded" -eq "$rows"
  else
    printf 'bucket=%s\nrows=%s\nbytes=%s\nformat=rclone-lsf-pshtm-csv-gzip\n' \
      "$bucket" "$rows" "$bytes" > "$receipt"
  fi
done

python3 - "$output_dir" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
buckets = []
for receipt in sorted(root.glob("*.receipt")):
    values = {}
    for line in receipt.read_text(encoding="utf-8").splitlines():
        key, value = line.split("=", 1)
        values[key] = value
    buckets.append({
        "bucket": values["bucket"],
        "rows": int(values["rows"]),
        "bytes": int(values["bytes"]),
        "inventory": str(receipt).removesuffix(".receipt"),
    })
summary = {
    "schema": "consignatio-live-r2-inventory-summary-v1",
    "buckets": buckets,
    "rows": sum(item["rows"] for item in buckets),
    "bytes": sum(item["bytes"] for item in buckets),
}
target = root / "summary.json"
encoded = json.dumps(summary, indent=2, sort_keys=True) + "\n"
if target.exists() and target.read_text(encoding="utf-8") != encoded:
    raise SystemExit("existing inventory summary differs")
if not target.exists():
    target.write_text(encoded, encoding="utf-8")
ready = root / "READY"
if ready.exists() and ready.read_text(encoding="utf-8") != "READY\n":
    raise SystemExit("existing READY marker differs")
if not ready.exists():
    ready.write_text("READY\n", encoding="utf-8")
PY
