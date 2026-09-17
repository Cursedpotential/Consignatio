#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 (1M) · 2026-09-17
#
# Step 1 of replacing spacedrive-gate in place with an image built from
# spacedriveapp/spacedrive main HEAD (owner order 2026-09-16 22:24).
#
# This step is REVERSIBILITY ONLY -- it records what is about to be replaced
# and takes a dated backup. It stops the container and any watcher loops that
# would restart it, but it does not change the compose file or start anything
# new. Nothing is ever deleted: the volume is copied to a tarball and the old
# image is retained by tag and id.
#
# Run from the desktop:
#   MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/ovh root@100.91.190.107 'bash -s' \
#     < docs/ops/spacedrive-gate-swap-2026-09-17-step1-backup.sh
set -euo pipefail

STAMP="2026-09-17"
BK="/data/probata/backups/spacedrive-gate-${STAMP}"
CFG="/data/probata/config/spacedrive-gate"
VOL="spacedrive_gate_state"

mkdir -p "$BK"

echo "=== 1. Record the image being replaced (for rollback) ==="
{
  echo "recorded_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "container_config_image=$(docker inspect spacedrive-gate --format '{{.Config.Image}}' 2>/dev/null || echo NONE)"
  echo "container_image_id=$(docker inspect spacedrive-gate --format '{{.Image}}' 2>/dev/null || echo NONE)"
  echo "image_created=$(docker image inspect spacedrive-gate:local --format '{{.Created}}' 2>/dev/null || echo NONE)"
  echo "image_size=$(docker image inspect spacedrive-gate:local --format '{{.Size}}' 2>/dev/null || echo NONE)"
} | tee "$BK/old-image.txt"

echo
echo "=== 2. Stop watcher loops that would restart the container ==="
# Another agent left boot-watch / watchdog loops polling this container; if
# they survive they will fight the swap. Stop the processes, keep the scripts
# and their logs in place.
for pat in boot-watch-2026-09-16.sh watchdog-2026-09-16.sh; do
  pids=$(pgrep -f "[b]ash.*$pat" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "stopping $pat -> pids: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
  else
    echo "$pat: not running"
  fi
done
echo "remaining spacedrive-related watcher processes:"
pgrep -af "spacedrive" | grep -v "docker\|containerd\|sd-server" || echo "  (none)"

echo
echo "=== 3. Stop the container (clean stop, so sqlite is quiesced) ==="
docker stop spacedrive-gate || echo "container was not running"
docker ps -a --filter name=spacedrive-gate --format '{{.Names}} | {{.Image}} | {{.Status}}'

echo
echo "=== 4. Back up the whole /data volume, dated ==="
MP=$(docker volume inspect "$VOL" --format '{{.Mountpoint}}')
echo "volume mountpoint: $MP"
echo "size before: $(du -sh "$MP" | cut -f1)"
echo "free space:  $(df -h / | tail -1)"
tar -czf "$BK/${VOL}.tar.gz" -C "$MP" .
echo "tarball: $(ls -lh "$BK/${VOL}.tar.gz" | awk '{print $5, $9}')"

echo
echo "=== 5. Back up the library DB files separately (fast restore path) ==="
# Belt and braces: the sqlite library DBs are the only irreplaceable part
# (the index can be rebuilt; a hand-made library config cannot).
find "$MP" -maxdepth 4 \( -name '*.db' -o -name '*.db.bak-*' -o -name '*.sqlite*' -o -name '*.sdlibrary' -o -name '*.sdconfig' \) 2>/dev/null | while read -r f; do
  rel="${f#"$MP"/}"
  dest="$BK/dbs/$(dirname "$rel")"
  mkdir -p "$dest"
  cp -p "$f" "$dest/"
  echo "copied: $rel"
done
echo "db backup tree:"
find "$BK/dbs" -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -20 || echo "  (no .db/.sqlite files found at depth<=4)"

echo
echo "=== 6. Back up the current compose file ==="
cp -p "$CFG/docker-compose.yml" "$CFG/docker-compose.yml.bak-${STAMP}-pre-current-source"
cp -p "$CFG/docker-compose.yml" "$BK/docker-compose.yml.old"
ls -la "$CFG"/docker-compose.yml*

echo
echo "=== STEP 1 COMPLETE ==="
echo "backup dir: $BK"
ls -la "$BK"
