#!/usr/bin/env bash
# cv2 (used by docling's table-structure model) needs libGL + glib at runtime.
# Byline: Claude Code · Sonnet 5 · 2026-09-14
set -euo pipefail
docker exec opendataloader-spike bash -c '
  apt-get install -y -qq libgl1 libglib2.0-0 >/tmp/apt3.log 2>&1
  echo "installed libgl1 libglib2.0-0"
'
