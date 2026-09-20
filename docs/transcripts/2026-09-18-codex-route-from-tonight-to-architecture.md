---
title: Codex — the route from tonight's state to the confirmed architecture (Phase 1 CocoIndex discovery first; build order 1–10)
platform: Codex
model: not stated by owner
created: 2026-09-18
tags: [architecture, build-order, cocoindex, casebible-index, catalog-backed-source, bounded-extraction, discovery-index, go-engine, duckdb-elt, sbv, selection-handoff, codex-review]
summary: "Codex's route: we are structurally miswired, not 5% done. Phase 1 = catalog → CocoIndex discovery (inventory for every object; bounded content where possible; signatures; packages; duplicates) → searchable whole vault → classify/sort/fix vault → SELECT FOR INTAKE (references only). Phase 2 = Go engine intake in place (signature → DuckDB ELT or backup decoder; finish registry/template/standalone DuckDB/RawRecordEnvelope/profferworker wiring; SBV for lossless attachments). Phase 3 = Weaviate/Surreal/Neo4j/timeline/analysis. Build order: (1) catalog-backed CocoIndex source instead of localfs.walk_dir; (2) bounded, source-type-aware discovery content path, no whole-source materialization; (3) make NIM summary optional post-index enrichment; (4) absorb 09-18 signatures into discovery classification, not its orchestration; (5) deploy + five-file proof (small doc, 61 MB conversations.json, 1.3 GB SMS XML, nested archive, unsupported media); (6) full catalog/B2 index; (7) classify/sort/fix the vault; (8) selected-for-intake handoff contract; (9) finish Go DuckDB lane; (10) authoritative in-place intake. Includes a do-not list."
provenance:
  saved_by: "Claude Code · Opus 5"
  saved_at: 2026-09-18T22:40:00-04:00
  shared_by: owner, pasted into chat 2026-09-18 22:38 EDT
  content: verbatim paste; only this front matter was added. "…chat-index.mdMD" strings are Codex citation chips; "[CocoIndex](…utm_source=chatgpt.com)" links are Codex's own citations as pasted.
  why_it_matters: the build order for the Coco Super Index; one conflict with an owner ruling is logged in docs/URGENT-TODO.md 2026-09-18 22:40 (step 3 "summary optional" vs owner 21:58 "THE SUMMARY IS NEEDED")
---

> _Byline: transcript from Codex, saved verbatim by Claude Code · Opus 5 · 2026-09-18_

Yes. And now that the boundary is clear, the path from where you are tonight to the architecture you actually wanted is much simpler than the mess makes it look.
We do not start over. We stop extending the wrong branches and reconnect the pieces in the correct order.
Where you actually are right now
You already have most of the ingredients:

1. A catalog of the B2/vault corpus already exists. The packet shows the catalog has the corpus/file inventory and the `ai_chat_probe` candidate set. CODEX-REVIEW-PACKET-2026-09-18-chat-index.mdMD
2. The CocoIndex discovery app already exists. It has inventory, package detection, fingerprinting, Parquet output, DuckDB search, Weaviate targeting, source locking, search/API/TUI, etc. It just has never been deployed against B2. CODEX-REVIEW-PACKET-2026-09-18-chat-index.mdMD
3. That CocoIndex app's current content path is wrong for your corpus. From the ZIP, it currently reads each source into one `bytes` object, extracts one giant text blob, splits that blob, summarizes it, then embeds it.
4. The 9/18 work produced useful format knowledge, especially AI-chat signatures and ELT templates, but most of its orchestration is a parallel pipeline that we should not promote.
5. The Go processing engine exists, but the intended DuckDB lane is unfinished: its existing ELT Activity is CSV/NDJSON-only, pg_duckdb-based, and isn't wired into the worker. That is a later implementation gap.
6. The lossless SBV attachment implementation exists, which means we don't need to reinvent attachment handling when we reach authoritative intake.

So:
We are not 5% done. We're structurally miswired.
That's fixable.
The actual route

```
                PHASE 1
        ENTIRE B2 / VAULT / CASEPAD
                    │
                    ▼
              CATALOG
        what objects actually exist
                    │
                    ▼
              COCOINDEX
       discovery / understanding layer
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   metadata      content      structure
   identity      discovery    packages
   hashes        search       duplicates
   signatures    chunks       relationships
       │            │            │
       └────────────┼────────────┘
                    ▼
          SEARCHABLE WHOLE VAULT
                    │
                    ▼
       classify / organize / sort
                    │
                    ▼
          SELECT FOR CASE INTAKE
                    │

                PHASE 2
                    ▼
              GO ENGINE
      authoritative processing control
                    │
                    ▼
        signature → registered handler
                    │
           ┌────────┴────────┐
           ▼                 ▼
       DuckDB ELT       backup decoder
                        when necessary
                    │
                    ▼
         IN-PLACE PROCESSING
                    │
                    ▼
       Intake Source Package
       originals / attachments
        hashes / provenance
                    │
                    ▼
        normalized information
                    │
                    ▼

                PHASE 3
        chunks / entities / time
        Weaviate / graph / Surreal
        timeline / analysis / evidence
```

Phase 1 is what we should build first
And this is where Claude kept dragging you away from the goal.
Step 1 — Stop using filesystem walking as the source of truth
The current CocoIndex scaffold does:

```
localfs.walk_dir(...)
```

That made sense for its little desktop proof.
You already have the catalog.
So CocoIndex's source should become approximately:

```
Catalog
  ├─ stable source ID
  ├─ B2 object key / locator
  ├─ size
  ├─ mtime/version
  ├─ existing hashes
  ├─ MIME/extension if known
  └─ other inventory metadata
          ↓
      CocoIndex item
```

Not source bytes.
This is well supported by current CocoIndex. CocoIndex v1 lets an application supply custom sources with ordinary async Python and stable keys, while its processing components retain incremental identity. [CocoIndex](https://cocoindex.io/docs/programming_guide/processing_component/?utm_source=chatgpt.com)
So we do not need to force this architecture through `localfs.walk_dir()`.
Why this matters
The first CocoIndex pass immediately knows:
“These are the half-million things that exist.”
It does not need to rediscover the vault before it can start understanding it.
Step 2 — Separate INVENTORY from CONTENT processing
The existing app mixes too much together.
Right now, for a supported file, the path is effectively:

```
find file
  ↓
READ WHOLE FILE
  ↓
extract whole text
  ↓
summarize
  ↓
chunk
  ↓
embed
  ↓
index
```

That's precisely what gets us into memory and cost problems.
Instead:

```
OBJECT DISCOVERED
        │
        ├──────────────────────────┐
        ▼                          ▼
INVENTORY INDEX              CONTENT INDEX
cheap/universal              only as appropriate
        │                          │
path/object key               signature
size                          content type
hash                          bounded extraction
mtime/version                 bounded chunks
package membership            searchable text
duplicate groups              embeddings
classification                document signals
```

Every object gets inventory representation.
Not every object needs an LLM summary just to exist in the index.
That's important because otherwise you'd burn model credits simply establishing that 500,000 files exist.
Step 3 — Kill the whole-source-in-memory path
Not by raising 8 MiB to 256 MiB.
Remove the assumption.
The unit that may live in memory should be a bounded processing unit, not the complete source.
So:

```
BAD

61 MB conversations.json
        ↓
61 MB bytes
        ↓
huge Python object
        ↓
huge text string
        ↓
hundreds of chunks
```

becomes:

```
GOOD

61 MB conversations.json
        ↓
source locator
        ↓
stream / iterate structure
        ↓
conversation
        ↓
turn / bounded document unit
        ↓
chunk
        ↓
embedding
```

Likewise:

```
1.3 GB SMS XML
```

doesn't become a 1.3 GB Python value merely because CocoIndex knows the object exists.
Important distinction
For Phase 1 discovery, we're not doing the authoritative Go intake yet.
CocoIndex needs enough content understanding to let you find and classify the source.
It does not need to transform every export into its final normalized Case Platform representation.
Step 4 — Remove mandatory summaries from the first corpus pass
The existing scaffold summarizes every text document.
That was fine as an experiment.
It's wrong as a prerequisite to indexing your entire vault.
For the first useful corpus index:

```
REQUIRED
✓ inventory
✓ stable identity
✓ signatures
✓ package relationships
✓ fingerprints
✓ duplicate relationships
✓ searchable content/chunks where obtainable
✓ embeddings where useful
✓ classification signals

NOT REQUIRED TO DISCOVER THE CORPUS
✗ LLM summary of every source
✗ entity extraction from every source
✗ timelines
✗ normalized messages
✗ evidentiary analysis
```

Summarization can become optional enrichment.
That means we can actually index the corpus without your remaining API balance determining whether the vault is discoverable.
Step 5 — Put the 9/18 chat discovery work where it belongs
A bunch of yesterday's work is useful.
Just not as an application.
For example, these become discovery signatures/classifiers:

```
ChatGPT export
Claude export
Gemini Takeout
Gemini clipped conversation
Perplexity clipping
OpenWebUI/Qwen export
chat-memo
SMS Backup & Restore
iMessage export
Facebook Messenger export
Google Voice
mbox
etc.
```

The discovery layer can say:

```
object 728281
    type: claude_export
    confidence: high
    package: Claude export 2026...
    contains: AI conversations
    likely_case_relevance: unknown
```

That's useful before intake.
The special:

```
publish_ai_chats_weaviate.py
run_ai_elt.py
load_surreal.py
```

do not become another permanent architecture.
Their useful knowledge gets absorbed.
Step 6 — Get CocoIndex indexing the corpus
At this point we actually deploy the CocoIndex application.
But not the current app unchanged.
That was Claude's earlier bad proposal.
The minimum viable corpus run should demonstrate five deliberately different objects:

1. ordinary small document;
2. 61 MB Claude `conversations.json`;
3. 1.3 GB SMS XML;
4. an archive/export package with nested files;
5. an image/audio/video or otherwise unsupported content object.

The success criterion is not:
“All five got fully parsed.”
It's:

```
All five are represented in the discovery index.

Nothing blew RAM.

Nothing disappeared because its type was unsupported.

Their source identities/locators are preserved.

Search/discovery finds what can be searched.

Package/signature information survives.

The operator can determine what they are.
```

Then expand to the full corpus.
CocoIndex itself is designed around stable per-item processing components and incremental synchronization, so after the initial corpus sweep, unchanged items don't need their transformation work repeated. [CocoIndex](https://cocoindex.io/docs/getting_started/overview/?utm_source=chatgpt.com)
Step 7 — Now actually solve the vault
Once CocoIndex can answer:
“What do I have?”
we use it for the thing you've been trying to accomplish:

```
Everything
   ↓
case-related
personal unrelated
software
system junk
exports
duplicates
recoveries
AI conversations
message exports
court documents
media
unknown
etc.
```

Then:

```
identify package boundaries
        ↓
identify duplicates
        ↓
identify misplaced material
        ↓
identify likely canonical locations
        ↓
produce organization/sort actions
        ↓
fix the vault structure
```

The current CocoIndex scaffold is deliberately read-only and currently stops at proposals/discovery, which is actually useful here: it means we can determine the reorganization without the indexer spontaneously moving half a million objects.
The execution of those organization decisions is the next operation.
Step 8 — The important boundary: SELECT FOR INTAKE
Now we finally reach the case application.
CocoIndex needs to produce a selection/handoff roughly like:

```
selection_id
source_id
object_locator
source fingerprint/hash
detected signature
package_id
classification
selected_for_intake = true
priority
operator notes/reason
```

Notice what's not there:

```
copied bytes
another copy of the file
giant parsed payload
```

The object stays where it is.
You said ingest in place.
That's what happens.
Phase 2 — Then fix the Go intake lane
Only once Phase 1 is serving its purpose.
This is where the Go work actually belongs.
Step 9 — Give the Go engine the selected source reference

```
CocoIndex selection
        ↓
Go Activity
        ↓
signature
        ↓
handler registry
```

And now the existing rule applies:

```
DuckDB capable of this signature?
            │
       YES ─┴─ NO
        │       │
    DuckDB   registered
      ELT     decoder
```

Go orchestrates that.
Step 10 — Finish the missing Go/DuckDB wiring
The ZIP confirms this is genuinely unfinished implementation, not something you need to rethink.
The current Go engine:

* has no DuckDB entries in its signature registry;
* has an ELT Activity for only CSV/NDJSON;
* doesn't register that Activity with `profferworker`;
* runs that old Activity via pg_duckdb, which is not the standalone DuckDB architecture you settled on.

So later we need exactly this:

```
Go handler registry
        ↓
DuckDB handler type
        ↓
template registry
        ↓
standalone DuckDB execution
        ↓
RawRecordEnvelope contract
        ↓
Go Activity result
```

No Python sidecar architecture required.
No PG acting as the extractor.
Step 11 — Make Intake lossless
This is where yesterday's SMS implementation gets corrected.
For authoritative intake:

```
source stays in place
      +
original identity retained
      +
package manifest
      +
attachments materialized where required
      +
all available source metadata retained
      +
context fingerprints
      +
provenance
```

And then:

```
normalized records
chunks
entities
temporal expressions
relationships
```

The existing SBV implementation has already demonstrated that its MMS path can stream attachment payloads rather than load them all into memory. So we reuse that capability where appropriate rather than letting the new locator-only SQL silently discard media.
Phase 3 — THEN the expensive intelligence
Only now:

```
approved/processed case context
        ↓
Weaviate
        ↓
Surreal / Neo4j
        ↓
timeline
        ↓
entity relationships
        ↓
case analysis
        ↓
potential evidence promotion
```

That's where your application becomes the thing you've been designing.
What I would do next, in exact order
This is the part I don't want Claude turning into seventeen parallel projects.
Build 1 — CocoIndex source correction
Change the existing CocoIndex app so:

```
catalog → stable CocoIndex source items
```

instead of:

```
walk directory → FileLike → whole-file bytes
```

Nothing else first.
Build 2 — Bounded discovery content path
Replace:

```
read_bounded(file)
extract_text(whole bytes)
RecursiveSplitter(whole string)
```

with a source-type-aware bounded discovery path.
No whole-source materialization.
Build 3 — Make enrichment optional
Turn mandatory:

```
NIM summary
```

into optional post-index enrichment.
Embeddings can also be scheduled/batched independently rather than making discovery wait for everything.
Build 4 — Import the useful signature work
Move the 9/18 format knowledge into discovery classification.
Do not import its competing orchestration.
Build 5 — Deploy CocoIndex and prove the five-file test
Only after those four changes.
Build 6 — Index the full catalog/B2 corpus
Now we get the thing you've wanted:
a searchable map of everything you own.
Build 7 — Use it to classify/sort/fix the vault
This is where we identify the case material and correct the larger storage organization.
Build 8 — Define the selected-for-intake handoff
Tiny contract. References only.
Build 9 — Finish the Go engine's DuckDB handler lane
Now we have a reason to finish it: actual selected material is waiting.
Build 10 — Run authoritative in-place intake
Then packages, attachments, normalized records, provenance, downstream analysis.
What NOT to do next
This is equally important.
Do not:

* deploy the existing CocoIndex app unchanged;
* raise `8 MiB → 256 MiB` and call it fixed;
* continue improving the standalone AI-chat pipeline;
* continue improving the standalone SMS timeline pipeline;
* send the entire vault through Go intake merely to discover what's there;
* make Go intake a prerequisite for CocoIndex;
* summarize half a million files with an LLM;
* physically copy everything into Intake;
* make Postgres the extraction engine;
* make CocoIndex parse authoritative normalized case records;
* throw away the 9/18 work—it contains useful signatures/templates;
* turn any of yesterday's emergency shortcuts into permanent architecture.

The shortest path
If I compress everything above to one implementation objective, it's this:
Take `Consignatio/Intake/backend/src/casebible_index`, replace its desktop whole-file filesystem source with a catalog-backed, bounded/streaming discovery source, make costly enrichment optional, absorb yesterday's format-signature knowledge into classification, and get that app indexing the complete B2 corpus. Do not touch the Go intake architecture until that index can tell us what we have and what we actually want to intake.
That's how we get from where you are to the architecture you just confirmed.
And importantly, the review packet's own statement that “no CocoIndex-based index over the catalog files exists as a running thing” gives us an extremely clean milestone: the next major deliverable is the first real catalog-backed CocoIndex corpus index. CODEX-REVIEW-PACKET-2026-09-18-chat-index.mdMD
