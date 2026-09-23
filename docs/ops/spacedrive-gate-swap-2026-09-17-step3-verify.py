#!/usr/bin/env python3
"""Prove the current-source Spacedrive image does no-index (ephemeral) browsing.

Byline: Claude Code · Opus 5 (1M) · 2026-09-17

Run ON ovh-files (it talks to 127.0.0.1:8090, the gate's published port):

    MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/ovh root@100.91.190.107 'python3 -' \
        < docs/ops/spacedrive-gate-swap-2026-09-17-step3-verify.py

Why this script exists in this shape
------------------------------------
Upstream `main` is a CQRS rewrite. The 2024 rspc routes an earlier probe
guessed at (`/rspc/search.ephemeralPaths`) do not exist. Read from
spacedriveapp/spacedrive @ 6dfeccf2113039e35f2ce735f945e70dc3e4ea45:

  * transport: POST /rpc, basic auth, body
        {"Query": {"method": ..., "library_id": ..., "payload": {...}}}
    reply {"JsonOk": ...} | {"Error": ...}   (apps/server/src/main.rs)
  * ephemeral browsing is the DEFAULT for unindexed dirs:
    core/src/ops/files/query/directory_listing.rs falls through to
    `query_ephemeral_directory_impl` when the path is not indexed, backed by
    core/src/ops/indexing/ephemeral/ (arena + cache + snapshot).
  * procedure names come from `register_{core,library}_query!` call sites.

The point is NOT merely "a listing returned". The point is that entries come
back for a path that no Location covers, and that no Location gets created as
a side effect. So locations.list is captured BEFORE and AFTER, and the
ephemeral cache is queried to show the index that served the listing.

Never prints SD_AUTH.
"""

import json
import ssl
import sys
import urllib.error
import urllib.request
from base64 import b64encode

BASE = "http://127.0.0.1:8090"
SECRET = "/data/probata/secrets/spacedrive-gate/sd_auth"
TARGET = "/media/openlist/b2/salem-data"

ssl._create_default_https_context = ssl._create_unverified_context


def read_auth():
    """Pull SD_AUTH=user:pass out of the env_file without echoing it."""
    with open(SECRET, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("SD_AUTH="):
                val = line[len("SD_AUTH=") :].strip().strip("'\"")
                if val:
                    return val
    raise SystemExit(f"FATAL: no non-empty SD_AUTH= line in {SECRET}")


AUTH = read_auth()
AUTH_HDR = "Basic " + b64encode(AUTH.encode()).decode()
print(f"auth loaded from {SECRET}: user={AUTH.split(':')[0]!r}, "
      f"secret length={len(AUTH.split(':', 1)[1]) if ':' in AUTH else 0} (value not printed)")


def http(path, data=None, timeout=120, raw=False):
    req = urllib.request.Request(BASE + path, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", AUTH_HDR)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, (body if raw else body.decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001 - want the reason, not a traceback
        return None, f"{type(e).__name__}: {e}"


def rpc(method, payload, library_id=None, timeout=300):
    """Send a Query. The wire name is NOT the bare procedure name.

    core/src/infra/wire/registry.rs registers every query under
    `query_method!(name)` == concat!("query:", name) and every action under
    `action_method!(name)` == concat!("action:", name, ".input"), and
    core/src/infra/daemon/rpc.rs looks the incoming `method` up in those maps
    verbatim. Sending the bare "libraries.list" therefore returns
    {"Error":{"OperationFailed":"Unknown method: libraries.list"}} -- which is
    a naming mismatch, NOT a missing procedure. packages/ts-client/src/client.ts
    does the same thing (it requires wireMethod to start with "query:"/"action:").
    """
    wire = method if method.startswith("query:") else f"query:{method}"
    body = json.dumps({"Query": {"method": wire,
                                 "library_id": library_id,
                                 "payload": payload}}).encode()
    code, text = http("/rpc", data=body, timeout=timeout)
    if code != 200:
        return code, text, None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return code, text, None
    if isinstance(parsed, dict) and "JsonOk" in parsed:
        return code, text, parsed["JsonOk"]
    return code, text, None


def section(n, title):
    print(f"\n{'=' * 72}\n=== {n}. {title}\n{'=' * 72}")


results = {}

# ---------------------------------------------------------------- 1. health
section(1, "/health (behind the same basic-auth layer as everything else)")
code, text = http("/health", timeout=30)
print(f"HTTP {code} :: {text[:200]!r}")
results["health"] = code
code_noauth, _ = (None, None)
req = urllib.request.Request(BASE + "/health")
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        code_noauth = r.status
except urllib.error.HTTPError as e:
    code_noauth = e.code
except Exception as e:  # noqa: BLE001
    code_noauth = f"{type(e).__name__}"
print(f"without credentials -> {code_noauth} (401 expected: auth is enforced)")
results["health_noauth"] = code_noauth

# ------------------------------------------------------------ 2. web client
section(2, "web client served from the embedded bundle")
code, text = http("/", timeout=60)
markers = [m for m in ("<!doctype html", "<!DOCTYPE html", "<div id=\"root\"",
                       "spacedrive", "/assets/", "<script") if m.lower() in text.lower()]
print(f"HTTP {code}, {len(text)} bytes, markers found: {markers}")
print("first 300 bytes:", text[:300].replace("\n", " "))
if "sd-server was built without" in text or "bun run build" in text:
    print("!! FAIL: server is serving the missing-web-bundle placeholder")
results["web"] = (code, len(text), markers)

# ------------------------------------------------------------- 3. libraries
section(3, "libraries.list -> library_id")
code, text, ok = rpc("libraries.list", {"include_stats": False})
print(f"HTTP {code} :: {text[:600]}")
library_id = None
if isinstance(ok, list) and ok:
    for lib in ok:
        if isinstance(lib, dict):
            library_id = lib.get("id") or lib.get("uuid") or lib.get("library_id")
            if library_id:
                print(f"-> library_id={library_id}  name={lib.get('name')!r}")
                break
if not library_id:
    # Expected whenever main-HEAD declines to open the frozen build's 2024
    # library (different schema entirely -- the CQRS rewrite) and the old
    # `libraries/` dir has been moved aside. A library is a container for the
    # index, and ephemeral browsing needs one to hang the query off, so create
    # one. This is not "test data becoming canonical": the ephemeral index is
    # by definition not persisted as a Location, and the real 2024 library is
    # preserved in the step1 backup.
    print("no library present -> creating one via the libraries.create action")
    body = json.dumps({"Action": {"method": "action:libraries.create.input",
                                  "library_id": None,
                                  "payload": {"name": "Propria", "path": None}}}).encode()
    code, text = http("/rpc", data=body, timeout=300)
    print(f"libraries.create HTTP {code} :: {text[:800]}")
    code, text, ok = rpc("libraries.list", {"include_stats": False})
    print(f"libraries.list again HTTP {code} :: {text[:600]}")
    if isinstance(ok, list):
        for lib in ok:
            if isinstance(lib, dict):
                library_id = lib.get("id") or lib.get("uuid") or lib.get("library_id")
                if library_id:
                    print(f"-> library_id={library_id}")
                    break
results["library_id"] = library_id

# --------------------------------------------------------------- 4. devices
section(4, "devices.list -> device_slug (SdPath::Physical requires it)")
device_slug = None
if library_id:
    code, text, ok = rpc("devices.list",
                         {"include_offline": True, "include_details": True,
                          "show_paired": False},
                         library_id=library_id)
    print(f"HTTP {code} :: {text[:800]}")
    if isinstance(ok, list):
        for d in ok:
            if isinstance(d, dict):
                slug = d.get("slug") or d.get("device_slug")
                if slug:
                    device_slug = slug
                    print(f"-> device_slug={device_slug!r} (name={d.get('name')!r})")
                    break
if not device_slug:
    code, text, ok = rpc("core.status", {})
    print(f"core.status HTTP {code} :: {text[:800]}")
    if isinstance(ok, dict):
        for key in ("device_slug", "slug"):
            if ok.get(key):
                device_slug = ok[key]
                print(f"-> device_slug from core.status: {device_slug!r}")
                break
results["device_slug"] = device_slug

# ------------------------------------------- 5. locations BEFORE the listing
section(5, f"locations.list BEFORE -- prove nothing covers {TARGET}")
def locations():
    if not library_id:
        return None, "no library"
    # LocationsListQueryInput is a UNIT struct, so serde wants `null`, not `{}`
    # ("invalid type: map, expected unit struct LocationsListQueryInput").
    c, t, o = rpc("locations.list", None, library_id=library_id)
    return o, t

before, before_raw = locations()
print(f"raw: {str(before_raw)[:900]}")
def as_location_list(o):
    """locations.list replies {"locations":[...]}, not a bare array."""
    if isinstance(o, dict):
        return o.get("locations") or []
    return o if isinstance(o, list) else None


def covering(locs):
    hits = []
    locs = as_location_list(locs)
    if isinstance(locs, list):
        for loc in locs:
            if isinstance(loc, dict):
                p = str(loc.get("path") or loc.get("local_path") or "")
                if p and (TARGET.startswith(p) or p.startswith(TARGET)):
                    hits.append(p)
    return hits
print(f"locations count before: {len(as_location_list(before)) if as_location_list(before) is not None else 'n/a'}")
print(f"locations covering {TARGET} before: {covering(before) or 'NONE  <-- required'}")
results["locations_before"] = len(as_location_list(before)) if as_location_list(before) is not None else None
results["covering_before"] = covering(before)

# ------------------------------------------------- 6. the ephemeral listing
section(6, f"files.directory_listing on {TARGET} (NO Location) -- the whole point")
listing = None
if library_id and device_slug:
    payload = {
        "path": {"Physical": {"device_slug": device_slug, "path": TARGET}},
        "limit": 200,
        "include_hidden": False,
        "sort_by": "name",
        "folders_first": True,
    }
    print("payload:", json.dumps(payload))
    # Ephemeral indexing is ASYNCHRONOUS. directory_listing checks the
    # ephemeral cache first and, on a miss, kicks off an on-demand index and
    # returns what it has -- which on the very first call for a cold path is
    # total_count=0 while core.ephemeral_status reports the path under
    # `paths_in_progress`. That is the feature working, not failing, so poll
    # until the path leaves `paths_in_progress` and entries appear rather than
    # reading the first empty reply as a negative result.
    import time
    listing, code, text = None, None, ""
    for attempt in range(1, 31):
        code, text, listing = rpc("files.directory_listing", payload,
                                  library_id=library_id, timeout=600)
        got = len((listing or {}).get("files") or []) if isinstance(listing, dict) else 0
        _, _, eph = rpc("core.ephemeral_status",
                        {"path_filter": None, "detailed": False}, timeout=60)
        in_prog = (eph or {}).get("paths_in_progress") if isinstance(eph, dict) else None
        done = (eph or {}).get("indexed_paths") if isinstance(eph, dict) else None
        print(f"  attempt {attempt}: HTTP {code} entries={got} "
              f"in_progress={in_prog} indexed={done}")
        if got > 0:
            break
        time.sleep(4)
    print(f"HTTP {code}")
    if listing is None:
        print(f"raw reply (first 2000): {text[:2000]}")
    else:
        files = listing.get("files") or []
        print(f"total_count={listing.get('total_count')} has_more={listing.get('has_more')} "
              f"returned={len(files)}")
        print("--- REAL ENTRIES ---")
        for f in files[:40]:
            if not isinstance(f, dict):
                print("  ", str(f)[:160]); continue
            name = f.get("name") or f.get("file_name") or "?"
            kind = f.get("kind") or f.get("content_kind") or ""
            isdir = f.get("is_dir") if "is_dir" in f else f.get("is_directory")
            size = f.get("size") or f.get("size_in_bytes") or ""
            print(f"   {'DIR ' if isdir else 'FILE'}  {name!r}  kind={kind} size={size}")
        results["entries"] = [
            (f.get("name") if isinstance(f, dict) else str(f)) for f in files[:40]
        ]
        results["total_count"] = listing.get("total_count")
else:
    print(f"SKIPPED: library_id={library_id} device_slug={device_slug} "
          "-- cannot build an SdPath without both")

# -------------------------------------------- 7. locations AFTER the listing
section(7, "locations.list AFTER -- prove the listing created NO Location")
after, after_raw = locations()
print(f"locations count after: {len(as_location_list(after)) if as_location_list(after) is not None else 'n/a'}")
print(f"locations covering {TARGET} after: {covering(after) or 'NONE  <-- required'}")
lb, la = as_location_list(before), as_location_list(after)
same = lb is not None and la is not None and len(lb) == len(la)
print(f"location count unchanged: {same}")
results["locations_after"] = len(as_location_list(after)) if as_location_list(after) is not None else None
results["covering_after"] = covering(after)

# ---------------------------------------------- 8. ephemeral cache evidence
section(8, "core.ephemeral_status -- which index actually served that listing")
code, text, eph = rpc("core.ephemeral_status",
                      {"path_filter": None, "detailed": True}, timeout=120)
print(f"HTTP {code} :: {text[:2500]}")
results["ephemeral_status_http"] = code

# ------------------------------------------------------------------ verdict
section(9, "VERDICT")
entries = results.get("entries") or []
ok_health = results.get("health") == 200
ok_web = results.get("web", (None,))[0] == 200
ok_entries = len(entries) > 0
ok_no_loc = not results.get("covering_after")
print(f"health 200 .................... {ok_health}")
print(f"web client served ............. {ok_web}")
print(f"real entries returned ......... {ok_entries} ({len(entries)} shown)")
print(f"no Location covers the path ... {ok_no_loc}")
print(f"\nEPHEMERAL NO-INDEX BROWSING PROVEN: {ok_health and ok_web and ok_entries and ok_no_loc}")
print("\njson summary:", json.dumps({k: v for k, v in results.items()}, default=str)[:1500])
sys.exit(0 if (ok_health and ok_web and ok_entries and ok_no_loc) else 1)
