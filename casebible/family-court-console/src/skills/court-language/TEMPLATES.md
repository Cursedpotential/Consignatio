---
name: court-language-templates
description: One fill-in template per doc_type for the court-safe language rewrite protocol. Read after SKILL.md; use with EXAMPLES.md's worked pairs and content/tools/court-language/lexicon.json's doc_profiles.
---

> _Byline: Claude Code · Fable 5.1 · 2026-09-07._ Each template has fixed sections matching its
> `doc_profiles` entry in `lexicon.json`. Fill every bracket from the reviewed source text and the
> `rewrite_plan` the `court_language_review` tool returns; never add a fact the source text did not
> contain.

## affidavit

```
[N]. On [date], I [specific, personally-observed fact]. [If a document is referenced: A true and
     accurate copy is attached as Exhibit [X].]
[N+1]. [Next fact, one per paragraph, chronological.]
```
Register: first person, numbered paragraphs, personal knowledge only, no argument, no
characterization. Keep each paragraph to roughly one to three sentences.

## motion_brief

```
[Legal standard, cited: MCR/MCL/case law.]

The record establishes that [specific fact], as shown in [Exhibit X / transcript page Y].
[Repeat one fact-plus-citation pair per material fact.]

Applying [the standard] to these facts, [the requested relief] is warranted because [reasoning tied
to the cited facts, not to the other party's character].
```
Register: argument allowed; every factual predicate cited to the record; no clinical labels or
characterizations standing in for legal analysis.

## testimony_answer

```
Q: [the question actually asked]
A: [one to two sentences that answer only that question]
```
Register: short, responsive, no volunteering. If unsure, ask for clarification instead of guessing
or explaining. Stop after the direct answer.

## message_to_other_parent

```
[Brief factual statement of the topic.] [Your position or response, stated once.] [Optional: one
specific next step or deadline.]
```
Register: BIFF — brief (2-5 sentences), informative (facts only), friendly (neutral tone, no
sarcasm), firm (states the position once and ends). No history, no accusations, no threats.

## incident_log

```
F (Facts): On [date] at [time], [observable behavior only, no interpretation].
A (Action): I [what you did in response].
C (Context/Consequence): This is the [Nth] occurrence of [pattern] in [timeframe] (prior: [dates]),
   OR the effect this had on [you/the child, observably].
T (Time): [date], [time], [location].
```
Register: FACT method (`references/documentation-methods/SKILL.md`). Observable behavior only; no
clinical labels; never present what the child said as your own personal knowledge.

## objection_to_recommendation

```
Finding [N]: [the referee's finding, quoted or closely paraphrased].
Why the record does not support it: [cite the specific transcript page or exhibit; state the
specific gap or conflict].
Requested correction: [narrow, specific relief - not "reverse the whole recommendation"].
```
Register: one row per finding objected to. Never a blanket objection to "the entire recommendation"
(MCR 3.215(E)(4) requires specificity); never argument about the other party's character.
