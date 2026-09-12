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
Every element whose value was not read from a structured field carries a
`derivation` block per `docs/DERIVATION.md` — level, why, `derived_from` with
byte offsets, method, assumptions, and `not_established`. Every flag states
why it fired. A bare label with no reasoning fails this phase (RULES R11).
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

## Phase 5b — JSON extraction (Facebook / Instagram / generic)
**Goal:** Structured conversation exports in JSON, same shape as Phase 5's output.
**Exit criterion:** Given a Facebook/Instagram message export directory,
`casekit extract <dir>` unions all `message_*.json` files into one thread,
emits the same `messages` / `parts` / `addrs` table shape as Phase 5, and
correctly repairs mojibake — a name or message containing non-ASCII decodes to
the right characters rather than `Ã©`-style sequences, and emoji survive as
real codepoints. Media references resolve against the export's `photos/`,
`videos/`, `audio/`, `gifs/` folders where present; where absent they appear as
`resolved: false` with `declared_uri` set. Direction is derived from
`sender_name` against the account owner and recorded with
`confidence: "derived"`.
**Gotchas:** S-8, S-9, A-8, A-9, A-10, B-5

## Phase 5d — HTML and text exports
**Goal:** The formats the PDF transcripts were *made from*. Same table shape as
Phases 5 and 5b.

HTML sits above PDF in source preference because it is upstream of it — the
reference PDF was produced by Stirling-PDF from HTML, and that conversion is
where the emoji died (GOTCHAS S-15). Recovering the HTML recovers the emoji for
a whole conversation at once.

**Exit criterion:** Given an HTML message export, casekit parses it as a **DOM**
(never regex), detects the exporter from its markup signature, and emits
messages in the Phase 5 shape. Emoji are recovered in all three forms — literal
character, HTML entity, and `<img>` with the emoji in `alt`/`title` — with
`emoji_source` recorded per occurrence. Inline `data:` base64 images route
through the generic blob pass; relative `src` paths resolve against the sibling
folder or flag `resolved: false`. Charset is determined BOM-first, then
detection, then declaration, with the winning method recorded and marked
`estimated`. Given a flat text export, messages parse with
`confidence_level: "header_derived"` and a populated `not_established`.

Where an HTML and a PDF cover the same conversation, the HTML supersedes; the
supersession is recorded and the PDF package is **not** deleted (RULES R6).
**Gotchas:** S-15, A-17, A-18, B-8, B-9, S-13, A-8

## Phase 5c — ZIP containers (unwrap, recurse, repair)
**Goal:** Treat archives as containers first and repair targets second. Most
evidence arrives zipped — Meta exports, phone backups, discovery productions —
so unwrapping and routing the contents is the common case.
**Exit criterion:** Given a zip containing a mix of PDF, XML and JSON, casekit
extracts members to a scratch dir, profiles and routes **each member
independently**, and produces one package whose manifest lists every member
with its own extraction. Recursion depth and total-expansion limits are
enforced and configurable. A member whose name escapes the extraction root is
refused, not written. A zip whose central directory omits entries present in
the local headers still yields those entries via the second channel, and the
discrepancy is recorded as a finding rather than silently resolved.
**Gotchas:** S-10, S-11, S-12, A-11, A-12, A-13, B-6

## Phase 6 — Package and seal
**Goal:** Bundle original + extraction + blobs + reports into a verifiable unit.
**Exit criterion:** `casekit package <file>` produces a directory containing
`original/` (byte-identical — hash before and after must match), `extracted/`,
`blobs/`, `attachments/`, `reports/`, `MANIFEST.json`, and `SHA256SUMS`.
Every base64 payload found anywhere in the source is decoded, type-identified
by magic bytes, written to `blobs/<sha256>`, and **also** copied into
`attachments/` under its real filename with the correct extension, so the
package can be browsed without decoding hashes. `blobs/INDEX.md` maps every
hash to declared name, declared type, detected type, size and owning message.
`reports/DERIVATIONS.md` lists every derived claim and every flag in the
package in plain English with its byte-level basis, readable by someone who has
never seen casekit. Verification succeeds
using **only** `sha256sum -c SHA256SUMS` with no casekit binary present. A
ledger line is appended. The source file's hash is unchanged.
**Gotchas:** R6 (Rules), A-7

## Phase 6b — Corpus index and corroboration coverage
**Goal:** One queryable table across every package and every format, plus a
measurement of which messages have independent support from a second source.
The index is **derived and disposable** — rebuildable from the packages at any
time, never authoritative.

Three jobs:

1. **Unify.** DuckDB globs `packages/*/extracted/*.parquet` and
   `*/pdf_messages.json` into one `messages` view. Includes a
   `pdf_transcript_to_messages` normalizer that turns header-delimited PDF
   transcript text into message rows. Every row carries `source_format`,
   `package_id`, and its full `confidence` block — never flattened.

2. **Corroborate.** Match messages across sources and record links with a
   stated basis (RULES R11): `exact` (identical attachment SHA-256, or
   normalized body hash), `timestamp` (same normalized participants within a
   configurable window), `content` (fuzzy body match). Each link carries its
   own `why` and `not_established`.

3. **Report.** Per thread and date range: corroboration coverage, uncorroborated
   spans, and **disagreements** — same participants and timestamp, different
   body, or a message present in one source and absent from another. A
   disagreement is a finding, surfaced, never auto-resolved.

**Exit criterion:** `casekit index` builds a DuckDB database over every
package. `SELECT source_format, count(*) FROM messages GROUP BY 1` returns rows
for each format present. Every row retains its `confidence_level` and
`not_established`. `casekit coverage --thread <id>` emits an HTML report showing
corroborated percentage, a timeline of gaps, and any disagreements. Against the
two reference files specifically — which share no party and no date range — the
report must correctly show them as **disjoint threads with 0% cross-source
corroboration**, rather than inventing matches. Deleting the index and
re-running reproduces it byte-for-byte from the packages alone.
Every uncorroborated derived value carries a `remediation` block (RULES R11):
what would corroborate it, a concrete searchable spec (time window, party,
attachment name or hash, text fragment), and a `status` of `open` / `resolved`
/ `accepted`. `casekit gaps` emits the open queue, ranked by how much each
would add. `casekit accept <id> --reason "…"` closes one without deleting it.
**Gotchas:** A-3 (address normalization), A-4 and B-5 (timestamp comparison
across sources with different timezone handling), S-13

## Phase 6c — Screenshot pile index
**Goal:** Make an unsorted image pile searchable so corroboration can be
proposed rather than hunted by hand. ~10,000 images is not a manual sorting
job.

Index each image once: SHA-256, EXIF `DateTimeOriginal` and any Samsung/editor
provenance (see `FINDINGS.md` — one reference blob carries its original
screenshot path, capture timestamp and crop geometry), filename-embedded
timestamps (`Screenshot_20221103-210020_*`), dimensions, and OCR text via
tesseract. Store as Parquet beside the corpus index.

Then the Phase 6b matcher proposes candidates instead of requiring a search:
for any `open` gap, rank images by **distinctive-keyword hits in OCR text
first**, timestamp proximity second. A screenshot's EXIF timestamp records when
the screenshot was taken, not when the message was sent, and the two are
routinely months apart (GOTCHAS A-16) — so content is the primary signal and
time is a tiebreak.

Keywords are selected by inverse corpus frequency, not by eye: proper nouns,
brand names, place names and misspellings discriminate; common words do not.
Each term's corpus frequency is recorded alongside the match so a reader can
see why it was considered strong.

**Exit criterion:** `casekit images index <dir>` builds a Parquet index over a
directory of images with hash, best-available timestamp (and which source it
came from, marked per R11), dimensions and OCR text. `casekit keywords <thread>`
emits per-message distinctive terms with corpus frequencies. `casekit gaps
--propose` returns ranked candidate images for each open gap, ranked by keyword
hits first and time second, with the match basis and which signal drove it
stated. A candidate whose timestamp is months from the message is still
proposed when its OCR content matches.
Accepting a proposal writes a corroboration link and flips the gap to
`resolved`; rejecting it records the rejection so the same image is not
proposed again.
**Gotchas:** A-16 (screenshot time ≠ message time), A-4, B-5 (EXIF timestamps
carry their own timezone problems), S-13

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
Screenshots (OCR), call logs, DOCX/OOXML (which are zips — Phase 5c does the
container half already). One format per pass, each
adding a route line and an engine. Do not start until Phases 0–6 are in use on
real files.
