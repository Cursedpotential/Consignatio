# Task Prompts — casekit

Copy-paste one per phase into Claude Code. Each assumes the working directory
is the repo root and that `RULES.md`, `STACK.md`, and `GOTCHAS.md` are present.

**Every prompt begins with the same preamble. Do not drop it.**

> Read `RULES.md` first and follow it. In particular: guidance is not rules —
> do not add rules to any file; nothing is created without approval; ask
> questions before building, not after.

---

## Phase 0

```
Read RULES.md, then STACK.md.

Set up the casekit repo skeleton in Go 1.26 at the current directory.
Create:
  cmd/casekit/main.go        - console entry point
  cmd/casekitw/main.go       - GUI-subsystem entry point (no console window)
  internal/config/config.go  - TOML config load, install root D:\case_apps
  go.mod                     - module casekit
  Makefile or Taskfile       - build targets for windows/amd64 and linux/amd64

Read GOTCHAS.md A-6 before writing the build targets: casekitw.exe MUST be
built with -ldflags "-H windowsgui" or it flashes a console on every
context-menu invocation.

Both binaries should accept `--version` and print the build version only.

EXIT CRITERION: `go build ./...` succeeds; both binaries produced; running
casekitw.exe --version from a shortcut produces no visible console window;
`duckdb -c "INSTALL webbed FROM community; LOAD webbed;"` succeeds.

Verify with: go vet ./... && go build ./... && ./casekit.exe --version
Do not proceed past this phase without asking.
```

## Phase 1

```
Read RULES.md, then SPLIT.md (engine contract section) and GOTCHAS.md A-7, B-4.

Implement the engine registry in internal/engine/:
  registry.go   - discover engines by scanning engines/*/engine.toml
  contract.go   - Request/Response types exactly as specified in SPLIT.md
  oneshot.go    - spawn per call, write JSON to stdin, read JSON from stdout
  worker.go     - resident process, NDJSON loop, bounded pool, timeout kill
  doctor.go     - probe every engine, report version + capabilities

Then create two engines to prove both modes:
  engines/poppler/engine.toml   - mode="oneshot", wraps pdftotext
  engines/pypdf/engine.toml     - mode="worker", frozen uv venv
  engines/pypdf/eng_pypdf.py    - NDJSON loop implementing extract_text

Paths in the contract are opaque absolute strings. Test with a path containing
a space and a non-ASCII character (GOTCHAS A-7).

EXIT CRITERION: `casekit doctor` prints a table with each engine's resolved
path, reported version, capabilities, and OK/FAIL — and both the oneshot and
worker engines report OK.

Verify with: casekit doctor
```

## Phase 2

```
Read RULES.md and GOTCHAS.md S-4.

Implement internal/profile/profile.go. Given a file path, produce JSON with:
  size, sha256, fmt, pages, images, chars, conversation, source,
  symbol_font, fonts_embedded

Detection: magic bytes, not extension. For PDF shell out to pdfinfo, pdffonts,
pdfimages -list, pdftotext. For XML read the leading comment for the producer
string. NEVER parse XML with regex (GOTCHAS S-4).

Reference files are in docs/reference/. The profile must return:
  _18102689630__1___1_.pdf ->
     source "Stirling-PDF v1.1.1", pages 24, images 0, symbol_font true,
     fonts_embedded false, conversation true, chars ~23257
  Copy_of_sms-20221104021809.xml ->
     source "SMS Backup & Restore v10.18.001", conversation true, 231 messages

EXIT CRITERION: `casekit profile <each reference file>` returns exactly those
values.

Verify with: casekit profile docs/reference/*.pdf docs/reference/*.xml
```

## Phase 3

```
Read RULES.md, GOTCHAS.md S-2 and S-5.

Implement internal/route/:
  routes.toml   - hand-editable ordered rule list, NOT compiled in
  route.go      - first matching rule wins, returns ranked engine list
  check.go      - confidence checks

Seed routes.toml with:
  [[route]] when = {fmt="pdf", images=0, conversation=true}
            rank = ["poppler","pypdf","pdfium"]
            avoid = ["mutool"]
            checks = ["symbol_glyph_count","char_volume","replacement_chars"]

symbol_glyph_count: if profile.symbol_font is true, count symbol-font show
operations in the content stream and require at least that many non-ASCII
characters in the engine output. This is the check that catches mutool
returning "I" and pdfminer returning "n" (GOTCHAS S-2, S-5).

On check failure, escalate to the next engine in rank and log the escalation.

EXIT CRITERION: routing the reference PDF selects poppler and passes. Forcing
`--engine mutool` on the same file FAILS symbol_glyph_count and auto-escalates.

Verify with: casekit extract --dry-run docs/reference/*.pdf
             casekit extract --engine mutool docs/reference/*.pdf
```

## Phase 4

```
Read RULES.md, GOTCHAS.md S-5, S-6, A-1, B-1.

Implement internal/extract/pdf.go producing extraction.json per the envelope
in docs/SCHEMA.md. Two parallel channels:

1. Text channel - the routed engine (poppler), producing text_run elements
   with page, byte offset, length, sha256.
2. Raw-stream channel - qpdf --qdf, scan text-showing operators directly.
   Run this whenever profile.symbol_font is true. It is NOT a fallback;
   it runs alongside (GOTCHAS S-6 - the "Love you"+4-glyph run is invisible
   to every text extractor but present in the content stream).

For symbol-font runs emit: emoji_count = glyph count in that run,
emoji_identity = "unavailable". Never drop them, never guess (RULES R7).

Attachment references matched from text as [Attachment(s): name] become
elements with kind="attachment_ref", resolved=false, declared_name set
(GOTCHAS A-1).

EVERY value not read from a structured field gets a derivation block per
docs/DERIVATION.md: level, why (one plain sentence), derived_from (element IDs
WITH byte offsets), method (plain + machine), assumptions, not_established.
Every flag states why it fired. A bare confidence label with no reasoning is a
failed phase (RULES R11). not_established is the field most likely to be
skipped - fill it every time.

For this file that means each header-derived message records that the sender
came from printed text rather than a structured field, and that the emoji
identity, the attachment bytes and the timezone are NOT established.

EXIT CRITERION on docs/reference/_18102689630__1___1_.pdf:
  - 33 symbol glyphs present as U+25A0
  - 22 distinct symbol show-operations recorded
  - 10 attachment_ref elements, all resolved=false
  - the "Love you" 4-glyph run present via the raw-stream channel
  - source file sha256 unchanged after the run
  - every derived value carries a derivation block with derived_from byte
    offsets and a populated not_established list

Verify with: casekit extract docs/reference/*.pdf && \
  jq '[.elements[]|select(.kind=="attachment_ref")]|length' out/extraction.json
```

## Phase 5

```
Read RULES.md, GOTCHAS.md S-1, S-3, S-4, S-7, A-2, A-3, A-5, B-2.

Implement XML ingestion as TWO stages. Do not skip stage 1.

Base64 decoding is a GENERIC pass in internal/blob/base64.go, not an XML-only
step - JSON, HTML data: URIs and .eml all reuse it. Read its TODO before
starting. Key points: identify type by MAGIC BYTES not declared ct (the
reference export declares image/png on JPEG bytes); record declared_type and
detected_type as two fields; on a length mismatch still write the bytes but
mark status:"partial" and classify "reconstructed" not "recovered".

Stage 1 - slim pass (engines/duckxml, Python + lxml):
  For every <part>: if data= present, base64-decode, write to
  blobs/<sha256>, delete the data attribute, set data_sha256 and data_bytes.
  If data= is ABSENT, still set data_sha256="" and data_bytes="0".
  That last part is mandatory - DuckDB infers struct schemas from a sample and
  will silently omit the field otherwise, losing every image (GOTCHAS S-1).
  Write slim.xml.

Stage 2 - DuckDB over slim.xml:
  read_xml() into three tables: messages, mms_parts, mms_addrs.
  NEVER use xml_extract_attributes for bulk work - it consumed 3.1 GiB on a
  3.8 MB file (GOTCHAS S-3).
  Decode codes per docs/CODES.md but ALSO persist raw_code (GOTCHAS B-2).
  Capture every attribute including ones absent from the official XSD
  (GOTCHAS A-5). Keep body_present separate from body_is_null (S-7).
  Retain raw address strings verbatim (A-3).
  Write Parquet for all three tables.

EXIT CRITERION on docs/reference/Copy_of_sms-20221104021809.xml:
  - 8 blobs, 2,822,412 bytes total
  - slim.xml under 100,000 bytes (source is 3,852,198)
  - data_sha256 present on all 14 parts
  - 231 messages, 14 mms_parts, 12 mms_addrs
  - row 227: direction=received, body_present=false,
    from:18102959303, to:8102959302, three image/jpeg blobs

Verify with: casekit extract docs/reference/*.xml && \
  duckdb -c "SELECT count(*) FROM 'out/messages.parquet'"
```

## Phase 6

```
Read RULES.md - especially R6 (never destroy an original) and R9 (recovered vs
reconstructed are never interchangeable).

Implement internal/pkg/ and internal/ledger/.

casekit package <file> produces:
  <pkg-id>/
    README.txt        plain-English: what this is, how to verify with stock tools
    original/<name>   byte-identical copy
    extracted/        extraction.json, text/, metadata/, structure/
    blobs/<sha256>
    reports/          profile.json, route.json, checks.json, casekit.log
    attachments/      SAME payloads under real filenames with the correct
                      extension from the DETECTED type, collision-suffixed.
                      A folder of 64-char hashes cannot be reviewed by a human;
                      this is the browsable view (GOTCHAS B-7).
    blobs/INDEX.md    hash -> declared name, declared type, detected type,
                      size, owning message
    MANIFEST.json     every file INCLUDING attachments/: path, size, sha256, mtime
    SHA256SUMS        same data, sha256sum-compatible

Package id = sha256 of the zipped directory. Append one line to the ledger
(JSONL) with package id, source sha256, engine, checks, timestamp.

Verification must work with NO casekit binary present - `sha256sum -c
SHA256SUMS` alone must pass. README.txt states the exact commands.

EXIT CRITERION: package both reference files. All 8 blobs from the XML appear
in BOTH blobs/ (by hash) and attachments/ (by real filename, correct extension,
openable). blobs/INDEX.md lists all 8. For each, the source file's
sha256 is identical before and after. `sha256sum -c SHA256SUMS` passes inside
the package directory. The ledger has one new line per package.

Verify with: sha256sum docs/reference/* > /tmp/before.txt
             casekit package docs/reference/*
             sha256sum -c /tmp/before.txt
             cd out/<pkg-id> && sha256sum -c SHA256SUMS
```

## Phase 5b

```
Read RULES.md, then GOTCHAS.md S-8, S-14, S-9, A-8, A-9, A-10, B-5.

Implement JSON conversation extraction in internal/extract/json.go plus
engines/duckjson/. Target: Facebook and Instagram message exports, and generic
JSON/JSONL conversation files.

Output MUST use the same table shape as Phase 5 (messages / parts / addrs) so
both formats land in one queryable corpus.

Stage 1 - normalize pass (engines/duckjson/normalize.py):
  a) Glob EVERY message_*.json in the thread directory and union them. They are
     not in chronological order; higher numbers are usually older (GOTCHAS A-9).
  b) Repair mojibake at BYTE level, BEFORE json.loads:
         fixed = re.sub(rb'\\u00([\da-f]{2})',
                        lambda m: bytes.fromhex(m[1].decode()), raw_bytes)
         data  = json.loads(fixed)
     Meta writes UTF-8 bytes as latin-1 then escapes them, so a naive parse
     yields "Ã©" with NO error (GOTCHAS S-8). Documented since 2018, still
     unfixed. There is no export setting and no alternative parser - the JSON
     is valid, it just contains the wrong characters.

     Use byte-level, NOT the post-parse s.encode('latin-1').decode('utf-8')
     form. Post-parse works on current exports but breaks on mixed content: one
     correctly-encoded character above U+00FF makes it raise, and the usual
     try/except then passes the WHOLE string through unfixed, mojibake included.

     Do NOT use the widely-copied SO answer that pairs \u00xx sequences two at
     a time. Emoji are 4-6 sequences, not 2. Verified: it turns the gem emoji
     into "P" and the heart into garbage, with no error (GOTCHAS S-14).
     Consume runs of ARBITRARY length and decode the whole run as UTF-8.

  b2) Run ftfy.fix_text() AFTER the byte fix, as a DETECTOR only. ftfy is built
     to avoid false positives and leaves correct text alone, so if it still
     changes a string, something else is wrong with that string - FLAG it,
     do not silently accept the change.

     Emoji are evidence in this corpus (see GOTCHAS S-5 for what the PDF path
     already did to them). Test b) and b2) explicitly on a message known to
     contain one.
  c) Normalize sparse keys: ensure EVERY message object carries photos, videos,
     audio_files, gifs, sticker, share, reactions, call_duration - empty where
     absent. Same reason as the XML slim pass (GOTCHAS S-9).
  d) Resolve media: each uri is relative to the export root. Present -> hash to
     blobs/<sha256>. Absent -> resolved:false with declared_uri set. A missing
     file is NOT a missing attachment (GOTCHAS A-8).
  e) Write normalized.jsonl.

Stage 2 - DuckDB over normalized.jsonl:
  read_json with an EXPLICIT columns={...} struct. Do not rely on inference.
  Run DESCRIBE and assert every expected field is present before extracting.

  Map to the Phase 5 shape:
    sender_name       -> addrs role=from, verbatim, never normalized away
    participants[]    -> addrs role=to
    timestamp_ms      -> date_epoch_ms (authoritative, no timezone - GOTCHAS B-5)
    content           -> body; body_present false when absent
    photos/videos/... -> parts with data_sha256 or resolved:false
    reactions[]       -> parts kind="reaction", actor + emoji preserved
    direction         -> DERIVED from sender_name vs account owner, and tagged
                         confidence:"derived" NEVER "structured" (GOTCHAS A-10)

EXIT CRITERION: given a real export directory, all message_*.json are unioned
into one chronologically sorted thread; a message containing non-ASCII decodes
to correct characters (not Ã©-style); a 4-byte emoji and a 6-sequence emoji
(heart + variation selector) BOTH survive as correct single codepoints;
ftfy run afterwards reports no further changes; media
present on disk resolves to blobs, media absent appears as resolved:false with
declared_uri; direction is present and tagged confidence:"derived".

Verify with: casekit extract <export-dir> && \
  duckdb -c "SELECT direction, count(*) FROM 'out/messages.parquet' GROUP BY 1" && \
  duckdb -c "SELECT body FROM 'out/messages.parquet' WHERE body ~ '[^\x00-\x7F]' LIMIT 5"

NOTE: these gotchas are marked [expected], not [observed] - they are documented
exporter behaviour but have not been reproduced against Matt's own files. Verify
each one on the first real export and report what actually happened.
```

## Phase 5c

```
Read RULES.md, then GOTCHAS.md S-10, S-11, S-12, A-11, A-12, A-13, B-6.

Implement ZIP container handling in internal/container/zip.go.

ZIP is a CONTAINER, not a leaf format. The common case is Meta exports, phone
backups and discovery productions arriving zipped. Unwrap and route the
contents. Repair is the fallback, not the default.

This makes the pipeline RECURSIVE. Build the recursion deliberately:

  zip -> extract members to scratch -> profile EACH member -> route EACH member
      -> a member may itself be a zip -> recurse (bounded)

TWO CHANNELS, same pattern as the PDF path:
  1. Go archive/zip - central directory, fast, correct for healthy archives.
  2. Local-header scan - search for PK\x03\x04 signatures directly.
  Compare them. archive/zip NEVER scans local headers, so an entry present
  locally but absent from the central directory is invisible to channel 1
  (GOTCHAS S-12). A discrepancy between channels is a FINDING recorded in the
  manifest with both counts - not an error, not silently reconciled.

HARD SAFETY, all configurable, all enforced before any write:
  - Reject any member whose resolved destination leaves the extraction root.
    Reject absolute paths. Reject "..". REFUSE, do not sanitize - a malicious
    name is a finding (GOTCHAS S-10). Go's archive/zip does NOT check this.
  - Cap total bytes written, per-member compression ratio, and recursion depth
    (default 3). Track cumulative expansion across the WHOLE recursion, not per
    archive (GOTCHAS S-11).

Extract by INDEX, not by name - duplicate names are legal and overwriting
silently loses data. Content-address every member to blobs/<sha256>, keep the
declared name as metadata (GOTCHAS A-12).

Filename encoding: honour general-purpose flag bit 11 for UTF-8. When unset and
bytes are non-ASCII, store raw bytes alongside a best-effort decode marked
"estimated" (GOTCHAS A-11, RULES R7).

Repair ladder (engines/ziprepair/, escalate ONLY on failure - GOTCHAS A-13):
  diagnose: unzip -t, zipdetails --scan   (writes nothing)
  tier 1:   zip -FF in.zip --out out.zip
  tier 2:   ziptail
  tier 3:   bsdtar  (native tar.exe on Windows 10+, independent parser)
  tier 4:   7z x -y (partial salvage)
  tier 5:   carve PK\x03\x04 signatures
Verify per-member with CRC + SHA-256, not exit codes. A repaired archive has a
different archive hash by definition; the claim is "same members, same
contents" - never "same file" (RULES R9).

EXIT CRITERION: a zip containing PDF + XML + JSON produces ONE package whose
manifest lists every member with its own extraction; depth and expansion limits
are enforced and configurable; a member named ../../evil.txt is REFUSED and
recorded; a zip whose central directory omits a locally-present entry still
yields that entry via channel 2, with the discrepancy in the manifest.

Verify with: casekit extract test/fixtures/mixed.zip && \
  jq '.members|length' out/*/MANIFEST.json
  casekit extract test/fixtures/zipslip.zip   # must refuse, exit nonzero
  casekit extract test/fixtures/nested-bomb.zip  # must abort at depth/ratio cap

Build the three fixtures yourself as part of this phase.
```

## Phase 6b

```
Read RULES.md - especially R11 (every derived value shows its work) and R1
(the index is derived, never authoritative). Then GOTCHAS.md A-3, A-4, B-5, S-13.

Implement internal/index/ plus internal/index/corpus.sql.

The index is DERIVED AND DISPOSABLE. Deleting it and re-running must reproduce
it from the packages alone. Nothing lives only in the index. Packages are the
source of truth; this is a view over them.

1. UNIFY
   DuckDB globs packages/*/extracted/*.parquet and */pdf_messages.json into one
   `messages` view. Write pdf_transcript_to_messages: header-delimited PDF
   transcript text -> message rows in the SAME shape as the XML and JSON paths.
   Every row keeps source_format, package_id, confidence_level, derivation_why
   and not_established. NEVER flatten confidence into a single column - a
   header_derived row and a structured row must stay distinguishable in every
   query.

2. CORROBORATE
   Match across sources, record each link with its basis:
     exact     - identical attachment sha256, or identical normalized body hash
     timestamp - same normalized participants within a configurable window
     content   - fuzzy body match above a threshold
   Normalize phone numbers for MATCHING only; keep every raw variant (A-3).
   One export has +18102959303, 18102959303, +18102959302, 8102959302 and null
   for the same parties in one file.
   Compare timestamps on epoch, never on readable_date, and record the window
   used - sources handle timezone differently (A-4, B-5).
   Every link gets a derivation block: why it matched, what it does NOT
   establish (RULES R11). A timestamp match is not proof of identical content.

3. REPORT
   casekit coverage --thread <id> emits HTML (Matt's default format):
     - corroborated percentage for the thread and per date range
     - a timeline showing WHERE the gaps are, so they can still be filled
     - disagreements: same participants + timestamp, different body; or a
       message present in one source and absent in another
   A disagreement is a FINDING. Surface it. Never auto-resolve it, never pick
   a winner.

4. REMEDIATE
   Every uncorroborated derived value gets a remediation block (RULES R11):
     what_would_corroborate - one plain sentence
     search - a CONCRETE spec: time window, party, attachment names, sha256 if
              known, a distinctive text fragment
     closes - which not_established items this would close
     status - open | resolved | accepted
   casekit gaps            emits the open queue, ranked by what each adds
   casekit accept <id> --reason "..."   closes one WITHOUT deleting it

   "accepted" matters as much as the other two. Not every gap needs filling.
   Once the pattern for a span is established, the rest get closed with a
   stated reason and drop out of the queue. A finding list that can never be
   closed is a finding list nobody reads.

EXIT CRITERION: casekit index builds a DuckDB db over every package.
`SELECT source_format, count(*) FROM messages GROUP BY 1` returns a row per
format. confidence_level and not_established survive on every row.
casekit coverage emits the HTML report. Against the two reference files - which
share NO party and NO date range - the report shows them as disjoint threads
with 0% cross-source corroboration rather than inventing matches. Deleting the
index and re-running reproduces it exactly.

Verify with: casekit index && \
  duckdb corpus.db -c "SELECT source_format, confidence_level, count(*) FROM messages GROUP BY 1,2" && \
  casekit coverage --all && \
  rm corpus.db && casekit index   # must reproduce identically
```

## Phase 6c

```
Read RULES.md (R11 - remediation and status), then FINDINGS.md on embedded
image provenance, and GOTCHAS.md A-4, B-5, S-13.

Matt has roughly 10,000 unsorted images. Sorting them by hand to find
corroborating screenshots is not a job anyone should do. Index them once and
let the matcher propose.

Implement internal/images/:

1. INDEX - casekit images index <dir>
   Per image, record:
     sha256, bytes, dimensions
     EXIF DateTimeOriginal / CreateDate
     editor provenance - one blob in the reference corpus carries its ORIGINAL
       screenshot path, capture timestamp and crop geometry from Samsung Photo
       Editor (FINDINGS.md). Parse it where present.
     filename-embedded timestamps: Screenshot_20221103-210020_*, IMG_YYYYMMDD_*
     OCR text via tesseract
   Record WHICH source each timestamp came from and mark confidence per R11 -
   EXIF, filename, editor metadata and filesystem mtime are not equivalent and
   must not be flattened into one "timestamp" column.
   Write Parquet beside the corpus index.

2. KEYWORDS - casekit keywords <thread>
   Per message, pick distinctive search terms by INVERSE CORPUS FREQUENCY, not
   by eye. Compute term frequency across the whole corpus in DuckDB; take the
   rarest handful per message. Record each term's corpus_freq on the record.
   Common words are worthless as keys. What discriminates: proper nouns, brand
   names, place names, medication names, misspellings - "Miralax", "Enzo's",
   "Clio high school", "famous footwear". Prefer longer terms; they survive OCR
   better.

3. PROPOSE - casekit gaps --propose
   Rank candidate images by, IN THIS ORDER:
     a) distinctive-keyword hits in OCR text - PRIMARY. Score by how many
        distinct high-weight terms hit, weighted by their rarity. Match fuzzily;
        OCR is noisy and mangles proper nouns.
     b) attachment filename appearing in OCR text
     c) timestamp proximity - TIEBREAK ONLY
   Ranking order matters and is not the obvious one. A screenshot's EXIF
   timestamp is when the SCREENSHOT was taken, not when the message was sent -
   routinely months apart (GOTCHAS A-16). Never drop a candidate because its
   timestamp is far from the message; that is the expected case.
   State which signal drove each proposal - a content match and a time match
   are different claims (RULES R11).
   This is a PROPOSAL, never an automatic link.

4. RESOLVE
   Accepting a proposal writes a corroboration link with its basis and flips
   the gap to resolved. Rejecting records the rejection so the same image is
   never proposed for that gap again.

EXIT CRITERION: casekit images index builds a Parquet index over a directory of
images with hash, best-available timestamp AND its source, dimensions and OCR
text. casekit keywords emits per-message distinctive terms with corpus
frequencies, and common words do NOT appear in the output. casekit gaps
--propose returns ranked candidates per open gap with a stated basis and which
signal drove it; an image whose OCR matches but whose timestamp is months away
IS still proposed. Accept flips the gap to resolved and records the link; reject is
remembered. Re-running the index over an unchanged directory is a no-op.

Verify with: casekit images index <dir> && \
  duckdb -c "SELECT timestamp_source, count(*) FROM 'images.parquet' GROUP BY 1" && \
  casekit keywords <thread> | head -20 && \
  casekit gaps --propose | head -20
```

## Phase 5d

```
Read RULES.md, then GOTCHAS.md S-15, A-17, A-18, B-8, B-9, S-13, A-8.

Implement HTML and text conversation extraction in internal/extract/html.go and
internal/extract/text.go, plus engines/htmlmsg/.

WHY THIS MATTERS MORE THAN IT LOOKS: the reference PDF transcript was produced
by Stirling-PDF v1.1.1 FROM HTML. The emoji destruction documented in GOTCHAS
S-5 happened during that conversion, not in the source. The HTML almost
certainly still has the real characters. This phase routes around a data-loss
problem instead of documenting it.

Output MUST use the same table shape as Phases 5 and 5b.

SOURCE PREFERENCE - implement as an explicit ordering, not a convention:
    XML / JSON   structured export    strongest
    HTML         marked-up export
    text         flat export
    PDF          rendered derivative  weakest
Where two sources cover the same conversation, the upstream form supersedes.
RECORD the supersession; never delete the downstream package (RULES R6).

HTML:
  Parse as a DOM. NEVER regex, never tag-stripping.
  Detect the exporter from its markup signature and record it.
  Emoji appear in THREE forms and a naive extractor loses the third silently:
    1. literal UTF-8 character
    2. HTML entity  &#128169;
    3. <img> tag with the emoji in alt / title / aria-label
  Handle all three, record emoji_source per occurrence (GOTCHAS A-17).
  Images: inline data: base64 -> generic blob pass in internal/blob/base64.go.
  Relative src -> resolve against sibling folder, else resolved:false with
  declared_uri (GOTCHAS A-18, A-8). Type by magic bytes; the data: mimetype is
  a claim (S-13).
  Charset: BOM first, then detection, then the declaration - IN THAT ORDER.
  Record which method won and mark it estimated (GOTCHAS B-8, RULES R11).

TEXT:
  Sender label, timestamp, body. Nothing else is there.
  confidence_level "header_derived" - same weakness as PDF headers.
  Populate not_established generously: no attachment bytes, no read status,
  no codes, direction from a text label only (GOTCHAS B-9).
  Same charset discipline as HTML.

EXIT CRITERION: an HTML export parses via DOM into the Phase 5 table shape with
the exporter detected; all three emoji forms recovered with emoji_source
recorded; inline base64 images land in blobs/ and attachments/; unresolvable
src values appear as resolved:false; the charset method used is recorded and
marked estimated. A flat text export parses with header_derived confidence and
a populated not_established. Where HTML and PDF cover one conversation, the
HTML supersedes, the supersession is recorded, and the PDF package still exists.

Verify with: casekit extract <export.html> && \
  jq '[.elements[]|select(.emoji_source)]|group_by(.emoji_source)|map({(.[0].emoji_source):length})' out/extraction.json
```
