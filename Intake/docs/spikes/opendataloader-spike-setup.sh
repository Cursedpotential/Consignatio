#!/usr/bin/env bash
# Bounded live spike: OpenDataLoader PDF as an Intake extraction tool candidate.
# Runs ONLY on ovh-files (100.91.190.107) inside a throwaway container.
# Byline: Claude Code · Sonnet 5 · 2026-09-14
set -euo pipefail

WORKDIR=/data/probata/exchange/opendataloader-spike
GATE_SAMPLE=/data/probata/exchange/spacedrive-gate/sample
R2_MOUNT=/srv/r2/casebible-sorted

mkdir -p "$WORKDIR"

docker rm -f opendataloader-spike >/dev/null 2>&1 || true

docker run -d --name opendataloader-spike \
  -v "$WORKDIR":/work \
  -v "$GATE_SAMPLE":/input/gate-sample:ro \
  -v "$R2_MOUNT":/input/r2:ro \
  -w /work \
  python:3.12-slim sleep infinity

docker exec opendataloader-spike bash -c '
  set -e
  apt-get update -qq
  apt-get install -y -qq default-jre-headless procps >/tmp/apt.log 2>&1
  echo "--- java ---"; java -version
  echo "--- python ---"; python3 --version
  echo "--- pip install opendataloader-pdf + pypdf ---"
  pip install --quiet opendataloader-pdf pypdf
  python3 -c "import opendataloader_pdf, pypdf; print(\"opendataloader-pdf OK\", opendataloader_pdf.__file__); print(\"pypdf OK\", pypdf.__version__)"
'
