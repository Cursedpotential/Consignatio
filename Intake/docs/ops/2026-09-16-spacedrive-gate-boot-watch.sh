#!/bin/sh
# Byline: Claude Code · Sonnet 5 · 2026-09-16
# Detached boot-progress watcher for spacedrive-gate after the 508,152-row catalog
# import for location 6. Polls every 15s for up to 50 minutes, logging health status,
# memory, and log-line count so a human/agent can check in without blocking on a
# single long-running foreground call. Runs via nohup on the VPS itself.
STARTED="2026-09-16T22:58:32.291606302Z"
LOG=/data/probata/config/spacedrive-gate/boot-watch-2026-09-16.log
: > "$LOG"
BASELINE=31
END=$(( $(date +%s) + 3000 ))
while [ "$(date +%s)" -lt "$END" ]; do
  LINES=$(docker logs --since "$STARTED" spacedrive-gate 2>&1 | wc -l)
  STATUS=$(docker inspect --format '{{.State.Health.Status}}' spacedrive-gate 2>/dev/null)
  MEM=$(docker stats --no-stream --format '{{.MemUsage}}' spacedrive-gate 2>/dev/null)
  echo "$(date -Is) loglines=$LINES health=$STATUS mem=$MEM" >> "$LOG"
  if [ "$STATUS" = "healthy" ]; then
    echo "$(date -Is) REACHED_HEALTHY" >> "$LOG"
    break
  fi
  if [ "$LINES" -gt "$BASELINE" ]; then
    echo "$(date -Is) NEW_LOG_LINES ($LINES)" >> "$LOG"
    docker logs --since "$STARTED" spacedrive-gate 2>&1 | tail -30 >> "$LOG"
  fi
  sleep 15
done
echo "$(date -Is) watch window ended" >> "$LOG"
