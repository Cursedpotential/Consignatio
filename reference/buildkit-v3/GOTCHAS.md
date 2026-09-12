# Gotchas — casekit

Ranked by damage. **S** = silent data loss / corruption. **A** = costs a day.
**B** = costs an hour.

Entries marked **[observed]** were hit and reproduced during planning on Matt's
actual evidence files. They are not hypothetical.

---

## Engine-boundary gotchas

### S-1. DuckDB `read_xml` silently drops sparse attributes **[observed]**

`read_xml()` infers struct schemas from a sample of rows. In the real SMS
export, only 8 of 14 `<part>` elements carried a `data=` attribute — the
base64 image payloads. **DuckDB omitted `data` from the inferred struct
entirely.** The query ran clean, returned 231 rows, and every image was gone
with no warning.

*Mechanism:* sample-based inference over a heterogeneous element set.
`sample_size=-1` does **not** fix it.

*Avoid:* in the XML pre-pass, write the attribute onto **every** element,
using an empty value where absent (`data_sha256=""`, `data_bytes="0"`). Then
inference always sees it. After any DuckDB or `webbed` upgrade, re-run
`DESCRIBE SELECT * FROM read_xml(...)` and assert the expected fields exist.

### S-2. mutool mis-maps ZapfDingbats to an unrelated letter **[observed]**

On the transcript, mutool rendered ZapfDingbats `0x6E` as `I` (U+0049). The
raw byte is `n`; the correct Unicode is U+25A0. `I` corresponds to nothing and
**cannot be reversed** — you cannot tell it from a real capital I in the text.

*Avoid:* mutool is not permitted in the glyph-accurate text path. Use poppler,
pypdf, or pdfium. mutool remains fine for raster and structure work.

### S-3. `xml_extract_attributes` OOMs on small files **[observed]**

`xml_extract_attributes(xml, '//sms')` on a **3.8 MB** file consumed 3.1 GiB
and died. This is not a scale problem — it is a small file.

*Avoid:* never use the XPath attribute functions for bulk extraction. Use
`read_xml()` on a slimmed document. Reserve XPath functions for targeted
single-element lookups.

### S-4. Regex over XML corrupts on base64 **[observed]**

An attribute-scanning regex picked up fragments of base64 payloads as
attribute names (`QfgScjKZOTcAAAAASUVORK5CYII`, `9k`) because base64 contains
`=`. Silent corruption of the parse.

*Avoid:* lxml or DuckDB only. No regex XML parsing anywhere in the codebase.

---

## PDF gotchas

### S-5. Emoji substitution is invisible in extracted text **[observed]**

The transcript's producer (Stirling-PDF v1.1.1) replaced **every** emoji with a
single ZapfDingbats glyph. 33 occurrences, 22 show-operations, **one** distinct
byte. Readers that don't decode it return a plain letter, so
`Love you ❤️❤️❤️❤️` becomes `Love you IIII` — which reads as a typo, not as
corruption.

*What survives:* emoji **count** and **position**. *What is destroyed:* which
emoji. There is no `ToUnicode` CMap; identity is not in the file and no reader
can recover it.

*Avoid:* emit `emoji_count` and `emoji_identity: "unavailable"` rather than
dropping or guessing. Never treat PDF-sourced text as verbatim when
`symbol_font_present` is true.

### S-6. Text runs invisible to every extractor **[observed]**

The `Love you` + 4-glyph line was dropped by **all seven** readers tested. The
glyphs are present in the content stream; no text extractor surfaced them.

*Avoid:* when the profile flags glyph substitution, run a raw content-stream
scan (`qpdf --qdf` + text-operator extraction) **in parallel** with the text
engine. Not as a fallback — as a second channel.

### A-1. PDF attachment references are frequently dangling **[observed]**

The transcript prints `[Attachment(s): image000000.jpg]` ten times.
`pdfimages -list` → 0 images. `pdfdetach -list` → 0 attachments. The filenames
are text; the files are not there.

*Avoid:* emit these as `resolved: false` with `declared_name` set. They become
a work queue, not an error.

### A-2. MMS attachment filenames are not unique **[observed]**

`image000000.png` appears four times across different messages in one export.
Resolving a PDF reference by filename alone will match the wrong image.

*Avoid:* content-address every blob by SHA-256. Resolution requires filename
**plus** message context (thread, timestamp), never filename alone.

### B-1. `pdftoppm` zero-pads output filenames by total page count

A 24-page doc yields `page-03.png`; a 200-page doc yields `page-003.png`.
Guessing the filename breaks.

*Avoid:* glob the output directory; never construct the expected name.

---

## Message-data gotchas

### S-7. Null body plus attachment is not an empty message **[observed]**

Six MMS in the sample have `body_present = false` and carry 1–3 images. The
image **is** the message. Collapsing that to `body: ""` destroys the record.

*Avoid:* three distinct fields — `body_present`, `body_is_null`, `body_text`.
Missing, present-and-null, and present-and-empty are three different facts.

### A-3. Phone number formats vary within a single file **[observed]**

One export contains `+18102959303`, `18102959303`, `+18102959302`,
`8102959302`, and `null` — the same parties, formatted differently, in the same
document. The one *received* MMS is the one missing the `+1`.

*Avoid:* normalize aggressively for matching, retain every raw variant
verbatim in the record. Never overwrite the original string.

### A-4. `date` and `readable_date` can disagree

`date` is epoch milliseconds (authoritative). `readable_date` is local time as
rendered by the exporting device, with **no timezone recorded**. Around DST
boundaries the ambiguity is an hour wide. `date` vs `date_sent` is a separate
distinction — received vs sent.

*Avoid:* store the epoch as truth, keep `readable_date` verbatim as its own
field, mark any derived offset as inferred, flag DST-boundary messages.

### A-5. Official XSD is a subset of real exports **[observed]**

The synctech XSD does not contain `sub_id`, `sim_imsi`, `creator`,
`correlation_tag`, `sef_type`, `secret_mode`, `safe_message`, `m_size`,
`tr_id`, and many more that the real Samsung export carries. The vendor docs
say attributes vary by phone.

*Avoid:* schema-**guided**, not schema-**limited**. Decode the documented
fields; capture every undocumented one verbatim. Never whitelist.

### B-2. Code mappings must be stored alongside their decoded label

`type` 1/2/3/4/5/6 = received/sent/draft/outbox/failed/queued (SMS).
`msg_box` 1/2/3/4 = received/sent/draft/outbox (MMS).
`addr type` 129/130/151/137 = bcc/cc/to/from.
`status` -1/0/32/64 = none/complete/pending/failed.
Call `type` 1–6 = incoming/outgoing/missed/voicemail/rejected/refused-list.

*Avoid:* persist `raw_code` **and** the label. A wrong mapping is then a SQL
update, not a re-extraction.

---

## JSON / Facebook-Instagram export gotchas

Marked **[expected]** — these are documented behaviours of these exporters, but
unlike the `[observed]` entries above they have **not** been reproduced against
Matt's own files yet. Verify on first real export before trusting.

### S-8. Meta JSON double-encodes all non-ASCII **[observed]**

Meta's data exports write UTF-8 bytes as if they were latin-1, then escape
them. `Radosław` arrives as `Rados\u00c5\u0082aw`; the gem emoji arrives as
`\u00f0\u009f\u0092\u008e`. A standard JSON parser reads this as **valid
JSON** and yields mojibake — `Ã©` — with no error.

Documented publicly since 2018 and still unfixed. **There is no export setting
and no alternative parser** — the JSON is well-formed, it simply contains the
wrong characters. The HTML export has the same defect.

*Fix — byte-level, applied to the raw bytes before `json.loads`:*

```python
fixed = re.sub(rb'\\u00([\da-f]{2})',
               lambda m: bytes.fromhex(m[1].decode()), raw_bytes)
data  = json.loads(fixed)
```

*Why byte-level rather than post-parse:* the common post-parse form
(`s.encode('latin-1').decode('utf-8')`) works on current exports and was
verified to, but it breaks on mixed content — if Meta ever emits one correctly
encoded character above U+00FF the round-trip raises, and the usual
`try/except` then passes the **whole string through unfixed**, mojibake
included. The byte fix has no such failure mode.

*ftfy as detector, not primary fix:* run `ftfy.fix_text()` **after** the byte
fix. It is explicitly built to avoid false positives and leaves correct text
alone, so if it still changes a string, something else is wrong with that
string — flag it rather than silently accepting the change.

Verified 2026-09-11 against documented payloads:

| case | byte-fix | post-parse latin-1 | ftfy |
|---|---|---|---|
| `Rados\u00c5\u0082aw` | Radosław | Radosław | Radosław |
| `\u00f0\u009f\u0092\u008e` | 💎 | 💎 | 💎 |
| `\u00e2\u009d\u00a4\u00ef\u00b8\u008f` | ❤️ | ❤️ | ❤️ |
| already clean | unchanged | unchanged | unchanged |

### S-14. The most-cited fix silently destroys emoji **[observed]**

The widely-copied Stack Overflow JavaScript answer pairs `\u00xx` sequences
**two at a time** and decodes each pair as one character. Accented Latin is
exactly two sequences, so it appears to work — and then eats every emoji.

Verified: `💎` (4 sequences) → `П`. `❤️` (6 sequences) → `¤ϸ`. No error either
time.

*Mechanism:* emoji are 4-byte UTF-8, often plus a variation selector, so a
single emoji is four to six `\u00xx` sequences, not two.

*Avoid:* consume runs of `\u00xx` of **arbitrary length** and decode the whole
run as UTF-8. Never assume a fixed sequence count. Given S-5 already destroyed
the emoji in the PDF transcripts, this would have been a second independent
emoji-destruction bug in the same corpus.

### S-9. DuckDB `read_json` drops sparse keys — same class as S-1 **[expected]**

`read_json` infers its schema from a sample exactly as `read_xml` does. A key
present on only some messages — `photos`, `videos`, `sticker`, `share`,
`reactions`, `call_duration` — can be omitted from the inferred struct, and
those messages silently lose their attachments.

*Avoid:* pass an explicit `columns={...}` struct covering every known key, or
normalize the JSON in a pre-pass so every object carries every key. Then assert
the expected fields exist with `DESCRIBE` before extracting. Same discipline as
the XML slim pass.

### A-8. Media lives outside the JSON, unlike SMS XML **[expected]**

SMS exports embed images as base64. Meta exports do **not** — messages carry a
relative `uri` like `photos/12345_678.jpg` pointing at a sibling folder. If
only the JSON was copied, every attachment is dangling.

*Avoid:* resolve `uri` against the export root; present when found, otherwise
`resolved: false` with `declared_uri` recorded. Never treat a missing file as a
missing attachment — the reference is evidence that something was sent.

### A-9. Threads split across numbered files **[expected]**

Long conversations export as `message_1.json`, `message_2.json`, … each a
complete object with its own `participants` array. Reading only the first gives
a silently truncated thread, and the files are **not** in chronological order —
higher numbers are usually older.

*Avoid:* glob every `message_*.json` in the thread directory, union them, then
sort by `timestamp_ms`. Assert the message count against the union, never a
single file.

### A-10. No direction field — it must be derived **[expected]**

There is no `type` or `msg_box`. Direction comes from comparing `sender_name`
to the account owner's name, which is a **display name** that can change, can
collide, and is absent from group threads where it matters most.

*Avoid:* record `sender_name` verbatim, derive direction, and mark it
`confidence: "derived"` — never `"structured"`. This is a genuinely weaker
claim than the SMS XML `type` code and must not be presented as equivalent
(RULES R7, R9).

### B-5. `timestamp_ms` carries no timezone **[expected]**

Epoch milliseconds only. Same class as A-4 — the epoch is authoritative, any
local rendering is inferred.

*Avoid:* store the epoch as truth; mark any derived offset as inferred.

---

## ZIP / container gotchas

Marked **[expected]** — researched and well documented, but not reproduced
against Matt's own archives yet.

### S-10. Zip slip — member names escape the extraction directory **[expected]**

A zip entry may be named `../../../Windows/System32/x.dll` or given an absolute
path. Go's `archive/zip` hands you the name **verbatim and does not validate
it**. Joining it to an output directory and writing walks straight out of the
sandbox. This is the single most exploited archive vulnerability there is, and
nothing in the standard library stops it.

*Avoid:* for every member — reject absolute paths, reject any path containing
`..` after cleaning, resolve the final destination and confirm it is still
inside the extraction root, and refuse rather than sanitize. A malicious name
is a **finding**, so record it; do not quietly rename it and continue.

### S-11. Decompression bombs **[expected]**

A few hundred kilobytes can expand to terabytes, and nested archives multiply
it. Recursion makes this worse: casekit will open zips inside zips.

*Avoid:* three independent caps, all configurable — maximum total bytes
written, maximum compression ratio per member, and maximum recursion depth
(default 3). Track cumulative expansion across the whole recursion, not per
archive. Abort and flag; never silently truncate.

### S-12. Go's `archive/zip` reads only the central directory **[expected]**

It never scans local file headers. An entry present in the local headers but
absent from the central directory is **completely invisible** — you get a clean
read, no error, and missing data. That gap is both how archives get corrupted
and how data gets deliberately concealed.

*Avoid:* the same two-channel pattern as the PDF path. Channel 1 is
`archive/zip` (fast, correct for healthy archives). Channel 2 scans for local
header signatures `PK\x03\x04` directly. Compare the two. **A discrepancy is a
finding, not an error** — record it in the manifest with both counts.

### A-11. Member filename encoding is ambiguous **[expected]**

ZIP stores names as CP437 unless bit 11 of the general-purpose flag is set, in
which case UTF-8. Many creators set neither correctly. Non-ASCII filenames —
accented names, emoji in phone-backup filenames — mojibake or fail to match.

*Avoid:* honour bit 11 when set. When unset and the bytes are not valid ASCII,
record the **raw bytes** alongside the best-effort decode, and mark the decode
`estimated` (RULES R7). Never match on a decoded name alone.

### A-12. Duplicate member names are legal **[expected]**

A zip may legitimately contain two entries with identical names. Naive
extraction overwrites, and one file silently disappears.

*Avoid:* extract by index, not by name. Content-address every member to
`blobs/<sha256>` and keep the declared name as metadata — same discipline as
the MMS `cl` collision (A-2). Record duplicates explicitly.

### A-13. Repair is a ladder of independent parsers **[expected]**

Different implementations disagree about broken archives in useful ways, the
same way PDF readers did. Escalate only on failure:

| Tier | Tool | What it fixes |
|---|---|---|
| diagnose | `unzip -t`, `zipdetails --scan` | structural report, writes nothing |
| 1 | `zip -FF in.zip --out out.zip` | rebuilds central directory from local headers |
| 2 | `ziptail` (Mark Adler) | rebuilds CD + end records, zip64-aware, fixes invalid data descriptors |
| 3 | `bsdtar` / `tar.exe` | genuinely independent parser — ships **native in Windows 10+** |
| 4 | `7z x -y` | partial extract, salvages what it can |
| 5 | carve | scan for `PK\x03\x04`, recover members with no usable index |

*Avoid:* verify with `zipcmp` (libzip) member-by-member rather than trusting an
exit code. Per-member CRC and SHA-256 are the real check — a repaired archive
has a different archive hash by definition, so the evidentiary claim is *same
members, same contents*, never *same file*.

### B-6. ZIP timestamps are DOS time **[expected]**

Two-second resolution, no timezone, no year before 1980. Extended timestamp
fields may or may not be present.

*Avoid:* record the DOS timestamp verbatim, use an extended field when present
and say which was used. Never present a zip mtime as an authoritative event
time.

---

## Base64 / payload gotchas

Base64 shows up in more places than the MMS `data=` attribute: `data:` URIs in
HTML and JSON, MIME transfer encoding in `.eml`, embedded thumbnails, and
occasionally base64 nested inside base64. Treat decoding as a **generic pass**
that any format can invoke, not an XML-specific step.

### S-13. Declared content-type lies **[observed]**

The reference export declares `ct="image/png"` on parts whose bytes are JPEG,
and `cl` filenames (`image000000.png`) that do not match content either.
Trusting the declared type produces files that will not open.

*Avoid:* identify every decoded payload by **magic bytes**, write the correct
extension, and record the declared type and the detected type as **two separate
fields**. Disagreement between them is a finding worth keeping, not an error to
resolve silently.

### A-14. Whitespace, padding, and URL-safe variants **[expected]**

XML attributes may carry embedded newlines inside base64. Some encoders omit
`=` padding. `data:` URIs may use the URL-safe alphabet (`-_` for `+/`) and
carry a `data:image/png;base64,` prefix that must be stripped — and whose
mimetype claim is subject to S-13 like any other declared type.

*Avoid:* strip all whitespace, normalize the URL-safe alphabet, re-pad to a
multiple of four, strip any `data:` prefix, and record the prefix's claimed
type separately. Decode with validation on; never silently discard bad
characters.

### A-15. Truncated payloads decode partially and silently **[expected]**

A cut-off base64 string still decodes to a usable-looking prefix. You get a
half image with no error.

*Avoid:* compare decoded length against the declared size where one exists
(`m_size`, `data_bytes`, Content-Length). On mismatch, still write the bytes —
partial data is data — but mark the blob `status: "partial"` and classify it
`reconstructed`, never `recovered` (RULES R9). Record both lengths.

### B-7. Blobs are unbrowsable by hash alone **[expected]**

`blobs/a8262508…` is right for integrity and useless for a human. A folder of
64-character filenames cannot be reviewed.

*Avoid:* the package carries **both** views — `blobs/<sha256>` as the canonical
store, and `attachments/` with real filenames restored from `cl`/`fn`/`uri`,
collision-suffixed, plus a `blobs/INDEX.md` mapping every hash to its declared
name, detected type, size, and the message it belongs to. `attachments/` is a
convenience copy and is listed in `MANIFEST.json` like everything else.

### A-16. A screenshot's timestamp is not the message's timestamp **[expected]**

EXIF `DateTimeOriginal` on a screenshot records when the **screenshot was
taken**. Someone screenshotting a conversation months after the fact produces
an image whose every timestamp — EXIF, filename, mtime — is months away from
the message it depicts.

This inverts the obvious ranking: for screenshot corroboration, **OCR content
match is the primary signal and timestamp proximity is secondary**, sometimes
actively misleading.

*Avoid:* rank candidates by distinctive-keyword hits in OCR text first, time
proximity second and only as a tiebreak. Record which signal drove the match in
the link's `derivation` block (RULES R11) — a content match and a time match
are different claims. Never reject a candidate purely because its timestamp is
far from the message; that is the expected case, not a disqualifier.

---

## HTML / text export gotchas

### S-15. The PDF transcripts are downstream of HTML — go upstream **[observed]**

The reference PDF's Producer is **Stirling-PDF v1.1.1**, which converts HTML to
PDF. The emoji destruction in S-5 happened **during that conversion**, when a
non-embedded base-14 font stack could not represent them. The HTML source
almost certainly still contains the real characters.

This means the highest-value action for any PDF-sourced gap is not
corroboration — it is **finding the HTML the PDF was made from**. One retrieval
closes the emoji loss for an entire conversation instead of one message at a
time.

*Avoid:* whenever a PDF profiles as a transcript with `symbol_font: true`, emit
a remediation item of `locate_upstream_source` naming the producer, the party
and the date range. Rank source preference explicitly:

```
XML / JSON  (structured export)   ← strongest
HTML        (marked-up export)
text        (flat export)
PDF         (rendered derivative)  ← weakest, use when nothing upstream exists
```

Where both exist for the same conversation, the upstream form supersedes and
the PDF becomes corroboration. Record the supersession; do not delete the PDF
package (RULES R6).

### A-17. Emoji in HTML exports take three different forms **[expected]**

Depending on exporter, an emoji may be a literal UTF-8 character, an HTML
entity (`&#128169;`), or an **`<img>` tag** pointing at a sprite or CDN asset
with the emoji in the `alt` or `title` attribute. Text extraction that strips
tags silently loses the third form entirely — the same failure mode as S-5, by
a different route.

*Avoid:* parse HTML as a DOM, never with regex or tag-stripping. For `<img>`,
read `alt`/`title`/`aria-label` and record which attribute supplied it. Decode
entities. Preserve literal characters as-is. Record `emoji_source` on each so
the three are distinguishable.

### A-18. Single-file HTML exports inline attachments as base64 **[expected]**

"Save as single file" exports embed images as `data:image/png;base64,…` in
`src`. Multi-file exports use relative paths into a sibling folder, like Meta
JSON (A-8).

*Avoid:* both paths go through the generic base64 pass
(`internal/blob/base64.go`) and the same resolve-or-flag logic. Identify type
by magic bytes; the `data:` mimetype is a claim (S-13).

### B-8. Charset declarations lie or are absent **[expected]**

An HTML export may declare `charset=utf-8` and contain CP1252 bytes, or declare
nothing. Text exports have no declaration at all and may be UTF-8, UTF-16 with
or without BOM, or CP1252.

*Avoid:* sniff the BOM first, then detect, then fall back to the declaration —
in that order, and record which one was used and mark it `estimated` (RULES
R11). Do not trust a declared charset over the actual bytes.

### B-9. Text exports have no structure to recover **[expected]**

A flat text transcript gives a sender label, a timestamp and a body, and
nothing else — no attachment linkage beyond a filename mention, no read status,
no codes. Direction comes from a text label, same weakness as PDF headers.

*Avoid:* extract what is there, mark `confidence_level: "header_derived"`, and
populate `not_established` generously. Text is above PDF in source preference
only because its characters are usually intact.

---

## Contract gotchas

### S-16. `offset` has no defined coordinate space **[observed — kit defect]**

`SPLIT.md` gives elements an `offset`, and R11 requires `derived_from` offsets
that trace back to bytes in the original file. For a PDF content-stream element
the offset is into the **decompressed stream**, which has no byte position in
the original at all. Two different coordinate spaces, one field name.

Get this wrong and every Phase 4 derivation block is untraceable — the claim
"traces to bytes in the original" becomes false without anything erroring.

*Avoid:* the contract carries the space explicitly, and this is
`SPLIT.md` sync point #1 — settle it before a second engine exists:

```json
"offset_space": "source_file" | "decoded_stream",
"offset": 182044,
"length": 611,
"container": { "object": 12, "source_offset": 31236, "source_length": 4894 }
```

Where `offset_space` is `decoded_stream`, `container` gives the enclosing
object's real position in the original, so the chain to source bytes is
`original → object → stream offset` rather than a single number that silently
means two things.

---

## Platform gotchas

### A-6. Windows console flash on context-menu invocation

A console-subsystem binary launched from a shell verb flashes a window on
every file.

*Avoid:* build two entry points — `casekit.exe` (console, for terminal use)
and `casekitw.exe` (`-ldflags "-H windowsgui"`, for menu verbs).

**And the children, which is the part that bites.** `-H windowsgui` hides the
*parent* only. A Go parent spawning `pdftotext.exe`, `qpdf.exe` or a worker
interpreter flashes a console **per child**. Across a corpus with worker pools
that is a flash storm. Every `exec.Cmd` needs
`SysProcAttr: &syscall.SysProcAttr{HideWindow: true}` / `CREATE_NO_WINDOW`.
Stdlib only — no new dependency.

### A-7. Windows path handling in JSON

Backslashes require escaping in JSON, and engines written in other languages
may normalize or mangle them.

*Avoid:* the contract carries absolute paths as-is; engines must treat the
path as opaque. Test with a path containing a space and a non-ASCII character.

### B-3. HKCU-only registry writes

Writing to HKLM needs elevation and affects all users.

*Avoid:* every shell verb goes under
`HKCU\Software\Classes\SystemFileAssociations\`. The uninstall script must be
tested **before** the install script is run.

### B-4. Frozen Python venv path length

`uv` venvs under a deep install path can approach the Windows path limit with
nested site-packages.

*Avoid:* keep the venv shallow — `<INSTALL_ROOT>\engines\python\.venv` (root is OD-1).
