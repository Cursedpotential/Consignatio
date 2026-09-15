#!/usr/bin/env bash
# Switch hybrid OCR backend from easyocr (broken: missing libxcb.so.1 for cv2)
# to tesseract, per opendataloader-pdf-hybrid --ocr-engine option.
# Byline: Claude Code · Sonnet 5 · 2026-09-14
set -euo pipefail

docker exec opendataloader-spike bash -c '
  for pid in $(ps aux | grep "port 5002" | grep -v grep | awk "{print \$2}"); do
    kill -9 "$pid" || true
  done
  sleep 1
  apt-get install -y -qq tesseract-ocr libtesseract-dev >/tmp/apt2.log 2>&1
  echo "--- tesseract version ---"
  tesseract --version | head -3
'
