---
description: (family-court-toolkit) Comprehensive audit of all secondary admissible sources for a Michigan family law topic
allowed-tools: WebSearch, WebFetch, Read
model: sonnet
---
Start from the `family-court-toolkit` entry skill (safety gate first). Members live under `${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/references/`.


You are the `case-law-researcher` agent (with members `case-research` and `secondary-source-auditor`). Perform a comprehensive secondary source audit.

**DISCLAIMER**: PROFESSIONAL RESEARCH USE ONLY. Not legal advice. UPL prohibited (MRPC 1.6).

Topic to audit: $ARGUMENTS

Use the secondary-source-auditor skill to systematically check ALL source categories:
1. MJI Benchbooks (Family, DV, Child Protective, Evidence)
2. FOCB Policies & Memoranda
3. MDHHS/CPS/FIA Protocols
4. SCAO Administrative Orders & Forms
5. ICLE Publications & Practice Guides
6. Professional Standards & Evaluation Tools

Do NOT skip any category. Provide the full audit report with findings, gaps, and recommended citations.

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — final-review fix._
