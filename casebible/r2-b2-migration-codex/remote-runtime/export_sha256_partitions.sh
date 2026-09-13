#!/usr/bin/env bash
set -euo pipefail

# Stream the R2 SHA-256 ledger into bounded, independently verifiable partitions.
# Existing finalized partitions are never overwritten. Interrupted .partial files
# must be moved to the migration's to_be_deleted area before a resume.

output_dir="${1:?usage: export_sha256_partitions.sh OUTPUT_DIR [WORKERS]}"
workers="${2:-2}"
source_root="${SOURCE_ROOT:-r2:casebible-hash-ledger/sha256/v2}"

case "$workers" in
  1|2) ;;
  *) echo "workers must be 1 or 2" >&2; exit 2 ;;
esac

mkdir -p "$output_dir"

export_one() {
  prefix="$1"
  final="$output_dir/$prefix.ndjson.gz"
  partial="$final.partial"
  checksum="$final.sha256"
  receipt="$final.receipt"

  if [[ -e "$partial" ]]; then
    echo "refusing to overwrite interrupted partial: $partial" >&2
    return 3
  fi

  if [[ -e "$final" ]]; then
    gzip -t "$final"
    if [[ -e "$checksum" ]]; then
      sha256sum -c "$checksum"
    else
      sha256sum "$final" > "$checksum"
    fi
  else
    rclone --include '*.json' --separator $'\n' cat "$source_root/$prefix" \
      | gzip -1 > "$partial"
    gzip -t "$partial"
    mv "$partial" "$final"
    sha256sum "$final" > "$checksum"
  fi

  records="$({ python3 - "$final" <<'PY'
import gzip
import json
import re
import sys

path = sys.argv[1]
digest_re = re.compile(r"^[0-9a-fA-F]{64}$")
records = 0
with gzip.open(path, "rt", encoding="utf-8") as handle:
    for line_number, line in enumerate(handle, start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number}: expected JSON object")
        if value.get("schema") != "casebible-r2-sha256-record-v2":
            raise ValueError(f"line {line_number}: unexpected schema")
        if not digest_re.fullmatch(str(value.get("digest", ""))):
            raise ValueError(f"line {line_number}: invalid SHA-256 digest")
        records += 1
print(records)
PY
  } 2>&1)" || {
    echo "validation failed for $final: $records" >&2
    return 4
  }

  if [[ -e "$receipt" ]]; then
    recorded="$(awk -F= '$1 == "records" { print $2 }' "$receipt")"
    if [[ "$recorded" != "$records" ]]; then
      echo "receipt count mismatch for $final: recorded=$recorded actual=$records" >&2
      return 5
    fi
  else
    printf 'prefix=%s\nrecords=%s\nsource=%s/%s\n' \
      "$prefix" "$records" "$source_root" "$prefix" > "$receipt"
  fi

  printf '%s %s\n' "$prefix" "$records"
}

export output_dir source_root
export -f export_one

python3 - <<'PY' | xargs -r -n 1 -P "$workers" bash -c 'export_one "$1"' _
for value in range(256):
    print(f"{value:02x}")
PY
