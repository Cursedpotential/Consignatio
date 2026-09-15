---
tags: [intake, pdf, extraction, opendataloader, spike, receipt]
---

> _Byline: Claude Code · Sonnet 5 · 2026-09-14_

# OpenDataLoader PDF — bounded live spike

Owner directive (2026-09-14 23:39 EDT): "add opendataloader as a tool, look
into." This is a bounded, read-only live spike run entirely on `ovh-files`
(`100.91.190.107`), inside a throwaway `python:3.12-slim` Docker container
(`opendataloader-spike`). Nothing ran on the desktop. No corpus source was
written to; no PDFs were deleted; no commits were made.

Reference doc for the library itself (written before this spike):
`E:/AI_Workspace/Projects/Propria/docs/reference/opendataloader-pdf-2026-09-14.md`.

## Environment / versions (verified live)

| Component | Version |
|---|---|
| Container base | `python:3.12-slim` |
| Java | OpenJDK 21.0.12.1 (Debian build) |
| Python | 3.12.14 |
| `opendataloader-pdf` (PyPI) | 2.5.8 (reference doc predates this; it named 2.3.0) |
| `pypdf` (control) | 6.18.1 |
| `docling` (hybrid backend, pulled in by `opendataloader-pdf[hybrid]`) | 2.127.0 |
| tesseract-ocr (system, installed for hybrid OCR) | 5.5.0 |

Install footprint: fast-mode-only install (`opendataloader-pdf` + `pypdf`) is
small (JVM + a couple of wheels). Adding `opendataloader-pdf[hybrid]` (Docling
backend, pulls `torch`/`transformers`/`docling-ibm-models`/etc.) brought
`/usr/local/lib/python3.12/site-packages` to **6.4 GB** — slightly over the
6 GB soft cap set for this spike, but the host had 72 GB free before the
install and 58 GB free after, well above the 20 GB floor, so it was left in
place rather than aborted. Two additional system packages were needed beyond
the documented `--ocr-engine` flag to make hybrid OCR actually run in this
minimal base image (see "Hybrid mode" below): `libgl1`, `libglib2.0-0` (small,
not part of the 6.4 GB figure — that's Python packages only).

## Inputs

10 real files, read-only, ≤ 1.6 MB total for the fast-mode batch plus ~1 MB
for two additional scanned-PDF candidates — all copied with `rclone copy`
(dry-run first, per policy) from the read-only `r2:casebible-sorted` bucket
(via `/opt/casebible/rclone.conf` on ovh-files) into
`/data/probata/exchange/opendataloader-spike/inputs{,-scan}/`, plus one file
already staged at `/data/probata/exchange/spacedrive-gate/sample/pdf/`.
No `b2:` rclone remote existed on ovh-files at spike time, so the R2 mount /
remote (documented fallback) was used instead of B2.

Fast-mode batch (`inputs/`):
- `CaseManagement/_intake/legal/.../rule-3204-proceedings-affecting-children-michigan-court-rule.pdf`
- `.../rule-3205-prior-and-subsequent-orders-and-judgments-affectin.pdf`
- `.../rule-3206-initiating-a-case-michigan-court-rules.pdf`
- `CaseManagement/filings/EX PARTE ORDER FOR TEMPORARY CUSTODY AND PARENTING TIME.pdf`
- `CaseManagement/filings/Motion ex parte.pdf`
- `CaseManagement/filings/Notice-Motion-Practice.pdf`
- `KnowledgeBase/_intake/backupimport_CSV/courts.mi.gov_..._FAQ2013-01.pdf`
- `KnowledgeBase/_intake/backupimport_CSV/courts.mi.gov_..._focb_2013MCSF.pdf`
- `KnowledgeBase/_intake/backupimport_CSV/courts.mi.gov_..._focb_2013MCSFSuppl.pdf`
- `sms-20221104021809.pdf` (from the gate sample dir — a real-text SMS-export
  PDF, not image-only; kept in the batch anyway as a table-heavy case)

Scanned/image-only candidates (`inputs-scan/`, found by grepping `rclone lsf`
for `scan|camscanner|fax`):
- `CaseManagement/filings/Scan 10 Jul 23 · 15·15·37.pdf` — **confirmed
  image-only** (pypdf extracts 0 chars from its 1 page): a faxed cover sheet.
  Used for the hybrid-OCR test below.
- `KnowledgeBase/notes/Adobe Scan Apr 13, 2024 (1).pdf` — has its own
  Adobe-OCR text layer (4,264 chars), so not a clean "no text layer" case;
  included for context only, not used further.

## Finding: 3 of the 9 R2 files are not valid PDFs at all

`courts.mi.gov_..._FAQ2013-01.pdf`, `..._focb_2013MCSF.pdf`, and
`..._focb_2013MCSFSuppl.pdf` are **not PDFs** — their first bytes are random
binary (`\xbe\xf2\xa4\xef...`, `\x02\xfd\x06\x04...`, `\x07\xee\xb0m...`), not
a `%PDF-` header. This is independent of OpenDataLoader: **pypdf fails on the
same three files** with `PdfStreamError: Stream has ended unexpectedly`, used
here as a control. This matches the known corpus-corruption pattern from the
2026 Google Drive restore (scrambled/zero-filled recoveries) already on file
in `zero-filled-quarantine-2026-09-13` / `corpus-disaster-origin` memory notes
— it is not something a better PDF extractor can recover from; these three
inputs need re-sourcing from an uncorrupted copy, not better parsing.

OpenDataLoader's behavior on a mixed batch with these files: the single JVM
CLI invocation logs `Error: '<name>' is not a valid PDF file (missing %PDF-
header)` per bad file, continues processing every other file in the batch,
and only raises a non-zero exit / `CalledProcessError` at the very end (the
Python wrapper doesn't expose per-file error objects — callers must catch the
batch-level exception and then check which output files actually exist).

## Fast-mode results (`-f json,markdown`, one batch call, all 10 files)

Wall time for the whole batch: **5.58 s** (includes JVM startup once; 3 files
fail fast on header check). 7 of 10 files produced valid JSON+Markdown:

| File | Input size | Pages | JSON bytes | MD bytes | Elements* | Tables |
|---|---:|---:|---:|---:|---:|---:|
| rule-3204 (court rule) | 34,737 B | 3 | 11,254 | 4,381 | 22 | 0 |
| rule-3205 (court rule) | 37,103 B | 3 | 12,253 | 3,594 | 27 | 0 |
| rule-3206 (court rule) | 43,345 B | 4 | 17,981 | 8,086 | 32 | 0 |
| EX PARTE ORDER (custody) | 177,356 B | 11 | 47,373 | 13,550 | 116 | 0 |
| Motion ex parte | 173,986 B | 9 | 34,801 | 18,965 | 52 | 0 |
| Notice-Motion-Practice | 310,550 B | 1 | 2,189 | 483 | 6 | 0 |
| sms-20221104021809 (SMS export) | 118,332 B | 9 | 623,973 | 24,279 | 2,100 | **9** |
| FAQ2013-01.pdf | 76,299 B | — | **corrupted, not a PDF** | | | |
| focb_2013MCSF.pdf | 271,545 B | — | **corrupted, not a PDF** | | | |
| focb_2013MCSFSuppl.pdf | 406,942 B | — | **corrupted, not a PDF** | | | |

\* "Elements" = count of JSON nodes carrying a `type`/`category` key
(paragraphs, headings, text blocks, table cells, images, …), a rough proxy
for document richness, not a tool-reported metric.

The SMS-export PDF's 9 detected "tables" are message-thread rows OpenDataLoader
grouped into a table structure — a reasonable call given the PDF's actual
layout (sender/date/content columns), and a good illustration that table
detection fires even on non-"legal-form" layouts.

## Before/after: pypdf vs OpenDataLoader Markdown

### File 1 — `rule-3204-proceedings-affecting-children-michigan-court-rule.pdf` (Michigan Court Rule, 3 pages)

**pypdf `extract_text()`** (raw reading order, line-wrapped mid-sentence):

```
© Copyright 2025, vLex. All Rights Reserved.
Copy for use in the context of the business of the vLex customer only. Otherwise, distribution or reproduction is not permitted
Rule 3.204. Proceedings Affecting Children
Library:
Michigan Court Rules
Edition:
2025
Currency:
As amended through October 7, 2025
Year:
2025
Citation:
Mich. Ct. R. 3.204
 
vLex Document Id:
 VLEX-1077629073
Link:
 
https://app.vlex.com/vid/rule-3-204-proceedings-1077629073
December 17, 2025 08:06
1/3
Downloaded from vLex by MATTHEW SALEM
(A)
 Unless the 
court orders otherwise for good cause, if a circuit court action involving 
child support,
custody, or parenting time is pending, or if the circuit court 
has continuing jurisdiction over such
matters because of a prior action:
(1)
 A new action concerning support, custody 
or parenting time of the same child must be filed
```

**OpenDataLoader Markdown** (headings detected, metadata row folded into a
table, numbered clauses reassembled into coherent paragraphs, footer/page
furniture separated):

```markdown
© Copyright 2025, vLex. All Rights Reserved. Copy for use in the context of the business of the vLex customer only. Otherwise, distribution or reproduction is not permitted

# Rule 3.204. Proceedings Affecting Children

|Library: Michigan Court Rules Edition: 2025 Currency: As amended through October 7, 2025 Year: 2025 Citation: Mich. Ct. R. 3.204|
|---|


vLex Document Id: VLEX-1077629073 Link: https://app.vlex.com/vid/rule-3-204-proceedings-1077629073

- (A) Unless the court orders otherwise for good cause, if a circuit court action involving child support, custody, or parenting time is pending, or if the circuit court has continuing jurisdiction over such matters because of a prior action:

- (1) A new action concerning support, custody or parenting time of the same child must be filed as a motion in the earlier action if the relief sought would have been available in the original cause of action. If the relief sought was not available in the original action, the new action must be filed as a new complaint.
- (2) A new action for the support, custody, or parenting time of a different child of the same parents must be filed in the same county as the prior action if the circuit court for that county has jurisdiction over the new action and the new case must be assigned to the same judge to whom the previous action was assigned.
```

**Most telling differences:** (1) pypdf splits `(A)` onto its own line, then
wraps mid-word/mid-phrase (`involving \nchild support,\ncustody`) because it
follows raw content-stream token order with no reflow — a downstream chunker
would need its own sentence-reassembly pass. OpenDataLoader reflows each
paragraph into one line and correctly reconstructs the `(A)` / `(1)` / `(2)`
outline as a nested Markdown list. (2) OpenDataLoader recognized the little
`Library: ... Citation: ...` metadata strip as a table and emitted a real
Markdown table row; pypdf just emits the same 6 key/value pairs as 12 bare
lines with no structural marker at all.

### File 2 — `rule-3206-initiating-a-case-michigan-court-rules.pdf` (4 pages, heavier nesting)

OpenDataLoader Markdown correctly kept 6 levels of `(A)/(1)/(a)` nesting as
readable sub-bullets across the whole 4-page rule (not reproduced in full
here for length — see `/work/out/rule-3206-initiating-a-case-michigan-court-rules.md`
on ovh-files); pypdf's plain-text output for the same rule breaks every
sub-clause onto its own physical PDF line, so a naive text-based downstream
parser would misjudge sentence boundaries constantly.

## Sample JSON element (with bounding box)

From `rule-3204-...json`, a heading element (`kids[1]`):

```json
{
  "type": "heading",
  "pdfua_tag": "H1",
  "id": 5,
  "level": "Doctitle",
  "page number": 1,
  "bounding box": [34.464, 723.401, 411.97, 734.975],
  "heading level": 1,
  "font": "NimbusSanL-Bold",
  "font size": 18.432,
  "text color": "[0.0, 0.0, 0.0]",
  "content": "Rule 3.204. Proceedings Affecting Children"
}
```

And a table cell from the SMS-export file's detected message-thread table
(`sms-20221104021809.json`), showing the nested row/cell/paragraph shape:

```json
{
  "type": "table",
  "pdfua_tag": "Table",
  "id": 1,
  "page number": 1,
  "bounding box": [6.0, 18.0, 606.0, 759.75],
  "number of rows": 25,
  "number of columns": 4,
  "rows": [
    {
      "type": "table row",
      "row number": 1,
      "cells": [
        {
          "type": "table cell",
          "pdfua_tag": "TD",
          "row number": 1,
          "column number": 1,
          "row span": 1,
          "column span": 1,
          "bounding box": [6.375, 729.75, 87.75, 759.375],
          "kids": [ { "type": "paragraph", "pdfua_tag": "P", "content": "..." } ]
        }
      ]
    }
  ]
}
```

Every element carries a page number and a `[x0, y0, x1, y1]` PDF-space
bounding box, plus a `pdfua_tag` (`P`, `H1`, `Table`, `TD`, …) that maps
directly onto PDF/UA structure-tree roles — useful for downstream highlighting
/ provenance UI without re-parsing the PDF.

## Hybrid mode (Docling backend) — scanned/image-only PDF

Target: `Scan 10 Jul 23 · 15·15·37.pdf`, a 1-page faxed cover sheet,
confirmed image-only (pypdf: 0 characters extracted). Fast mode alone (no
`--hybrid`) confirms this: its Markdown output is just an embedded image
reference (`![](<..._images/imageFile1.png>)`), 56 bytes, no text — the
expected "auto triage misses image-only scans" behavior called out in the
reference doc.

**Getting hybrid mode actually running required two undocumented fixes**
beyond the reference doc's recorded command:

1. `opendataloader-pdf-hybrid`'s default OCR engine (`easyocr`) fails to
   import in a `python:3.12-slim` base: `ImportError: libxcb.so.1: cannot
   open shared object file`. Switched to `--ocr-engine tesseract` (installed
   `tesseract-ocr` via apt).
2. Tesseract's language auto-detect picked `spa` (not installed) and then
   rejected `--ocr-lang en` (Docling's tesseract-cli wrapper wants the
   3-letter ISO code, not `en`) — needed `--ocr-lang eng` explicitly.
3. Even after that, the *table-structure* stage (`docling-ibm-models`, used
   for **every** Docling document, not just OCR) imports `cv2` too, and
   `cv2` needs `libGL.so.1` which isn't in the slim base either — installed
   `libgl1 libglib2.0-0` (apt, small).

After those three fixes, `--hybrid docling-fast --hybrid-mode full` against
the hybrid server (`opendataloader-pdf-hybrid --port 5002 --ocr-engine
tesseract --ocr-lang eng`) succeeded:

- **Elapsed: 106.78 s for 1 page** on CPU (no GPU on ovh-files) — this is the
  single most important capacity-planning number from this spike: CPU OCR is
  roughly **~1.5–2 minutes per page**, not seconds. Any real hybrid-OCR
  workload needs either a GPU box, a small worker pool, or to be treated as
  a background/batch job, never an inline request.
- OCR quality on this particular fax was **mixed**: it correctly read the fax
  header fields (`FAX NO.`, `DATE`, `DOCUMENT PAGES`, `07-10-2023 15:20`,
  `***SUCCESSFUL TX NOTICE***`) and the sign-off name (misread "Salem" as
  "Selem"), but the body paragraph of the actual letter came back heavily
  garbled (`"EI eE © FORCES bn Fie erreeeeret SPs Get Eee Garment..."`) —
  consistent with a low-resolution fax-quality scan, not a tool defect.
  This is a realistic result, not a cherry-picked good one.

## Recommendation for `extractors.py`

Current state: `Consignatio/Intake/backend/src/casebible_index/extractors.py:110-124`
uses pypdf's raw `extract_text()` only — no reading order, no tables, no OCR.

Proposed integration shape (not implemented in this spike — read-only per
task scope):

1. **Add OpenDataLoader as a second extraction backend**, selected the same
   way the corpus already treats content-hash-keyed sidecars: run
   `opendataloader_pdf.convert([path], output_dir=<tmp>, format=["json"])`
   once per file (batch multiple files per JVM invocation where possible —
   fast mode is ~0.5–0.8 s/file amortized, dominated by JVM startup, so
   batching matters for throughput), then store the resulting JSON verbatim
   as a sidecar keyed by the same content hash Intake already uses for other
   extraction artifacts (see `docs/DOCUMENT-HANDLING-AND-DEDUPE.md` /
   `docstore-always-registered` pattern) — e.g.
   `<content_hash>.opendataloader.json`. The JSON's own `kids[].bounding box`
   + `pdfua_tag` fields are exactly the shape Intake's atomic-units /
   provenance UI wants (page number + bbox + semantic role per element)
   without extra normalization work.
2. **Wrap `convert()` calls to survive partial-batch failure**: as shown
   above, a single corrupt file in a batch raises `CalledProcessError` for
   the *whole* batch even though good files already got their output
   written — callers must check `output_dir` contents after catching the
   exception rather than trusting the return value (`convert()` returns
   `None` even on success).
3. **Treat hybrid/OCR as an explicitly separate, opt-in, likely-async path**
   given the ~100 s/page CPU cost measured here — not something invoked
   inline in the normal per-file extraction path. A sensible trigger: run
   fast mode first, and only if fast-mode text density (chars/page) is
   near zero AND the source is flagged as scanned/photo/fax, queue an OCR
   job separately.
4. **Keep pypdf as the corruption-detection control**: this spike showed
   both tools agree on which files are structurally broken (`%PDF-` header
   missing), so a cheap pypdf `PdfReader()` open-check is a reasonable fast
   pre-filter before spending a JVM invocation on a batch.
5. Word/Excel are out of scope for OpenDataLoader (PDF-only) — no change to
   however Intake currently handles those formats.

## Artifacts left in place (ovh-files, read-only corpus untouched)

- Container `opendataloader-spike` — **stopped** (`docker stop`, confirmed
  `Exited (137)`), not removed, with all installs (Java, opendataloader-pdf
  2.5.8, docling 2.127.0 hybrid extras, tesseract-ocr) intact for inspection
  or resuming with `docker start opendataloader-spike`.
- `/data/probata/exchange/opendataloader-spike/inputs/` — 9 files copied from
  `r2:casebible-sorted` (read-only source untouched).
- `/data/probata/exchange/opendataloader-spike/inputs-scan/` — 2 more scanned
  candidates copied the same way.
- `/data/probata/exchange/opendataloader-spike/out/`, `out-scan/`,
  `out-hybrid/`, `out.attempt1/` — all conversion outputs (JSON + Markdown +
  extracted images + pypdf `.txt` controls + `_summary.json`).
- `run.log` / `run2.log` / `run3.log`, `hybrid-server*.log` — full stdout/stderr
  from every attempt, including the three failed hybrid-server configs, kept
  for provenance rather than deleted.
- Tracked spike scripts (not scratch/temp, per the case-bible
  `require_tracked_code` hook): `docs/spikes/opendataloader-run.py`,
  `opendataloader-scan-fastmode.py`, `opendataloader-hybrid-run.py`,
  `opendataloader-spike-setup.sh`, `opendataloader-hybrid-tesseract-setup.sh`,
  `opendataloader-libgl-setup.sh` in this same `Intake` repo.

Final disk state on ovh-files: 59 GB free on `/` (started at 72 GB free;
the hybrid extras install used ~13 GB of that, matching the 6.4 GB Python
site-packages figure plus JRE/tesseract/apt cache/docker image layers).

## Bake-off parity with FINDINGS.md

Requested by the parent session as a required follow-up: check OpenDataLoader
against the same reference file and known-glyph edge case already documented
in `E:/AI_Workspace/Projects/Propria/projects/consignatio/repair-tool-kit/FINDINGS.md`
(2026-09-11), so a new tool can be slotted into that existing bake-off table.

**File:** `+18102689630 (1) (1).pdf` (the sanitized form of this name is
`_18102689630__1___1_.pdf`), 36,025 bytes, sha256
`f18e250e5aca784f2043dc6f141eca983a2a82e29ba55ebf3bb82b91d39da48b` — **matches
the FINDINGS.md hash exactly**, confirming it's the same reference file.
Located read-only via `rclone lsf r2:casebible-sorted --format sp` filtered to
PDFs of exactly 36,025 bytes (two same-sized copies exist in the sorted tree;
`EvidenceVault/messaging/sms/+18102689630 (1) (1).pdf` was used). Copied
into the spike container's own working directory
(`/data/probata/exchange/opendataloader-spike/inputs-bakeoff/`, which is the
host-side half of the same bind mount that is `/work` inside
`opendataloader-spike` — no other copy was made) and not modified.

**Ground truth (FINDINGS.md):** the line `Nvm she pooped` is immediately
followed by one glyph from font `/F4` (ZapfDingbats), byte `0x6E`, which
should decode to U+25A0 BLACK SQUARE (■). Across the whole 24-page document
there are 22 such show-operations totaling 33 glyphs, all the same
substituted byte. Three readers (poppler, pypdf, pypdfium2) recover
`■`/U+25A0 for all 33; three (pdf.js, pdfminer.six, pdfplumber) return the
raw byte as `n`/U+006E for all 33; mutool maps it to `I`/U+0049 (a value
corresponding to nothing) for all 33.

**Commands run** (inside the container, via a tracked script,
`docs/spikes/opendataloader-bakeoff.py`):

```python
opendataloader_pdf.convert(
    ["/work/inputs-bakeoff/+18102689630 (1) (1).pdf"],
    output_dir="/work/out-bakeoff",
    format=["text", "markdown", "json"],
)
# control:
reader = pypdf.PdfReader(INPUT)
full_text = "\n".join((p.extract_text() or "") for p in reader.pages)
```

**Result — side by side:**

| Reader | Text right after "Nvm she pooped" | Codepoint | Non-ASCII glyphs recovered (of 33) |
|---|---|---|---|
| **pypdf (control, this spike)** | `Nvm she pooped ■` | U+25A0 (matches FINDINGS.md exactly) | **33 / 33** |
| **OpenDataLoader fast mode — text** (`-f text`) | `Nvm she pooped` then straight to next message (`Me - 2024-05-23 12:17 AM...`) | **none — glyph is absent, not substituted** | **0 / 33** |
| **OpenDataLoader fast mode — markdown** (`-f markdown`) | Same: `Nvm she pooped` then straight to the next line, no placeholder | **none — glyph is absent** | **0 / 33** |

pypdf reproduces the FINDINGS.md ground truth exactly (33/33 `■`), confirming
this is the same file and the same known behavior — a valid control.

OpenDataLoader's JSON output was also inspected directly for the specific
text run: the element for that message reads
`"+18102689630 - 2024-05-23 12:17 AM Nvm she pooped"` with
`"font": "Helvetica-Bold"` — the run simply ends there. A full scan of every
font name referenced anywhere in the JSON output for this document returns
only `{Helvetica, Helvetica-Bold, Helvetica-Oblique, Courier}` — **ZapfDingbats
never appears at all**, on any of the 24 pages. This is a fourth, previously
undocumented behavior category next to FINDINGS.md's three (correct-Unicode,
raw-byte, wrong-mapping): **silent, traceless omission**. Unlike the raw-byte
readers (`n`, reversible) or mutool (`I`, wrong but present), OpenDataLoader
leaves no artifact at all — nothing in the text, Markdown, or JSON to indicate
a glyph ever existed at that position. The most plausible mechanism, based on
the fast-mode run log's own content-safety/filtering behavior seen elsewhere
in this spike (`WARNING: Text with zero height ... filtered out`,
`WARNING: Detected background`), is that OpenDataLoader treats ZapfDingbats/
symbol-font runs as decorative/non-text content and drops them — a reasonable
default for actual bullets/dingbats, but one that silently destroys real
message content when a producer (here, Stirling-PDF) has (mis)used a symbol
font as a substitution cipher for emoji. `--content-safety-off` was not tried
in this bounded spike; it is the first thing to test if OpenDataLoader is
ever used on this class of file (SMS-to-PDF exports where emoji get mapped
through Symbol/ZapfDingbats/Wingdings) — recommend a follow-up spike (not run
here) checking whether that flag surfaces the raw byte or the correct glyph
before deciding OpenDataLoader is safe for this file family.

**Read-only confirmed:** only `rclone copy` (from a read-only-mounted source
config) into the spike's own working directory was used; the source object in
`r2:casebible-sorted` was never modified. Container stopped again after this
check completed.
