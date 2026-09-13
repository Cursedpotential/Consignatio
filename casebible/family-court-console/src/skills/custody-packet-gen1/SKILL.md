---
name: fct-custody-packet-gen1
description: "(family-court-toolkit) Use to build a real, tailored Genesee County parenting-time/custody filing set from assembled case facts — motion for specific parenting time, proposed order, concurrence certificate, notice of hearing, service pack, and hearing prep — driven by an explicit reason-and-act loop under the project's verified-source and translation discipline."
when_to_use: Trigger on build my packet, draft the motion, I'm ready to file, custody packet, replace 'as the parties agree', make-up parenting time, or what is still needed before filing.
argument-hint: '[filing goal, or ''intake'' to see what is still needed]'
allowed-tools:
- Read
- Grep
- Glob
- Bash
- Write
- Edit
user-invocable: true
disable-model-invocation: false
license: MIT
compatibility: Claude Code plugin; bundled resources are read-only reference copies. Real case facts are written only to the user's own filing workspace.
metadata:
  plugin: family-court-toolkit
  legal_mode: informational-only
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/custody-packet-gen1` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Custody Packet — assembled facts to filing set

Companion to the `toolkit` skill, which supplies general Genesee procedure, evidence, and
verification workflow. **This skill executes one specific filing event** for a parent whose
parenting time is stated in open-ended terms ("as the parties agree").

Run it as an explicit **reason-and-act loop**, not a script read top to bottom. Each turn is one
cycle — **Thought → Action → Observation** — and you take exactly **one** Action per cycle. The
reasoning is not ceremony: a packet fails when a model races ahead, invents a case fact it was
never given, or drafts past a stop-condition. Naming what you know, what is missing, and what
single next step is safe — *before* every action — is the mechanism that prevents all three.

## Invariants — re-check these in every Thought, not once

- **Legal information and drafting structure only.** Never advice, outcome prediction,
  representation, or autonomous filing. Nothing you produce is filing-ready; every document states
  the posture it assumes and carries its "do not use if" list. For immediate danger, 911; U.S.
  crisis support, 988.
- **A missing case fact is an intake item, never an assumption.** If you do not have it, you ask
  for it — you do not guess it, average it, or infer it from another fact. A guessed case number or
  invented order date is a defect, not a convenience.
- **The child is never a source, courier, subject of tasking, or recording target.** Not a
  balancing test.
- **Real case facts are written only to the user's own `filing-workspace/`** — never into the
  bundled `draft/`, and never anywhere inside this plugin's directory.
- **Route out and stop the loop** the moment the facts show any of: immediate danger, a recording
  question, CPS or police contact, a PPO where the user is the respondent, UCCJEA or interstate
  facts, criminal exposure, ICWA/MIFPA indicators, or an appellate deadline. Name the boundary,
  point to a free resource, and halt — do not draft around it.

## The action menu — every cycle picks exactly one

| Action | What it does | Observation records |
|---|---|---|
| **READ** ‹source› | Load one bundled reference (Phase 0 order below) | what it now binds you to |
| **INTAKE** ‹item› | Log one supplied fact, or add a missing one to the gate list | known-vs-missing, updated |
| **DRAFT** ‹component› | Produce one packet component into `filing-workspace/` | what it assumed; open PROVISIONALs |
| **SWEEP** ‹check› | Run one pre-hand-back verification | pass/fail + what you fixed |
| **ROUTE-OUT** ‹trigger› | Refer outward on a stop condition and halt | which invariant fired |

The phases below are the order the loop moves through — Orient, then the intake gate, then
drafting, then verification. You do not leave a phase until its Thought says its exit condition is
met.

## Phase 0 — Orient (READ, in this order)

Load the binding rules before any intake or drafting. One READ per cycle; the Observation is what
that document now commits you to.

1. `${CLAUDE_PLUGIN_ROOT}/skills/custody-packet/content/custody-guide/GUARDRAILS.md` — binding.
   §3 who decides what, §4 the four dispositions, §8 the child, §9 escalation, §11 standing
   instructions, §11a case-facts hygiene.
2. `.../content/custody-guide/verification_ledger.md` — the only citation source besides the
   primary archive. §4.3 carries the specific-terms case line and **two** renumbering traps. If a
   proposition is not in the ledger or the archive, it is not cited.
3. `.../content/custody-guide/CHEAT-SHEET.md` — the campaign map, clocks, translation table.
4. `.../content/custody-guide/DRAFTING-HANDOFF.md` — posture and packet sequence.
5. `.../content/custody-guide/draft/` — the models. **Everything there is generic or FICTIONAL
   (*Merrow v Vantel*). Real-case documents never go there.**
6. `.../content/custody-guide/draft/P1-translation-card.md` — the raw-to-court-safe thesaurus; the
   one file allowed to quote banned vocabulary, in its left-hand columns only.

## Phase 1 — Intake gate (INTAKE)

Thought each cycle: compare what is known against the required set below; the next Action logs the
next supplied fact or names the next gap. **While anything is still missing, the Action is to list
every missing item once, plainly, then stop the loop** — hand the list back and tailor nothing.
Never guess a case fact to keep moving; the gate exists precisely because a fabricated fact is
worse than a pause.

Required before any tailoring:
- case number, court, assigned judge/referee
- the order's **exact** parenting-time words and entry date
- the communication provision's exact words, and whether a mail-only narrowing came from the order
  or from counsel's letter (date + signer of each)
- child's age (never name or birthdate)
- the **overnights number** stated in the support order
- the dated request/denial record
- the other parent's **FOC address of record** and counsel's mailing address
- the user's conduct-audit answers (documentation protocol; "your own conduct audit")
- the proposed schedule ask, sized per the recharacterization trap in Phase 2

## Phase 2 — Draft (DRAFT, one component per cycle, in dependency order)

Each cycle's Thought confirms the component's inputs exist and no invariant is at risk; then one
DRAFT. The order is dependency-forced — you cannot draft the motion before you hold the order's
exact words.

1. **Motion for specific parenting time.** Lead on MCL 722.27a(8) — specific terms "if requested by
   either party at any time" — with *Pickering v Pickering*, 268 Mich App 1 (2005) (vague terms do
   not satisfy the statute once specificity is requested; refusal is legal error). Plead the
   *Shade*/*Kaeb* threshold in the alternative. **Size the ask below the ECE-alteration line** — an
   over-ask (equal time + holidays + summers in one motion) gets recharacterized as a custody motion
   under *Vodvarka*. Add MCL 722.27a(9) terms: a defined written communication channel, exchange
   logistics, a make-up-time protocol.
2. **Proposed order** (Genesee LCR 2.119(B): attached **and** served), **concurrence certificate**
   (LCR 2.119(A) binds pro se), **notice of hearing**, narrative attachments keyed to the log.
3. **Service pack.** Serve the **party** at the FOC address of record (MCR 2.107(B)(1)(c),
   MCR 3.203) **and** counsel; one proof of service; both MCR 2.119(C) clocks — serve 9 days ahead
   by mail, file 7 days ahead — plus the local praecipe practice, marked PROVISIONAL.
4. **Hearing prep.** MRE apply at referee hearings; do not stipulate the FOC report into evidence
   (*Duperon* line); objection clocks per the cheat sheet.
5. **Hand-back.** Deliverables list plus every `ℹ PROVISIONAL` item compressed into one clerk
   phone-call script.

Every authority you write carries its ledger disposition. Bracket-note the renumbering traps on any
pre-2016 quotation: old (6)/(7)/(8) → current (7)/(8)/(9); old MCL 552.505(d)/507(5) → current
552.505(1)(g)–(h)/507(4). Quote operative legal text from `$C/sources/primary/` verbatim — never
paraphrase a standard — and check each document's own currency stamp before relying on it.

## Phase 3 — Verify (SWEEP, one check per cycle)

Before hand-back, run each as its own cycle so a failure is observed and fixed before the next:
- banned-vocabulary sweep (the translation card is the whitelisted exception)
- weekday labels checked against a real calendar
- every deadline recomputed from its triggering event
- child's name and birthdate absent everywhere, including file names
- no document labeled filing-ready

## Bundled resources — everything travels with the install

Let `$C` = `${CLAUDE_PLUGIN_ROOT}/skills/custody-packet/content/custody-guide`.

| Resource | Path |
|---|---|
| **Archived primary law** — structured markdown of Michigan Court Rules, Rules of Evidence, Genesee local court rules, 2025 child support formula, MJI evidence and DV benchbooks (headings, tables, section numbers preserved) | `$C/sources/primary/*.md` |
| Integrity hashes for the source PDFs | `$C/sources/primary/SHA256SUMS` |
| **Restore the source PDFs** if you want the binary originals (not bundled — the markdown is the working copy); browser-User-Agent fetch, never disables TLS verification | `bash $C/sources/fetch-sources.sh` |
| Full drafting specification — 29 modules, 15 appendices, Appendix A master deadline table, Appendix N glossary | `$C/custody_guide_outline_v2.md` |
| Critical review of the specification | `$C/critical_review_outline_v2.md` |
| 213-source directory | `$C/master_source_directory.md` |
| Independent model reviews and synthesis | `$C/council/` |
| Scope, audience, style | `$C/custody_guide_plan.md`, `$C/custody_guide_research.md` |

Quote operative legal text from `$C/sources/primary/` verbatim; do not paraphrase a standard. Check
the document's own currency stamp before relying on it.

## Case-law tools

- The plugin's `courtlistener` MCP server (declared in `.mcp.json`, credential-free HTTP) is a
  **discovery** tool, not a citator — results are leads; read the opinion before citing, and never
  assert negative treatment from search metadata.
- Source-currency records for the general toolkit:
  `${CLAUDE_PLUGIN_ROOT}/skills/toolkit/content/toolkit/ledger.json`.
- The companion `case-law` and `case-lookup` commands and the `case-law-researcher` subagent cover
  discovery workflow.
