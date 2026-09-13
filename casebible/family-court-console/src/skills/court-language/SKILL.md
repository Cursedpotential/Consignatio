---
name: fct-court-language
description: "(family-court-toolkit) Court-safe language reviewer/rewriter for Michigan family-court documents and testimony prep: run court_language_review to flag banned clinical labels, absolutes, mind-reading, characterizations, threats, child-as-witness, speculation, legal conclusions, recording admissions, and minor PII — then rewrite following the tool''s rewrite_plan, TEMPLATES.md, and EXAMPLES.md, and re-review until the score clears 90 with zero stop flags. Use for affidavits, motion briefs, testimony prep, messages to the other parent, incident logs, and referee-recommendation objections."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/court-language` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# court-language — court-safe language reviewer / rewriter

> _Byline: Claude Code · Fable 5.1 · 2026-09-07._ Owner framing (2026-09-07): this is "my verbiage to
> court-safe verbiage... a tool that creates, or reviews it on the fly," and — like the survival
> guide — it is primarily a **prompt with templates and examples**, though the flagging side is
> mechanical. Read this file, then `TEMPLATES.md` (one fill-in template per doc type) and
> `EXAMPLES.md` (worked before/after pairs + the safe phrasebank), before rewriting anything.

## The split: mechanical review, model-written rewrite

The MCP tool `court_language_review` (and its CLI twin `court_language.py`) run a **deterministic**
lexicon (`content/tools/court-language/lexicon.json`) over the text — every pattern is a plain regex,
every category has a fixed severity (`stop` / `fix` / `soften`), and the score is computed the same
way every time. The tool does **not** rewrite anything. It returns:

- `findings[]` — every matched pattern, its category, severity, excerpt, and a `suggested_rewrite`
  cue drawn from the lexicon entry's `rewrite_pattern`.
- `stop_flags[]` — the categories that must not survive into a filing or a message at all
  (`banned_clinical_labels`, `profanity_insults`, `threats_or_ultimatums`, `child_as_witness`,
  `recording_or_surveillance_admissions`).
- `profile_violations[]` — structural problems specific to the `doc_type` (an affidavit paragraph
  that argues instead of stating a fact, a BIFF message that recaps history, a testimony answer that
  volunteers beyond the question, etc.), drawn from `lexicon.json`'s `doc_profiles`.
- `rewrite_plan[]` — ordered, plain-language instructions for the model to follow.
- `safe_phrasebank[]` — 10-20 court-safe openers/phrases for this `doc_type`, loaded at runtime from
  `EXAMPLES.md`'s "Safe phrasebank" list under the matching heading.
- `score` (0-100) — 100 minus a weighted deduction per finding (`stop` costs the most).

**The model does the actual rewriting.** Say this plainly to the reader/user: the tool guarantees the
review is thorough and repeatable; it does not guarantee the rewrite is good writing, and it cannot
write the rewrite for you.

## The protocol, every time

1. **Review.** Call `court_language_review` with `mode: "review"` and the correct `doc_type`. Read
   every `finding`, every `profile_violation`, and the full `rewrite_plan`.
2. **Rewrite.** Using the matching `TEMPLATES.md` template and `EXAMPLES.md` worked pairs for this
   `doc_type`, rewrite the text by following the `rewrite_plan` step by step:
   - Replace every `stop`-severity finding's excerpt per its `rewrite_pattern` — these must not
     survive into the output in any form, even softened.
   - Replace every `fix`-severity finding with the specific, dated, observable-fact version.
   - Address every `soften`-severity finding if it does not cost meaning.
   - Fix every `profile_violation` (split long affidavit paragraphs, cut history from a BIFF
     message, add a record cite to a motion-brief factual predicate, etc.).
   - **Never add a fact the source text did not contain.** The rewrite changes *how* something is
     said, never *what happened*. If a sentence has no safe factual version, cut it — do not invent
     detail to replace it.
3. **Re-review.** Call `court_language_review` again with `mode: "review"` on your rewritten text.
   Repeat steps 2-3 until `score >= 90` and `stop_flags` is empty. **Never present a rewrite you have
   not re-reviewed.**
4. **Present a before/after table.** Show the original excerpt, the category/severity that flagged
   it, and the rewritten sentence, so the reader can see exactly what changed and why. This is not
   optional — a silent rewrite hides exactly the safety judgment the reader needs to see.
5. **Never soften a safety report into silence.** If `stop_flags` remain after your best rewrite
   attempt (most commonly `recording_or_surveillance_admissions` or `child_as_witness`), say so
   explicitly and route to the child-protection rule or an attorney — do not keep iterating wording
   until the flag technically stops matching while the substance survives. A regex dodge is not a
   safe rewrite; the goal is removing the substance the category exists to catch.

## Child-protection rule (absolute, carried from GUARDRAILS.md S8)

No rewrite may keep, soften, or relocate a statement that uses the child as a witness, messenger, or
source — including a statement about the child's affect or behavior that was actually derived from
something the child said. Rewrite `child_as_witness` findings by grounding the fact in your own
direct observation (what you saw, when) or a document/third party, never by paraphrasing what the
child told you into something that reads like your own knowledge.

## Doc-type quick index

| doc_type | one line | template section |
|---|---|---|
| `affidavit` | numbered facts, personal knowledge only, no argument | `TEMPLATES.md#affidavit` |
| `motion_brief` | argument allowed, every fact cited to the record | `TEMPLATES.md#motion_brief` |
| `testimony_answer` | short, responsive, no volunteering | `TEMPLATES.md#testimony_answer` |
| `message_to_other_parent` | BIFF: brief, informative, friendly, firm | `TEMPLATES.md#message_to_other_parent` |
| `incident_log` | FACT: fact, action, consequence/context, time | `TEMPLATES.md#incident_log` |
| `objection_to_recommendation` | finding + why the record doesn't support it + relief | `TEMPLATES.md#objection_to_recommendation` |

## Calling the tool

```
court_language_review({ text: "<the draft>", doc_type: "affidavit", mode: "review" })
```

Then, after rewriting, call again with the same `doc_type` and the rewritten text to confirm
`score >= 90` and `stop_flags: []` before presenting it to the user.

## Sources

`content/tools/court-language/lexicon.json` (categories, severities, doc_profiles) ·
`references/court-language/TEMPLATES.md` · `references/court-language/EXAMPLES.md` ·
`references/documentation-methods/SKILL.md` (FACT, BIFF, reframing table) ·
`content/custody-guide/GUARDRAILS.md` S2 (banned clinical labels), S8 (child-protection absolute),
S9 (recording is unsettled/criminal exposure).
