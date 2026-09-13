#!/usr/bin/env bash
set -Eeuo pipefail

umask 027

readonly LIVE_NAMESPACE="consignatio"
readonly LIVE_DATABASE="intake"
readonly ENDPOINT="http://127.0.0.1:8000"
readonly BACKUP_ROOT="/data/consignatio/backups/surreal-intake"
readonly LOCK_FILE="/run/lock/consignatio-surreal-intake-restore-drill.lock"
readonly DEFAULT_CONTAINER_LABEL="com.docker.compose.service=surreal-intake"

usage() {
  cat >&2 <<'USAGE'
Usage: restore-drill.sh --namespace restore_drill_NAME --database restore_drill_NAME --export /data/consignatio/backups/surreal-intake/FILE.surql

The target must be a deliberately named restore-drill namespace/database. The
live consignatio/intake target is always refused. The target must be empty.
Credentials are inherited inside the selected container and are never accepted
as arguments.
USAGE
  exit 64
}

namespace=""
database=""
export_path=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --namespace)
      [[ $# -ge 2 ]] || usage
      namespace="$2"
      shift 2
      ;;
    --database)
      [[ $# -ge 2 ]] || usage
      database="$2"
      shift 2
      ;;
    --export)
      [[ $# -ge 2 ]] || usage
      export_path="$2"
      shift 2
      ;;
    *) usage ;;
  esac
done

[[ -n "$namespace" && -n "$database" && -n "$export_path" ]] || usage
if [[ "$namespace" == "$LIVE_NAMESPACE" && "$database" == "$LIVE_DATABASE" ]]; then
  printf 'Refusing to restore into the live %s/%s database.\n' "$LIVE_NAMESPACE" "$LIVE_DATABASE" >&2
  exit 77
fi
if [[ ! "$namespace" =~ ^restore_drill_[A-Za-z0-9_]{1,48}$ ]]; then
  printf 'Restore-drill namespace must match restore_drill_[A-Za-z0-9_]{1,48}.\n' >&2
  exit 64
fi
if [[ ! "$database" =~ ^restore_drill_[A-Za-z0-9_]{1,48}$ ]]; then
  printf 'Restore-drill database must match restore_drill_[A-Za-z0-9_]{1,48}.\n' >&2
  exit 64
fi

for required in docker flock sha256sum realpath logger python3; do
  command -v "$required" >/dev/null 2>&1 || {
    printf 'Required command is unavailable: %s\n' "$required" >&2
    exit 69
  }
done

if [[ ! -f "$export_path" || -L "$export_path" ]]; then
  printf 'Export must be an existing regular, non-symlink file.\n' >&2
  exit 66
fi
resolved_export="$(realpath -e -- "$export_path")"
if [[ "$(dirname -- "$resolved_export")" != "$BACKUP_ROOT" || "$resolved_export" != *.surql ]]; then
    printf 'Export must be a .surql artifact directly under %s.\n' "$BACKUP_ROOT" >&2
    exit 66
fi

checksum_path="${resolved_export%.surql}.sha256"
if [[ ! -f "$checksum_path" || -L "$checksum_path" ]]; then
  printf 'A regular, non-symlink SHA-256 manifest is required: %s\n' "$checksum_path" >&2
  exit 66
fi
# The manifest must name exactly the selected export, not a different file that
# happens to have a valid checksum. Reject extra entries and path components.
python3 - "$resolved_export" "$checksum_path" <<'PY'
import hashlib
import pathlib
import re
import sys

export = pathlib.Path(sys.argv[1])
manifest = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
match = re.fullmatch(r"([0-9a-fA-F]{64})  " + re.escape(export.name) + r"\n?", manifest)
if not match:
    raise SystemExit("Manifest must contain exactly the selected export and its SHA-256")
with export.open("rb") as source:
    digest = hashlib.sha256()
    for block in iter(lambda: source.read(1024 * 1024), b""):
        digest.update(block)
    actual = digest.hexdigest()
if actual != match.group(1).lower():
    raise SystemExit("Export SHA-256 mismatch; restore refused")
print("Export SHA-256 verified")
PY

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  printf 'Another restore drill holds %s.\n' "$LOCK_FILE" >&2
  exit 75
fi

readonly container_label="${SURREAL_RESTORE_CONTAINER_LABEL:-$DEFAULT_CONTAINER_LABEL}"
if [[ ! "$container_label" =~ ^[A-Za-z0-9_.-]+=[A-Za-z0-9_.-]+$ ]]; then
  printf 'SURREAL_RESTORE_CONTAINER_LABEL is invalid.\n' >&2
  exit 64
fi
mapfile -t containers < <(
  docker ps \
    --filter "label=${container_label}" \
    --filter "status=running" \
    --format '{{.ID}}'
)
if [[ "${#containers[@]}" -ne 1 ]]; then
  printf 'Expected exactly one running target container; found %s.\n' "${#containers[@]}" >&2
  exit 69
fi
readonly container_id="${containers[0]}"
docker exec "$container_id" /surreal is-ready --endpoint "$ENDPOINT" >/dev/null

# Parse JSON structurally. CLI versions can return raw statement results or
# response envelopes; neither command success nor a regex match proves success.
table_count() {
  python3 -c '
import json, sys
results = json.load(sys.stdin)
if not isinstance(results, list) or len(results) != 1:
    raise SystemExit("Expected one SQL result")
value = results[0]
if isinstance(value, dict):
    if value.get("status") != "OK":
        raise SystemExit("SQL response did not succeed")
    value = value.get("result")
if type(value) is not int or value < 0:
    raise SystemExit("SQL result was not a nonnegative table count")
print(value)
'
}

# Fail closed unless INFO FOR DB proves there are no existing table definitions.
info_output="$(
  printf 'RETURN array::len(object::keys((INFO FOR DB).tables));\n' |
    docker exec -i "$container_id" /surreal sql \
      --endpoint "$ENDPOINT" \
      --auth-level root \
      --namespace "$namespace" \
      --database "$database" \
      --json
)"
if ! initial_count="$(printf '%s' "$info_output" | table_count)" || [[ "$initial_count" != 0 ]]; then
  printf 'Target is not provably empty; restore refused. INFO result: %s\n' "$info_output" >&2
  exit 78
fi

# SurrealDB <3.3 checks ENFORCED endpoints during import. Preserve source bytes
# and derive schema-first, dependency-ordered data without weakening enforcement.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
derived_export="${resolved_export%.surql}-${namespace}-${database}-ordered.surql"
python3 "$script_dir/order_restore.py" "$resolved_export" "$derived_export"
chmod 0440 "$derived_export" "${derived_export%.surql}.receipt.json"

# SurrealDB 3.2.4 import requires a file; '-' is a literal filename.
# Keep the drill input for inspection under a unique container-local path.
container_export="/tmp/${namespace}-${database}-$(date -u +%Y%m%dT%H%M%SZ).surql"
docker cp "$derived_export" "${container_id}:${container_export}"
docker exec "$container_id" /surreal import \
  --endpoint "$ENDPOINT" \
  --auth-level root \
  --namespace "$namespace" \
  --database "$database" \
  "$container_export"

post_info="$(
  printf 'RETURN array::len(object::keys((INFO FOR DB).tables));\n' |
    docker exec -i "$container_id" /surreal sql \
      --endpoint "$ENDPOINT" \
      --auth-level root \
      --namespace "$namespace" \
      --database "$database" \
      --json
)"
if ! restored_count="$(printf '%s' "$post_info" | table_count)" || [[ "$restored_count" -lt 1 ]]; then
  printf 'Import returned, but restored schema verification failed: %s\n' "$post_info" >&2
  logger -t surreal-intake-restore-drill -- "error verification_failed target=${namespace}/${database}"
  exit 79
fi

logger -t surreal-intake-restore-drill -- "info completed target=${namespace}/${database} source=$(basename -- "$resolved_export")"
printf 'Restore drill completed in isolated target %s/%s. %s\n' "$namespace" "$database" "$post_info"
printf 'The drill target is intentionally retained; do not remove it automatically.\n'
