# Master Outline v2 — Pro Se Custody, Parenting-Time, and Child-Support Treatise
## Genesee County, Michigan · 7th Judicial Circuit Court, Family Division

**Document type:** Drafting specification. This is not reader-facing text. It is the contract handed to the treatise-drafting model.
**Supersedes:** `custody_guide_outline.md` (v1).
**Built from:** `custody_guide_plan.md`, `custody_guide_research.md`, and the three council reviews (`model-council-claude_opus_5_0.md`, `model-council-gpt_5_6_sol.md`, `model-council-gemini_3_1_pro.md`) plus `model-council-synthesis.md`.
**Architecture:** GPT-5.6 Sol's pathway-based spine (48-hour triage router → Choose the Path → Build Proof → Ask/Respond/Resolve → Try the Case → Orders/Enforce/Change/Review), carrying **all** substance from Claude Opus 5.0's 18-module revised outline and **all** additions from Gemini 3.1 Pro.
**Merge rule applied throughout:** nothing from any council report was dropped. Where reports overlapped, the substance was merged into a single module. Where reports conflicted, **both positions appear side by side with a `⊗ COUNCIL CONFLICT` note** and an instruction on how to resolve it before publication.
**Reader:** a self-represented parent in a contested Genesee County custody / parenting-time / support matter, facing a high-conflict ex, where parental alienation is a live concern; likely dysregulated, sleep-deprived, and arriving mid-crisis at a specific procedural moment.
**Date of specification:** August 9, 2026.

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — Module 4.4's MiFILE non-use promoted from working assumption to VERIFIED (owner confirmation, 2026-09-07: "Genesee doesn't do MiFILE")._

---

# PART 0 — GOVERNING SPECIFICATION (binding on every module)

Part 0 is machinery, not content. It does not appear in the reader-facing book except where noted (the flag legend and hard labels do; the acceptance tests do not).

## 0.1 The 12-Point Drafting Contract — every module, in this order

Adopted verbatim from GPT-5.6 Sol §5 ("Drafting contract for every module"). **A module is not draftable, reviewable, or shippable until all twelve items are present.** No module may reorder or omit an item; where an item is genuinely inapplicable, the module must say so explicitly ("Route tag: applies to all postures").

1. **Route tag** — original case, pending case, temporary-order stage, postjudgment, enforcement, emergency, or appeal. (Cross-reference the Module 1 pathway taxonomy.)
2. **Authority panel** — the current statute / court rule / SCAO form governing the module, each with a URL and a **"verified as of [date]"** stamp.
3. **Plain-language rule** — 8th–10th grade reading level, short sentences readable aloud in a stressed state (per `custody_guide_plan.md` §7).
4. **Decision tree** — a branching diagram, not a paragraph.
5. **Evidence needed and admissibility issues** — for every fact the module asks the reader to prove: authentication route, hearsay layer, privilege, disclosure obligation, and sponsoring witness.
6. **Genesee local steps** — where to physically go, what to file, what it costs, who to ask. Flagged `ℹ LOCAL PRACTICE`.
7. **Safety / privilege / deadline traps** — the specific ways this module can hurt the reader.
8. **Official forms, not recreated substitutes** — link the SCAO or Genesee form; never publish a competing unofficial version of an official form (`custody_guide_plan.md` §7, Templates).
9. **Drafting aid + worked example** — a blank fill-in aid plus a completed fictional version stating its assumed procedural posture and facts.
10. **Exercise with an explicit completion criterion** — the reader must be able to tell when they are done.
11. **When to stop and seek counsel** — the module's own hard-stop gates (see §0.4).
12. **Glossary terms** — terms introduced or used, each already defined verbatim in Appendix N.

**Absolute rule on templates (Sol §5):** *No filing template may be labeled "filing-ready."* Every sample states the procedural posture and facts it assumes, plus a "do not use if" condition list.

## 0.2 The 12 Acceptance Tests — the gate every drafted module must pass

Adopted verbatim from GPT-5.6 Sol §7. A module that fails any test is returned for redraft.

| # | Test | Passing condition |
|---|---|---|
| 1 | **Path test** | A reader can tell whether the module applies to an original, pending, postjudgment, enforcement, emergency, or appellate posture. |
| 2 | **Authority test** | Every legal claim has a primary source and a verification date. |
| 3 | **Deadline test** | Every period identifies its triggering event — entry, mailing, service, filing, or occurrence. |
| 4 | **Evidence test** | Every proposed exhibit identifies authentication, hearsay, privilege, disclosure, and witness issues. |
| 5 | **Form test** | The official form is linked and its current revision checked. |
| 6 | **Local test** | Statewide law is not mislabeled as Genesee practice, and one judge's policy is not generalized to all judges. |
| 7 | **Safety test** | Ordinary communication, service, mediation, and exchange guidance yields to PPO / no-contact / safety constraints. |
| 8 | **Child test** | No exercise asks the reader to interview, recruit, coach, diagnose, or emotionally rely on the child. |
| 9 | **Adversarial-fairness test** | Each strategy includes the likely counterargument and the reader's own-conduct audit. |
| 10 | **Escalation test** | Criminal, CPS, appellate, jurisdictional, recording, and immediate-danger issues stop the self-help workflow and refer outward. |
| 11 | **Operational-order test** | Proposed relief can be placed on a calendar and enforced without guessing. |
| 12 | **Maintenance test** | Time-sensitive facts live in a change-controlled appendix (Appendix M) rather than being repeated throughout prose. |

## 0.2a Evidence dispositions — what we know, as distinct from reader risk

**Added August 9, 2026. Governs alongside `GUARDRAILS.md` §4, which controls if the two conflict.**

The §0.3 flags describe **reader-facing risk**. This is the separate, internal question of **what the project actually knows**. Every factual claim carries exactly one disposition:

| Disposition | Meaning | May it ship? |
|---|---|---|
| **VERIFIED** | Quoted from an archived primary source in `sources/primary/`, with that document's own currency stamp recorded | Yes |
| **PROVISIONAL** | Sourced to the best available document, but the source is secondary, stale, or locally unconfirmable. Ships **only** with a visible marker naming what is unconfirmed and who can confirm it | Yes, marked |
| **CONFLICTED** | Sources disagree. Both positions stated; no resolution asserted (see `⊗ COUNCIL CONFLICT`) | Yes, as a conflict |
| **UNVERIFIED** | We do not know | **No** — cut it or flag it; never smooth it into confident prose |

**Why PROVISIONAL exists.** Acceptance Test 2 requires a primary source and verification date for every legal claim. §0.8 states that **every Genesee County local fact** is unconfirmable by any model. Read strictly, those two rules together mean **no Genesee module could ever ship** — which would remove the only thing this guide offers that a reader cannot get elsewhere. Without a fourth state, the acceptance tests get quietly ignored during drafting, destroying their force everywhere else. **Acceptance Test 2 is satisfied by a PROVISIONAL claim that carries its marker.**

## 0.3 Flag system — two tiers plus three hard labels

**Tier system (Claude Opus 5.0 §4.5).** The single `VERIFY BEFORE RELYING` flag from v1 is retired. Opus's objection stands: uniform flagging conveys uniform risk, which is false — "a wrong statement about mediation costs the reader an afternoon; a wrong statement about the objection deadline costs them the case." The flag was also applied to the wrong items in v1 (rule texts, the most verifiable category) instead of the volatile ones (fees, judicial and referee assignments, local administrative orders, office hours, form revision dates, MiFILE status).

- **`⚠ TIME-CRITICAL — independently confirm before acting`** — attaches to anything with a jurisdictional or forfeiture consequence. **Every deadline in the book carries this tier and must also appear in Appendix A (Master Deadline Table).**
- **`ℹ LOCAL PRACTICE — may have changed`** — attaches to fees, phone numbers, addresses, office hours, judge and referee assignments, local administrative orders, form revision dates, filing location, and MiFILE/e-service status.

**Three hard labels (GPT-5.6 Sol §4).** These sit *above* the tier system; they are not currency flags, they are stop signs.

1. **`DEADLINE — ACT TODAY`** — states the triggering event, the current default period, the official source, and where to get same-day help.
2. **`DO NOT USE THIS GUIDE ALONE`** — recording law; criminal/CPS overlap; child removal; interstate abduction risk; complex jurisdiction; appeal and stay; expert psychological testing.
3. **`SAFETY OVERRIDE`** — no contact, mediation, exchange, or service step in this book supersedes a PPO, a no-contact order, law-enforcement direction, or an individualized safety plan.

**Per-module verification stamp.** Every module carries a **"verified as of"** date (Opus §4.5). The book must state that Michigan restyled its Rules of Evidence effective January 1, 2024, so pre-2024 secondary sources may cite superseded rule text and numbering — `⚠` the drafting model must confirm the restyling effective date against the SCAO adopting order ([ADM 2021-10 order text via ICLE](https://www.icle.org/contentfiles/MILawNews/rules/MRE/2021-10_2023-09-20_formor_amdmre.pdf)).

**DV interstitials (Opus §3.5).** The safety override is not a front-matter paragraph. It is a **recurring interstitial**: every module capable of producing a dangerous action in a DV context — documentation, recording, confrontation about alienation, enforcement motions, mediation, relocation objections, service of process, exchanges — carries its own DV variant box, because readers do not read front matter.

## 0.4 Stop-and-seek-counsel gates (hard stops)

Consolidated from Sol Appendix F, Opus Appendix H, and Gemini §4. When any trigger below is present, the module **must** interrupt the workflow, say plainly that the guide stops here, and route outward. These also populate Appendix K.

- Active police investigation or possible criminal charge.
- CPS removal, petition, or Central Registry notice.
- PPO or no-contact order that conflicts with a custody or parenting-time order.
- Interstate or international child-location dispute; suspected abduction risk.
- Any hidden recording, recording device, tracker, or account access — **and any recording question at all** (see Module 9).
- A child's disclosure of abuse.
- Any appeal or stay clock running.
- Proposed psychological testing or expert-versus-expert evaluation.
- Threatened unilateral relocation.
- Any question of privilege waiver.
- Immediate danger to the reader or a child.
- Termination of parental rights; defense of an abuse/neglect petition.
- A custody change already granted against the reader.

## 0.5 Banned vocabulary and framing rules

**All three council models agreed on this** (synthesis, "Where Models Agree," row 10). Gemini stated it most operationally: the drafting instructions must **explicitly forbid** the model from putting clinical terms in any drafted pleading template.

- **Never in a template, sample filing, worked example, or suggested oral argument:** "narcissist," "narcissistic," "abuser," "alienator," "parental alienation syndrome," "PAS," "gaslighting," "personality disorder," or any diagnostic label applied to the other parent.
- These words may appear only in framing/orientation prose that explains *why the reader should not use them* (`custody_guide_plan.md` §7, Voice).
- **Plead conduct; let the court name the pattern.** Michigan has no "parental alienation" cause of action. The conduct is reached through MCL 722.23(j) and MCL 722.27a(7)(f)–(g).
- Neutral, court-facing register toward the opposing party throughout. The book models the register the reader should adopt.
- **The guide must not assume the reader is the non-abusive party** (Opus §4.4). A treatise this specific will be read by both kinds of parent. Teach process and proof rather than tactics keyed to an assumed victim posture.

## 0.6 Conflict-of-authority protocol

Where the council reports disagreed, this outline preserves both positions with a `⊗ COUNCIL CONFLICT` box. The drafting model may **not** silently pick one. Each conflict box states: (a) each position and its authority; (b) the practical instruction all positions converge on; (c) who must resolve it before publication. Live conflicts carried into this outline:

| # | Conflict | Location |
|---|---|---|
| 1 | Recording law: three legal theories (participant/non-participant line; vicarious-consent prohibition; unsettled-law hard stop) | Module 9 |
| 2 | ICLE numbering: preserve (Gemini) vs. abandon in reader-facing structure (Opus, Sol) | §0.7 + Appendix L |
| 3 | Depth of restructure: full rebuild (Opus, Sol) vs. incremental insertion (Gemini) | §0.7 |
| 4 | Custody journal: sharply demoted as evidence (Opus, Sol) vs. not addressed (Gemini) | Module 8 |
| 5 | Flag taxonomy: two tiers (Opus) vs. three hard labels (Sol) vs. adequate-for-logistics (Gemini) | §0.3 — resolved by adopting **both** Opus's tiers and Sol's labels as separate layers |
| 6 | MCSF deviation-factor count: 18 per Gemini's direct fetch vs. unverified/unstated by Opus and Sol | Module 22 — **resolved by direct verification; see §0.8** |

**Resolution recorded for #2 and #3:** the reader-facing structure abandons ICLE numbering (Opus §3.1, Sol §3.3). Gemini's provenance concern is preserved in full through **Appendix L (ICLE Crosswalk)**, which maps every module here to the original Lesson 1.1–3.4 numbering. Gemini's substantive insertions are all carried; only its *structural* recommendation is overridden, and the override is recorded here rather than hidden.

## 0.7 Reader-facing navigation labels

Reader-facing stages (Sol §3.3): **Start → Stabilize → Build Proof → Ask/Respond → Resolve → Try → Enforce/Change → Review.** Modules are numbered 1–28 within five Parts. ICLE lesson numbers appear nowhere in the reader-facing text.

## 0.8 Verified-in-this-pass ledger

**Newly verified for v2:** the complete enumerated list of **18** deviation factors in §1.04(E) of the 2025 Michigan Child Support Formula Manual, fetched directly from the primary PDF ([2025 Michigan Child Support Formula Manual](https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf)). This confirms Gemini's count of 18 (reduced from 20 in prior manuals) and resolves flagged item 5 in `custody_guide_research.md` §12. Verbatim text appears in Module 22 and Appendix I.

**SUPERSEDED by the August 9, 2026 verification pass — see `../verification_ledger.md`.** The statewide legal layer is substantially cleared and the primary documents are archived in `sources/primary/`. `courts.michigan.gov` was never robots-blocked for these documents; it rejects requests without a browser User-Agent, which is why earlier passes fell back to snippets.

**Now VERIFIED** (quote from the archive, not from a mirror): MCR 3.207, 3.210, 3.215, 3.218, 3.219, 2.119, 2.302, 2.305, 2.506, 3.206, 7.202, 7.203, 7.204, 7.215; MRE 801(d)(2), 803A, 902, 1101(b); MCL 722.23, 722.26a, 722.27, 722.27a, 552.505a, 552.507, 552.605b, 552.605c, 552.641, 552.642, 552.644, 400.1501, 600.2591, 600.2950, 750.411h; **Genesee LCR 2.119**; the **MRE restyling effective date — January 1, 2024** (ADM File 2021-10); *Vodvarka* (259 Mich App 499; 675 NW2d 847 (**2003** — do not "correct" to 2004)), *Shade* (291 Mich App 17 (2010)), *Hayes* (209 Mich App 385 (1995)); and that **no published Michigan opinion establishes parental alienation as a freestanding claim** (four published opinions mention the phrase; none creates a cause of action).

**Two MCSF items closed:** §1.04(E) confirmed at **18** deviation factors; and §3.03 has **no percentage brackets** — it is an equation. Do not draft brackets.

~~**Still unverified — do not state without independent confirmation:** MCR 2.300-series numeric discovery limits; full holdings of *Shade*, *Berger v Berger*, *Dailey v Kloenhamer*, *Duperon v Duperon*, and the factor (j) line (*McRoberts*, *Kessler*, *MacIntyre*, *Barringer*, *Luna*); *Grew v Knox* (unpublished, persuasive only, MCR 7.215(C)(1)); **whether interference alone clears the *Vodvarka* gateway** — the threshold question for Module 18; MCL 750.350a; CPS Category V and the three-unfounded-reports provision; the hearsay-waiver-by-appointment-order claim; FOC 89 and FOC 57 titles ([FOC 57](https://www.courts.michigan.gov/4a7bf6/siteassets/forms/scao-approved/foc57.pdf)); the currency of the 2000-era Michigan Parenting Time Guideline; **and every Genesee County local fact** — fees, judicial and referee rosters, FOC procedures, CDRP, MiFILE status, local administrative orders, and SCAO form revision dates. Genesee facts are **PROVISIONAL** at best (§0.2a); the toolkit audit found the bench roster genuinely conflict-prone, with a 2024 case-assignment LAO partially stale against the 2025 Family Court Plan.~~ **VERIFIED 2026-09-07 (owner confirmation + official e-filing court list): Genesee/7th Circuit is not a MiFILE court.**

**Wrong-jurisdiction trap:** `circuit7.org` is the **Florida** Seventh Judicial Circuit. Genesee's court is **7thcircuitcourt.com**.

**Three things no model may settle; a Michigan family-law attorney must clear them before publication** (synthesis, Recommendation): (1) the vicarious-consent recording question; (2) every Genesee County local fact; (3) any template a reader might mistake for filing-ready.

---

# FRONT MATTER — Use this guide without losing a right

*Route tag: all postures. Reader-facing stage: Start.*

## FM.0 — What Happened Today? The 48-Hour Triage Router

**This is the most important page in the book** (Opus §3.4(iv), F.0; Sol front matter). It is a decision table, printed on the inside front cover and repeated as the first page of text. Each row states the reader's situation, the governing deadline with its trigger, the tier flag, and the module to go to *right now*.

| "What happened today?" | Go to | Clock | Flag |
|---|---|---|---|
| I was just served with a complaint or motion | M11, M12 | Response period runs from **service** | `⚠` |
| I was served with an **ex parte order** | M14 | **14 days after service** to object or move to rescind/modify (MCR 3.207(B)) | `DEADLINE — ACT TODAY` |
| I got a **referee recommendation** | M16 | **21 days after service** to file a written objection (MCR 3.215(E)) | `DEADLINE — ACT TODAY` |
| I lost — a **final custody or domicile order** entered | M28 | **21 days** to claim appeal (MCR 7.204(A)(1)(a)) — jurisdictional | `DEADLINE — ACT TODAY` |
| My ex denied parenting time | M26 | FOC may decline a complaint over **56 days** old | `⚠` |
| I have a hearing this week | M21, M22, M23 | Exhibit/witness exchange and courtesy-copy deadlines | `⚠` |
| The **FOC report** just came out against me | M15 | Review-and-object right before decision (MCR 3.210(C)(6)) | `⚠` |
| CPS or the police contacted me | M17 | No self-help. Counsel now. | `DO NOT USE THIS GUIDE ALONE` |
| I've been accused of abuse | M17 | Parallel-proceeding firewall applies immediately | `DO NOT USE THIS GUIDE ALONE` |
| I received a **move / change-of-domicile notice** | M27 | Respond before the move happens | `⚠` |
| There is a PPO, or one was just served | M17, M10 | PPO takes precedence over custody/PT orders until modified | `SAFETY OVERRIDE` |
| I'm afraid for my safety right now | FM.2 | Call 911. Stop reading. | `SAFETY OVERRIDE` |
| Nothing has happened yet — I'm deciding whether to file | M1, M2, M4 | Pre-filing safety planning first (FM.5) | — |
| Another state is involved, or the child was taken out of state | M3 | UCCJEA. Counsel now. | `DO NOT USE THIS GUIDE ALONE` |

**Templates/tools:** the router card itself; a **Master Deadline Tracker** (columns: trigger event, date of trigger, service date, computed deadline, official source URL, proof of filing, calendar reminder set y/n); the safety and confidential-address card; the edition/source-change log.
**Exercise (completion criterion):** enter the last five docket events and calculate every possible response deadline. *Done when each date has an official source URL and a calendar reminder.*
**Glossary terms:** service, entry, filing, calendar day, court day, jurisdiction, order, judgment, stay.

## FM.1 — Master Disclaimer as Content

Not boilerplate (`custody_guide_plan.md` §6.1). States: legal information, not legal advice; no attorney-client relationship; Michigan statutes, rules, local administrative orders, forms, and fees change; verify at legislature.mi.gov, courts.michigan.gov, and the Genesee County / 7th Circuit sites; outcomes depend on facts, judge, and evidence no guide can predict. **Adds:** what a lawyer does that this book cannot, and the specific circumstances in which continuing pro se is a mistake (cross-ref Appendix K).

## FM.2 — Safety Override

`SAFETY OVERRIDE`. Immediate danger → 911. Michigan 24-hour DV hotline and the National Domestic Violence Hotline (1-800-799-7233) take priority over every procedural step in this book. Genesee/Flint resources: YWCA Greater Flint PPO-filing assistance, on-site at the courthouse, Room 203 ([Michigan Legal Help — Genesee County Legal Resource Center](https://michiganlegalhelp.org/self-help-centers/genesee-county-legal-resource-center)). `ℹ LOCAL PRACTICE`.

## FM.3 — Edition, Verification, and Flag Legend

Verified-as-of date. Full legend for `⚠ TIME-CRITICAL` and `ℹ LOCAL PRACTICE` and the three hard labels. Note on the **2024 MRE restyling** — pre-2024 secondary sources may cite superseded rule text and numbering. Note that this edition's local facts have a shorter maintenance cycle than its statewide legal content (Appendix M).

## FM.4 — Genesee Quick-Reference Card

`ℹ LOCAL PRACTICE`. 7th Circuit Court, 900 S. Saginaw St., Flint, MI 48502, (810) 424-4355 ([7th Circuit Court](https://7thcircuitcourt.com/)). Genesee County FOC, 630 S. Saginaw St., Ste 2500, Flint, MI 48502, (810) 257-3300, toll-free (877) 543-2660 ([Michigan Legal Help — Genesee County Friend of Court](https://michiganlegalhelp.org/courts-and-agencies/genesee-county-friend-of-court); [Genesee County FOC Handbook 2022](https://cms7files.revize.com/genessecountymi/New%20Handbook%202022.pdf)). **File at Circuit Court Records, 2nd Floor — explicitly NOT at the FOC office** ([Genesee County Custody Motion Packet](https://cms7files.revize.com/genessecountymi/Document_Center/Courts%20and%20Law%20Enforcement/Friend%20of%20the%20Court/Online%20Forms/Pro%20Per/fillable%20Custody%20motion.pdf)). Motion day is Monday. Praecipe filed ≥7 days ahead (**PROVISIONAL** — not in Genesee LCR 2.119; confirm with the clerk). Motion, notice of hearing, and any supporting brief or affidavits must be **served ≥9 days** before the hearing if served by first-class mail, or **≥7 days** if served by delivery — **this is the statewide rule, MCR 2.119(C)(1), not a stricter Genesee requirement.** A response is served ≥5 days (mail) or ≥3 days (delivery) before the hearing, MCR 2.119(C)(2). **⚠ Two separate deadlines apply: MCR 2.119(C)(4) requires the motion be *filed* ≥7 days before the hearing (response ≥3 days), and MCR 2.119(C)(1) requires it be *served* ≥9 days ahead by mail / ≥7 by delivery. The county's posted Notice Regarding Motion Practice (2019) states only the (C)(4) filing rule — a reader relying on it alone who serves by mail is late on service.** **Genesee LCR 2.119 does impose two requirements the statewide rule does not:** (A) a **concurrence certificate** — required of "the attorney of record **or the party in propria persona**" — stating that personal contact was made requesting concurrence and it was denied, or that reasonable and diligent attempts were made; and (B) **a proposed order must be attached to and served with the motion** ([Local Court Rules — Circuit](https://www.courts.michigan.gov/492c71/siteassets/rules-instructions-administrative-orders/local-court-rules/local-court-rules-circuit-court.pdf), eff. 6/1/2025). Fees: general motion $20; custody/parenting-time motion $100 total; support-only motion $60 — all `ℹ LOCAL PRACTICE`, confirm at the [Genesee County Clerk Legal Division fees page](https://www.geneseecountymi.gov/departments/county_clerk/legal_division/fees.php). Genesee is **not** on MiFILE; paper filing is the default; AO No. 2026-3 authorizes a 7th Circuit **electronic-service** pilot (service, not filing) ([AO No. 2026-3](https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/administrative-orders/aos-responsive-html5.zip/AOs/Administrative_Orders/AO_No._2026-3_%E2%80%94_Establishing_Pilot_Project_for_Implementing_Expanded_Electronic_Service.htm)); check [MiFILE Available Courts](https://mifile.courts.michigan.gov/availablecourts) before filing.

## FM.5 — Pre-Filing Safety Planning (before anything else)

**Gemini §4, Safety Issues.** Safety planning must **precede** filing, not follow it. The act of filing — a custody motion or a PPO petition — is itself an escalation trigger. v1 discussed DV safety retroactively; this module moves it in front of the first filing.

**Objectives:** recognize filing as an escalation event; complete a safety plan before the first document goes to the counter; secure the home, workplace, and school; establish a confidential address; identify a safe service method; identify a DV advocate before the reader needs one.
**Templates/tools:** pre-filing safety checklist (locks, phone security, account passwords, school and daycare notification and authorized-pickup list, workplace notification, go-bag, safe contacts); confidential-address protocol; safe-service options; advocate contact card.
**Exercise:** complete the pre-filing safety checklist. *Done when every item is either completed or marked "not applicable" with a one-line reason.*
**Stop and seek counsel:** any current threat; any weapon; any stalking behavior.

## FM.6 — How to Use This Book

Reading order by pathway, not front-to-back. The stage labels. The exercise-type taxonomy (`custody_guide_plan.md` §5): fill-in template, worked example, checklist, scenario exercise, self-assessment/diagnostic, evidence log/journal template, practice script, red-flag spotting. Cumulative-build principle: templates introduced once, referenced thereafter (Appendix O cross-reference map).

---

# PART I — CHOOSE THE CORRECT PATH
*Reader-facing stages: Start, Stabilize.*

Sol's core diagnosis (§1.1): v1 "begins with strategy and then uses 'motion' as though motions were interchangeable. They are not." Part I fixes the sequencing error both Opus (§3.1) and Sol (§3.1) identified — legal standards were at Lesson 7 and procedural survival at Lesson 6, both behind material the reader cannot execute without them.

## MODULE 1 — Case-Stage and Jurisdiction Triage

*Route tag: all. Sol Module 1.*

**Objectives**
- Separate the ten procedural roads, each of which invokes different standards, forms, service rules, and clocks: (1) no existing case or order; (2) pending original action; (3) temporary-order stage; (4) postjudgment modification; (5) enforcement of an existing order; (6) objection to an ex parte order; (7) objection to a referee recommendation; (8) emergency / PPO / CPS / criminal overlap; (9) domicile or interstate-jurisdiction dispute; (10) appeal or stay.
- Identify marriage / paternity / existing-order prerequisites without attempting to teach all paternity or divorce law.
- Screen for UCCJEA home state, an existing other-state order, simultaneous proceedings, emergency jurisdiction, tribal/ICWA indicators, nonparent custody, and international issues.
- Understand that **MC 416 is jurisdictional information, not a routine attachment** ([MC 416 UCCJEA Affidavit](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc416.pdf)).
- Recognize the difference between a postjudgment custody motion (must clear the proper-cause / change-of-circumstances gate), a parenting-time-only request (lower *Shade* framework if it does not alter the ECE), and an emergency ex parte request (distinct irreparable-harm / notice standard).

**Templates/tools:** case-stage flowchart; existing-orders inventory; child residence and case-history table (five years); "outside this guide" referral triggers card.
**Exercises:** classify ten scenarios by procedural path (*done when each has a path, a governing standard, and a form*); complete a five-year residence and case-history chronology (*done when every address, school, and prior case is dated and sourced*).
**Traps:** filing the wrong vehicle; assuming Michigan has jurisdiction; treating MC 416 as paperwork.
**Stop and seek counsel:** any other-state order or proceeding; any tribal/ICWA indicator; any international element; suspected abduction risk. `DO NOT USE THIS GUIDE ALONE`.
**Glossary:** original action, postjudgment, UCCJEA, home state, emergency jurisdiction, paternity, standing, subject-matter jurisdiction.

## MODULE 2 — The Standards That Decide Your Case

*Route tag: all. Opus Module 2 + Sol Module 2, merged. Moved to the front from v1 Lesson 7.*

Opus §3.1: "ECE and *Vodvarka* are the framework that determines whether the reader has a case at all. A reader who reads Lesson 1 without Lesson 7 will build a strategy on a burden they don't understand."

### 2.1 The Established Custodial Environment
MCL 722.27(1)(c) definition, quoted verbatim. ECE can exist in one home, both, or neither. ECE is a question of **fact about how the child actually lives**, not about what an order says.

> ### ⚠ BOXED WARNING — THE TEMPORARY-ORDER / ECE TRAP
> **Placement: page one of this module, and cross-referenced from FM.0, M12, M13, M14, and M17.** Opus calls this "the highest-value single sentence in the entire treatise," and v1 did not contain it.
>
> An established custodial environment is a question of fact, and "it makes no difference whether that environment was created by a court order, without a court order, in violation of a court order, or by a court order that was subsequently reversed" — *Hayes v Hayes*, 209 Mich App 385, 388 (1995) ([quoted in COA unpublished opinion](https://cases.justia.com/michigan/court-of-appeals-unpublished/302626-7.pdf?ts=1396126000); [Hayes summary](https://case-law.vlex.com/vid/hayes-v-hayes-docket-887302332)).
>
> **Operational consequence:** if you agree to a temporary order giving the other parent primary care "just for now," and the case takes 14 months, you may have to overcome **by clear and convincing evidence** an ECE your own signature helped create.
>
> SCAO's own judicial training states that temporary orders "do not automatically create ECE (and sometimes they do)" ([MJI/FOCB ECE material](https://www.courts.michigan.gov/4adec3/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/developing-an-understanding-of-the-established-custodial-environment/nov2024_mjifocb_ecematerial_zubac2.pdf)); Wayne County judicial training says flatly that custody orders alone do not establish a custodial environment ([3rd Circuit custody training](https://www.3rdcc.org/docs/default-source/divisions/family-juvenile/custody-training--juvenile-revised.pdf?sfvrsn=f36622ca_0)).
>
> **Never sign a "just for now" order without reading this section.** `⚠ TIME-CRITICAL`

### 2.2 The Two Burdens
Preponderance vs. clear and convincing; which applies when; **why the court must decide ECE before reaching best interests**. Cross-ref *Bofysil v Bofysil* (working parent and the ECE) and *Pierron v Pierron* (ECE and "important decisions" — school changes, relocation-adjacent) from `custody_guide_research.md` §§4.5, 4.9.

### 2.3 The Gatekeeper: Proper Cause or Change of Circumstances
*Vodvarka v Grasmeyer*, 259 Mich App 499; 675 NW2d 847 (2003) for custody; *Shade v Wright*, 291 Mich App 17 (2010) — lower threshold — for parenting-time-only requests. Why most pro se modification motions die here. What facts clear the bar; normal life changes generally do not. `⚠` — the drafting model must verify both citations and holdings directly (Opus §6; research file §12 items 7–8).

### 2.4 The Twelve Best-Interest Factors
MCL 722.23(a)–(l), quoted verbatim, each with (i) what it means, (ii) what evidence proves it, (iii) how a high-conflict opponent attacks it. Factor **(j)** flagged as the alienation/facilitation factor including its **protective-action carve-out**; factor **(k)** as domestic violence "regardless of whether the violence was directed against or witnessed by the child"; factor **(g)** flagged as *the reader's own credibility exposure*. Cite *Baker v Baker* (factors as a sum total, not a simple majority) and *Fletcher v Fletcher* (standards of review; factor weighting) per research file §§4.3–4.4.

### 2.5 The Parenting-Time Factors — a Separate List (Opus §2.10)
**v1 treated MCL 722.23 as the only factor list. There is a second one.** MCL 722.27a(7)(a)–(i) governs the frequency, duration, and type of parenting time: special needs; nursing infants; likelihood of abuse or neglect of the child; likelihood of abuse of a parent; travel burden; **(f) whether a parent can be expected to comply with the order**; **(g) whether a parent has frequently failed to exercise parenting time**; threatened or actual detention or concealment — with the express carve-out that a custodial parent's temporary residence with the child **in a domestic-violence shelter is not evidence of intent to conceal** ([MCL 722.27a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27a); [SCAO Establishing Parenting Time checklist](https://www.courts.michigan.gov/4ab6e0/siteassets/publications/benchbooks/qrms/family/domestic-relations/establishing-parenting-time-checklist.pdf)). **Factors (f) and (g) are the alienated parent's statutory hooks** and were absent from v1.

### 2.6 Joint vs. Sole; Legal vs. Physical
MCL 722.26a — the court must consider joint custody on request and state reasons for granting or denying it. The ability-to-cooperate requirement (*Foskett v Foskett*) and why it cuts against joint legal custody in high-conflict cases — **including against the reader**. `⚠` full current text of MCL 722.26a unverified (research §12 item 1).

### 2.7 Framing the Relief Precisely
Custody vs. parenting time are different requests with different standards. Requesting sole custody merely because conflict exists may reward conflict manufacture or expose the requester under factor (j) (Sol §4, Strategy traps).

**Templates/tools:** ECE / burden decision tree; **Best-Interest Evidence Matrix** — 12 factors × (my evidence / their likely evidence / witness / exhibit / **admissibility route**) — the master template referenced throughout; custody-vs.-parenting-time relief worksheet; proper-cause/change worksheet; verbatim-quote reference cards for the ECE clause and the two burdens; MCL 722.27a(7) factor worksheet.
**Exercises:** apply the complete threshold → ECE → merits sequence to four scenarios; apply *Vodvarka* to three fact patterns, two of which fail; draft a one-paragraph neutral statement of requested relief. *Done when the relief statement can be placed on a calendar and enforced without guessing (acceptance test 11).*
**Glossary:** ECE, proper cause, change of circumstances, preponderance of the evidence, clear and convincing evidence, best interests of the child, legal custody, physical custody, joint custody, sole custody.

## MODULE 3 — Jurisdiction, UCCJEA, and Interstate Issues

*Route tag: all. Sol §2, "Additional non-obvious gaps," item 1; Opus §17.4.*

v1 listed MC 416 as an attachment but never taught jurisdiction.

**Objectives:** home-state jurisdiction; simultaneous proceedings in two states; temporary emergency jurisdiction; continuing exclusive jurisdiction; registration and enforcement of an out-of-state order; when Michigan may lack power; why leaving the state first is catastrophic; international and tribal/ICWA indicators.
**Templates/tools:** home-state determination worksheet; existing-order registration checklist; MC 416 completion walkthrough; jurisdiction referral card.
**Exercise:** complete MC 416 from the five-year residence chronology built in Module 1. *Done when every residence period is accounted for with no gaps.*
**Stop and seek counsel:** `DO NOT USE THIS GUIDE ALONE` on every interstate or international question.
**Glossary:** UCCJEA, home state, continuing exclusive jurisdiction, temporary emergency jurisdiction, registration of a foreign order, ICWA.

## MODULE 4 — How This System Actually Works: Genesee Court Map, Filing, and Orientation

*Route tag: all. Opus Module 1 (moved to front from v1 Lesson 6) + Sol Module 3, merged. Opus §3.3: "A reader who does not know how to file cannot execute Lesson 1."*

### 4.1 Who Is Who
Judge; domestic-relations referee; FOC caseworker; FOC investigator; clerk / Circuit Court Records; LGAL; GAL; attorney for the child; custody evaluator; mediator; Legal Resource Center navigator. **What each can and cannot decide.** (Full role/evidentiary comparison lives in Module 16; this is the orientation version.)

### 4.2 The Two Tracks
Referee track vs. judge track; when each applies; **why the referee hearing is usually the real trial** for a Genesee pro se parent.

### 4.3 Filing Mechanics
`ℹ LOCAL PRACTICE`. Paper filing at Circuit Court Records, 2nd Floor; caption and format under MCR 1.109; the **color-coded praecipe** system (yellow = domestic relations motion praecipe; blue = contested domestic relations at-issue; white = general civil) filed with the clerk **≥7 days** before the hearing, listing parties, case number, nature of the motion, attorneys, hearing date, and assigned judge ([Michigan Local Court Rules — Circuit Court compilation](https://www.courts.michigan.gov/498ad4/siteassets/rules-instructions-administrative-orders/local-court-rules/local-court-rules-circuit-court.pdf) — `ℹ` verify the Genesee-specific section); notice of hearing; proof of service; the **9-day mail-service period, which is statewide law (MCR 2.119(C)(1)), alongside the separate MCR 2.119(C)(4) filing deadline** (motion filed ≥7 days, response ≥3 days before hearing), which Genesee announced it would strictly enforce effective March 4, 2019 ([Notice Regarding Motion Practice](https://cms2.revize.com/revize/geneseecountyjudicialcourt/Documents/Quick%20Links/Notice%20Regarding%20Motion%20Practice/Notice-Motion-Practice.pdf)).

### 4.4 Filing Method Currency
Genesee is not a MiFILE court; the AO 2026-3 pilot concerns **electronic service, not filing**. **VERIFIED 2026-09-07 (owner confirmation)** — this is no longer a working assumption pending a confirmation call; treat "Genesee does not use MiFILE" as settled. Re-check only if a future AO or the MiFILE Available Courts listing changes. `ℹ LOCAL PRACTICE` still applies to the AO 2026-3 e-service pilot's current live/enforced status.

### 4.5 Fees, Waivers, and the Real Cost of a Case
Motion fees ($20 general / $100 custody-parenting time / $60 support-only, `ℹ`); fee waiver **MC 20** — eligibility (means-tested benefits: Medicaid, SSI, SNAP), form, supporting documentation, what happens next ([MC 20](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc20.pdf); [Michigan Legal Help DIY Fee Waiver](https://michiganlegalhelp.org/resources/going-court/do-it-yourself-fee-waiver)). Total-cost planning: copying, service, transcripts, mediator fees, evaluator fees, LGAL fees, subpoena and witness fees. **Distinguish fee waiver from an attorney-fee request against the other party — those are different things** (Module 24.6).

### 4.6 Motion Day, Judge-Specific Policies, and Courtroom Conduct
Monday motion day, confirmed by a sitting judge: "Mondays are always our motion day"; contested motions in person, uncontested/stipulated often by Zoom ([ICLE Q&A with Judge Anthony J. McDowell](https://community.icle.org/blogs/lindsey-a-dicesare/2026/05/18/qa-with-judge-anthony-j-mcdowell-7th-circuit-court)). **Judge-specific policies vary and must be checked for the reader's assigned judge** — illustrated, not generalized, by Judge Hood's published policies (courtesy copies required under MCR 2.119(A)(2)(d); motions in limine ≥3 weeks before trial; two adjournments without re-filing; published Monday schedule: 8:30 PPO motions, 9:30 show-cause pretrials, 10:30 objections to referee recommendations, 1:30 contested motions A–K, 2:30 L–Z) ([Judge Hood Policies and Procedures](https://cms2.revize.com/revize/geneseecountyjudicialcourt/Documents/General%20Information/Judges/Hood-Policies-and-Procedures.pdf)). **Acceptance test 6 applies: one judge's policy is not all judges' policy.** Courtroom decorum: forms of address, standing, not interrupting, referring to the other party formally, time discipline, what judges read as instability.

### 4.7 Getting Help Without Hiring Full Counsel
Limited-scope representation under MCR 2.117(B) with MCR 2.107 and MRPC 1.0/1.2/4.2/4.3; Form **MC 516** Notice of Limited Scope Appearance ([MC 516](https://www.courts.michigan.gov/4aa4e1/siteassets/forms/scao-approved/mc516.pdf); [SBM, New Limited Scope Representation Rules](https://www.michbar.org/news/newsdetail/New-Limited-Scope-Representation-Rules-Effective-January-1?nid=5507)). Note MCR 5.117 is the probate analogue and must not be cited here. Ghostwriting; consulting-only arrangements. Genesee County Legal Resource Center (900 Saginaw St., M–F 8:30–4:30; Legal Aid of Eastern Michigan Mondays 10–3; YWCA Greater Flint PPO help Mondays 9–noon and Wednesdays noon–3, Room 203) ([Michigan Legal Help](https://michiganlegalhelp.org/self-help-centers/genesee-county-legal-resource-center)); Legal Services of Eastern Michigan ([lsem-mi.org](https://lsem-mi.org/)); SBM Lawyer Referral ([lrs.michbar.org](https://lrs.michbar.org/)); Michigan Legal Help DIY tools. **Legal information vs. legal advice: clerks, referees, and navigators cannot tell the reader what to do.**

**Templates/tools:** Genesee filing route card; judge-policy verification log (judge, policy, URL, date checked, checker); praecipe / service / courtesy-copy checklist; fee and contact currency table; MC 20 completion checklist; resource directory; "which resource do I need?" decision worksheet; courtroom decorum one-pager.
**Exercises:** build a complete filing packet backward from a hypothetical hearing date (*done when the praecipe, motion, notice, proof of service, and fee or waiver are all dated correctly*); verify one current judge policy and record the URL and date; red-flag spotting — five filing errors that get a motion rejected at the counter.
**Glossary:** praecipe, motion day, referee, clerk, Friend of the Court, courtesy copy, proof of service, fee waiver, limited-scope representation, assigned judge, MiFILE, e-filing, electronic service.

---

# PART II — BUILD PROOF BEFORE FILING
*Reader-facing stage: Build Proof.*

**The council's unanimous finding.** All three models identified evidence and admissibility as the single largest gap and located the same root cause: v1 teaches strategy before it teaches proof. Opus: "a reader who wins" versus "a reader who stands at a podium holding a three-ring binder that the judge will not look at." Sol: admissibility "determines what the reader must preserve and obtain months earlier." Gemini: the "pro se trap." Evidence is a **spine**, not a chapter, and it sits before every tactical module.

## MODULE 5 — Where the Rules of Evidence Apply, and Where They Don't

*Route tag: all. Opus Module 3.1.*

**Objectives**
- **The Michigan Rules of Evidence apply at referee hearings.** MCR 3.215(D)(1): "The Michigan Rules of Evidence apply to referee hearings" ([MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215)). v1 treated the referee hearing as an informal step. **For most Genesee pro se parents the referee hearing *is* the case, and it is their first and often only contested evidentiary proceeding.**
- They apply at trial.
- They do **not** apply to in camera child interviews — MRE 1101(b)(6) ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf)).
- They do **not** apply to the court's consideration of an FOC report submitted under MCL 552.505(1)(g) or (h) — MRE 1101(b)(9) (same source). **This is the setup for the FOC report paradox in Module 15.**
- The 2024 restyling means older secondary sources may cite superseded MRE numbering. `⚠`

**Templates/tools:** "where do the rules apply?" one-page matrix (proceeding type × rules apply y/n × consequence).
**Exercise:** for five proceedings in the reader's own case, state whether the MRE apply. *Done when each answer cites a rule.*
**Glossary:** Michigan Rules of Evidence, in camera, referee hearing, evidentiary hearing.

## MODULE 6 — Relevance, Hearsay, and the Rules You Will Actually Use

*Route tag: all. Opus Module 3.2–3.5 + Sol Module 4, merged.*

**Objectives**
- Relevance and the judge's patience: MRE 401/402/403. Why "everything bad she ever did" loses. Over-documenting every slight buries the material facts and makes the writer look obsessive (Sol §4).
- Personal knowledge; the difference between a fact and an inference.
- **Hearsay in ninety seconds:** the definition and the four questions to ask before offering any statement. Hearsay **within** hearsay in medical, school, police, CPS, GAL, and evaluator records — a record admitted under MRE 803(6) does not admit every statement inside it.
- **The rule that wins cases — MRE 801(d)(2), an opposing party's statement.** Anything the other parent said, texted, emailed, or posted is **not hearsay** when offered against them. Worked examples. Opus calls this "the single most useful rule for a parent."
- **The exceptions you will actually use:** MRE 803(1) present sense impression; 803(2) excited utterance; 803(3) then-existing state of mind; 803(4) statements for medical diagnosis or treatment; 803(5) recorded recollection; 803(6) records of regularly conducted activity (school, medical, therapy); 803(8) public records (police reports and CPS documents — **with the law-enforcement caveat**); MRE 612 refreshing recollection.
- Completeness and context; original/duplicate rules under MRE 1001–1008 — duplicates are generally permitted unless authenticity or fairness is genuinely disputed ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf)).
- Privileges and confidentiality: therapist-patient, physician-patient, spousal; child records; releases; what filing sensitive material publicly costs.
- **Preserving an evidentiary issue**: objection → grounds → ruling → offer of proof.

> ### ⚠ THE CHILD-HEARSAY PROBLEM — MRE 803A DOES NOT APPLY IN CUSTODY CASES
> **Opus §2.1(c). This is devastating to v1's alienation lesson as written, whose implicit theory of proof was "the child said Mom told him I don't love him."**
>
> The tender-years exception, MRE 803A, reaches only **criminal and juvenile delinquency proceedings** ([SCAO Sexual Assault Benchbook, Tender-Years Exception](https://www.courts.michigan.gov/4a3004/siteassets/publications/benchbooks/sabb/sabbresponsivehtml5.zip/SABB/Ch_6_Evidence/Tender-Years_Exception.htm)). The reader **will** find it online and assume it saves the child's statement. It does not.
>
> **Legitimate routes instead:** (1) the statement offered **not for its truth** — effect on the listener; (2) MRE 803(3) then-existing state of mind as circumstantial evidence; (3) the **in camera interview** under MCR 3.210(C)(5), which the court may conduct privately with **questioning limited to the reasonable-preference factor** ([MCR 3.210](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-210)) and to which the rules of evidence do not apply (MRE 1101(b)(6)) — the reader must understand **both halves: the interview exists, and it is narrow**; it is not a channel for the child to narrate the other parent's misconduct; (4) a court-appointed evaluator or LGAL; (5) a treating therapist; (6) **MRE 801(d)(2)** where the alienating statement was made by the other parent directly.

**Templates/tools:** hearsay decision tree; four-question hearsay screen card; objection and offer-of-proof cards; party-opponent worked-example set; privilege screen.
**Exercises:** analyze five proposed exhibits for every evidentiary step (*done when each exhibit has an authentication route, a hearsay answer, a privilege answer, a disclosure answer, and a sponsoring witness*); convert a journal entry into admissible-source leads.
**Glossary:** relevance, foundation, hearsay, nonhearsay, party-opponent statement, business record, public record, present sense impression, excited utterance, state of mind, recorded recollection, refreshing recollection, privilege, offer of proof, hearsay within hearsay.

## MODULE 7 — Authentication: There Is No Shortcut in Michigan

*Route tag: all. Opus Module 3.7 — flagged by the synthesis as one of the three highest-weight discoveries in the entire council.*

> ### ⚠ MICHIGAN HAS NO FRE 902(13)/(14) ANALOGUE
> Michigan's MRE 902 self-authentication list runs **(1)–(11)** and does **not** include the certified-electronic-record provisions that exist federally as FRE 902(13)–(14) ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf); compare [FRE 902](https://www.law.cornell.edu/rules/fre/rule_902)).
>
> **Every text message, screenshot, call log, and OurFamilyWizard export must be authenticated by live testimony under MRE 901. There is no certificate shortcut.** A guide that tells a reader to "print your texts and bring them" without teaching an MRE 901 foundation script is setting them up.

**Objectives**
- MRE 901's standard: sufficient proof that an item is what its proponent claims it is; the rule expressly recognizes voice identification and process/system evidence as authentication methods ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf); [SCAO Evidence Benchbook, Foundation](https://staging.courts.michigan.gov/4a50d8/siteassets/publications/benchbooks/evidence/evidenceresponsivehtml5.zip/Evidence/Ch_1_General/Foundation.htm)).
- **Authentication does not cure hearsay** (Sol §1.2). These are two separate questions and a "foundation script" that teaches ritual words without the predicates invites the reader to believe otherwise.
- A screenshot is not "admissible because it is a screenshot." The reader must be able to identify the account, the participants, the date, the continuity of the conversation, and the method of capture.
- What MRE 902(1)–(11) *does* cover, and how to use certified public records.

**Templates/tools — verbatim foundation scripts, formatted for reading at the podium**, one page each for: text-message thread; screenshot; email; photograph (with metadata); video; voicemail; OurFamilyWizard / TalkingParents / AppClose export; social-media post; school record; medical record; police report; calendar; business-record certification; journal/calendar; opposing-party statement; hearsay within hearsay; offer of proof; preserving a ruling. (These are Appendix C; the module introduces and teaches them.)
**Exercises:** practice script — lay the foundation for a text thread, out loud, three times (*done when the reader can do it without the card*); produce a complete, chronologically numbered text exhibit with source notes; identify authenticity defects in three sample screenshots.
**Glossary:** authentication, self-authentication, MRE 901, MRE 902, duplicate, original, metadata, native file, chain of custody, sponsoring witness.

## MODULE 8 — Your Custody Journal, Documentation, and Digital Preservation

*Route tag: all. Opus Module 3.8 + Sol Modules 5 and 7, merged.*

> ### ⊗ COUNCIL CONFLICT — the custody journal
> **Opus:** the journal is "largely inadmissible self-serving hearsay" when offered by its author for the truth of its contents. It is valuable as an MRE 612 memory refresher, as impeachment material, as recorded recollection under MRE 803(5) in narrow circumstances, and as the backbone of the reader's own live testimony. **v1 presented journaling as if the journal were the evidence. It is not; the reader's testimony is the evidence and the journal is the scaffolding.**
> **Sol:** same demotion, plus a distinct warning — **do not send the whole journal to an evaluator or attach it wholesale to a motion**; doing so can disclose hearsay, privileged material, litigation strategy, and inflammatory commentary. v1's advice to "share the custody journal with the evaluator" must not survive drafting.
> **Gemini:** did not address the journal's admissibility.
> **Convergence:** keep the journal; demote it evidentially; never file or hand it over wholesale. **Both Opus's and Sol's warnings appear in the drafted text.**

**Objectives**
- Keep a journal that survives cross-examination: contemporaneous, factual, dated, no conclusions, no editorializing, **no retroactive additions**.
- Separate **facts / inferences / emotions / requested action** (Sol §2).
- Maintain a concise, corroborated incident log rather than an exhaustive grievance record.
- Preserve native texts, emails, app exports, voicemails, photographs, and metadata; capture complete conversation context; document the collection method.
- **Litigation hold on the reader's own data** — do not edit, selectively delete, or "clean up" anything.
- Redact protected identifiers; avoid public filing of unnecessary child, medical, address, or account information; confidential-address protocol.

**Templates/tools:** custody journal template (date/time, factual event description, location, witnesses, related communications, factor tag, follow-up) **carrying a "do not file wholesale / do not hand to an evaluator wholesale" warning**; facts/inference/emotion/action worksheet; litigation-hold checklist; digital chain-of-custody log; redaction and confidential-address checklist.
**Exercises:** complete one week of journal entries from a fictional scenario, then from the reader's own recent events; audit ten journal entries for relevance, tone, corroboration, and privacy; red-flag spotting — sort sample entries into "useful evidence," "needs corroboration," and "leave out."
**Traps:** journaling as catharsis; retroactive reconstruction; privacy violations; documenting by provocation (Module 12).
**Glossary:** contemporaneous documentation, corroboration, inference, custody journal, metadata, native file, chain of custody, litigation hold, redaction, confidential address.

## MODULE 9 — Recording Law and the Do-Not-Do List

*Route tag: all. **`DO NOT USE THIS GUIDE ALONE`.** Opus §2.2 + Gemini §2 + Sol §1.4, presented side by side.*

This module is the single most legally hazardous subject in the book. v1's sentence — "one-party consent generally" — must not survive drafting. Sol: "This is not a 'VERIFY BEFORE RELYING' issue. It is a potential felony/privacy/safety issue requiring an affirmative warning not to act from a generic summary."

> ### ⊗ COUNCIL CONFLICT — THREE LEGAL THEORIES, PRESENTED SIDE BY SIDE
> **All three must appear in the drafted text, in this order, in a single boxed section. The drafting model may not choose among them.**
>
> **Theory 1 — Claude Opus 5.0: the participant / non-participant line.**
> MCL 750.539c is drafted as all-party consent, but *Sullivan v Gray*, 117 Mich App 476; 324 NW2d 58 (1982), construes "eavesdrop" to exclude a **participant** to the conversation ([Sullivan v Gray](https://law.justia.com/cases/michigan/court-of-appeals-published/1982/57301.html)). The State Bar's ethics opinion RI-309 proceeds on the same understanding ([SBM RI-309](https://www.michbar.org/opinions/ethics/numbered_opinions/ri-309)). The Michigan Supreme Court declined to answer the certified question in 2021 ([MSC docket 162121](https://www.courts.michigan.gov/c/courts/msc/case/162121/)). On **March 30, 2026**, the Eastern District of Michigan granted summary judgment in *AFT Michigan v Project Veritas*, confirming Michigan remains a one-party-consent state for participants and that a person whose presence is apparent counts as a party whether or not they speak ([Butzel](https://www.butzel.com/alert-butzel-prevails-in-long-running-michigan-eavesdropping-statute-litigation); [Detroit News](https://www.detroitnews.com/story/news/politics/2026/04/03/federal-judge-upholds-michigans-one-party-consent-recording-law/89449448007/); [Michigan Lawyers Weekly](https://milawyersweekly.com/news/2026/05/04/fraud-infiltration-project-veritas/)).
> **Consequence under this theory:** *Sullivan* is explicit that a participant's consent does **not** authorize a **third party** to record. **The single most common recording idea an alienated parent has — sending the child to the other parent's house with a phone recording, or a hidden recorder in a backpack — is non-participant recording and is felony conduct, not a clever evidence strategy.** So is placing a device in a car the other parent uses, or in the other parent's home. Punishment under MCL 750.539c runs to **2 years and/or $2,000**.
>
> **Theory 2 — Gemini 3.1 Pro: an affirmative vicarious-consent prohibition.**
> Michigan operates as a one-party-consent state **only for participants**, per *Sullivan v Gray* and as affirmed by the Sixth Circuit in *Fisher v Perron*, 30 F.4th 289 (6th Cir. 2022) ([Recording Law — Michigan](https://www.recordinglaw.com/united-states-recording-laws/one-party-consent-states/michigan-recording-laws/)). Gemini's distinct doctrinal claim: there is a **vicarious-consent prohibition** — **a parent cannot consent on behalf of a minor child to record the child's conversations with the other parent.** Instructing a pro se parent to record without this caveat risks exposing them to felony eavesdropping charges.
>
> **Theory 3 — GPT-5.6 Sol: the unsettled-law hard stop.**
> Sol declines to state a rule. The statutory wording refers to the permission of **all** persons; the issue has generated serious interpretive litigation; **MCL 750.539d separately restricts devices used to observe or record in a private place**; and interstate calls may implicate another state's law ([MCL 750.539a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-750-539a); [MCL 750.539d](https://www.legislature.mi.gov/Laws/MCL?objectName=MCL-750-539D); [*Lewis v LeGrow*](https://www.courts.michigan.gov/siteassets/case-documents/uploads/OPINIONS/FINAL/COA/20030821_C234723_55_161O.234723.OPN.COA.PDF)). Sol's architecture: state the participant rule **cautiously**, then impose a **stop-and-get-specific-advice gate** for hidden devices, recordings in another person's home, calls crossing state lines, recording a child, and any recording touching a PPO, criminal allegation, therapy, school, or medical setting.
>
> **Where all three converge — the practical instruction, which is not in doubt:** do not record the child; do not send a child in with a recorder; do not plant devices; do not record conversations you are not part of.
>
> **Resolution architecture adopted (per the synthesis):** use **Sol's hard-stop gate as the default**, **Opus's participant/non-participant framing for the explanation**, and present **Gemini's vicarious-consent position as a separate stated position** — because the three rest on different legal theories and "the guide will be read by people whose liberty depends on getting this right."

> ### 🔒 ATTORNEY MUST VERIFY BEFORE PUBLICATION
> **The vicarious-consent question and the current status of the participant exception must be confirmed by a licensed Michigan attorney before a single sentence of this module is published.** No model may resolve it. This box appears in the drafting file and is replaced, before publication, by a signed verification note recording the attorney's name, the date, and the authority relied on. If verification is not obtained, the module publishes with the hard stop and **no** affirmative statement that any recording is lawful.

### 9.1 The Recording-Law Stoplight (Sol Module 5)
- **GREEN** — only after verified facts about participation, location, and jurisdiction, *and* only after the attorney-verification note above is in place.
- **YELLOW** — any uncertainty. Stop and ask.
- **RED** — hidden device; another person's home or car; recording a child; recording a conversation the reader is not part of; interstate call; any PPO, criminal, CPS, therapy, school, or medical overlap.

### 9.2 ⚠ THE DO-NOT-DO LIST (boxed, unmissable, placed *before* the documentation module in the reading order)
Opus §4.1 calls this the highest-severity risk in the document: v1 told the reader to document aggressively without bounding the methods. Foreseeable reader actions that are **crimes**:

| Action | Statute / consequence |
|---|---|
| Recording a conversation you are **not** part of — **including sending your child in with a recorder** | MCL 750.539c per *Sullivan v Gray*; up to 2 years and/or $2,000 ([Sullivan](https://law.justia.com/cases/michigan/court-of-appeals-published/1982/57301.html)) |
| Installing a recording or observation device in a **private place** — the other parent's home or vehicle | [MCL 750.539d](https://www.legislature.mi.gov/Laws/MCL?objectName=MCL-750-539D) |
| Accessing the other parent's email, phone, or social-media accounts with remembered or shared credentials | Unlawful access; destroys credibility; may taint the evidence. **This is the most common pro se evidence-gathering method.** |
| **GPS-tracking the other parent's vehicle** | Criminal and civil exposure; factor (j) and factor (g) damage |
| Reading the other parent's mail | Federal and state exposure |
| Using the child as an intelligence asset — interrogating, tasking, or debriefing | Factor (j) damage; harm to the child; violates acceptance test 8 |

**Consequences stated plainly in every entry:** criminal charge; evidence excluded; credibility destroyed; **factor (g) and factor (j) damage**; potential PPO exposure.

### 9.3 If a Recording Already Exists
Even a lawfully made participant recording must still be **authenticated** under MRE 901 (Module 7) and analyzed for hearsay — note that a recording of the **other parent** is a party-opponent statement under MRE 801(d)(2) and therefore not hearsay. Also: **some judges react badly to recordings of children even when lawful.** Do not delete a recording that may be evidence in a proceeding; ask counsel.

**Templates/tools:** recording-law stoplight card; Do-Not-Do list (also Appendix J); "I already recorded something" decision tree ending in a counsel referral.
**Exercise:** red-flag spotting — classify eight proposed recording scenarios as red/yellow and identify which statute is implicated. *Done when no scenario is classified green.*
**Glossary:** eavesdropping, private place, participant recording, vicarious consent, one-party consent, MCL 750.539c, MCL 750.539d.

## MODULE 10 — Discovery, Records, and Subpoenas

*Route tag: pending case, postjudgment, enforcement. Opus Module 7 + Sol Module 6 + Gemini's MC 11 addition, merged. All three models flagged the same trap.*

### 10.1 What Discovery Is For
Plan discovery by **disputed element**, not by curiosity. In a custody case, discovery is usually about income, records, and third-party accounts — not about winning the narrative. Tie every request to a row in the Best-Interest Evidence Matrix.

### 10.2 ⚠ The Domestic-Relations Initial-Disclosure Exemption (Sol §1.3)
**Domestic-relations actions are exempt from the general initial-disclosure regime under MCR 2.302(A)(4).** The reader cannot assume the other side must volunteer the ordinary civil disclosures ([Michigan Judicial Institute, Disclosure](https://www.courts.michigan.gov/4aeeef/siteassets/publications/benchbooks/civil/civilresponsivehtml5.zip/Civil/Ch_5_Discovery/Disclosure.htm)). A false expectation here wrecks discovery planning.

### 10.3 Party Discovery
Interrogatories, requests for production, requests to admit, depositions (and their real cost and complexity for a self-represented party). MCR 2.300-series limits and timing — `⚠ VERIFY` current numeric limits (research §12 item 4). Scope and proportionality; objections; supplementation; protective orders; motions to compel; sanctions; preservation letters; discovery log; meet-and-confer letter.

### 10.4 ⚠ SUBPOENAS — THE TWO-TRACK RULE FOR PRO SE LITIGANTS
**All three council models identified this as a trap v1's discovery module rests on a false premise about.**

- **Hearing and trial subpoenas:** MCR 2.506(B)(1) — a subpoena signed by an attorney of record **or by the clerk of the court** has the same force as a judge's order. As a pro se party you obtain a **clerk-issued** [MC 11](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc11.pdf). Service at least **2 days** before testimony, and **14 days before** when documents are requested ([MCR 2.506](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-506)).
- **Discovery subpoenas to non-parties:** MCR 2.305(A)(1) — "a represented party may issue a subpoena to a non-party… **An unrepresented party may move the court for issuance of non-party discovery subpoenas**" ([MCR 2.305](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-305); [MJI, Request for Documents](https://www.courts.michigan.gov/4a4e88/siteassets/publications/benchbooks/civil/civilresponsivehtml5.zip/Civil/Ch_5_Discovery/Request_for_Documents.htm)). **You must file a motion. You cannot self-issue.** A lawyer's ability to issue one must not be copied into a pro se template.
- Witness fees and mileage; service mechanics; objections to a subpoena; quashing.

### 10.5 Getting Specific Records
School records and **FERPA**; medical and therapy records and **HIPAA** and privilege — including the **child's** therapist; police reports and CAD logs; employment and payroll; **MDHHS/CPS records**, which have their own process and generally contemplate an attorney-signed subpoena with proof of representation ([MDHHS subpoena page](https://www.michigan.gov/mdhhs/inside-mdhhs/legal/subpoena)); phone records; bank records; platform/social-media records; public-records requests; signed releases as an alternative to compulsion.

### 10.6 Connect Discovery Backward to Admissibility
**Plan every subpoena backward from the MRE 803(6) or 803(8) foundation you will need — including subpoenaing the *custodian of records*, not just the records.** Request a records-custodian certification. (Remember Module 7: Michigan has no self-authentication certificate for electronic records, so plan for a live witness.)

### 10.7 When the Other Side Won't Comply
Motion to compel; costs; **the fee hook in MCR 3.206(D)(2)(b)** (Module 24.6). Proportionality and good-faith certification to avoid sanctions running against the reader.

**Templates/tools:** discovery plan mapping fact → source → mechanism → **admissibility route**; narrow interrogatory / RFP / RFA drafting aids; nonparty-records flowchart; **motion for issuance of non-party discovery subpoenas under MCR 2.305(A)(1)** (annotated drafting aid); MC 11 checklist including service and fees; records-custodian certification request; preservation letter; discovery log; meet-and-confer letter.
**Exercises:** draft one proportional request and one valid objection; build a subpoena plan for school attendance records **without assuming admissibility** (*done when the plan names the custodian, the foundation rule, and the sponsoring witness*); Gemini's worked example — an MC 11 requesting school attendance records.
**Traps:** invalid subpoena; privacy violation; sanctions for overbroad discovery; assuming records arrive admissible.
**Glossary:** discovery, interrogatory, request for production, request for admission, deposition, subpoena (trial vs. discovery), custodian of records, privilege log, protective order, motion to compel, sanctions, FERPA, HIPAA.

## MODULE 11 — Case Strategy, Theory of the Case, and Your Own Exposure

*Route tag: all. Opus Module 4 (v1 Lesson 1, now downstream of standards and evidence).*

**Objectives**
- Define the outcome **in order language** — what you are actually asking for, expressed as a clause a court could enter.
- Build a theory of the case: one sentence a judge can repeat; how conduct evidence maps onto the MCL 722.23 and MCL 722.27a(7) factors.
- Honest case assessment: strengths, weaknesses, what your opponent will say about you, and a **factor (g) self-audit** (mental and physical health — the reader's own credibility exposure).
- Cost, time, and energy budget: realistic timeline for a contested Genesee custody case; what each stage costs; when to spend on limited-scope counsel.
- Settlement posture: what is worth trading; why joint legal custody with a non-cooperative party often fails; **what to never concede** — ECE-affecting temporary terms (Module 2.1), hearsay waivers in evaluation orders (Module 19.3), open-ended relocation consent (Module 27).
- **Adversarial-fairness discipline (acceptance test 9):** every strategy in this book states the likely counterargument and requires the reader's own-conduct audit.

**Strategy traps to teach explicitly (Sol §4):** calling all resistance "alienation" can obscure abuse, developmental needs, or a child's independent experience; equating an unsubstantiated CPS report with a fabricated one overstates the evidence; requesting sole custody merely because conflict exists may reward conflict manufacture; over-documenting buries the material facts; sending the whole journal to an evaluator backfires; treating a co-parenting app as inherently court-favored is unsupported — it is only a tool, and access, cost, disability, safety, and order language matter; filing contempt on a vague order may fail, and clarification or modification may be the better first objective; assuming an appeal pauses an adverse order is dangerous — it ordinarily does not ([MCR 7.209](https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/michigan-court-rules/michigan-court-rules-responsive-html5.zip/Michigan_Court_Rules/Court_Rules_Chapter_7/Court_Rules_Chapter_7.htm?rhtocid=_7)).

**Templates/tools:** one-page case theory memo; case assessment worksheet with an opponent's-view column; factor (g) self-audit; cost/time budget worksheet; settlement posture worksheet with a "never concede" list.
**Exercise:** write the case theory in one sentence, then test it against the evidence matrix. *Done when every clause of the theory has at least one admissible exhibit or witness behind it.*
**Glossary:** theory of the case, prayer for relief, concession, settlement posture.

---

# PART III — ASK, RESPOND, AND RESOLVE BEFORE TRIAL
*Reader-facing stages: Ask/Respond, Resolve.*

## MODULE 12 — Pleadings, Motions, Service, and Proposed Relief

*Route tag: original, pending, postjudgment. Sol Module 9 + Opus Module 6.1, 6.6, 6.7, merged.*

**Objectives**
- Distinguish complaint / answer / counterclaim from motion / response. Initial-action basics (Sol §2, gap 2): complaint, summons, answer, counterclaim, default and final-default safeguards, service, proof of service, confidential identifiers, prior-case disclosure, paternity and marriage gatekeeping.
- **Anatomy of a motion:** motion, brief, notice of hearing, proposed order, proof of service.
- Draft **numbered, material facts tied to legal elements**, not narrative.
- Request relief the court can implement (acceptance test 11).
- Attach affidavits and exhibits without argument-by-volume.
- Complete filing, scheduling, service, proof, response, and reply steps; Genesee's praecipe and 9-day service instruction (Module 4.3).
- Amendment, adjournment, and proposed-order issues.
- **MCR 1.109(E) signature and verification — and the sanctions exposure it creates**, MCL 600.2591.

### 12.1 ⚠ WHEN NOT TO FILE (Opus §4.3(c))
Nothing in v1 discouraged over-filing. A high-conflict litigant reading an empowering guide will file too much. The downside must be stated: MCR 3.215(F)(3) sanctions frivolous referee objections; **MCR 3.206(D)(2)(b) lets the *other* party recover fees caused by noncompliance**; MCR 1.109(E)(5)–(7) and MCL 600.2591 sanction frivolous filings; and there is a judicial-patience budget. Repeated emergency motions, overbroad discovery, unsupported "alienation" accusations, and bad-faith contempt create fee exposure and credibility damage (Sol §2, gap 5). Teach a "three motions rule of thumb" and a pre-filing sanity check.

### 12.2 Motions for Reconsideration
MCR 2.119(F), **21 days**; palpable-error standard; the cheap first move before an appeal and a common way to preserve issues. `⚠` (Also Module 27.)

**Templates/tools:** motion architecture worksheet; affidavit fact-quality checklist; relief precision checklist; service and proof matrix; filing packet table of contents; annotated model motion / brief / notice of hearing / proof of service (Appendix D); 10-point rejection checklist.
**Exercises:** convert a narrative into eight numbered material facts; draft an enforceable prayer for relief and **test it against a calendar**; self-assessment — score a draft motion against the 10-point rejection checklist. *Done when the score is 10/10 and a second reader can execute the requested order without asking a question.*
**Glossary:** pleading, motion, response, affidavit, verified pleading, material fact, prayer for relief, default, notice of hearing, caption, reconsideration, sanctions.

## MODULE 13 — Temporary Orders

*Route tag: pending, temporary-order stage. Opus Module 6.2, 6.5.*

**Objectives**
- What a temporary order does and how long it lasts.
- **The ECE consequence** — cross-reference the boxed *Hayes* warning in Module 2.1. This is the module where the trap actually springs.
- How to structure a temporary order that protects the reader's position: interim schedule language, review dates, express non-prejudice language (and its limits — an express recital does not change the *facts* of how the child lives).
- **Your shield: the evidentiary-hearing requirement.** A court may not enter an order changing an established custodial environment without first holding an evidentiary hearing on clear and convincing evidence — MCR 3.210(C)(1) ([MCR 3.210](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-210)). Contested custody hearing within **56 days**; decision within **28 days** after the hearing (MCR 3.210(C)). `⚠` current text unverified pending ADM File 2021-27 (research §12 item 4).

**Templates/tools:** temporary-order clause checklist; ECE-impact declaration; "before you sign" review card (ECE, hearsay waiver, relocation consent, vague language).
**Exercise:** review a sample stipulated temporary order for ECE-creating terms. *Done when the reader can name each term that shifts primary care and state the burden it would later create.*
**Glossary:** temporary order, stipulated order, consent order, established custodial environment, evidentiary hearing.

## MODULE 14 — Emergency and Ex Parte Orders: Getting One and Fighting One

*Route tag: emergency. Sol Module 10 + Opus Module 6.3–6.4 + Gemini's MCR 3.207 addition, merged. All three models flagged v1 as too thin here.*

### 14.1 Getting One
Distinguish ordinary temporary relief from ex parte relief. The heightened standard: **irreparable injury, loss, or damage, or that notice itself will precipitate adverse action**. The **specific-facts affidavit** — source, date, admissibility, immediacy, and nexus to the requested relief; not conclusions. Address ECE and whether the requested relief alters it. Why most are denied and the credibility cost of an unsupported request. Current FOC 137/138 and local requirements `⚠`.

### 14.2 ⚠ Fighting One — the 14-Day Clock
`DEADLINE — ACT TODAY`. **14 days after service** to file an objection or a motion to rescind or modify (MCR 3.207(B)). The FOC then attempts resolution within 14 days and a hearing is set within 21 days of the motion. Form [FOC 61, Objection to Ex Parte Order and Motion to Rescind or Modify](https://www.courts.michigan.gov/496b3f/siteassets/forms/scao-approved/foc61.pdf), with FOC 62 as the modifying order; plain-language walkthrough at [Michigan Legal Help — Ex Parte Orders](https://michiganlegalhelp.org/resources/family/ex-parte-orders-family-court); rule text at [MCR 3.207](https://casetext.com/rule/michigan-court-rules/michigan-court-rules/chapter-3-special-proceedings-and-actions/subchapter-3200-domestic-relations-actions/rule-3207-ex-parte-temporary-and-protective-orders).

> **⚠ VERIFY — RULE IN FLUX.** Amendments to MCR 3.207 and 3.210 have been under consideration in **ADM File 2021-27** ([proposed amendment](https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/proposed-and-recently-adopted-orders-on-admin-matters/proposed-orders/2021-27_2024-09-11_formor_propamdmcr3.207-3.210.pdf)), and Sol cites a **2025 adopted amendment order** together with revised form materials indicating a 14-day service-based objection deadline ([Michigan Supreme Court 2025 amendment order](https://www.courts.michigan.gov/49e151/siteassets/rules-instructions-administrative-orders/proposed-and-recently-adopted-orders-on-admin-matters/adopted-orders/2021-27_2025-06-18_formor_amdmcr3.207-3.210.pdf); [FOC 138](https://www.courts.michigan.gov/498596/siteassets/forms/scao-approved/foc138.pdf)). **The drafting model must confirm the current text and the current form numbers before this module states any number.** Note the two council reports cite different form families (Opus: FOC 61/62; Sol: FOC 137/138 for requesting and FOC 61/61a for responding) — both are recorded here and must be reconciled against the current SCAO form set.

### 14.3 Living Under an Ex Parte Order
**The order remains enforceable until changed.** Objecting does not suspend it. Coordinate with PPO and safety processes without creating conflicting orders. `SAFETY OVERRIDE`.

**Templates/tools:** emergency-facts affidavit worksheet (source / date / admissibility / immediacy / nexus); ECE-impact declaration; FOC 61 / 61a response checklist; 14-day objection calculator; emergency counsel and safety referral card.
**Exercises:** separate urgent facts from old conflict in a scenario; calculate the objection and hearing path from a sample service date. *Done when the reader has a dated filing plan with an official-source citation for each date.*
**Traps:** harmful emergency motion; conflicting orders; assuming the objection stays the order.
**Stop and seek counsel:** any request involving removal of a child, suspension of parenting time, or a criminal or CPS overlay.
**Glossary:** ex parte, irreparable injury, imminent harm, objection, rescind, modify, adverse action.

## MODULE 15 — The Friend of the Court: Investigation, Report, and the Report Paradox

*Route tag: pending, postjudgment. Opus Module 8 + Sol Module 11 (first half), merged.*

### 15.1 What Genesee FOC Does
`ℹ LOCAL PRACTICE`. Investigation, recommendation, enforcement, support administration; what it provides in-house vs. refers out; how to contact FOC for account/enforcement information vs. case-specific questions; FOC **39** Case Questionnaire ([FOC 39](https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc39.pdf)).

### 15.2 Opt In or Opt Out of FOC Services
MCL 552.505a `⚠` full text unverified (research §12 item 2). The legal default (a FOC case opens unless the parties jointly opt out) and what opting out actually costs — loss of a neutral investigator and enforcer. High-conflict-specific tradeoffs. Genesee opt-out packet and opt-in request form ([Genesee County Opt-Out Packet](https://cms7files.revize.com/genessecountymi/Document_Center/Courts%20and%20Law%20Enforcement/Friend%20of%20the%20Court/Online%20Forms/Pro%20Per/Opt%20out%20packet.pdf)).

### 15.3 The Custody / Parenting-Time Investigation
What the investigator does; the interview; what to bring; what never to say; whether the FOC must address ECE — **it is not statutorily required, though a judge may request it** ([MJI, Custody and Parenting Time Investigation Myths](https://www.courts.michigan.gov/4a2436/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/custody-parenting-time-investigation-myths/custody-and-parenting-time-investigation-myths_material.pdf)); [SCAO Custody and Parenting Time Investigation Manual](https://www.courts.michigan.gov/4932e6/siteassets/publications/manuals/foc/cp_investigationmnl.pdf). **Do not hand over the journal wholesale** (Module 8).

### 15.4 ⚠ THE FOC REPORT PARADOX
**Opus §2.1(e) — subtle, consequential, and entirely absent from v1.**

MRE 1101(b)(9) says the rules of evidence do **not** apply to "the court's consideration of a report or recommendation submitted by the friend of the court under MCL 552.505(1)(g) or (h)" ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf)). **But** *Duperon v Duperon*, 175 Mich App 77, 79 (1989), holds the FOC report "is not admissible as evidence unless both parties agree to admit it in evidence," may be used only for background and context, and the court's custody findings "must be based upon competent evidence adduced at the hearing" ([Duperon](https://www.casemine.com/judgement/us/59148af2add7b0493451a3c2); applied in [COA 2002 opinion](http://www.michbar.org/file/opinions/appeals/2002/081602/16034.pdf)).

**Practical rules, stated as three numbered instructions:**
1. **A favorable report does not carry your burden.** Put in your proofs anyway.
2. **Do not stipulate to admission of an unfavorable report.**
3. **You have the right to review the report and file objections before the decision** — MCR 3.210(C)(6) ([MCR 3.210](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-210)).

The same non-admissibility-absent-stipulation rule applies to an **LGAL's written report** under MCL 722.24(3) ([SCAO third-person custody checklist](https://www.courts.michigan.gov/48dbed/siteassets/publications/benchbooks/qrms/family/domestic-relations/child-custody-dispute-involving-third-person-checklist.pdf)).

### 15.5 Objecting to the Recommendation
Grounds; how to write an objection specific enough to work; timing. (Full objection mechanics in Module 16.)

**Templates/tools:** FOC 39 completion audit; FOC interview preparation sheet; report error / omission / source / methodology matrix; draft objection; opt-in vs. opt-out decision worksheet; FOC contact card `ℹ`.
**Exercises:** prepare for the FOC interview using the prep sheet; given a hypothetical report, identify three findings unsupported by competent evidence and the exhibit that rebuts each.
**Glossary:** Friend of the Court, FOC case questionnaire, FOC investigation, FOC enforcement, opt-in, opt-out, recommendation, background and context.

## MODULE 16 — The Referee Hearing, the Objection, and What "De Novo" Really Means

*Route tag: pending, postjudgment, enforcement. **Promoted to a full module.** Opus Module 9 + Sol Module 11 + Gemini's critical addition, merged. All three models found v1's treatment materially misstated.*

### 16.1 What a Referee Hearing Actually Is
> **⚠ THE MICHIGAN RULES OF EVIDENCE APPLY.** MCR 3.215(D)(1) ([MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215)). **Treat it as a trial.** For most Genesee pro se parents, it is the trial.

A record is made electronically or stenographically, and a party may make a contemporaneous copy (MCR 3.215(D)(4)).

### 16.2 Building the Record
Why **everything** must go in here; how to make an offer of proof when evidence is excluded; how to get an objection and a **ruling** on the record; ensuring the proceeding is recorded; ordering transcripts.

### 16.3 The Recommendation
The referee must issue findings and a recommendation within **21 days**; **the recommended order becomes final if no written objection is filed within 21 days after service** (MCR 3.215(E)(1)). Genesee's own custody-motion packet states the recommendation "becomes a court order automatically unless a party files an objection within 21 days after the recommendation was mailed," with blank objection forms at the clerk's office ([Genesee County Custody Motion Packet](https://cms7files.revize.com/genessecountymi/Document_Center/Courts%20and%20Law%20Enforcement/Friend%20of%20the%20Court/Online%20Forms/Pro%20Per/fillable%20Custody%20motion.pdf)). `DEADLINE — ACT TODAY`. **Note the trigger discrepancy — "after service" (rule) vs. "after mailing" (county packet) — and resolve it before publication.** Form [FOC 68](https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc68.pdf); notice language appears on [FOC 60](https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc60.pdf).

### 16.4 ⚠ Writing an Objection That Works
MCR 3.215(E)(4) — the objection "must include a clear and concise statement of the **specific findings or application of law** to which an objection is made." A generic "I object to the whole recommendation" invites the court to treat unobjected findings as conclusive. Template: identify the finding → state why it is wrong → cite the record.

### 16.5 ⚠⚠ WHAT "DE NOVO" REALLY MEANS — AND THE NEW-EVIDENCE BAR
**v1 told the reader the judge "does not defer to the referee's findings but rehears the matter fresh." That is materially misleading, and all three council models said so.**

The judicial hearing must be held within 21 days of the objection. The court **must** allow the parties to present live evidence — but under **MCR 3.215(F)(2)** it may, in its discretion:
- **(a)** prohibit a party from presenting evidence on findings of fact to which **no objection** was filed;
- **(b)** determine that the referee's finding was **conclusive** as to a fact to which no objection was filed;
- **(c)** **prohibit a party from introducing new evidence or calling new witnesses unless there is an adequate showing that the evidence was not available at the referee hearing.**

([MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215); Gemini's supporting citation: [COA opinion applying MCR 3.215(F)(2)(c)](https://www.courts.michigan.gov/siteassets/case-documents/uploads/opinions/final/coa/20100427_c293956_28_293956.opn.pdf).) MCL 552.507 permits a new decision based entirely on the referee record, entirely on new hearing evidence, or on a supplemented record; reasonable restrictions may apply while live evidence remains available as the rule permits ([MCL 552.507](https://legislature.mi.gov/Laws/MCL?objectName=MCL-552-507); [*Butters v Butters*](https://www.courts.michigan.gov/49f1dc/siteassets/case-documents/uploads/opinions/final/coa/20220728_c359665_49_359665.opn.pdf)).

> **⚠ THE FATAL PRO SE STRATEGY: "SAVE YOUR BEST EVIDENCE FOR THE JUDGE."**
> **Do not do this.** Because new evidence can be barred absent a showing of unavailability, the reader who saves it may never get to present it. **Failing to build a record at the referee hearing is often unrecoverable.** Gemini requested an explicit exercise on this: a checklist for ensuring *all* evidence is presented at the referee stage.

If you rely on the referee-hearing record, you must give notice and you pay for the transcript.

### 16.6 ⚠ The Cost of a Bad Objection
MCR 3.215(F)(3) — costs and attorney fees if the objection is found frivolous or filed to delay. v1's tone encouraged objecting as a default posture with no counterweight.

### 16.7 Interim Effect
MCR 3.215(G) limits on giving a recommendation interim effect by administrative order — notably **not** for orders changing custody or domicile.

**Templates/tools:** referee-hearing proof plan; **"everything in now" completeness checklist** (Gemini); finding-by-finding objection worksheet; FOC 68 drafting aid with worked example; 21-day deadline calculator; transcript and record-preservation checklist; objection/ruling/offer-of-proof log.
**Exercises:** draft three specific objections to findings and to applications of law with record cites (*done when each objection names the finding, the reason, and the record page*); prepare a five-minute referee presentation with exhibit references; red-flag spotting — three defective objections and why each fails.
**Glossary:** referee, recommendation for an order, de novo hearing, de novo review, specific objection, interim order, transcript, conclusive finding, offer of proof.

## MODULE 17 — CPS, Police, PPO, False Allegations, and the Parallel-Proceeding Firewall

*Route tag: emergency, all. **`DO NOT USE THIS GUIDE ALONE`.** Opus Module 12 + Sol Module 13 + v1 §4.3/4.4, merged and substantially expanded.*

### 17.1 The First 24 Hours
Do not contact the accuser. **Do not talk to police without counsel — this is a hard stop; consult a criminal attorney.** Preserve everything. Continue to comply with every existing order.

### 17.2 ⚠ THE PARALLEL-PROCEEDING FIREWALL (Sol §2)
v1 treated a false accusation mostly as a rebuttal worksheet, which **invites self-incrimination**. The firewall, as a numbered protocol:
1. Preserve records; **do not alter, delete, or fabricate**.
2. Do not contact or intimidate the accuser or collateral witnesses.
3. **Do not interrogate the child or seek a recantation.**
4. Obey PPO, bond, no-contact, school, and custody orders **even if believed false**.
5. Separate the family-court response from the CPS administrative response and from criminal defense. They are different tracks with different rules and different consequences for what you say.
6. Avoid broad written narratives before obtaining advice where criminal exposure exists.
7. Request particulars and use formal process — **not social-media rebuttal**.
8. Distinguish "unsubstantiated" from an affirmative finding that an allegation was **knowingly false**. These are not the same and conflating them overstates the evidence.
9. Use neutral language in court.

### 17.3 How a CPS Investigation Works
CPS classifies investigations into **five categories** under MCL 722.628d. Categories I–III mean a preponderance finding of abuse or neglect. **Category V means the referral was based on false or erroneous information** ([MDHHS CPS investigation process](https://www.michigan.gov/mdhhs/adult-child-serv/abuse-neglect/childrens/report-process/investigation-process-and-results/childrens-protective-services-investigation-process); [MDHHS PSM 713-01](https://mdhhs-pres-prod.michigan.gov/olmweb/EX/PS/Public/PSM/713-01.pdf)). **A Category V finding is a document a falsely accused parent should obtain and use.** v1's false-allegations module never mentioned that the categorization exists.

### 17.4 Records, Confidentiality, and Central Registry
CPS records are confidential and access is controlled ([MDHHS Central Registry Clearance Requests](https://www.michigan.gov/mdhhs/adult-child-serv/abuse-neglect/accordion/forms/central-registry-clearance-requests)). A CPS disposition is **not** automatically the family court's custody finding. A person placed on the Central Registry has notice, record-review, expungement-request, and administrative-hearing rights ([MDHHS Central Registry](https://www.michigan.gov/mdhhs/adult-child-serv/abuse-neglect/childrens/investigation/results/central-registry)); MDHHS must hold a hearing to determine by a preponderance whether a record should be amended or expunged under MCL 722.627j(9) ([Child Protective Proceedings Benchbook](https://www.courts.michigan.gov/49bf88/siteassets/publications/benchbooks/cpp/cpp.pdf)). How to request your determination letter; how to get CPS records into the custody case (Module 10.5 subpoena route).

### 17.5 ⚠ SERIAL FALSE REPORTS — A CONCRETE, CITABLE REMEDY (Opus §2.8)
CPS **must** notify the local FOC office when there is an open FOC case and the investigation produces a preponderance finding, an emergency removal, court jurisdiction, or other safety-jeopardizing circumstances — and CPS **may** notify the FOC when a parent has made **three unfounded child abuse reports** ([SCAO FOCB memorandum on mandated reporters](https://www.courts.michigan.gov/4a8510/siteassets/court-administration/focb-memoranda/2012/mandatedreporters.pdf)). For a parent facing serial false referrals from a high-conflict ex, this is a concrete remedy v1 did not contain. How to raise the pattern under best-interest factor (j).

### 17.6 Domestic Violence and PPOs
MCL 722.23(k) — domestic violence "regardless of whether the violence was directed against or witnessed by the child." MCL 722.27a(7)(c)–(d) (likelihood of abuse of the child; likelihood of abuse of a parent). **The DV-shelter protection**: a custodial parent's temporary residence with the child in a DV shelter is **not** evidence of intent to conceal — MCL 722.27a(7)(h) ([MCL 722.27a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27a)) — stated explicitly for a reader who fled and fears it will be used against them. Domestic-relationship PPO process, Form [CC 375](https://www.courts.michigan.gov/siteassets/forms/scao-approved/cc375.pdf); YWCA Greater Flint on-site filing help `ℹ`. **A PPO takes precedence over any existing custody or parenting-time order until it expires or the custody court modifies its order to accommodate it** ([MJI Domestic Violence Benchbook, Ch. 5](https://www.courts.michigan.gov/siteassets/publications/benchbooks/dvbb/dvbbresponsivehtml5.zip/DVBB/Ch_5_Special_Orders/Issuing_a_PPO_in_Domestic_Relations_Proceedings.htm)); MCL 600.2950(1)(l) authorizes a PPO to affect custody or parenting time **without** a separate MCL 722.23 best-interest analysis at the issuance stage ([MJI DVBB Ch. 8](https://www.courts.michigan.gov/siteassets/publications/benchbooks/dvbb/dvbbresponsivehtml5.zip/DVBB/Ch_8_Effects/Effect_of_Domestic_Abuse_on_Child_Custody_Determinations.htm)). Safe service and safe exchange options; DV advocates. `SAFETY OVERRIDE`.

### 17.7 Factor (j)'s Protective-Action Carve-Out — Cutting Both Ways
It protects a parent who took reasonable protective action against domestic violence or sexual assault; it does not excuse a parent who fabricates allegations. Teach both directions.

### 17.8 Rebuilding Credibility
Supervised parenting time as a bridge; voluntary evaluations and their risks; **how not to over-argue innocence in family court**.

### 17.9 Scope Boundary
This module does **not** cover defending an abuse/neglect petition, a criminal charge, or a PPO respondent case. Hire counsel. (`custody_guide_plan.md` §4.)

**Templates/tools:** parallel-proceeding map; allegation / evidence / order / counsel-action chronology; **"do not contact / do not post / do not delete" card**; CPS document and deadline log; determination-letter request; Central Registry expungement checklist; DV/PPO evidence organization worksheet (incident, date, evidence type, reported y/n, factor (k) relevance); safety plan and order-conflict audit; PPO filing preparation checklist.
**Exercises:** classify which facts belong in which proceeding; rewrite a defensive accusation response as a concise, preservation-focused court statement. *Done when the rewritten statement contains no characterization of the accuser's motives and no admission beyond what the record already contains.*
**Glossary:** substantiated, unsubstantiated, Category V, Central Registry, expungement, PPO, domestic-relationship PPO, ex parte PPO, no-contact order, parallel proceeding, protective-action carve-out, false allegation.

## MODULE 18 — Interference, Resistance, and "Parental Alienation" Claims

*Route tag: all. Opus Module 13 + Sol Module 8 + v1 Lesson 5, reframed away from syndrome-pleading.*

### 18.1 ⚠ Frame It as Conduct, Not a Diagnosis
**Michigan has no "parental alienation" cause of action.** No standalone published Michigan appellate doctrine was located (`custody_guide_research.md` §12 item 9). The conduct is relevant through **MCL 722.23(j)** (willingness to facilitate a close relationship with the other parent) and **MCL 722.27a(7)(f)–(g)** (whether a parent can be expected to comply; whether a parent has frequently failed to exercise parenting time). **Plead specific acts; let the court name the pattern.** A pro se parent who opens by telling a judge "this is parental alienation" is heard as **the high-conflict party**. Banned vocabulary per §0.5.

### 18.2 Distinguish, Don't Label
Interference vs. justified safety action vs. ordinary conflict vs. developmental resistance vs. unknown cause. **Calling all resistance "alienation" can obscure abuse, a developmental need, or a child's independent experience.** Non-diagnostic child-resistance differential checklist.

### 18.3 The Interference Inventory
Denied exchanges; blocked calls; withheld school and medical information; unilateral schedule changes; disparagement; scheduling activities during your time; refusing to add you as an emergency contact; the "child refuses to come" pattern.

### 18.4 Proving It — Every Row With an Admissibility Route
School and medical records under MRE 803(6) plus attendance and pickup logs; **the other parent's own messages under MRE 801(d)(2)**; third-party exchange witnesses; provider testimony; the exchange log; neutral third-party evidence over party testimony wherever possible.

### 18.5 ⚠ The Child's Statements
Cross-reference Module 6 — **MRE 803A does not apply here.** The legitimate routes and their limits. Reasonable preference (factor (i)) vs. improper influence. **No exercise in this book asks the reader to interview, recruit, coach, diagnose, or emotionally rely on the child** (acceptance test 8).

### 18.6 Your Own Facilitation Audit
Courts scrutinize **both** parents on factor (j). A self-audit worksheet: am I doing something that could look like interference?

### 18.7 Remedies Realistically Available
Make-up and compensatory time; contempt; parenting coordinator; therapy orders; specific order-term amendments (which are often more useful than a custody change); change in legal custody; and — rarely — a custody change. **What courts actually grant.**

### 18.8 Experts and Their Limits
MRE 702/703; the field is contested; **reunification-therapy and PAS-based expert testimony draws MRE 702 challenges**; a retained alienation expert is expensive and can be neutralized on cross. **An LGAL request is usually the better and cheaper move** (Module 19).

**Templates/tools:** conduct → order term → factor → evidence → **alternative explanation** matrix; missed-contact/interference log (a specialized variant of the Module 8 journal, tagged to factor (j)); facilitation self-audit; child-resistance differential checklist (expressly non-diagnostic); "what not to do" checklist on involving the child.
**Exercises:** rewrite ten "alienation" labels as specific, dated conduct (*done when no entry contains a characterization or a clinical term*); identify what evidence would test each competing explanation; map ten co-parent behaviors to the factor(s) they may support, noting where a behavior is not clearly factor-relevant.
**Glossary:** facilitation, interference, protective action, reasonable preference, alternative explanation, coaching, triangulation, parentification (descriptive, not a Michigan legal term), published vs. unpublished opinion, persuasive vs. binding authority.

**Teaching note on unpublished authority:** *Grew v Knox* and similar unpublished opinions are persuasive only under MCR 7.215(C)(1) and must be labeled as such if used at all (`custody_guide_research.md` §12 item 8).

## MODULE 19 — GAL, LGAL, FOC Investigator, Evaluator, and Experts

*Route tag: pending, postjudgment. Opus Module 13.5–13.7 + Sol Module 12, merged. v1 conflated four legally distinct actors.*

### 19.1 The Roles, Side by Side
| Role | Who they are | Duty runs to | Report's evidentiary status |
|---|---|---|---|
| **LGAL** | An attorney appointed for the child | The child's **best interests** | **Not admissible unless all parties stipulate** — MCL 722.24(3) ([SCAO checklist](https://www.courts.michigan.gov/48dbed/siteassets/publications/benchbooks/qrms/family/domestic-relations/child-custody-dispute-involving-third-person-checklist.pdf)) |
| **GAL** | An individual appointed to assist the court; **need not be a lawyer** | The court | Depends on the appointment; **hearsay in a GAL report may remain inadmissible over proper objection** ([MJI summary of *Kuebler v Kuebler*](https://www.courts.michigan.gov/49add7/siteassets/publications/impact/written/family/impact-e-mail-5-22-23-family.pdf)) |
| **Attorney for the child** | The child's lawyer | The child's **expressed preference** | N/A |
| **FOC investigator** | A court-office function | The court | See the FOC report paradox, Module 15.4 |
| **Custody / psychological evaluator** | Court-appointed or party-retained expert | Their engagement | Hearsay; admission governed by the appointment order and MRE 702/703 |
| **Treating therapist** | A treating professional, **not a custody evaluator** | The patient | Privilege issues; role confusion is a common error |
| **Child-protective LGAL** | Mandatory framework in a **separate** proceeding under MCL 712A | The child | **Do not conflate with the custody-case LGAL** ([MJI CPP Benchbook, LGAL chapter](https://www.courts.michigan.gov/4a26a2/siteassets/publications/benchbooks/cpp/cppresponsivehtml5.zip/CPP/Ch_7_Preliminary_Steps/Lawyer-Guardian_Ad_Litem_L-GAL-.htm)) |

Statutory basis: [Child Custody Act](https://www.legislature.mi.gov/documents/mcl/pdf/mcl-act-91-of-1970.pdf); [MCL 722.24](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-24) authorizes a **discretionary** custody-case LGAL and bars admission of the LGAL report absent all-party stipulation.

### 19.2 Which Appointment Solves Which Problem — and Who Pays
**For most pro se alienation cases, an LGAL request is the highest-leverage motion available**, because it creates an independent voice the court will actually listen to. It also costs money and **can backfire**. Teach both. Respond to appointment scope and cost.

### 19.3 ⚠ BEFORE YOU SIGN THE EVALUATION ORDER — THE HEARSAY-WAIVER TRAP
**Opus §2.1(f).** A Michigan appellate panel held a mother waived hearsay objections to an evaluator's report where **the appointment order itself provided that the parties waived hearsay objections**, she submitted to the evaluation, and she did not object at admission ([State Bar e-Journal summary](https://www.michbar.org/opinions/content_search_detail/EJournalNumber/86190)). **A pro se parent will sign a stipulated evaluation order without reading this clause.** Teach the reader to read the appointment order for a waiver clause before signing, and to negotiate: scope, who pays, collateral contacts, access to raw data and underlying material, and deposition rights.

### 19.4 Participating in an Evaluation
Honestly, without advocacy theater or document dumping. **Do not send the whole journal** (Module 8). Selective, inflammatory, privileged, or child-generated material can backfire. What topics an evaluator typically explores.

### 19.5 Challenging a Report
**MCR 3.219 — "Dissemination of a Professional Report" — VERIFIED** from the archived primary text. Where a custody, visitation, or change-of-domicile dispute exists and the court uses a community resource, the court must ensure the written findings and recommendations go to the FOC and to the attorneys, **or to the parties if unrepresented**, and "[t]he attorneys for the parties, or the parties if they are not represented by counsel, **may file objections to the report before a decision is made**." **Correction:** research §12 item 4 and earlier drafts described MCR 3.219 as governing FOC "file access." It does not. **FOC records access is MCR 3.218** — and note **MCR 3.218(A): "Friend of the court records are not subject to a subpoena issued under these Michigan Court Rules."** See also [MJI training on custody and parenting-time reports](https://www.courts.michigan.gov/4a7d51/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2023-2024/what-jurists-look-for-in-custody-and-parenting-time-reports/mjifocb_decoster-and-martinez-august-2024_material.pdf). Evaluate neutrality, scope, data sources, collateral contacts, testing limits, fees, and report access. Test methodology; subpoena and cross-examine where permitted; present contrary evidence. **The court retains independent decision responsibility and is not bound by an evaluator's or LGAL's recommendation** (*McIntosh v McIntosh*, research §4.8).

**Templates/tools:** role comparison chart (above); appointment-scope and fee worksheet; **appointment-order review card with the hearsay-waiver clause at the top**; evaluation participation checklist; report error/omission/source/methodology matrix; expert qualification and opinion-foundation checklist; motion/request drafting aid for an LGAL appointment.
**Exercises:** identify the correct role for five scenarios; prepare cross-examination topics from a sample report **without attacking the professional personally**. *Done when every topic points to a data gap, a methodology limit, or an unverified source rather than to the evaluator's character.*
**Glossary:** GAL, LGAL, attorney for the child, FOC investigator, custody evaluator, expert witness, methodology, collateral source, appointment order, hearsay waiver, stipulation.

## MODULE 20 — Negotiation, Mediation, and Settlement

*Route tag: pending, postjudgment. Sol Module 14 + Opus Module 14 + v1 §3.1, merged and compressed.*

**Objectives**
- Distinguish **FOC domestic-relations mediation (MCR 3.224)** from **general court-rule mediation (MCR 3.216)**, including confidentiality rules and the DV screening / written-consent requirement under MCR 3.224.
- Genesee: the CDRP center is the **Community Resolution Center**, Flint, MI — (989) 799-5949, mediation-crc.org; also reachable through MI-Resolve ([Michigan ODR CDRP center list](https://www.courts.michigan.gov/4aaccd/siteassets/offices/odr/cdrp-centers-(list-only).pdf); [2024 CDRP Annual Report](https://www.courts.michigan.gov/4aa1ab/siteassets/reports/cdrp-annual-reports/2024-cdrp-annual-report.pdf)). `ℹ` **Do not confuse it with the similarly named center serving Genesee County, New York.**
- **Screen coercion, DV, power imbalance, and safety.** How to raise safety concerns; shuttle/caucus mediation; when to decline. `SAFETY OVERRIDE`.
- Prepare issue-by-issue proposals with fallback positions, organized around the evidence matrix.
- **Authority to settle; on-record settlements; voluntariness; review before assent** (Sol §2, gap 6).
- Test enforceability, calendar operation, support and tax consequences, and information-sharing terms.
- Understand when and how an agreement becomes binding and then an order.

### 20.1 ⚠ Reading a Proposed Consent Order Before You Sign
The four things that most often cause irreversible harm at this step: **ECE implications** (Module 2.1); **hearsay waivers** (Module 19.3); **open-ended relocation consent** (Module 27); **vague language that becomes unenforceable** (Module 25). Plus: who drafts, and entry mechanics.

**Templates/tools:** mediation suitability and safety screen; mediation position statement tied to the evidence matrix; **settlement term sheet** covering custody, schedule, holidays, exchanges, decision-making, information access, support, tax, fees, dispute resolution, and effective date; **ambiguity stress test**; "before you sign" card.
**Exercises:** calendar-test a proposed schedule across one full school year including holidays and breaks (*done when no date is claimed by both parents and no gap is unassigned*); identify missing terms in a sample on-record agreement; red-flag spotting for DV safety precautions.
**Glossary:** mediation, MCR 3.216, MCR 3.224, caucus, confidentiality (mediation), term sheet, mediated settlement agreement, consent order, memorialize, coercion, Community Dispute Resolution Program.

---

# PART IV — PREPARE AND PRESENT THE ADJUDICATED CASE (TRY THE CASE)
*Reader-facing stage: Try.*

## MODULE 21 — Pretrial Management and the Deadline Tracker

*Route tag: pending, postjudgment. Sol Module 15 + Opus Module 15.1 + **Gemini's Master Pretrial Deadline Tracker**, merged.*

> ### 📋 MASTER PRETRIAL DEADLINE TRACKER — STANDALONE VISUAL, FIRST PAGE OF THIS MODULE
> **Gemini §3** asked that this be elevated to a standalone visual checklist at the start of the pretrial phase: "a stressed pro se litigant needs a consolidated timeline," not deadlines distributed across modules. It consolidates praecipe filing, motion filing and response, service, discovery cutoff, witness and exhibit exchange, motions in limine, trial brief, courtesy copies, and objection deadlines into one page keyed to the scheduling order and the assigned judge's policies. It is a **local-practice-flagged duplicate** of the relevant rows in Appendix A, not a substitute for it (acceptance test 12: the authoritative version lives in the change-controlled appendix).

**Objectives**
- Extract every date from the scheduling order: discovery cutoff, motion deadlines, witness and exhibit list deadlines, motions in limine, trial brief, pretrial conference, trial.
- Narrow facts and exhibits through **stipulations**; document a stipulation properly.
- Disclose witnesses and exhibits in the required form and on time.
- Resolve evidentiary issues before trial where appropriate (**motions in limine**) — note Judge Hood's published policy requires motions in limine filed and heard at least 3 weeks before trial, illustrating that judge-specific deadlines control `ℹ`.
- **Plan subpoenas early enough for service and witness availability** — recall the MCR 2.506(C)(1) 14-day document-subpoena rule and the MCR 2.305(A)(1) motion requirement (Module 10.4).
- MCR 3.210(C) timing: contested custody hearing within **56 days**; decision within **28 days** after the hearing. `⚠`

**Templates/tools:** scheduling-order extraction sheet; the Master Pretrial Deadline Tracker; witness list and exhibit list templates (blank + worked); stipulation drafting aid; motion-in-limine issue spotter; **trial brief skeleton organized as standard → evidence → finding → relief**.
**Exercises:** build a 60-day pretrial calendar from a hypothetical scheduling order; map each witness and exhibit to a disputed element and the **expected objection**. *Done when every exhibit row shows its foundation rule and every witness row shows the element they prove.*
**Glossary:** scheduling order, discovery cutoff, stipulation, witness list, exhibit list, motion in limine, trial brief, pretrial conference.

## MODULE 22 — Witnesses, Objections, Exhibits, and the Record

*Route tag: pending, postjudgment, enforcement. Sol Module 16 + Opus Module 15.2–15.6, 15.8, merged.*

**Objectives**
- **Who is credible to a family judge** — teachers, doctors, coaches, neighbors, providers — and who is not, standing alone: your mother, your new partner, your best friend.
- Subpoena them (Module 10.4); prepare them **without coaching**.
- Nonleading direct examination; controlled, short, one-fact-per-question cross-examination; when to stop; not arguing with the witness.
- **Direct examination of yourself:** narrative structure; using MRE 612 to refresh from your journal; not editorializing; testifying as both party and witness.
- Refresh recollection and use prior inconsistent statements correctly.
- **Getting exhibits in:** live execution of the Module 7 foundation scripts; the exhibit admission sequence; numbering, pre-marking, copies for the court, witness, and opponent; stipulations to admissibility.
- **The six objections you will make and the six you will hear**, with responses. Concise objections; no speaking objections.
- **⚠ Preserving error:** object → state grounds → make an **offer of proof** → **get a ruling on the record**. Without it there is nothing to appeal (Module 28). Ensure the proceeding is recorded; obtain transcripts.

**Templates/tools:** witness proof outline; direct/cross question planner; exhibit admission sequence card; objection / ruling / offer-of-proof log; witness preparation worksheet (topics, expected questions, demeanor do's and don'ts).
**Exercises:** conduct a mock exhibit foundation; revise argumentative questions into admissible form; practice script — a five-minute direct examination of yourself, timed. *Done when the reader completes a foundation and secures a ruling without notes.*
**Glossary:** direct examination, cross-examination, leading question, impeachment, refreshing recollection, prior inconsistent statement, objection, ruling, offer of proof, transcript.

## MODULE 23 — The Hearing and the Bench Trial

*Route tag: pending, postjudgment. Sol Module 17 + Opus Module 15.1, 15.7, merged.*

**Objectives**
- The structure: opening statement, proofs, rebuttal, closing argument, findings, decision.
- Present a theory of the case **without labels and without cumulative evidence**.
- Integrate the best-interest findings, the ECE and burden analysis, parenting time, support, and precise relief.
- **Ask for findings on each contested factor** — the court must make findings on each best-interest factor — and preserve issues.
- Structure the closing **factor by factor**, citing **admitted evidence** rather than allegations.
- Present income and expense evidence supporting the requested support outcome (Module 24).
- Courtroom decorum for a self-represented litigant (Module 4.6).

**Templates/tools:** hearing-day run sheet; opening and closing outlines; factor-by-factor proof chart; requested-findings and proposed-relief sheet; trial-day logistics checklist (copies for court/opposing party/witnesses, exhibit list, witness list, trial brief, arrival time, attire, what to bring vs. leave outside); **complete trial notebook** assembly guide.
**Exercises:** deliver a three-minute opening; build a closing that cites only admitted evidence. *Done when every assertion in the closing maps to an admitted exhibit or sworn testimony.*
**Glossary:** bench trial, opening statement, proofs, rebuttal, closing argument, finding of fact, conclusion of law, requested findings.

---

# PART V — ORDERS, MONEY, ENFORCEMENT, CHANGE, AND REVIEW
*Reader-facing stages: Enforce/Change, Review.*

## MODULE 24 — Child Support, Tax Benefits, Child Care, Health Care, and Attorney Fees

*Route tag: all. Sol Module 18 + Opus Module 5 and 16.4 + Gemini's MCSF correction, merged.*

### 24.1 The Michigan Child Support Formula
MCL 552.605 requires support in conformity with the MCSF unless the formula amount is unjust or inappropriate under **specific written findings** ([MCL 552.605](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-605)). Core steps from the [2025 Michigan Child Support Formula Manual](https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf): determine each parent's net income (including imputation; the Low Income Threshold concept); combine into monthly family income; derive base support; apply the **Parental Time Offset (§3.03)** based on annual overnights `⚠ verify current brackets`; medical/health-care obligation and Ordinary Medical Expense (§3.04); child care (§3.06). **The parenting-time schedule the reader is negotiating directly affects the support calculation.** MiChildSupport calculator as a planning tool only, not a guarantee `ℹ verify current URL`.

### 24.2 Proving the Other Parent's Income
Documents to demand (Module 10); imputation for voluntary unemployment or underemployment; the self-employed and cash-income problem; **what the FOC will and will not dig for**; red-flag spotting in pay stubs and bank statements.

### 24.3 ⚠ DEVIATION — THE 18 FACTORS OF MCSF §1.04(E), VERBATIM
**Verified in this pass directly from the 2025 manual PDF.** Gemini's count of **18** (reduced from 20 in prior manuals) is **confirmed**; this resolves flagged item 5 in `custody_guide_research.md` §12 and supersedes any secondary source stating 20. The 2025 manual also clarified that **a deviation is not mandatory even where a factor exists**, and **the list is not exhaustive**.

Source, verbatim: [2025 Michigan Child Support Formula Manual, §1.04(E)](https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf), verified August 9, 2026.

1. The child has special needs.
2. The child has extraordinary educational expenses.
3. A parent is a minor.
4. The child's residence income is below the threshold to qualify for public assistance, and at least one parent has sufficient income to pay additional support that will raise the child's standard of living above the public assistance threshold.
5. A parent has a reduction in the income available to support a child due to extraordinary levels of jointly accumulated debt.
6. The court awards property in lieu of support for the benefit of the child (§4.04).
7. A parent has incurred, or is likely to incur, extraordinary medical expenses for either that parent or a dependent.
8. A parent receives bonus income in varying amounts or at irregular intervals.
9. A parent provides substantially all the support for stepchildren or another child for whom the parent is legally responsible, and the child(ren)'s parents are unable to earn income or are otherwise unable to support the child(ren).
10. A child earns an extraordinary income.
11. The court orders a parent to pay taxes, mortgage installments, home insurance premiums, telephone or utility bills, etc., before entry of a final judgment or order.
12. A parent makes payments to a bankruptcy plan or has debt discharged, when neither significantly impacts the monies that parent has available to pay support.
13. A parent provides a substantial amount of a child's day-time care and directly contributes toward a significantly greater share of the child's costs than those reflected by the overnights used to calculate the offset for parental time.
14. A child in the custody of a nonparent-recipient spends a significant number of overnights with the payer that causes savings in the nonparent-custodian's expenses, or an increase in the payer's expenses. When deviating, the court may use the parental time offset and set the nonparent custodian's income as zero.
15. The court ordered nonmodifiable spousal support paid between the parents before October 2004.
16. When a parent's share of child care expenses, under §3.06, exceeds 50 percent of that parent's base support obligation calculated under §3.02.
17. When the amount calculated, as defined in §3.01(A), does not exceed $20, and the administrative cost to enforce and process payments outweighs the benefit of the minimal amounts.
18. Any other factor the court deems relevant to the best interests of a child.

**How to request a deviation on the record:** identify the factor, put in evidence supporting it, and ask the court for the **specific written findings** MCL 552.605 requires. (These 18 factors are reproduced again as Appendix I so the reader can work from a single page.)

### 24.4 Modification, Review, Retroactivity, and Arrears
The FOC review cycle; the change-of-circumstances threshold for support; retroactivity limits; surcharge and arrearage machinery; enforcement running **against** the reader as well as by them.

### 24.5 ⚠ Tax Dependency and Child-Related Credits
Michigan courts have general authority to allocate the federal dependency exemption (*Fear v Rogers*, 207 Mich App 642, 645 (1994), discussed at [Kershaw Vititoe & Jedinak](https://www.monroecountylawyers.com/blog/2019/10/who-gets-to-claim-the-tax-exemptions-for-minor-children-in-michigan/)), and Michigan appellate authority treats the allocation as **part of child support** (*Onyejekwulum v Onyejekwulum*, [opinion PDF](https://www.courts.michigan.gov/siteassets/case-documents/uploads/OPINIONS/FINAL/COA/20230316_C361167_33_361167.OPN.PDF)). **But federal law controls execution:** the noncustodial parent must attach a signed **Form 8332** or a substantially similar document, regardless of what the state order says ([IRS Form 8332](https://www.irs.gov/pub/irs-pdf/f8332.pdf); [IRS Dependents FAQ](https://www.irs.gov/faqs/filing-requirements-status-dependents/dependents/dependents-7)).

> **⚠ FORM 8332 DOES NOT TRANSFER EVERYTHING.** It does **not** transfer head-of-household filing status, the Earned Income Tax Credit, the child and dependent care credit, or the dependent-care exclusion ([IRS Dependents FAQ](https://www.irs.gov/faqs/filing-requirements-status-dependents/dependents/dependents-3); [Michigan Legal Help](https://michiganlegalhelp.org/resources/income-tax/am-i-eligible-child-tax-credit)). **A judgment provision that merely says "Father claims the child" is operationally incomplete.** Drafting tip: build the Form 8332 **execution obligation** into the judgment, plus a conditioning clause tied to support compliance.

### 24.6 Attorney Fees, Costs, and Sanctions — Four Different Things
Distinguish **fee waiver** (Module 4.5) from an **attorney-fee request against the other party**, from **taxable costs**, from **sanctions**, and from evaluator, LGAL, and transcript costs.

**MCR 3.206(D) provides two independent routes:** (1) the moving party is unable to bear the expense of the action and the other party is able to pay; and (2) **the fees were incurred because the other party refused to comply with a previous order despite having the ability to comply.** Requests must be supported by actual evidence, not "unsubstantiated assertions" ([Michigan Court of Appeals 2026 opinion](https://www.michbar.org/Portals/0/opinions/appeals/2026/030926/85341.pdf); [State Bar e-Journal](https://www.michbar.org/opinions/content_search_detail/EJournalNumber/86151/P/LDS); [Michigan Bar Journal background](https://www.michbar.org/file/barjournal/article/documents/pdf4article883.pdf); [SCAO Divorce Proceeding Checklist quoting MCR 3.206(D)](https://www.courts.michigan.gov/4ab2c2/siteassets/publications/benchbooks/qrms/family/domestic-relations/divorce-checklist.pdf); see also MCL 552.13(1)).

> **⚠ THE MCR 3.206(D)(2)(b) FEE TACTIC (Opus §2.6).** Handle two nuances honestly: a **pro se party generally cannot recover a fee for their own time** — there is no fee to shift. **But route (2) is precisely designed for the reader's situation** — an opposing party who violates orders — and **a fee award can fund limited-scope counsel for the next stage.** That reframes a rule the reader would assume is "not for me" into a live tactic. It also runs in the other direction: the same rule lets the *other* party recover fees caused by **the reader's** noncompliance (Module 12.1).

**Templates/tools:** income documentation checklist; income / source / verification matrix; support-input audit; support estimate worksheet with a worked numeric example; **deviation findings worksheet keyed to the 18 factors**; Form 8332 / order-coordination checklist; **MCR 3.206(D) fee-request evidence worksheet** (need and ability, or noncompliance nexus, with invoices and reasonableness).
**Exercises:** audit a fictional support calculation for missing inputs; identify which tax benefits do and do not transfer with Form 8332; red-flag spotting for hidden or underreported income. *Done when the reader can name the input, the document that proves it, and the person who would authenticate it.*
**Glossary:** MCSF, net income, imputed income, Low Income Threshold, parental time offset, deviation, ordinary medical expense, uninsured health care expense, retroactivity, arrearage, surcharge, Form 8332, dependency exemption, head of household, attorney fees, taxable costs, sanctions, MiChildSupport calculator.

## MODULE 25 — Drafting and Entering a Workable Order

*Route tag: pending, postjudgment. Sol Module 19 + Opus Module 16, merged.*

**Objectives**
- Who drafts; the **seven-day rule / settle-order practice**; objections to entry of a proposed order.
- **Specificity as self-defense.** Include: legal custody; physical custody; the parenting-time schedule with exact times and locations; transportation and exchange location; holiday and school-break tables; summer; virtual contact; **right of first refusal**; decision-making allocation and a deadlock-breaking mechanism; information access (school, medical, extracurricular, emergency contact); health care and insurance; support per FOC 10 ([FOC 10 Uniform Child Support Order](https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc10.pdf)); **the dependency-exemption clause and a Form 8332 execution obligation**; communication protocol and platform; travel and passports; medication; extracurriculars; **relocation and change-of-address notice**; safety exceptions.
- **Avoid vague "reasonable parenting time"** where conflict makes it unenforceable.
- Reconcile PPO, no-contact, and confidentiality provisions so the orders do not conflict.
- Complete required FOC and order-information forms.
- The court must make findings on each best-interest factor; decision within 28 days of a contested custody hearing (MCR 3.210(C)(3)). `⚠`

**Templates/tools:** comprehensive order-clause checklist; **Order-Clause Library** (Appendix E) with alternatives and tradeoffs; holiday/calendar conflict test; ambiguity and enforcement audit; proposed-order comparison and redline table; model order language for a co-parenting communication platform — presented as a **generic vendor template**, not a Genesee-specific order, absent confirmation that local judges use a standard one ([OurFamilyWizard model order language](https://www.ourfamilywizard.com/practitioners/model-order-language); [full model order template](https://www.ourfamilywizard.com/sites/default/files/inline-files/us-modelordertemplate-ofw.pdf)) — with the caution that **treating a co-parenting app as inherently court-favored is unsupported**; access, cost, disability, safety, and order language all matter.
**Exercises:** find ten enforcement defects in a sample order; convert three vague provisions into date/time/location-specific language. *Done when a stranger could execute the order without asking a question (acceptance test 11).*
**Glossary:** proposed order, entry, seven-day rule, settle order, uniform child support order, operative provision, ambiguity, right of first refusal, deadlock provision.

## MODULE 26 — Parenting-Time Enforcement, Contempt, and Make-Up Time

*Route tag: enforcement. **The tool this reader will use most.** Opus Module 10 + Sol Module 20 + Gemini's addition, merged. v1 compressed this into a bullet.*

Opus §1.2, Failure 4: "In lived practice, a parent facing alienation spends far more time on denied exchanges than on trial."

### 26.1 First: Is the Order Actually Enforceable?
Confirm the existing order contains a specific, enforceable provision. **Filing contempt on a vague order may fail; the better first objective may be clarification or modification** (Sol §4).

### 26.2 Two Doors
FOC complaint vs. the reader's own motion to show cause. Trade-offs: cost, speed, control, and safety. Also available: documentation only; direct resolution; motion to clarify; motion to enforce.

### 26.3 The FOC Route
File a **written parenting-time complaint** ([MCL 552.511b](https://law.justia.com/codes/michigan/chapter-552/statute-act-294-of-1982/section-552-511b/); [MDHHS, get parenting time](https://www.michigan.gov/mdhhs/adult-child-serv/child-sup/how-do-i/get-parenting-time)). On a written complaint the FOC must apply the make-up parenting-time policy, commence civil contempt proceedings, or move to modify ([MCL 552.641](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-641)); FOC 16 notice ([SCAO/FOCB memo 2025-02](https://www.courts.michigan.gov/4a4d85/siteassets/court-administration/focb-memoranda/2025/2025-02.pdf)). **⚠ The FOC may decline a complaint when the alleged violation is more than 56 days old.** Genesee accepts complaints through its own form process or MiChildSupport ([Genesee FOC online forms](https://www.geneseecountymi.gov/courts_and_law_enforcement/friend_of_the_court/online_forms.php); [Genesee FOC FAQ](https://www.geneseecountymi.gov/courts_and_law_enforcement/friend_of_the_court/frequently_asked_questions.php)). `ℹ`

### 26.4 Make-Up Parenting Time — the Details That Give You Leverage
MCL 552.642 requires each circuit to maintain a make-up policy. The specifics a reader can use:
- Make-up time must be of the **same type and duration** as the time denied.
- It must be taken **within one year**.
- **The denied parent chooses when.**
- **One week's notice** for weekend or weekday time; **28 days' notice** for holiday or summer time.
- The other parent has **21 days to respond** to the FOC notice, and **failure to respond is treated as agreement**.

([MCL 552.642](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-642); [SCAO/FOCB memo 2025-02 on FOC 16](https://www.courts.michigan.gov/4a4d85/siteassets/court-administration/focb-memoranda/2025/2025-02.pdf).) `⚠` — all four periods belong in Appendix A.

### 26.5 Contempt
Elements: a valid order; notice; ability to comply; willful noncompliance. Remedies under MCL 552.644: additional terms, modified parenting time, make-up time, **fine up to $100, jail up to 45 days for a first finding and 90 for subsequent**, work release, license suspension, community corrections placement, FOC supervision ([MCL 552.644](https://law.justia.com/codes/michigan/2006/mcl-chap552/mcl-552-644.html); [MJI Contempt Benchbook ch. 5](https://www.courts.michigan.gov/49aeda/siteassets/publications/benchbooks/contempt/contemptresponsivehtml5.zip/Contempt/Ch_5_Common_Forms_of_Contempt/Contempt_for_Violation_of_Parenting_Time_Order.htm)). **Bad-faith sanctions escalate $250 / $500 / $1,000 plus costs, and license suspension carries a 21-day window to request a modification hearing** ([MCL 552.645](https://law.justia.com/codes/michigan/chapter-552/statute-act-295-of-1982/section-552-645/)). `⚠` Distinguish civil from criminal contempt. Cross-ref *Dailey v Kloenhamer* on custody, parenting time, and civil contempt procedure (research §4.10) `⚠ holding unverified`.

### 26.6 Proving a Denial
The enforcement evidence packet: the order; the schedule; the exchange log; the messages (MRE 801(d)(2)); the third-party witness; the police "keep the peace" report. Foundations cross-referenced to Module 7.

### 26.7 ⚠ Enforcement Myths
Support and parenting time are **independent** — you may not withhold either because of the other. Police generally will not enforce a custody order at the curb. A child "refusing to go" is **not a defense**, but it is a serious factual problem requiring a different response than contempt. SCAO's own 2024–25 training is titled "Custody and Parenting Time Enforcement Myths" — and the myths it corrects are precisely the ones a guide like this propagates if enforcement is treated as an afterthought ([MJI Enforcement Myths material](https://www.courts.michigan.gov/4a509e/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/custody-and-parenting-time-enforcement-myths/custody-and-parenting-time-enforcement-myths-material.pdf)).

### 26.8 Responding to an Enforcement Allegation Against You
Good cause; ability to comply; documentation; what not to say.

### 26.9 Safety Overlay
`SAFETY OVERRIDE`. Enforcement filings can trigger retaliation. When to route through the FOC rather than direct contact; safe exchange options.

**Templates/tools:** enforcement route decision tree; Genesee parenting-time complaint checklist `ℹ`; violation proof table; make-up-time notice calendar; motion to show cause drafting aid; contempt response worksheet; judgment compliance log.
**Exercises:** choose the correct remedy for five violations; draft a specific complaint **quoting the violated order term verbatim**. *Done when the complaint quotes the term, states the date and time of each denial, and identifies the corroborating evidence for each.*
**Glossary:** enforcement, civil contempt, criminal contempt, good cause, show cause, make-up parenting time, clarification, self-help withholding.

## MODULE 27 — Modification and Change of Domicile (the 100-Mile Rule)

*Route tag: postjudgment. Opus Module 17 + Sol Module 21 + Gemini's new module, merged. **Entirely absent from v1**, per all three models.*

### 27.1 Modification Thresholds
Apply the *Vodvarka* (custody) or *Shade* (parenting-time-only) threshold to postjudgment facts (Module 2.3). Determine whether the proposed parenting-time relief **changes the ECE** — if it does, the custody framework and the higher burden apply.

### 27.2 The 100-Mile Rule
MCL 722.31 generally restricts changing a child's legal residence **more than 100 miles** from the residence at the commencement of the action, subject to consent, court permission, sole-legal-custody, and other statutory exceptions ([MCL 722.31](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-31)). **Exceptions under MCL 722.31(3)** where the parents' residences are already more than 100 miles apart, or the move brings them closer. Distances are measured radially.

### 27.3 The Five Factors — MCL 722.31(4)(a)–(e)
Degree to which the move will improve the quality of life for the child and the relocating parent; the degree to which each parent has complied with and utilized the parenting-time order and **whether the moving parent's motive is to frustrate parenting time**; whether a realistic modified schedule can preserve and foster the relationship; whether the opposing parent's motive is financial; **domestic violence**.

### 27.4 The Sequenced Analysis — Courts Have Remanded for Skipping Steps
1. The five factors, by **preponderance**.
2. Whether the move **alters the ECE**.
3. If it does, **clear and convincing evidence** on best interests.
4. A modified parenting-time schedule.

([Speaker Law, 100-mile rule procedural misstep](https://www.speakerlaw.com/blog/100-mile-rule-procedural-misstep-requires-remand-re-evaluation); [SCAO Changing Child's Legal Residence Checklist](https://www.courts.michigan.gov/48dc1e/siteassets/publications/benchbooks/qrms/family/domestic-relations/changing-childs-legal-residence-checklist.pdf).)

### 27.5 Out-of-State Moves and the Jurisdiction Overlay
UCCJEA basics (Module 3). **Leaving first is catastrophic.** `DO NOT USE THIS GUIDE ALONE`.

### 27.6 Opposing a Move; School Change; Support Consequences
Evidence that matters; proposing a workable long-distance schedule and cost allocation as a fallback; **separating a school-choice dispute from a domicile request** (they are different requests); the support consequences of a schedule change (Module 24).

### 27.7 Responding to Threatened Unilateral Relocation
Without violating any order. Immediate counsel trigger.

**Templates/tools:** modification threshold worksheet; domicile applicability checklist; five-factor relocation evidence matrix; proposed long-distance parenting schedule with transportation cost allocation; relocation response outline.
**Exercises:** analyze three moves by radial distance, legal custody, consent, and destination; separate a school-choice dispute from a domicile request. *Done when the reader can state which statute governs each of the three moves and why.*
**Glossary:** domicile, legal residence, 100-mile rule, radial miles, relocation, modification, change of circumstances.

## MODULE 28 — Reconsideration, Appeal, and Stay Triage

*Route tag: appeal. **`DO NOT USE THIS GUIDE ALONE` + `DEADLINE — ACT TODAY`.** Opus Module 18 + Sol Module 22 + Gemini's addition, merged. **This module explicitly reverses `custody_guide_plan.md` §4's out-of-scope call**, unanimously, on the ground that the deadline is jurisdictional and a reader who does not know it exists loses the right permanently while reading a guide that never mentioned it.*

The scope call is not "teach appellate practice." It is: **teach the deadline, the appeal-of-right/leave distinction, the standard of review, and how to preserve error — then hand off to counsel.**

### 28.1 ⚠ THE 21-DAY CLIFF
A claim of appeal must be filed within **21 days** (MCR 7.204(A)(1)(a)); Michigan's own civil-appeal guide identifies 21 days as the key period for a claim of appeal from a final order or an application for leave ([Michigan Court of Appeals, Guide to Handling a Civil Appeal](https://www.courts.michigan.gov/49b19f/siteassets/publications/manuals/coa/guide-to-handling-a-civil-appeal.pdf)). **This deadline is jurisdictional. Miss it and the right is gone.** Put it on the calendar the day any adverse final order enters.

### 28.2 ⚠ APPEAL OF RIGHT VS. LEAVE — THE DOMESTIC-RELATIONS ASYMMETRY
**Opus's finding; no pro se reader will guess this.** A postjudgment order is "final" — and thus appealable **of right** — when it "grants or denies a motion to change **legal custody, physical custody, or domicile**," MCR 7.202(6)(a)(iii) ([MCR 7.202](https://www.courtrules.net/michigan/michigan-court-rules/rule-7-202)); MCR 7.203(A)(1) limits the appeal to that portion. **An order resolving parenting time only generally is not appealable of right and requires an application for leave.**

> **The consequence:** an alienated parent's most common loss — **a parenting-time reduction** — is the one that is **not** appealable of right, while a custody loss is.

*Rains v Rains*, 301 Mich App 313 (2013), holds an order need not literally change custody to "affect" custody for appellate purposes ([opinion PDF](https://www.courts.michigan.gov/4a399b/siteassets/case-documents/uploads/opinions/final/coa/20130613_c312243(55)_rptr_90o-312243-final.pdf)).

### 28.3 The Standard of Review — Why Most Appeals Lose
MCL 722.28: affirm unless the findings are against the **great weight of the evidence**, there was a **palpable abuse of discretion**, or there was **clear legal error on a major issue** ([MCL 722.28](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-28); overview at [Michigan Bar Journal](https://www.michbar.org/file/barjournal/article/documents/pdf4article3753.pdf)).

### 28.4 Reconsideration First
MCR 2.119(F), **21 days**, palpable-error standard. Cheaper, faster, sometimes sufficient, and a common way to preserve issues. Note the effect of a timely postjudgment motion on the appellate period. Also: correction and settlement of an order.

### 28.5 ⚠ Stays — An Appeal Does Not Pause the Order
Filing an appeal ordinarily does **not** stay the order, and a stay request generally must first be decided by the **trial court** ([MCR 7.209 and the Court of Appeals guide](https://www.courts.michigan.gov/49b19f/siteassets/publications/manuals/coa/guide-to-handling-a-civil-appeal.pdf); [MCR 7.209](https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/michigan-court-rules/michigan-court-rules-responsive-html5.zip/Michigan_Court_Rules/Court_Rules_Chapter_7/Court_Rules_Chapter_7.htm?rhtocid=_7)). **Assuming an appeal pauses an adverse order is dangerous.** Comply with the adverse order while preserving objections.

### 28.6 Preserving Error and Ordering the Record
Object, state grounds, offer of proof, obtain a ruling (Module 22). Order the transcript; collect the register of actions, the orders, and the record on appeal.

### 28.7 ⚠ HARD STOP — GET A LAWYER
Appellate practice is a specialty. This module exists to protect the deadline and preserve the record, **not** to teach brief writing. Options: appellate limited-scope consultation, SBM referral, law school appellate clinics.

**Templates/tools:** final-order and appellate-path checklist; **21-day emergency calendar**; record / transcript / order / register-of-actions collection list; stay factors and harm worksheet **labeled attorney-review required**; appellate referral card.
**Exercises:** classify five orders as likely appeal-by-right, leave required, or attorney review required; build the **first-72-hours action list** after an adverse custody order. *Done when the list has a date, a source, and a phone number for each step.*
**Glossary:** reconsideration, final order, appeal of right, application for leave, stay, record on appeal, transcript, great weight of the evidence, palpable abuse of discretion, clear legal error.

## MODULE 29 — Long-Term Compliance, Self-Management, and Child-Centered Recovery

*Route tag: all. Sol Module 23 + Sol Module 7's self-management content + Opus Module 11.5 + Gemini's new Module 1.4, merged. **All three models called this substantive, not soft content.***

Opus frames it as **best-interest factor (g) risk management**; Sol frames it as a **litigation operating system**; Gemini asked for it as a standalone module on the psychological and practical toll. All three framings appear.

### 29.1 Why This Is Legal Content, Not Wellness Content
The target reader is likely dysregulated, sleep-deprived, hypervigilant, grieving loss of contact, and tempted to answer every provocation. That affects **credibility, deadlines, communication, and child safety**. Documented, predictable failure modes: over-filing; emotional testimony that reads as instability under **factor (g)**; retaliatory motion practice that funds the other side's fee request under **MCR 3.206(D)(2)(b)**; burnout mid-case.

### 29.2 The Litigation Operating System
**One calendar. One document repository. One communication channel. A weekly review.** A 24-hour pause rule for non-emergency messages. Structured escalation rather than reactive filing.

### 29.3 Communication Discipline
Single channel (OurFamilyWizard / TalkingParents / AppClose) — a tool, not a court-favored talisman (Module 25). **BIFF** (brief, informative, firm, friendly) as a non-legal conflict-communication technique, labeled as such. Never respond in kind. **The anti-pattern: baiting for admissions.** A reader taught to "document everything" will start texting the other parent to provoke a usable message; that produces bad exhibits, escalates conflict, and reads badly on factor (j) (Opus §4.3(d)).

### 29.4 Child-Safe Boundaries
No using the child as confidant, messenger, investigator, or emotional regulator. No litigation talk. No disparagement in the child's presence. No interrogation after exchanges. Acceptance test 8 governs every exercise in the book.

### 29.5 Affect Management and Hearing Performance
Grounding techniques; hearing rehearsal; recovery plan for the day after. **The material must avoid diagnosing either parent and must not imply that calm presentation proves truth or that trauma responses prove unreliability** (Sol §2).

### 29.6 Support Team, Therapy, and Privilege
A support-team map that preserves privilege boundaries. **Therapy is both self-care and an evidence risk** — records may be discoverable. Burnout and crisis triggers. Boundaries for reviewing case materials. Support resources independent of the legal process (Gemini's Module 1.4 objectives).

### 29.7 Living Under the Order
Implement it accurately. **Comply exactly even when they don't.** Calendar it. Maintain proportionate records without living in permanent litigation mode. Review support, school, medical, and schedule changes at defined intervals. Support the child's relationship with the other parent and the child's emotional safety. Know when changed facts justify legal review.

**Templates/tools:** litigation operating system setup guide; weekly review card; message pause-and-review card with a five-point pre-send checklist; facts/inference/emotion/action worksheet; child-safe boundaries card; hearing grounding and recovery plan; order implementation calendar; quarterly compliance audit; escalation ladder; post-litigation communication and wellness plan; communication protocol; one-page safety plan.
**Exercises:** reduce a 500-word reactive message to a factual logistics response (*done when the rewritten message contains no characterization, no history, and one clear request*); convert the final order into a one-year operational calendar; set objective triggers for documentation, FOC contact, and legal consultation.
**Glossary:** self-regulation, litigation fatigue, triangulation, escalation, material change, review interval, child-centered communication, BIFF communication method.

---

# APPENDICES

## APPENDIX A — MASTER DEADLINE TABLE

**Every clock in the book, in one place.** Opus §3.4(i) and Sol Appendix A. Every deadline in the treatise carries `⚠ TIME-CRITICAL` **and** appears here. Every row must state: **deadline · triggering event · rule or statute cite (with URL) · official form · where filed · consequence of missing it · verified-as-of date.** No deadline may appear in prose without a corresponding row here (acceptance tests 3 and 12).

| Period | Trigger | Authority | Consequence of missing it | Module |
|---|---|---|---|---|
| **7 days** — praecipe filed before hearing | Scheduled hearing date | Genesee local practice — **PROVISIONAL** `ℹ`. **Not in Genesee LCR 2.119**, which contains no timing or praecipe provision (verified from [Local Court Rules — Circuit](https://www.courts.michigan.gov/492c71/siteassets/rules-instructions-administrative-orders/local-court-rules/local-court-rules-circuit-court.pdf), eff. 6/1/2025). Confirm the source of this requirement with the clerk. | Motion not scheduled | 4.3 |
| **9 days (mail) / 7 days (delivery)** — **service** of motion, notice of hearing, and supporting brief or affidavits | Hearing date | **MCR 2.119(C)(1)** — 9 days if served by first-class mail, 7 days if served by delivery under MCR 2.107(C)(1)–(2) or MCR 1.109(G)(6)(a) | Motion not considered | 4.3, 12 |
| **5 days (mail) / 3 days (delivery)** — **service** of a response | Hearing date | **MCR 2.119(C)(2)** | Response not considered | 4.3, 12 |
| **7 days / 3 days** — motion **filed** / response **filed** before hearing | Hearing date | **MCR 2.119(C)(4)** — the **filing** deadline, a separate obligation from the (C)(1)–(2) **service** periods; both must be met | Motion or response not considered | 4.3, 12 |
| ⚠ **The posted Genesee notice states only half the rule** | — | The county's [Notice Regarding Motion Practice](https://cms2.revize.com/revize/geneseecountyjudicialcourt/Documents/Quick%20Links/Notice%20Regarding%20Motion%20Practice/Notice-Motion-Practice.pdf) (eff. March 4, 2019) **accurately quotes the MCR 2.119(C)(4) filing deadline but omits the (C)(1) service periods** | **A reader relying on the notice alone who serves by mail is late on service** | 4.3, 12 |
| **14 days** — pay the filing fee after a **fee-waiver denial**, or the filing is rejected | **The date the clerk sends notice** of the denial order (MDOC prisoners: 21 days from the order date) | **MCR 2.002(G)(1)**; the judge must rule on the waiver request within **3 business days** and a denial must state its reason, MCR 2.002(G) | **Filing rejected — the original filing date is lost** | 4.5, 12 |
| **14 days** — objection, or motion to rescind/modify, an ex parte order | **Service** of the order | **MCR 3.207(B)(5)–(6)**; parallel statutory clock at **MCL 722.27a(13)**. Text verified as of Chapter Updated May 1, 2026 — **not in flux** | Ex parte order becomes a temporary order | 14 |
| **14 days** — FOC resolution attempt after a timely objection | Filing of the objection | **MCR 3.207(B)(5)(b)**; MCL 722.27a(14) | FOC must then provide form pleadings and schedule a hearing | 14 |
| **21 days** — evidentiary hearing after a motion to rescind/modify | Filing of the motion | **MCR 3.207(B)(5)(a)** | — | 14 |
| **21 days** — evidentiary hearing the court **must** schedule after an ex parte order that could alter an ECE | **Entry** of the ex parte order | **MCR 3.207(B)(1)(b)** — notice of the hearing must appear in the order itself | Order entered without the hearing the rule requires | 14 |
| **28 days** — court **shall resolve** an ex parte parenting-time dispute | Request for a hearing | **MCL 722.27a(14)** — statutory, no MCR analogue | — | 14 |
| **14 days** — motion to modify or rescind a **PPO** | Service, or actual notice, of the order | **MCL 600.2950(13)** (later filing requires good cause); hearing within **14 days** under (14), or **5 days** where a firearm prohibition affects a respondent who must carry for employment | PPO stands | 17 |
| **14 days** — service of a subpoena **when documents are requested** | Date of required production | [MCR 2.506(C)(1)](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-506) | Subpoena unenforceable | 10.4 |
| **2 days** — service of a subpoena for testimony | Appearance date | MCR 2.506(C)(1) | Subpoena unenforceable | 10.4 |
| **21 days** — referee issues findings and recommendation | Close of referee hearing | **MCR 3.215(E)(1)** | — | 16.3 |
| **7 days** — objection to the **accuracy or completeness of a proposed recommended order** | Service of the proposed recommended order | **MCR 3.215(E)(3)(d)** — objections must state the inaccuracy or omission with specificity, be served under MCR 2.107, and be accompanied by a notice of hearing **and an alternative proposed recommended order** | Clerk submits the proposed order to the referee for approval | 16.3 |
| **7 days** — notice of intent to offer evidence **from the referee-hearing record** at the judicial hearing | The judicial hearing date, counted backward | **MCR 3.215(D)(4)(c)** — notice to the court and each other party; the offering party pays for any needed transcript (except as provided in (D)(4)(b)). A distinct clock from (E)(3)(d) above — surfaced by the Packet 1 drafting pass | Record evidence may be excluded; unplanned transcript cost | 16.5 |
| **7 days** — **supplemental objections** where the court *on its own motion* uses the referee record to limit the judicial hearing | **The date the record is provided** to the parties | **MCR 3.215(D)(4)(d)** — does not apply when a *party* requests the limitation under (F), or when the court orders a transcript to resolve a dispute about what occurred | Supplemental objections waived | 16.5 |
| **21 days** — written objection **and notice of hearing** to a referee recommendation | **Service** of the recommendation (note: Genesee packet says "mailed" — reconcile). Statutory trigger differs: MCL 552.507(4) runs from when the recommendation is **made available** | **MCR 3.215(E)(4)** — must state the specific findings or application of law objected to | **Recommended order becomes a final order** | 16.3 |
| **21 days** — judicial (de novo) hearing after objection | Filing of the objection | MCR 3.215(F)(1), extendable for good cause | — | 16.5 |
| **21 days** — response to an FOC make-up parenting-time notice | **The date the FOC notice was *sent*** — not receipt ([MCL 552.642(3)](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-642)) | MCL 552.642(2)–(3); the notice must carry the statutory warning in **boldface 12-point type** | **Failure to respond in writing is treated as agreement that parenting time was wrongfully denied** | 26.4 |
| **21 days** — request a hearing on a proposed **modification of parenting time** after a contempt notice | **Date of the notice** | **MCL 552.644(1)(b)**, referring to §45 | Right to be heard on modification lost | 26.5 |
| **1 week / 28 days** — notice of make-up time (weekend or weekday / holiday or summer) | Choice of make-up dates | MCL 552.642 | Make-up time may be refused | 26.4 |
| **1 year** — outer limit to take make-up time | Denial of parenting time | MCL 552.642 | Right to make-up time lost | 26.4 |
| **56 days** — FOC **may** decline a parenting-time complaint older than this | Date of the alleged violation | [MCL 552.641(2)(b)](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-641) — **discretionary ("may decline"), not jurisdictional.** The FOC may also decline under (2)(a) where the complainant has 2+ prior unwarranted complaints with unpaid costs, or under **(2)(c) where the order contains no enforceable provision relevant to the violation** | FOC route likely closes; motion route remains | 26.3 |
| **21 days** — request a hearing after license suspension | Suspension notice | [MCL 552.645](https://law.justia.com/codes/michigan/chapter-552/statute-act-295-of-1982/section-552-645/) | Suspension stands | 26.5 |
| **56 days** — contested custody hearing | Filing/commencement per rule | MCR 3.210(C) `⚠` | — | 13, 21 |
| **28 days** — court's decision after a contested custody hearing | Close of hearing | MCR 3.210(C)(3) `⚠` | — | 21, 25 |
| **7 days** — settle-order / objection-to-entry practice | Service of proposed order | MCR 2.602(B) `⚠ verify` | Order enters as proposed | 25 |
| **21 days** — motion for reconsideration | Entry of the order | MCR 2.119(F) | Reconsideration unavailable | 12.2, 28.4 |
| **21 days** — motion to amend or add **findings of fact** | **Entry** of the judgment or order | **MCR 2.517(B)** — and findings are *required* on contested postjudgment motions to modify a final judgment or order, **MCR 3.210(D)(1)**, an express exception to MCR 2.517(A)(4) | Amendment window closes. (Sufficiency-of-evidence challenges survive regardless — MCR 2.517(B) final sentence) | 16.5, 25, 28 |
| **21 days** — claim of appeal of right | **Entry** of the final order — and "entry" means the date the order is **signed**, or the date data entry is accomplished in the register of actions (**MCR 7.204(A)**) | **MCR 7.204(A)(1)(a)**: "The time limit for an appeal of right is jurisdictional." Runs instead from an order deciding a reconsideration motion **only if that motion was filed within the initial 21 days** — MCR 7.204(A)(1)(d). A **parenting-time-only** postjudgment order is generally **not** appealable of right: MCR 7.202(6)(a)(iii) covers legal custody, physical custody, and domicile only. [COA Civil Appeal Guide](https://www.courts.michigan.gov/49b19f/siteassets/publications/manuals/coa/guide-to-handling-a-civil-appeal.pdf) | **Jurisdictional — the right is gone.** Leave may still be sought under MCR 7.203(B)(5) | 28.1 |
| **Ongoing** — an appeal does **not** stay the order | Filing of appeal | MCR 7.209 | Adverse order continues to operate | 28.5 |
| **Statute-driven** — CPS Central Registry review/expungement timelines | Central Registry notice | MCL 722.627j(9) `⚠ verify periods` | Registry placement stands | 17.4 |

## APPENDIX B — PATHWAY, FORM, AND STANDARD DECISION MATRIX

Sol Appendix A. Rows: **triggering event · legal path · controlling authority · applicable standard/burden · current deadline · service rule · official form · Genesee filing location · fee · proof required · verified-as-of date.** Include only after current verification: FOC 61/61a, 62, 65, 68, 87, 137, 138; MC 11, 20, 416, 516; FOC 10, 16, 39, 50, 57, 58, 60, 67, 100; CC 375; and the Genesee complaint, praecipe, opt-in, opt-out, and miscellaneous-relief materials.

## APPENDIX C — EVIDENCE FOUNDATION AND OBJECTION CARDS

Opus Appendix C + Sol Appendix B. **Verbatim Q&A scripts, one page each, formatted for reading at the podium.** Text/email/app export; screenshot; photograph and video; audio and voicemail; social-media post; school record; medical/therapy record; police/CPS/public record; business-record certification; journal and calendar; opposing-party statement (MRE 801(d)(2)); hearsay within hearsay; the six objections you will make; the six you will hear and how to respond; making an offer of proof; preserving a ruling. Each card states the rule, the predicate facts, the script, and the objection most likely to be made.

## APPENDIX D — ANNOTATED DRAFTING-AID AND MODEL-DOCUMENT LIBRARY

Opus Appendix D + Sol Appendix D. Each item includes: assumed procedural posture and facts; issue checklist; official-form link; blank drafting aid; worked example; **"do not use if" conditions**; and a caption stating that a completed template is a starting draft, not a guarantee of legal sufficiency, and that clerks and referees cannot advise on how to complete it.

Contents: motion, brief, notice of hearing, proof of service; objection to referee recommendation (FOC 68); **motion for issuance of non-party discovery subpoenas under MCR 2.305(A)(1)**; MC 11 subpoena worked example (school attendance records); objection to ex parte order (FOC 61); motion to show cause; parenting-time complaint; motion for LGAL appointment; mediation position statement; stipulation; witness list and exhibit list; trial brief skeleton; opening and closing outlines; proposed order; custody journal with fictional entries; best-interest evidence matrix (full blank); discovery requests (interrogatories, RFP, RFA); MC 20 fee-waiver walkthrough; DV/PPO incident log; MCR 3.206(D) fee-request affidavit.

**Two absolute rules:** (1) do not reproduce a competing unofficial version of an SCAO form; (2) **no template is labeled "filing-ready."**

## APPENDIX E — ORDER-CLAUSE LIBRARY

Sol Appendix E. Alternative clauses with tradeoffs for: parenting-time schedules; holidays and school breaks; summer; exchanges and transportation; right of first refusal; communication protocol and platform; school and medical decision-making; deadlock-breaking; information access and emergency contacts; travel and passports; taxes and the Form 8332 execution obligation; expenses and cost allocation; domicile and change-of-address notice; safety exceptions and PPO reconciliation; dispute-resolution ladder. **Mark every provision that requires individualized review.**

## APPENDIX F — SCAO AND GENESEE COUNTY FORM DIRECTORY

Opus Appendix B: a **populated table**, not a list of numbers. Columns: SCAO or local form number · exact title · current revision date · direct URL · when you use it · which module covers it · common errors · `ℹ` verified-as-of.

Baseline entries (all revision dates must be re-verified at publication): FOC 10, FOC 16, FOC 39, FOC 50, FOC 57 (title identified as "Referee Findings and Recommendation After Hearing on Alleged Custody/Parenting Time Violation" — [FOC 57](https://www.courts.michigan.gov/4a7bf6/siteassets/forms/scao-approved/foc57.pdf), verify), FOC 60, FOC 61 and 62, FOC 65, FOC 68, FOC 87, FOC 89 (`⚠ title unverified — pull before publishing; Sol's instruction: remove uncertain entries rather than publish a guess`), FOC 137 and 138 (`⚠ verify`); MC 11, MC 20, MC 416, MC 516; CC 375; IRS Form 8332; Genesee opt-out packet, opt-in request, miscellaneous-relief motion, custody-motion packet, parenting-time complaint, color-coded praecipes. Plus the Michigan Legal Help DIY tool index (motion to change parenting time; answer and counterclaim for custody; fee waiver; overview of a Michigan custody case; filing a custody case for unmarried parents) ([All Forms](https://michiganlegalhelp.org/all-forms)).

**Closing worksheet:** "Which forms do I need for my situation?" mapping initial filing, postjudgment modification, support-only, enforcement, ex parte response, referee objection, PPO, and opt-out to their form sets.

## APPENDIX G — GENESEE COUNTY LOCAL-PRACTICE AND RESOURCE DIRECTORY

Sol Appendix C + Opus Appendix E + v1 Appendix B. **Live links, not only phone numbers. Every entry carries a checked date and a named checker.** `ℹ LOCAL PRACTICE` throughout.

Separate sections for: 7th Circuit Court and Circuit Court Records (filing location and hours); Genesee County FOC (address, phone, toll-free account line, email, complaint intake); **assigned-judge policy pages** — and a standing warning that one judge's policy is not all judges' policy; the family-division judicial roster and referee roster (`⚠` names change with elections, retirements, and reassignment — Judge McDowell's transition from FOC Director to the bench is the worked example; confirm the current FOC director); forms; the Genesee County Legal Resource Center and its on-site partner schedules; Legal Aid of Eastern Michigan; Legal Services of Eastern Michigan; SBM Lawyer Referral; Michigan Legal Help; YWCA Greater Flint PPO assistance; DV hotlines (statewide and national, 1-800-799-7233); the Community Resolution Center (CDRP) and MI-Resolve; supervised parenting-time and supervised-exchange providers; co-parenting and reunification therapists; the 7th Circuit Court Law Library; appellate resources.

## APPENDIX H — SPECIAL-CONTEXTS ROUTING APPENDIX

Sol §2, gap 8. Prevents silent failure for readers the guide never contemplated. Each entry: what is different, what this guide does **not** cover, and where to go.

Military deployment and the servicemember custody protections; incarceration of a parent; disability and courtroom accommodation requests; interpreters and limited English proficiency; **tribal / ICWA indicators**; nonparent (third-person) custody; a child conceived through sexual assault; guardianship overlap; a parent who is a minor; immigration status concerns; a child with significant special needs; a parent living out of state; grandparenting time.

## APPENDIX I — CHILD-SUPPORT DEVIATION FACTORS AND SUPPORT-INPUT AUDIT

The **18 factors of MCSF §1.04(E)** reproduced verbatim (see Module 24.3), on one page, with a working column for the reader's facts and the evidence that would support each. Source and verification date stated on the page: [2025 Michigan Child Support Formula Manual](https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf), verified August 9, 2026. **Reminder printed on the page:** a deviation is discretionary even where a factor exists, the list is not exhaustive, and MCL 552.605 requires specific written findings. Accompanied by the support-input audit checklist and the income/source/verification matrix.

## APPENDIX J — DO NOT DO THESE THINGS

Opus Appendix G. Consolidated criminal-, privacy-, and credibility-risk list with statutory cites and consequences, duplicating Module 9.2 verbatim so it can be printed and kept: non-participant recording including sending a child in with a recorder (MCL 750.539c; *Sullivan v Gray*); device installation in a private place (MCL 750.539d); accessing the other parent's accounts; GPS tracking; reading mail; using the child as an intelligence asset; deleting or altering evidence; contacting an accuser or witnesses; public/social-media rebuttal; disparagement in the child's presence; self-help withholding of the child or of support; filing sensitive material publicly without redaction.

## APPENDIX K — HARD-STOP AND REFERRAL MATRIX (WHEN YOU MUST HIRE A LAWYER)

Sol Appendix F + Opus Appendix H. The §0.4 trigger list, expanded into a matrix: trigger · why the self-help workflow stops · who to call · how fast · what to bring · what not to say before you get there. Includes appellate limited-scope consultation, criminal defense, CPS/administrative counsel, DV advocacy, and immigration referral.

## APPENDIX L — ICLE ARCHITECTURE CROSSWALK (EDITORIAL ONLY)

Opus Appendix I + Sol Appendix I. **Preserves the provenance value Gemini argued for, without imposing a practitioner's mental model on the reader** (see §0.6, conflicts 2 and 3). Maps every module in this outline to the original v1 / ICLE numbering. **Not the reader's navigation system.**

| v1 / ICLE | v2 module(s) |
|---|---|
| Front matter | FM.0–FM.6 |
| 1.1 Establish a custody and parenting-time strategy | M2 (standards), M11 (strategy) |
| 1.2 Child support issues | M24 |
| 1.3 Opt in/out of FOC services | M15.2 |
| 2.1 Pretrial phase and discovery | M10, M21 |
| 2.2 Local FOC practices | M4, M15.1 |
| 2.3 Motions and temporary orders | M12, M13, M14 |
| 2.4 Hearing on temporary orders / witness prep | M13, M22 |
| 2.5 Pretrial FOC referee hearing | M16 |
| 3.1 Mediation | M20 |
| 3.2 Prepare for trial | M21 |
| 3.3 Present proofs at trial | M22, M23 |
| 3.4 Enter the judgment | M25, M26, M29.7 |
| 4.1 Documentation and the custody journal | M8, M9 |
| 4.2 Communication tools | M29.3 |
| 4.3 False allegations | M17 |
| 4.4 DV, PPOs, and custody | M17.6, FM.5 |
| 5.1 How Michigan courts address alienation-type conduct | M18.1–18.2 |
| 5.2 Evidence strategies for alienation-type claims | M18.3–18.6 |
| 5.3 Experts and court-ordered evaluations | M19 |
| 6.1 Court rules for self-represented parties | M4 |
| 6.2 MiFILE and paper filing | M4.4 |
| 6.3 Fees and fee waivers | M4.5 |
| 6.4 Referees vs. judges, motion day, praecipe | M4.2, M4.6 |
| 6.5 Free and low-cost help | M4.7 |
| 7.1 ECE and burdens of proof | M2.1–2.2 |
| 7.2 Proper cause and change of circumstances | M2.3 |
| 7.3 Joint vs. sole custody | M2.6 |
| Appendix A (form directory) | Appendix F |
| Appendix B (resource directory) | Appendix G |
| Appendix C (sample documents) | Appendix D |
| Appendix D (glossary, terms only) | **Appendix N (full definitions, drafted first)** |
| Cross-reference map | Appendix O |
| *(no v1 counterpart)* | M1, M3, M5, M6, M7, M9, M27, M28, M29; Appendices A, B, C, E, H, I, J, K, M |

## APPENDIX M — SOURCE AND CHANGE-CONTROL REGISTER

Sol Appendix G. For **every** legal proposition in the treatise: module · exact authority · URL · quoted text · effective date · verification date · superseded source · reviewer name. Two maintenance cycles: **short cycle** for local fees, contacts, judge and referee assignments, forms, filing systems, and administrative orders; **long cycle** for stable published statutes and cases. Also holds the edition/source-change log surfaced to the reader in FM.3, and the open-items list from §0.8.

## APPENDIX N — MASTER GLOSSARY

**Drafted FIRST, before any module, and used verbatim throughout** (Opus §3.4: deferring definitions "guarantees the treatise will define 'de novo,' 'ECE,' and 'proper cause' inconsistently across seven lessons"). This is a complete appendix, not a term list — v1's Appendix D was a defect, not a design choice.

**Every entry has five fields:**
1. **Plain-language meaning** — what it means in ordinary words.
2. **Precise legal meaning** — stated only where it differs from the plain meaning.
3. **Controlling source** — statute, rule, case, or manual, with URL.
4. **Do not confuse with** — the adjacent terms readers conflate.
5. **Module** — where the concept is owned and taught.

Entries below are written to specification. Alphabetical.

---

**Adjournment.** *Plain:* postponing a hearing to a later date. *Legal:* a court-granted continuance; local practice governs how many a party may take without re-filing — Judge Hood's published policy allows the moving party two adjournments without re-filing, which is a **judge-specific** policy, not a countywide rule. *Source:* [Judge Hood Policies and Procedures](https://cms2.revize.com/revize/geneseecountyjudicialcourt/Documents/General%20Information/Judges/Hood-Policies-and-Procedures.pdf) `ℹ`. *Do not confuse with:* dismissal; stay. *Module:* 4.6.

**Affidavit.** *Plain:* a written statement of facts you swear is true. *Legal:* a sworn statement based on **personal knowledge**, admissible only for what the signer actually perceived; conclusions and hearsay inside an affidavit remain objectionable. *Source:* MCR 1.109(D)(3); MRE 602. *Do not confuse with:* a verified pleading; a brief; an unsworn letter. *Module:* 12, 14.1.

**Ambiguity (in an order).** *Plain:* wording vague enough that two parents can each claim they are complying. *Legal:* a provision a court cannot enforce by contempt because its terms are not definite; the usual cure is a motion to clarify rather than contempt. *Do not confuse with:* a violation. *Module:* 25, 26.1.

**Appeal of right.** *Plain:* an appeal the Court of Appeals must hear. *Legal:* available from a final order; in domestic relations, a postjudgment order is final and appealable of right when it grants or denies a motion to change **legal custody, physical custody, or domicile** — MCR 7.202(6)(a)(iii). *Source:* [MCR 7.202](https://www.courtrules.net/michigan/michigan-court-rules/rule-7-202). *Do not confuse with:* **application for leave** — a parenting-time-only order generally requires leave. *Module:* 28.2.

**Application for leave to appeal.** *Plain:* asking the Court of Appeals for permission to appeal. *Legal:* the route for orders that are not final for appellate purposes; the court may deny without reaching the merits. *Source:* MCR 7.203, 7.205. *Do not confuse with:* appeal of right. *Module:* 28.2.

**Arrearage.** *Plain:* unpaid back support. *Legal:* accrued unpaid support subject to statutory enforcement and, in some circumstances, surcharge. *Do not confuse with:* a current support obligation; a deviation. *Module:* 24.4.

**Attorney fees (award against the other party).** *Plain:* asking the court to make the other parent pay your legal costs. *Legal:* MCR 3.206(D) provides two independent routes — inability to bear the expense plus the other party's ability to pay; **or** fees incurred because the other party refused to comply with a previous order despite the ability to comply. Actual evidence is required, not unsubstantiated assertions. *Source:* [Michigan Court of Appeals 2026 opinion](https://www.michbar.org/Portals/0/opinions/appeals/2026/030926/85341.pdf); [SCAO Divorce Proceeding Checklist](https://www.courts.michigan.gov/4ab2c2/siteassets/publications/benchbooks/qrms/family/domestic-relations/divorce-checklist.pdf). *Do not confuse with:* a **fee waiver** (which only waives your own court fees); taxable costs; sanctions. *Module:* 24.6.

**Authentication.** *Plain:* proving an item is what you say it is. *Legal:* MRE 901 requires evidence sufficient to support a finding that the item is what its proponent claims; **Michigan has no FRE 902(13)/(14) analogue**, so electronic records cannot be self-authenticated by certificate and require live testimony. *Source:* [Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf). *Do not confuse with:* **hearsay** — authentication does not cure hearsay; relevance. *Module:* 7.

**Bench trial.** *Plain:* a trial decided by a judge, with no jury. *Legal:* the standard form of custody trial; the judge makes findings of fact and conclusions of law. *Do not confuse with:* a motion hearing; a referee hearing. *Module:* 23.

**Best interests of the child.** *Plain:* the standard the court uses to decide custody. *Legal:* the sum total of the twelve factors in MCL 722.23(a)–(l), weighed — **not** counted as a majority (*Baker v Baker*). *Source:* MCL 722.23. *Do not confuse with:* the **parenting-time factors** in MCL 722.27a(7), which are a separate list; the ECE question, which is decided first. *Module:* 2.4.

**BIFF.** *Plain:* a way of writing messages — brief, informative, firm, friendly. *Legal:* **not a legal term and not a Michigan rule**; a general conflict-communication technique. *Do not confuse with:* a court-ordered communication protocol. *Module:* 29.3.

**Binding authority.** *Plain:* law a Michigan trial court must follow. *Legal:* published Michigan Supreme Court and Court of Appeals decisions, statutes, and court rules. *Do not confuse with:* **persuasive authority** — unpublished opinions are persuasive only, MCR 7.215(C)(1). *Module:* 18.8.

**Burden of proof.** *Plain:* who has to prove what, and how convincingly. *Legal:* in custody, **preponderance** unless the proposed change would alter an established custodial environment, in which case **clear and convincing evidence** is required. *Source:* MCL 722.27(1)(c). *Do not confuse with:* the *Vodvarka* **threshold**, which is a separate gatekeeping showing. *Module:* 2.2.

**Business record (records of regularly conducted activity).** *Plain:* a record a school, clinic, or company keeps in the ordinary course of business. *Legal:* MRE 803(6) hearsay exception requiring a qualified witness or an appropriate certification; **statements inside the record made by outsiders are separate hearsay**. *Do not confuse with:* authentication (a different step); public records under MRE 803(8). *Module:* 6, 10.6.

**Calendar day / court day.** *Plain:* a calendar day is any day; a court day excludes weekends and holidays. *Legal:* computation of time is governed by MCR 1.108; read every deadline to see which it uses. *Do not confuse with:* business day. *Module:* FM.0, Appendix A.

**Caption.** *Plain:* the heading of a court document. *Legal:* the court name, county, case number, assigned judge, parties, and document title required by MCR 1.109. *Module:* 4.3, 12.

**Category V (CPS).** *Plain:* a CPS finding that the report was based on false or wrong information. *Legal:* one of five CPS investigation dispositions under MCL 722.628d; Categories I–III require a preponderance finding of abuse or neglect. *Source:* [MDHHS CPS investigation process](https://www.michigan.gov/mdhhs/adult-child-serv/abuse-neglect/childrens/report-process/investigation-process-and-results/childrens-protective-services-investigation-process); [PSM 713-01](https://mdhhs-pres-prod.michigan.gov/olmweb/EX/PS/Public/PSM/713-01.pdf). *Do not confuse with:* "unsubstantiated," which is **not** the same as a finding that a report was knowingly false. *Module:* 17.3.

**Central Registry.** *Plain:* a state list of people with a substantiated child-abuse or neglect finding. *Legal:* placement carries notice, record-review, expungement-request, and administrative-hearing rights; MDHHS must hold a hearing on a preponderance standard under MCL 722.627j(9). *Source:* [MDHHS Central Registry](https://www.michigan.gov/mdhhs/adult-child-serv/abuse-neglect/childrens/investigation/results/central-registry). *Do not confuse with:* a criminal record; a custody finding. *Module:* 17.4.

**Chain of custody.** *Plain:* the documented history of who had a piece of evidence and when. *Legal:* relevant to authentication and to the weight a court gives digital evidence. *Module:* 8.

**Change of circumstances.** *Plain:* something significant has changed since the last order. *Legal:* under *Vodvarka*, conditions surrounding custody that have or could have a **significant effect on the child's well-being** must have **materially changed since the last custody order**; normal life changes do not suffice. *Source:* [Paul Scott Associates memo quoting Vodvarka](https://www.paulscottassociates.com/wp-content/uploads/2019/08/Rifkin-Shade-v.-Vodvarka.pdf) `⚠ verify citation directly`. *Do not confuse with:* **proper cause** (the alternative threshold); the *Shade* standard for parenting-time-only requests; the merits. *Module:* 2.3.

**Clarification (motion to).** *Plain:* asking the court to make a vague order specific. *Legal:* often the correct first move where contempt would fail because the order's terms are indefinite. *Do not confuse with:* modification (which changes the order) or enforcement. *Module:* 26.1.

**Clear and convincing evidence.** *Plain:* substantially more convincing than "more likely than not," though less than criminal certainty. *Legal:* the burden that applies when a proposed change would alter an established custodial environment. *Source:* MCL 722.27(1)(c). *Do not confuse with:* preponderance; beyond a reasonable doubt. *Module:* 2.2.

**Coercion (in mediation).** *Plain:* being pressured into an agreement. *Legal:* a screening concern; MCR 3.224 requires domestic-violence screening and written consent in FOC domestic-relations mediation. *Module:* 20.

**Collateral source (evaluation).** *Plain:* a third party an evaluator contacts — a teacher, a doctor, a relative. *Legal:* collateral contacts are a legitimate cross-examination target: who was contacted, who was not, and why. *Module:* 19.5.

**Confidential address.** *Plain:* keeping your address out of court papers. *Legal:* protection available in DV contexts; requires following the court's protocol rather than simply omitting the address. *Do not confuse with:* sealing a record. *Module:* 8, FM.5.

**Consent order.** *Plain:* an order both parents agreed to. *Legal:* enforceable exactly as written; it can create an ECE regardless of any recital that it is "temporary" or "without prejudice." *Do not confuse with:* a stipulation (the agreement) versus the order (the court's act); a mediated settlement agreement before entry. *Module:* 13, 20.1.

**Contempt (civil).** *Plain:* being punished for disobeying a court order, with the punishment designed to force compliance. *Legal:* requires a valid order, notice, **ability to comply**, and willful noncompliance; remedies under MCL 552.644 include additional terms, modified parenting time, make-up time, a fine up to $100, jail up to 45 days first / 90 subsequent, work release, license suspension, community corrections, and FOC supervision. *Source:* [MCL 552.644](https://law.justia.com/codes/michigan/2006/mcl-chap552/mcl-552-644.html); [MJI Contempt Benchbook ch. 5](https://www.courts.michigan.gov/49aeda/siteassets/publications/benchbooks/contempt/contemptresponsivehtml5.zip/Contempt/Ch_5_Common_Forms_of_Contempt/Contempt_for_Violation_of_Parenting_Time_Order.htm). *Do not confuse with:* **criminal contempt** (punitive, different procedure); a police matter. *Module:* 26.5.

**Contemporaneous documentation.** *Plain:* writing it down at the time, not later. *Legal:* strengthens accuracy and supports MRE 612 refreshing and, narrowly, MRE 803(5) recorded recollection; **retroactive additions destroy the value and invite impeachment**. *Module:* 8.

**Corroboration.** *Plain:* independent evidence that backs up your account. *Legal:* not formally required for most custody facts, but decisive in practice where two parents contradict each other. *Module:* 8, 18.4.

**Custodian of records.** *Plain:* the person at a school, clinic, or company who keeps the files. *Legal:* the witness who supplies the MRE 803(6) foundation; **subpoena the custodian, not just the records**. *Module:* 10.6.

**Custody, legal.** *Plain:* who decides important things — school, medical care, religion. *Legal:* decision-making authority; may be joint or sole under MCL 722.26a. *Do not confuse with:* physical custody; parenting time. *Module:* 2.6.

**Custody, physical.** *Plain:* where the child lives. *Legal:* the residential arrangement; may be joint or sole. *Do not confuse with:* **parenting time**, which is the schedule, and with the **established custodial environment**, which is a factual finding. *Module:* 2.6.

**Custody journal.** *Plain:* your running log of what happened. *Legal:* **generally not an exhibit when offered by its author for the truth of its contents.** Its legitimate uses are as an MRE 612 memory refresher, as impeachment material, in narrow circumstances as recorded recollection under MRE 803(5), and as the outline for your own testimony. **Do not file it wholesale and do not hand it to an evaluator wholesale.** *Do not confuse with:* evidence — the reader's testimony is the evidence; the journal is scaffolding. *Module:* 8.

**De novo hearing (judicial review of a referee recommendation).** *Plain:* a new hearing in front of the judge. *Legal:* the court must allow the parties to present live evidence, **but under MCR 3.215(F)(2) it may prohibit evidence on unobjected findings, treat unobjected findings as conclusive, and bar new evidence or new witnesses absent an adequate showing the evidence was not available at the referee hearing.** MCL 552.507 permits a decision on the referee record, on new evidence, or on a supplemented record. *Source:* [MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215); [MCL 552.507](https://legislature.mi.gov/Laws/MCL?objectName=MCL-552-507). *Do not confuse with:* an **appeal**; a fresh trial with no constraints — that is what v1 wrongly described. *Module:* 16.5.

**Default.** *Plain:* losing because you did not respond in time. *Legal:* entry of default followed by a default judgment; domestic-relations defaults carry additional safeguards. *Module:* 12.

**Deviation (child support).** *Plain:* a support amount different from the formula result. *Legal:* permitted where the formula amount would be unjust or inappropriate, on **specific written findings**; MCSF §1.04(E) lists **18 factors**, deviation is **not mandatory** even where a factor exists, and the list is **not exhaustive**. *Source:* [2025 MCSF Manual](https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf) (verified August 9, 2026); MCL 552.605. *Do not confuse with:* modification; imputation. *Module:* 24.3, Appendix I.

**Direct examination.** *Plain:* questioning your own witness. *Legal:* generally **non-leading**; the witness tells the story. *Do not confuse with:* cross-examination, which is leading and controlled. *Module:* 22.

**Discovery.** *Plain:* the formal process of getting information from the other side and from third parties. *Legal:* MCR subchapter 2.300 applies in domestic relations except as Chapter 3 modifies it; **domestic-relations actions are exempt from the initial-disclosure regime under MCR 2.302(A)(4)**. *Source:* [MJI, Disclosure](https://www.courts.michigan.gov/4aeeef/siteassets/publications/benchbooks/civil/civilresponsivehtml5.zip/Civil/Ch_5_Discovery/Disclosure.htm). *Do not confuse with:* subpoenas for a hearing; a FOIA request. *Module:* 10.

**Domicile / legal residence.** *Plain:* where the child legally lives. *Legal:* MCL 722.31 generally bars changing the child's legal residence more than **100 radial miles** from the residence at commencement of the action without consent or court permission, with statutory exceptions. *Source:* [MCL 722.31](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-31). *Do not confuse with:* a school-choice dispute; a parent's own move without the child. *Module:* 27.

**Duperon rule.** *Plain:* the FOC report is not evidence unless both sides agree it is. *Legal:* *Duperon v Duperon*, 175 Mich App 77, 79 (1989) — the FOC report is not admissible unless both parties agree, may be used only for background and context, and the court's custody findings must rest on **competent evidence adduced at the hearing**. *Source:* [Duperon](https://www.casemine.com/judgement/us/59148af2add7b0493451a3c2). *Do not confuse with:* MRE 1101(b)(9), which merely exempts the court's *consideration* of the report from the evidence rules — the two operate together and produce the **report paradox**. *Module:* 15.4.

**Eavesdropping.** *Plain:* secretly listening to or recording other people. *Legal:* MCL 750.539c; *Sullivan v Gray* construes "eavesdrop" to exclude a **participant**; a participant's consent does **not** authorize a third party to record. Penalty up to 2 years and/or $2,000. **See the three-theory conflict box in Module 9 — the vicarious-consent question is unresolved and requires attorney verification.** *Source:* [Sullivan v Gray](https://law.justia.com/cases/michigan/court-of-appeals-published/1982/57301.html); [MCL 750.539a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-750-539a). *Do not confuse with:* MCL 750.539d (installing a device to observe or record in a **private place**), which is a separate offense. *Module:* 9.

**Established custodial environment (ECE).** *Plain:* the home where the child actually looks for guidance, discipline, the necessities of life, and parental comfort. *Legal:* a question of **fact about how the child lives** — MCL 722.27(1)(c); "it makes no difference whether that environment was created by a court order, without a court order, in violation of a court order, or by a court order that was subsequently reversed" (*Hayes v Hayes*, 209 Mich App 385, 388 (1995)). It may exist in one home, both, or neither; the court must determine it **before** reaching best interests, because it sets the burden. *Source:* [Hayes, quoted in COA opinion](https://cases.justia.com/michigan/court-of-appeals-unpublished/302626-7.pdf?ts=1396126000); [MJI/FOCB ECE material](https://www.courts.michigan.gov/4adec3/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/developing-an-understanding-of-the-established-custodial-environment/nov2024_mjifocb_ecematerial_zubac2.pdf). *Do not confuse with:* physical custody as labeled in an order — the label does not control the fact. *Module:* 2.1.

**Evidentiary hearing.** *Plain:* a hearing where witnesses testify and exhibits are admitted. *Legal:* required before a court may enter an order changing an ECE, on clear and convincing evidence — MCR 3.210(C)(1). *Source:* [MCR 3.210](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-210). *Do not confuse with:* a motion hearing on argument only. *Module:* 13.

**Ex parte order.** *Plain:* an order the judge signs without hearing from the other side first. *Legal:* requires a showing of irreparable injury, loss, or damage, or that notice would precipitate adverse action; **the other party has 14 days after service to object or move to rescind or modify** (MCR 3.207(B)) `⚠ rule in flux, ADM 2021-27`. The order remains enforceable until changed. *Do not confuse with:* an ordinary temporary order; an ex parte **PPO**, which is a different proceeding. *Module:* 14.

**Expungement (Central Registry).** *Plain:* getting your name removed from the state registry. *Legal:* MDHHS must hold a hearing to determine by a preponderance whether the record should be amended or expunged — MCL 722.627j(9). *Module:* 17.4.

**Facilitation.** *Plain:* actively helping the child have a good relationship with the other parent. *Legal:* MCL 722.23(j) asks about the willingness and ability of each parent to facilitate and encourage a close and continuing relationship — **and it is applied to both parents, including the reader**. *Do not confuse with:* mere non-interference. *Module:* 18.6.

**Fee waiver.** *Plain:* asking the court not to charge you filing fees because you cannot afford them. *Legal:* Form MC 20; eligibility commonly rests on means-tested benefits or indigency. *Source:* [MC 20](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc20.pdf). *Do not confuse with:* an **attorney-fee award against the other party** (MCR 3.206(D)) — a completely different thing. *Module:* 4.5.

**Final order.** *Plain:* the order that ends the case, or one the rules treat as final. *Legal:* for appellate purposes in domestic relations, includes a postjudgment order granting or denying a motion to change **legal custody, physical custody, or domicile** — MCR 7.202(6)(a)(iii). *Do not confuse with:* any order the reader considers important; a parenting-time-only order, which generally is not final for this purpose. *Module:* 28.2.

**Findings of fact.** *Plain:* what the judge decides actually happened. *Legal:* the court must make findings on each contested best-interest factor; ask for them and preserve the issue if they are not made. *Do not confuse with:* conclusions of law. *Module:* 23, 25.

**FOC (Friend of the Court).** *Plain:* the court office that investigates, recommends, and enforces in family cases. *Legal:* a statutory office under the Friend of the Court Act, MCL 552.501 et seq.; it investigates, recommends, mediates, and enforces, but it **does not decide** — the court does. *Do not confuse with:* the judge; the clerk; the **filing counter** (in Genesee, motions are filed at Circuit Court Records, **not** at the FOC). *Module:* 15.

**FOC case questionnaire (FOC 39).** *Plain:* the intake form that builds the FOC's file on your case. *Source:* [FOC 39](https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc39.pdf). *Module:* 15.1.

**FOC report paradox.** *Plain:* the judge may read the FOC report, but it is not evidence. *Legal:* MRE 1101(b)(9) exempts the court's consideration of the report from the evidence rules; *Duperon* holds it inadmissible absent both parties' agreement. **Consequences: a favorable report does not carry your burden; an unfavorable one is not evidence against you — unless you stipulate it in.** *Module:* 15.4.

**Form 8332.** *Plain:* the IRS form a custodial parent signs to let the other parent claim the child. *Legal:* required by federal law for the noncustodial parent to claim specified benefits regardless of what the state order says; **it does not transfer head-of-household status, the EITC, the child and dependent care credit, or the dependent-care exclusion**. *Source:* [IRS Form 8332](https://www.irs.gov/pub/irs-pdf/f8332.pdf); [IRS Dependents FAQ](https://www.irs.gov/faqs/filing-requirements-status-dependents/dependents/dependents-3). *Do not confuse with:* a state-court order allocating the exemption — the order creates the obligation, the form executes it. *Module:* 24.5.

**Foundation.** *Plain:* the preliminary facts you must establish before an exhibit or opinion comes in. *Legal:* varies by exhibit type; **laying a foundation is not a magic phrase**, and it does not resolve hearsay. *Module:* 7, Appendix C.

**GAL (guardian ad litem).** *Plain:* someone appointed to help the court figure out what is best for the child. *Legal:* an individual appointed to assist the court in determining best interests; **need not be an attorney**; hearsay in a GAL report may remain inadmissible over proper objection. *Source:* [Child Custody Act](https://www.legislature.mi.gov/documents/mcl/pdf/mcl-act-91-of-1970.pdf); [MJI summary of *Kuebler v Kuebler*](https://www.courts.michigan.gov/49add7/siteassets/publications/impact/written/family/impact-e-mail-5-22-23-family.pdf). *Do not confuse with:* **LGAL**; attorney for the child; FOC investigator; evaluator. *Module:* 19.1.

**Ghostwriting.** *Plain:* an attorney drafting a document you file under your own name. *Legal:* permitted within the limited-scope framework, MCR 2.117(B) and MCR 2.107. *Module:* 4.7.

**Good cause.** *Plain:* a legitimate reason. *Legal:* in enforcement, the absence of good cause for noncompliance is what opens the door to remedies. *Module:* 26.5.

**Great weight of the evidence.** *Plain:* the appellate court will not disturb a finding unless the evidence clearly points the other way. *Legal:* one of the three grounds for reversal under MCL 722.28, together with palpable abuse of discretion and clear legal error on a major issue. *Source:* [MCL 722.28](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-28). *Module:* 28.3.

**Hearsay.** *Plain:* an out-of-court statement offered to prove that what it says is true. *Legal:* inadmissible unless an exclusion or exception applies; **hearsay within hearsay** must be resolved layer by layer. *Do not confuse with:* an **opposing party's statement** under MRE 801(d)(2), which is not hearsay when offered against them; authentication. *Module:* 6.

**Home state (UCCJEA).** *Plain:* the state where the child has lived recently enough for its courts to decide custody. *Legal:* the jurisdictional anchor of the UCCJEA. *Do not confuse with:* where a parent lives; where the case was filed. *Module:* 3.

**Imputed income.** *Plain:* income the court treats you as having even though you are not earning it. *Legal:* used where a parent is voluntarily unemployed or underemployed; an MCSF concept. *Do not confuse with:* actual income; a deviation. *Module:* 24.2.

**In camera interview.** *Plain:* the judge talking to the child privately. *Legal:* permitted under MCR 3.210(C)(5) with **questioning limited to the reasonable-preference factor**; the rules of evidence do not apply, MRE 1101(b)(6). *Do not confuse with:* a channel for the child to narrate the other parent's misconduct — it is not one; an evaluation. *Module:* 6.

**Interference.** *Plain:* getting in the way of the other parent's time or relationship. *Legal:* not a cause of action; relevant through MCL 722.23(j) and MCL 722.27a(7)(f)–(g), and enforceable through Module 26. *Do not confuse with:* justified protective action; ordinary conflict; developmental resistance. *Module:* 18.

**Interrogatory.** *Plain:* a written question the other party must answer under oath. *Legal:* MCR subchapter 2.300; numeric limits apply `⚠ verify`. *Do not confuse with:* a request for production; a deposition question. *Module:* 10.3.

**Judgment.** *Plain:* the court's final decision document. *Legal:* in domestic relations, typically includes custody, parenting time, support, and related provisions. *Do not confuse with:* an order (broader); a recommendation. *Module:* 25.

**LGAL (lawyer-guardian ad litem).** *Plain:* a lawyer appointed for the child. *Legal:* an attorney whose duty runs to the child's **best interests**; MCL 722.24 authorizes a **discretionary** LGAL in a custody case, and **the LGAL's report is not admissible absent all-party stipulation** (MCL 722.24(3)). *Source:* [MCL 722.24](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-24); [SCAO third-person custody checklist](https://www.courts.michigan.gov/48dbed/siteassets/publications/benchbooks/qrms/family/domestic-relations/child-custody-dispute-involving-third-person-checklist.pdf). *Do not confuse with:* the **mandatory** LGAL in child-protective proceedings under MCL 712A — a different framework; a GAL; an attorney for the child, who advocates the child's **expressed preference**. *Module:* 19.1.

**Limited-scope representation.** *Plain:* hiring a lawyer for one task instead of the whole case. *Legal:* MCR 2.117(B) with MCR 2.107; Form MC 516 Notice of Limited Scope Appearance. *Source:* [SBM](https://www.michbar.org/news/newsdetail/New-Limited-Scope-Representation-Rules-Effective-January-1?nid=5507). *Do not confuse with:* MCR 5.117, the probate analogue, which does not apply here. *Module:* 4.7.

**Litigation hold.** *Plain:* stop deleting anything. *Legal:* a preservation obligation; deleting or altering potentially relevant material is independently damaging even if the underlying claim was weak. *Module:* 8.

**Make-up parenting time.** *Plain:* replacement time for time you were denied. *Legal:* MCL 552.642 requires a circuit make-up policy: **same type and duration**, taken **within one year**, **the denied parent chooses when**, **one week's notice** for weekend or weekday time and **28 days** for holiday or summer time; the other parent has **21 days to respond and failure to respond is treated as agreement**. *Source:* [MCL 552.642](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-642); [FOCB memo 2025-02](https://www.courts.michigan.gov/4a4d85/siteassets/court-administration/focb-memoranda/2025/2025-02.pdf). *Do not confuse with:* contempt remedies; compensatory time ordered by a judge. *Module:* 26.4.

**Material fact.** *Plain:* a fact that actually matters to the legal question. *Legal:* motions should plead numbered material facts tied to elements, not narrative. *Module:* 12.

**MCSF (Michigan Child Support Formula).** *Plain:* the state formula that sets child support. *Legal:* MCL 552.605 requires conformity unless the amount is unjust or inappropriate on specific written findings. *Source:* [2025 MCSF Manual](https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf). *Do not confuse with:* the MiChildSupport calculator, which is an estimate, not an order. *Module:* 24.1.

**Mediation.** *Plain:* a neutral person helping the parents try to agree. *Legal:* **FOC domestic-relations mediation under MCR 3.224** and **general court-rule mediation under MCR 3.216** are different, with different confidentiality rules; MCR 3.224 carries DV screening and written-consent requirements. *Do not confuse with:* an FOC investigation; arbitration; a settlement conference. *Module:* 20.

**MiFILE / e-filing / electronic service.** *Plain:* filing or serving documents online. *Legal:* Genesee is not currently a MiFILE court; paper filing is the default; AO No. 2026-3 authorizes a 7th Circuit pilot for **expanded electronic service**, which is service, not filing. *Source:* [MiFILE Available Courts](https://mifile.courts.michigan.gov/availablecourts); [AO No. 2026-3](https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/administrative-orders/aos-responsive-html5.zip/AOs/Administrative_Orders/AO_No._2026-3_%E2%80%94_Establishing_Pilot_Project_for_Implementing_Expanded_Electronic_Service.htm). `ℹ` *Module:* 4.4.

**Modification.** *Plain:* changing an existing order. *Legal:* requires clearing the *Vodvarka* threshold for custody or the *Shade* threshold for parenting time only, then the ECE/burden analysis, then the merits. *Do not confuse with:* enforcement; clarification. *Module:* 27.1.

**Motion.** *Plain:* a written request asking the court to do something. *Legal:* a motion is not interchangeable with a pleading, and different motions invoke different standards, forms, and clocks — that distinction is the organizing idea of Part I. *Module:* 12.

**Motion day.** *Plain:* the day of the week the court hears motions. *Legal:* Genesee's motion day is Monday, with judge-specific schedules `ℹ`. *Source:* [ICLE Q&A with Judge McDowell](https://community.icle.org/blogs/lindsey-a-dicesare/2026/05/18/qa-with-judge-anthony-j-mcdowell-7th-circuit-court). *Module:* 4.6.

**Motion in limine.** *Plain:* asking the judge to rule on an evidence question before trial. *Legal:* a pretrial evidentiary motion; some judges require it weeks before trial `ℹ`. *Module:* 21.

**Motion to compel.** *Plain:* asking the court to force the other side to answer discovery. *Legal:* may carry costs; pairs with the MCR 3.206(D)(2)(b) fee hook. *Module:* 10.7.

**Notice of hearing.** *Plain:* the paper telling everyone when and where the motion will be heard. *Legal:* must be served with the motion; Genesee's custody-motion packet instructs service **at least 9 days** before the hearing `ℹ`. *Module:* 4.3, 12.

**Objection (evidentiary).** *Plain:* telling the judge why the other side's evidence should not come in. *Legal:* must be timely and state grounds; **get a ruling** — an unresolved objection preserves nothing. *Module:* 22.

**Objection (to a referee recommendation).** *Plain:* the written filing that stops a referee's recommendation from becoming a final order. *Legal:* due within **21 days** after service; must include "a clear and concise statement of the **specific findings or application of law** to which an objection is made" (MCR 3.215(E)(4)); a frivolous or delay-motivated objection can carry costs and fees (MCR 3.215(F)(3)). *Do not confuse with:* an appeal; an evidentiary objection. *Module:* 16.4.

**Offer of proof.** *Plain:* telling the court, on the record, what the excluded evidence would have shown. *Legal:* the mechanism that preserves an evidentiary ruling for review. *Module:* 22, 28.6.

**One-party consent.** *Plain:* the idea that only one person in a conversation has to agree to a recording. *Legal:* **contested shorthand.** MCL 750.539c is drafted as all-party consent; *Sullivan v Gray* construes it to exclude a participant; *AFT Michigan v Project Veritas* (E.D. Mich., Mar. 30, 2026) confirms the participant rule; **the vicarious-consent question is unresolved.** See the three-theory conflict box. *Do not confuse with:* permission to record conversations you are not part of — that is a felony exposure. *Module:* 9.

**Opt in / opt out (FOC services).** *Plain:* choosing whether the Friend of the Court handles your case. *Legal:* MCL 552.505a `⚠ text unverified`; a FOC case opens by default unless the parties jointly opt out, and opting out forfeits FOC investigation and enforcement services. *Module:* 15.2.

**Order to show cause.** *Plain:* an order telling the other parent to come to court and explain why they should not be held in contempt. *Do not confuse with:* an FOC parenting-time complaint, which is the administrative route. *Module:* 26.2.

**Ordinary medical expense (OME).** *Plain:* routine, predictable medical costs built into the support figure. *Legal:* MCSF §3.04 allocation; the 2025 manual changed OME treatment where both parents have qualifying assistance. *Do not confuse with:* uninsured extraordinary health-care expenses, which are handled separately. *Module:* 24.1.

**Palpable abuse of discretion.** *Plain:* a decision so far outside the range of reasonable outcomes that it must be reversed. *Legal:* one of the three MCL 722.28 grounds. *Module:* 28.3.

**Parallel proceeding.** *Plain:* another case about the same facts running at the same time — CPS, criminal, PPO. *Legal:* each has its own rules and its own consequences for what you say; the **firewall protocol** in Module 17.2 governs. *Module:* 17.

**Parental alienation.** *Plain:* a lay and clinical term for one parent turning a child against the other. *Legal:* **not a Michigan cause of action and not a recognized standalone doctrine** in any published Michigan opinion located in this research. The conduct is reached through MCL 722.23(j) and MCL 722.27a(7)(f)–(g). **The word is banned from every template and every drafted filing** (§0.5). *Do not confuse with:* interference (conduct that can be proved); a diagnosis (which the reader must not make). *Module:* 18.1.

**Parental time offset.** *Plain:* the support adjustment for how many overnights each parent has. *Legal:* MCSF §3.03 `⚠ verify current brackets`. *Do not confuse with:* a deviation. *Module:* 24.1.

**Parenting time.** *Plain:* the schedule of when the child is with each parent. *Legal:* governed by MCL 722.27a, which contains **its own factor list** in subsection (7) separate from the MCL 722.23 best-interest factors. *Do not confuse with:* physical custody; the ECE. *Module:* 2.5.

**Party-opponent statement.** *Plain:* something the other parent said or wrote, offered against them. *Legal:* **not hearsay** under MRE 801(d)(2). Opus calls it the single most useful rule for a parent. *Do not confuse with:* a statement by the other parent's friend or relative, which is ordinary hearsay. *Module:* 6.

**Persuasive authority.** *Plain:* law a court may consider but does not have to follow. *Legal:* unpublished Michigan opinions, MCR 7.215(C)(1); out-of-state decisions. *Module:* 18.8.

**PPO (personal protection order).** *Plain:* a court order telling someone to stay away from you. *Legal:* a domestic-relationship PPO uses Form CC 375; **a PPO takes precedence over an existing custody or parenting-time order until it expires or the custody court modifies its order to accommodate it**, and MCL 600.2950(1)(l) allows a PPO to affect custody or parenting time without a separate best-interest analysis at issuance. *Source:* [MJI DV Benchbook Ch. 5](https://www.courts.michigan.gov/siteassets/publications/benchbooks/dvbb/dvbbresponsivehtml5.zip/DVBB/Ch_5_Special_Orders/Issuing_a_PPO_in_Domestic_Relations_Proceedings.htm). *Do not confuse with:* a no-contact order in a criminal case; an ex parte custody order. *Module:* 17.6.

**Praecipe.** *Plain:* the local scheduling slip you file to get a motion on the docket. *Legal:* Genesee uses a **color-coded** praecipe system and requires filing with the clerk at least 7 days before the hearing `ℹ`. *Do not confuse with:* the motion itself; the notice of hearing; proof of service. *Module:* 4.3.

**Preponderance of the evidence.** *Plain:* more likely than not. *Legal:* the default burden; applies unless a change would alter an ECE. *Module:* 2.2.

**Privilege.** *Plain:* a legal protection that keeps certain communications out of court. *Legal:* includes therapist-patient and physician-patient protections; **privilege can be waived**, including inadvertently — see the evaluation-order hearsay-waiver trap. *Do not confuse with:* confidentiality (a broader, weaker concept). *Module:* 6, 19.3.

**Pro se / self-represented / pro per.** *Plain:* representing yourself. *Legal:* **the Michigan Court Rules apply equally** — there is no separate, lighter rulebook. *Module:* 4.

**Proof of service.** *Plain:* the document proving you delivered papers to the other side. *Legal:* required; without it a motion may not be heard. *Do not confuse with:* the notice of hearing; service itself. *Module:* 4.3, 12.

**Proper cause.** *Plain:* a serious reason to revisit custody. *Legal:* under *Vodvarka*, "one or more appropriate grounds that have or could have a significant effect on the child's life to the extent that a reevaluation of the child's custodial situation should be undertaken." *Do not confuse with:* change of circumstances (the alternative branch); the merits. *Module:* 2.3.

**Protective action carve-out.** *Plain:* you are not penalized for reasonably protecting a child from abuse. *Legal:* built into MCL 722.23(j); it protects a parent who took reasonable protective action **and** does not excuse fabricated allegations. *Module:* 17.7.

**Protective order (discovery).** *Plain:* a court order limiting or conditioning discovery. *Do not confuse with:* a **personal protection order (PPO)** — completely different. *Module:* 10.3.

**Public record.** *Plain:* a government record. *Legal:* MRE 803(8) hearsay exception, with a law-enforcement caveat that limits some police material. *Module:* 6.

**Radial miles.** *Plain:* straight-line distance, not driving distance. *Legal:* the measure used for the MCL 722.31 100-mile rule. *Module:* 27.2.

**Reasonable preference (factor (i)).** *Plain:* what the child wants, if the child is old enough to express it. *Legal:* MCL 722.23(i); explored through the in camera interview, which is limited to this factor. *Do not confuse with:* letting the child decide; the child narrating the other parent's conduct. *Module:* 18.5.

**Recommendation for an order (referee).** *Plain:* the referee's proposed decision. *Legal:* **becomes a court order automatically unless a written objection is filed within 21 days after service** (MCR 3.215(E)(1)); Genesee's own packet describes the trigger as mailing — reconcile before publication. *Do not confuse with:* a judge's order; an interim order. *Module:* 16.3.

**Reconsideration.** *Plain:* asking the same judge to change their mind. *Legal:* MCR 2.119(F), **21 days**, palpable-error standard. *Do not confuse with:* an appeal. *Module:* 28.4.

**Record on appeal.** *Plain:* everything the appellate court gets to look at. *Legal:* transcripts, exhibits admitted, orders, and the register of actions — which is why preserving error at the hearing matters. *Module:* 28.6.

**Redaction.** *Plain:* blacking out protected information before filing. *Legal:* required for certain identifiers; a safety issue as well as a rules issue. *Module:* 8.

**Referee.** *Plain:* a court officer who hears family matters and recommends decisions. *Legal:* a domestic-relations referee; **the Michigan Rules of Evidence apply at referee hearings** (MCR 3.215(D)(1)); the referee recommends, the judge decides. *Do not confuse with:* a judge; a mediator; an FOC caseworker. *Module:* 16.1.

**Request for admission / request for production.** *Plain:* asking the other side to admit a fact, or to hand over documents. *Legal:* MCR subchapter 2.300 tools; limits and timing apply `⚠ verify`. *Module:* 10.3.

**Right of first refusal.** *Plain:* a clause giving the other parent the first chance to care for the child when you cannot. *Legal:* only as enforceable as its terms — define the trigger duration, the notice method, and the response window. *Module:* 25.

**Sanctions.** *Plain:* penalties for filing something baseless or acting in bad faith. *Legal:* MCR 1.109(E)(5)–(7) and MCL 600.2591 for frivolous filings; MCR 3.215(F)(3) for frivolous referee objections; MCL 552.645 escalating bad-faith parenting-time sanctions of $250 / $500 / $1,000 plus costs. *Do not confuse with:* contempt; an attorney-fee award. *Module:* 12.1, 26.5.

**Scheduling order.** *Plain:* the court's calendar for the case. *Legal:* sets discovery cutoff, disclosure deadlines, motion deadlines, and the trial date; extract every date into the Master Pretrial Deadline Tracker. *Module:* 21.

**Self-authentication.** *Plain:* evidence that proves itself without a witness. *Legal:* MRE 902(1)–(11); **Michigan has no equivalent to FRE 902(13)/(14)**, so certified electronic records are not self-authenticating here. *Module:* 7.

**Service.** *Plain:* legally delivering papers to the other party. *Legal:* the trigger for most response deadlines in this book; method and proof are governed by rule, and **safety may require an alternative method**. *Do not confuse with:* filing (delivering to the court); mailing. *Module:* 4.3, 12, FM.5.

**Settle-order / seven-day rule.** *Plain:* the process for entering a written order after the judge rules. *Legal:* the opposing party gets a short window to object to the form of the proposed order `⚠ verify current rule text`. *Module:* 25.

**Shade v Wright.** *Plain:* the case that sets an easier threshold for parenting-time-only changes. *Legal:* 291 Mich App 17 (2010) `⚠ citation and holding unverified — verify directly`. *Do not confuse with:* *Vodvarka*, which governs custody modification; the ECE analysis. *Module:* 2.3.

**Show cause.** *Plain:* a hearing where someone must explain why they should not be held in contempt. *Module:* 26.2.

**Specific objection.** *Plain:* naming exactly which finding you disagree with and why. *Legal:* required by MCR 3.215(E)(4); a generic objection invites the court to treat unobjected findings as conclusive. *Module:* 16.4.

**Standing.** *Plain:* whether you are legally entitled to bring the case. *Legal:* in custody, tied to parentage, an existing order, or a statutory basis for a nonparent. *Module:* 1.

**Stay.** *Plain:* pausing an order while you challenge it. *Legal:* **an appeal does not automatically stay a custody order**; a stay generally must be sought in the trial court first (MCR 7.209). *Source:* [COA Civil Appeal Guide](https://www.courts.michigan.gov/49b19f/siteassets/publications/manuals/coa/guide-to-handling-a-civil-appeal.pdf). *Do not confuse with:* an adjournment; a dismissal. *Module:* 28.5.

**Stipulation.** *Plain:* an agreement between the parties. *Legal:* can narrow issues usefully — **and can waive rights permanently**, including admitting an FOC or LGAL report that would otherwise be inadmissible, or waiving hearsay objections in an evaluation appointment order. *Do not confuse with:* a consent order (the court's act); a settlement. *Module:* 15.4, 19.3, 21.

**Subpoena (trial).** *Plain:* a court paper ordering a witness to appear or bring documents to a hearing. *Legal:* MCR 2.506(B)(1) — a subpoena signed by an attorney of record **or by the clerk** has the force of a judge's order; a pro se party obtains a **clerk-issued MC 11**; service at least 2 days before testimony, **14 days** when documents are requested. *Source:* [MCR 2.506](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-506); [MC 11](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc11.pdf). *Do not confuse with:* a **discovery subpoena** — see next entry. *Module:* 10.4.

**Subpoena (non-party discovery).** *Plain:* a subpoena for records or a deposition before the hearing. *Legal:* MCR 2.305(A)(1) — a represented party may issue one; **an unrepresented party must move the court for issuance.** *Source:* [MCR 2.305](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-305). *Do not confuse with:* a trial subpoena, which the clerk can issue for you. *Module:* 10.4.

**Substantiated / unsubstantiated (CPS).** *Plain:* whether CPS found the allegation supported. *Legal:* Categories I–III involve a preponderance finding; **"unsubstantiated" is not a finding that the report was knowingly false** — that is Category V. *Do not confuse with:* a court's custody finding, which is independent. *Module:* 17.3.

**Sullivan v Gray.** *Plain:* the Michigan case holding that a person taking part in a conversation is not "eavesdropping" by recording it. *Legal:* 117 Mich App 476; 324 NW2d 58 (1982); **explicit that a participant's consent does not authorize a third party to record.** *Source:* [Sullivan v Gray](https://law.justia.com/cases/michigan/court-of-appeals-published/1982/57301.html). *Do not confuse with:* blanket permission to record; the unresolved vicarious-consent question. *Module:* 9.

**Temporary order.** *Plain:* an order that governs while the case is pending. *Legal:* fully enforceable; **it can create or shift an established custodial environment regardless of the word "temporary."** *Do not confuse with:* an ex parte order; a final judgment. *Module:* 13.

**Tender-years exception (MRE 803A).** *Plain:* a hearsay exception for young children's statements. *Legal:* **applies only in criminal and juvenile delinquency proceedings — not in custody cases.** *Source:* [SCAO Sexual Assault Benchbook](https://www.courts.michigan.gov/4a3004/siteassets/publications/benchbooks/sabb/sabbresponsivehtml5.zip/SABB/Ch_6_Evidence/Tender-Years_Exception.htm). *Do not confuse with:* MRE 803(3) state of mind; the in camera interview. *Module:* 6.

**Testimony.** *Plain:* sworn statements made in court. *Legal:* the evidence; a journal, a timeline, and a binder are not substitutes for it. *Module:* 22.

**Transcript.** *Plain:* the written record of what was said at a hearing. *Legal:* the objecting party ordinarily pays for it when relying on the referee-hearing record; required for appellate review. *Module:* 16.5, 28.6.

**Triangulation.** *Plain:* putting the child in the middle between the parents. *Legal:* **descriptive, not a Michigan legal term**; conduct that damages the reader under factor (j) and harms the child. *Module:* 29.4.

**UCCJEA.** *Plain:* the law that decides which state's courts handle a custody case. *Legal:* the Uniform Child-Custody Jurisdiction and Enforcement Act; Form MC 416 collects the residence history the court needs. *Source:* [MC 416](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc416.pdf). *Do not confuse with:* venue (which county); personal jurisdiction. *Module:* 3.

**Uniform child support order (FOC 10).** *Plain:* the standard form the support order takes. *Source:* [FOC 10](https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc10.pdf). *Module:* 25.

**Verified pleading.** *Plain:* a pleading you swear to. *Legal:* signature and verification under MCR 1.109(E) carry sanctions exposure for baseless assertions. *Do not confuse with:* an affidavit. *Module:* 12.

**Vicarious consent.** *Plain:* the idea that a parent can consent to a recording on a child's behalf. *Legal:* **unresolved in Michigan.** Gemini asserts an affirmative prohibition citing *Fisher v Perron*, 30 F.4th 289 (6th Cir. 2022); Opus reaches the same practical result through the non-participant felony analysis; Sol declines to state a rule and imposes a hard stop. **Attorney verification required before publication.** *Source:* [Recording Law — Michigan](https://www.recordinglaw.com/united-states-recording-laws/one-party-consent-states/michigan-recording-laws/). *Do not confuse with:* participant recording. *Module:* 9.

**Vodvarka threshold.** *Plain:* the gate you must get through before a court will even consider changing custody. *Legal:* *Vodvarka v Grasmeyer*, 259 Mich App 499; 675 NW2d 847 (2003) — proper cause **or** a material change of circumstances since the last custody order, having or capable of having a significant effect on the child. `⚠ verify citation and holding directly`. *Do not confuse with:* the burden of proof; the best-interest merits; the *Shade* standard for parenting time only. *Module:* 2.3.

**Witness list / exhibit list.** *Plain:* the papers naming who will testify and what documents you will use. *Legal:* due on the scheduling order's deadline; late disclosure can result in exclusion. *Module:* 21.

---

---

### Glossary, continued — remaining controlled terms
*(These entries complete coverage of Claude Opus 5.0's Appendix F term list plus every term introduced in a GPT-5.6 Sol or Gemini 3.1 Pro module. At drafting, merge this run into the single alphabetical sequence above; it is kept as a separate run here only so the reviewer can see what was added in v2.)*

**Alternative explanation.** *Plain:* another reason the same fact could be true. *Legal:* not a legal doctrine but a required analytic step in this book — every interference allegation must be tested against safety concerns, developmental resistance, ordinary conflict, and unknown cause before it is presented as interference (acceptance test 9). *Do not confuse with:* an excuse. *Module:* 18.2.

**Appointment order (evaluation).** *Plain:* the order that creates an evaluator's or LGAL's job. *Legal:* it controls scope, cost allocation, collateral contacts, data access, and — critically — **may contain a hearsay-waiver clause that waives your objection to the report**. Read it before signing. *Source:* [SBM e-Journal summary](https://www.michbar.org/opinions/content_search_detail/EJournalNumber/86190). *Do not confuse with:* the report itself; a stipulation to admit the report. *Module:* 19.3.

**Caucus.** *Plain:* the mediator meeting separately with one parent. *Legal:* a mediation technique; **shuttle or caucus-only mediation is a safety accommodation** where direct contact is unsafe. *Do not confuse with:* an ex parte communication with a judge, which is improper. *Module:* 20.

**CDRP (Community Dispute Resolution Program).** *Plain:* the state-funded community mediation network. *Legal:* the center serving Genesee County is the **Community Resolution Center**, Flint, Michigan. *Source:* [Michigan ODR CDRP center list](https://www.courts.michigan.gov/4aaccd/siteassets/offices/odr/cdrp-centers-(list-only).pdf). *Do not confuse with:* the similarly named center serving Genesee County, **New York**; FOC in-house mediation. `ℹ` *Module:* 20.

**Clear legal error on a major issue.** *Plain:* the judge got an important legal rule wrong. *Legal:* one of the three grounds for appellate reversal under MCL 722.28. *Do not confuse with:* disagreeing with how the judge weighed the evidence, which is the great-weight ground and is much harder. *Module:* 28.3.

**Closing argument.** *Plain:* your summary at the end of trial. *Legal:* argument, not evidence; it must cite **admitted** evidence, and in a custody case it is structured factor by factor. *Do not confuse with:* an opening statement, which is not argument. *Module:* 23.

**Coaching.** *Plain:* telling a child or witness what to say. *Legal:* not a separate offense, but it destroys credibility, damages the reader under factor (j), and — with a child — is banned from every exercise in this book (acceptance test 8). *Do not confuse with:* legitimate witness preparation, which covers process and topics, never content. *Module:* 18.5, 22.

**Compliance.** *Plain:* actually doing what the order says. *Legal:* comply exactly even when the other parent does not; noncompliance funds the other side's MCR 3.206(D)(2)(b) fee request and is itself evidence under MCL 722.27a(7)(f). *Do not confuse with:* agreement — you can comply while preserving an objection or an appeal. *Module:* 29.7.

**Conclusion of law.** *Plain:* the judge's ruling on what the law requires given the facts found. *Do not confuse with:* findings of fact, which are reviewed under a different appellate standard. *Module:* 23.

**Conclusive finding.** *Plain:* a referee finding the judge may treat as settled. *Legal:* under MCR 3.215(F)(2)(b) the court may determine that a referee finding is conclusive **as to a fact to which no objection was filed** — which is why objections must be finding-by-finding. *Module:* 16.5.

**Confidentiality (mediation).** *Plain:* what is said in mediation generally stays there. *Legal:* the protections differ between MCR 3.216 mediation and MCR 3.224 FOC domestic-relations mediation; read which applies before speaking freely. *Do not confuse with:* privilege; a protective order. *Module:* 20.

**Contempt (criminal).** *Plain:* punishment for disobeying the court, imposed to vindicate the court's authority rather than to force compliance. *Legal:* carries greater procedural protections than civil contempt; the two are not interchangeable and a pro se litigant should not assume which the court is using. *Do not confuse with:* **civil contempt**, which is coercive and remedial; a criminal charge brought by a prosecutor. *Module:* 26.5.

**Continuing exclusive jurisdiction.** *Plain:* the state that made the custody order usually keeps control of it. *Legal:* a UCCJEA concept; it is why moving does not automatically move the case. *Do not confuse with:* home state; venue. *Module:* 3.

**Corroborating witness.** *Plain:* a neutral person who saw what you say happened. *Legal:* third-party exchange witnesses, teachers, coaches, and providers carry more weight with a family judge than a parent, a new partner, or a relative standing alone. *Module:* 22.

**Costs (taxable).** *Plain:* specific court-related expenses the winning side may recover. *Legal:* distinct from attorney fees and from sanctions; governed by separate rules and generally modest. *Do not confuse with:* an MCR 3.206(D) attorney-fee award; a fee waiver. *Module:* 24.6.

**Cross-examination.** *Plain:* questioning the other side's witness. *Legal:* leading questions are permitted; the technique is short questions, one fact per question, and knowing when to stop. **Do not argue with the witness.** *Do not confuse with:* direct examination, which is non-leading. *Module:* 22.

**Deadlock provision.** *Plain:* the clause that says what happens when joint legal custodians cannot agree. *Legal:* essential in a high-conflict case; without one, joint legal custody produces repeat motion practice. *Module:* 25, Appendix E.

**Dependency exemption / child tax benefits.** *Plain:* who gets to claim the child on taxes. *Legal:* Michigan courts may allocate it and treat the allocation as part of child support, but **federal law controls execution through Form 8332**, which does not transfer head-of-household status, the EITC, or the dependent-care credit. *Source:* [IRS Dependents FAQ](https://www.irs.gov/faqs/filing-requirements-status-dependents/dependents/dependents-7). *Do not confuse with:* the Child Tax Credit rules; head-of-household status. *Module:* 24.5.

**Direct resolution.** *Plain:* solving a parenting-time problem by talking to the other parent. *Legal:* the first rung of the enforcement ladder — **but it is overridden by any PPO, no-contact order, or safety plan.** *Module:* 26.2.

**Discovery cutoff.** *Plain:* the last day to conduct discovery. *Legal:* set by the scheduling order; missing it usually cannot be cured by a late subpoena. *Module:* 21.

**Duplicate.** *Plain:* a copy. *Legal:* MRE 1001–1008 generally permit a duplicate unless a genuine question is raised about authenticity or it would be unfair to admit it. *Do not confuse with:* an original; an altered or cropped screenshot, which is neither. *Module:* 6, 7.

**Emergency jurisdiction (temporary).** *Plain:* a state can act in an emergency even if it is not the home state. *Legal:* a narrow UCCJEA power, usually temporary; it is not a way to relitigate custody in a friendlier state. *Do not confuse with:* home-state jurisdiction; an ex parte order. *Module:* 3.

**Enforcement.** *Plain:* making the other parent follow the order. *Legal:* the ladder is documentation → clarification → direct resolution (safety permitting) → FOC complaint and make-up policy → motion to enforce → contempt. **Support and parenting time are independent; you may not withhold either because of the other.** *Do not confuse with:* modification; self-help. *Module:* 26.

**Entry (of an order).** *Plain:* the date the judge signs and the clerk files the order. *Legal:* the trigger for reconsideration (21 days) and for the appellate period (21 days) — **not** the date of the oral ruling. *Do not confuse with:* the hearing date; the service date. *Module:* 25, 28.1.

**Escalation ladder.** *Plain:* a planned sequence of responses instead of reacting. *Legal:* not a legal term; a case-management discipline that reduces over-filing and its sanctions and fee exposure. *Module:* 29.2.

**Excited utterance.** *Plain:* something said in the heat of a startling event. *Legal:* MRE 803(2) hearsay exception. *Do not confuse with:* a present sense impression (MRE 803(1)); a statement made later, calmly, which is neither. *Module:* 6.

**Exhibit.** *Plain:* a document or object you ask the court to accept as evidence. *Legal:* an item is not evidence until it is **admitted**; admission requires authentication (MRE 901), a hearsay answer, and no successful privilege or unfair-prejudice objection. Exhibits are pre-marked and numbered, with copies for the court, the witness, and the opposing party. *Do not confuse with:* an attachment to a motion, which is not admitted evidence; the reader's binder. *Module:* 22, Appendix C.

**Expert witness.** *Plain:* someone allowed to give an opinion because of specialized knowledge. *Legal:* MRE 702/703; **PAS-framed and reunification-theory testimony draws MRE 702 challenges**, is expensive, and can be neutralized on cross-examination. *Do not confuse with:* a treating therapist, who is a fact witness about treatment; an FOC investigator; an LGAL. *Module:* 19.5, 18.8.

**Facts / inference / emotion / action.** *Plain:* a four-way sort applied to everything you write. *Legal:* not a legal rule; the discipline that keeps affidavits, journals, and messages admissible and credible. *Module:* 8, 29.3.

**False allegation.** *Plain:* an accusation that is not true. *Legal:* the guide never asserts falsity as a conclusion; it distinguishes **unsubstantiated** (not proven) from **Category V** (based on false or erroneous information) from an affirmative judicial finding that a report was knowingly false. *Do not confuse with:* an unsubstantiated finding. *Module:* 17.3.

**Filing.** *Plain:* delivering a document to the court. *Legal:* distinct from **service**, which is delivering it to the other party; both are required and each has its own proof and deadline. In Genesee, motions are filed at Circuit Court Records, 2nd Floor `ℹ`. *Module:* 4.3.

**FOC enforcement.** *Plain:* the Friend of the Court acting on a violation. *Legal:* on a written parenting-time complaint the FOC must apply the make-up policy, commence civil contempt, or move to modify (MCL 552.641). *Do not confuse with:* your own motion to show cause, which you control. *Module:* 26.3.

**FOC investigation.** *Plain:* the FOC looking into custody and parenting time and writing a recommendation. *Legal:* the FOC is not statutorily required to address the ECE, though a judge may request it. *Source:* [MJI Investigation Myths](https://www.courts.michigan.gov/4a2436/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/custody-parenting-time-investigation-myths/custody-and-parenting-time-investigation-myths_material.pdf). *Do not confuse with:* a custody evaluation by a licensed professional; a CPS investigation. *Module:* 15.3.

**Hearsay within hearsay.** *Plain:* a statement inside a document that itself repeats someone else's statement. *Legal:* each layer needs its own exclusion or exception — admitting a school or medical record does not admit every statement recorded inside it. *Module:* 6.

**ICWA (Indian Child Welfare Act) indicators.** *Plain:* signs that a child may be a member of, or eligible for membership in, a tribe. *Legal:* triggers a separate federal and state framework outside this guide's scope. **Hard stop; get counsel.** *Module:* 1, 3, Appendix H.

**Impeachment.** *Plain:* showing a witness is not reliable. *Legal:* commonly through a prior inconsistent statement; the custody journal's most realistic courtroom use is as impeachment material, not as substantive evidence. *Do not confuse with:* attacking a person's character, which usually backfires. *Module:* 22.

**Inference.** *Plain:* a conclusion you draw from a fact. *Legal:* not a fact; affidavits and journals must separate the two, and a witness may testify only to what they perceived. *Module:* 8.

**Interim order.** *Plain:* a referee recommendation given effect while an objection is pending. *Legal:* MCR 3.215(G) limits interim effect by administrative order — **notably not for orders changing custody or domicile**. *Do not confuse with:* a temporary order; the judge's final order. *Module:* 16.7.

**Joint custody.** *Plain:* both parents share something — decisions, time, or both. *Legal:* MCL 722.26a; the court must consider joint custody on request and state reasons for granting or denying it, and must consider **whether the parents can cooperate and generally agree on important decisions**, which in a high-conflict case cuts against joint legal custody — **including against the reader**. *Do not confuse with:* equal parenting time; joint legal and joint physical custody, which are separate questions. `⚠ full statutory text unverified`. *Module:* 2.6.

**Leading question.** *Plain:* a question that suggests its own answer. *Legal:* generally improper on direct examination, proper on cross. *Module:* 22.

**Legal information vs. legal advice.** *Plain:* explaining how the system works vs. telling you what to do in your case. *Legal:* clerks, referees, FOC staff, and self-help navigators may give information only. **This book gives information and decision frameworks, never advice.** *Module:* 4.7, FM.1.

**Litigation fatigue.** *Plain:* burning out mid-case. *Legal:* not a legal term, but a documented failure mode producing missed deadlines, over-filing, and testimony that reads as instability under factor (g). *Module:* 29.1.

**Low Income Threshold.** *Plain:* an MCSF floor that protects a very low earner's income in the calculation. *Legal:* a 2025 MCSF concept affecting how family income is combined. *Source:* [2025 MCSF Manual](https://www.courts.michigan.gov/4a7a53/siteassets/court-administration/standardsguidelines/foc/2025mcsf.pdf). *Do not confuse with:* deviation factor 4, which concerns the child's residence income relative to public assistance. *Module:* 24.1.

**Material change (postjudgment review trigger).** *Plain:* a change big enough to justify going back to court. *Legal:* in the long-term-compliance module this is an operational trigger for legal consultation; the legal test remains *Vodvarka* or *Shade*. *Module:* 29.7.

**Memorialize.** *Plain:* writing an agreement down so it counts. *Legal:* an agreement becomes enforceable through entry as an order; an unmemorialized understanding is not enforceable by contempt. *Module:* 20.

**Metadata.** *Plain:* the hidden data attached to a file — dates, device, location. *Legal:* can support authentication and can also disclose more than intended; preserve **native files**, do not re-photograph or re-export in ways that strip it. *Do not confuse with:* the visible content. *Module:* 8.

**Methodology (of an evaluation).** *Plain:* how the evaluator did the work. *Legal:* the legitimate cross-examination target — data sources, testing limits, collateral contacts made and not made, time spent — **not** the evaluator's character. *Module:* 19.5.

**MiChildSupport calculator.** *Plain:* the state's free online support estimator. *Legal:* a planning tool; **its output is an estimate, not an order**. `ℹ verify current URL`. *Module:* 24.1.

**Motion to enforce.** *Plain:* asking the court to make the other parent follow the order, short of contempt. *Do not confuse with:* a motion to clarify (the order is vague) or a motion to modify (you want different terms). *Module:* 26.2.

**Native file.** *Plain:* the original digital file in its original format. *Legal:* preserve it; a screenshot of a screenshot weakens authentication and invites a completeness objection. *Module:* 8.

**No-contact order.** *Plain:* a criminal-case order telling someone not to contact another person. *Legal:* independent of a PPO and of any custody order; **it overrides ordinary exchange and communication guidance in this book**. *Do not confuse with:* a PPO, which is a civil proceeding. `SAFETY OVERRIDE`. *Module:* 17.

**Nonhearsay.** *Plain:* an out-of-court statement offered for some purpose other than proving it is true. *Legal:* includes effect on the listener, notice, and statements offered to show the speaker's state of mind — **and, separately, an opposing party's statement, which the rule defines as not hearsay**. *Module:* 6.

**Opening statement.** *Plain:* the short preview you give at the start of trial. *Legal:* a roadmap, not argument and not evidence. *Do not confuse with:* closing argument. *Module:* 23.

**Operative provision.** *Plain:* the part of an order that actually tells someone to do something. *Legal:* recitals and background do not create obligations; enforcement runs on the operative language. *Module:* 25.

**Original action.** *Plain:* the case that first establishes custody. *Legal:* distinct from a postjudgment proceeding; different standards, forms, and thresholds apply — the *Vodvarka* gate does not apply to an initial determination. *Do not confuse with:* postjudgment modification. *Module:* 1.

**Parentification.** *Plain:* treating a child like an adult confidant or caretaker. *Legal:* **descriptive, not a Michigan legal term**; conduct relevant to factors and harmful to the child, but never to be pleaded as a diagnosis. *Module:* 29.4.

**Paternity.** *Plain:* legal fatherhood. *Legal:* custody rights for an unmarried father generally depend on an existing paternity determination or acknowledgment; establishing paternity is largely outside this guide's scope and is referenced only as a prerequisite. *Module:* 1.

**Postjudgment.** *Plain:* after the final order or judgment. *Legal:* the phase where a high-conflict case actually lives — modification, enforcement, and review — and where the *Vodvarka* / *Shade* thresholds apply. *Module:* 1, 26–29.

**Present sense impression.** *Plain:* describing something as it happens or right after. *Legal:* MRE 803(1) hearsay exception. *Do not confuse with:* an excited utterance; a later recollection. *Module:* 6.

**Pretrial conference.** *Plain:* a meeting with the judge to organize the trial. *Legal:* often where stipulations, witness and exhibit lists, and evidentiary disputes are settled. *Module:* 21.

**Prior inconsistent statement.** *Plain:* something the witness said before that contradicts their testimony now. *Legal:* an impeachment tool with its own foundation requirements. *Module:* 22.

**Private place.** *Plain:* somewhere a person reasonably expects not to be watched or recorded. *Legal:* MCL 750.539d separately criminalizes installing or using a device to observe or record in a private place — **a distinct offense from eavesdropping under MCL 750.539c**. *Source:* [MCL 750.539d](https://www.legislature.mi.gov/Laws/MCL?objectName=MCL-750-539D). *Module:* 9.

**Proofs.** *Plain:* the evidence phase of a trial. *Legal:* the part between opening and closing where testimony is taken and exhibits are admitted. *Module:* 23.

**Proposed order.** *Plain:* the draft order you hand the court after a ruling. *Legal:* subject to settle-order / objection-to-entry practice; **read the other side's proposed order line by line before it enters** `⚠ verify current rule text`. *Do not confuse with:* the judge's oral ruling. *Module:* 25.

**Published / unpublished opinion.** *Plain:* whether a Court of Appeals decision counts as binding law. *Legal:* published opinions bind; **unpublished opinions are persuasive only** under MCR 7.215(C)(1) and must be labeled as such — *Grew v Knox* is the worked example. *Module:* 18.8.

**Rebuttal.** *Plain:* evidence answering what the other side just put in. *Legal:* limited in scope to the matters raised; it is not a second chance to present your case in chief. *Module:* 23.

**Recorded recollection.** *Plain:* a written note used when the witness no longer remembers. *Legal:* MRE 803(5); narrow, and it is **read into the record rather than admitted as an exhibit** by the proponent. *Do not confuse with:* refreshing recollection under MRE 612, which is a different mechanism with a different result. *Module:* 6, 8.

**Refreshing recollection.** *Plain:* looking at something to jog your memory, then testifying from memory. *Legal:* MRE 612; the item used is **not** thereby admitted, and the other side may inspect it. This is the custody journal's most common legitimate courtroom use. *Do not confuse with:* recorded recollection. *Module:* 6, 22.

**Register of actions.** *Plain:* the court's list of everything filed in your case. *Legal:* the docket; needed for the appellate record and for reconstructing deadlines in the FM.0 exercise. *Module:* 28.6.

**Registration of an out-of-state order.** *Plain:* making another state's custody order enforceable in Michigan. *Legal:* a UCCJEA process; **registration is not the same as modification**, and Michigan may lack power to modify. *Module:* 3.

**Relevance.** *Plain:* whether the fact makes something the judge must decide more or less likely. *Legal:* MRE 401/402, subject to MRE 403 exclusion where the probative value is substantially outweighed by unfair prejudice, confusion, or waste of time. **"Everything bad she ever did" loses on relevance and on 403.** *Module:* 6.

**Relocation.** *Plain:* moving the child a significant distance. *Legal:* governed by MCL 722.31; the analysis is sequenced — five factors by preponderance, then whether the move alters the ECE, then clear and convincing best interests if it does, then a modified schedule. *Do not confuse with:* a parent moving without the child; a school-choice dispute. *Module:* 27.

**Review interval.** *Plain:* a date you set to re-examine the order and the support figure. *Legal:* an operational discipline, not a legal requirement; it replaces reactive filing. *Module:* 29.7.

**Ruling.** *Plain:* the judge's decision on an objection or a motion. *Legal:* **get one on the record** — an objection without a ruling preserves nothing for appeal. *Module:* 22, 28.6.

**Safety override.** *Plain:* safety comes before every procedural step in this book. *Legal:* not a legal doctrine; a design rule of this treatise — no contact, mediation, exchange, or service instruction supersedes a PPO, a no-contact order, law-enforcement direction, or an individualized safety plan. *Module:* §0.3, FM.2, and every DV interstitial.

**Self-help withholding.** *Plain:* keeping the child, or stopping support, because the other parent broke the order. *Legal:* **not a remedy.** Support and parenting time are independent; self-help exposes the reader to contempt, sanctions, and factor (j) and (f) damage. *Module:* 26.7.

**Self-regulation.** *Plain:* managing your own reactions. *Legal:* not a legal term; it is factor (g) risk management, deadline protection, and child protection at once. *Module:* 29.5.

**Settlement.** *Plain:* an agreement resolving some or all issues. *Legal:* becomes enforceable when memorialized and entered; check authority to settle, voluntariness, completeness, and calendar operation before assenting. *Do not confuse with:* a stipulation on a single point; mediation itself. *Module:* 20.

**Sole custody.** *Plain:* one parent has the decision-making authority, the residence, or both. *Legal:* MCL 722.26a still requires the court to consider joint custody on request and to state reasons for denying it. **Requesting sole custody merely because conflict exists may reward conflict manufacture and can expose the requester under factor (j).** *Do not confuse with:* the other parent losing parenting time — sole legal custody does not by itself change the schedule. *Module:* 2.6, 2.7.

**Sponsoring witness.** *Plain:* the person who gets your exhibit into evidence. *Legal:* required for nearly every exhibit in Michigan because there is no self-authentication route for electronic records; identify the sponsoring witness **before** you subpoena the record. *Module:* 7, 10.6.

**State of mind (MRE 803(3)).** *Plain:* evidence of what someone was feeling or intending at the time. *Legal:* a hearsay exception for a then-existing mental, emotional, or physical condition; **one of the legitimate routes for a child's statement now that MRE 803A is off the table** — but it proves the child's state of mind, not the truth of what the child described. *Module:* 6, 18.5.

**Subject-matter jurisdiction.** *Plain:* whether this court has power over this kind of case at all. *Legal:* cannot be waived or agreed to; a UCCJEA defect is not cured by both parents proceeding. *Do not confuse with:* venue; personal jurisdiction. *Module:* 1, 3.

**Supervised parenting time / supervised exchange.** *Plain:* time or handoffs that happen with a third party present. *Legal:* a bridge remedy where safety or allegations are live; provider availability and cost are `ℹ LOCAL PRACTICE` facts. *Module:* 17.8, Appendix G.

**Surcharge.** *Plain:* an added charge on unpaid support. *Legal:* part of the arrearage machinery; runs against the reader as readily as for them. *Module:* 24.4.

**Term sheet.** *Plain:* a written list of every point an agreement must cover. *Legal:* the tool that prevents an agreement too vague to enforce; it must cover custody, schedule, holidays, exchanges, decision-making, information access, support, tax, fees, dispute resolution, and effective date. *Module:* 20.

**Theory of the case.** *Plain:* the one sentence that explains why you should win. *Legal:* not a filing; the organizing device that keeps proofs relevant and closings factor-based. *Module:* 11.

**Trial brief.** *Plain:* a short written document telling the judge the law and what you will prove. *Legal:* structured as **standard → evidence → finding → relief**; some judges set their own deadline for it `ℹ`. *Do not confuse with:* a motion brief; a closing argument. *Module:* 21.

**Uninsured health-care expense.** *Plain:* medical costs insurance did not cover. *Legal:* allocated separately from the ordinary medical expense built into the base support figure. *Do not confuse with:* OME. *Module:* 24.1.

**Weekly review.** *Plain:* a set time each week to look at the calendar, the file, and what is due. *Legal:* the core habit of the litigation operating system; it is how deadlines in Appendix A actually get met. *Module:* 29.2.

**Witness preparation.** *Plain:* getting a witness ready. *Legal:* legitimate preparation covers process, topics, and expectations. **It never covers content, and it never applies to the child.** *Do not confuse with:* coaching. *Module:* 22.

---

**Glossary drafting instruction:** this appendix is written **before** any module. Every module's item 12 (glossary terms) must point to an entry that already exists here, and every module must use these definitions **verbatim**. If drafting a module reveals a needed term that is missing, the glossary is amended first and the amendment is logged in Appendix M.

## APPENDIX O — CROSS-REFERENCE MAP (CONCEPT OWNERSHIP)

To prevent duplicated or conflicting explanations, each concept is **owned** by one module and referenced — not re-explained — elsewhere.

| Concept | Owned by | Referenced in |
|---|---|---|
| 48-hour triage router | FM.0 | Every module's route tag |
| Pathway taxonomy (ten roads) | M1 | All |
| ECE and the *Hayes* trap | M2.1 | FM.0, M11, M13, M14, M17, M20.1, M27 |
| Burdens of proof | M2.2 | M13, M23, M27 |
| *Vodvarka* / *Shade* thresholds | M2.3 | M11, M27 |
| Best-interest factors (MCL 722.23) | M2.4 | M11, M15, M18, M23 |
| Parenting-time factors (MCL 722.27a(7)) | M2.5 | M18, M25, M26 |
| Best-Interest Evidence Matrix | M2 | M10, M15, M16, M18, M20, M21, M23 |
| Genesee filing mechanics, praecipe, fees | M4 | M12, M14, M16, M26 — **single master location; v1 duplicated these across 2.3, 6.2, 6.3, 6.4** |
| Where the MRE apply | M5 | M15, M16, M22 |
| Hearsay and MRE 801(d)(2) | M6 | M8, M18, M22, M26 |
| MRE 803A inapplicability | M6 | M18.5 |
| Authentication and foundation scripts | M7 | M10.6, M16, M22, Appendix C |
| Custody journal (and its limits) | M8 | M15.3, M18, M19.4, M22 |
| Recording law and the Do-Not-Do list | M9 | M8, M17, Appendix J |
| Subpoena two-track rule | M10.4 | M16, M17.4, M21, M22 |
| MCR 2.302(A)(4) disclosure exemption | M10.2 | M21 |
| When not to file / sanctions exposure | M12.1 | M14, M16.6, M26 |
| 14-day ex parte objection | M14.2 | FM.0, Appendix A |
| FOC report paradox (*Duperon*) | M15.4 | M16, M19.1, M23 |
| MCR 3.215(F)(2)(c) new-evidence bar | M16.5 | FM.0, M21, M22 |
| Parallel-proceeding firewall | M17.2 | M8, M9, M18 |
| CPS Category V and three-unfounded-reports | M17.3, M17.5 | M18 |
| PPO precedence over custody orders | M17.6 | M20, M25, M26 |
| Alienation-as-conduct framing | M18.1 | M2.4, M11, M23 |
| Evaluation-order hearsay-waiver trap | M19.3 | M11.5, M20.1 |
| LGAL vs. GAL vs. evaluator | M19.1 | M15, M18.5 |
| MCSF and the 18 deviation factors | M24.1, M24.3 | Appendix I, M25 |
| Form 8332 limits | M24.5 | M25 |
| MCR 3.206(D) fee routes | M24.6 | M4.5, M10.7, M12.1, M26 |
| Order-clause specificity | M25 | M20.1, M26.1, Appendix E |
| Make-up parenting time mechanics | M26.4 | FM.0, Appendix A |
| 100-mile rule and the five factors | M27 | M11, M25 |
| 21-day appeal cliff and the leave asymmetry | M28.1–28.2 | FM.0, M22, M23 |
| Litigation operating system / factor (g) risk | M29 | M8, M11.3, M12.1, M18 |
| Two-tier flags and three hard labels | §0.3, FM.3 | All |

---

*End of master outline v2. This document, with `custody_guide_plan.md` (as amended by §0.6 and Module 28's scope reversal) and `custody_guide_research.md`, constitutes the complete drafting specification. No module may be drafted until Appendix N is written and the §0.8 open items and the Module 9 attorney-verification flag are resolved or visibly carried forward.*

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — final-review fix._
