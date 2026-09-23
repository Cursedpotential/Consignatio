#!/bin/sh
# Byline: Claude Code · Sonnet 5 · 2026-09-16
# Watchdog for spacedrive-gate during the B2-as-one-location index run.
# Polls docker stats every 10s; if container memory exceeds 85% of the
# 8g mem_limit (i.e. > 6.8 GiB), logs a WARN and restarts the container
# as the documented last resort (no rspc job-cancel procedure was found
# in the served client bundle within this task's time budget, and
# generate_preview_media/sync_preview_media are already set to 0 for the
# b2 location, so a thumbnail-driven spike is not expected).
# Runs detached via nohup on ovh-files itself, never as a child of an
# agent's shell (per standing rule: long jobs die with the agent's shell
# otherwise).
LIMIT_BYTES=8589934592
THRESH_BYTES=$((LIMIT_BYTES * 85 / 100))
LOG=/data/probata/config/spacedrive-gate/watchdog-2026-09-16.log
echo "$(date -Is) watchdog started, limit=8g threshold_bytes=$THRESH_BYTES" >> "$LOG"
END_EPOCH=$(( $(date +%s) + 3600 ))
while [ "$(date +%s)" -lt "$END_EPOCH" ]; do
  STATS=$(docker stats --no-stream --format '{{.MemUsage}}|{{.CPUPerc}}' spacedrive-gate 2>/dev/null)
  MEMPART=$(echo "$STATS" | cut -d'|' -f1 | cut -d'/' -f1 | tr -d ' ')
  CPU=$(echo "$STATS" | cut -d'|' -f2)
  # Convert MEMPART (e.g. 512MiB, 1.2GiB) to bytes via python (available on host)
  BYTES=$(python3 -c "
s='$MEMPART'
import re
m=re.match(r'([0-9.]+)([A-Za-z]+)', s)
if not m:
    print(0)
else:
    val=float(m.group(1)); unit=m.group(2)
    mult={'B':1,'KiB':1024,'MiB':1024**2,'GiB':1024**3}.get(unit,1)
    print(int(val*mult))
" 2>/dev/null)
  LOCROWS=$(sqlite3 -readonly /var/lib/docker/volumes/spacedrive_gate_state/_data/libraries/891f127d-e9de-4330-bd3c-37f8fcc7aba4.db "SELECT count(*) FROM file_path WHERE location_id=6;" 2>/dev/null)
  echo "$(date -Is) mem=$MEMPART bytes=$BYTES cpu=$CPU b2_rows=$LOCROWS" >> "$LOG"
  if [ -n "$BYTES" ] && [ "$BYTES" -gt "$THRESH_BYTES" ] 2>/dev/null; then
    echo "$(date -Is) WARN: memory $BYTES > threshold $THRESH_BYTES, restarting container" >> "$LOG"
    cd /data/probata/config/spacedrive-gate && docker compose restart spacedrive-gate >> "$LOG" 2>&1
    echo "$(date -Is) restart issued" >> "$LOG"
    sleep 30
  fi
  sleep 10
done
echo "$(date -Is) watchdog finished 60min window" >> "$LOG"
