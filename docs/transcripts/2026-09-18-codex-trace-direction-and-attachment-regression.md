---
title: Codex direction — trace the existing architecture first; SMS attachment regression is a blocking defect
platform: Codex
model: not stated by owner
created: 2026-09-18
tags: [cocoindex, intake, duckdb-elt, signature-registry, chunking, adr-0053, attachments, source-package, d-154, provenance, sms, regression, codex-review]
summary: "Codex's follow-up: do not fix the whole-file-memory defect by raising limits or adding a large-file-only DuckDB path. DuckDB is the registered extractor for every signature it supports regardless of size; parsers are fallback; CocoIndex is the case-wide orchestrator; sources pass by identity/locator; chunking works on bounded extracted units. Identify existing chunker(s), ADR-0053, handler registry, source/catalog contract and proposal-bundle contract before editing. Adds a blocking defect: the 09-18 SMS sanitizer discards embedded attachment bytes (locator-only), writes no package, and projects only selected fields — contrary to the preserved-original + materialized-attachment + full-provenance design. Names the pattern: three bypasses of existing answers (whole-file reads, parallel chat pipeline, discarded attachments)."
provenance:
  saved_by: "Claude Code · Opus 5"
  saved_at: 2026-09-18T22:12:00-04:00
  shared_by: owner, pasted into chat 2026-09-18 22:09 EDT prefixed "PER CODEX"
  content: verbatim paste; only this front matter was added. "Pasted text.txtTXT" strings are Codex's citation chips as pasted.
  why_it_matters: sets the method for the Intake indexer fix (trace, then smallest wiring change) and opens the SMS attachment regression; follow-up logged in docs/URGENT-TODO.md 2026-09-18 22:15
---

> _Byline: transcript from Codex, saved verbatim by Claude Code · Opus 5 · 2026-09-18_

You have now found the whole-file-memory defect, but do not solve it by raising limits or by creating a large-file-only DuckDB path. Trace the existing architecture first. The intended design already separates corpus orchestration, DuckDB ELT extraction, and chunking. DuckDB is the registered extraction handler for every signature it supports regardless of file size; parsers/decoders are fallback handlers, not the default for “small” sources. CocoIndex remains the case-wide incremental index/orchestration application. The source object should remain in place and be passed by identity/reference/locator, not loaded as a complete Python byte payload. Existing chunking policy operates on bounded extracted units downstream. Reuse the 9/18 format signatures/templates as handlers within that architecture, not as a parallel AI-chat pipeline. Before editing anything, identify the exact existing chunker(s), ADR-0053 requirements, handler registry, source/catalog contract, proposal-bundle contract, and the smallest wiring change that connects them. Do not invent a new chunking policy, change-detection policy, memory threshold, or global rule without identifying the existing decision that authorizes it.

That is the review direction I would continue with.
And the biggest new finding from this pass is: the problem is deeper than the 8 MiB cap, but it does not require a redesign. The already-decided pieces appear to exist; they were wired around instead of wired together.

Yes. This is another concrete architecture violation, not a minor implementation detail.
The current template is explicitly doing the opposite of the design you had established:
`"ATTACHMENTS ARE LOCATOR-ONLY."`
and the sanitizer throws the attachment bytes away, writes no media out, creates no package folder, and retains only the message attributes selected by one query. Pasted text.txtTXT
That was not the design.
What the design actually was
The distinction was:

```
PRESERVED SOURCE / ARCHIVE
        │
        ├── original export
        ├── original archive members
        ├── embedded attachments
        ├── externally referenced attachments when recoverable
        └── immutable hashes / provenance
                     │
                     ▼
              DERIVED RECORDS
                     │
        ├── normalized messages
        ├── metadata
        ├── extracted text
        ├── entities/events
        ├── chunks
        └── analytical projections
```

A normalized Messaging KB record doesn't contain the binary itself, but that does not mean the binary gets discarded.
The binary belongs in preserved source/package storage.
The normalized message points back to it through deterministic provenance.
Attachment locator ≠ attachment preservation
The locator is supposed to tell us where an attachment occurrence came from, for example:

```
source export
message native ID
archive/member path
XML node / row / record
sibling attachment directory
ZIP member
original filename
attachment ID
URL/reference
```

Then, when the actual payload exists, the system was supposed to recover/materialize it, hash it, preserve it, and associate it with the message.
A locator-only record is appropriate when the bytes genuinely aren't available.
It was never supposed to mean:
“We found the attachment bytes and deliberately threw them away.”
That destroys information.
The intended SMS/export flow
Something much closer to this:

```
1. IMMUTABLE ORIGINAL
   1.3 GB SMS XML
          │
          │ remains untouched
          ▼

2. DUCKDB STREAMING / SANITIZATION
   inspect/read incrementally
   no giant Python object
          │
          ├───────────────┐
          ▼               ▼
   message records   attachment occurrences
                          │
                          ▼

3. ATTACHMENT RECOVERY
   ├─ embedded binary/base64
   ├─ archive members
   ├─ sibling files/folders
   ├─ export attachment arrays
   ├─ referenced local files
   └─ other source-specific forms
                          │
                          ▼

4. MATERIALIZE PRESERVED ARTIFACT
   hash
   sniff actual type
   retain original filename/metadata
   deterministic stored path
                          │
                          ▼

5. PACKAGE MANIFEST / PROVENANCE
   message occurrence
          ↕
   attachment occurrence
          ↕
   preserved source artifact
          ↕
   original export locator
                          │
                          ▼

6. NORMALIZED MESSAGING RECORD
   message text
   timestamp
   sender/participants
   edits/deletions
   native identifiers
   attachment references
   provenance
                          │
                          ▼

7. DERIVED PROCESSING
   bounded extraction
   chunking
   OCR/transcription where applicable
   embeddings
   entities/events/etc.
```

That preserves both levels:

* the immutable/original source;
* the normalized useful representation.

And it preserves the many-to-many reality that multiple source artifacts can corroborate the same normalized message, while one source message can have several attachment occurrences.
The sanitizer is allowed to make a temporary clean representation
This is where Claude seems to have confused two different concepts.
For a malformed 1.3 GB XML file, it can absolutely create a sanitized streaming representation so DuckDB `read_xml` can consume it.
But:

```
SANITIZED INPUT FOR PARSING
```

is a processing artifact.
It must not become:

```
THE ONLY REMAINING REPRESENTATION OF THE SOURCE
```

If sanitizing strips binary payloads to make the XML tractable, those payloads need to be intercepted/materialized before they're discarded, or processed in another lossless pass.
So this:

```
original XML
    ↓
strip attachment bytes
    ↓
read_xml
```

is incomplete.
It needs to be more like:

```
original XML
      │
      ├── streaming attachment recovery
      │        ↓
      │   preserved hashed artifacts
      │
      └── streaming sanitized XML
               ↓
           DuckDB ELT
               ↓
       normalized records
```

The phrase that worries me most
Claude says:
“It keeps only the message fields that one query selects.”
That's another problem.
The extraction template can certainly select a normalized projection.
But it shouldn't silently make everything it doesn't select cease to exist.
You designed this system specifically around loss-minimizing extraction + preserved originals + deterministic lineage.
Therefore:

```
SOURCE ATTRIBUTES
       ↓
normalize known fields
       +
retain unmapped/source-specific metadata
       +
reference immutable original
```

Not:

```
SELECT these 12 columns
       ↓
everything else effectively disappears
```

That latter approach is exactly how obscure export fields later turn out to contain something important—attachment state, deleted-message flags, service information, address normalization, read state, MMS parts, identifiers, etc.—and then you have to ingest the corpus all over again.
So Claude's current proposed plan is still incomplete
The pasted conversation says it had reduced the plan to:
catalog feeds file list and hashes → export files through DuckDB templates → summaries → Weaviate. Pasted text.txtTXT
That's missing a critical existing layer:

```
SOURCE/PACKAGE PRESERVATION
       +
ATTACHMENT EXTRACTION/MATERIALIZATION
       +
FULL PROVENANCE
```

before the normalized/index representation.
And the fact that Claude later discovered the SMS template was explicitly locator-only means this isn't hypothetical—it is an actual implementation gap.
I would now add this to the review as a blocking defect
Attachment/source preservation regression
Current SMS ELT sanitization is lossy. It removes embedded attachment payloads, produces locator-only attachment metadata, does not materialize recoverable image/video/audio payloads, does not create the intended source/package representation, and only projects a subset of source attributes. This conflicts with the established architecture in which immutable originals are retained, recoverable attachments are materialized and hashed as preserved source artifacts, normalized Messaging records retain deterministic lineage and attachment associations, and locators are provenance—not substitutes for available source bytes. The sanitizer may produce a temporary parseable representation, but it must not destroy the only recoverable copy of embedded content.
And importantly, this doesn't require inventing a new architecture.
It means Claude needs to stop designing around whatever script it wrote yesterday and trace the already-established package extractor / attachment materializer / provenance model, then wire the DuckDB templates into those components.
That is now at least the third instance of the same underlying failure:

1. Whole files read into memory despite the chunk/DuckDB design.
2. Chat-specific pipelines built beside the corpus-wide CocoIndex system.
3. Attachment bytes discarded despite the source-preservation/package design.

The pattern is not that your architecture lacked an answer. The existing answer keeps getting bypassed by locally convenient implementations.
