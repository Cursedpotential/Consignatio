#!/usr/bin/env python3
"""Remove the Spacedrive tile from the portal (owner 2026-09-17 08:27: "just kill it").

Byline: Claude Code · Fable 5.1 · 2026-09-17

Run ON ovh-app:
    MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/ovh root@100.72.169.40 'python3 -' \
        < docs/ops/spacedrive-retire-portal-tile-2026-09-17.py

Drops the `- Spacedrive ...:` list item (and its indented body) from both Homepage
instances' services.yaml. Dated backup beside each file. Idempotent.
"""
import re
import shutil
import time

FILES = ["/data/dashboards/homepage/services.yaml",
         "/data/dashboards/homepage-public/services.yaml"]
STAMP = time.strftime("%Y%m%dT%H%M%S")

for path in FILES:
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except FileNotFoundError:
        print(path, "missing, skipped")
        continue
    out, skip_indent, removed = [], None, 0
    for line in lines:
        if skip_indent is not None:
            indent = len(line) - len(line.lstrip())
            if line.strip() == "" or indent > skip_indent:
                continue
            skip_indent = None
        m = re.match(r"^(\s*)- .*[Ss]pacedrive.*:\s*$", line)
        if m:
            skip_indent = len(m.group(1))
            removed += 1
            continue
        out.append(line)
    if removed:
        shutil.copy2(path, f"{path}.bak-{STAMP}-retire-spacedrive")
        open(path, "w", encoding="utf-8").write("\n".join(out))
    print(path, "tiles removed:", removed)
