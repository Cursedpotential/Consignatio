#!/usr/bin/env bash
set -euo pipefail

# Follow-on job for the bounded SHA export. This script finalizes metadata only:
# it does not create the corpus gate and cannot copy, move, or delete payloads.

migration_root="${MIGRATION_ROOT:-/data/consignatio/migrations/r2-to-b2}"
builder_root="${BUILDER_ROOT:-$migration_root/components/manifest-builder/20260912T180000Z}"
partition_dir="$migration_root/hash-ledger-partitions"
ledger="$migration_root/state/corpus-ledger-live-20260912.sqlite"
live_inventory_dir="$migration_root/inventory/live-20260912"
generation_dir="$migration_root/generations/live-r2-sha256-v2-20260912"
expected_partitions=256
expected_records=338318
deadline=$((SECONDS + 14400))

while (( SECONDS < deadline )); do
  finalized="$(find "$partition_dir" -maxdepth 1 -type f -name '*.ndjson.gz' | wc -l)"
  receipts="$(find "$partition_dir" -maxdepth 1 -type f -name '*.receipt' | wc -l)"
  partials="$(find "$partition_dir" -maxdepth 1 -type f -name '*.partial' | wc -l)"
  if [[ "$finalized" -eq "$expected_partitions" && "$receipts" -eq "$expected_partitions" && "$partials" -eq 0 ]]; then
    break
  fi
  sleep 60
done

finalized="$(find "$partition_dir" -maxdepth 1 -type f -name '*.ndjson.gz' | wc -l)"
receipts="$(find "$partition_dir" -maxdepth 1 -type f -name '*.receipt' | wc -l)"
partials="$(find "$partition_dir" -maxdepth 1 -type f -name '*.partial' | wc -l)"
if [[ "$finalized" -ne "$expected_partitions" || "$receipts" -ne "$expected_partitions" || "$partials" -ne 0 ]]; then
  echo "partition set incomplete: finalized=$finalized receipts=$receipts partials=$partials" >&2
  exit 10
fi

for value in $(seq 0 255); do
  prefix="$(printf '%02x' "$value")"
  test -f "$partition_dir/$prefix.ndjson.gz"
  test -f "$partition_dir/$prefix.ndjson.gz.sha256"
  test -f "$partition_dir/$prefix.ndjson.gz.receipt"
  sha256sum -c "$partition_dir/$prefix.ndjson.gz.sha256"
done

record_total="$(awk -F= '$1 == "records" { total += $2 } END { print total + 0 }' "$partition_dir"/*.receipt)"
if [[ "$record_total" -ne "$expected_records" ]]; then
  echo "record count mismatch: expected=$expected_records observed=$record_total" >&2
  exit 11
fi

inventory_deadline=$((SECONDS + 14400))
while (( SECONDS < inventory_deadline )); do
  if [[ -f "$live_inventory_dir/READY" && -f "$live_inventory_dir/summary.json" ]]; then
    break
  fi
  sleep 60
done
test -f "$live_inventory_dir/READY"
test -f "$live_inventory_dir/summary.json"

cd "$builder_root"
PYTHONPATH=src python3 - "$ledger" "$live_inventory_dir" <<'PY'
import sys
from pathlib import Path

from r2_b2_manifest.builder import ManifestBuilder

ledger = Path(sys.argv[1])
root = Path(sys.argv[2])
with ManifestBuilder(ledger) as builder:
    for bucket in ("casebible-raw", "casebible-sorted", "casebible-quarantine"):
        builder.ingest([root / f"{bucket}.csv.gz"], source_bucket=bucket)
PY

backup_dir="$migration_root/state/backups"
mkdir -p "$backup_dir"
backup="$backup_dir/corpus-ledger-before-sha-finalize-$(date -u +%Y%m%dT%H%M%SZ).sqlite"
cp --reflink=auto --preserve=mode,timestamps "$ledger" "$backup"
sha256sum "$backup" > "$backup.sha256"

partition_args=()
for value in $(seq 0 255); do
  prefix="$(printf '%02x' "$value")"
  partition_args+=(--ledger-partition "$partition_dir/$prefix.ndjson.gz")
done

cd "$builder_root"
PYTHONPATH=src python3 -m r2_b2_manifest.cli import-sha256-ledger \
  --ledger "$ledger" "${partition_args[@]}" \
  > "$migration_root/state/sha256-import-final.json"

PYTHONPATH=src python3 -m r2_b2_manifest.cli finalize-sha256-bridge \
  --ledger "$ledger" \
  --expected-partition-count "$expected_partitions" \
  --expected-record-count "$expected_records" \
  > "$migration_root/state/sha256-bridge-finalization.json"

mkdir -p "$generation_dir"
PYTHONPATH=src python3 -m r2_b2_manifest.cli build \
  --ledger "$ledger" \
  --output-dir "$generation_dir" \
  --inventory "$live_inventory_dir/casebible-raw.csv.gz" \
  --inventory "$live_inventory_dir/casebible-sorted.csv.gz" \
  --inventory "$live_inventory_dir/casebible-quarantine.csv.gz" \
  --destination-remote 'b2:salem-data' \
  --destination-prefix 'consignatio/intake/raw-dedupe/v1' \
  > "$generation_dir/build-result.json"

python3 - "$generation_dir/payload-mapping.jsonl" "$generation_dir" <<'PY'
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
root = Path(sys.argv[2])
targets = {
    "canonical": root / "payload-canonical.jsonl",
    "source-identity": root / "payload-source-identity.jsonl",
    "held": root / "payload-held.jsonl",
}
counts = {key: 0 for key in targets}
handles = {key: path.open("x", encoding="utf-8", newline="\n") for key, path in targets.items()}
try:
    with source.open(encoding="utf-8") as input_handle:
        for line_number, line in enumerate(input_handle, start=1):
            row = json.loads(line)
            disposition = row.get("disposition")
            if disposition not in handles:
                raise ValueError(f"row {line_number}: unexpected disposition {disposition!r}")
            handles[disposition].write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            counts[disposition] += 1
finally:
    for handle in handles.values():
        handle.close()
if counts["canonical"] <= 0:
    raise SystemExit("split mapping contains no canonical payloads")
(root / "payload-split-summary.json").write_text(
    json.dumps(counts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
PY

cd "$migration_root/runtime"
python3 payload_runner.py run \
  --mode dry-run \
  --verification fast \
  --workers 2 \
  --run-id live-r2-sha256-v2-dryrun-20260912 \
  --format jsonl \
  --mapping "$generation_dir/payload-canonical.jsonl" \
  > "$generation_dir/payload-canonical-dry-run.json"

source_identity_count="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source-identity"])' "$generation_dir/payload-split-summary.json")"
if [[ "$source_identity_count" -gt 0 ]]; then
  python3 payload_runner.py run \
    --mode dry-run \
    --verification full \
    --workers 1 \
    --run-id live-r2-source-identity-dryrun-20260912 \
    --format jsonl \
    --mapping "$generation_dir/payload-source-identity.jsonl" \
    > "$generation_dir/payload-source-identity-dry-run.json"
else
  printf '{"planned":0,"planned_bytes":0,"failed":0,"result":"dry-run"}\n' \
    > "$generation_dir/payload-source-identity-dry-run.json"
fi

printf 'READY_FOR_REVIEW\n' > "$generation_dir/READY_FOR_REVIEW"
(
  cd "$generation_dir"
  find . -type f ! -name SHA256SUMS -print0 \
    | sort -z \
    | xargs -0 sha256sum > SHA256SUMS
)
printf 'generation_dir=%s\nrecords=%s\npartitions=%s\nledger_backup=%s\n' \
  "$generation_dir" "$record_total" "$finalized" "$backup"
