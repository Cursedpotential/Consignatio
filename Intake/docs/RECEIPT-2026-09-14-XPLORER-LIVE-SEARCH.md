---
tags: [intake, search, xplorer, receipt, ui-components]
---

# Xplorer live search + native metadata panel — receipt

> _Byline: Claude Code · Sonnet 5 · 2026-09-14_

This continues a task whose previous agent was lost mid-run (a partially built
`IntakeFilesystemSearchPanel.tsx` with rg/keyword/hybrid methods survived on
disk; the live index run and the iframe-based `ReviewDockPanel` did not). Mid-task
the coordinator relayed four live owner redirects (22:02–22:16 EDT) that changed
the target architecture from "search panel in `Intake/src`" to "native panels
inside the Xplorer fork's own React tree, no iframe, no postMessage" plus a
dual-grid (Glide + AG Grid) requirement and a fields-must-be-real constraint on
the metadata panel. Everything below reflects that final scope.

## What was built

### Backend (`Intake/backend`, package `casebible_index`)

- `src/casebible_index/search.py`: added `relative_path_for`, `lookup_document`
  (real catalog/fingerprint row for one absolute path, plus same-content-hash
  duplicate detection within the corpus — never invents a field the pipeline
  doesn't write), and `run_lake_query` / `DuckDbQueryError` (read-only SQL over
  two fixed views, `documents` and `chunks`, bound to this backend's own output
  dir; single-statement, SELECT/WITH only, blocklists DDL/DML keywords, bounded
  result rows).
- `src/casebible_index/api.py`: two new endpoints — `GET /filesystem/lookup?path=`
  and `POST /filesystem/duckdb`.
- `src/casebible_index/models.py`: `LakeQueryRequest`.
- `src/casebible_index/pipeline.py`: the failure-observer now appends one JSON
  line per failure (path, processor, exception type/message) to
  `output/<run>/run-status/failure-diagnostics.jsonl` — the prior counter-only
  observer gave no way to explain *why* files failed after the fact.
- `pyproject.toml` / `uv.lock`: added `pytz` (duckdb needs it to convert
  `TIMESTAMPTZ` columns via `fetchone`/`fetchall`; this was a pre-existing gap,
  hit for the first time by the new lookup/lake-query code paths).
- `tests/test_lookup_and_lake.py` (new, 12 tests, all passing): path-outside-source
  rejection, not-yet-indexed, real-fields-only assertion (asserts no `exif`/`xmp`
  key ever appears), duplicate detection, and the full unsafe-SQL blocklist.
- Full backend suite: **119 passed** (`.venv/Scripts/python.exe -m pytest tests/
  -q --ignore=tests/test_cli_lifecycle.py`; that one file is excluded because it
  exercises the live index CLI end-to-end and would collide with the live run
  below).

### Xplorer fork (`Intake/xplorer-copilot-buildkit/xplorer-copilot`)

Owner-mandated architecture: everything below is a **native component in the
fork's own `apps/client/src` React tree** — no iframe, no `postMessage` bridge,
no second app.

- `apps/client/src/lib/intake-backend.ts` (new): the one adapter module to the
  `casebible-corpus serve` HTTP API — `lookupPath`, `searchCocoIndex`,
  `runLakeQuery`, `graphNeighbors`/`graphStatus`, `filesystemStatus`. Base URL
  is `http://localhost:8765` by default (see **Known limitation** below for why
  `localhost`, not `127.0.0.1`, matters). The renderer never holds a database
  credential — every call is a plain HTTP request to this one loopback backend.
- `apps/client/src/components/panels/ReviewDockPanel.tsx` (rewritten, no shell
  kept around it): the native metadata panel. No selection → one line ("No file
  selected."). One file selected → a detail card with exactly the columns the
  `documents` Parquet dataset actually has (size, content SHA-256, source/indexed
  timestamps, document type/date, review/index state, extraction method, chunk
  count, confidence, people/orgs/locations/topics/keywords, duplicate count +
  list). Not found → one small `⚠` flag with the real reason (outside configured
  source / no index yet / not indexed yet), never a fabricated row. 2+ files
  selected → the `ResultsGrid` toggle (below), one row per file. A static,
  always-visible "not extracted by this backend yet" block lists the field
  classes that are genuinely absent (photo EXIF/XMP, HEIC internals, PDF
  info/XMP, Office properties, media tags) — per owner direction, disclosed as
  flags, never invented values. No "Extract metadata" action is present (no
  backend endpoint exists for it yet).
- `apps/client/src/components/panels/ResultsGrid.tsx` (new): the owner-requested
  dual grid — **both** Glide Data Grid and AG Grid Community, behind a
  user-selectable toggle (persisted per-browser in `localStorage`). Used by the
  metadata panel (multi-file rows) and by the DuckDB SQL results in the search
  panel.
- `apps/client/src/components/explorer/IntakeFilesystemSearchPanel.tsx`
  (extended): added two methods to the existing rg/keyword/hybrid selector —
  **cocoindex** (semantic search over the Parquet lake via `/search`, normalized
  into the same hit shape so provenance/selection/open-location stay one code
  path) and **duckdb** (free SQL against `documents`/`chunks`, rendered through
  `ResultsGrid`). Every hit still carries engine/collection/source id/score/path
  provenance, matching the existing pattern.
- `apps/client/src/components/panels/RightSidebar.tsx`: passes the real
  `selectedFile`/`selectedFiles` props into `ReviewDockPanel` (previously it took
  no props — the iframe read `window.__xplorer_state__` instead).
- `apps/client/src/components/explorer/VerticalExtensionsBar.tsx`: removed the
  "Example review set in this deployment" flag now that the panel is real.
- `apps/client/src/locales/en.json` (+3 keys: `cocoindex`, `duckdb`, `duckdbSql`);
  `id.json`/`ja.json`/`zh.json` got the same 3 keys for parity but with
  **untranslated English text** — a deviation from this repo's own convention
  ("add new keys to ALL 4 locale files"); translation was out of scope for the
  time available.
- `pnpm-workspace.yaml`: fixed an `allowBuilds` stub pnpm auto-inserted with
  invalid placeholder values (`"set this to true or false"`) when installing the
  new grid packages; set to `true` for the five already-trusted packages
  (matches the pre-existing `onlyBuiltDependencies` list).
- New tests: `apps/client/src/__tests__/components/panels/ReviewDockPanel.test.tsx`
  (4 tests — no-selection line, real-row rendering, not-indexed flag, and an
  explicit assertion that EXIF/PDF text never appears from an empty lookup).

**New dependencies added** (flagged per instruction; not silently added):
`ag-grid-community@36.1.0`, `ag-grid-react@36.1.0`,
`@glideapps/glide-data-grid@6.0.3` — owner explicitly asked for both grid
libraries side by side (22:16 EDT). React stayed at whatever the fork already
pins (`^19.0.0` — this fork is React 19, unlike the separate `Intake/src` app
pinned to 18.3.1; the fork's own `CLAUDE.md` header says "React 18", which is
now stale against its own `package.json` — flagging the drift, not fixing it,
since it predates this session and touches a doc I wasn't asked to reconcile).

### Verification run (this session)

```
cd Intake/xplorer-copilot-buildkit/xplorer-copilot
npx tsc --noEmit                                            # exit 0, workspace-wide
npx eslint <7 changed files>                                # 0 errors, 4 stylistic warnings (nested ternary)
npx vitest run .../ReviewDockPanel.test.tsx .../RightSidebar.test.tsx .../IntakeFilesystemSearchPanel.test.tsx
  → 3 files, 29 tests, all passed
```

```
cd Intake/backend
.venv/Scripts/python.exe -m pytest tests/ -q --ignore=tests/test_cli_lifecycle.py
  → 119 passed
```

## Live index run — status, the bug found and fixed, and what remains

The lost agent's run (`run_id 8333fde9…`) had died with `files_observed: 245,
files_transformed: 225, failure_events: 7, state: running` — no process alive,
confirmed via `Get-CimInstance Win32_Process`. Its stale source lock
(`bbb9084e9…lock`, 20:44 EDT) was moved to
`backend/output/.source-locks/_stale/` (not deleted; the lock module itself
notes "stale lock files are harmless" since it's an OS-owned advisory lock
released on process exit).

**Resuming naively broke almost every file.** The first resume (no Weaviate env
vars set) went from 0 → ~93% failure rate almost immediately. Root cause, found
by extending the failure observer to log full tracebacks
(`run-status/failure-diagnostics.jsonl`, added this session — see backend
section above): `pipeline.py`'s CocoIndex flow only calls `declare_chunk(...)`
for the Weaviate target `if weaviate_target is not None`. The lost agent's
*original* run **had** `INTAKE_WEAVIATE_INDEX_ENABLED=1` set (confirmed live: a
real collection `IntakeXplorerLegalKB20260914` already existed on
`100.91.190.107:8082` with 892 objects from that run). My first resume omitted
those env vars, so CocoIndex's incremental reconciler tried to *tear down* the
previously-declared Weaviate target for every already-indexed file — and the
teardown path (`weaviate_target.py: apply_actions` → `context_provider.get
(WEAVIATE_WRITER)`) unconditionally needs a writer that this run never
provided, raising `KeyError` for every reprocessed file.

**Fix**: killed the broken run, restarted with the original Weaviate env vars
recovered from the live collection (`INTAKE_WEAVIATE_URL=http://
100.91.190.107:8082`, `INTAKE_WEAVIATE_COLLECTION=IntakeXplorerLegalKB20260914`,
`INTAKE_WEAVIATE_TEXT_VECTOR=text`, `INTAKE_WEAVIATE_EMBED_MODEL=nvidia/
nemotron-3-embed-1b`). Failures dropped to 0 immediately, then only genuine
content-level failures accumulated over the next ~2500s:

| # | File | Cause |
|---|---|---|
| 1–6 | large scraped-record files (voter records, CSV search exports) | NIM `nemotron-3.5-lightning-30b-a3b` summary hit `max_tokens=1600` before finishing valid JSON (`finish_reason: length`) — the source text is dense enough that the enrichment prompt's summary response gets cut off |
| 7 | `Copy your recovery code for safe keeping…` clipping | NIM returned `date_basis: null`; `DocumentEnrichment.date_basis` is typed `str` (no `| None`, no cleaning validator like the list fields have) — a real, fixable schema-strictness gap, not touched this pass |

**Current status (last checked, run still live in the background):**

```json
{
  "run_id": "87841a11e58f4e05bf0d11f7d4299217",
  "state": "running",
  "files_observed": 373,
  "files_transformed": 175,
  "failure_events": 7,
  "started_at": "2026-09-15T02:13:08Z"
}
```

stdout stats at the same moment: `process_file: 378 total | 123 added, 57
reprocessed, 189 unchanged, 7 errors`. Weaviate object count grew live from 892
→ 1154 during this session (`Aggregate { IntakeXplorerLegalKB20260914 { meta {
count } } }` via the collection's own GraphQL endpoint). The run was started
detached (`nohup … &`, disowned) and will keep running after this session ends;
it is NOT finished as of this receipt. Check with:

```
cat "Intake/backend/output/xplorer-live-20260914/run-status/$(ls -t Intake/backend/output/xplorer-live-20260914/run-status/*.json | head -1)"
```

or tail `Intake/backend/output/xplorer-live-20260914/.run-logs/resume-20260914-2226.log`.
**CocoIndex-semantic search (`/search`) and `/filesystem/lookup` will report
"not indexed"/`no_active_index_snapshot` until this run reaches `state:
finished` and the CLI writes an active snapshot** — that only happens once, at
the very end of a clean `index` run. Weaviate keyword/hybrid and the DuckDB SQL
method do NOT depend on that snapshot and already work today (evidence below).

## Live verification evidence

Backend (`casebible-corpus serve --host 127.0.0.1 --port 8765`, started with the
recovered Weaviate + `INTAKE_SURREAL_URL` env vars):

- `GET /filesystem/graph/status` → `{"status":"ready","version":"surrealdb-3.2.4+20260803.93ab219"}`
  (read-only; the concurrent Surreal-population agent was left untouched).
- `POST /filesystem/duckdb {"sql":"SELECT relative_path, title, document_type, byte_size FROM documents LIMIT 5"}`
  → 5 real rows from the live corpus (e.g. `Julie Ann Fleming from Clio,
  Michigan | VoterRecords.com`, `document_type: voter_registration`).
- `POST /filesystem/search {"query":"Clio Michigan","mode":"keyword"}` → 3 real
  BM25 hits from `IntakeXplorerLegalKB20260914`, full chunk text and scores
  (7.97, 7.93, 7.85).
- `POST /filesystem/search {"query":"custody hearing schedule","mode":"hybrid"}`
  → `Interim_Parenting_Time_Schedule.md` (0.972) and its `_DUPLICATE` sibling
  (0.965) — a genuinely relevant hybrid result.
- `POST /filesystem/duckdb {"sql":"DROP TABLE documents"}` and similar → rejected
  with `422` before touching DuckDB (unit-tested; not re-curled live to avoid
  wasting time on an already-proven negative).
- `GET /filesystem/lookup?path=…` and `POST /search` (CocoIndex) → currently
  `no_active_index_snapshot` (see index-run status above; expected, not a bug).

Frontend, deployed page (`https://homepage.tilapia-skilift.ts.net/progress/
intake/xplorer/`, portal frame is intentionally kept per owner's "portals are
fine" clarification — only the panel-level iframe was rejected):

- **Before**: "Review & metadata" tab carried a flag, `"Example review set in
  this deployment"`, and rendered a separate app's demo grid (`July incident —
  review`, `IMG_1842.HEIC`) inside an iframe-in-an-iframe.
- **After**: tab carries no flag. Clicking it with nothing selected renders,
  verbatim from the live page (`get_page_text`):
  ```
  Review & metadata

  No file selected.

  Not extracted by this backend yet:
  ⚠ Photo EXIF / XMP
  ⚠ HEIC internals
  ⚠ PDF info / XMP
  ⚠ Office document properties
  ⚠ Media (audio/video) tags
  ```
  No sample data anywhere. Browsing into `/b2/salem-data/...` only reached
  folders in this pass (an OpenList/B2 mount, several levels deep before any
  individual file) — selecting a real *file* to see the "found" success path
  render live was not reached in the time available; that path IS covered by
  the automated test (`ReviewDockPanel.test.tsx`, mocked `lookupPath`) and by a
  live backend curl equivalent (`/filesystem/duckdb` returning real rows).

## Known limitation, found live, not resolved this pass

**The deployed portal build cannot reach the backend at all — by design of its
own CSP, not a bug I introduced.** Confirmed live:

```
curl -sD- -o /dev/null https://homepage.tilapia-skilift.ts.net/progress/intake/xplorer/
→ Content-Security-Policy: default-src 'self'; ... connect-src 'self'; ...
```

`connect-src 'self'` blocks any `fetch()` to `http://localhost:8765` from that
page, full stop — confirmed by running `fetch('http://localhost:8765/health')`
in that exact page's own JS context via the browser tool, which returned
`TypeError: Failed to fetch`. This is **not new**: the pre-existing rg/keyword/
hybrid methods already only work through `TauriAPI.grepSearch`/`FilesystemIndex.
search`, both of which explicitly throw `"…requires the Intake desktop
connection"` when `isTauri()` is false — i.e. the web portal deployment has
never been able to search, before or after this session's changes. The Tauri
desktop app's own CSP (`apps/src-tauri/tauri.conf.json`) explicitly allows
`http://localhost:*` in `connect-src` (not `127.0.0.1` — CSP matches hostnames
literally, so I deliberately pointed `intake-backend.ts` at `localhost:8765`,
not `127.0.0.1:8765`, to land inside that existing allowance).

**What this means**: today, search and the metadata-lookup network call only
work inside the native Tauri desktop app, never in the browser-hosted portal
view — which matches the owner's own framing ("this isn't a portal, it's an
app"; the portal is fine to exist, it was just never meant to run the real
functionality). **I did not launch/verify the native Tauri desktop app this
pass** (a debug binary already exists at `apps/src-tauri/target/debug/
xplorer.exe` from an earlier session, but relaunching `scripts/start-intake.ps1`
and driving/screenshotting a native window was judged too slow and too failure-
prone to fit remaining time, versus the value of writing this receipt
accurately). This is the single most important "not done" item — see next
concrete test below.

## Not done / deferred

- **Native Tauri desktop verification.** Everything above is verified either
  by direct backend curl (real, unambiguous) or by loading the deployed *web*
  build (which cannot reach the backend by CSP design, as just explained). The
  actual end-to-end "select a file in the app → see real metadata; type a query
  → see real search results" loop has only been verified in pieces (backend
  live, frontend unit-tested against a mocked backend) — not as one live click-
  through inside the real desktop app.
- **Surreal graph tab / query UI.** The adapter (`graphNeighbors`, `graphStatus`)
  exists and `/filesystem/graph/status` was verified live, but no panel renders
  it yet — directive slice 4.
- **Weaviate parameter drawer + collection/index tab with freshness** — directive
  slice 2, not started.
- **CocoIndex run controls / receipts UI** — directive slice 5, not started.
- **rg tweaks** (context lines, max results, hidden files, glob include/exclude,
  case/word toggles) beyond the existing single free-text query — the
  Rust `grep_search` command itself doesn't expose these yet either.
- **`DocumentEnrichment.date_basis` schema-strictness bug** (see failure #7
  above) — real, found live, not fixed.
- **Large main JS chunk** (`index-*.js`, ~3 MB / 902 KB gzipped) after adding
  ag-grid + Glide — `IntakeFilesystemSearchPanel` is statically imported into
  `LeftSidebar`, so the new grid libraries didn't get their own lazy chunk.
  Works, but is a legitimate follow-up (route `ResultsGrid` through
  `React.lazy`).
- **id/ja/zh locale files** carry the 3 new keys in English, not translated.
- **`docs/MASTER-TODO.md`, `docs/UNIFIED-WORKBENCH-PLAN.md`,
  `../docs/DEVELOPMENT.md`, `../docs/HANDOFF-2026-09-11-…`, `../src/app/App.tsx`**
  show as modified in `git status` but were NOT touched by this session — they
  were already dirty at session start (visible in the conversation's initial
  git-status snapshot) and are presumably another agent's in-flight work;
  reported here only so nothing looks silently swept in.

## Guesses / assumptions made

- The Weaviate collection name/vector/embed-model for the resumed index run
  were **recovered by inspection** (live schema + object query against
  `100.91.190.107:8082`), not told to me directly — the lost agent never left a
  record of them. High confidence: `source_id` inside a sampled object exactly
  matched `diskdrill-legal-kb-20260914`.
- `http://localhost:8765` as the backend adapter's default assumes the browser
  viewing the native app and the machine running `casebible-corpus serve` are
  the same machine — true for this single-user desktop today, per the existing
  "personal tailnet, keep it simple" pattern, but worth stating explicitly.
- Grid engine choice defaults to Glide Data Grid on first load (arbitrary; both
  are equally one click away).

## Files changed

**Backend** (`Intake/backend`):
- `src/casebible_index/search.py`, `api.py`, `models.py`, `pipeline.py`
- `pyproject.toml`, `uv.lock`
- `tests/test_lookup_and_lake.py` (new)
- `output/xplorer-live-20260914/**` (live run artifacts; not source)

**Xplorer fork** (`Intake/xplorer-copilot-buildkit/xplorer-copilot`):
- `apps/client/src/lib/intake-backend.ts` (new)
- `apps/client/src/components/panels/ResultsGrid.tsx` (new)
- `apps/client/src/components/panels/ReviewDockPanel.tsx` (rewritten)
- `apps/client/src/components/panels/RightSidebar.tsx`
- `apps/client/src/components/explorer/VerticalExtensionsBar.tsx`
- `apps/client/src/components/explorer/IntakeFilesystemSearchPanel.tsx`
- `apps/client/src/locales/{en,id,ja,zh}.json`
- `apps/client/src/__tests__/components/panels/ReviewDockPanel.test.tsx` (new)
- `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`

**VPS ovh-app** (`/data/dashboards/progress-board/`):
- `intake-build/releases/2026-09-15T02-48-01-000Z/` and
  `2026-09-15T02-50-44-000Z/` (new; `xplorer/` = this session's build twice,
  second time after the `localhost` CSP fix; `metadata/` carried forward
  byte-for-byte unchanged from `2026-09-14T21-34-12-000Z`, since nothing
  references it from the app anymore but "no deletes" applies)
- `intake-build/current.json` (points at `2026-09-15T02-50-44-000Z`; backup
  `current.json.bak-20260914-native-metadata-search` kept)
- No Coolify restart was needed or performed — `server.mjs` reads
  `current.json` fresh on every request (confirmed by reading its source), and
  the live page was observed serving the new release without one.

## Next concrete test for the owner

1. **Launch the native desktop app** (`Intake/xplorer-copilot-buildkit/
   xplorer-copilot/scripts/start-intake.ps1`) with `casebible-corpus serve`
   running (`cd Intake/backend && INTAKE_WEAVIATE_URL=http://100.91.190.107:8082
   INTAKE_WEAVIATE_COLLECTION=IntakeXplorerLegalKB20260914
   INTAKE_WEAVIATE_TEXT_VECTOR=text
   INTAKE_WEAVIATE_EMBED_MODEL=nvidia/nemotron-3-embed-1b
   INTAKE_SURREAL_URL=https://surreal-intake.tilapia-skilift.ts.net
   .venv/Scripts/python.exe -m casebible_index.cli serve`), select a real file
   under `F:\Disk Drill\Legal_Knowledge_Base_Obsidian`, open "Review & metadata",
   and confirm it shows the real catalog row (title/type/summary/duplicates) —
   this is the one loop this session could not click through live.
2. Once the background index run reaches `state: finished` (poll the run-status
   file above), try the new **cocoindex** search method and confirm `/filesystem/
   lookup` returns `found: true` instead of `no_active_index_snapshot`.
3. Try the **duckdb** method with something like `SELECT document_type,
   count(*) FROM documents GROUP BY document_type ORDER BY 2 DESC` to see the
   corpus's real document-type breakdown in the grid, and toggle between Glide
   and AG Grid to compare them as requested.
