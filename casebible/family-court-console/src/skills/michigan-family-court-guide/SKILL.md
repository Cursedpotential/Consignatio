---
name: fct-michigan-family-court-guide
description: "(family-court-toolkit) Route and explain Michigan family-court and custody procedure using current primary authority, explicit uncertainty, and safety gates. Use for Michigan custody, parenting time, FOC, PPO, CPS, UCCJEA, evidence, hearing, order, or appeal questions."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/michigan-family-court-guide` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Michigan Family Court Guide

> _Byline: OpenAI Codex · GPT-5.6 · 2026-08-13_
> _Ported to Claude Code plugin spec: Claude Code · Fable 5.1 · 2026-09-07_

> _Port note (Claude Code · Fable 5.1 · 2026-09-07): in Claude Code the console tools are exposed as `mcp__plugin_family-court-toolkit_family-court-console__<tool>` (e.g. `…__route_issue`). Paths under `${CLAUDE_PLUGIN_ROOT}` resolve to this plugin's install directory._

Treat the bundled guide as a **publication-blocked research draft**, never as filing-ready legal advice.

## Start safely

1. Use `route_issue` before substantive analysis.
2. Stop ordinary guidance when the route flags immediate danger, DV/PPO/CPS, interstate jurisdiction, an appeal deadline, recording, or criminal exposure.
3. For immediate danger, direct the user to 911 or local emergency services. Do not imply the plugin monitors emergencies.
4. Never ask a child to collect evidence. Avoid a child's full name, birth date, address, school, or medical identifiers.

## Explain the issue

1. Identify jurisdiction, county, case stage, controlling order, requested relief, entry date, service date, hearing date, and known deadlines.
2. Separate user facts, assumptions, legal rules, local practice, and unresolved questions.
3. Use `audit_sources` and current official primary authority for every material proposition.
4. Label each proposition `VERIFIED_PRIMARY`, `PROVISIONAL_CURRENCY_NOT_CLEARED`, `CONFLICTED`, or `ATTORNEY_REVIEW`.
5. Explain what the source directly supports. A live URL is not substantive verification.

## Hard release gates

Do not rely on missing draft Modules 3, 17, or 28. Do not calculate a filing deadline from generic arithmetic alone. A timely qualifying postjudgment motion can affect appeal timing under MCR 7.204(A)(1)(d); escalate any appeal question immediately.

Use `${CLAUDE_PLUGIN_ROOT}/content/toolkit` and `${CLAUDE_PLUGIN_ROOT}/content/custody-guide` only as research leads. Re-check claims against current official sources before presenting them.

End with a short **What is verified / What is uncertain / What to do next** block.
