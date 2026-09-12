# Loose-archive sweep — MASTER findings (117 listed + strays, 5-agent sweep)

> _Byline: Claude Code · Fable 5 · 2026-07-03 · dir: dev-resources/Archives/_project_dirs_loose/ (Manus-era "MCP Tool Shop" ancestor, repo Cursedpotential/mcp-tool-platform, Jan 2026). Companion to drizzle-schemas-vs-live-DIFF.md + extracted-code-sweep-ADDENDUM.md._

## 🔴 SECURITY — 2 live-credential files quarantined (owner action needed)
Moved to `_stale/secrets-quarantine/` (see its README):
1. **Neo4j-660660c9-Created-2026-01-05.txt** — live Neo4j Aura password + URI. ROTATE or delete instance 660660c9 (check for case data first).
2. **Groq Compound Agent Handoff…md** — live Coolify + Hetzner + **Cloudflare GLOBAL** API keys + root SSH IPs. ROTATE ALL; Cloudflare global key is highest blast radius (controls R2/DNS for case buckets). Verify Hetzner boxes 116.203.199.238 / .198.77 aren't still billing.
Milder: `mcp_recovery_memory.json` + `pasted_content_5.txt` leak a Supabase project ref (no password) — scrub before any sharing.

## LIVE VERIFICATIONS (done 2026-07-03)
- **MCL j/k swap bug is NOT in live DB.** analysis.custody_factor: j="Willingness to facilitate the other relationship", k="Domestic violence" — correct. The swap existed only in old forensics-router.ts. No fix needed; do not copy that file's letter↔text map.
- **Pattern-gap diff vs live 153-category seed** — 11 candidate categories GENUINELY MISSING (in_seed=false): `boundary_testing, boundary_violation, cycle_honeymoon, cycle_tension, escalation, guilt_trip, intermittent_reinforcement, interruption, mirroring, premature_intimacy, pronoun_ratio`. Already present (14): triangulation, future_faking, hoovering, double_bind, word_salad, stonewalling, projection, isolation, financial_control, monitoring_stalking, child_weaponization, medical_abuse, reproductive_coercion, special_needs. → the 11 are 0006-seed-addendum candidates (esp. the cycle/escalation temporal set + pronoun_ratio statistical marker). Old seed-patterns.ts = 256 patterns/26 categories = the ~half-size baseline the live 512 already grew from.

## MASTER ADOPTION LIST (feeds migration 0008 + beyond)

### A. Migration 0008 — concrete values recovered
1. **format_resolver** ← schema_resolver.py (port from Python, has working Ollama AI path; .ts twin AI-stubbed): key = md5(sorted-lowercased fields)[:12]; row = {sourceField, targetField, confidence, method ∈ exact|fuzzy|content|ai|cached} + usedCount; thresholds exact≥2 short-circuit / fuzzy>0.3 / content 0.6-0.7; 6-field alias dictionary is a ready seed (needs expansion to live targets). Complement: output_schemas.py (loose) field-level validators; DRIVE_UTILITIES_ANALYSIS.md points to external file_analyzer.py for schema inference.
2. **conversation clustering** ← conversation-segmentation.ts: timeGap=2h, similarity=0.6, ID=PLAT_YYMM_TOPIC_iii (per-platform-month counter, topic=6-char pad), split-cause enum time_gap|topic_change|entity_change|first_message (store on cluster row). Pairwise (msg-to-prev) similarity = documented baseline weakness. PLATFORM_CODES + topic_detector.py TOPIC_MAPPING (KAILAH/VISITS/CALLS/SCHOOL/MONEY/HEALTH/SUBST/INFID/THREAT/GENRL) = topic_code seed. Embeddings = all-MiniLM-L6-v2 (384-dim) via Milvus lane (skip broken BERTopic).
3. **message.is_read** promotion + **hint_provenance** ← message-schemas.ts preliminary_* set (the loose copy correctly populates chatgpt_conversations' 6 cols incl preliminary_reasoning + analyzed_at); supabase-message-exporter.ts idempotency key (file_hash,timestamp,sender).
4. **behavior_category.is_enabled** toggle ← analysisModules.isEnabled (0003 sql); priority-screener.ts category→severity→mcl_factor table.
5. **HurtLex sync provenance** ← hurtlex-fetcher.ts hurtlexSyncStatus {status, sourceUrl, lastSyncAt, termCount, errorMessage} + pinned v1.2 + level(conservative|inclusive) + isCustom protect-on-resync; lexicon-importer.ts priority field for multi-lexicon conflict.
6. **cost/prompt-metrics views** ← smart-router.ts PROVIDER_COSTS + taskTypePreferences + litellm_config.yaml model_group_alias chains; prompt-manager.ts version-chain (parentId) + rolling successRate/avgLatencyMs/usageCount.
7. **finding SPAN columns + escalation** ← 0003 sql patternMatches (sourceLocation, isContradiction + contradictsWith self-FK, matchType enum exact|fuzzy|regex|semantic) + app.py escalation_index = (2nd-half mean severity − 1st-half)/1st-half ×100%, risk_level thresholds CRITICAL(avg≥7|max≥9)/HIGH(avg≥6|max≥7)/MODERATE(avg≥4)/LOW → severity_progression semantics.
8. **11 missing pattern categories** (above) — 0006 seed addendum, plus app.py ABUSE_PATTERNS regex corpus + SEVERITY_WEIGHTS to backfill detection_pattern; Expanded Pattern Library.md research-backed additions (cite before seeding).

### B. Held graph lane (Semantica/Neo4j wiring, when unblocked)
- **neo4j-integration.md = authoritative prior ontology** (NEO4J_GRAPH_SCHEMA_COMPLETE.md is the truncated copy). 11 nodes (Person w/ relevance-tier+subtype taxonomy, Address w/ geohash_5/6/7 tiers, GpsPoint, Property, VoterRecord, Organization, Place, Phone, Email, Event), ~25 temporal edges incl AFFAIR_WITH{start,discovered_date}, person↔person NEAR{distance_meters,timestamp} co-location, RESIDED_AT/VISITED/MESSAGED/CONTACTED. Graphiti API sketch: add_entity/relationship, get_entity_timeline, detect_contradictions, query_as_of. langchain-memory.ts hypothesis-supersession + preliminary-vs-final delta design → Graphiti temporal model.

### C. Pipeline/ingest engineering (port to evidence/tools)
- **stream-processor.ts** — best single adoption: SAX XML / depth-JSON / text streaming chunkers, 5GB+, resume-from-offset (pairs w/ working-memory.ts resumable-job model). For large SBV XML ingest.
- **real-embedding-service.ts** — batch→sequential→zero-vector(index-aligned) fallback, retry/backoff, dedup cache → Milvus writer (fix 1536→384 dim).
- **conversation_ingestion_system_design.md** — chunk→validate→repair(structure-only)→schema-fingerprint(>85% Jaccard)→transform(tz→Eastern, PII, derived)→preview(10 rec, interactive fix)→ingest, w/ ingestion_runs/chunk_status audit + SHA-256 chunk hashing.
- **6-pass classifier** (multi-pass-classifier.ts, Analysis Library Architecture.md): Pass0 priority-screen(no-LLM) → spaCy → VADER → patterns → TextBlob → sentence-transformer semantic → consensus. Cheap court-explainable heuristics: sarcasm(subj>0.7 ∧ neg ∧ pol>0.2), negation+positive-polarity→gaslighting signal. **Preliminary-vs-meta DELTA-as-evidence** concept → maps to live bitemporal knowledge_time/disclosure_tier.
- **document.ts + format_converter.py + unstructured_parser.py** — Pandoc/Tesseract/pdftotext doc→md/OCR (parse.document capability, extractors sweep).
- **text_miner.py** (≡ text_miner-1.py, dedupe) — ugrep/rg forensic search + timeline + court-report.
- **approval-system.ts** — backup+rollback mechanism + typed-preview (diff|summary|list) + operation taxonomy = the parts richer than live public.approval_request.
- **MarkdownCodeExtractor.py** (dedupe the byte-identical "Advanced" copy) — standalone code-from-chat-export utility.

### D. Custody hashing
- Python evidence_hasher.py FULLY PRESERVED: hash_records = sha256(json.dumps(records, sort_keys=True, default=str)); chain via previous_hash links + verify_chain; stage enum imported|converted|normalized|analyzed|redacted|exported. Historical per-message H2 = sha256(msg.text) (production-pipeline.ts) — plain text hash, NOT the lost bestoffort-v2 recipe. Re-crack of lost H2v1 attempted again w/ hash_records recipe (217 candidates) → STILL no match; lost-recipe verdict final, h2-canonical-v2 stands.
- evidence-hasher.ts + pattern-analyzer.ts (loose) = TRUNCATED fragments (bodies unrecoverable); full versions in behavioral-analyzer-complete.zip → vindicates require_tracked_code rule.

### E. ARCHITECTURE.md — MCP Tool Platform (cross-check vs live Agno gateway, not confirmed gaps)
Candidates the live AgentOS surface may lack: (1) preprocessing tool catalog w/ cost+permission-annotated schemas + semantic routing/getRelatedTools; (2) **ContentStore + get_ref paginated reference-returns** (output >1MB → ref envelope, agent pages only needed slices → claimed 85% token cut); (3) declarative workflow templates w/ ${prior.output} piping; (4) screenshot.*/image.* OCR-to-conversation tools (MCP_TOOL_CATALOG.md).

## DUPLICATES / JUNK / SUPERSEDED
- Byte-identical dupes to extracted-code (formatting only): production-message-schemas.ts, settings-schema.ts, pdf-imessage-parser.ts, facebook-parser.ts, pdf_extractor.py. Loose truncated-inferior: parser.py, chatgpt_parser.py. Loose-newer-worth-keeping: output_schemas.py (validators), message-schemas.ts (chatgpt preliminary_* cols).
- Superseded infra: langgraph/langchain/llamaindex/chroma/qdrant/pgvector clients, per-platform sharded schema, MySQL migrations (0001 junk; 0003 = mine columns only), vector-db/mem0/n8n/gcp-ai/sdk/oauth/search/filesystem, all *.tsx UI (keep PatternLibrary.tsx + behavioral-pattern-analyzer.html as UX/regex spec).
- pasted_content_1-6 = chat scraps; only _5 (real schema/detection IDs) + _2 (delta-as-evidence) + _3 (storage flow) worth keeping. pasted_content/ subdir = full snapshot copy, not new.
- Owner's own past GAP/AUDIT/PUNCHLIST reports: confirm the live architecture already RESOLVES the gaps they diagnosed (missing doc-intel staging tables + HITL = what normalized_record + 0008 close). Read as validation, not action items.
