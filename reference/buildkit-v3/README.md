# casekit — build kit

Planning output for a local evidence extraction and packaging tool.
Generated 2026-09-11. Greenfield, single workstream.

## Read in this order

| # | File | What it is |
|---|---|---|
| 0 | **`OPEN-DECISIONS.md`** | Seven unresolved items; three block Phase 0. Read with the kickoff. |
| 0 | **`KICKOFF.md`** | **Paste this into Claude Code first.** Session-zero orientation prompt. |
| 1 | **`RULES.md`** | **Operating agreement. Outranks everything else here.** |
| 2 | `BUILD_GUIDE.md` | One-page orientation and architecture sketch |
| 3 | `FINDINGS.md` | What the real evidence files actually contain, with reproduction commands |
| 4 | `STACK.md` | Chosen stack, versions, rejected alternatives |
| 5 | `GOTCHAS.md` | Ranked failure modes — most were hit during planning |
| 6 | `SPLIT.md` | The engine contract (the boundary that matters) |
| 7 | `PHASES.md` | Build sequence with hard exit criteria |
| 8 | `PROMPTS.md` | Copy-paste task prompts, one per phase |
| 9 | `TOOL-CATALOG.md` | Everything needed to build and run |
| 10 | `INTEGRATION.md` | Deferred: Temporal, n8n, the Go engine boundary, promotion and hash levels. Nothing decided — plus one thing that shouldn't wait. |
| 11 | `DIAGRAMS.html` | All of the above, visually — open in a browser |

## Scaffold

`scaffold/` is the stub tree. Every file carries a `TODO(claude)` naming what
goes there and which phase implements it. Copy it to the repo root to start.

## Start here

```
cd <repo>
# 1. copy scaffold/ to the repo root
# 2. put both reference files in docs/reference/
# 3. paste KICKOFF.md into a fresh Claude Code session
# 4. when it reports back, paste PROMPTS.md → Phase 0
```

### Formats covered in the core build

| Format | Phase | Engine | Status |
|---|---|---|---|
| **PDF** transcripts | 4 | poppler + raw-stream channel | verified on a real file |
| **XML** SMS/MMS exports | 5 | duckxml (slim pass + DuckDB) | verified on a real file |
| **JSON** Facebook / Instagram / generic | 5b | duckjson (normalize + DuckDB) | gotchas documented, unverified |
| **ZIP** containers | 5c | container + ziprepair ladder | gotchas documented, unverified |

ZIP is a **container**, not a leaf format — most evidence arrives zipped, so
Phase 5c unwraps it and routes each member back through the pipeline. That
makes the pipeline recursive, with bounded depth and expansion caps.

XML and JSON produce the **same** table shape — `messages` / `mms_parts` /
`mms_addrs` — so SMS threads and Facebook threads land in one queryable corpus.

Screenshots (OCR), call logs, DOCX/OOXML and plain text are Phase 10. DOCX is
itself a zip, so Phase 5c already does half of it.

**Phase 6b** builds the corpus index — one DuckDB view across every package and
every format, plus corroboration coverage: which messages have independent
support from a second source, where the gaps are, and where two sources
disagree. Derived and disposable; rebuildable from the packages alone.

Phases 0–6b are the usable product. 7–10 are deferred deliberately — do not
start them until 0–6 are running on real files.

## Known open questions

Six, listed in `DIAGRAMS.html` §12. **None of them block Phases 0–5.**

## One thing worth knowing before you start

The reference PDF in this corpus silently replaced every emoji with a single
repeated symbol, and four of the seven most widely used PDF readers report that
symbol as an ordinary letter. That is why this tool exists, why there is no
default engine, and why every extraction is graded against a prediction derived
from the file itself.
