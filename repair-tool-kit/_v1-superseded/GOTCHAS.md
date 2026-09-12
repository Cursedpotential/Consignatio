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

## Platform gotchas

### A-6. Windows console flash on context-menu invocation

A console-subsystem binary launched from a shell verb flashes a window on
every file.

*Avoid:* build two entry points — `casekit.exe` (console, for terminal use)
and `casekitw.exe` (`-ldflags "-H windowsgui"`, for menu verbs).

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

*Avoid:* keep the venv shallow — `D:\case_apps\engines\python\.venv`.
