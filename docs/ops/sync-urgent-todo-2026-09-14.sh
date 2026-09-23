#!/usr/bin/env bash
# Byline: Claude Code · Sonnet 5 · 2026-09-14
#
# Pushes the desktop URGENT-TODO.md to the progress-board host on ovh-app so
# its /api/todo-feed endpoint (and the "Open to-dos" Homepage widget) can read
# open `- [ ]` items. There is no automatic desktop<->VPS sync of this file;
# run this manually (or from a supervisor step) after editing
# docs/URGENT-TODO.md so the portal widget reflects the latest list.
#
# Usage:
#   bash docs/ops/sync-urgent-todo-2026-09-14.sh
#
# Safe to re-run; it only overwrites the synced COPY on the VPS
# (/data/dashboards/progress-board/data/URGENT-TODO.md), never the source.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR/../URGENT-TODO.md"
HOST="root@100.72.169.40"
KEY="$HOME/.ssh/ovh"
DEST_DIR="/data/dashboards/progress-board/data"
DEST="$DEST_DIR/URGENT-TODO.md"

if [ ! -f "$SOURCE" ]; then
  echo "sync-urgent-todo: source not found: $SOURCE" >&2
  exit 1
fi

MSYS_NO_PATHCONV=1 ssh -i "$KEY" "$HOST" "mkdir -p '$DEST_DIR'"
MSYS_NO_PATHCONV=1 scp -i "$KEY" "$SOURCE" "$HOST:$DEST.tmp"
MSYS_NO_PATHCONV=1 ssh -i "$KEY" "$HOST" "mv '$DEST.tmp' '$DEST' && chmod 0644 '$DEST' && wc -l '$DEST'"

echo "sync-urgent-todo: synced $SOURCE -> $HOST:$DEST"
