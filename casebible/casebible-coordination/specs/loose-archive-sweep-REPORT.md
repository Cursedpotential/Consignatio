# Loose-archive sweep — consolidated report (5 subagent sweeps + live verification)

> _Byline: Claude Code · Fable 5 · 2026-07-03 · scope: dev-resources/Archives/_project_dirs_loose/ (215 entries; owner-listed 117 + high-value strays) · companion to drizzle-schemas-vs-live-DIFF.md + extracted-code-sweep-ADDENDUM.md_

## 0. SECURITY — two live-credential files QUARANTINED to _stale/secrets-quarantine/
1. `Neo4j-660660c9-Created-2026-01-05.txt` — live Neo4j Aura password + URI. **Owner: rotate/kill Aura instance 660660c9 (check for case data first).**
2. `Groq Compound Agent Handoff - Salem Nexus Deployment.md` — plaintext **Cloudflare GLOBAL API key + Zone ID, Hetzner API key, Coolify token**, root SSH IPs (116.203.199.238/.198.77). **Owner: rotate all three (Cloudflare first — it controls R2/DNS); check if the Hetzner boxes still bill.**
Minor: `mcp_recovery_memory.json` + `pasted_content_5.txt` leak Supabase project ref/topology (no passwords) — scrub before sharing.

## 1. Live verifications performed (read-only, 2026-07-03)
- **MCL j/k swap bug did NOT propagate**: live custody_factor has j=facilitate-relationship, k=domestic-violence (correct). But `statutory_text` is EMPTY for all factors — old `mcl_factors.statutoryText` content is a fillable gap (0008 seed candidate).
- **Pattern-gap diff vs live 153 categories**: already present = triangulation, future_faking, hoovering, stonewalling, word_salad, double_bind, projection, special_needs, reproductive_coercion, medical_abuse, child_weaponization, monitoring_stalking, isolation, financial_control. **Genuinely MISSING (11)**: `guilt_trip`, `boundary_violation`, `intermittent_reinforcement`, `mirroring`/agreement-bombing, `premature_intimacy`, `boundary_testing`, `interruption` (conversation-level), `cycle_tension` + `cycle_honeymoon` (cycle-of-abuse phase markers), and two that are MECHANISMS not literal categories: `escalation` (→ 0008 finding-span severity_progression) and `pronoun_ratio` (→ statistical pass, I-talk≥0.08 / you-talk≥0.12 thresholds from research).
- **Lost H2 recipe: final verdict stands.** Ancestor recipe `sha256(json.dumps(records, sort_keys=True, default=str))` recovered from evidence_hasher.py and tested against pilot hashes (+217 more candidates) — no match. Pilot serialization remains unrecoverable; h2-canonical-v2 governs the future.

## 2. Top adoption findings by agent

### Pipeline/detection sweep (highest value)
- **Clustering constants** (conversation-segmentation.ts): timeGap **2h**, similarity **0.6**, `PLAT_YYMM_TOPIC_iii` (topic 6-char padded, per-platform-per-month 3-digit counter), split-reason enum `time_gap|topic_change|entity_change|first_message` → store on cluster rows. Platform codes: SMS/IMSG/FB/MAIL/CHAT/WA/DISC/SNAP.
- **format_resolver reference impl** = `schema_resolver.py` (Python has the working Ollama AI path): md5[:12] fieldset signature key, mapping tuples (source,target,confidence,method∈exact|fuzzy|content|ai|cached), usedCount, thresholds exact≥2/fuzzy>0.3/content over 10-record sample.
- **Escalation math** (analyzer zip app.py): `escalation_index = (2nd-half mean sev − 1st-half)/1st-half ×100%`; risk thresholds CRITICAL avg≥7|max≥9, HIGH avg≥6|max≥7, MOD avg≥4. → 0008 finding-span severity_progression semantics. Also SEVERITY_WEIGHTS per category (threats=10 … love_bombing=4) + full ABUSE_PATTERNS regex corpus to diff-backfill detection_pattern.
- **HurtLex sync provenance**: hurtlexSyncStatus{status,sourceUrl,lastSyncAt,termCount,errorMessage}, pinned v1.2 URL pattern, level conservative|inclusive, isCustom protect-on-resync, per-term matchCount telemetry; lexicon-importer's LEXICON_REGISTRY priority field for multi-lexicon precedence.
- **Priority screener table**: call_blocking/visit_blocking/custody_interference sev 9-10 mapped to MCL a/k — cross-check vs seed.
- **Multi-pass scoring heuristics** (court-explainable, cheap): sarcasm = subjectivity>0.7 ∧ neg-patterns ∧ polarity>0.2; negation+positive-polarity → gaslighting signal; severity = 5 + 0.8/neg-pattern + polarity/sarcasm bumps, cap 10; confidence = passes/6 + 0.2 agreement bonus.
- **Cust