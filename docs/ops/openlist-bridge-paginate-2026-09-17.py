#!/usr/bin/env python3
"""Replace the 500-entry hard stop in the portal's Xplorer/OpenList bridge with paging.

Byline: Claude Code · Fable 5.1 · 2026-09-17

Run ON ovh-app:
    MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/ovh root@100.72.169.40 'python3 -' \
        < docs/ops/openlist-bridge-paginate-2026-09-17.py

Why: `list()` in /data/dashboards/progress-board/openlist-bridge.mjs asked OpenList for one
page of 500 and threw 413 "exceeds the 500-entry browser limit" on anything larger, so the
hosted Xplorer could not open vault/v1 (owner 2026-09-17 08:16). The cap was ours, not
OpenList's. Now: page through 500 at a time up to MAX_ENTRIES, then stop with the same 413.
Idempotent; keeps a dated backup beside the file. Restart the app through Coolify afterwards.
"""
import shutil
import sys
import time

PATH = "/data/dashboards/progress-board/openlist-bridge.mjs"
OLD = '''    const data = await api("list", {
      path,
      password: "",
      page: 1,
      per_page: 500,
      refresh: false,
    });
    if (data.total > 500)
      throw new StorageError(
        "This folder exceeds the 500-entry browser limit; use a narrower directory",
        413,
      );
'''
NEW = '''    // 2026-09-17: page through large folders instead of refusing them at 500 entries.
    const MAX_ENTRIES = 20000;
    const data = await api("list", {
      path,
      password: "",
      page: 1,
      per_page: 500,
      refresh: false,
    });
    if (data.total > MAX_ENTRIES)
      throw new StorageError(
        `This folder has ${data.total} entries (browser limit ${MAX_ENTRIES}); use a narrower directory`,
        413,
      );
    data.content = data.content || [];
    for (let page = 2; data.content.length < data.total && page <= MAX_ENTRIES / 500; page++) {
      const more = await api("list", {
        path,
        password: "",
        page,
        per_page: 500,
        refresh: false,
      });
      if (!more.content || more.content.length === 0) break;
      data.content.push(...more.content);
    }
'''

src = open(PATH, encoding="utf-8").read()
if "MAX_ENTRIES" in src:
    print("already patched")
    sys.exit(0)
if src.count(OLD) != 1:
    sys.exit("FATAL: expected block not found exactly once; file changed, not patching")
backup = f"{PATH}.bak-{time.strftime('%Y%m%dT%H%M%S')}-pre-paginate"
shutil.copy2(PATH, backup)
open(PATH, "w", encoding="utf-8").write(src.replace(OLD, NEW))
print("patched; backup:", backup)
