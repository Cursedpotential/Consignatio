# Xplore CB co-workspace — first vertical slice

<!-- Byline: Claude Code · Sonnet 5 · 2026-09-14 -->

Owner direction 2026-09-14 08:19-09:28 EDT: make the Xplore CB surface a single
working co-workspace (Xplorer as engine, no side-by-side apps), reach B2 through
the existing OpenList bridge, allow explicit user/agent-directed file operations
pre-evidence-space, and prove the metadata-catalog join. This receipt records what
shipped, what was verified live, and one deliberately unimplemented piece with an
explicit design for the owner to choose from.

## Deployed

- Route: `https://homepage.tilapia-skilift.ts.net/progress/intake/`
- Release `2026-09-14T13-05-08-000Z` is current; prior release
  `2026-09-12T16-01-25-624Z` is untouched on disk for rollback (flip
  `intake-build/current.json` back to it).
- Host: ovh-app (100.72.169.40), Coolify service `homv6zeg4ay2r2puxtzakf83`
  (propria-progress-board), restarted only via the Coolify API.

## What changed

### Shell (`/data/dashboards/progress-board/intake-preview/`)

Replaced the two-independent-iframe preview with a single full-bleed Explorer
pane (Xplorer is the engine; no second app displayed beside it, per owner
direction 2026-09-13 "the Xplorer copilot and the Case Bible/Consignatio review
surfaces are one tool"). A thin header shows a live context strip (scope,
selection count, connection status) fed by a `postMessage` the engine already
broadcasts. Styled with the Propria design contract (`pr-tokens.css`,
`pr-theme.css`, `pr-intake-adapter.css` vendored from
`E:\AI_Workspace\Projects\Propria\resources\design`, contract v1.0.0,
2026-09-12 pin). No paragraph disclaimers on the page (owner direction
2026-09-13); unvalidated/limited controls carry one small flag (a caution dot
with a tooltip) instead.

Backups: `index.html.bak-20260914-two-iframe-shell`,
`style.css.bak-20260914-two-iframe-shell`, `app.js.bak-20260914-two-iframe-shell`
(same pattern for the intermediate docked-shell revision, superseded within the
same session before final deploy).

### Xplorer fork (`xplorer-copilot-buildkit/xplorer-copilot`, branch `feat/acp-copilot`)

- `apps/client/src/hooks/use-intake-embed-bridge.ts` (new): broadcasts the
  existing `window.__xplorer_state__` selection manifest to the parent frame via
  `postMessage`, same-origin only. No-op outside an iframe.
- `apps/client/src/pages/xplorer.tsx`: mounts the bridge hook.
- `apps/client/src/components/panels/ReviewDockPanel.tsx` (new) +
  `RightSidebar.tsx` + `VerticalExtensionsBar.tsx`: adds "Review & metadata" as
  a right-rail panel _inside_ Xplorer (alongside Preview/AI Chat), not a second
  app. It iframes the existing Intake review app (`../metadata/`, sibling
  build) and forwards the live selection into it directly. Gated behind
  `VITE_INTAKE_MODE=1`. Carries one small flag ("Example review set in this
  deployment"); AI Chat carries one small flag when not running under Tauri
  ("Model not connected in this browser build") — see Not done, below.
- `apps/client/src/App.tsx`: wouter now gets an explicit `base` computed from
  `window.location.pathname` at load. **Bug found live**: without this, the
  app 404'd (wouter's default location hook does not know the page is served
  under `/progress/intake/xplorer/`, since the reverse proxy strips
  `/progress` server-side but the browser's own `location.pathname` still
  carries it). Verified fixed live.
- Build: `MSYS_NO_PATHCONV=1 VITE_API_MODE=http VITE_API_URL=../storage npx vite
build --base ./` (relative `../storage`, not `/intake/storage` — the absolute
  form bypasses the `/progress` mount and 404s at the wrong host route; found
  live). **Gotcha for future builds on this Windows/Git-Bash desktop**:
  `MSYS_NO_PATHCONV=1` is required or Git-Bash rewrites `VITE_API_URL=/intake/
storage` into a `C:/Program Files/Git/...` path, which gets baked into the
  bundle and breaks every storage call (`file://` URL errors in the browser
  console) — found and fixed live before it reached this deploy.

### Intake review app (`Consignatio/Intake` root, `src/`)

- `src/features/live-selection/use-intake-selection-bridge.ts` (new),
  `LiveSelectionPanel.tsx` (new): receives the engine's selection manifest over
  `postMessage`, renders name/path/type/size for up to 5 items plus a remainder
  count (matches the shared chat-context presentation rule), metadata only —
  never reads file bytes itself.
- `src/app/App.tsx`: mounts the panel above the existing review workbench.

### Storage bridge (`/data/dashboards/progress-board/openlist-bridge.mjs`, `server.mjs`)

- `OPENLIST_TOKEN` was never configured — the bridge was permanently
  unauthenticated (503 on every OpenList call). Obtained the OpenList site's
  permanent token (via `/api/auth/login` then `/api/admin/setting/get?key=
token` with the existing admin credential in `~/.secrets/openlist.env`) and
  set it in `/data/dashboards/progress-board.env` (backed up
  `.bak-20260914-openlist-token`). Restarted via Coolify API.
- **Bug found live**: `server.mjs`'s generic `storageCommand` route
  (`/intake/storage/api/([a-z_]{1,80})`) also matched the literal path segment
  `asset`, so the dedicated GET/HEAD `/intake/storage/api/asset` preview route
  was permanently shadowed (always 405). Fixed by excluding `asset` from that
  match. Backup: `server.mjs.bak-20260914-asset-route-shadowed`.
- **Bug found live**: `storagePath()`'s character blocklist rejected `%`, `?`,
  `#`, which are legitimate filename characters that exist in this actual
  corpus (`# new_timeline_processor／file_reconstructor.docx`, and a `.webloc`
  file with a literal `%`) — one such name in a folder failed the _entire_
  directory listing (`casebible-raw`, 324 entries, all inaccessible). Relaxed
  the blocklist to only backslash/control-chars/`.`/`..`, and made `list()`
  resilient (skip + count any entry that still can't be represented, instead of
  failing the whole folder). Backup:
  `openlist-bridge.mjs.bak-20260914-readonly-strict-validator`.
- **Preview 403 found live**: `/p` (WebProxy) is disabled on the B2 storage
  mount ("403 proxy not allowed"). Switched to `/d` (direct download) with the
  per-file `sign` query param from `/api/fs/get`, following its redirect
  **server-side only** — the browser never sees the signed provider URL or any
  provider credential, only the resulting bytes. Backup:
  `openlist-bridge.mjs.bak-20260914-preview-proxy-403`.
- **Write operations added** (owner direction 2026-09-14 09:28 EDT: explicit
  user/agent-directed move, rename, copy, delete, mkdir are in scope
  pre-evidence-space): `create_dir_recursive` → mkdir, `rename` → rename
  in-place, `remove_file`/`remove_dir` → remove, `move_file`/`copy` → move/copy
  (with a same-directory rename follow-up when source and destination names
  differ). Deliberately did **not** wire `move_to_trash` — OpenList/B2 has no
  trash/undo, so aliasing the app's "trash" action (which reads as
  recoverable) to a permanent remove would be dishonest; it stays a clear
  "not available" (501) instead.

## Verified live (via the exact public route, `https://homepage.tilapia-skilift.ts.net/progress/intake/...`)

- Explorer loads (wouter fix) and reports "Explorer connected" with a live
  selection count in the context strip.
- B2 root and `salem-data` list correctly (`b2`, `desktop`, `exchange`,
  `gdrive`, `onedrive`, `r2`, `volumes`; salem-data → `consignatio`,
  `db_backups`, `infra-backups`).
- The previously-broken `casebible-raw` folder now lists all 324 entries,
  including the two names that used to break it.
- A real file previews: `GET .../storage/api/asset?path=/b2/salem-data/.../
casebible-raw/.directory` → 200, 32 bytes, correct content.
- Write operations proven end-to-end against a disposable path
  (`/b2/salem-data/_agent-test-20260914/...`): mkdir, rename, copy, move,
  remove all succeeded via the real bridge/command layer; **the disposable
  folder was fully removed afterward** — `read_directory('/b2/salem-data')`
  confirms only `consignatio`, `db_backups`, `infra-backups` remain. No owner
  file was touched.
- Metadata catalog join proven with real rows (see below).

**Not independently confirmed by rendered screenshot**: the Browser pane in
this session renders at a very small fixed size, so click-through/visual
confirmation of the Review & metadata panel and AI Chat inside Xplorer's own
right rail is partial. All calls above were verified against the exact same
public HTTP route and headers the browser UI itself calls (confirmed via the
page's own network log for some), which is a strong proxy but not a full
rendered-screenshot substitute.

## Metadata catalog join — proven, endpoint not yet wired

Confirmed against real data (read-only, `metabase_ro` role, `casebible`
database, schema `raw_duck`, on Coolify service `casebible-pg18` /
`fgz1n7useplhk0t91uk7k1aw`, host ovh-files):

- `source_occurrences.b2_key` has 546,187 non-null rows.
- The join key is exactly what the owner specified: an OpenList path under
  `/b2/salem-data/` maps to a B2 object key by stripping that prefix. Example
  proven live: `/b2/salem-data/consignatio/intake/raw-dedupe/v1/source-
buckets/casebible-raw/_backup_import/g/Takeout/Google Photos/screens/
2025-06-29(496).png` (confirmed browsable via `file_exist` → `true`) has
  `b2_key = 'consignatio/intake/raw-dedupe/v1/source-buckets/casebible-raw/
_backup_import/g/Takeout/Google Photos/screens/2025-06-29(496).png'` in
  both `b2_content` (md5 `820cc1fb9c872ff8d7f50f50084a86f0`, size 5148310) and
  **two** `source_occurrences` rows — `local/F-case` and `onedrive` — proving
  the "every occurrence, corroborating copies stay distinct" model the Intake
  contract requires.

**Why the endpoint is not wired yet**: `casebible-pg18` is a Coolify-managed
database (`is_public: false`, no `public_port`) reachable **only** from other
containers on the same `coolify` docker network on **ovh-files**
(100.91.190.107). `progress-board` runs on a different host, **ovh-app**
(100.72.169.40). There is currently no tailnet-reachable path between them —
this is a real network topology fact, not a credential or code gap.

Concrete options for the owner to choose (per the explicit instruction to stop
and report a design here rather than build one unilaterally):

1. **Publish `casebible-pg18` on a tailnet-scoped host port on ovh-files**
   (e.g., bind to the tailscale interface only, not `0.0.0.0`), then
   `progress-board` connects directly with `metabase_ro` over the tailnet.
   Lowest-effort, but is a security-relevant change to a database's network
   exposure and needs explicit sign-off even though it stays tailnet-only.
2. **A minimal read-only HTTP sidecar on ovh-files** (same `coolify` network as
   the database), called by `progress-board` over the tailnet. Avoids
   widening the database's own exposure, but is a new running service on a
   host explicitly marked "DO NOT DISTURB" for other casebible work, so it
   needs its own care (separate compose/container, does not touch the
   existing casebible services).
3. **Move the lookup to run on ovh-files itself** instead of progress-board
   (e.g., a small addition to something already deployed there with tailnet
   reachability) — no such existing service was identified in this pass.

Once reachability is settled, the endpoint itself is small: a same-origin
`POST /intake/metadata/lookup {b2_path}` on `progress-board`, deriving
`b2_key` by stripping `/b2/salem-data/`, then a single parameterized,
`LIMIT`-bounded query joining `b2_content` and `source_occurrences` on
`(md5, size)`, returning the occurrence rows (source, scope, path,
disposition, provider metadata) for the panel to render next to the live
selection. No DB credential would ever reach the browser bundle.

## Native desktop / OpenList WebDAV

Not built this pass (owner: "don't build that in this pass unless it's
trivial" — it is not trivial). The fork's Rust backend
(`apps/src-tauri/src/operations/`) has no existing WebDAV client; reaching
`https://files.tilapia-skilift.ts.net/dav` from the native app would need
either a new Rust WebDAV crate wired into a new operations module, or an OS-
level mount the app just browses as a local path. Both are real, scoped
follow-up work, not a drop-in change.

## Files changed

**Local (this desktop):**

- `xplorer-copilot-buildkit/xplorer-copilot/apps/client/src/hooks/use-intake-embed-bridge.ts` (new)
- `xplorer-copilot-buildkit/xplorer-copilot/apps/client/src/pages/xplorer.tsx`
- `xplorer-copilot-buildkit/xplorer-copilot/apps/client/src/components/panels/ReviewDockPanel.tsx` (new)
- `xplorer-copilot-buildkit/xplorer-copilot/apps/client/src/components/panels/RightSidebar.tsx`
- `xplorer-copilot-buildkit/xplorer-copilot/apps/client/src/components/explorer/VerticalExtensionsBar.tsx`
- `xplorer-copilot-buildkit/xplorer-copilot/apps/client/src/App.tsx`
- `src/features/live-selection/use-intake-selection-bridge.ts` (new)
- `src/features/live-selection/LiveSelectionPanel.tsx` (new)
- `src/app/App.tsx`
- `docs/RECEIPT-2026-09-14-XPLORE-CB-CO-WORKSPACE.md` (this file)

**VPS (ovh-app, `/data/dashboards/progress-board/`):**

- `intake-preview/index.html`, `style.css`, `app.js` (rewritten; `.bak-20260914-*` kept)
- `server.mjs` (asset-route fix + 3 new intakeFiles entries; `.bak-20260914-*` kept)
- `openlist-bridge.mjs` (validator relaxation, resilient listing, `/d`+sign preview, write ops; `.bak-20260914-*` kept)
- `progress-board.env` (added `OPENLIST_TOKEN`; `.bak-20260914-openlist-token` kept)
- `intake-build/releases/2026-09-14T13-05-08-000Z/{xplorer,metadata}/`, `current.json`

No owner file was moved, renamed, copied or deleted. The only writes against
live storage were the disposable `_agent-test-20260914` test path, fully
removed afterward, and the read-only PG queries proving the join.

## Addendum 2026-09-14 17:19-21:44 EDT — catalog lookup wired end to end

<!-- Byline: Claude Code · Sonnet 5 · 2026-09-14 -->

Owner decision 2026-09-14 17:18 EDT: "it's my personal tailnet, just me, I need
it to work, make it simple" -- option 1 from the three above (publish
`casebible-pg18` on the tailnet, then wire the endpoint), no sidecar. This
closes the gap the initial pass reported: the metadata catalog join was proven
but not reachable from `progress-board`.

### Published: casebible-pg18 on the tailnet

- Coolify database `fgz1n7useplhk0t91uk7k1aw` (casebible-pg18) on ovh-files
  (100.91.190.107) is now published at **100.91.190.107:5475 -> 5432**,
  bound to the tailnet interface only (`docker ports:
  '100.91.190.107:5475:5432'`, never `0.0.0.0`) -- confirmed via `ss -ltnp` on
  ovh-files, which shows the docker-proxy listener bound to that specific
  address, not the wildcard.
- Done by a manual edit of the rendered compose
  (`/data/coolify/databases/fgz1n7useplhk0t91uk7k1aw/docker-compose.yml`,
  backup `docker-compose.yml.bak-20260914-tailnet-port` kept) plus
  `docker compose up -d` in that directory -- **not** Coolify's
  `is_public`/`public_port` fields, which always render an unrestricted
  `0.0.0.0` publish and would violate the tailnet-only requirement.
  Precedent followed: `probata-db` on the same host already publishes
  `100.91.190.107:5432->5432` the same way (its git-tracked compose uses a
  `${BIND_IP:-127.0.0.1}` port binding).
- `pg_hba.conf` inside the container already had `host all all all
  scram-sha-256` as its catch-all rule (no restrictive earlier rule shadowed
  it) -- no pg_hba change was needed. `listen_addresses` was already `*`.
- Live-verified from ovh-app (a different host, over the tailnet) as
  `metabase_ro`: `SELECT count(*) FROM raw_duck.b2_content` -> 504,482;
  `SELECT count(*) FROM raw_duck.source_occurrences WHERE b2_key IS NOT NULL`
  -> 1,495,454.
- **Risk carried forward**: this port binding lives only in the rendered
  compose file on disk, not in Coolify's stored database config. A future
  Coolify-driven redeploy/restart of `casebible-pg18` (UI or API) will
  re-render from Coolify's stored state and **could drop the ports mapping**,
  same as it dropped a hand-edited volume mount on `progress-board` during
  this session (see below) until that one was persisted through the API.
  Coolify has no public_port option restricted to one bind address for a
  database resource, so persisting this one the same way is not directly
  possible; if it disappears after any future Coolify action on this
  database, redo the same manual compose edit + `docker compose up -d`.

### Wired: `/intake/metadata/api/lookup` on progress-board

- New file `/data/dashboards/progress-board/pg-catalog.mjs` on ovh-app: a
  `pg.Pool` (added via `npm install pg` in that directory -- it had zero prior
  npm dependencies) reading the `metabase_ro` password from a file at startup,
  never from an env var, never logged. Exposes `lookup(openlistPath)`:
  strips the `/b2/salem-data/` prefix to get a `b2_key`, then queries
  `raw_duck.b2_content` and `raw_duck.source_occurrences` **by `b2_key`
  directly** (not `(md5, size)` as the original design note above suggested --
  live introspection found the proven example's OneDrive occurrence row has
  `md5 = NULL`, matched only via `name_size_mtime:carrier`; an `(md5,size)`
  join would silently drop it, so `b2_key` is the correct join column on both
  tables).
- `server.mjs` gained one route, `GET /intake/metadata/api/lookup?path=...`
  (inserted before the generic `/intake/(xplorer|metadata)/*` static-asset
  matcher, which would otherwise have shadowed it the same way `asset` shadowed
  the storage preview route earlier in this file). Backup:
  `server.mjs.bak-20260914-metadata-endpoint`.
- The `metabase_ro` password file (`/data/probata/secrets/metabase/pg-readonly`,
  mode 600, owned root:root, in a 700 root:root directory) is **not** readable
  by the `progress-board` container, which runs as uid 1000 (host user
  `debian`) with no root-owned paths mounted in. Rather than weaken the shared
  secrets tree's permissions, a scoped copy was made:
  `/data/probata/secrets/progress-board/metabase-ro` (mode 400, owned
  `debian:debian`), mounted read-only into the container at
  `/run/secrets/metabase-ro`. `PGCATALOG_PASSWORD_FILE` in
  `/data/dashboards/progress-board.env` points at that mounted path (backup
  `progress-board.env.bak-20260914-pgcatalog`); `PGCATALOG_HOST/PORT/USER/
DATABASE` are also set there for clarity, matching the defaults already
  compiled into `pg-catalog.mjs`.
- **Gotcha found live**: `progress-board` is a Coolify *service* (compose-based),
  not an *application*. Its `docker-compose.yml` on disk
  (`/data/coolify/services/homv6zeg4ay2r2puxtzakf83/docker-compose.yml`) is
  **regenerated from Coolify's own stored `docker_compose_raw` on every
  deploy** -- a manual edit to add the secret volume mount survived a plain
  `POST /services/{uuid}/restart` (which only restarts the existing container,
  no mount change reached it) but was silently wiped by
  `GET /deploy?uuid={uuid}` (which recreates the container from Coolify's
  stored compose, discarding the on-disk edit). Fixed by
  `PATCH /services/{uuid}` with `docker_compose_raw` set to the updated
  compose, **base64-encoded** (the API 422s with a clear message if it isn't),
  then `GET /deploy?uuid={uuid}` to render and recreate -- confirmed by
  `docker inspect ... --format '{{range .Mounts}}...'` showing both mounts
  after that redeploy. This is the correct way to persist a Coolify *service*
  compose change; the manual-edit-then-`docker compose up -d` approach used
  for `casebible-pg18` above only works there because it is a Coolify
  *database* resource, which has no equivalent "redeploy from stored config"
  action bound to it (only `is_public`/`public_port`, which weren't used).

### Release and live verification

- New release `2026-09-14T21-34-12-000Z` under
  `/data/dashboards/progress-board/intake-build/releases/`: `metadata/`
  rebuilt from `Consignatio/Intake` (`npx tsc -b && npx vite build --base ./`,
  matching the relative-asset convention the prior `metadata` release already
  used); `xplorer/` carried forward **unchanged** (byte-for-byte copy) from
  release `2026-09-14T13-05-08-000Z`, since nothing in the Xplorer fork
  changed this pass. `intake-build/current.json` now points at the new
  release; the prior one is untouched on disk for rollback (backup of the old
  `current.json` kept as `current.json.bak-20260914-pre-metadata-endpoint`).
- Local source changes (`Consignatio/Intake/src/features/live-selection/`):
  `use-catalog-lookup.ts` (new) fetches the lookup endpoint (same-origin,
  relative `api/lookup?path=...`) for each of the live selection's shown
  items, with a per-path in-memory cache. `LiveSelectionPanel.tsx` renders
  each item's real occurrence rows (source, path, size, md5 prefix) beneath
  it; an item with zero occurrences gets one small `⚠` flag ("No catalog
  match for this file") and nothing else -- no banner, no paragraph, per the
  "one flag, no disclaimers" UI rule. `npx tsc -b` passes clean.
- **Verified live through the exact public route**,
  `https://homepage.tilapia-skilift.ts.net/progress/intake/metadata/...`:
  - `GET .../api/lookup?path=%2Fb2%2Fsalem-data%2F...%2F2025-06-29(496).png`
    (the same proven example file from the first pass) -> HTTP 200, real
    `b2_content` row (md5 `820cc1fb9c872ff8d7f50f50084a86f0`, size 5148310)
    and all **6** real `source_occurrences` rows, including both
    `local/D-Backup`/`local/F-case` and the `onedrive` row with `md5: null`.
  - `GET .../api/lookup?path=%2Fb2%2Fsalem-data%2Fdoes%2Fnot%2Fexist.png` ->
    HTTP 200, `occurrences: []`, `count: 0` (graceful no-match, not an error).
  - `GET .../api/lookup?path=%2Fnot-b2%2Fx` -> HTTP 400, clear error message.
  - `GET .../healthz`, `GET .../intake/xplorer/`, `GET .../intake/metadata/`
    all still 200 -- no regression from the new route or the redeploy.
  - In an actual browser loaded at the public metadata URL, a simulated
    `postMessage` matching the real Xplorer selection-bridge shape (the same
    contract `use-intake-embed-bridge.ts` / `use-intake-selection-bridge.ts`
    use) was posted for the proven example file: the Live Selection panel
    updated and rendered all 6 real occurrence rows with no flag; a second
    postMessage for a nonexistent path rendered the `⚠` "No catalog match"
    flag and nothing else. `read_console_messages` showed no new errors tied
    to the catalog code path (pre-existing, unrelated 501s from an
    unimplemented `get_tokenizer_stats` storage command are visible on that
    page regardless of this change -- not touched, out of scope here).

### Files changed this addendum

**Local (this desktop):**

- `Consignatio/Intake/src/features/live-selection/use-catalog-lookup.ts` (new)
- `Consignatio/Intake/src/features/live-selection/LiveSelectionPanel.tsx`
- `Probata/probata/deploy/service-port-registry.json` (new `casebible` entry,
  port 5475 -- working tree only, not committed, per instruction)
- `docs/RECEIPT-2026-09-14-XPLORE-CB-CO-WORKSPACE.md` (this addendum)

**VPS ovh-files (`/data/coolify/databases/fgz1n7useplhk0t91uk7k1aw/`):**

- `docker-compose.yml` (added tailnet-bound `ports:`; backup
  `docker-compose.yml.bak-20260914-tailnet-port` kept)

**VPS ovh-app:**

- `/data/dashboards/progress-board/server.mjs` (new lookup route; backup
  `server.mjs.bak-20260914-metadata-endpoint` kept, alongside the two earlier
  backups from the first pass)
- `/data/dashboards/progress-board/pg-catalog.mjs` (new)
- `/data/dashboards/progress-board/package.json` / `package-lock.json` /
  `node_modules/` (added `pg` ^8.23.0 and its transitive deps -- first
  dependency this app has ever had)
- `/data/dashboards/progress-board.env` (appended `PGCATALOG_*` vars; backup
  `progress-board.env.bak-20260914-pgcatalog` kept)
- `/data/dashboards/progress-board/intake-build/current.json` (points at new
  release; backup `current.json.bak-20260914-pre-metadata-endpoint` kept)
- `/data/dashboards/progress-board/intake-build/releases/2026-09-14T21-34-12-000Z/`
  (new release: `metadata/` rebuilt, `xplorer/` copied forward unchanged)
- `/data/dashboards/progress-board/_scratch/` (new: two disposable
  verification scripts used to prove tailnet connectivity and introspect the
  schema before wiring the endpoint; harmless, not routed, left in place
  rather than deleted)
- `/data/probata/secrets/progress-board/metabase-ro` (new: a scoped,
  uid-1000-readable copy of the `metabase_ro` password, mode 400, for this
  one container to mount; the original root-only file and its directory were
  left untouched)
- `/data/coolify/services/homv6zeg4ay2r2puxtzakf83/docker-compose.yml` (gained
  the secret volume mount; also persisted into Coolify's own stored
  `docker_compose_raw` via the API, so a future Coolify redeploy will not
  silently drop it the way it dropped the first, file-only edit)

No owner file was touched. No test/sample rows were written to
`raw_duck.*` -- every query above was read-only.
