#!/usr/bin/env bash
set -Eeuo pipefail

umask 027

readonly NAMESPACE="consignatio"
readonly DATABASE="intake"
readonly ENDPOINT="http://127.0.0.1:8000"
readonly BACKUP_ROOT="/data/consignatio/backups/surreal-intake"
readonly QUARANTINE_ROOT="/data/consignatio/to_be_deleted/surreal-intake-backups"
readonly LOCK_FILE="/run/lock/consignatio-surreal-intake-backup.lock"
readonly CONTAINER_LABEL="com.docker.compose.service=surreal-intake"
readonly RETENTION_DAYS="${SURREAL_INTAKE_RETENTION_DAYS:-30}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
event_log="${BACKUP_ROOT}/events.jsonl"
partial_path=""
manifest_partial=""
completed=0
log_ready=0

json_log() {
  local level="$1"
  local event="$2"
  local detail="${3:-}"
  local now
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '{"at":"%s","level":"%s","event":"%s","detail":"%s"}\n' \
    "$now" "$level" "$event" "$detail" >>"$event_log"
  logger -t surreal-intake-backup -- "${level} ${event} ${detail}" || true
}

quarantine_partial_on_exit() {
  local status=$?
  if [[ "$status" -ne 0 && "$log_ready" -eq 1 ]]; then
    if [[ "$completed" -eq 1 ]]; then
      json_log "error" "post_export_failed" "exit_status=${status}; completed export retained"
      exit "$status"
    fi
    local failed_dir="${QUARANTINE_ROOT}/failed-${timestamp}"
    mkdir -p -- "$failed_dir"
    if [[ -n "$partial_path" && -e "$partial_path" ]]; then
      mv -- "$partial_path" "$failed_dir/"
    fi
    if [[ -n "$manifest_partial" && -e "$manifest_partial" ]]; then
      mv -- "$manifest_partial" "$failed_dir/"
    fi
    json_log "error" "backup_failed" "exit_status=${status}; preserved=${failed_dir}"
  fi
  exit "$status"
}
trap quarantine_partial_on_exit EXIT

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Required command is unavailable: %s\n' "$1" >&2
    exit 69
  }
}

for required in docker flock sha256sum find stat logger awk; do
  require_command "$required"
done

if [[ ! "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
  printf 'SURREAL_INTAKE_RETENTION_DAYS must be a positive integer.\n' >&2
  exit 64
fi

mkdir -p -- "$BACKUP_ROOT" "$QUARANTINE_ROOT"
if [[ -L "$BACKUP_ROOT" || -L "$QUARANTINE_ROOT" ]]; then
  printf 'Backup and quarantine roots must not be symbolic links.\n' >&2
  exit 65
fi
chmod 0750 "$BACKUP_ROOT" "$QUARANTINE_ROOT"
touch "$event_log"
chmod 0640 "$event_log"
log_ready=1

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  json_log "warning" "backup_skipped" "another run holds ${LOCK_FILE}"
  exit 75
fi

mapfile -t containers < <(
  docker ps \
    --filter "label=${CONTAINER_LABEL}" \
    --filter "status=running" \
    --format '{{.ID}}'
)
if [[ "${#containers[@]}" -ne 1 ]]; then
  json_log "error" "container_selection_failed" "running_matches=${#containers[@]}"
  exit 69
fi
readonly container_id="${containers[0]}"

docker exec "$container_id" /surreal is-ready --endpoint "$ENDPOINT" >/dev/null

readonly base_name="${NAMESPACE}-${DATABASE}-${timestamp}"
readonly final_path="${BACKUP_ROOT}/${base_name}.surql"
readonly manifest_path="${BACKUP_ROOT}/${base_name}.sha256"
partial_path="${BACKUP_ROOT}/.${base_name}.surql.partial"
manifest_partial="${BACKUP_ROOT}/.${base_name}.sha256.partial"

if [[ -e "$final_path" || -e "$manifest_path" || -e "$partial_path" || -e "$manifest_partial" ]]; then
  json_log "error" "name_collision" "artifact=${base_name}"
  exit 73
fi

# Authentication comes only from SURREAL_USER/SURREAL_PASS inherited by the
# process inside the container. Secrets are never copied into arguments.
docker exec -i "$container_id" /surreal export \
  --log none \
  --endpoint "$ENDPOINT" \
  --auth-level root \
  --namespace "$NAMESPACE" \
  --database "$DATABASE" \
  - >"$partial_path"

if [[ ! -s "$partial_path" ]]; then
  json_log "error" "empty_export" "artifact=${base_name}"
  exit 74
fi

chmod 0440 "$partial_path"
readonly digest="$(sha256sum "$partial_path" | awk '{print $1}')"
readonly byte_count="$(stat -c '%s' "$partial_path")"
printf '%s  %s\n' "$digest" "${base_name}.surql" >"$manifest_partial"
chmod 0440 "$manifest_partial"

mv -- "$partial_path" "$final_path"
partial_path=""
mv -- "$manifest_partial" "$manifest_path"
manifest_partial=""
completed=1
json_log "info" "backup_completed" "artifact=${base_name}.surql; bytes=${byte_count}; sha256=${digest}"

# Retention never deletes. Every expired complete export and its checksum are
# moved together into a unique, operator-reviewable quarantine directory.
mapfile -d '' -t expired < <(
  find "$BACKUP_ROOT" -maxdepth 1 -type f \
    -name 'consignatio-intake-*.surql' \
    -mtime "+${RETENTION_DAYS}" -print0
)
if [[ "${#expired[@]}" -gt 0 ]]; then
  readonly retention_dir="${QUARANTINE_ROOT}/expired-${timestamp}"
  mkdir -p -- "$retention_dir"
  chmod 0750 "$retention_dir"
  moved=0
  for export_path in "${expired[@]}"; do
    export_name="$(basename -- "$export_path")"
    checksum_path="${export_path%.surql}.sha256"
    if [[ -e "$retention_dir/$export_name" ]]; then
      json_log "error" "retention_collision" "artifact=${export_name}"
      exit 73
    fi
    if [[ -f "$checksum_path" ]]; then
      checksum_name="$(basename -- "$checksum_path")"
      if [[ -e "$retention_dir/$checksum_name" ]]; then
        json_log "error" "retention_collision" "artifact=${checksum_name}"
        exit 73
      fi
    fi
    mv -- "$export_path" "$retention_dir/"
    if [[ -f "$checksum_path" ]]; then
      mv -- "$checksum_path" "$retention_dir/"
    fi
    moved=$((moved + 1))
  done
  json_log "info" "retention_quarantined" "exports=${moved}; destination=${retention_dir}"
fi

printf 'Created %s (%s bytes, SHA-256 %s)\n' "$final_path" "$byte_count" "$digest"
