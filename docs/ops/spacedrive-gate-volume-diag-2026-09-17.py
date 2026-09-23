#!/usr/bin/env python3
"""Why does the Spacedrive web UI show one volume that opens empty?

Byline: Claude Code · Fable 5.1 · 2026-09-17

Read-only. Run ON ovh-files:

    MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/ovh root@100.91.190.107 'python3 -' \
        < docs/ops/spacedrive-gate-volume-diag-2026-09-17.py

Asks the server the same things the UI asks: volumes.list, then a directory
listing of the volume's mount point and of the real data paths, with the
device slug the UI uses (taken from the server log: local://<slug>/...).
Never prints SD_AUTH.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from base64 import b64encode

BASE = "http://127.0.0.1:8090"
SECRET = "/data/probata/secrets/spacedrive-gate/sd_auth"
SLUGS = [a for a in sys.argv[1:] if not a.startswith("--")] or ["a3cb8334ac95", ""]
PATHS = ["/media", "/media/openlist", "/media/openlist/b2",
         "/media/openlist/b2/salem-data", "/media/openlist/b2/salem-data/consignatio"]


def auth():
    for line in open(SECRET, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("SD_AUTH="):
            return line[len("SD_AUTH="):].strip().strip("'\"")
    raise SystemExit("no SD_AUTH")


HDR = "Basic " + b64encode(auth().encode()).decode()


def rpc(method, payload, library_id=None):
    body = json.dumps({"Query": {"method": "query:" + method,
                                 "library_id": library_id,
                                 "payload": payload}}).encode()
    req = urllib.request.Request(BASE + "/rpc", data=body, method="POST")
    req.add_header("Authorization", HDR)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            text = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}"
    parsed = json.loads(text)
    return parsed.get("JsonOk"), text


if "--status" in sys.argv:
    # which paths the ephemeral cache believes it has, and how many entries each
    out, raw = rpc("core.ephemeral_status", {"path_filter": None, "detailed": True})
    print(json.dumps(out, indent=1)[:6000] if out is not None else raw[:1500])
    sys.exit(0)

libs, raw = rpc("libraries.list", {"include_stats": False})
lib = libs[0]["id"] if libs else None
print("library:", lib)

for payload in ({"filter": "All"}, {}, None):
    vols, raw = rpc("volumes.list", payload, library_id=lib)
    if vols is not None:
        print("volumes.list payload", payload, "->")
        print(json.dumps(vols, indent=1)[:3000])
        break
    print("volumes.list payload", payload, "failed:", raw[:300])

for slug in SLUGS:
    for p in PATHS:
        payload = {"path": {"Physical": {"device_slug": slug, "path": p}},
                   "limit": 200, "include_hidden": "--hidden" in sys.argv,
                   "sort_by": "name", "folders_first": True}
        n, names = 0, []
        for _ in range(6):
            out, raw = rpc("files.directory_listing", payload, library_id=lib)
            files = (out or {}).get("files") or []
            n = len(files)
            names = [f.get("name") for f in files[:8] if isinstance(f, dict)]
            if n or out is None:
                break
            time.sleep(3)
        print(f"slug={slug!r:16} {p:40} entries={n:4} {names if out is not None else raw[:200]}")
