#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 (1M) · 2026-09-17
#
# Step 2b: move the frozen 2024 library aside so main-HEAD can initialize its
# own, then create a fresh library.
#
# WHY this is needed (observed, not assumed -- from the new image's first boot
# log at 2026-09-17T02:51:48Z):
#     Entry is a library directory: "/data/libraries/<uuid>.sdlibrary"
#     Failed to load library from "/data/libraries/<uuid>.sdlibrary":
#         IO error: Not a directory (os error 20)
#     Loaded 0 libraries
#     ERROR Found 1 library directories but none loaded successfully
# main-HEAD's library manager expects `<uuid>.sdlibrary` to be a DIRECTORY
# holding the library; the frozen 2024 build wrote it as a 101-byte FILE
# alongside `<uuid>.db`. That is a layout change, not a corrupt library --
# the 2024 index is not migratable by this server, and the owner's own
# finding (frozen build re-walks every location over WebDAV on each cold
# boot, 22+ min and never finishing) means that index had no value to carry
# forward anyway.
#
# NOTHING IS DELETED. The 2024 library files are MOVED into
# /data/libraries.frozen2024-2026-09-17/ inside the same volume, and a full
# dated tarball already exists from step1.
#
#   MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/ovh root@100.91.190.107 'bash -s' \
#     < docs/ops/spacedrive-gate-swap-2026-09-17-step2b-library-reset.sh
set -euo pipefail

STAMP="2026-09-17"
BK="/data/probata/backups/spacedrive-gate-${STAMP}"
CFG="/data/probata/config/spacedrive-gate"

echo "=== 0. Refuse to proceed without step1's backup ==="
test -s "$BK/spacedrive_gate_state.tar.gz" \
  || { echo "FATAL: step1 backup missing"; exit 1; }
echo "backup present: $(ls -lh "$BK/spacedrive_gate_state.tar.gz" | awk '{print $5}')"

MP=$(docker volume inspect spacedrive_gate_state --format '{{.Mountpoint}}')
echo "volume: $MP"

echo
echo "=== 1. Stop the container so the library dir is quiescent ==="
docker stop spacedrive-gate

echo
echo "=== 2. Move the 2024 library aside (move, never delete) ==="
OLD="$MP/libraries.frozen2024-${STAMP}"
mkdir -p "$OLD"
shopt -s nullglob dotglob
moved=0
for f in "$MP"/libraries/*; do
  mv "$f" "$OLD"/
  echo "moved aside: $(basename "$f")"
  moved=$((moved + 1))
done
shopt -u nullglob dotglob
echo "moved $moved entries"
echo "libraries/ now:"; ls -la "$MP/libraries" || true
echo "frozen2024 holdings:"; ls -la "$OLD" | head -20
echo "byte total preserved: $(du -sh "$OLD" | cut -f1)"

echo
echo "=== 3. Start the container again ==="
cd "$CFG"
docker compose up -d
STARTED=$(docker inspect --format '{{.State.StartedAt}}' spacedrive-gate)
echo "StartedAt: $STARTED"

echo
echo "=== 4. Boot log for THIS start only (library lines) ==="
# --since the container's own StartedAt, so pre-restart lines cannot fake
# a success or failure.
sleep 12
docker logs --since "$STARTED" spacedrive-gate 2>&1 \
  | grep -iE "librar|listening|Web UI|RPC endpoint|error|panic" | head -40 || true

echo
echo "=== STEP 2b COMPLETE ==="
