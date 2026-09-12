# Empirical Findings — 2026-09-11

Everything here was produced by running real tools against Matt's actual
evidence files during planning. Reproduction commands included. This is the
evidence base the whole plan rests on — if a later decision contradicts
something here, this file wins until re-tested.

## Reference file A — PDF transcript

`_18102689630__1___1_.pdf` · 36,025 bytes · sha256 `f18e250e5aca784f…`

| Property | Value |
|---|---|
| Producer | **Stirling-PDF v1.1.1**, 2025-08-14 |
| Pages | 24 |
| Embedded images | **0** |
| Attachments | **0** |
| Fonts | Helvetica, Helvetica-Bold/Oblique, Courier, Symbol, ZapfDingbats — **none embedded** |
| ToUnicode CMaps | **0** |
| Generations | 1 (single `%%EOF`, no incremental updates) |
| qpdf --check | clean |

It is a **derivative**, not an original export. Conversation spans
2024-05-22 → 2024-05-30 with `+18102689630`.

### Reader bake-off

Same file, same line — `Nvm she pooped` + one emoji:

| Reader | Language | Output | Codepoint | Non-ASCII recovered |
|---|---|---|---|---|
| **poppler** `pdftotext` | C++ | `… ■` | U+25A0 | **33 / 33** |
| **pypdf** | pure Python | `… ■` | U+25A0 | **33 / 33** |
| **pdfium** `pypdfium2` | C++ | `… ■` | U+25A0 | **33 / 33** |
| pdf.js | JavaScript | `… n` | U+006E | 0 |
| pdfminer.six | Python | `… n` | U+006E | 0 |
| pdfplumber | Python | `… n` | U+006E | 0 |
| **mutool** | C | `… I` | U+0049 | 0 |

pdf.js was retested with `standardFontDataUrl` correctly configured — **still
`n`**. Font data affects rendering, not `getTextContent()` Unicode mapping.

**mutool is the only reader that produces a value corresponding to nothing.**
`n` is the raw byte and is reversible. `I` is not.

### The substitution

Raw content stream:

```
(Nvm she pooped ) Tj  /F4 10 Tf  (n) Tj
```

`/F4` = ZapfDingbats. Byte `0x6E` = glyph a73 = U+25A0 BLACK SQUARE.

Across all 24 pages: **22 show-operations, 33 glyphs, ONE distinct byte.**
Payload distribution: `n` ×16, `nn` ×3, `nnn` ×1, `nnnn` ×2.

- **Preserved:** emoji count and position. `Love you ❤️❤️❤️❤️` is recoverable
  as exactly four emoji at that spot.
- **Destroyed:** which emoji. One code for all of them, no ToUnicode. Not
  recoverable by any reader.

### Disagreement triangulates the truth

Three readers gave decoded Unicode, three gave the raw byte, one gave a
corrupted mapping. From that spread alone the entire substitution mechanism is
reconstructible without opening the content stream. The "wrong" readers are
useful — they are raw-byte reporters.

### Invisible content

The `Love you` + 4-glyph run was dropped by **all seven** readers. Present in
the content stream, surfaced only by raw-stream scanning.

### Dangling attachments

10 `[Attachment(s): …]` references in text; zero images, zero attachments in
the file. Names seen: `image000000.jpg`, `image000000.png`, `IMG_1786.PNG`,
`IMG_2955–2958.PNG`, `644fac64-…jpg`, `00205f83-…jpg`.

## Reference file B — SMS XML export

`Copy_of_sms-20221104021809.xml` · 3,852,198 bytes · sha256 `55515f2a490c9a0a…`

| Property | Value |
|---|---|
| Producer | **SMS Backup & Restore v10.18.001**, 04/11/2022 02:19:19 |
| backup_set | `1a0f935d-eee1-45e0-a16d-5babe1987f01` |
| Messages | 231 (225 sms + 6 mms) |
| Parts / addrs | 14 / 12 |
| Range | Nov 3 – Nov 4, 2022 |
| Party | `+18102959303`, contact_name **Katrina Kinzel** |
| Creator app | `com.google.android.apps.messaging` |

**No overlap with file A** — different number, different period. No
cross-validation possible between these two.

### Blobs are embedded

8 base64 payloads extracted, 2,822,412 bytes:

| sha256 | type | bytes | cl | dimensions |
|---|---|---|---|---|
| `a8262508` | image/png | 101,603 | image000000.png | 1080×2176 |
| `555435db` | image/jpeg | 305,112 | image000000.jpg | 767×1023 |
| `bf676610` | image/jpeg | 335,607 | image000001.jpg | 1086×1448 |
| `088ae854` | image/jpeg | 369,338 | image000002.jpg | 1086×1448 |
| `cf7b2e20` | image/png | 880,089 | image000000.png | 1077×1005 |
| `9b95d3fd` | image/jpeg | 218,859 | image000000.jpg | 697×2048 |
| `004bc3b9` | image/png | 391,405 | image000000.png | 1080×1032 |
| `6878c492` | image/png | 220,399 | image000000.png | 1080×2176 |

`image000000.png` appears **four times** — filenames are not unique.

### Embedded provenance inside a blob

One PNG carries Samsung Photo Editor metadata:

```
"originalPath":"/data/sec/photoeditor/0/storage/emulated/0/DCIM/Screenshots/
                Screenshot_20221103-210020_One UI Home.png"
"clipInfoValue":"{mCenterX:0.5, mCenterY:0.5445, mWidth:1, mHeight:0.4742}"
```

A **cropped screenshot**, with original filename, source directory, capture
timestamp, and exact crop geometry intact. Blob metadata parsing is worth its
own pass.

### Extraction result

```
3,852,198 B source
   → slim pass (lxml)  → 8 blobs (2,822,412 B) + slim.xml (89,925 B)
   → DuckDB read_xml   → 231 messages / 14 parts / 12 addrs → Parquet
```

Direction breakdown: sms sent 173, sms received 52, mms sent 5, mms received 1.

The null-body case, verbatim from the run:

```
row 227  2022-11-03 17:55  received  body_present=false
         from:18102959303  to:8102959302
         image/jpeg→088ae854, image/jpeg→bf676610, image/jpeg→555435db
```

Row 227 is also the only *received* MMS and the only one whose addresses lack
the `+1` prefix — same parties, two formats, one file.

## Meta JSON mojibake — verified 2026-09-11

Tested against documented Facebook export payload shapes. No Meta export of
Matt's was available, so these are the published payload forms, not his files.

| case | byte-fix | post-parse latin-1 | pairwise regex | ftfy |
|---|---|---|---|---|
| `Rados\u00c5\u0082aw` | Radosław | Radosław | Radosław | Radosław |
| `\u00f0\u009f\u0092\u008e` (💎) | 💎 | 💎 | **П** ✗ | 💎 |
| `\u00e2\u009d\u00a4\u00ef\u00b8\u008f` (❤️) | ❤️ | ❤️ | **¤ϸ** ✗ | ❤️ |
| `ok \u00f0\u009f\u0092\u008e thanks` | ok 💎 thanks | ok 💎 thanks | **ok П thanks** ✗ | ok 💎 thanks |
| already clean ASCII | unchanged | unchanged | unchanged | unchanged |

Three approaches work. The pairwise-regex form — the most widely copied answer
— assumes two escape sequences per character. Accented Latin is two, so it
appears correct and destroys every emoji with no error.

**Decision:** byte-level fix before `json.loads` as primary; `ftfy.fix_text()`
after as a detector only.

## Reproduction

```bash
# reader bake-off
pdftotext -enc UTF-8 file.pdf out_poppler.txt
mutool draw -F text -o out_mutool.txt file.pdf 1-24
python -c "from pypdf import PdfReader; ..."

# the substitution, ground truth
qpdf --qdf --object-streams=disable file.pdf qdf.pdf
grep -o '/F4 [0-9]* Tf[^)]*([^)]*)' qdf.pdf

# XML
python slim.py source.xml out/
duckdb -c "LOAD webbed; SELECT count(*) FROM read_xml('out/slim.xml')"
```
