# Survival Guide — Master Template

> _Byline: Claude Code · Fable 5.1 · 2026-09-07._
> This is a **writing template**, not a static document. The `survival_guide` MCP tool (and its CLI
> twin) do not generate the guide themselves — they return this template plus a `context_pack` (the
> event's cited rules, sequence, traps, deadlines, sources) and, optionally, `case_facts` and
> `source_excerpts`. **The calling model writes the guide** by filling every fixed section below from
> those inputs. Modeled directly on `references/referee-hearing-survival/SKILL.md` (the Vincent-style
> opening-statement + cheat-sheet guide), `content/custody-guide/draft/P1-hearing-prep-referee.md`
> (the worked hearing-prep packet), and `content/toolkit/cheatsheet/L0-hearing-day-card.md` /
`L1-pro-se-guide.md` (the one-page card and the plain-language reference index).

## How to fill this template

1. Read the `context_pack` for the requested event — it carries `what_it_is`, `who_is_in_the_room`,
   `sequence`, `prepare`, `applicable_rules` (cited, quote them, do not paraphrase an operative
   standard), `deadlines`, `traps` (≥3), `do_not`, `phrases`, `safety_gates`, and `sources`.
2. If `case_facts.configured` is true, use it to fill in the county, court, judge/referee, next
   hearing date, and controlling orders — **never** invent a fact the case file does not carry, and
   never echo a child's name (case_facts already reduces children to initials).
3. Read the matching draft module(s) named in `context_pack.sources` for the doctrinal detail behind
   each rule citation before writing more than the bare cite.
4. Run every date you compute through `calculate_planning_date` with the matching `rule_preset`
   before stating it as a deadline; never hand-compute a court date.
5. Fill every fixed section below. Do not delete a section for lack of content — write
   `Not applicable to this event.` instead, so a reader can tell omission from absence.
6. Prepend the required header (below) verbatim, and end every deadline or rule statement you did
   not personally verify against the archived MCR with `PROVISIONAL — verify before relying on it.`

## Required header (prepend verbatim, every guide)

```
Legal information, not legal advice. No attorney-client relationship is created. This guide was
assembled from a template and a context pack, not hand-drafted by a lawyer for your case — verify
every deadline and rule citation against the current Michigan Court Rules / MCL and, wherever
possible, a licensed Michigan attorney before you rely on it or file anything. If you or a child are
in immediate danger, call 911. National Domestic Violence Hotline: 1-800-799-7233.
```

If `context_pack.safety_gates` includes `route_issue first`, add: *"Before using this guide, run
`route_issue` on your situation. If it returns `STOP_AND_VERIFY`, do not proceed on this guide alone —
follow the stop-and-seek-counsel section instead."*

---

## Fixed sections (every one must appear, in this order)

### 1. What This Is
One paragraph: what kind of hearing/document this is, and the single most important fact about it
(pull from `context_pack.what_it_is` and the matching draft module's "why this module matters" framing).

### 2. Who Is In The Room / Who Reads This
From `context_pack.who_is_in_the_room`. Name every role present (referee/judge, FOC, GAL, opposing
party/counsel) and what each one decides or does not decide.

### 3. Sequence
Numbered, chronological, from `context_pack.sequence`. What happens first, what happens next, and
what document or clock each step starts.

### 4. Prepare / Bring
Checklist from `context_pack.prepare`, in L0-card style: short imperative bullets — hearing notice,
ID, exhibit sets, chronology, proof plan, three asks.

### 5. Opening Statement / Framing Options
Only for in-person events (hearings, interviews). Offer at least: a **minimal/factual** option, a
**slightly more contextual** option, an option **with a soft emotional note kept brief**, and a
**boundary-setting** option — the same four registers as the referee-hearing-survival member. Adapt
the wording to this specific event; do not copy the referee script verbatim into an unrelated event.

### 6. Question Types & Safe Answers
For each question category in `context_pack.sections` or a category you can reasonably infer from
`what_it_is` (employment/income, parenting time, the disputed issue itself, emotional-state
questions, alienation/gatekeeping questions), give **minimal**, **clarifying**, **contextual**, and
**boundary** answer patterns, in the register of `references/referee-hearing-survival/SKILL.md`
§2. Never write an answer that asks the reader to characterize the other parent or diagnose anyone.

### 7. Trap Questions & Safe Moves
One row per trap in `context_pack.traps` (≥3): the trap question or situation, then the safe move.
Do not invent a trap not grounded in the context pack or the draft module.

### 8. Do Not List
Verbatim or adapted from `context_pack.do_not`, plus the standing rules that apply to every event:
never characterize the other parent with a clinical label (`GUARDRAILS.md` §2, banned: narcissist,
alienator, PAS, coercive control as a pleaded label); never use the child as a witness, messenger, or
source (`GUARDRAILS.md` §8, absolute); never assert a recording is lawful (unsettled law, criminal
exposure).

### 9. Court-Safe Phrases
Openers and closers from `context_pack.phrases`, in BIFF/FACT register
(`references/documentation-methods/SKILL.md`). Short, neutral, factual.

### 10. Deadlines
Table: label, computed date (via `calculate_planning_date` + the matching `rule_preset`), cite,
status. Every row carries `PROVISIONAL — verify before relying on it` unless the calling model has
independently confirmed the rule text this session.

| Label | Date | Rule / Cite | Status |
|---|---|---|---|

### 11. Exit Checklist
From `context_pack.exit_checklist` — what must be true, or written down, before the reader leaves
the building or ends the call/session.

### 12. Stop and Seek Counsel
Restate `context_pack.safety_gates` as plain stop conditions (danger, PPO/DV/CPS, UCCJEA/interstate,
recording, appeal-of-right posture, custody/domicile change, child asked to speak to anyone).

### 13. Sources
List every `context_pack.sources` entry as `file — section`. Never cite a source the context pack or
the draft modules do not carry; mark anything else `[VERIFY]`.

---

## Card mode (`format: "card"`)

For a one-page hearing-day card instead of a full guide, use `content/tools/survival-guide/CARD_TEMPLATE.md`
instead of this file. It reuses the same context pack but keeps only: bring list, three short
objections/asks, the deadline table, and the safety header — modeled on
`content/toolkit/cheatsheet/L0-hearing-day-card.md`.
