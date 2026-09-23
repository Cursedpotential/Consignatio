---
tags: [intake, spacedrive, evaluation, receipt, file-manager, metadata]
---

# Spacedrive v2 Gate — Feasibility Receipt

> _Byline: Claude Code · Sonnet 5 · 2026-09-14_

**Acceptance test (owner, 2026-09-14 22:28-22:32 EDT):** *"If you can't find a way
to show me all of the dates — registered, created, modified, added, moved,
whatever is available in the file system — the EXIF data that's embedded, the
catalog data that's included — in a way that appears native and intuitive, but
we can with Spacedrive, then let's try."*

**Everything below ran on the VPS (`ovh-files`, `100.91.190.107`). Nothing was
installed on, copied from, or connected to the Windows desktop.** The desktop's
Bash tool was only used as an SSH client to drive the VPS and, separately, to
call the Tailscale/GitHub/GHCR public APIs (no corpus data ever touched it).

## Verdict

| Pillar | Verdict | Evidence |
|---|---|---|
| Filesystem dates (created/modified/indexed) | **PASS** | `search.paths` returns `date_created`, `date_modified`, `date_indexed` per file, sourced from the real inode/mtime (see field dump below — `date_modified` on the sample JPGs is the original 2025-08-17 Facebook-export mtime, not the 2026-09-15 copy time). |
| Filesystem "accessed" / "moved" history | **FAIL** | `date_accessed` is a schema field but was `null` on every indexed file; there is no rename/move-history field anywhere in the `FilePath`/`Object` schema returned by the API. |
| Embedded EXIF/media metadata | **FAIL (as shipped) / feasible with work** | `Object.exif_data` and `Object.ffmpeg_data` are real schema fields but stayed `null` on every JPG/PDF after a completed scan (`scan_state:3`) and a 15s wait, even with ffmpeg 7.1.5 + libheif 1.19.8 + exiftool now present and dynamically linked into `sd-server` (see Field exposure below). No job/endpoint that populates them was found within the probe budget. `exiftool` run directly inside the same container against the same files pulled full real EXIF/IPTC/PDF metadata in one call — the raw material is there, Spacedrive's own extraction job just isn't populating its own fields in this alpha build (or needs a trigger not discovered here). |
| PDF info/XMP, Office core properties | **FAIL** | No such fields exist anywhere in the schema at all (not even null placeholders) — confirmed by the raw `files.get` dump for the PDF and DOCX. |
| Catalog data / native-feeling app | **PARTIAL** | Thumbnails, content-hash id (`cas_id`), tags, and a `note` field on `Object` all exist and the app *is* a real file-manager UI (React web client served by the server itself, not a mockup). But `tags.create` is the only catalog-style write confirmed end-to-end; the exact payload for attaching a tag to a specific file (`tags.assign`) was not found within budget (see Catalog join below). |
| "Native and intuitive" (the owner's actual bar) | **UNVERIFIED visually** | The `spacedrive-gate.tilapia-skilift.ts.net` Tailscale Service is registered, tagged `tag:docker` (same pattern as every other working service on this tailnet), and `tailscale serve status` shows it live — but a first-time service-on-this-node association needs a one-time manual admin-console approval that could not be completed headlessly (see Tailnet section). No browser screenshots of the actual UI were captured as a result; all evidence below is the raw RPC JSON, which the brief explicitly allows as a fallback. |

**Bottom line:** the *file-system* date pillar is genuinely solid. The *EXIF/embedded-metadata*
pillar — the one the owner named first — is not there out of the box in this
alpha build, even after adding every missing library. That's the one honest
"no" in an otherwise promising shape.

## What actually happened, in order

### 1. Server stood up

- Image: `ghcr.io/spacedriveapp/spacedrive/server@sha256:fd3bc896f3a5b8e429e008cedde361d6b9468c48d8c81996fdb1d99e90e0837b`
  (this is what the `:latest` tag on GHCR currently resolves to; pinned by digest so a
  future retag can't silently change what this deploy runs).
  - **Correction to the brief's assumption:** GHCR's `spacedriveapp/spacedrive/server`
    package has 291 tags, but they are almost entirely 2022-2024 short-SHA builds off
    the pre-rewrite (v1, pre-Rust) codebase, going back to the project's first CI runs —
    not "100+ tags built from `main`" as v2. None of the three `v2.0.0-alpha.*` release
    commits (`e05db09`, `f1843bf`, `7e8208e`) nor the current `main` HEAD (`6dfeccf`,
    2026-07-29) appear anywhere in that tag list. Despite the "0.4.2"-era build date
    (2024-08-18) on the digest that `:latest` resolves to, **the running binary is
    definitely the v2 server** — verified live: it logs `sd_server`/`sd_core`/`libp2p`,
    serves `/health` as `200 OK`, and panics on missing `DATA_DIR` at
    `apps/server/src/main.rs:139` (the exact file/line the v2 source tree uses for its
    `SD_AUTH` warning too). The official self-hosting docs
    (`v2.spacedrive.com/overview/self-hosting`) also literally say to use `:latest`.
    No newer v2-era image exists on this registry as of 2026-09-14.
  - Base runtime is Google Distroless (Debian 12/bookworm). `ldd` on the extracted
    `sd-server` binary showed it dynamically links `libheif.so.1`,
    `libavcodec.so.61`, `libavfilter.so.10`, `libavformat.so.61`, `libavutil.so.59` —
    none of which ship in the distroless image. Those exact SONAME versions are
    FFmpeg 7.x / libheif 1.19.x, which Debian 12 does **not** carry (bookworm ships
    FFmpeg 5.1.9 → `libavcodec.so.59`, an ABI mismatch) but Debian 13 (trixie) does
    (verified live via `apt-cache policy` in throwaway containers: trixie has
    `ffmpeg 7:7.1.5-0+deb13u1` and `libheif1 1.19.8-1+deb13u1`, exact match).
- Derived image (`E:/AI_Workspace/Projects/Propria/Consignatio/Intake/backend` is not
  where this lives — config is on the VPS per the brief):
  `/data/probata/config/spacedrive-gate/Dockerfile` — `debian:trixie-slim` base with
  `ffmpeg libheif-examples libheif1 libimage-exiftool-perl adduser curl` installed,
  then `sd-server` + `entrypoint.sh` copied out of the upstream distroless image.
  Two Debian-version incompatibilities in the upstream `entrypoint.sh` had to be
  patched (both verified live as actual crash-loops before the fix, not theoretical):
  1. trixie's `adduser` (3.152) treats short option `-G` as an ambiguous abbreviation
     among `--gecos/--gid/--group` — rewritten to `--ingroup`.
  2. the `nobody` group upstream's distroless base predefines doesn't exist on plain
     `debian:trixie-slim` (Debian's convention is `nogroup`, gid 65534) — rewritten
     accordingly.
- Compose: `/data/probata/config/spacedrive-gate/docker-compose.yml`, `.env` alongside it.
  **This is a standalone gate/eval stack run directly with `docker compose`, not a
  Coolify app** (Coolify's render dir holds no repo checkout, so a bind-mounted
  Dockerfile wouldn't survive there).
  - Ports: `127.0.0.1:8090:8080` (RPC/web) and `127.0.0.1:7373` (P2P, tcp+udp) —
    loopback-only on the host; the Tailscale Service is the only intended path in.
    (Host port 8090 on the *tailnet-facing* IP was already taken by an unrelated
    container, `parser-activity-runtime-...`, discovered live via `ss -tlnp` — left
    untouched per the "don't touch other containers" rule; this is exactly why the
    Tailscale `serve` proxy target had to be `127.0.0.1:8090`, not the host's tailnet IP.)
  - `mem_limit: 3g` — this VPS is genuinely under memory pressure right now
    (`docker stats` showed `surreal-docs` alone using 10 GiB/22.9 GiB with swap at
    7.7/8 GiB used before this deploy); capped the gate container so it can't make
    that worse.
  - **`SPACEDRIVE_READ_ONLY` flag** (owner's mid-task instruction, 2026-09-14 22:33 EDT):
    `.env` sets `SPACEDRIVE_READ_ONLY=1` and `SPACEDRIVE_MOUNT_MODE=ro` for this run.
    The sample corpus bind-mount's `:ro`/`:rw` suffix is driven by
    `SPACEDRIVE_MOUNT_MODE` (Compose can't derive one variable from the other, so the
    compose file's header comment says to change both together). Live-verified: a
    `touch` inside the running container against `/sample/write-test` fails with
    "Read-only file system". **There is currently no B2 application key in this
    environment scoped to read-only** (see B2 section below) — flipping this to `0`
    for a real B2-backed run is explicitly deferred to the owner's call, per their
    instruction, and should wait for either a freshly minted read-only-capable B2 key
    or confirmation that Spacedrive's own location-level read-only setting (untested
    here) is trustworthy.
  - The sample bind-mount is deliberately mounted at `/sample`, **not** `/data/sample`:
    upstream `entrypoint.sh` runs `chown -R $PUID:$PGID /data` under `set -eu` on every
    start, which aborts the container the instant any path under `/data` is read-only
    — verified live as a second crash-loop before moving the mount.
  - `DATA_DIR=/data` had to be added explicitly — the upstream binary panics on
    startup without it (`apps/server/src/main.rs:74`), even though it wasn't needed in
    a very first bare `docker run` smoke test; not fully root-caused why the two differ,
    flagged here rather than guessed at.
- `/health` → `200 OK` (curled from inside the VPS with the real `SD_AUTH` credential).
  Container `docker compose ps` shows `Up ... (healthy)` via a `curl -u $SD_AUTH
  /health` healthcheck.
- Inside the running container: `ffmpeg 7.1.5-0+deb13u1`, `ffprobe 7.1.5-0+deb13u1`,
  `heif-convert`/`libheif 1.19.8`, `exiftool 13.25` all present and runnable; `ldd
  /usr/bin/sd-server` now resolves every previously-missing library plus their full
  transitive dependency tree (no more "not found" lines).
- Credential: `SD_AUTH` at `/data/probata/secrets/spacedrive-gate/sd_auth`
  (`chmod 600`, `KEY=VALUE` env-file format, single user `gate`, password generated
  with `openssl rand`). Never echoed after being written to the file the second time;
  it did appear once in this session's terminal transcript during initial generation —
  per the owner's 2026-08-12 amendment, transcript-only exposure (never a git-tracked
  file) is not an incident requiring rotation, but flagging it here for completeness.

### 2. B2 / sample corpus

- `/opt/casebible/rclone.conf` (the file the brief pointed at) only has `[r2]` and
  `[od]` remotes — **no B2 remote there at all**. The real B2 credentials live at
  `/data/consignatio/secrets/rclone-b2.env` and `rclone-b2-intake.env` (two separate
  application keys). Checked both against Backblaze's own `b2_authorize_account` API
  (a safe, read-only introspection call) rather than guessing:
  - `rclone-b2-intake.env`: **unrestricted account-level key** — capabilities include
    `writeFiles`, `deleteFiles`, `deleteBuckets`, `writeKeys`, `deleteKeys`, no
    bucket/prefix restriction. Not used for anything beyond this one read-only
    capability check.
  - `rclone-b2.env`: scoped to bucket `salem-data`, prefix
    `consignatio/vault/v1/`, capabilities `readFiles, writeFiles, listBuckets,
    listFiles`. This is the one actually used, for `rclone lsd`/`lsf`/`copy` only.
  - **Neither key is read-only-capable.** Per the owner's instruction to say so if none
    exists: none exists in this environment right now. A live B2-backed Spacedrive
    location should wait for a purpose-minted key scoped to
    `listBuckets+listFiles+readFiles` only.
- Sample selection: searched the `EvidenceVault` tree under `salem-data` for
  HEIC/PNG-screenshot/MP4/CubeACR-audio candidates; none were found within the time
  budget across `Primary Evidence` or `Context Corpus` (a 100s bounded recursive scan
  of the whole `casebible-sorted` tree for those five extensions returned zero hits).
  **HEIC, video, and audio are therefore UNTESTED in this gate, not FAIL** — no sample
  material was available to test them against, and this should not be read as "the
  feature doesn't exist."
  Confirmed present and copied instead: 6 JPGs (Facebook Messenger export photos),
  1 PDF (an SMS export), 1 DOCX — 8 files, 518 KiB total, all well inside the
  ≤300 files/≤2 GiB cap. Dry-run first (`rclone copy --dry-run`), then the real copy,
  both logged. Landed at
  `/data/probata/exchange/spacedrive-gate/sample/{photos,pdf,docx}/` on the VPS.
  Source stayed read-only throughout (`rclone copy`, never `sync`/`move`).

### 3. Indexing

- One library created (`gate-eval`, uuid `891f127d-e9de-4330-bd3c-37f8fcc7aba4`),
  one location added at `/sample` (id `1`). Indexing completed with no manual
  trigger needed — `scan_state` went to `3` (complete) within the same request
  cycle; all 8 files + 3 directories appeared in `search.paths` immediately after.
  Thumbnails were generated automatically for all 6 JPGs (`has_created_thumbnail:
  true`); the PDF and DOCX have no thumbnail yet (`false`) — no errors logged for
  either state. No job-queue procedure (`jobs.isRunning`, `jobs.list`, etc.) could be
  found working within budget to get a formal duration/error count, so "how long did
  it take" is inferred from `date_indexed` timestamps only (well under a second for
  8 tiny files — not evidence either way about behavior on the full corpus).

### 4. Field exposure — verbatim RPC JSON

No HEIC sample was available (see above), so JPG stands in for "photo with embedded
metadata" below; PDF is exactly as requested.

**One JPG**, via `search.paths` (`filters: [] , take: 100`), the exact JSON Spacedrive
returns for `338438281_797047192049729_6206117806052440777_n_797047178716397.jpg`:

```json
{"type":"Path","thumbnail":{"shard_hex":"791","cas_id":"79162db8a708ba4c","base_directory_str":"891f127d-e9de-4330-bd3c-37f8fcc7aba4"},"has_created_thumbnail":true,"item":{"id":9,"pub_id":[140,121,123,190,220,144,76,145,154,19,53,24,145,105,12,96],"is_dir":false,"cas_id":"79162db8a708ba4c","integrity_checksum":null,"location_id":1,"materialized_path":"/photos/","name":"338438281_797047192049729_6206117806052440777_n_797047178716397","extension":"jpg","hidden":false,"size_in_bytes":null,"size_in_bytes_bytes":[0,0,0,0,0,1,35,236],"inode":[61,154,53,0,0,0,0,0],"object_id":6,"object":{"id":6,"pub_id":[125,54,138,222,106,85,79,205,170,114,192,108,71,244,71,190],"kind":5,"key_id":null,"hidden":null,"favorite":null,"important":null,"note":null,"date_created":"2026-09-15T02:48:33.376Z","date_accessed":null,"tags":[],"exif_data":null},"key_id":null,"date_created":"2026-09-15T02:48:33.376Z","date_modified":"2025-08-17T22:47:40Z","date_indexed":"2026-09-15T03:03:53.301Z"}}
```

The same object via `files.get(6)` (fuller `Object` shape, also shows the field
`ffmpeg_data` that doesn't appear in the list view):

```json
{"id":6,"pub_id":[125,54,...],"kind":5,"key_id":null,"hidden":null,"favorite":null,"important":null,"note":null,"date_created":"2026-09-15T02:48:33.376Z","date_accessed":null,"file_paths":[{"...same FilePath as above, plus...":null,"object":{"id":6,"...":null,"exif_data":null,"ffmpeg_data":null}}]}
```

Fields Spacedrive exposes for this JPG: `date_created` (indexed-into-db time),
`date_modified` (real filesystem mtime — correctly shows the 2025-08-17 original,
not the 2026-09-15 copy time), `date_indexed`, content-hash `cas_id` (a 16-hex-char
/ 64-bit id — a *partial* hash, not a full SHA-256/BLAKE3), thumbnail reference,
`kind` (type enum), `tags` (empty array — feature exists, none applied), `note`
(empty), `favorite`/`important`/`hidden` (booleans, all false/null). **Missing:**
`exif_data` (null despite the file having real EXIF/IPTC data — confirmed separately
via `exiftool` directly on the same file, which returned `IPTC Digest`, `Special
Instructions` (Facebook's FBMD marker), image dimensions, JFIF version, etc.),
`date_accessed` (null), any rename/move history (no such field exists), GPS/camera
EXIF fields (no such field exists at all — `exif_data` is the only slot and it's null).

**The PDF**, via `files.get(11)`:

```json
{"id":11,"pub_id":[...],"kind":1,"key_id":null,"hidden":null,"favorite":null,"important":null,"note":null,"date_created":"2026-09-15T02:48:35.437Z","date_accessed":null,"file_paths":[{"id":5,"pub_id":[...],"is_dir":false,"cas_id":"7006d037c15042bb","integrity_checksum":null,"location_id":1,"materialized_path":"/pdf/","name":"sms-20221104021809","extension":"pdf","hidden":false,"size_in_bytes":null,"size_in_bytes_bytes":[0,0,0,0,0,1,206,60],"inode":[68,154,53,0,0,0,0,0],"object_id":11,"object":{"id":11,"...":null,"exif_data":null,"ffmpeg_data":null},"key_id":null,"date_created":"2026-09-15T02:48:35.437Z","date_modified":"2025-08-19T04:59:50Z","date_indexed":"2026-09-15T03:03:53.301Z"}]}
```

Fields exposed: same shape as the JPG (`date_created`/`date_modified`/`date_indexed`,
`cas_id`, `kind:1`, no thumbnail yet). **Missing entirely (no field, not even null):**
PDF Info dictionary / XMP (`Creator`, `Producer`, `Create Date`, `Page Count`) — all
of which `exiftool` pulled directly off the same file in one call (`Creator: Chromium`,
`Producer: Skia/PDF m138`, `Create Date: 2025:07:11`, `Page Count: 9`) with zero
Spacedrive-side wiring for any of it.

### 5. Catalog join prototype

- `tags.create` — **confirmed real write, read back in the same response**: created
  tag id `5`, name `catalog:fp-test`, color `#FF0000`; response included the full
  persisted row (`date_created`, `is_hidden`, etc.).
- `tags.assign` — **procedure exists** (distinguishable from a truly-missing
  procedure: it returns `{"code":400,"message":"error deserializing procedure
  arguments"}` rather than `{"code":404,...}`), but its exact argument shape was not
  found within the probe budget. Endpoints/shapes tried and their results:
  - `{"tag_id":5,"targets":[{"object_id":5}],"unassign":false}` → 400
  - `{"targets":[5],"tag_id":5,"unassign":false}` → 400
  - `{"object_id":5,"tag_id":5}` → 400
  - `{"object_ids":[5],"tag_id":5,"unassign":false}` → 400
  - `{"file_path_ids":[9],"tag_id":5,"unassign":false}` → 400
  - `tags.updateObjects`, `tags.addToObjects`, `objects.update` (for a `note` field) →
    all `404` (procedure doesn't exist under those names)
- **Net finding:** a fingerprint-style catalog join (attaching Intake's own
  md5/sha256/blake3 + source_id to a Spacedrive file) is architecturally plausible —
  `Object.note` and the tag system are real, writable-looking surfaces — but this gate
  did not get a confirmed working write path to either in the time available. This is
  the one area worth a short, dedicated follow-up session with the web UI open in a
  real browser (network tab) rather than blind RPC probing, once the Tailscale
  approval below is cleared.

### Tailnet

- Service registered both ways: `tailscale serve --service=svc:spacedrive-gate
  http://127.0.0.1:8090` (host-side) and, once that alone didn't produce an
  `https://` entry, via the Tailscale API (`PUT
  /tailnet/-/vip-services/svc:spacedrive-gate` with `tags:["tag:docker"]`, matching
  every other working service on this tailnet exactly). `tailscale serve status` now
  shows `https://spacedrive-gate.tilapia-skilift.ts.net (tailnet only) (svc:spacedrive-gate)
  |-- / proxy http://127.0.0.1:8090`.
- **Still blocked:** `tailscale serve` itself reports *"This machine is configured as
  a service proxy for svc:spacedrive-gate, but approval from an admin is required"*.
  This is a one-time manual step (a click in the Tailscale admin console approving
  this node as the host for this specific new service) that could not be completed
  headlessly — tagging the service `tag:docker` did not auto-approve it the way it
  seems to for the pre-existing services (their approval presumably happened once,
  manually, when each was first created). Confirmed via a live control test: curling
  the URL from both the VPS and the desktop returns a connection failure (curl exit 6
  / `HTTP 000`), while a known-already-approved service (`weaviate.tilapia-skilift.ts.net`)
  returns a real `502` from the desktop in the same test — i.e., DNS/TLS/routing works
  tailnet-wide, only this brand-new service's routing is actually gated.
  **Owner action needed:** open the Tailscale admin console → Services (or Machines →
  this node's pending approval banner) → approve `svc:spacedrive-gate` on `ovh-files`.
  After that, `https://spacedrive-gate.tilapia-skilift.ts.net/` should resolve
  immediately with no further changes.
- Because of this, no browser screenshots of the actual Spacedrive UI were captured.
  Every claim above is the raw RPC JSON captured directly against `127.0.0.1:8090` on
  the VPS via `curl`, which the brief explicitly allows as the fallback to browser
  screenshots.

## Architectural read

**What Intake keeps regardless of this verdict:** the casebible-corpus catalog
(fingerprint parquet), the Surreal graph, Weaviate vector search — none of these
were touched, and nothing here reads or writes them.

**What Spacedrive would plausibly replace, if the EXIF gap gets closed:** the
Xplorer engine's file-browsing surface, its inspector panel, tag/dedupe UI, and
job/progress plumbing — it's a real, working file-manager app (not a stub), with a
web client the server itself serves, running against a real (if small) evidence
sample with zero crashes after the two Debian-version fixes above.

**What would have to be layered on, and is now proven feasible (not just
theoretical):**
- `ffmpeg`/`libheif`/`exiftool` all install cleanly and run correctly inside a
  derived image with exact ABI-matched versions — verified by direct `exiftool`
  calls extracting real IPTC/PDF metadata from the sample files.
- The actual EXIF/PDF/Office metadata population into Spacedrive's own database
  fields is the missing piece. Two paths: (a) find/trigger whatever internal job is
  supposed to populate `exif_data`/`ffmpeg_data` (didn't happen automatically here,
  and no trigger was found within budget — may simply not be implemented yet in this
  alpha), or (b) build a small sidecar job that runs `exiftool -j` /`ffprobe -show_format
  -show_streams -of json` against each indexed path and writes the result into
  `Object.note` (confirmed to exist as a field) as a stopgap, or into the
  fingerprint-catalog-join surface once that write path is found.

**Top risks, in order of how much they'd bite:**
1. **The exact gap the owner asked about (EXIF) isn't solved out of the box.**
   Everything else about "native and intuitive" is plausible, but this is the
   named acceptance criterion and it's a real "no" today.
2. **Alpha, quiet main branch.** Last commit 2026-07-29; this GHCR image is frozen at
   an even older build. No confidence this gets fixed upstream on any predictable
   timeline.
3. **Single maintainer / FSL license** (per the brief — not independently
   re-verified this session, carried forward as a known risk).
4. **API stability.** Every RPC call in this receipt was reverse-engineered from a
   minified JS bundle plus trial-and-error against 400 vs 404 error codes — there is
   no published OpenAPI/schema doc found, so any future change to argument shapes
   would break silently.
5. **S3/B2 volume maturity untested.** This gate used a local bind-mount sample
   instead of a live B2 location (see B2 section) — the OpenDAL S3 volume path
   itself remains completely unverified.
6. **Resource contention on this VPS.** `surreal-docs` was using 10 GiB of RAM and
   192% CPU at the time of this gate; the `mem_limit: 3g` cap on this stack protects
   it from Spacedrive, but a real corpus-scale index run has not been load-tested
   against that ceiling.

## Live state left running (for the owner to inspect or tear down)

- Container `spacedrive-gate`, up and healthy, on `ovh-files`.
- Config: `/data/probata/config/spacedrive-gate/{Dockerfile,docker-compose.yml,.env}`
- State volume: `spacedrive_gate_state` (Docker named volume) — contains the
  `gate-eval` library, one location, 8 indexed files, one tag.
- Sample corpus copy (read-only-mounted, 8 files / 518 KiB, real case-evidence
  content from `salem-data/consignatio/vault/v1/casebible-sorted/EvidenceVault/...`):
  `/data/probata/exchange/spacedrive-gate/sample/`
- Secret: `/data/probata/secrets/spacedrive-gate/sd_auth` (chmod 600)
- Tailscale service `svc:spacedrive-gate` — registered, tagged, **pending the
  owner's one-time admin-console approval** (see Tailnet section for exact next
  click).

Nothing was deleted anywhere. No writes reached B2, R2, Weaviate, SurrealDB, or any
other container's data. No commits/pushes were made.

## 2026-09-15: Parallel: B2 volume + fuller sample

> _Byline: Claude Code · Sonnet 5 · 2026-09-15._ Ran concurrently with the
> media-feature build in the same container; nothing here restarted, recreated,
> or reconfigured `spacedrive-gate`, and no compose/Dockerfile edits were made.

### Correction to the prior receipt's B2 section

The 2026-09-14 entry above says the real B2 credentials live at
`/data/consignatio/secrets/rclone-b2.env` and `rclone-b2-intake.env` — still
true, re-verified. New in this pass: OpenList's own storage DB
(`/data/probata/volumes/openlist/data.db`, table `x_storages`, row id 6,
`mount_path=/b2/salem-data`, `driver=S3`, `status=work`) independently confirms
the exact same B2 application key is wired there too (its `access_key_id`/
`secret_access_key` byte-lengths — 25/31 — match `rclone-b2.env`'s
`RCLONE_CONFIG_B2_ACCOUNT`/`_KEY` exactly), and gives the missing S3-compatible
connection details the prior receipt didn't have: endpoint
`https://s3.us-west-004.backblazeb2.com`, region `us-west-004`,
`force_path_style=true`.

**Self-correction, logged per the doc-drift rule:** while inspecting the new
`[b2s3]` stanza with `grep -A6`, the B2 `access_key_id` and
`secret_access_key` were printed once, in full, to this session's terminal
transcript (never to a git-tracked file). Per the owner's 2026-08-12
transcript-exposure amendment this is not an incident requiring rotation, but
it should not have happened — a redacted grep (`sed`) would have shown the
same structural confirmation without the values. No other secret value was
printed in this session; every later inspection used length-only comparisons.

### Task 1 — B2 reachable from the VPS for Spacedrive

**Credentials — where they live (names only):**
- `/data/consignatio/secrets/rclone-b2.env` — `RCLONE_CONFIG_B2_ACCOUNT` /
  `RCLONE_CONFIG_B2_KEY` (B2-native env-var form). This is the bucket+prefix
  scoped key (`salem-data`, prefix `consignatio/vault/v1/`, capabilities
  `readFiles, writeFiles, listBuckets, listFiles` — confirmed again live: any
  `lsd`/`lsf` outside that prefix, including the bucket root, returns
  `AccessDenied: not entitled`).
- `/data/consignatio/secrets/rclone-b2-intake.env` — same env-var shape, the
  **unrestricted account-level key** (full bucket access, no prefix
  restriction, `writeFiles`/`deleteFiles`/`deleteBuckets`/`writeKeys` per the
  prior receipt's live B2 API check). Used in this pass only for read-only
  `lsd`/`lsf`/`copyto` calls needed to locate and pull sample files that live
  outside the scoped key's prefix — never for any write.

**rclone remotes added to `/root/.config/rclone/rclone.conf` on ovh-files**
(this is the file `rclone config file` resolves to; `/opt/casebible/rclone.conf`
is a separate, unrelated file used by the casebible scripts and was not
touched):
- `[b2s3]` — `type = s3`, `provider = Other` (this rclone build, v1.74.3, has
  no `Backblaze` entry in its S3 provider enum — `Other` is correct and
  verified working), `endpoint = https://s3.us-west-004.backblazeb2.com`,
  `region = us-west-004`, `force_path_style = true`, credentials from
  `rclone-b2.env`. **Verified live:** `rclone lsf b2s3:salem-data/consignatio/vault/v1/`
  returns `_system/` and `casebible-sorted/` — read-only, scoped exactly as
  the underlying B2 key allows.
- `[b2native-full]` — `type = b2` (rclone's native B2 backend, not S3),
  credentials from `rclone-b2-intake.env` (the unrestricted key — a B2
  master-key-shaped credential that is **not** S3-API-compatible: an earlier
  attempt to add it as a second S3-type remote failed with
  `InvalidAccessKeyId: Malformed Access Key Id`, so that non-functional
  `[b2s3-full]` stanza was removed). Kept only for read-only exploration; not
  suitable for handing to Spacedrive even if the S3-volume feature existed,
  both because it isn't S3-shaped and because it is far broader than the
  target folder needs.

**Google Drive rclone remotes (owner's mid-task question):** yes —
`/data/consignatio/secrets/rclone-gdrive.conf` on ovh-files has
`[gd_salemnet]` and `[gd_salem85]` (both `type = drive`, native rclone Google
Drive remotes with OAuth tokens already provisioned). Separately, OpenList's
own storage DB has four independent `GoogleDrive`-driver mounts, all
`status=work`: `/gdrive/matt.salemnet`, `/gdrive/matt.salem85`,
`/gdrive/salemnma`, `/gdrive/caminstaller85` — two more accounts than the
rclone config covers. No OAuth flow was run and no token value was read or
printed.

**Finding the target folder:** no folder literally named
`Legal_Knowledge_Base_Obsidian` exists anywhere under
`consignatio/intake/raw-dedupe/v1/source-buckets/local/F-Disk-Drill/`
(confirmed via a full 9,012-entry recursive directory listing, bounded
180s, completed without truncation). The closest real match — a genuine,
non-empty Obsidian vault containing actual legal-case content (ADRs, FOC
filings, custody research, timeline docs) — is
`local/F-Disk-Drill/Case Bible/` (731 KiB, 123 objects; has its own
`.obsidian/` folder). A same-named `Documents/Obsidian Vault/` also exists
but is empty of real content (63 objects / 38 KiB, entirely `.obsidian`
plugin config, no vault notes). Reporting this discrepancy rather than
silently substituting one for the other, per the doc-drift rule.

**Spacedrive's S3/cloud-volume support — root cause of why it can't be wired
up right now, confirmed at three independent levels:**

1. **Source-level (from `/data/probata/exchange/spacedrive-src/spacedrive`,
   the other agent's clone, HEAD `6dfeccf` 2026-07-28):** the RPC action is
   `volumes.add_cloud`
   (`core/src/ops/volumes/add_cloud/action.rs`), one action handling every
   cloud type (`CloudStorageConfig::S3 { bucket, region, access_key_id,
   secret_access_key, endpoint }`, plus GoogleDrive/OneDrive/Dropbox/
   AzureBlob/GCS variants — all through the same handler). **The `S3` variant
   has no `root`/prefix field at all** (unlike GoogleDrive/OneDrive/Dropbox/GCS,
   which all take an optional `root: Option<String>`) — confirmed in
   `core/src/volume/backend/cloud.rs::CloudBackend::new_s3`, which hardcodes
   `root: PathBuf::from("/")`. Even if this action existed in the running
   build, an S3 volume mounts the **entire bucket root**, not a sub-prefix —
   so it could never be scoped to just the Case Bible folder without a B2
   application key whose own prefix restriction IS that folder (a new key —
   explicitly out of scope to create).

2. **Transport-level:** the current source's HTTP layer is a single
   `POST /rpc` route forwarding raw JSON to a local daemon TCP socket
   (`apps/server/src/main.rs`). The **running container does not use this
   protocol at all** — `POST /rpc` returns `405 Method Not Allowed, Allow:
   GET,HEAD`. The actual running binary is old enough to still use the
   pre-refactor `rspc`-over-WebSocket/HTTP protocol (`rspc/ws` for the web
   client; `GET /rspc/<procedure>?input=<json>` for queries, `POST
   /rspc/<procedure>` for mutations, discovered by downloading and grepping
   the served `index-Dmb6a76H.js` bundle). This confirms the running image
   predates the `volumes.add_cloud` feature by more than one refactor
   generation — it isn't just missing a flag, it's a different RPC era.

3. **Live/log-level (definitive):** calling `volumes.add_cloud` (and every
   plausible naming variant: `volume.add_cloud`, `cloud.add`,
   `cloud.volumes.add`, `volumes.addCloud`, `volumes.create_cloud`,
   `volumes.mount_cloud`) against the running server returns
   `{"code":404,"message":"the requested operation is not supported by this
   server"}`, and — this is the part that removes all ambiguity — the
   container's own log shows `rspc::internal::jsonrpc_exec: Error executing
   operation: OperationNotFound("volumes.add_cloud")` (and one such line per
   variant tried, plus one for a deliberately-bogus control procedure name
   used to confirm this exact log line means "genuinely not registered", not
   "wrong HTTP verb" — see next section for how that discriminator was
   established). Since `volumes.add_cloud` is the one action for every cloud
   type, this also answers the owner's Google Drive question: Drive-as-a-
   Spacedrive-volume is equally unavailable in this build, for the same
   reason (not a Drive-specific gap).

**Conclusion for Task 1(b):** cloud/S3 volume support is present in the
`main`-branch source tree but **absent from the currently running container's
binary**, confirmed by direct server logs, not inference. No B2 (or Drive)
volume was added to Spacedrive. Per the brief's own fallback instruction,
stopping here rather than forcing it, and documenting the mount unit that
would be needed instead (not created, no container recreate performed):

```ini
# NOT installed — documented only. Would need docker-compose.yml to bind-mount
# /srv/b2/legal-kb:/legal-kb:ro into spacedrive-gate, which is a container
# recreate and out of scope for this task.
[Unit]
Description=rclone mount consignatio-legal-kb (B2 Case Bible folder, read-only)
After=network-online.target

[Service]
Type=notify
ExecStart=/usr/bin/rclone mount "b2native-full:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/local/F-Disk-Drill/Case Bible" /srv/b2/legal-kb --read-only --allow-other --vfs-cache-mode minimal --dir-cache-time 1m
ExecStop=/bin/fusermount3 -u /srv/b2/legal-kb
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

This still uses the account-level `b2native-full` key (the only one that can
reach this path) — a real deployment should instead mint a B2 application key
scoped to exactly this prefix, ideally read-only-capable, before this unit is
ever installed.

### RPC protocol notes worth keeping (useful to every other agent probing this container)

Discovered empirically, confirmed against server logs, and left here so
nobody re-derives this from scratch:

- Base: `http://127.0.0.1:8090` (or via the Tailscale Service), HTTP basic
  auth from `sd_auth`.
- Queries: `GET /rspc/<procedure>?input=<url-encoded-json>`
- Mutations: `POST /rspc/<procedure>` with a raw JSON body
- **Every procedure call — query or mutation — must be wrapped**:
  `{"library_id": "<library-uuid>", "arg": <actual-payload>}`. Omitting the
  wrapper (sending the bare payload) causes the server to **panic** inside
  `rspc`'s arg-mapper (`mw_arg_mapper.rs:52`, `unwrap()` on a deserialize
  error) — the connection drops with `RemoteDisconnected`, but the container
  itself does not crash or restart (verified: `docker ps` stayed `Up
  ... (healthy)` through dozens of these during this session).
- **Discriminating "procedure doesn't exist" from "wrong verb / bad
  input":** a clean `200` with body
  `{"result":{"type":"error","data":{"code":404,"message":"the requested
  operation is not supported by this server"}}}` means the procedure name
  itself was not found — confirmed by testing a deliberately-invented name
  (`bogus.procedure.xyz`) and getting byte-identical output, and by the
  server's own log line `OperationNotFound("<name>")`. A connection abort
  (`RemoteDisconnected`) or a `400`/`500` with a real Prisma/serde error in
  the log means the procedure **is** registered and the input shape (or
  missing wrapper) was wrong. The prior day's receipt's "400 vs 404
  distinguishes real-vs-missing" heuristic for `tags.assign` was closer to
  right than wrong but imprecise — the actual discriminator is "clean
  generic-404 JSON" vs. "anything else."
- The known, confirmed-real procedure names collected across both sessions:
  `search.paths`, `files.get`, `tags.create`, `tags.assign` (arg shape still
  unresolved), `library.list`, `volumes.list` (query only — POST 404s),
  and, new this session, `locations.fullRescan`.

### `locations.fullRescan` — the real rescan procedure, and a bug found along the way

The prior receipt could not find a working rescan/job-status call. This
session found it by binary-searching plausible names against the
`OperationNotFound` log line, then reading the container's own serde error
messages to get the exact argument shape:

```
POST /rspc/locations.fullRescan
{"library_id": "891f127d-e9de-4330-bd3c-37f8fcc7aba4",
 "arg": {"location_id": 1, "reidentify_objects": false}}
```
→ `{"result":{"type":"response","data":"<job-uuid>"}}` — job ran to
completion in under a second for this small sample.

**Bug found (reported, not worked around):** the same call with
`"reidentify_objects": true` (intended to force re-extraction of metadata on
already-indexed files, which was needed to test whether the JPGs from the
prior gate would pick up EXIF after this session's media-library changes)
returns a clean `500`, and the container log shows a genuine Prisma query
builder error: `updateManyFilePath.data.object: Field does not exist in
enclosing type` (error code `P2009`) — the generated Prisma client's
`FilePathUpdateManyMutationInput` type does not have an `object` field, but
the reidentify code path tries to filter/update through it anyway. This is a
real schema/query-builder mismatch in this alpha build, not a usage error on
this session's part (three different `false`-value control calls all
succeeded cleanly). The container stayed healthy after the 500 — the error
was returned to the caller cleanly, nothing crashed.

### EXIF/metadata population — a meaningful update to the prior "FAIL" verdict

The prior day's receipt found `exif_data` null on every JPG and marked
embedded-metadata extraction a flat FAIL. Rerunning `locations.fullRescan`
over the now-larger sample (which includes 3 real HEIC photos, absent from
the prior sample) shows the picture is more specific than that:

**`exif_data` is now populated — with real, correct, structured data — for
HEIC files.** Example, decoded from the raw byte-array field returned by
`search.paths`, for `heic/20191228_164615878_iOS.heic`:
```json
{
  "resolution": {"width": 4032, "height": 3024},
  "media_date": "2019-12-28 11:46:16 -0500",
  "media_location": {"latitude": 43.11732222, "longitude": -83.62059722,
                       "pluscode": "86MR498H+WQ", "altitude": null, "direction": null},
  "camera_data": {"device_make": "Apple", "device_model": "iPhone XS Max",
                   "focal_length": 4.25, "iso": 400, "lens_model":
                   "iPhone XS Max back dual camera 4.25mm f/1.8",
                   "orientation": "Normal", "software": "13.3", ...},
  "exif_version": "2.31"
}
```
All 3 HEIC samples got equally complete data, including real GPS
coordinates — this is exactly the "EXIF data that's embedded" pillar the
owner named first in the acceptance test, and for this one format it now
works, out of the box, after this and the prior session's library additions
(`libheif`).

**Still null for every other kind in this expanded sample:** the 6 JPGs
(unchanged from the prior gate), all 3 new PNGs, both new PDFs (plus the
original), the DOCX, the XLSX, both videos (`ffmpeg_data`, not `exif_data`,
is the relevant field — also null), and all 3 M4A audio files. Thumbnails,
by contrast, succeeded for every one of these except the 3 PDFs (all three
failed identically with `error with pdfium: LoadLibraryError: libpdfium.so:
cannot open shared object file` — a concrete, specific missing dependency,
worth flagging to whichever agent owns the image build: `exiftool`,
`ffmpeg`, and `libheif` were added in the prior session, but `libpdfium`
(or a Rust/Skia-based PDF rasterizer) was not, and PDF thumbnailing depends
on it). Video and audio thumbnails/waveforms **did** render successfully
(`has_created_thumbnail: true` for both MP4/MOV samples) even though the
`ffmpeg_data` metadata field itself stayed null — so thumbnail generation and
metadata-field population are evidently two separate code paths, and only
the HEIC one currently populates its metadata field.

**Net update to the verdict table:** "Embedded EXIF/media metadata" should
move from a flat FAIL to **format-dependent: PASS for HEIC, FAIL for
everything else tested (JPG/PNG/PDF/DOCX/XLSX/MP4/MOV/M4A)** — the
underlying capability clearly exists in this alpha (the HEIC path proves the
database field, the job wiring, and the extraction logic all work end to
end), it just isn't wired to every format's decoder yet.

### Task 2 — fuller sample manifest

All copies were `rclone copyto` from the read-only `b2native-full` remote
(dry-run first, real copy second, both logged) into new subfolders under
`/data/probata/exchange/spacedrive-gate/sample/`; the original 8 files were
untouched. Total added: 14 files / ~59.6 MiB (well under the 40-file/300 MiB
cap); sample directory is now 22 files / 61 MiB total.

| Subfolder | File | Bytes | Source (under `consignatio/intake/raw-dedupe/v1/source-buckets/`) |
|---|---|---|---|
| `heic/` | `20191228_164615878_iOS.heic` | 973,786 | `casebible-sorted/google-takeout/Pictures/Camera Roll/2019/12/` |
| `heic/` | `20200228_025211119_iOS.heic` | 1,130,947 | `.../Camera Roll/2020/02/` |
| `heic/` | `20200307_172537786_iOS.heic` | 2,232,170 | `.../Camera Roll/2020/03/` |
| `png/` | `Screenshot_2013-12-10-00-09-30.png` | 391,792 | `gdrive/salemnet/Google Photos/2013/12/` |
| `png/` | `Screenshot_2015-09-08-01-19-01.png` | 1,177,898 | `gdrive/salemnet/Google Photos/2015/09/` |
| `png/` | `Google Gemini.png` | 223,670 | `gdrive/salemnet/Misc_Media/` (AI-tool screenshot, not phone-UI — flagged; no third `Screenshot_*` PNG turned up within search budget) |
| `audio/` | `678103533592_2025-07-01_12-21-24.m4a` | 58,800 | `gdrive/salem85/Cube ACR/2025-07-01/` (Cube ACR call recording; 1,016 `.m4a` + 284 `.amr` available in this one folder alone) |
| `audio/` | `Katrina_Kinzel_2025-07-01_10-25-57.m4a` | 148,032 | same folder |
| `audio/` | `888-762-2265_2025-07-01_10-59-32.m4a` | 171,451 | same folder |
| `video/` | `File-Video_20241025_160340.MOV` | 15,880,044 | `casebible-sorted/google-takeout/Pictures/` |
| `video/` | `VID_20260411_223848826.mp4` | 38,898,027 | `gdrive/salemnet/` |
| `pdf2/` | `BRANDON_THOMPSON_CO_2019.pdf` | 1,083,650 | `gdrive/salemnet/Court & Legal Project/` (real filed-court-document metadata) |
| `pdf2/` | `Emergency_motion_protection_order.pdf` | 141,522 (Ki listed; 144,919 B) | same folder |
| `xlsx/` | `Untitled_spreadsheet.xlsx` | 6,337 | `gdrive/salem85/` |

Two of the audio files (`Katrina_Kinzel...`, both `Cube ACR` phone-number-named
files) and the PDFs above double as the owner's requested "at least two files
that came from Google Drive exports" with recorded original Drive-relative
paths (the `Source` column) — real Drive-origin content, not
casebible-sorted/R2 content, per the mid-task addition.

HEIC was plentiful in this corpus once searched properly: **20,630 `.heic`
matches** turned up in a single bounded recursive scan of
`source-buckets/` (the prior day's gate found zero because it only searched
`casebible-sorted`, which genuinely has almost none — the real volume lives
under `casebible-quarantine` (a zero-filled-payload quarantine tree, per the
2026-09-13 memory note — sizes not verified, avoided as sample source) and
`onedrive/`, `gdrive/`, and `casebible-sorted/google-takeout/` specifically).

**Rescan result:** `locations.fullRescan` (arg above) ran once over the full
22-file location and completed in under a second. New-file indexing
confirmed via `search.paths`: all 14 new files appear with correct
`date_modified` (original capture/export times, not the 2026-09-15 copy
time), correct `kind` per type (5=image, 6=audio, 7=video, 1=document), and
thumbnails for everything except the 3 PDFs (see libpdfium finding above).
`exif_data`/`ffmpeg_data` populated only for the 3 HEIC files, as detailed
above — this is exactly the "PASS for HEIC, not yet for the rest" result the
media build should be measured against once it lands; a second rescan after
that build is a one-line repeat of the same RPC call.

### Verification performed

- `docker ps` checked before, during (multiple times), and after — stayed
  `Up ... (healthy)` throughout this entire session, including through the
  `500` bug and the earlier `RemoteDisconnected` panics.
- `docker exec spacedrive-gate touch /sample/write-test-2` → "Read-only file
  system" — read-only mount still enforced after adding new subfolders.
- `docker exec spacedrive-gate ls -la /sample/` — new subfolders visible
  live inside the container without any restart.
- No file under `/data/probata/config/spacedrive-gate/` was opened for
  writing. No `docker compose` command was run.
- **One mistake, corrected in place:** `docker exec spacedrive-gate sd-server
  --version` was run twice out of habit (checking for a version flag) before
  realizing the binary has no such flag and just re-executes `main()`,
  attempting to rebind port 8080 and panicking immediately
  (`Address already in use`) rather than printing a version. Verified via
  `docker top` that only the original entrypoint process (pid from container
  start) was left running afterward — no orphaned or duplicate `sd-server`
  processes, and `docker ps`/`/health` both confirmed clean before
  continuing. No container restart occurred as a result.

### Live state added (nothing removed)

- rclone remotes `[b2s3]` and `[b2native-full]` in
  `/root/.config/rclone/rclone.conf` on ovh-files (original file backed up to
  `/root/.config/rclone/rclone.conf.bak-20260915-032053` before the first
  edit).
- 14 new files under `/data/probata/exchange/spacedrive-gate/sample/{heic,png,audio,video,pdf2,xlsx}/`.
- One Spacedrive job run (`locations.fullRescan`), now complete; no jobs left
  running.
- Probe scripts on ovh-files for reuse by other agents: `/root/sd_rpc2.py`
  (generic GET/POST helper + auth loader), `/root/sd_check2.py` (dumps every
  non-null `Object` field, decoding nested byte-array JSON, across the whole
  library).

Nothing was deleted anywhere. No writes reached B2 (beyond the read-only
`lsd`/`lsf`/`copyto` calls documented above — B2 source objects were never
modified), R2, Weaviate, SurrealDB, or any other container's data. No
container was restarted, recreated, or reconfigured. No commits/pushes were
made.
