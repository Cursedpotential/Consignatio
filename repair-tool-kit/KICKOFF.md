# Session kickoff — paste this first

Copy everything between the lines into a fresh Claude Code session at the repo
root, before any phase prompt.

---

```
You're picking up a project that has already been planned. The planning is done
and it was done carefully — do not redo it, and do not start by proposing a
different architecture.

WHO I AM
I'm Matt. Pro se father in Genesee County, Michigan family court. I'm not a
coder, but I architect systems and direct agents at that level — talk to me
like an architect, not like a junior. I think out loud and often via
voice-to-text, so parse intent and run with it rather than asking me to
restructure the question.

WHAT WE'RE BUILDING
casekit. A local Windows CLI that takes an evidence file, works out what it is,
picks the right tool to read it, extracts everything the file contains, and
seals the original plus the extraction into a verifiable package. Originals are
never modified. Repair is optional and additive.

It exists because evidence formats lie quietly. A PDF transcript in my corpus
silently replaced every emoji with one repeated symbol, dropped every
attachment, and four of the seven most common PDF readers report that symbol as
an ordinary letter. That was found by testing, not by reading docs.

HOW WE WORK — these matter more than the technical spec
1. RULES.md outranks every other file, including anything you write. Read it
   first, fully.
2. Guidance is not rules. Everything except RULES.md is guidance. Never promote
   a "should" into a "must". Never write new rules into project files. If you
   think something ought to be binding, say so and ask me.
3. Plan before building. No code, no files, no artifacts until I say start.
   Front-load questions. Surface gaps and improvements during planning, not
   after you've written the thing. Delivering a finished draft and then listing
   what's missing is a failure.
4. No silent decisions. No file creation without approval.
5. The bar is "done and mostly accurate." This is family court, not a homicide
   investigation. Don't gold-plate. Don't add verification layers I didn't ask
   for. Scope creep has been the single biggest drag on this project.
6. Don't volunteer risk warnings, legal exposure, or what opposing counsel
   might argue. We red-team when I say it's time.
7. Originals are never opened for write. Nothing is ever deleted.
8. Never infer, assume, or fabricate. Unknown is unknown. Mark uncertainty
   "estimated".
9. Complete scripts, not fragments. Expose all the data, don't filter it for
   brevity.

READ IN THIS ORDER — do this before doing anything else
  RULES.md          the operating agreement, outranks everything
  FINDINGS.md       what my actual evidence files contain, with repro commands
  STACK.md          what to build it with, and what was rejected and why
  GOTCHAS.md        ranked failure modes — most were hit during planning
  SPLIT.md          the engine contract
  PHASES.md         build sequence with hard exit criteria
  CLAUDE.md         operating rules for this codebase
  DIAGRAMS.html     all of the above, visually
  INTEGRATION.md    deferred — Temporal, n8n, promotion, hashing. Don't act on it.

ALREADY DECIDED — don't relitigate these
  Go orchestrator, single static binary, Windows + Linux
  Engines are SUBPROCESSES speaking JSON on stdin/stdout — any language
  Extract always; repair only on request, and additively
  Sealed package is the unit: original + extraction + blobs + hashes
  Profile -> route -> ONE engine -> cheap check -> escalate only on failure
  No default engine anywhere. Routing is a hand-edited config file.
  DuckDB for XML/JSON, with a mandatory pre-pass in both cases
  Install root D:\case_apps
  poppler / pypdf / pdfium are correct on glyphs. mutool is NOT — it maps
    ZapfDingbats 0x6E to "I", which corresponds to nothing and is unrecoverable.

WHAT TO DO NOW
Read the files above. Then tell me:
  - anything in the plan you think is wrong, and why
  - anything you need from me that isn't in the kit
  - your understanding of what Phase 0 requires

Then STOP and wait. I'll paste the Phase 0 prompt when I'm ready.

Do not write any code in this first turn.
```

---

## After Phase 0

Paste one phase prompt at a time from `PROMPTS.md`. Each ends with a
verification command and a stop. Don't run ahead.

## The move that isn't in the phase list

Once Phase 3 works — profile plus routing plus the confidence check — point
`casekit diagnose` at:

```
V:\sorted\_raw\Case Bible\Evidence\Phone Records\Messages with Katrina
```

It writes nothing. It tells you what formats, exporters and versions are
actually in there, and which conversations exist in more than one form. That
inventory will probably reorder the remaining phases, and no amount of further
planning could produce it.

## If a session goes sideways

Three failure modes to watch for, all of them things that have happened before:

- **Skipping ahead.** Phase 0 looks trivial. It's the phase that catches
  environment problems before they're buried under feature code.
- **Rule accretion.** A document comes back with new "must" language nobody
  agreed to. RULES.md R0 exists for exactly this.
- **Declaring done without validating.** Every phase has a verification
  command. Make it actually run.
