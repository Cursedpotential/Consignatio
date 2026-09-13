#!/usr/bin/env bash
set -euo pipefail

# Operator follow-on for the 2026-09-12 approved migration. It waits for the
# independently checksummed manifest generation, runs one full-verification
# copy, publishes the frozen catalog, and only then begins bounded fast copy.

migration_root="${MIGRATION_ROOT:-/data/consignatio/migrations/r2-to-b2}"
generation_dir="$migration_root/generations/live-r2-sha256-v2-20260912"
runtime_dir="$migration_root/runtime"
control_file="$migration_root/controls/ENABLE_CORPUS_TRANSFER.20260912.approved"
gate_file="$runtime_dir/ENABLE_CORPUS_TRANSFER"
mapping="$generation_dir/payload-canonical.jsonl"
source_identity_mapping="$generation_dir/payload-source-identity.jsonl"
split_summary="$generation_dir/payload-split-summary.json"
probe_mapping="$generation_dir/first-copy.mapping.jsonl"
deadline=$((SECONDS + 21600))

while (( SECONDS < deadline )); do
  if [[ -f "$generation_dir/READY_FOR_REVIEW" ]]; then
    break
  fi
  sleep 60
done

test -f "$generation_dir/READY_FOR_REVIEW"
test -f "$generation_dir/SHA256SUMS"
test -f "$mapping"
test -f "$source_identity_mapping"
test -f "$split_summary"
test -f "$control_file"

(
  cd "$generation_dir"
  sha256sum -c SHA256SUMS
)

python3 - "$generation_dir/build-result.json" \
  "$generation_dir/payload-canonical-dry-run.json" \
  "$generation_dir/payload-source-identity-dry-run.json" \
  "$migration_root/inventory/live-20260912/summary.json" \
  "$split_summary" <<'PY'
import json
import sys

build = json.load(open(sys.argv[1], encoding="utf-8"))
canonical_dry_run = json.load(open(sys.argv[2], encoding="utf-8"))
source_identity_dry_run = json.load(open(sys.argv[3], encoding="utf-8"))
summary = json.load(open(sys.argv[4], encoding="utf-8"))
split = json.load(open(sys.argv[5], encoding="utf-8"))
if build.get("occurrence_count") != summary.get("rows"):
    raise SystemExit(f"unexpected occurrence count: {build.get('occurrence_count')}")
if build.get("sha256_verified_content_count", 0) <= 0:
    raise SystemExit("generation contains no SHA-256 content")
if canonical_dry_run.get("result") != "dry-run" or canonical_dry_run.get("failed") != 0:
    raise SystemExit("canonical payload dry-run did not complete cleanly")
if canonical_dry_run.get("planned") != split.get("canonical") or canonical_dry_run.get("planned_bytes", 0) <= 0:
    raise SystemExit("canonical payload dry-run does not match the split manifest")
if source_identity_dry_run.get("result") != "dry-run" or source_identity_dry_run.get("failed") != 0:
    raise SystemExit("source-identity payload dry-run did not complete cleanly")
if source_identity_dry_run.get("planned") != split.get("source-identity"):
    raise SystemExit("source-identity payload dry-run does not match the split manifest")
PY

python3 - "$mapping" "$probe_mapping" <<'PY'
import json
import sys
from pathlib import Path

source, target = sys.argv[1:]
with open(source, encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("disposition") == "canonical" and 0 < int(row["size"]) <= 1024 * 1024:
            expected = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            target_path = Path(target)
            if target_path.exists():
                if target_path.read_text(encoding="utf-8") != expected:
                    raise SystemExit("existing first-copy mapping differs from deterministic selection")
            else:
                target_path.write_text(expected, encoding="utf-8", newline="\n")
            break
    else:
        raise SystemExit("no <=1 MiB canonical payload available for first-copy verification")
PY

install -m 0600 -o root -g root "$control_file" "$gate_file"

cd "$runtime_dir"
python3 payload_runner.py run \
  --mode transfer \
  --verification full \
  --workers 1 \
  --memory-limit-mib 512 \
  --run-id live-r2-sha256-v2-first-copy-20260912 \
  --format jsonl \
  --mapping "$probe_mapping" \
  > "$generation_dir/first-copy.result.json"

python3 - "$generation_dir/first-copy.result.json" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
if result.get("result") != "complete" or result.get("failed") != 0 or result.get("verified") != 1:
    raise SystemExit(f"first mapped copy did not verify: {result}")
PY

snapshot="$generation_dir/catalog-ledger.sqlite"
if [[ ! -e "$snapshot" ]]; then
  cp --reflink=auto --preserve=mode,timestamps "$migration_root/state/corpus-ledger-live-20260912.sqlite" "$snapshot"
fi
sha256sum "$snapshot" > "$snapshot.sha256"

if [[ ! -e "$generation_dir/SHA256SUMS.pre-transfer" ]]; then
  cp --preserve=mode,timestamps "$generation_dir/SHA256SUMS" "$generation_dir/SHA256SUMS.pre-transfer"
fi
(
  cd "$generation_dir"
  find . -type f ! -name SHA256SUMS -print0 \
    | sort -z \
    | xargs -0 sha256sum > SHA256SUMS
)

set -a
source /data/consignatio/secrets/rclone-b2.env
set +a
rclone copy --immutable --metadata "$generation_dir" \
  'b2:salem-data/consignatio/intake/raw-dedupe/v1/_system/lake/generations/live-r2-sha256-v2-20260912'

python3 payload_runner.py run \
  --mode transfer \
  --verification fast \
  --workers 2 \
  --checkers 4 \
  --buffer-size 4M \
  --b2-chunk-size 16M \
  --b2-upload-concurrency 1 \
  --memory-limit-mib 1024 \
  --max-duration-seconds 604800 \
  --run-id live-r2-sha256-v2-bulk-20260912 \
  --format jsonl \
  --mapping "$mapping" \
  > "$generation_dir/bulk-transfer.result.json"

source_identity_count="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source-identity"])' "$split_summary")"
if [[ "$source_identity_count" -gt 0 ]]; then
  python3 payload_runner.py run \
    --mode transfer \
    --verification full \
    --workers 1 \
    --checkers 2 \
    --buffer-size 4M \
    --b2-chunk-size 16M \
    --b2-upload-concurrency 1 \
    --memory-limit-mib 768 \
    --max-duration-seconds 604800 \
    --run-id live-r2-source-identity-full-20260912 \
    --format jsonl \
    --mapping "$source_identity_mapping" \
    > "$generation_dir/source-identity-transfer.result.json"
fi
