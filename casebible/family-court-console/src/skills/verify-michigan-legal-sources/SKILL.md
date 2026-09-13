---
name: fct-verify-michigan-legal-sources
description: "(family-court-toolkit) Audit Michigan family-law claims against current official primary sources with authority level, pinpoint, currency, claim-to-source fit, and conflict status. Use for statutes, court rules, SCAO forms, cases, MDHHS policy, local procedure, deadlines, or citation validation."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/verify-michigan-legal-sources` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Verify Michigan Legal Sources

> _Byline: OpenAI Codex · GPT-5.6 · 2026-08-13_
> _Ported to Claude Code plugin spec: Claude Code · Fable 5.1 · 2026-09-07_

> _Port note (Claude Code · Fable 5.1 · 2026-09-07): in Claude Code the console tools are exposed as `mcp__plugin_family-court-toolkit_family-court-console__<tool>` (e.g. `…__route_issue`). Paths under `${CLAUDE_PLUGIN_ROOT}` resolve to this plugin's install directory._

Verify meaning, not merely link availability.

## Source order

1. Current Michigan Court Rules, Michigan Rules of Evidence, SCAO forms, and Michigan Judicial Institute materials.
2. Current Michigan Legislature statutory text and enactment history.
3. Published Michigan appellate opinions.
4. Federal opinions only as persuasive authority when interpreting Michigan law.
5. Official MDHHS and county materials for agency or local procedure.
6. Secondary sources only as locators or clearly labeled commentary.

## Audit each claim

Record:

- exact claim;
- issuing body and authority class;
- official URL;
- section, rule, page, paragraph, or form revision;
- amendment/effective date and verification date;
- quoted-text hash or preserved copy when permitted;
- whether the source directly supports the claim;
- conflicts or limiting authority;
- one normalized status.

Use only these statuses: `VERIFIED_PRIMARY`, `VERIFIED_OFFICIAL_METADATA_ONLY`, `MIRROR_ONLY`, `BLOCKED`, `CONFLICTED`, `STALE`, `SUPERSEDED`, `PROVISIONAL_CURRENCY_NOT_CLEARED`, `ATTORNEY_REVIEW`.

## Guardrails

Use `audit_sources` for the reviewed registry, then browse the live official source when currency matters. Do not equate HTTP success with validation. Do not accept a source ID, issuer label, or syntactic pinpoint without checking claim-to-pin fit.

Treat CourtListener as optional discovery, not a citator. Do not use write-capable CourtListener tools. Verify located opinions against the issuing court's official copy when available.

Return **Verified claims**, **Unsupported or overstated claims**, **Currency gaps**, **Conflicts**, and **Required corrections**.
