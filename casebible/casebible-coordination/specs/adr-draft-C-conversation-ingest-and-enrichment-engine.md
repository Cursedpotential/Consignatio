# ADR-draft-C — Conversation-Ingest & Enrichment Engine (meld + validate, Semantica-centered)
> _Byline: Claude Code · Opus 4.8 · 2026-06-27_ · Status: **PROPOSED** (SORT-drafted; PIPELINE to number → docs/adr and Accept). Supersedes the "ChatMiner-only" framing in `plans/refactored-discovering-codd.md`.

## Context
The corpus was classified by **provenance** ("came from an AI chat" → `doc_type=ai_chat`) instead of **function**, producing real misclassification (53% of 444 `ai_chat`-tagged files have non-chat extensions; a litigation guide, a draft email, and Docker code all filed under `Knowledge/ai-chats`). A deep `dev-resources` scan (2026-06-27) found mature, reusable engines for this — and surfaced **Semantica, which had been missed in earlier planning despite being a VIP component in the architect specs.** All discovered engines are **heavily iterated but UNTESTED** (ChatMiner audited at ~65% real with crash bugs + 0% entity extraction; same caution applies to the rest).

## Decision
Build the conversation-ingest / classification / tagging / entity workflow by **melding existing components — not rebuilding — with a hard validate-first gate.** Component map (canonical copies only; ignore stale forks):

| Capability | Engine (reuse) | Path |
|---|---|---|
| Multi-format parse + per-turn chunk + segmentation | **ChatMiner** | `Agno-MCP-Platform/chatminer/{parsers,segmenters,core}` |
| **Entities + relations + events/timeline + normalize + dedup + provenance** | **🔑 Semantica** | `dev-resources/Archives/dial-stack/docs/wiki/tools/semantica/{semantic_extract,normalize,deduplication,ingest}` |
| Multi-label controlled-vocab tagging | **controlled_smart_tagger** (+ controlled_taxonomy) | `dial-stack/utilities/External_Utils_Lib/ofw-assistant-main/app/utils/` |
| Custody → parse → normalize → store spine (per-message) | **evidence/** framework | `Agno-MCP-Platform/evidence/{custody,normalize,store,registry}.py` + `tools/` |
| Best-format select + md5 best-version dedup | `deduplication_spec.md` + `cb_r2_sort.py` md5 logic | case-bible plugin |

Wiring: ChatMiner (deterministic parse/segment) → **Semantica** (entities/relations/events/normalize/dedup, provenance) → **smart_tagger** (function + multi-label tags, path-aware) → sidecars (`sidecar_provenance_spec.md`) + SQLite registry + ovh2 PG. Evidence-grade conversations additionally run the evidence/ custody spine (3-level hashing, PROCESS lane). **AI chats stay knowledge-only** (`casebible_ai_conversations`), never the evidence schema.

**LLM access (was dropped — restored):** ALL classify/tag/extract/summarize LLM calls route through the **LLM gateway** (Portkey = target, currently TBD; LiteLLM `tailnet:4000` = interim) — one OpenAI-compatible base_url + **virtual keys**, no direct provider SDKs, **no provider keys in code/env** (this is the real fix for the hardcoded Groq key). Provider pool (Groq/Kimi/Qwen/Ollama-cloud/Gemini; Anthropic for hard cases; NOT OpenRouter) configured in the gateway. Vector store = bge-m3 + Milvus; graph = Graphiti-only writer. Standing up Portkey = PIPELINE infra (exec-tier `gateway` cutover).

## Validate-first gate (Phase 0 — nothing proceeds until green)
Smoke-test **each** engine on a REAL sample, assuming broken until proven:
- ChatMiner: parse every present format end-to-end; fix `core/pipeline.py` (missing), `ArtifactType.EVIDENCE_REFERENCE` (crash, `core/artifacts.py:238`), `parsers/discovery.py`, deps.
- **Semantica**: NER + relation/event + normalize + dedup + provenance run end-to-end; deps inventoried.
- smart_tagger: emits the controlled multi-label vocab; mapped to `tagging_spec.md`.

## Consequences
- **Fills the entity-extraction gap** (ChatMiner had 0%) with **Semantica = forensic CONTENT analysis** (NER/relations/patterns/conflicts/temporal over the evidence), feeding the multi-level analysis. **Owner clarification: Graphiti ≠ Semantica and they DON'T merge.** Graphiti = **AGENT MEMORY** (agents persist/recall knowledge, conversations, evidence-state; ADR-0031); Semantica = the forensic engine. Semantica output is NOT piped into Graphiti.
- Reuse over rebuild; provenance is first-class throughout (Semantica + sidecars + custody chain).
- **Lane dependency:** Semantica, evidence/, ChatMiner all live in **PIPELINE's** repo → PIPELINE co-owns their validation/fixes; SORT owns the function-classification + tag-mapping + sidecars + routing in `casebible-sorted`.
- Risk: all engines unverified → the Phase-0 gate is mandatory; pilot on conversations first, HITL-review before scaling.
- Parked: `timeline_analyzer` (owner deferred); `dev-resources/OTHER_RESOURCES_TO_SORT` (46,945 files) not yet scanned — may surface more.

## Alignment
No contradictions with the locked model (TYPE-first top level; AI chats = knowledge-only; per-message normalized_record; 3-level custody hashing — ADR-draft-A/B). This ADR selects the *engines* that implement it.
