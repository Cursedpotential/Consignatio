# Critical Review — `custody_guide_outline_v2.md`

**Date:** August 9, 2026
**Reviewer posture:** the three council reports reviewed **v1**. Nobody has reviewed the v2 rebuild. This review checks v2 against the primary text archived in `sources/primary/`, and against v2's own acceptance tests.
**Verdict:** **v2 is close to draftable and should not be rebuilt again.** It has one class of defect that must be fixed first — the deadline table and several rule cites encode superseded or wrong text — plus a structural gap in how the acceptance tests handle unverifiable local facts.

---

## 1. What v2 gets right

Stated plainly, because the defect list below is long and the document deserves the credit.

- **The sequencing fix is correct and is the single most important thing in the rebuild.** Moving evidence ahead of strategy, and pathway triage ahead of everything, addresses a real failure mode. Part II's framing — "evidence is a spine, not a chapter" — is right.
- **The council conflicts are preserved rather than resolved by fiat.** Module 9's three-theory recording section, with a `🔒 ATTORNEY MUST VERIFY` gate that converts to a signed verification note before publication, is a genuinely good mechanism. Most drafting specs would have picked one theory and buried the disagreement.
- **The 12-point contract and 12 acceptance tests are real gates**, not aspiration — and §2 below shows the tests actually catching v2's own errors, which is the strongest evidence they work.
- **Appendix A exists as a populated 24-row table**, not a placeholder. Appendices C, D, E, N are specified to a level a drafter can execute.
- **Appendix N (231 glossary terms, five fields each) is already written**, which removes the definitional-drift risk the council flagged.
- **The adversarial-fairness discipline is built in structurally** — Module 11's "what your opponent will say about you," the factor (g) self-audit, Module 12.1's "when not to file." Most pro se guides have no such thing.
- **Module 26 is excellent** and correctly identified as "the tool this reader will use most."

---

## 2. Defect class 1 — Appendix A contains errors that would cost a reader

Appendix A is load-bearing by the outline's own rule: *"No deadline may appear in prose without a corresponding row here."* Checked row by row against `sources/primary/michigan-court-rules_2026-07-31.pdf` and `local-court-rules-circuit_2025-06-01.pdf`:

| # | Row | Problem | Correct position |
|---|---|---|---|
| **A-1** | "**7 days / 3 days** — motion filed / response filed before hearing \| **MCR 2.119(C)(4)**" | ~~"The current rule has no (C)(4)"~~ — **that half of this finding was wrong (revised the same evening; see ledger C-3): (C)(4) exists and is the *filing* deadline (7/3 days).** The surviving defect: the original row treated (C)(4) as the *only* deadline and omitted the **service** periods entirely. | Appendix A now carries **both**: **MCR 2.119(C)(1)** service — 9 days by mail / 7 by delivery ((C)(2): response 5/3) — **and** the **(C)(4)** filing row. A reader who mails a motion 7 days out satisfies (C)(4) but is **late on (C)(1) service**. |
| **A-2** | "**9 days** — service of custody motion \| Genesee custody-motion packet `ℹ` (**stricter than the MCR rule**)" | Not a local variance. 9 days **is** the statewide mail branch. Genesee LCR 2.119 contains **no timing provision at all** (verified). | Merge into A-1 as the mail branch. Delete the "stricter than" claim. Fails **Acceptance Test 6**. |
| **A-3** | "**7 days** — praecipe filed before hearing \| Genesee local practice ([Local Court Rules — Circuit](…498ad4…))" | Two faults: the URL segment `498ad4` is stale (working: `492c71`), and **the LCR does not contain a praecipe provision** — Genesee's LCR 2.119 covers only concurrence certification and proposed orders. Wayne has an LCR praecipe rule; Genesee does not. | Re-source to the actual Genesee document that imposes it, or demote to unverified local practice pending clerk confirmation. |
| **A-4** | "**21 days** — referee issues findings \| MCR 3.215(**E**)" and "**21 days** — written objection \| MCR 3.215(**E)(1)**" | Subrules wrong and effectively swapped. | Referee's 21 days = **(E)(1)**. Objection = **(E)(4)**, and it requires a written objection **and notice of hearing**. |
| **A-5** | "MCR 3.207(B) `⚠ in flux, ADM 2021-27`" (three rows) | Not in flux. The archived text is stamped **Chapter Updated May 1, 2026** and already incorporates the ECE-pleading amendments. | Clear the flag; cite subrules precisely — objection **(B)(5)(b)**, motion **(B)(5)(a)**. |
| **A-6** | "**21 days** — claim of appeal \| [MCR 7.204(A)(1)(a)](…courtrules.net/…**rule-7-202**)" | Link anchors to rule 7-202, not 7-204. | Re-anchor to the primary PDF. |

**Missing rows** — each is a clock with a forfeiture consequence, so each is `⚠ TIME-CRITICAL` by v2's own flag rule:

1. **7 days** — objection to the accuracy or completeness of a **proposed recommended order**, MCR 3.215(E)(3)(d). Absent entirely, and it is the earliest referee-stage trap.
2. **21 days** — evidentiary hearing the court **must** schedule after an ex parte order that could alter an ECE, MCR 3.207(B)(1)(b).
3. **21 days** — request a hearing on proposed **modification of parenting time** after a contempt notice, MCL 552.644(1)(b).
4. **28 days** — the court **shall resolve** an ex parte parenting-time dispute after a hearing is requested, MCL 722.27a(14). A statutory clock with no MCR analogue.
5. **14 days** — motion to modify or rescind a **PPO**, MCL 600.2950(13), and the **14-day** hearing under (14) (**5 days** where a firearm prohibition affects a respondent who must carry for employment).

---

## 3. Defect class 2 — load-bearing rule text cited to a commercial mirror

v2 cites **courtrules.net** for MCR 3.215, 3.210, 2.305, 2.506, and 7.204 — that is, for the referee rule, the new-evidence bar, and the subpoena two-track rule, the three findings the synthesis called highest-weight. It also cites the MRE at path segment `492ca5`; the working segment is `498acb`.

This was a reasonable workaround when the primary host appeared robots-blocked. **It no longer is** — the official PDFs retrieve with a browser User-Agent and are now archived in `sources/primary/`. Every load-bearing citation should be re-anchored to the primary document, with the mirror kept only as a convenience link. Leaving it as-is means the treatise's most important propositions rest on a commercial secondary source whose text v2 never independently checked.

The same applies to Justia links used for MCL 552.644 and 552.645 while `legislature.mi.gov` links are used elsewhere — inconsistent sourcing for statutes of equal weight.

---

## 4. Defect class 3 — Acceptance Test 2 cannot pass, and v2 has no exception mechanism

**Test 2:** *"Every legal claim has a primary source and a verification date."*
**§0.8:** every Genesee local fact is unverifiable and must go to a human.

These cannot both hold. Under a strict reading, **no Genesee module can ever ship** — which would gut the guide's entire reason for existing, since local specificity is what a pro se parent cannot get elsewhere.

v2 needs a fourth disposition alongside its flags: a **provisional-pass** state meaning *"asserted, sourced to the best available local document, explicitly marked as requiring clerk confirmation, and carrying the date it was last checked."* Without it, either the tests get quietly ignored during drafting — which destroys their force everywhere else — or the guide never ships. This is the single most consequential structural gap in v2.

Related: **Test 5** ("the official form is linked and its current revision checked") has no mechanism for the form-revision drift the toolkit audit found between the Genesee referee-objection packet and statewide FOC 68.

---

## 5. Defect class 4 — substantive gaps my verification pass surfaced

None of these are in v2. Each is verified primary text.

| # | Missing | Where it belongs |
|---|---|---|
| **G-1** | **MCR 3.207(B)(1)(a)** — a verified pleading or affidavit seeking an ex parte custody/parenting-time order **or a change of custody or parenting time** *must* plead ECE facts and either non-alteration or clear-and-convincing best-interest facts. A pro se motion omitting this is facially deficient. | Module 14.1, Module 12 |
| **G-2** | **Genesee LCR 2.119** — the concurrence certificate binds "the party in propria persona," and **a proposed order must be attached to and served with** every motion. This is exactly the local insider knowledge the guide exists to supply. | Module 4.3, Module 12, filing checklist |
| **G-3** | **MCR 3.218(A)** — "Friend of the court records are **not subject to a subpoena** issued under these Michigan Court Rules." Module 10.5 sends readers after records without this. | Module 10.5, Module 15 |
| **G-4** | **MCR 3.219 is "Dissemination of a Professional Report"** — and gives parties the right to **file objections to the report before a decision is made**. v2 inherits research §12's mislabel of it as FOC file access. | Module 15, Module 19 |
| **G-5** | **MCL 722.27a(7)(d) and (h)** — likelihood of **abuse of a parent** from the exercise of parenting time, and **detention with intent to retain or conceal**. v2's Module 2.5 carries only (f) and (g). (h) is the most on-point provision in the statute for withholding a child. | Modules 2.5, 18, 26 |
| ~~**G-6**~~ | ~~MCR 3.215(F)(2)'s mandatory floor is missing from Module 16.5~~ — **WITHDRAWN, August 9, 2026. This finding was wrong.** Module 16.5 already states it correctly: "The court **must** allow the parties to present live evidence — but under **MCR 3.215(F)(2)** it may, in its discretion…" and then lists (a), (b), and (c). Appendix N's "de novo hearing" entry states it correctly too. I read the module's `⚠⚠` heading and the "save your best evidence" warning and asserted the omission without checking the body text. The outline was right; the review was wrong. | — |
| **G-7** | **MCL 552.641(2)(c)** — the FOC may decline where the order "does not include an enforceable provision." Module 26.1 gestures at this; the statutory hook makes it the strongest argument in the book for Module 25's specificity discipline. | Modules 25, 26.1 |
| **G-8** | **MCL 552.644(3)** — the court **shall state on the record** why it is not imposing a listed sanction; and "good cause" is statutorily defined to include **child or party safety**. The first is a preserved appellate issue handed to the reader; the second is the other parent's built-in defense. | Module 26.5 |
| **G-9** | **The consent-gate inventory.** v2 warns about the ECE trap and hearsay waivers separately. They are one pattern: MCR 3.207(C)(2), MCR 3.215(E)(8), MRE 1101(b)(9) + *Duperon*, evaluation appointment orders, MCL 552.505a(2). Every template a reader might **sign** — not just file — needs a "what you give up by signing this" block. Suggest adding this as **contract item 9(b)**. | Module 11, Appendices D and E |

---

## 6. Defect class 5 — feasibility

v2 specifies 29 modules, each of which must satisfy a 12-point contract and pass 12 acceptance tests, plus 15 appendices, and Appendices C and D alone call for roughly 19 verbatim foundation scripts and 22 annotated model documents.

There is no sequencing plan, no effort estimate, and no definition of a shippable subset. The realistic failure mode for v2 is not a dangerous book — the gates are good enough to prevent that — it is **a book that never gets finished**, or one drafted at uneven depth as fatigue sets in, with the late modules thinner than the early ones.

**Recommendation:** define a **Volume 1** that can ship on its own. The natural cut is the reader's actual first 60 days: Front Matter, Modules 1–2, 4–10, 12–16, 26, and Appendices A, C, N. That is coherent, covers the 48-hour router's most common entry points, and defers trial practice, support, domicile, and appeals to Volume 2. Nothing about the architecture is lost, and the highest-value material reaches a reader years sooner.

---

## 7. Smaller notes

- **§0.8 lists *Vodvarka* and *Shade* citations as unverified.** Both are now verified (ledger §4). *Vodvarka* is **2003** — CourtListener's `dateFiled` of 2004-02-19 is a publication-release artifact. Record this so a future editor does not "correct" it.
- **Module 24.3's 18 deviation factors** are the best-sourced passage in the document. Use it as the model for how every verified list should look.
- **The `⊗ COUNCIL CONFLICT` device is good but has no closure procedure.** Each conflict needs a named owner and a resolution deadline, or they will still be open at publication.
- **Module 9's `🔒 ATTORNEY MUST VERIFY` gate should be generalized** — it currently exists only for recording. The same mechanism should cover every Genesee local fact and every template.
- **Test 12 (maintenance) says time-sensitive facts live in Appendix M**, but Appendix M is one line. Given how much of this guide is time-sensitive, Appendix M needs the same treatment Appendix A got.

---

## 8. Bottom line

Do **not** rebuild. v2's architecture is sound and the council's structural criticisms of v1 were addressed properly.

Before drafting begins, in this order:

1. **Fix Appendix A** — corrections A-1 through A-6 and the five missing rows. It is the most dangerous artifact in the book because readers will trust it most.
2. **Re-anchor load-bearing citations** to `sources/primary/`, and apply corrections C-1 through C-6 from the verification ledger.
3. **Add the provisional-pass disposition** so the acceptance tests survive contact with unverifiable local facts.
4. **Fold in G-1 through G-9.**
5. **Define Volume 1** and sequence it.

Items 1–4 are edits to a document that already exists and are perhaps a day of work. Item 5 is the decision that determines whether this project ever reaches a reader.
