# ADR-DRAFT-B: Multi-level custody hashing + signed/timestamped chain of custody
- Status: **Proposed** (drafted by PROCESS for PIPELINE to number [next free, e.g. 0033] + Accept)
- Date: 2026-06-25
- _Byline: Claude Code (PROCESS lane) · Opus 4.8 · 2026-06-25_
- Extends: ADR-0017 (evidence mesh), 0018 (bitemporal); supersedes the current single-file-hash custody in `evidence/custody.py`
- Implements: `casebible-coordination/specs/chat-parser-and-custody-hashing-spec.md`
- Donor: `dev-resources/Archives/dial-stack/{migrations/004_chain_of_custody.sql, mcp-servers/py-mcp-server/src/tools/evidence_signing.py}`

## Context
Current custody computes **one sha256 of the whole file** — enough to detect file change, but not to cite
or verify an individual message, and not tamper-evident against someone who can recompute hashes. A forensic
chain of custody needs multiple hash levels + an unforgeable, time-anchored attestation. The dial-stack donor
already implements the pattern (Ed25519 signatures, hash-linked `chain_of_custody`).

## Decision
**Three SHA-256 levels (REQUIRED):**
1. **File/content hash** — sha256 of the raw artifact bytes.
2. **Per-message hash** — sha256 of each message's canonical record (`conversation_id, sequence_number, role,
   speaker, content, occurred_at`) → every bubble independently verifiable/citable.
3. **Chain entry hash** — `entry_hash = sha256(entry incl. previous_hash)` per custody action → tamper-evident
   **hash-linked chain** (`chain_of_custody` table).

**Attestation:**
- **Ed25519 signature** over the canonical signable record + `verify_custody_chain()` — **OPTIONAL / phase-2**
  (caveat: self-signed by the data-holder is strong internal integrity but legally weaker; depends on key mgmt).
- **External trusted timestamp (RFC-3161 TSA / OpenTimestamps) — RECOMMENDED** as the court-weight anchor:
  proves the chain-head hashes existed by a date **independent of us**, preferred over self-signing.
- Optional **fuzzy hash** (ssdeep/tlsh) for near-duplicate detection across formats/platforms.
- WORM: `evidence.*` append-only (DB trigger); agents read-only (ADR-0005/0006).

## Consequences
- Each evidence artifact AND each message is independently verifiable; the custody log is tamper-evident and
  externally time-anchored — court-defensible without depending on a self-held private key.
- PIPELINE ports the donor into `evidence/custody.py`; this hardening **gates real-evidence ingest** (no real
  evidence until it exists). PROCESS verifies (`verify_custody_chain()` passes, all three hashes present).

## Alternatives considered
- Single whole-file hash only — rejected: can't cite a message, not tamper-evident against re-hashing.
- Ed25519 as the primary legal anchor — deprioritized: self-signing is legally weaker than external timestamping.
- No timestamping — rejected: loses the strongest, cheapest court-weight mechanism.
