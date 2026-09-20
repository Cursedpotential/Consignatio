#!/usr/bin/env bash
# Byline: Claude Code · Fable 5.1 · 2026-09-14
# Copy one OneDrive scope's hash-verified copy list to B2. Runs ON the VPS (ovh-files), svr-to-svr.
#
# Input is lists/<scope>.copy.list from onedrive_hash_join.py = files new-by-size ∪ files whose md5
# matched nothing in the catalog. Everything else already has a good copy (bytes once on B2; the
# occurrence is recorded from lists/<scope>.matched.tsv, not re-uploaded). Destination mirrors the
# true OneDrive path under source-buckets/onedrive/, same convention as gdrive/<acct>/<path>.
# OneDrive has no SHA1; rclone streams to B2 with hex_digits_at_end, so nothing is spooled.
#
# Usage: launch_onedrive_copy.sh <scope>          dry run: prints count/bytes, moves nothing
#        launch_onedrive_copy.sh <scope> --go     transient systemd unit doing the real copy
set -euo pipefail
SCOPE="${1:?scope: AI_Space|Case_Bible|Documents_CSV|Documents_Disk_Drill}"; GO="${2:-}"
RUN=/data/consignatio/migrations/onedrive-copy-20260914
CONF=/opt/casebible/rclone.conf
ENV=/data/consignatio/secrets/rclone-b2-intake.env
declare -A ROOT=( [AI_Space]="AI Space" [Documents_CSV]="Documents/CSV" [Documents_Disk_Drill]="Documents/Disk Drill" [Case_Bible]="Case Bible" )
SRC="od:${ROOT[$SCOPE]}"
DST="b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/onedrive/${ROOT[$SCOPE]}"
LIST="$RUN/lists/$SCOPE.copy.list"
UNIT="consignatio-onedrive-copy-$SCOPE-20260914"
[ -s "$LIST" ] || { echo "$SCOPE: copy list missing or empty ($LIST) — run onedrive_hash_join.py first"; exit 1; }
[ -s "$RUN/lists/$SCOPE.join-summary.txt" ] && cat "$RUN/lists/$SCOPE.join-summary.txt"
set -a; . "$ENV"; set +a
COMMON=(--config "$CONF" --files-from-raw "$LIST" --no-traverse --immutable --metadata
        --transfers 4 --checkers 4 --tpslimit 8 --b2-upload-concurrency 2 --retries 3 --low-level-retries 10)
if [ "$GO" != "--go" ]; then
  echo "DRY RUN  $SRC  ->  $DST  ($(wc -l < "$LIST") listed files)"
  rclone copy "$SRC" "$DST" "${COMMON[@]}" --dry-run --stats-one-line --stats 0 -v 2>&1 | grep -E 'Skipped copy|NOTICE|ERROR|Transferred|Checks|Errors' | tail -n 12
  echo "re-run with --go to launch $UNIT"
  exit 0
fi
if systemctl is-active --quiet "$UNIT"; then echo "already running: $UNIT"; exit 0; fi
SETENV=(); while read -r k; do SETENV+=("--setenv=$k"); done < <(grep -o '^RCLONE_CONFIG_B2_[A-Z_]*' "$ENV")
# No --collect (an OOM-killed unit erased by --collect reads as "success" afterwards — hit 2026-09-14); cap sized
# for transfers × --b2-upload-concurrency × 96 MiB chunks. Verification is `rclone check --download`, never Result.
systemctl reset-failed "$UNIT" 2>/dev/null || true
systemd-run --unit "$UNIT" -p MemoryMax=3G --working-directory "$RUN" "${SETENV[@]}" \
  /usr/bin/rclone copy "$SRC" "$DST" "${COMMON[@]}" \
  --stats 60s --stats-one-line --log-level INFO --log-file "$RUN/logs/copy-$SCOPE.log"
echo "launched $UNIT — log $RUN/logs/copy-$SCOPE.log"
