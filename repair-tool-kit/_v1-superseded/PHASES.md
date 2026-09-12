# Build Phases — casekit

Single workstream (see `SPLIT.md`). Every phase has a checkable exit criterion.
Phases 0–6 are the usable product. 7+ are deferred under R5.

---

## Phase 0 — Preflight
**Goal:** Prove the toolchain works on the target machine before any feature code.
**Exit criterion:** `go version` reports 1.26.x; `go build ./cmd/casekit` produces
both `casekit.exe` and `casekitw.exe`; running `casekitw.exe` from a shell verb
on a test `.pdf` produces **no visible console flash**; `duckdb` loads the
`webbed` extension successfully.
**Gotchas:** A-6

## Phase 1 — Engine registry and contract
**Goal:** Discover engines from manifests, invoke them, parse responses.
**Exit criterion:** `casekit doctor` prints a table of every discovered engine
with resolved path, reported version, declared capabilities, and OK/FAIL — and
it works for at least one `oneshot` engine (poppler) and one `worker` engine
(pypdf), proving both modes against the same contract.
**Gotchas:** A-7, B-4

## Phase 2 — Profile
**Goal:** Cheap pre-extraction classification of a file.
**Exit criterion:** `casekit profile <file>` emits JSON with `size`, `fmt`,
`images`, `chars`, `conversation`, `source`, `symbol_font`, `fonts_embedded`,
and returns correct values for **both** reference files —
`_18102689630.pdf` → `source: "Stirling-PDF v1.1.1"`, `symbol_font: true`,
`images: 0`, `conversation: true`; `sms-2022…xml` → `source:
"SMS Backup & Restore v10.18.001"`, `conversation: true`, 231 messages.
**Gotchas:** S-4

## Phase 3 — Routing and confidence check
**Goal:** Pick one engine from the profile; grade its output; escalate on failure.
**Exit criterion:** Given the reference PDF, routing selects poppler and the
check passes. Given a forced run with mutool, the `symbol_glyph_count` check
**fails** and the run escalates to the next engine automatically. The routing
table is a hand-editable config file, not compiled in.
**Gotchas:** S-2, S-5

## Phase 4 — PDF extraction
**Goal:** Produce `extraction.json` for a PDF, with the raw-stream channel.
**Exit criterion:** On the reference transcript, output contains all 33 symbol
glyphs as U+25A0 with `emoji_count` per run and
`emoji_identity: "unavailable"`; all 10 `[Attachment(s): …]` references appear
as elements with `resolved: false`; and the `Love you`+4-glyph run — invisible
to every text extractor — is present via the raw content-stream channel.
**Gotchas:** S-5, S-6, A-1, B-1

## Phase 5 — XML extraction (slim pass + DuckDB)
**Goal:** Two-stage SMS/MMS ingestion.
**Exit criterion:** On the reference XML, the slim pass extracts **8 blobs**
(2,822,412 bytes total) to `blobs/<sha256>`, reduces 3,852,198 → ~90,000 bytes,
and sets `data_sha256` on **all 14** parts. DuckDB then yields exactly 231
messages / 14 parts / 12 addrs, with row 227 showing `direction: received`,
`body_present: false`, `from:18102959303`, `to:8102959302`, and three
`image/jpeg` blobs. Parquet written for all three tables.
**Gotchas:** S-1, S-3, S-4, S-7, A-2, A-3, A-5, B-2

## Phase 6 — Package and seal
**Goal:** Bundle original + extraction + blobs + reports into a verifiable unit.
**Exit criterion:** `casekit package <file>` produces a directory containing
`original/` (byte-identical — hash before and after must match), `extracted/`,
`blobs/`, `reports/`, `MANIFEST.json`, and `SHA256SUMS`. Verification succeeds
using **only** `sha256sum -c SHA256SUMS` with no casekit binary present. A
ledger line is appended. The source file's hash is unchanged.
**Gotchas:** R6 (Rules), A-7

---

## Deferred — do not build until asked

## Phase 7 — Shell menu installer
Registry cascade under `HKCU\Software\Classes\SystemFileAssociations\`,
generated from `menu.json`; uninstall script tested first.
**Exit criterion:** right-click a PDF → "Package & extract" → package appears;
uninstall script removes every key it added, verified by registry diff.
**Gotchas:** B-3, A-6

## Phase 8 — Daemon + tsnet
`casekit serve --tsnet` joins the tailnet; HTTP API per `SPLIT.md`.
**Exit criterion:** OVH instance reachable from the workstation over the
tailnet only, caller identity resolved via `LocalClient.WhoIs`, `/v1/healthz`
returns engine inventory, and the service is unreachable from the public
internet.

## Phase 9 — Review UI
Two queues: files with `issues`, plus a random sample of clean ones.
**Exit criterion:** original and extraction side by side, next/prev, thumbs
up/down writes to the ledger.

## Phase 10 — Additional formats
Screenshots (OCR), Facebook JSON, call logs, DOCX. One format per pass, each
adding a route line and an engine. Do not start until Phases 0–6 are in use on
real files.
