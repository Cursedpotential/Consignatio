#!/usr/bin/env bash
# Byline: Claude Code · Fable 5 · 2026-09-13
# Amended 2026-09-14 00:08 EDT (owner order): source the Google Drives DIRECTLY via rclone Drive remotes
# on the VPS — no openlist middleman. Verified: openlist-gateway runs transferred 0 files and reported
# "nothing to transfer"; the direct remote copied 8,717 files correctly and exposes full Drive API metadata.
# Remotes live in /data/consignatio/secrets/rclone-gdrive.conf (root-only, 0600).
# Usage: launch_gdrive_transfer.sh <salemnet|salem85>
set -euo pipefail
NAME="${1:?usage: launch_gdrive_transfer.sh <salemnet|salem85>}"
SRC="gd_${NAME}:"
RUN=/data/consignatio/migrations/gdrive-copy-20260913
LIST="$RUN/gdrive-$NAME.list"
GDCONF=/data/consignatio/secrets/rclone-gdrive.conf
B2ENV=/data/consignatio/secrets/rclone-b2-intake.env
UNIT="consignatio-gdrive-copy-$NAME-20260913"
DEST="b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/gdrive/$NAME"

test -s "$LIST" || { echo "ABORT: list missing/empty: $LIST"; exit 2; }
test -f "$GDCONF" || { echo "ABORT: gdrive config missing"; exit 2; }
test -f "$B2ENV" || { echo "ABORT: b2 env missing"; exit 2; }
if systemctl is-active --quiet "$UNIT"; then echo "ABORT: $UNIT already active"; exit 3; fi

echo "launching $UNIT: $(wc -l < "$LIST") files from $SRC (direct Drive API) -> $DEST"
systemd-run --unit "$UNIT" --collect \
  -p MemoryMax=1G -p Nice=10 -p EnvironmentFile="$B2ENV" \
  -p Environment="RCLONE_CONFIG=$GDCONF" \
  /usr/bin/rclone copy "$SRC" "$DEST" \
    --files-from-raw "$LIST" --no-traverse --immutable --metadata \
    --transfers 4 --checkers 4 --drive-chunk-size 64M \
    --retries 3 --low-level-retries 10 --stats 60s --stats-one-line --log-level INFO \
    --log-file "$RUN/$NAME.log"
sleep 5
systemctl status "$UNIT" --no-pager -n 2 || true
