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

EXIT CRITERION on docs/reference/_18102689630__1___1_.pdf:
  - 33 symbol glyphs present as U+25A0
  - 22 distinct symbol show-operations recorded
  - 10 attachment_ref elements, all resolved=false
  - the "Love you" 4-glyph run present via the raw-stream channel
  - source file sha256 unchanged after the run

Verify with: casekit extract docs/reference/*.pdf && \
  jq '[.elements[]|select(.kind=="attachment_ref")]|length' out/extraction.json
```

## Phase 5

```
Read RULES.md, GOTCHAS.md S-1, S-3, S-4, S-7, A-2, A-3, A-5, B-2.

Implement XML ingestion as TWO stages. Do not skip stage 1.

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
    MANIFEST.json     every file: path, size, sha256, mtime
    SHA256SUMS        same data, sha256sum-compatible

Package id = sha256 of the zipped directory. Append one line to the ledger
(JSONL) with package id, source sha256, engine, checks, timestamp.

Verification must work with NO casekit binary present - `sha256sum -c
SHA256SUMS` alone must pass. README.txt states the exact commands.

EXIT CRITERION: package both reference files. For each, the source file's
sha256 is identical before and after. `sha256sum -c SHA256SUMS` passes inside
the package directory. The ledger has one new line per package.

Verify with: sha256sum docs/reference/* > /tmp/before.txt
             casekit package docs/reference/*
             sha256sum -c /tmp/before.txt
             cd out/<pkg-id> && sha256sum -c SHA256SUMS
```
