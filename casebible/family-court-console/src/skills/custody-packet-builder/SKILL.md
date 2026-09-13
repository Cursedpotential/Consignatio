---
name: fct-custody-packet-builder
description: "(family-court-toolkit) Organize a Michigan custody or parenting-time packet without claiming court acceptance or legal sufficiency. Use for hearing binders, exhibit indexes, fact chronologies, order collections, evidence packets, redaction checks, and guarded drafting plans."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/custody-packet-builder` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Custody Packet Builder

> _Byline: OpenAI Codex · GPT-5.6 · 2026-08-13_
> _Ported to Claude Code plugin spec: Claude Code · Fable 5.1 · 2026-09-07_

> _Port note (Claude Code · Fable 5.1 · 2026-09-07): in Claude Code the console tools are exposed as `mcp__plugin_family-court-toolkit_family-court-console__<tool>` (e.g. `…__route_issue`). Paths under `${CLAUDE_PLUGIN_ROOT}` resolve to this plugin's install directory._

Build an **organization packet**, not a filing-ready product.

## Workflow

1. Run `route_issue`. Stop for safety, UCCJEA, appeal, recording, CPS/police, PPO, or criminal-overlap flags.
2. Use `get_packet_plan` with the case stage and exact goal.
3. Collect the signed, file-stamped controlling orders and notices.
4. Use `build_chronology` to separate event date, knowledge date, source, and neutral description.
5. Use `get_checklist` for evidence and hearing preparation.
6. Preserve originals. Work from copies. Record provenance and acquisition dates.
7. Minimize protected information and child identifiers. Redact only working copies.
8. Use `audit_sources` before adding any law, form, deadline, or procedural statement.

## Output structure

Return these sections:

- **Safety and jurisdiction gates**
- **Controlling orders and notices**
- **Date ledger**
- **Neutral fact chronology**
- **Exhibit index and provenance gaps**
- **Authority and form verification**
- **Privacy/redaction review**
- **Attorney-review items**

Never invent a fact, date, quotation, exhibit, docket entry, local practice, or citation. Never say “complete,” “court-ready,” or “file now” without current primary-source verification and qualified review.

Use `${CLAUDE_PLUGIN_ROOT}/content/custody-guide` only as a research lead. The copied source archive contains known legal and integrity defects documented in the remediation report.
