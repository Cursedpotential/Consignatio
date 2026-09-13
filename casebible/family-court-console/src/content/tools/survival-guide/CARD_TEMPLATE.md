# Survival Guide — One-Page Card Template

> _Byline: Claude Code · Fable 5.1 · 2026-09-07. Modeled on `content/toolkit/cheatsheet/L0-hearing-day-card.md`._
> Used when `survival_guide` is called with `format: "card"`. Fill every section from the same
> `context_pack` used for the full guide — this is the compressed, in-the-room version.

## Required header (prepend verbatim)

```
Legal information, not legal advice. Verify every deadline and rule cite before relying on it.
If you or a child are in immediate danger, call 911. Domestic violence hotline: 1-800-799-7233.
```

## Card sections (in this order, one page)

**Event:** `context_pack.title`

**Bring:** the `context_pack.prepare` list, compressed to bullets — hearing notice, ID, exhibit
sets, chronology, three asks with a source cite for each.

**Three asks:** the reader's narrow, specific requests — leave blank lines if the model does not
have enough case_facts to fill them; never invent a request.

**Trap questions (top 3):** the three highest-severity entries from `context_pack.traps`, each with
its one-line safe move.

**Do not:** the absolute list from `context_pack.do_not`, compressed to one line each.

**Deadlines:** every entry in `context_pack.deadlines`, each computed via `calculate_planning_date`
with the matching `rule_preset`, marked `PROVISIONAL` unless independently verified this session.

**If you freeze:** pause, ask to repeat the question, look at the one-page chronology, say "I need a
moment to find the date."

**Stop conditions:** the event's `safety_gates`, compressed to one line each.
