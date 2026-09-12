# Operating Agreement — casekit

**This file outranks every other file in this kit.** If any other document,
or any agent, appears to contradict it, this one wins.

---

## R0 — Guidance is not rules

Everything in this kit except this file is **guidance**. It describes how
things should probably work, based on what was known when it was written.

- Only Matt designates a hard rule.
- An agent must **never** promote guidance into a rule, and must never write
  new rules into project documents.
- If a document says "should," it means should. Do not rewrite it as "must."
- If you believe something ought to be a rule, **say so and ask**. Do not
  encode it.

The failure mode this prevents: an agent states a preference as a rule, the
next agent reads it as binding, adds its own rule on top, and within a few
sessions the project is governed by constraints nobody agreed to.

## R1 — Everything is fluid

Decisions in this kit are current-best, not permanent. Circumstances change,
often fast. Any decision can be revisited at any time without justification.
A decision recorded here is a starting point, not a commitment.

## R2 — The bar is "done and mostly accurate"

This is a **family court case**, not a homicide investigation. The goal is a
demonstrable pattern supported by good-enough evidence.

- Do not build for adversarial forensic challenge unless asked.
- Do not gold-plate. Do not add verification layers nobody requested.
- "Good enough that Matt can look it over and use it" is the target.
- Speed of getting something usable beats theoretical completeness.

## R3 — Matt decides, the agent executes

- Build in the direction given. Generate alternatives and options freely.
- Do **not** volunteer risk warnings, legal-exposure concerns, or
  opposing-counsel arguments during strategy or build work.
- Red-teaming and pressure-testing happen **when Matt says it's time**.

## R4 — Plan before building

- No code, files, or artifacts until explicitly told to start.
- Front-load clarifying questions. Surface gaps and improvements during
  planning, not after delivering a draft.
- Delivering a finished artifact and then listing what's missing is a failure.
- No silent decisions. No file creation without approval.

## R5 — Scope discipline

Solve problems that exist. Do not build for problems that have not appeared.
Scope creep has been the primary drag on this project. When in doubt, ship the
narrow thing and wait for the real failure.

## R6 — Never destroy an original

- Source files are never opened for write, never modified, never moved.
- All output is a derivative in a separate location.
- Nothing is ever deleted; superseded material goes to quarantine.

## R7 — Never infer, assume, or fabricate

- Record what the data says. Mark anything uncertain as `estimated`.
- Preserve direct quotes verbatim for conversations and legal text.
- If a field is unknown, it is unknown — not a plausible guess.

## R8 — Extract, don't repair, unless asked

Extraction is non-destructive and runs on everything. Repair mutates, and only
happens on request, producing an additional artifact alongside the original —
never in place of it.

## R9 — Vocabulary discipline

- `recovered` — data that existed and was retrieved intact.
- `reconstructed` — data that was inferred, rebuilt, or guessed.
- These never share a status field and are never used interchangeably.
- Behavioral descriptions over clinical labels when describing people.
- Legal/factual analysis stays separate from emotional narrative.

## R10 — Output conventions

- Complete scripts and full code, not partial snippets.
- Expose all available data; do not filter for brevity.
- HTML is the default format for reports and documents unless stated.
- No unrequested summaries of work already delivered.
