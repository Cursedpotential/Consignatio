# ADR-DRAFT-A: Evidence-vs-Context boundary + forensic transcript data model
- Status: **Proposed** (drafted by PROCESS for PIPELINE to number [next free, e.g. 0032] + Accept)
- Date: 2026-06-25
- _Byline: Claude Code (PROCESS lane) · Opus 4.8 · 2026-06-25_
- Extends: ADR-0017 (evidence polyglot mesh), 0018 (bitemporal), 0020 (multi-domain knowledge)
- Implements: `casebible-coordination/specs/chat-parser-and-custody-hashing-spec.md`

## Context
The 25-file AI-chats pilot ran the evidence vertical and exposed two governance failures: (1) AI chats
were written into the **evidence schema** (`evidence.evidence_hash` / `analysis.normalized_record`), and
(2) the `transcripts.markdown` whole-file fallback **blended User + assistant turns into one blob** with
`participants:['owner']`, no per-message structure, and `occurred_at` NULL. Both are disqualifying for a
forensic system — you cannot blend different people's messages and call it normalized evidence.

## Decision
1. **Evidence-vs-context data boundary (hard).** AI chats / research / notes are **Context Corpus →
   knowledge-only** (Milvus `casebible_ai_conversations`, owned by SORT). They **never** enter the evidence
   schema. The custody/evidence vertical (`evidence.evidence_hash`, `analysis.normalized_record`,
   `casebible_evidence`) is reserved for **primary evidence** (messaging between parties, records, media).
2. **Forensic transcript data model.** Chat/transcript ingestion emits **one `normalized_record` per
   message** — `role` (user|assistant|system|tool), resolved `speaker`, per-message `content`,
   `occurred_at`, `sequence_number`. **Never blend speakers; never a whole-file blob for evidence.**
3. **Best-format selection.** When a conversation exists in multiple formats, ingest the **structured**
   source (JSON/JSONL with real turns + timestamps) over markdown over whole-file; log rejected siblings.
4. **Tiered parser.** Explicit speaker markers (per-platform) → structural heuristics → LLM segmentation
   fallback. The whole-file `transcripts.markdown` parser is the **last resort only and BANNED for evidence.**

## Consequences
- Evidence stays defensible (per-message attribution, citable turns); context stays in the knowledge layer.
- The parser is shared infra: PIPELINE builds it in `evidence/tools/`; SORT reuses it for context ingest.
- Pilot data (AI chats currently in the evidence schema + `casebible_evidence`) is **throwaway** — dumped
  clean before any real-evidence ingest.

## Alternatives considered
- Whole-file blob "normalized" — rejected: blends speakers, no timeline, unusable as evidence.
- AI chats in the evidence schema — rejected: they're context, not primary evidence (data-boundary violation).
- Markdown over JSON when both exist — rejected: lossy; structured always wins.
