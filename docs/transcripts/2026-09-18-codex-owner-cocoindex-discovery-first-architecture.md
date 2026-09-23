---
title: Owner + Codex — CocoIndex discovery over EVERYTHING first, then selection, then Go engine intake in place
platform: Codex (conversation with the owner)
model: not stated by owner
created: 2026-09-18
tags: [architecture, cocoindex, discovery-index, vault-sorting, go-engine, intake-in-place, duckdb, sbv, selection, review-baseline, owner-confirmed]
summary: "Owner-confirmed sequence ('yes!!!!!!!!!', 'FOR FUCKS SAKE YES!'): (1) CocoIndex discovery/index of the ENTIRE vault/corpus, case-related or not — find, classify, search, dedupe, relate, fix the vault structure, put things where they belong; (2) select what belongs in the case platform; (3) Go engine intake IN PLACE, orchestrating DuckDB/SBV/other registered handlers; (4) lossless package + attachments + hashes + provenance, normalized records/bounded chunks/entities/temporal data; (5) Weaviate/graph/timeline/analysis. Corrects Claude's 22:15 claim that CocoIndex only indexes Go-engine output. Codex's review flag list: full Go intake as a prerequisite to discovery; CocoIndex downstream-only; format-specific side pipelines; whole-file memory loads; discarded attachments/metadata; invented decisions; local shortcuts turned into global rules."
provenance:
  saved_by: "Claude Code · Opus 5"
  saved_at: 2026-09-18T22:28:00-04:00
  shared_by: owner, pasted into chat 2026-09-18 22:26 EDT prefixed "JUST READ....."
  content: verbatim paste (Codex turns and the owner's own turns interleaved as pasted); only this front matter was added. "Pasted text.txtTXT" is a Codex citation chip.
  why_it_matters: supersedes the 22:15 URGENT-TODO consequence line; this is the baseline every Intake/Probata finding is judged against
---

> _Byline: transcript from Codex + owner, saved verbatim by Claude Code · Opus 5 · 2026-09-18_

Yes. That’s an important correction, and it changes the order of operations.
You were not saying:
Go intakes everything first → CocoIndex indexes the Go output.
You wanted:
CocoIndex first, across the casepad, so you can discover what is actually there and decide what deserves full intake.
So the intended shape is closer to:

```
ENTIRE CASEPAD / B2 CORPUS
        ↓
COCOINDEX DISCOVERY / INDEX
        ↓
searchable inventory of what exists
        ↓
classify / discover / select
        ↓
"these files/packages/chats/messages matter"
        ↓
GO ENGINE INTAKE
        ↓
DuckDB / SBV / other handler
        ↓
lossless source package + attachments + provenance
        ↓
normalized records / chunks / entities / timeline data
        ↓
richer downstream indexes / graph / analysis
```

That makes a lot more sense of what you've been saying.
The previous Claude conclusion —
“The Go engine processes every file... The CocoIndex app does no extraction. It indexes what the engine produces.” Pasted text.txtTXT
— is therefore too broad and wrong as a system-level ordering.
The Go engine can still be the authority for actual intake/processing, and DuckDB can still be its primary extractor, without requiring every half-million source files to go through full intake before you can even find out which ones matter.
The distinction is:
CocoIndex first-pass indexing

* broad corpus coverage;
* cheap enough to run over everything;
* identify what exists;
* expose names/content/signatures/metadata;
* enable search;
* identify likely chats, messages, exports, evidence-bearing packages;
* help you decide what to intake.

Go engine intake

* happens after selection/prioritization;
* performs the authoritative processing;
* invokes DuckDB/SBV/etc.;
* preserves originals and attachments;
* builds source packages and provenance;
* normalizes records;
* generates the richer structured case data.

So CocoIndex is not downstream-only.
It has a pre-intake discovery role.
And then, after authoritative intake, it can also index the richer derived output if useful.
That gives you two legitimate CocoIndex surfaces:

```
RAW CORPUS
   ↓
CocoIndex discovery index
   ↓
SELECT
   ↓
Go intake
   ↓
structured/normalized outputs
   ↓
CocoIndex / Weaviate richer searchable index
```

That also explains why you were so focused on getting the case-wide CocoIndex app running first instead of Claude disappearing into specialized SMS and AI-chat pipelines: you wanted visibility over the corpus so you could make informed intake decisions instead
There's two things to understand here. There's the sorting and. Fucking fixing. Of the Volt structure that includes them. Everything that I have.SOME C ASE related, some of it not. Every fucking thing. Then there's. The fucking. Application processing system. After we figure out what the fuck everything is and put it where the fuck it goes. It was supposed to be ingested in place. Into the fucking platform.
Yes. That is the distinction I was still collapsing.
There are two different systems/jobs, and they happen in sequence.
1. First: fix and understand the entire vault/corpus
This is everything you have, not “case evidence intake.”

```
EVERYTHING
├── case-related
├── probably case-related
├── unrelated personal material
├── AI chats
├── exports
├── documents
├── screenshots
├── media
├── backups
├── duplicates
├── random recovered files
└── unknown shit
        ↓
DISCOVER / INDEX / IDENTIFY
        ↓
figure out what everything actually is
        ↓
classify it
        ↓
dedupe / identify relationships
        ↓
fix the vault/folder/package structure
        ↓
put things where they belong
```

That is where the case-wide CocoIndex system comes first.
Its job is to give you visibility over the mess so you can search it, identify things, classify them, discover packages/relationships, and straighten out the actual storage structure.
It is not yet the formal application-processing/intake pipeline.
And it absolutely includes non-case material because you can't determine what belongs in the case system until you know what the files are.
2. Then: the application processing/intake system
Once the underlying corpus has been identified and put where it belongs:

```
ORGANIZED / UNDERSTOOD CORPUS
        ↓
select material that belongs in the platform
        ↓
INGEST IT IN PLACE
        ↓
Go processing engine
        ↓
signature / handler selection
        ├── DuckDB ELT
        ├── SBV
        ├── document handlers
```


```
ENTIRE CASEPAD / B2 CORPUS
        ↓
COCOINDEX DISCOVERY / INDEX
        ↓
searchable inventory of what exists
        ↓
classify / discover / select
        ↓
"these files/packages/chats/messages matter"
        ↓
GO ENGINE INTAKE
        ↓
DuckDB / SBV / other handler
        ↓
lossless source package + attachments + provenance
        ↓
normalized records / chunks / entities / timeline data
        ↓
richer downstream indexes / graph / analysis



yes!!!!!!!!!
```

Exactly. That is the architecture. Lock the understanding there.
The critical boundary is:

```
ENTIRE CASEPAD / B2 CORPUS
        ↓
COCOINDEX DISCOVERY / INDEX
        ↓
searchable inventory of EVERYTHING
        ↓
identify / classify / sort / dedupe / organize
        ↓
determine what belongs in the case-processing platform
        ↓
SELECT FOR INTAKE
        ↓
GO ENGINE INTAKE — IN PLACE
        ↓
Go orchestrates the processing
        ↓
DuckDB / SBV / other registered handler
        ↓
lossless source package
+ attachments
+ hashes
+ provenance
        ↓
normalized records / bounded chunks / entities / temporal data
        ↓
Weaviate / graph / timeline / analysis / work products
```

And the two parts must not be collapsed:
CocoIndex answers: “What the fuck do I have, where is it, what is it related to, and where should it go?”
The application/Go engine answers: “Now that this material belongs in the case system, process it correctly and losslessly in place.”
That also means the first CocoIndex index covers everything, including material that ultimately turns out to have nothing to do with the case. Determining that is part of the discovery/sorting job.
This is the model I’ll use for the rest of the review.
FOR FUCKS SAKE YES!
Then that’s the frame. I’m not going to drift off it again.
From here, every review finding gets judged against this sequence:
1. CocoIndex discovery/index of the entire vault/corpus
Figure out what exists, classify it, search it, identify packages/duplicates/relationships, and determine what belongs where.
2. Selection for case intake
Only after discovery do we decide what enters the case-processing platform.
3. Go engine intake in place
Go remains the processing/orchestration authority and invokes DuckDB, SBV, or other handlers as appropriate.
4. Lossless preservation and normalization
Originals, attachments, hashes, provenance, normalized records, chunks, entities, temporal data.
5. Downstream case intelligence
Weaviate, graph, timelines, analysis, evidence/work products.
So if I see Claude or the code doing any of these, I’ll flag it immediately:

* making full Go intake a prerequisite to corpus discovery;
* making CocoIndex downstream-only;
* building format-specific side pipelines instead of integrating them;
* loading whole source files into memory;
* discarding attachments or source metadata;
* inventing a new architecture decision where one already exists;
* turning a local implementation shortcut into a global rule.

That is the review baseline now.
