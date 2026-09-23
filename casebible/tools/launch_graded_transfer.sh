#!/usr/bin/env bash
# Byline: Claude Code · Fable 5 · 2026-09-13
# Launch one graded R2->B2 tranche as a transient systemd unit on the VPS (run ON the VPS).
# Usage: launch_graded_transfer.sh <bucket>   e.g. casebible-quarantine
# Server-side copy, immutable destination, metadata preserved, bounded memory, survives sessions.
# Concurrency: TRANSFERS/CHECKERS env (default 8/8 since 2026-09-14 — at 2/4 the raw tranche ran
# ~3 files/s, per-file-overhead bound, 0 errors; --immutable makes a restart at higher concurrency safe).
set -euo pipefail
BUCKET="${1:?usage: launch_graded_transfer.sh <bucket> [list]}"
RUN=/data/consignatio/migrations/r2-to-b2/graded-copy-20260913
LIST="${2:-$RUN/graded-$BUCKET.list}"   # e.g. a tranche_verify.sh *.missing.list to resume only what is absent
ENVF=/data/consignatio/secrets/rclone-b2-intake.env
UNIT="consignatio-graded-copy-$BUCKET-20260913"
DEST="b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/$BUCKET"

test -s "$LIST" || { echo "ABORT: list missing/empty: $LIST"; exit 2; }
test -f "$ENVF" || { echo "ABORT: env file missing: $ENVF"; exit 2; }
if systemctl is-active --quiet "$UNIT"; then echo "ABORT: $UNIT already active"; exit 3; fi
# 2026-09-14: the 8/8 run at MemoryMax=1G was OOM-killed (SIGKILL) after 3,401 files and `--collect` then
# erased the failed unit, so every later status query returned the default "success". Units now stay
# loaded after failure (inspect with `systemctl status`), get reset here before a relaunch, and get a cap
# sized for rclone's real footprint: transfers × --b2-upload-concurrency × chunk (8 × 2 × 96 MiB ≈ 1.5 GiB).
systemctl reset-failed "$UNIT" 2>/dev/null || true
busy=$(pgrep -a -x rclone | grep -E " (copy|copyto|sync|move|moveto) " | grep -E "b2:|salem-data" || true)
if [ -n "$busy" ]; then echo "ABORT: another B2 copy is running:"; echo "$busy"; exit 3; fi

echo "launching $UNIT: $(wc -l < "$LIST") files from r2:$BUCKET -> $DEST"
systemd-run --unit "$UNIT" \
  -p MemoryMax="${MEMMAX:-4G}" -p Nice=10 -p EnvironmentFile="$ENVF" \
  /usr/bin/rclone copy "r2:$BUCKET" "$DEST" \
    --files-from-raw "$LIST" --no-traverse --immutable --metadata \
    --transfers "${TRANSFERS:-8}" --checkers "${CHECKERS:-8}" --b2-upload-concurrency 2 \
    --retries 3 --low-level-retries 10 \
    --stats 60s --stats-one-line --log-level INFO \
    --log-file "$RUN/$BUCKET.log"
sleep 5
systemctl status "$UNIT" --no-pager -n 3 || true
