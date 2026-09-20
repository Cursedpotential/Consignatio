#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-17 08:25 EDT
# Materialize the recovery-dump sorting manifest raw_duck.recovery_manifest_20260917 on B2 (run ON ovh-files).
# Owner 2026-09-16 22:43 "extract into master directories based on file type ... check file integrity";
# 2026-09-17 08:06 "yes" (Software Fragments folder); 08:17 "sure" (go on the copy).
# Server-side copies b2:salem-data/<src_key> -> b2:salem-data/<dest_key> through vault_copy_driver.py
# (rclone rcd operations/copyfile, Immutable: an existing different destination is refused, never overwritten).
# NOTHING is deleted: the recup_dir originals stay until a separate owner-approved retire step.
# B2 credentials come only from the EnvironmentFile inside transient systemd units.
# Usage: recovery_integrity_04_materialize.sh export   # manifest CSV, baseline keys, listing filter from the catalog
#        recovery_integrity_04_materialize.sh test     # 100 objects, then verify those 100 against a fresh listing
#        recovery_integrity_04_materialize.sh full     # everything not yet in the ledger, detached systemd unit
#        recovery_integrity_04_materialize.sh verify   # fresh listing of the destination folders vs the whole manifest
set -euo pipefail
MODE="${1:?usage: recovery_integrity_04_materialize.sh export|test|full|verify}"
RUN=/data/consignatio/migrations/recovery-extract-20260917
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
DRIVER=/data/consignatio/migrations/vault-consolidation-20260915/vault_copy_driver.py
CONF=/opt/casebible/rclone.conf          # holds no b2 section; the b2 remote comes from $ENVF
PG=cd840572ae7b
MANIFEST="$RUN/recovery_manifest_20260917.csv"
BASELINE="$RUN/dest_folders.preexisting.txt"
FILTER="$RUN/dest_folders.filter"
LEDGER="$RUN/recovery_copy.ledger.sqlite"
UNIT=consignatio-recovery-extract-20260917
PREFIX=consignatio/vault/v1/
DEST="b2:salem-data/$PREFIX"
mkdir -p "$RUN"

psql_out() { docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 -At -c "$1"; }

listing() {  # fresh listing of only the destination folders under vault/v1/
  local out="$RUN/dest_folders.lsjson.$(date -u +%Y%m%dT%H%M%SZ).json"
  systemd-run --unit "$UNIT-list-$(date +%s)" --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
    /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --config "$CONF" \
      --filter-from "$FILTER" "$DEST" > "$out"
  echo "$out"
}

busy_check() {
  if systemctl is-active --quiet "$UNIT"; then echo "ABORT: $UNIT already active"; exit 3; fi
  busy=$(pgrep -a -x rclone | grep -E " (copy|copyto|sync|move|moveto|rcd|delete|deletefile|purge) " || true)
  if [ -n "$busy" ]; then echo "ABORT: another rclone job is running:"; echo "$busy"; exit 3; fi
}

need_export() {
  for f in "$MANIFEST" "$BASELINE" "$FILTER"; do test -s "$f" || { echo "ABORT: run export first ($f missing)"; exit 2; }; done
  test -f "$ENVF" || { echo "ABORT: env file missing: $ENVF"; exit 2; }
  test -f "$DRIVER" || { echo "ABORT: driver missing: $DRIVER"; exit 2; }
}

case "$MODE" in
  export)
    docker exec -i "$PG" psql -U postgres -d casebible -v ON_ERROR_STOP=1 -c \
      "\\copy (SELECT src_key AS canonical_key, dest_key, size FROM raw_duck.recovery_manifest_20260917 WHERE action = 'COPY' ORDER BY dest_key) TO STDOUT WITH (FORMAT csv, HEADER true)" \
      > "$MANIFEST"
    # destination folders = first path segment under vault/v1/ for type dirs and Software Fragments/, and the
    # review-and-control root; rclone filter lines anchored at the listing root
    psql_out "SELECT DISTINCT split_part(substr(dest_key, length('$PREFIX')+1), '/', 1) FROM raw_duck.recovery_manifest_20260917 ORDER BY 1" \
      | awk 'BEGIN{print "# destination folders of recovery_manifest_20260917"} {gsub(/[\[\]\{\}\*\?]/, "\\\\&"); print "+ /" $0 "/**"} END{print "- **"}' > "$FILTER"
    # objects already present in those folders (from the current catalog listing): not ours, never touched
    psql_out "SELECT v.key FROM raw_duck.vault_objects_20260916_r4 v WHERE split_part(substr(v.key, length('$PREFIX')+1), '/', 1) IN (SELECT DISTINCT split_part(substr(dest_key, length('$PREFIX')+1), '/', 1) FROM raw_duck.recovery_manifest_20260917) ORDER BY 1" \
      > "$BASELINE"
    echo "manifest rows: $(($(wc -l < "$MANIFEST") - 1))  bytes: $(tail -n +2 "$MANIFEST" | awk -F, '{s+=$NF} END{print s}')"
    echo "destination folders: $(grep -c '^+ ' "$FILTER")  preexisting objects in them: $(wc -l < "$BASELINE")"
    ;;
  test)
    need_export; busy_check
    systemctl reset-failed "$UNIT-test" 2>/dev/null || true
    systemd-run --unit "$UNIT-test" --wait --pipe --quiet -p MemoryMax=2G -p EnvironmentFile="$ENVF" \
      /usr/bin/python3 "$DRIVER" copy --manifest "$MANIFEST" --ledger "$LEDGER" --config "$CONF" \
        --rclone-log "$RUN/recovery_copy.rcd.log" --workers 16 --limit 100
    L=$(listing)
    /usr/bin/python3 "$DRIVER" verify --manifest "$MANIFEST" --listing "$L" --prefix "$PREFIX" --baseline "$BASELINE" --ledger "$LEDGER"
    ;;
  full)
    need_export; busy_check
    systemctl reset-failed "$UNIT" 2>/dev/null || true
    echo "launching $UNIT: $(($(wc -l < "$MANIFEST") - 1)) manifest rows -> $DEST"
    systemd-run --unit "$UNIT" -p MemoryMax="${MEMMAX:-4G}" -p Nice=10 -p EnvironmentFile="$ENVF" \
      /usr/bin/python3 "$DRIVER" copy --manifest "$MANIFEST" --ledger "$LEDGER" --config "$CONF" \
        --rclone-log "$RUN/recovery_copy.rcd.log" --workers "${WORKERS:-32}"
    sleep 10
    systemctl status "$UNIT" --no-pager -n 5 || true
    ;;
  verify)
    need_export
    L=$(listing)
    /usr/bin/python3 "$DRIVER" verify --manifest "$MANIFEST" --listing "$L" --prefix "$PREFIX" --baseline "$BASELINE"
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
