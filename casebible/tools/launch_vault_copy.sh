#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 · 2026-09-15 08:45 EDT (session propria-79)
# Materialize vault merge plan v6 on B2 (run ON ovh-files). Owner 2026-09-15 08:31: "do all the moves up till now";
# 04:55: "new dir so nothing is deleted or overwritten make a copy".
# Server-side copies b2:salem-data/<canonical_key> -> b2:salem-data/consignatio/vault/v1/<merged path>, Immutable
# (never overwrite), nothing deleted. B2 credentials come from the same EnvironmentFile as launch_graded_transfer.sh.
# Usage: launch_vault_copy.sh test     # 100 objects, waits, then verifies those 100 against a fresh listing
#        launch_vault_copy.sh full     # everything not yet in the ledger, detached systemd unit
#        launch_vault_copy.sh verify   # fresh lsjson of vault/v1/ vs the whole manifest
set -euo pipefail
MODE="${1:?usage: launch_vault_copy.sh test|full|verify}"
RUN=/data/consignatio/migrations/vault-consolidation-20260915
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
MANIFEST="$RUN/vault_copy_manifest_v6.csv"
LEDGER="$RUN/vault_copy_v6.ledger.sqlite"
DRIVER="$RUN/vault_copy_driver.py"
CONF=/opt/casebible/rclone.conf          # holds no b2 section; the b2 remote comes from $ENVF
UNIT=consignatio-vault-copy-v6-20260915
DEST=b2:salem-data/consignatio/vault/v1/
# 51 objects already under vault/v1/ before this copy (2026-09-12 pilot: casebible-sorted/… + one _system canary);
# not in the manifest, left untouched, excluded from "extra" in verify
BASELINE="$RUN/vault_v1.preexisting-20260915.txt"

test -s "$MANIFEST" || { echo "ABORT: manifest missing/empty: $MANIFEST"; exit 2; }
test -f "$ENVF" || { echo "ABORT: env file missing: $ENVF"; exit 2; }
test -f "$DRIVER" || { echo "ABORT: driver missing: $DRIVER"; exit 2; }

listing() {  # fresh listing of the vault prefix, credentials only inside the transient unit
  local out="$RUN/vault_v1.lsjson.$(date -u +%Y%m%dT%H%M%SZ).json"
  systemd-run --unit "$UNIT-list-$(date +%s)" --wait --pipe --quiet -p EnvironmentFile="$ENVF" \
    /usr/bin/rclone lsjson -R --files-only --no-mimetype --no-modtime --config "$CONF" "$DEST" > "$out"
  echo "$out"
}

busy_check() {
  if systemctl is-active --quiet "$UNIT"; then echo "ABORT: $UNIT already active"; exit 3; fi
  busy=$(pgrep -a -x rclone | grep -E " (copy|copyto|sync|move|moveto|rcd) " || true)
  if [ -n "$busy" ]; then echo "ABORT: another rclone job is running:"; echo "$busy"; exit 3; fi
}

case "$MODE" in
  test)
    busy_check
    systemctl reset-failed "$UNIT-test" 2>/dev/null || true
    systemd-run --unit "$UNIT-test" --wait --pipe --quiet -p MemoryMax=2G -p EnvironmentFile="$ENVF" \
      /usr/bin/python3 "$DRIVER" copy --manifest "$MANIFEST" --ledger "$LEDGER" --config "$CONF" \
        --rclone-log "$RUN/vault_copy_v6.rcd.log" --workers 16 --limit 100
    L=$(listing)
    /usr/bin/python3 "$DRIVER" verify --manifest "$MANIFEST" --listing "$L" --baseline "$BASELINE" --ledger "$LEDGER"
    ;;
  batch)
    # a bounded batch at production concurrency, to measure throughput before the full run (LIMIT, WORKERS env)
    busy_check
    systemctl reset-failed "$UNIT-batch" 2>/dev/null || true
    systemd-run --unit "$UNIT-batch" --wait --pipe --quiet -p MemoryMax=2G -p EnvironmentFile="$ENVF" \
      /usr/bin/python3 "$DRIVER" copy --manifest "$MANIFEST" --ledger "$LEDGER" --config "$CONF" \
        --rclone-log "$RUN/vault_copy_v6.rcd.log" --workers "${WORKERS:-64}" --limit "${LIMIT:-2000}"
    L=$(listing)
    /usr/bin/python3 "$DRIVER" verify --manifest "$MANIFEST" --listing "$L" --baseline "$BASELINE" --ledger "$LEDGER"
    ;;
  testbig)
    # the 100-object test only sees small files; B2 copies > 5 GB through copy_part, so prove the largest one too
    busy_check
    systemctl reset-failed "$UNIT-testbig" 2>/dev/null || true
    BIG="$RUN/vault_copy_manifest_v6.largest.csv"
    /usr/bin/python3 - "$MANIFEST" "$BIG" <<'PY'
import csv
import sys

src, out = sys.argv[1], sys.argv[2]
with open(src, newline="", encoding="utf-8") as fh:
    best = max(csv.DictReader(fh), key=lambda r: int(r["size"]))
with open(out, "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=["canonical_key", "dest_key", "size"])
    writer.writeheader()
    writer.writerow(best)
print("largest object:", best["size"], "bytes ->", best["dest_key"])
PY
    systemd-run --unit "$UNIT-testbig" --wait --pipe --quiet -p MemoryMax=2G -p EnvironmentFile="$ENVF" \
      /usr/bin/python3 "$DRIVER" copy --manifest "$BIG" --ledger "$LEDGER" --config "$CONF" \
        --rclone-log "$RUN/vault_copy_v6.rcd.log" --workers 1
    L=$(listing)
    /usr/bin/python3 "$DRIVER" verify --manifest "$MANIFEST" --listing "$L" --baseline "$BASELINE" --ledger "$LEDGER"
    ;;
  full)
    busy_check
    systemctl reset-failed "$UNIT" 2>/dev/null || true
    echo "launching $UNIT: $(($(wc -l < "$MANIFEST") - 1)) manifest rows -> $DEST"
    systemd-run --unit "$UNIT" -p MemoryMax="${MEMMAX:-4G}" -p Nice=10 -p EnvironmentFile="$ENVF" \
      /usr/bin/python3 "$DRIVER" copy --manifest "$MANIFEST" --ledger "$LEDGER" --config "$CONF" \
        --rclone-log "$RUN/vault_copy_v6.rcd.log" --workers "${WORKERS:-32}"
    sleep 10
    systemctl status "$UNIT" --no-pager -n 5 || true
    ;;
  verify)
    L=$(listing)
    /usr/bin/python3 "$DRIVER" verify --manifest "$MANIFEST" --listing "$L" --baseline "$BASELINE"
    ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac
