# SPEC — Forensic Chat-Transcript Parser + 3-Level Hashing + Best-Format Selection
> _Byline: Claude Code (PROCESS lane) · Opus 4.8 · 2026-06-25_ · Build-agent-ready. Read AUTONOMY.md + README.md for lane ownership.

## Why (what the pilot exposed)
The 25-file AI-chats pilot ran the evidence vertical but produced **unusable forensic output**:
- The `transcripts.markdown` parser is a **whole-file fallback** → each chat became ONE blob with
  `participants:['owner']`, **User and assistant turns blended together**, no per-message structure.
- `occurred_at` was NULL even though the text contains `Created: 7/27/2025` etc. → no timeline.
- Only **one sha256 of the whole file** — no per-message hash, no signed custody chain.
- Speaker-blending is **disqualifying for real evidence** (you can never merge different people's messages).

This spec defines the correct parser + hashing so we can do real evidence later. **Pilot/knowledge data
is throwaway — it will be dumped clean before any real-evidence ingest.**

---

## 1. Best-format selection (structured beats markdown)
The same conversation often exists in multiple formats (e.g. ChatGPT `conversations.json` AND a `.md`
export). **Always prefer the structured format; fall back to markdown only when no structured source exists.**
- Group candidate files by **conversation identity** (conversation_id / title + participants + date window).
- Rank: `structured JSON/JSONL` (true turns + per-message timestamps) > `markdown w/ speaker markers` >
  `whole-file fallback`. Ingest the **best available**; record the rejected siblings in provenance (don't delete).
- This is dedup-by-best-FORMAT, layered on the existing dedup-by-best-COPY.

## 2. Tiered speaker-attributed parser (the core fix)
A new `parse.transcript` registry tool for chat exports, **multi-platform**, that emits **one record per message**:
- **Tier 1 — explicit markers (most exports).** Per-platform marker table → split into turns, label
  `role ∈ {user, assistant, system, tool}`:
  | Platform | user marker | assistant marker |
  |---|---|---|
  | ChatGPT (md export) | `**User:**` / `You said:` | `ChatGPT said:` / `**ChatGPT:**` |
  | Claude | `**Human:**` / `**Prompt:**` | `**Assistant:**` / `**Claude:**` |
  | Gemini / Perplexity / others | detect per-export; extend table | detect per-export |
  Extract per-message timestamp when present (e.g. ChatGPT `Created:`/`Updated:` headers, inline times).
- **Tier 2 — structural fallback (no markers).** Infer turns from blank-line/block boundaries, heading
  patterns, quote/indent levels, alternating-speaker heuristics.
- **Tier 3 — LLM fallback (ambiguous).** Pass the raw text to an LLM with a strict schema
  (`[{role, speaker, text, ts?}]`) to segment into turns. Cheap model; cache by file hash.
- Registry: this is the new primary `parse.transcript`; the current whole-file `transcripts.markdown`
  stays as the **last-resort fallback only**, and is **BANNED for real evidence**.

## 3. Normalized record schema (one row per message)
Each parsed turn → one `analysis.normalized_record` (NOT one per file):
- `id` UUIDv7 (already enforced: `DEFAULT uuidv7()` ✓), `artifact_id` → `evidence.evidence_hash`
- `record_type='message'`, `conversation_id`, `sequence_number` (turn order)
- `role` (user|assistant|system|tool), `speaker` (resolved identity, e.g. "Matthew Salem" / "ChatGPT")
- `content` (that message only), `occurred_at` (per-message timestamp), `disclosure_tier`
  (derive, don't hardcode 'contemporaneous'), `message_hash` (see §4), `attrs`

## 4. Hashing & custody — 3-level SHA-256 (REQUIRED) + optional Ed25519 + timestamping (dial-stack donor)
Donor (read these, port — don't reinvent):
`dev-resources/Archives/dial-stack/migrations/004_chain_of_custody.sql` +
`dev-resources/Archives/dial-stack/mcp-servers/py-mcp-server/src/tools/evidence_signing.py`.
- **Hash 1 — file/content hash:** sha256 of the raw artifact bytes (custody of the source file). [exists today]
- **Hash 2 — message hash:** sha256 of each message's canonical record `{conversation_id, sequence_number,
  role, speaker, content, occurred_at}` → so every bubble is independently verifiable/citable. [NEW]
- **Hash 3 — chain entry hash:** `entry_hash = sha256(entry incl. previous_hash)` per custody action →
  tamper-evident **hash-linked chain** (`chain_of_custody` table, `previous_hash`/`entry_hash`). [NEW]
- **The three SHA-256 hashes above + the hash-linked chain are REQUIRED** — cheap, standard, tamper-evident.
- **Ed25519 signature** over the canonical signable message (`evidence_signatures`: signature, public_key,
  signed_hash, signer_id, action) + `verify_custody_chain()` — **OPTIONAL / phase-2.** Caveat: self-signed by
  the same party that holds the data is strong *internal* integrity but legally weaker; its value depends on
  key management (where the private key lives, who controls it).
- **External trusted timestamp — RECOMMENDED** (RFC-3161 TSA or OpenTimestamps): timestamp the chain-head /
  entry hashes so they're provably anchored to a date **independent of us** — higher legal leverage than
  self-signing, and cheap. This is the preferred court-weight anchor over Ed25519.
- Optional **fuzzy hash** (ssdeep/tlsh) for near-duplicate detection across formats/platforms.
- WORM enforcement: `evidence.*` is append-only (DB trigger), agents read-only (ADR-0005/0006).

## 5. Lanes + evidence-vs-knowledge boundary
- **AI chats = CONTEXT, knowledge-only** → SORT's `casebible_ai_conversations`. They do NOT enter
  `evidence.evidence_hash` / `analysis.normalized_record`. (The parser still applies — context wants turns too.)
- **Real evidence** (messaging between people, records, etc.) → PROCESS's evidence vertical into
  `casebible_evidence`, ONLY after this parser + 3-level hashing exist. **Never blend speakers.**
- **Parser tool** lives in PIPELINE's `evidence/tools/` registry (PIPELINE owns parsers); SORT reuses it
  for context. PROCESS verifies output (per-message rows, distinct speakers, hashes present, timeline populated).

## 6. Acceptance criteria (build agent must demonstrate)
- A multi-turn ChatGPT + a Claude export each parse into **N message rows** (N>1), correct `role`/`speaker`
  per turn, **zero blended turns**, per-message `occurred_at` where the source has it.
- Same conversation present as JSON + MD → only the **JSON** is ingested; MD logged as rejected sibling.
- Each message has a `message_hash`; file has a content hash; a `chain_of_custody` entry exists with a
  valid `entry_hash`/`previous_hash` link and an Ed25519 signature that `verify_custody_chain()` validates.
- Run on ≥5 real exports across ≥2 platforms from the vault; no whole-file fallback used.

## Handoff
Kick to a build agent. PIPELINE implements the registry parser + hashing in `evidence/tools/` + `evidence/custody.py`
(donor-ported); SORT wires the parser into the context-ingest for `casebible_ai_conversations`; PROCESS verifies.
