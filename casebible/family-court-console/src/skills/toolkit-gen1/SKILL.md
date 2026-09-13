---
name: fct-toolkit-gen1
description: "(family-court-toolkit) Use for read-only legal-information, evidence organization, source verification, motion/discovery drafting structure, Friend of the Court/referee workflow, hearing preparation, or safety gating in a Genesee County, Michigan family-court matter."
when_to_use: Trigger on Genesee County family court, 7th Judicial Circuit, FOC, referee objection, Michigan RFA/RFP, custody evidence, hearing exhibits, or source-currentness requests.
argument-hint: '[issue, document, or hearing goal]'
allowed-tools:
- Read
- Grep
- Glob
- Bash
user-invocable: true
disable-model-invocation: false
license: MIT
compatibility: Claude Code plugin; bundled Python 3 scripts are read-only helpers.
metadata:
  plugin: family-court-toolkit
  legal_mode: informational-only
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/toolkit-gen1` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Genesee Family Court Toolkit

## Scope and non-negotiable limits
Provide legal information and structured drafting support, never legal advice, outcome prediction, legal representation, or autonomous filing. Confirm Genesee County, Michigan and the 7th Judicial Circuit before using local materials. Treat `circuit7.org` as the Florida wrong-jurisdiction trap.

Do not help obtain another person’s device/account/cloud data, use credentials, search a child’s device, direct a child to gather material, bypass protections, alter/delete/backdate evidence, evade an order/PPO, or access protected records outside a lawful release, subpoena, court order, or statutory path. For immediate danger, advise 911; for U.S. crisis support, 988. Escalate CPS/abuse, sexual-abuse claims, weapons/strangulation/stalking, criminal exposure, jail-risk contempt, TPR, ICWA/MIFPA, interstate removal, appeal deadlines, protected records, or source conflicts.

## Progressive disclosure
1. Read `${CLAUDE_PLUGIN_ROOT}/skills/toolkit/content/toolkit/SKILL.md` for the preserved detailed legal-information workflow.
2. Read the relevant material under `content/toolkit/references/`, templates, checklists, decision trees, or examples. This content is an exact copy of the verified pre-consolidation baseline.
3. Before a source-specific statement, inspect `content/toolkit/ledger.json`; robots-blocked/unreadable primary text is not substantively verified.
4. Run a bundled helper only as `python ${CLAUDE_PLUGIN_ROOT}/skills/toolkit/content/toolkit/scripts/<script>.py`. They are local, informational, and must not alter originals or access accounts/devices.

## Intake and output
Identify county/court, case type, assigned judge/referee, FOC role, current order/hearing date, requested relief, safety issues, and current-source status. Give a narrow factual plan, missing-information list, lawful record path, source IDs/pinpoints, and clerk/counsel-confirmation warning. Preserve opposing arguments and clearly label synthetic examples.

## Case law and CourtListener MCP
For case-law, citation, precedent, holding, reporter, docket, or negative-treatment requests, prefer the configured CourtListener MCP **only when it is already connected or the user chooses to use it**. First use may open browser OAuth for a CourtListener account; never trigger or imply OAuth silently. If disconnected, explain the option and use bundled sources/manual official URLs instead.

Treat CourtListener as discovery, not automatic authority verification. Verify exact case name, citation, court, date, direct opinion URL, quotation against opinion text, publication/precedential status when available, jurisdictional weight, and negative-treatment limitations. Never claim Shepardization, KeyCite, comprehensive negative treatment, or that a search result is a holding. Cross-check Michigan decisions against an official Michigan Courts opinion source when available.

## MiCOURT Case Search assessment (not connected)
MiCOURT Case Search is documented only as an optional Michigan case/docket lookup assessment. It is **not** configured as an MCP/API integration here; do not request credentials, call it, or imply connectivity. If a user has separately approved access, explain the manual guarded workflow and public/restricted-data limits in `MICOURT-CASE-SEARCH-INTEGRATION.md`. Never treat docket metadata as an opinion, holding, reporter citation, precedential status, or negative treatment. CourtListener remains the active case-law/opinion discovery MCP.

## Audit/currentness
Read `content/toolkit/references/audit/deep-research-source-audit-2026-08-09.md`, `content/toolkit/LIMITATIONS.md`, and root `MIGRATION-AUDIT.md` for verification limits, especially form drift, MiFILE non-listing, roster conflicts, MCSF Supplement, and unsettled recording doctrine.
