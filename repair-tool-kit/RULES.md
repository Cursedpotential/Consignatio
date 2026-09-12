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

## R11 — Every derived value shows its work

Anything not read directly from a structured field carries a `derivation`
block explaining itself. A bare confidence label is not acceptable — `"level":
"derived"` with no reasoning tells a reader nothing they can check.

Every derivation states, in the record:

- **level** — what tier of confidence and nothing more precise than earned
- **why** — one plain sentence a non-technical reader can follow
- **derived_from** — the source element IDs with byte offsets, so any claim
  traces back to bytes in the original file
- **method** — how it was derived, in words and in machine form
- **assumptions** — anything taken as given that the file does not establish
- **not_established** — what this record specifically does NOT prove

`not_established` is the load-bearing field. It is what stops a derived value
from being read as a stronger claim than it is, and it is the field most likely
to be skipped. It gets filled in every time.

The same applies to every flag, warning and finding: a flag without a stated
reason is noise. Whatever raised it says why it raised it.

Where a gap could be closed by other evidence, the record also carries:

- **remediation** — what would corroborate this, stated concretely enough to
  search for: a time window, a hash to match, a phone number and date range, a
  filename pattern
- **status** — `open`, `resolved`, or `accepted`

`accepted` is as important as the other two. Not every gap needs filling. Once
a pattern is established well enough for the purpose at hand, remaining gaps
get marked `accepted` **with a stated reason**, and they stop appearing in the
work queue. A finding list that can never be closed is a finding list nobody
reads.

This is machine-readable in the extraction and human-readable in
`reports/DERIVATIONS.md`, which lists every derived claim in the package with
its basis in plain English.

## R10 — Output conventions

- Complete scripts and full code, not partial snippets.
- Expose all available data; do not filter for brevity.
- HTML is the default format for reports and documents unless stated.
- No unrequested summaries of work already delivered.
