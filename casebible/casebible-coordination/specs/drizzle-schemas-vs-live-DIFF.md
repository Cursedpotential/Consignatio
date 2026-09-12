# Drizzle/extracted schemas vs live forensic DB — full diff & adoption review

> _Byline: Claude Code · Fable 5 · 2026-07-02_
> Inputs: 7 files in `extracted-code/schemas/drizzle/` + `review_schema.ts` + `agno-alpha-schema.sql` (1,800 lines, ~50 tables)
> Baseline: live ovh3 DB (98 tables, migrations 0005/0006), full introspection 2026-07-02.

## Verdict in one line
These files are **ancestors** of the live schema (two of them literally so), the live DB is a
**superset of the messaging/forensic core** — but the app-layer files carry **8 genuinely missing
features/settings** worth adopting, listed in §3.

---

## 1. Lineage — two files are already IN the live DB

| File | Relationship to live |
|---|---|
| `production-message-schemas.ts` | The "900-line production schema" that migration 0005 reconciled. Live `analysis.message` (48 cols) ⊇ `messaging_messages` (~45), same for conversation/attachment/behaviors/evidence_items/factor_citations. |
| `agno-alpha-schema.sql` + `review_schema.ts` | Direct ancestor of live `public.agent_run` (10 cols ✓ same run_type/status sets), `public.approval_request` (12 ✓), `public.transcript_insight` (7 ✓). `learned_knowledge` → superseded by `public.memory_items` (24 cols, richer). `review_schema.ts` is just the UI mirror of these. |

## 2. Where LIVE is already equal or richer (no action — do not regress)

| Drizzle feature | Live counterpart | Note |
|---|---|---|
| `messaging_documents` custody fields (acquiredBy/verifiedBy/storagePath) | `evidence.source` (36 cols) | live adds custodian, provenance_tier, acquired-tz/certainty, hash_canon_version, 5 status lanes, verified_by/at ✓ |
| `messaging_behaviors` incl. contextBefore/After | `analysis.pattern_finding` (34) | live adds bias_caution, authored_perspective, court-safety gates, provenance_id ✓ context_before/after ✓ |
| `messaging_attachments` (ocr/transcription/faces/screenshot/exif) | `analysis.attachment` (27) | all present ✓ + embedding_ref, review lane |
| `mcl_factors` (+statutoryText) | `analysis.custody_factor` | statutory_text ✓ + is_key_factor |
| `behavior_categories` w/ mclFactors array | `behavior_category` + `behavior_category_mcl` (225 rows) | relational, weighted — richer |
| `severityWeights` (+escalationThreshold) | `analysis.score` + `score_band_config` | versioned bands + rationale + staleness — richer |
| `evidenceChains` (chainData/isVerified/verificationErrors) | `evidence.evidence_hash` H1/H2/H3 + `custody_event` + new `cb_custody_chain.py` verify tool | live scheme is stronger; verification runs should LOG to custody_event (convention, not DDL) |
| export/importHistory | `analysis.export/export_item/export_package` + `processing_run` | ✓ |
| `apiKeyUsageLogs` (latency/tokens/cost per call) | `analysis.tool_call_ledger` (runtime_ms, cost_estimate, hashes, approval status) | richer |
| documents/sections/chunks/spans | `artifact_registry` + `evidence.file_node` + `entity_mention` + Milvus lane (ADR-0027: chunks/BM25 live in Milvus, not PG) | keep the lane split |
| Per-platform message tables (`sms_messages`, `facebook_messages`, …) | unified `message` + `platform` col + `platform_attrs` jsonb | per-platform tables are the anti-pattern 0005 deliberately killed; platform-specific fields ride `platform_attrs` |
| serial int PKs, varchar(N), JSON-in-text, MySQL enum('true','false') | uuidv7, citext, jsonb, real enums | live conventions strictly better |

## 3. ADOPTION CANDIDATES — in these files, missing from live

Ranked by value to the current build. None applied — all owner-gated.

1. **`schemaResolvers` — AI-assisted field-mapping registry** (schema.ts)
   name, sourceFormat, fieldMappings, aiGenerated, confidence, sampleData, usageCount.
   Directly attacks the open parser gaps (XLSX / Snapchat-JSON / call logs): resolve an unknown
   format once, store the mapping + sample, reuse + audit forever. → propose `analysis.format_resolver`.

2. **Preliminary-analysis provenance: `preliminary_reasoning` + `analyzed_at` + model** (message-schemas.ts)
   Live `message` has 6 `*_hint` columns but records neither WHY, WHEN, nor WHO (model) set them.
   → propose `message.hint_provenance jsonb` (or hints written as low-tier pattern_finding rows).
   Cheap, big court-defensibility win for any model-assigned field.

3. **Conversation clustering settings + human-readable cluster codes** (settings-schema.ts `nlpConfig` + `topicCodes`/`platformCodes` + `conversation_cluster_id` "PLAT_YYMM_TOPIC_iii")
   Live has NO clustering config and no topic coding. The timeGapMinutes + similarityThreshold
   settings and the PLAT_YYMM_TOPIC_iii label scheme are exactly what the upcoming
   conversation_ref/clustering pass needs. → propose `public.app_setting` (key/value/jsonb,
   versioned) + `analysis.topic_code` / reuse `platform` values; add `conversation.cluster_code`.

4. **Module-level detection toggles** (schema.ts `analysisModules.isEnabled` + severityWeight override)
   Live can only toggle per-pattern (`detection_pattern.is_active`) or per-set; `behavior_category`
   has NO enable/disable. Detection v2's noise review showed exactly why category-level kill
   switches matter. → propose `behavior_category.is_enabled boolean DEFAULT true` (+ runner honors it).

5. **Lexicon sync provenance** (schema.ts `hurtlexSyncStatus`: sourceUrl, sourceCommit, lastSyncAt, termCount, status, errorMessage)
   `pattern_lexicon.source` is a bare string. If external lexicons (HurtLex itself is a good
   candidate — categorized offensive-language lexicon, en) get pulled, sync provenance belongs in
   data. → fold into `detection_pattern_set` rows per import (has source/source_artifact/version ✓)
   + one `sync_status`-style row per refresh; near-covered, convention + tiny addition.

6. **LLM provider routing + cost rollup** (schema.ts/settings-schema.ts `llmProviders`, `routingRules` w/ fallback, `llmCostTracking`, totalCostCents)
   Live tracks per-call cost_estimate in tool_call_ledger but has no provider registry, no
   task→provider routing with fallback, no cost rollup. Platform-side (Agno/env) handles routing
   today — adopt ONLY the rollup: a view over tool_call_ledger first; tables only if routing
   becomes data-driven.

7. **Prompt performance metrics** (systemPrompts: successRate, avgLatencyMs, usageCount, parentId chains)
   `public.prompt_registry` versions prompts (superseded_by ✓, sha256 ✓, safety_constraints ✓) but
   records zero usage/outcome. → view over tool_call_ledger joined on prompt_version first;
   columns later if needed.

8. **`workflowTemplates` / `agentConfigurations` as data**
   Live keeps agent/workflow config as code (AgentOS). Adopt only if runtime-editable workflows
   become a real need — otherwise config-as-code + git wins. PARKED.

## 4. Fields in these files live should KEEP refusing

- `bodyLower` (search denorm) — citext/pg_trgm + Milvus BM25 cover it.
- `dateUs`/`time12h` display denorms — formatting is a view/export concern; `raw_ts`+`tz` retained.
- `containsApology/Blame/Threat/Minimizing` booleans on message — flag-per-behavior on the message
  row can't carry provenance or review state; live's pattern_finding rows + has_behaviors/counters
  are the defensible shape. (A materialized view can expose the booleans for UI.)
- int auto-increment PKs / stringified JSON / enum('true','false') — regressions vs uuidv7/jsonb/boolean.

## 5. Proposed next step (owner call)
Draft `0008_app_layer_adoptions.sql` covering §3 items 1–4 (+5's small addition): format_resolver,
hint_provenance, app_setting + topic_code + conversation.cluster_code, behavior_category.is_enabled.
Items 6–7 start as views (no DDL risk); item 8 parked.
