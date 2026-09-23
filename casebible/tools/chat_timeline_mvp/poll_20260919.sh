#!/bin/bash
# Byline: Claude Code · Opus 5 (1M context) · 2026-09-18
# Keep the Surreal timeline graph current while the extraction agent adds Weaviate objects.
# Each pass: spool only new/changed objects, refresh the catalog source map, upsert, relink.
# Everything is idempotent (ids derive from dedup_key), so a pass that finds nothing is a no-op.
# Launch detached on the VPS: setsid nohup /root/stl/poll.sh > poll.log 2>&1 < /dev/null &
set -eu
APP=${APP:-/data/probata/config/timeline-mvp/app2}
VOL=${VOL:-/data/probata/volumes/timeline-mvp}
INTERVAL=${INTERVAL:-600}
NEW_STATE=${NEW_STATE:-$VOL/poll_state_20260919.json}

while true; do
  echo "=== pass $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  before=$(wc -l < "$VOL/chat_events_20260919.jsonl" || echo 0)
  python3 "$APP/weaviate_fetch_20260919.py" || echo "fetch failed; will retry next pass"
  after=$(wc -l < "$VOL/chat_events_20260919.jsonl" || echo 0)
  if [ "$after" -gt "$before" ]; then
    echo "spool grew $before -> $after; reloading"
    python3 "$APP/resolve_sources_20260919.py" || true
    # a fresh state file makes the loader walk the whole spool again; every write is an upsert
    STATE=$NEW_STATE
    export STATE
    : > "$NEW_STATE"
    echo '{"done": {}, "events": 0}' > "$NEW_STATE"
    /root/stl/run_load.sh || echo "load stopped (exit $?)"
    echo '[]' > "$VOL/next_state_20260919.json"   # relink every conversation; IGNORE makes it a no-op where unchanged
    python3 "$APP/build_next_20260919.py" || echo "next-link stopped (exit $?)"
  else
    echo "no new objects"
  fi
  sleep "$INTERVAL"
done
