#!/usr/bin/env bash
# Byline: Claude Code · Opus 5 (1M) · 2026-09-17
#
# Step 2 of replacing spacedrive-gate in place: pull the current-source image,
# install the new compose file, start it. Run step1 (backup) FIRST -- this
# script refuses to run if step1's backup tarball is missing.
#
# The new compose file is uploaded separately (it is tracked as
# docs/ops/spacedrive-gate-docker-compose-2026-09-17-current-source-image.yml)
# to /data/probata/config/spacedrive-gate/docker-compose.yml.new before this
# runs; this script validates it, swaps it in, and brings the stack up.
#
#   MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/ovh root@100.91.190.107 'bash -s' \
#     < docs/ops/spacedrive-gate-swap-2026-09-17-step2-deploy.sh
set -euo pipefail

STAMP="2026-09-17"
BK="/data/probata/backups/spacedrive-gate-${STAMP}"
CFG="/data/probata/config/spacedrive-gate"
IMAGE="ghcr.io/cursedpotential/spacedrive-server:main-6dfeccf"

echo "=== 0. Refuse to proceed without step1's backup ==="
test -s "$BK/spacedrive_gate_state.tar.gz" \
  || { echo "FATAL: $BK/spacedrive_gate_state.tar.gz missing or empty -- run step1 first"; exit 1; }
test -s "$BK/old-image.txt" \
  || { echo "FATAL: $BK/old-image.txt missing -- run step1 first"; exit 1; }
echo "backup present: $(ls -lh "$BK/spacedrive_gate_state.tar.gz" | awk '{print $5}')"
echo "rollback record:"; cat "$BK/old-image.txt"

echo
echo "=== 1. Pull the current-source image ==="
docker pull "$IMAGE"
echo
echo "image identity (upstream commit is stamped in the labels):"
docker image inspect "$IMAGE" --format \
  'digest: {{index .RepoDigests 0}}
created: {{.Created}}
size:    {{.Size}}
upstream revision: {{index .Config.Labels "org.opencontainers.image.revision"}}
upstream source:   {{index .Config.Labels "org.opencontainers.image.source"}}
entrypoint: {{json .Config.Entrypoint}} cmd: {{json .Config.Cmd}}
user: {{.Config.User}}'

echo
echo "=== 2. Does the runtime image have curl? (decides the healthcheck) ==="
# Upstream's runtime stage installs only libssl3/ca-certificates/ffmpeg
# libs/libheif1 -- no curl, no wget, and /bin/sh is dash (no /dev/tcp). The
# new compose therefore has NO in-container healthcheck and health is checked
# from the host. This prints the evidence rather than assuming it.
docker run --rm --entrypoint sh "$IMAGE" -c \
  'for b in curl wget nc python3; do printf "%s: " "$b"; command -v $b || echo MISSING; done' \
  || echo "(probe failed; assuming no curl)"

echo
echo "=== 3. Install the new compose file ==="
test -s "$CFG/docker-compose.yml.new" \
  || { echo "FATAL: $CFG/docker-compose.yml.new not uploaded"; exit 1; }
python3 -c "import yaml,sys; d=yaml.safe_load(open('$CFG/docker-compose.yml.new')); \
svc=d['services']['spacedrive-gate']; print('image:',svc['image']); print('ports:',svc['ports']); \
print('volumes:',svc['volumes']); print('env_file:',svc['env_file']); \
assert svc['image']=='$IMAGE', 'image mismatch'; print('compose YAML valid')"
test -f "$CFG/docker-compose.yml.bak-${STAMP}-pre-current-source" \
  || cp -p "$CFG/docker-compose.yml" "$CFG/docker-compose.yml.bak-${STAMP}-pre-current-source"
cp "$CFG/docker-compose.yml.new" "$CFG/docker-compose.yml"
ls -la "$CFG"/docker-compose.yml*

echo
echo "=== 4. Recreate the container on the new image ==="
cd "$CFG"
# `down` (not just stop) so the container is recreated against the new image
# and the old container definition does not linger. The volume is `external:
# true` in the new compose, so `down` cannot take it with it.
docker compose down --remove-orphans || true
docker compose up -d
sleep 5
docker ps -a --filter name=spacedrive-gate --format '{{.Names}} | {{.Image}} | {{.Status}} | {{.Ports}}'

echo
echo "=== 5. First 80 lines of the new boot (since this start only) ==="
STARTED=$(docker inspect --format '{{.State.StartedAt}}' spacedrive-gate)
echo "container StartedAt: $STARTED"
docker logs --since "$STARTED" spacedrive-gate 2>&1 | head -80 || true

echo
echo "=== STEP 2 COMPLETE -- now run step3 verify ==="
echo "rollback if needed:"
echo "  cp $CFG/docker-compose.yml.bak-${STAMP}-pre-current-source $CFG/docker-compose.yml"
echo "  cd $CFG && docker compose up -d --force-recreate"
