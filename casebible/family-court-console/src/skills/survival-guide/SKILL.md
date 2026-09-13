---
name: fct-survival-guide
description: "(family-court-toolkit) In-the-room survival guide generator for any Michigan family-court hearing, interview, or filing (referee hearing, de novo hearing, motion hearing, evidentiary hearing, show-cause/contempt, PPO hearing, FOC interview, GAL/LGAL interview, custody evaluation, mediation, and 7 document types). Call survival_guide to get a context pack + writing template; the calling model writes the guide, enriched with case_facts and the matching draft module. Use the day before or the morning of a hearing, or before drafting a motion/objection/affidavit."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/survival-guide` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# survival-guide — hearing/document survival guide generator

> _Byline: Claude Code · Fable 5.1 · 2026-09-07._ Owner framing (2026-09-07, corrected 09:51): the
> survival guide is **LLM-based, not a static document store** — this tool "just creates a prompt and
> a template," modeled on `references/referee-hearing-survival/SKILL.md` (the Vincent-style
> opening-statement + cheat-sheet guide), `content/custody-guide/draft/P1-hearing-prep-referee.md`
> (the worked hearing-prep packet), and `content/toolkit/cheatsheet/L0-hearing-day-card.md` /
> `L1-pro-se-guide.md` (the one-page card and the reference index). **The MCP tool does not author a
> guide. It resolves the inputs; the calling model writes the guide.**

## When to use this member

- The user has a referee hearing, de novo hearing, motion hearing, evidentiary hearing, show-cause
  hearing, PPO hearing, FOC interview, GAL/LGAL interview, custody evaluation session, or mediation
  coming up and wants to prepare.
- The user is about to draft a motion, response, objection to a referee recommendation, affidavit,
  proposed order, proof of service, or an emergency ex parte motion and wants the assembly-and-traps
  brief before drafting.

## How to call the tool

```
survival_guide({ event: "referee-hearing", format: "full", include_case_facts: true })
```

- `event` — one of the 17 ids under `content/tools/survival-guide/events/*.json`. Call
  `survival_guide({ event: "referee-hearing", format: "json" })` or run
  `scripts/survival_guide.py list` first if unsure which id applies; do not guess an id.
- `format` — `"full"` (complete guide via the master template), `"card"` (one-page hearing-day card
  via the card template), or `"json"` (context pack + case facts only, no template — use this to
  inspect the raw inputs).
- `include_case_facts` — pass `true` whenever a real case file exists (`case_facts` tool /
  `CUSTODY_CASE_FILE`); the returned `case_facts` never carries a child's name, only initials.

## What the tool returns, and what the model does with it

The tool's result carries: `release_warning` (prepend it verbatim), `template` (the master template
or the card template, unless `format: "json"`), `context_pack` (the event's cited rules, sequence,
prepare list, ≥3 traps, deadlines with `rule_preset` values, do-not list, phrases, safety gates, and
source file paths), `case_facts` (if requested and configured), and `source_excerpts` (the first ~40
lines of each cited source file, so the model can go read the rest before writing more than a bare
citation).

**The model then writes the guide** by following `content/tools/survival-guide/TEMPLATE.md` (or
`CARD_TEMPLATE.md` for card mode) section by section, using:

1. The `context_pack` for the event's own cited rules, sequence, traps, and deadlines.
2. `case_facts` (when present) to fill county, court, judge/referee, next hearing date, and
   controlling orders — never inventing a fact the case file does not carry, and never a child's name.
3. The draft module(s) named in `context_pack.sources` for the doctrinal detail behind a bare cite —
   read the module, do not paraphrase an operative legal standard from memory.
4. `calculate_planning_date` with the matching `rule_preset` for every date the guide states —
   never hand-compute a court date.

## PROVISIONAL, always

Every guide the model produces from this tool is **PROVISIONAL** until the deadline and rule lines
are independently checked against the archived MCR
(`content/custody-guide/sources/primary/michigan-court-rules_2026-07-31.md`) or MCL, and — for any
Genesee-specific fact — against the clerk or FOC (`GUARDRAILS.md` S4, four-tier disposition:
VERIFIED / PROVISIONAL / CONFLICTED / UNVERIFIED). A generated guide is legal information assembled
from a template and a context pack; it is never legal advice and is never "filing-ready."

## Safety gate

Before generating any guide, run `route_issue` on the user's situation (`context_pack.safety_gates`
always lists this first). If it returns `STOP_AND_VERIFY` or `UNCLASSIFIED_REVIEW_RECOMMENDED`, say so
and route to safety resources or counsel instead of generating a guide as if the situation were routine.

## CLI twin (outside the MCP context)

```
python "${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/scripts/survival_guide.py" list
python "${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/scripts/survival_guide.py" referee-hearing --card --out card.md
```

The CLI reads the same JSON knowledge base and fills the template directly (no LLM step) — use it for
a quick static reference; prefer the MCP tool + model-authored guide for anything the reader will
actually rely on, since the CLI's fill is mechanical and does not incorporate `case_facts` reasoning
or the draft modules' doctrinal detail beyond what the context pack already states.

## Sources

`content/tools/survival-guide/TEMPLATE.md`, `CARD_TEMPLATE.md`, `events/*.json` ·
`references/referee-hearing-survival/SKILL.md` · `content/custody-guide/draft/P1-hearing-prep-referee.md` ·
`content/toolkit/cheatsheet/L0-hearing-day-card.md`, `L1-pro-se-guide.md` ·
`content/custody-guide/GUARDRAILS.md` S4 (four-tier disposition), S8 (child-protection absolute).
