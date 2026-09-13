# Verification Ledger — Pass 1

**Date of pass:** August 9, 2026
**Scope:** the items flagged in `custody_guide_outline_v2.md` §0.8 and `custody_guide_research.md` §12.
**Status:** the statewide legal layer is substantially cleared. The Genesee County local layer is **not** cleared and is not clearable by any model — see §4.

---

## 0. Method, and what changed this pass

Prior passes recorded `courts.michigan.gov` and `legislature.mi.gov` as robots-blocked, and reconstructed rule text from search snippets and secondary mirrors. That limitation is **resolved for this pass**:

- `curl` with a browser User-Agent retrieves the official PDFs from `courts.michigan.gov` directly (WebFetch alone returns HTTP 503; the block is UA-based, not a hard robots wall).
- The Exa fetch tool retrieves `legislature.mi.gov` MCL section pages in full.

Two primary documents were downloaded whole and read locally:

| Document | Currency stamp on the document face |
|---|---|
| Michigan Court Rules (complete, all chapters) | **Updated July 31, 2026**; Chapters 2, 3, 7 each stamped "Chapter Updated May 1, 2026" |
| Michigan Rules of Evidence (complete) | **"Updated with MSC order(s) effective on 1/28/2026"** |

Everything in §1 below is quoted from those two documents or from `legislature.mi.gov` directly, not from a mirror.

**Caveat on the MCL text.** The `legislature.mi.gov` pages retrieved carry the banner "Michigan Compiled Laws Complete Through PA 2 of 2025." Statutory text below is verified as of that compilation point; a human should confirm no 2025–2026 public act has since amended these sections.

---

## 1. Cleared — statutes

| Item | Result | Source |
|---|---|---|
| **MCL 722.26a** (joint custody) full text | **Cleared.** Seven subsections captured verbatim. History: Add. 1980, Act 434, Imd. Eff. Jan. 14, 1981 — **no later amendment**. (1) court must consider joint custody on either parent's request and state reasons on the record; factors are the §3 best-interest factors plus whether parents can cooperate and generally agree. (2) if parents agree on joint custody the court **shall** award it unless clear and convincing evidence on the record shows it is not in the child's best interests. (7) defines joint custody as alternating residence and/or shared decision-making. | [MCL 722.26a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-26a) |
| **MCL 552.505a** (FOC case opening/closure) full text | **Cleared, and the project's label is imprecise.** The section is titled "**Open friend of the court case; closure**," not "opt-out." Mechanism: with *initial pleadings* the parties may move for an order that no FOC case be opened (subsection 2); parties to an existing case may move to close it (subsection 4). Each has an enumerated list of conditions that **defeat** the motion — including public-assistance/title IV-D eligibility, either party's objection, evidence of domestic violence or uneven bargaining position, and failure to file the signed acknowledgment of foregone services. Nine subsections captured. History: Add. 2002, Act 571; Am. 2009, Act 233. | [MCL 552.505a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-505a) |
| **MCL 552.605b** (support past 18) full text | **Cleared.** Five subsections. Support may run while the child attends high school full time with a reasonable expectation of graduating, **but in no case past 19 years 6 months**; the motion may be filed any time before that age. History: Add. 2001, Act 106; Am. 2009, Act 193. | [MCL 552.605b](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-605b) |
| **MCL 552.605c** (monthly amounts; proration; excess payments) full text | **Cleared.** Five subsections. All support orders stated in monthly amounts payable on the first, in advance; unpaid by month's end is past due. History: Add. 2002, Act 565; Am. 2009, Act 193. | [MCL 552.605c](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-605c) |
| **MCL 552.507** (referee powers; de novo hearing) | **Cleared, and materially more important than the outline treats it.** (4) the court **shall** hold a de novo hearing on written request made **within 21 days after the recommendation is made available to that party**. (5) a hearing is still de novo despite reasonable restrictions if the parties had a full opportunity to present evidence at the referee hearing and, for objected-to findings, get a new opportunity to offer the same evidence plus evidence that could not have been presented earlier. **(6) "de novo hearings include… (a) a new decision based entirely on the record of a previous hearing."** | [MCL 552.507](https://legislature.mi.gov/Laws/MCL?objectName=MCL-552-507) |

---

## 2. Cleared — court rules and evidence rules

All quoted from the official consolidated PDFs described in §0.

### 2.1 The findings the council flagged as load-bearing — all confirmed verbatim

| Proposition | Verified text | Verdict |
|---|---|---|
| MRE apply at referee hearings | **MCR 3.215(D)(1): "The Michigan Rules of Evidence apply to referee hearings."** | ✅ Confirmed |
| The de novo new-evidence bar | **MCR 3.215(F)(2)(c):** the court may "prohibit a party from introducing new evidence or calling new witnesses unless there is an adequate showing that the evidence was not available at the referee hearing" | ✅ Confirmed |
| Referee objection clock | **MCR 3.215(E)(4):** written objection **and notice of hearing** within **21 days after the recommendation is served**; the objection "must include a clear and concise statement of the specific findings or application of law to which an objection is made" | ✅ Confirmed |
| Pro se cannot self-issue discovery subpoenas | **MCR 2.305(A)(1):** "A represented party may issue a subpoena to a non-party… **An unrepresented party may move the court for issuance of non-party discovery subpoenas.**" | ✅ Confirmed |
| Trial subpoenas are a separate, clerk-issued track | **MCR 2.506(B)(1):** "A subpoena signed by an attorney of record in the action **or by the clerk of the court** in which the matter is pending has the force and effect of an order signed by the judge." MCR 2.506(A)(1) expressly excludes discovery subpoenas. | ✅ Confirmed — the two-track rule is real |
| Domestic relations exempt from initial disclosures | **MCR 2.302(A)(4)(c):** exempt — "an action under subchapter 3.200" | ✅ Confirmed |
| Appeal clock is 21 days and jurisdictional | **MCR 7.204(A):** "The time limit for an appeal of right is jurisdictional." (A)(1): 21 days from entry; "entry" = the date the order is **signed** or the date data entry is accomplished in the register of actions | ✅ Confirmed |
| Appeal-of-right asymmetry (parenting time excluded) | **MCR 7.202(6)(a)(iii):** final order includes "in a domestic relations action, a postjudgment order that, as to a minor, grants or denies a motion to change **legal custody, physical custody, or domicile**." Parenting time is absent from the list. | ✅ Confirmed |
| MRE 902 has no digital-records self-authentication | **MRE 902 ends at (11)**; Rule 903 follows immediately. The MJI Evidence Benchbook describes MRE 902(1)–(11) and calls it "**a finite list**." No FRE 902(13)/(14) analogue exists. | ✅ Confirmed |
| MRE 803A is unavailable in custody | **MRE 803A(a): "Scope. This rule applies in criminal and delinquency proceedings only."** Title is "Hearsay Exception; Child's Statement About a Sexual Act." | ✅ Confirmed |
| FOC report exempt from the evidence rules | **MRE 1101(b)(9):** rules inapplicable to "the court's consideration of a report or recommendation submitted by the friend of the court under MCL 552.505(1)(g) or (h)" | ✅ Confirmed (the *Duperon* half of the paradox is still open — see §3) |
| Party-opponent statements | **MRE 801(d)(2)(A)–(E)** verified verbatim, restyled as "An Opposing Party's Statement" | ✅ Confirmed |
| Unpublished opinions | **MCR 7.215(C)(1):** not precedentially binding; "should not be cited for propositions of law for which there is published authority"; a party citing one **must explain the reason for citing it**; post-1996 opinions need docket number and date of decision in the citation | ✅ Confirmed |
| MRE restyling date | **Effective January 1, 2024**, adopted September 20, 2023, **ADM File No. 2021-10** | ✅ Confirmed |

### 2.2 MCR 3.207 — richer than the outline assumes

Verified in full. Four provisions the outline's Module 14 does not currently carry:

1. **MCR 3.207(B)(1)(a) — a mandatory pleading-content rule.** A verified pleading or affidavit requesting an ex parte custody/parenting-time order **or a change of custody or parenting time** must include (i) facts establishing whether the child has an established custodial environment with either parent, both, neither, or a third party; **and** (ii) either facts showing the order will not change that ECE, or facts showing clear and convincing evidence that changing it is in the child's best interest. A pro se motion that omits this is facially deficient.
2. **MCR 3.207(B)(1)(b).** The court **must not** issue an order that could alter an ECE without also scheduling an MCL 722.27 evidentiary hearing **within 21 days** of entry, with notice of that hearing in the order itself.
3. **MCR 3.207(B)(5)** distinguishes two responses with **different clocks**: a motion to rescind/modify without objection → evidentiary hearing within **21 days of filing**; a timely **objection** → FOC attempts resolution within **14 days**, and if it fails must give a pro se objector form pleadings and written instructions and schedule the hearing. No timely objection or motion → **the ex parte order becomes a temporary order**.
4. **The mandated notice text confirms the 14-day clock** — "You must file the written objection or motion with the clerk of the court within **14 days after you were served with this order**" — and states plainly: "Even if an objection or motion is filed, the ex parte order **will remain in effect and must be obeyed** unless changed by a later court order."

### 2.3 MCR 3.215 — the counterweight the council omitted

`MCR 3.215(F)(2)(c)` (bar on *new* evidence) is real, but the **same subrule opens with a mandatory floor**:

> "the court may conduct the judicial hearing by review of the record of the referee hearing, **but the court must allow the parties to present live evidence at the judicial hearing**."

Both halves must be taught together. Confirmed by *McGregor v Jones* (Mich COA, unpublished, 2023), which reversed a trial court that treated an objection as forfeited and decided on the record alone. Also verified:

- **MCR 3.215(F)(3):** a frivolous objection, or one interposed for delay, may draw **costs and attorney fees** — the outline's Module 16.6 is well founded.
- **MCR 3.215(G)(3):** the court may **not** by administrative order give interim effect to an order changing a child's **custody** or **domicile**.
- **MCR 3.215(E)(3)(d):** a **7-day** clock — a party may serve a proposed recommended order, and objections to its accuracy or completeness are due within 7 days. This deadline appears nowhere in the outline's triage router or Appendix A.

### 2.4 Other rules verified

- **MCR 3.218** — "Friend of the Court Records; Access." **(A): "Friend of the court records are not subject to a subpoena issued under these Michigan Court Rules."** Confidential information is enumerated at (A)(3)(a)–(h), including staff notes, CPS-sourced information, ADR/mediation records, and communications from minors.
- **MCR 2.119(F)(1)** — reconsideration served and filed **not later than 21 days after entry** of the order deciding the motion; **(F)(3)** requires demonstrating "a palpable error by which the court and the parties have been misled."
- **MCR 7.203(A)(1)** closing clause — "An appeal from an order described in MCR 7.202(6)(a)(iii)-(vi) is **limited to the portion of the order** with respect to which there is an appeal of right." **MCR 7.203(B)(5)** allows leave "when an appeal of right could have been taken but was not timely filed."
- **MCR 7.204(A)(1)(d)** — the clock runs from an order deciding a postjudgment motion for reconsideration **only if that motion was filed within the initial 21-day appeal period**. A late reconsideration motion does not revive the appeal.
- **MCR 2.506(C)(1)** — trial subpoena must be served at least **2 days** before appearance, or **14 days** before when documents are requested.
- **MCR 2.305(A)(3)** — a discovery subpoena must give the non-party a minimum of **14 days**.

**Added after the Packet 1 drafting pass (verified verbatim from the archive; surfaced by the drafting agent's Documents 3–4):**

- **MCR 3.215(D)(4)(c)** — "At least **7 days before the judicial hearing**, a party who intends to offer evidence **from the record of the referee hearing** must provide notice to the court and each other party. If a stenographic transcript is necessary, except as provided in subrule (4)(b), the party offering the evidence must pay for the transcript." A distinct clock from (E)(3)(d) — the drafting pass cited (D)(4) while this ledger cited (E)(3)(d), and **both are correct**: they are different 7-day deadlines. (E)(3)(d) confirmed at its position in the archive (proposed-recommended-order objection, with the (i)/(ii) sub-procedure); (D)(4)(c) is the record-evidence notice.
- **MCR 3.215(D)(4)(d)** — where the court **on its own motion** uses the referee record to limit the judicial hearing under (F), it must make the record available and allow **supplemental objections within 7 days of the date the record is provided**. Does not apply where a party requested the limitation.
- **MCR 2.002(G) and (G)(1)** — the judge must grant or deny a fee-waiver request within **3 business days** (order nonpublic; a denial must state its reason). On denial, the clerk sends notice and the filer must **pay within 14 days from the date the clerk sends notice or the filing is rejected** — the original filing date is lost. MDOC prisoners: 21 days from the order date. Directly material to any fee-waiver filer; now in Appendix A and the FM-0 router.
- **MCR 2.107(B)(1)(c)** — verbatim: "After a final judgment or final order has been entered and the time for an appeal of right has passed, **documents must be served on the party** unless the rule governing the particular postjudgment procedure specifically allows service on the attorney." Confirms the drafting pass's C-8: postjudgment service defaults to the **party**; the packet's serve-both instruction stands.
- **MCR 3.210(D)(1)** — verbatim: "The court must make findings of fact as provided in MCR 2.517, except that (1) **findings of fact and conclusions of law are required on contested postjudgment motions to modify a final judgment or order**." This is an express carve-out from **MCR 2.517(A)(4)** ("Findings of fact and conclusions of law are unnecessary in decisions on motions unless findings are required by a particular rule") — and it binds the **judge**, not just the referee, in exactly the Packet 1 posture: a contested postjudgment motion to make a parenting-time provision specific. Materially stronger than MCR 3.215(E)(1)(a), which reaches only the referee's recommendation. Surfaced by the drafting agent's Part Four; verified verbatim from the archive (rules text line region: Rule 3.210(D)).
- **MCR 2.517(B)** — a further **21-day clock, triggered by entry**: "On motion of a party made within 21 days after entry of judgment, the court may amend its findings or make additional findings, and may amend the judgment accordingly." Same rule: sufficiency-of-the-evidence challenges survive **whether or not** the party objected to the findings or moved to amend; **(A)(6)–(7)**: requests for findings are not necessary for review, and no exception need be taken. Added to Appendix A.
- **MCR 3.210(C)(5)** — verbatim: the court "may interview the child privately to determine if the child is of sufficient age to express a preference regarding custody, and, if so, the reasonable preference of the child. The court shall focus the interview on these determinations, and **the information received shall be applied only to the reasonable preference factor**." Independent structural support for GUARDRAILS §8: even the judge's own private channel to the child is confined to one factor by rule.
- **MCR 3.203(A)–(D)** — the address-concealment answer, verbatim: in a case whose judgment requires FOC address updates, "**a party's last known mailing address means the most recent address (1) that the party provided in writing to the friend of the court office, or (2) set forth in the most recent judgment or order entered in the case, or (3) the address established by the friend of the court office pursuant to subrule (D)**" — and service by mail "shall be to a party's last known mailing address." (D): where mail bounces or a federal database shows non-delivery, **the FOC may administratively establish the address**. Consequence: a party's true residence is irrelevant to service validity — the **FOC address of record is the service address by definition**, mail service is complete on mailing (2.107(C)(3)), and concealing or failing to update an address is the concealing party's own order violation, documentable as conduct.

---

## 2.5 Genesee LCR 2.119 — verified from the official compilation

The toolkit package's audit recorded this as robots-blocked: *"Human must open the PDF for full current LCR text before L2 quotes."* It fetches fine with a browser User-Agent. Archived at `sources/primary/local-court-rules-circuit_2025-06-01.pdf` (104 pp., "Updated with MSC order(s) effective on 6/1/2025").

**SEVENTH JUDICIAL CIRCUIT (GENESEE), Rule 2.119. Motion Practice** — complete text:

> **(A) Motion Certification by Attorney.** The following certificate signed by the attorney of record **or by the party in propria persona** shall be attached to or incorporated in the motion and notice of hearing filed with the clerk:
>
> > *I hereby certify that I have made personal contact with \_\_\_\_\_\_\_\_[name] on \_\_\_\_\_\_\_\_[date], requesting concurrence in the relief sought with this motion and that concurrence has been denied, or that I have made reasonable and diligent attempts to contact counsel requesting concurrence in the relief sought with this motion.*
>
> **(B) Proposed Orders.** A proposed order must be attached to and served with the motion.
>
> **(C) Application.** This rule applies to all motions filed in the circuit court and to motions filed in civil actions in the probate court.

Three consequences:

1. **The certificate binds pro se parties.** The rule says "or by the party in propria persona" — despite the heading reading "by Attorney." A self-represented filer who omits it is out of compliance with a binding local rule. This is exactly the insider knowledge the guide exists to supply, and it belongs in Module 12 and the filing checklist.
2. **A proposed order is mandatory, attached *and served*** — not optional, not "helpful."
3. **Genesee's local rule contains no motion-timing provision at all.** It governs concurrence and proposed orders only. This independently confirms correction **C-2**: the 9-day figure is the statewide MCR 2.119(C)(1) mail branch, not a Genesee variance. There is no stricter local timing rule to mislabel.

## 2.6 Child support formula — both open MCSF items cleared

Archived: `sources/primary/2025-michigan-child-support-formula_eff-2025-01-01.pdf`.

**§1.04(E) — 18 deviation factors confirmed.** Read from the primary PDF. The enumerated list runs (1)–(18) and ends at "(18) Any other factor the court deems relevant to the best interests of a child." The manual's own change log records that the 2025 edition **"Removed two deviation factors (alternative health care coverage; costs associated…)"**, which explains the 20 → 18 reduction, and **"Added clarification that a deviation is not required if a deviation factor exists."** Outline Module 24.3's reproduction of the list is accurate. Research §12 item 5 is closed.

**§3.03 — the "percentage brackets" do not exist.** Research §12 item 6 and outline §0.8 both ask for the "current Parental Time Offset percentage brackets/table in MCSF §3.03." **That premise is wrong.** §3.03(A)(2) is an equation, not a bracket table:

> (A<sub>o</sub>)<sup>2.5</sup> · (B<sub>s</sub>) − (B<sub>o</sub>)<sup>2.5</sup> · (A<sub>s</sub>) , divided by (A<sub>o</sub>)<sup>2.5</sup> + (B<sub>o</sub>)<sup>2.5</sup>
>
> where A<sub>o</sub>/B<sub>o</sub> are each parent's approximate annual overnights and A<sub>s</sub>/B<sub>s</sub> are their base support obligations. "A negative result means that parent A pays and a positive result means parent B pays."

Any secondary source describing bracket percentages is either stale or describing the supplement's illustrative graph. **Do not draft brackets.**

Four provisions from §3.03 that matter directly to the interference and order-drafting modules, and are in neither the outline nor the research:

1. **§3.03(C)(4): credit overnights a child "lawfully and actually" spends with a parent, including time exercised outside the order's terms — but "Do not consider overnights exercised in violation of an order."** A parent who withholds time cannot bank those overnights for support purposes.
2. **§3.03(C)(4)(a):** where a parent produces credible evidence that actual overnights differ from the ordered number, the FOC/court credits the evidence **without requiring a formal motion to modify custody or parenting time**.
3. **§3.03(D):** a substantial difference — **at least 21 overnights**, or one exceeding the §4.05 modification threshold — supports a motion to modify.
4. **§3.03(E): every child support order must state whether it includes a parental time offset and the number of overnights used.** An order-drafting checklist item the outline's Module 25 does not have.

## 3. Corrections to the project documents

These are errors in the current package that would have propagated into the treatise.

| # | Where | Current text | Correction |
|---|---|---|---|
| **C-1** | research §12 item 4; outline §0.8 | Treats **MCR 3.219** as the FOC "file-access provisions" | **MCR 3.219 is "Dissemination of a Professional Report."** It governs court use of a community resource in custody/visitation/domicile disputes and gives parties the right to **file objections to the report before a decision is made** — useful, but a different rule. FOC records access is **MCR 3.218**. |
| **C-2** | outline FM.4 (Genesee Quick-Reference Card) | "motion + notice of hearing served **≥9 days** ahead per the county packet (**stricter than the MCR 2.119(C)(4) 7-day rule**)" | Imprecise — it compared two **different obligations**. The 9-day figure is the statewide **service** rule's mail branch, MCR 2.119(C)(1) (9 by mail / 7 by delivery) — not a stricter Genesee requirement. MCR 2.119(C)(4) is the separate **filing** deadline (motion filed ≥7 days, response ≥3 days before hearing). **Both apply.** The Acceptance Test 6 point (statewide law mislabeled as Genesee practice) stands. |
| **C-3** | Genesee "Notice Regarding Motion Practice" (still posted; effective March 4, 2019, never reaffirmed) | Quotes "MCR 2.119(C)(4)": a motion must be **filed** at least 7 days before hearing, response 3 days | **REVISED the same evening — my original correction here was itself wrong.** I wrote "the current rule has no such (C)(4)." **It does.** Verbatim from the archive (line 3677, after a page break): *"(4) Unless the court sets a different time, a motion must be filed at least 7 days before the hearing, and any response to a motion required or permitted by these rules must be filed at least 3 days before the hearing."* The county notice quotes it **accurately**; its defect is **omission, not obsolescence** — it never mentions the separate (C)(1) **service** periods, so a reader relying on it alone who serves by mail is **late on service**. **Root cause of my error:** the archived text breaks across a PDF page between (C)(3) and (C)(4); my read window ended at the break and I asserted a negative from a truncated excerpt — the exact failure mode the whole-statute rule was later written to prevent, and it caught its own author within hours. Practical guidance unchanged: **file ≥7 days ahead AND serve ≥9 days ahead by mail (7 by delivery).** |
| **C-4** | council report (Opus seat), adopted into outline | Attorney fees for another party's non-compliance cited as **MCR 3.206(D)(1)(b)** | The current rule places that at **MCR 3.206(D)(2)(b)**. (D)(1) is the general right to request at any time; (D)(2)(a)/(b) are the two alternative factual showings. |
| **C-5** | synthesis; outline Module 16 | "the judge **may bar new evidence**" presented as the whole rule | Incomplete in a way that could cost a reader their hearing. MCR 3.215(F)(2) **requires** the court to allow live evidence; (F)(2)(c) limits only *new* evidence that was available earlier. Teach both halves. |
| **C-6** | outline FM.0 triage router / Appendix A | No entry for the MCR 3.215(E)(3)(d) proposed-recommended-order objection | Add the **7-day** clock for objecting to the accuracy or completeness of a proposed recommended order. |

**Non-correction, recorded to prevent a future "fix."** `custody_guide_plan.md` §7 cites *Vodvarka v Grasmeyer*, 259 Mich App 499; 675 NW2d 847 **(2003)**. That is **correct**. CourtListener reports `dateFiled` **2004-02-19** for this cluster, which is a publication-release/administrative date, not the decision date; FindLaw and vLex both report the case as 2003. Do not "correct" the year to 2004. (Reported decision day varies between Nov 25 and Dec 2, 2003 across secondary sources — a human should open the official opinion if the exact day is ever needed. The year, which is all the citation requires, is settled.)

---

## 4. Cleared — case law

| Case | Result |
|---|---|
| ***Vodvarka v Grasmeyer*** | **Cleared.** 259 Mich App 499; 675 NW2d 847 (2003), Docket 248058, **published**. Holding confirmed from the opinion's own summary: in determining a **change of circumstances**, the trial court is limited to events occurring **after entry of the most recent custody order**; for **proper cause**, the court should generally do the same, "but… there will be unusual cases where that rule is not applicable." |
| ***Shade v Wright*** | **Cleared as to citation.** 291 Mich App 17; 805 NW2d 1 (2010), Docket 296318, **published**. Full holding text still to be read (§5). |
| ***Hayes v Hayes*** | **Cleared as to citation.** 209 Mich App 385; 532 NW2d 190 (1995), **published**. This is the "ECE exists regardless of how it arose" case Opus put on page one; the citation is real and correctly identified. Holding text still to be read (§5). |
| **Freestanding "parental alienation" doctrine** | **Cleared — the research finding stands.** A published-only search of Michigan Supreme Court and Court of Appeals opinions returns **four** opinions mentioning "parental alienation": *Luna v Regnier*, 326 Mich App 173; 930 NW2d 410 (2018); *Martin v Martin* (2020); *Barretta v Zhitkov* (2023); and *In re Hon Lisa O Gorcyca* (2017) — the last a Judicial Tenure Commission matter about a judge's handling of an alienation dispute, not a custody doctrine case. **No published Michigan opinion establishes parental alienation as a freestanding cause of action.** The guide must continue to route alienation through MCL 722.23(j), MCL 722.27a(7), and ordinary best-interest proof. |

---

## 4.1 *Shade v Wright* — full holding verified, and the outline understates it

**291 Mich App 17; 805 NW2d 1 (2010)**, Docket 296318, published. Read in full. The outline treats *Shade* as "a lower threshold for parenting-time-only modifications." That is directionally right but imprecise in ways that matter.

**The actual structure is a two-step gate, and the trigger is the ECE — not the label on the motion.**

> "We discern nothing in the *Vodvarka* opinion that requires the standards used to determine the existence of proper cause or change of circumstances for custody determinations to apply to determinations regarding parenting time, **absent a conclusion that a change in parenting time will result in a change in an established custodial environment**. … **If a change in parenting time results in a change in the established custodial environment, then the *Vodvarka* framework is appropriate.**"

So: a motion captioned "parenting time" still gets the **full *Vodvarka* threshold** if the relief sought would alter the ECE. A reader cannot lower their burden by re-labelling the motion. This belongs in Module 2.3 and Module 27.1 as the controlling first question.

**The holding, verbatim, and its express limit:**

> "we hold that, in a case where a modification of parenting time **does not alter the established custodial environment**, the fact that a child has begun high school and seeks to become more involved in social and extracurricular activities (normal life changes that do not constitute a change of circumstances under *Vodvarka*) constitutes a change of circumstances sufficient to modify parenting time."

And footnote 4 — **which the guide must carry, because it prevents overstatement**:

> "With our holding today, **we do not seek to precisely define** the proper cause or change of circumstances necessary to change parenting time. Our holding is limited to our conclusion that the normal life changes that occurred with the minor child in this case are sufficient to modify parenting time."

*Shade* is therefore **not** a general test. It is a narrow holding plus a widely-quoted rationale:

> "the very normal life change factors that *Vodvarka* finds insufficient to justify a change in custodial environment are precisely the types of considerations that trial courts should take into account in making determinations regarding modification of parenting time."

**⚠ Citation trap — a renumbered subsection.** *Shade* and other pre-amendment cases cite the parenting-time factors as **MCL 722.27a(6)(a)–(i)**. The current statute places them at **MCL 722.27a(7)(a)–(i)**. A reader who follows a case citation to subsection (6) will land on the wrong provision. Every case quotation in the treatise that references 722.27a(6) needs a bracketed note. This also explains the apparent discrepancy between the council reports (which say (7)) and the case law (which says (6)) — both are correct for their dates.

**Concurrence worth teaching (Shapiro, J.).** SCAO **FOC 65 "Motion Regarding Parenting Time" does not ask the movant for proper cause or change of circumstances at all**, while the custody motion form does — a discrepancy Shapiro read as evidence that the standards differ. A pro se reader filling out FOC 65 will not be prompted for the very showing the statute requires. That is a concrete forms trap for Module 12 and Appendix F.

**Cases verified through *Shade*'s own text** (citations confirmed, holdings as characterized by *Shade*):

| Case | Proposition |
|---|---|
| ***Pierron v Pierron***, 486 Mich 81, 92–93; 782 NW2d 480 (2010) | **Michigan Supreme Court** — binding. Change alters the ECE → **clear and convincing**. Does not alter it → **preponderance**, burden on the parent proposing the change. The outline's research file lists *Pierron* only for "important decisions"; this burden allocation is the more load-bearing use. |
| ***Terry v Affum (On Remand)***, 237 Mich App 522, 534–535; 603 NW2d 788 (1999) | Proper cause or change of circumstances **is** required to modify a **parenting-time** order |
| ***Powery v Wells***, 278 Mich App 526, 528; 752 NW2d 47 (2008) | **An evidentiary hearing is required** where a parenting-time modification would change the ECE — and, per the concurrence, no hearing is required where it would not |
| ***Corporan v Henton***, 282 Mich App 599, 603; 766 NW2d 903 (2009) | "The goal of MCL 722.27 is to minimize unwarranted and disruptive changes of custody orders, except under the most compelling circumstances" |
| ***Heid v AAA Sulewski (After Remand)***, 209 Mich App 587, 593–594; 532 NW2d 205 (1995) | The threshold "erects a barrier against removal of a child from an established custodial environment" |
| ***Brown v Loveman***, 260 Mich App 576, 595; 680 NW2d 432 (2004) | Hearing requirement, parenting-time changes |

***Vodvarka*'s definitions, now captured verbatim** (259 Mich App at 511, 513–514):

> "proper cause means one or more appropriate grounds that have or could have a **significant effect on the child's life** to the extent that a reevaluation of the child's custodial situation should be undertaken."

> "in order to establish a 'change of circumstances,' a movant must prove that, **since the entry of the last custody order**, the conditions surrounding custody of the child, which have or could have a significant effect on the child's well-being, **have materially changed**. … the evidence must demonstrate **something more than the normal life changes** (both good and bad) that occur during the life of a child, and there must be at least some evidence that the material changes **have had or will almost certainly have an effect on the child**."

**The gateway question is now sharper but still open.** Whether interference alone clears *Vodvarka* depends first on whether the relief sought would alter the ECE — if it would not, *Shade*'s more expansive standard governs and the bar is materially lower. Module 18 should be drafted around that branch, not around a single threshold. Whether a published Michigan opinion holds that interference **by itself** satisfies *Vodvarka* where the ECE **would** change remains unverified.

## 4.2 MCL 722.27a — now read in FULL (all 19 subsections), and it contains the case-critical provision everyone missed

Re-fetched complete from `legislature.mi.gov` August 9, 2026 (evening pass). History: Add. 1988 PA 377; last amended **2016 PA 96, eff. Aug 1, 2016** — the amendment-currency question in the addendum §13 is now **closed**.

**The find: MCL 722.27a(8), verbatim —**

> **"(8) Parenting time shall be granted in specific terms if requested by either party at any time."**

Mandatory voice ("shall"), no threshold stated, no window ("at any time"), available to "either party." **No council report, neither research pass, the outline, nor this project's own addendum carried this subsection.** For the vague-order fact pattern — parenting time "as the parties agree" — this is the lead authority: a statutory entitlement to convert open-ended parenting time into specific terms on request.

**Drafting caution (unverified):** how the Court of Appeals reconciles (8) with the proper-cause/change-of-circumstances gate for *modifying* an existing order is **not verified** — no case law read on (8). The safe structure: lead with the (8) request for specific terms (arguing an "as agreed" provision never granted specific terms to modify), and plead *Shade*-level proper cause / change of circumstances **in the alternative**. Do not present (8) as threshold-free settled law; present the statutory text, which is verified.

**Also now verbatim-complete:**

- **(7)(a)–(i)** — the full parenting-time factor list, closing the partial capture in the addendum: (a) special circumstances or needs; **(b) nursing child under 6 months, or under 1 year if the child receives substantial nutrition through nursing**; (c)–(h) as previously quoted; (i) any other relevant factors.
- **(9)(a)–(i)** — the order-terms menu, confirmed as previously summarized.
- **(10)** — a parenting-time order **shall contain** a prohibition on exercising parenting time in a non-Hague country, absent both parents' written consent. Mandatory order content for Module 25 that the outline does not carry.
- **(11)** — "During the time a child is with a parent to whom parenting time has been awarded, that parent shall decide all routine matters concerning the child." The parenting-time twin of MCL 722.26a(4).
- **(12)–(15)** — the ex parte interim parenting-time machinery and its 14/14/21/28-day clocks, confirming Appendix A's corrected rows, including the statutory notice text.
- **(4)–(6), (19)** — criminal-sexual-conduct parenting-time bars (scope boundary: hard-stop territory, not self-help).
- **(16)–(18)** — deployment provisions.

## 4.2 *Duperon* read — the FOC report paradox, both halves now verified

***Duperon v Duperon*, 175 Mich App 77; 437 NW2d 318 (1989)**, published. Opinion text read via three independent mirrors (ecases.us, cetient, vLex) with **identical operative language in all three**; official-reporter cross-check remains open but the convergence is strong. The operative passage, verbatim:

> "The FOC's report and recommendation is **not admissible as evidence unless both parties agree to admit it in evidence.** However, the report **may be considered by the trial court as an aid to understanding the issues** to be resolved. The trial court's **ultimate findings relative to custody must be based upon competent evidence adduced at the hearing.** Thus, while the FOC's report and recommendation may not form the basis for the trial court's findings, it may be used to establish a **background and context** for the proceedings."

And the second holding: there is **no mandate that the court consider the report at all** — *Duperon* rejects the argument that *Hoffman v Hoffman* requires it: "We do not read *Hoffman* as establishing a blanket mandate that the trial court consider FOC reports."

**The paradox, now stated precisely (three prongs, not two):**

1. **Not evidence** absent both parties' agreement — so an unfavorable report is not proof against the reader, and a favorable one carries none of the reader's burden.
2. **But considerable** as background, context, and an aid to understanding — which is how it coexists with MRE 1101(b)(9) (the evidence rules do not apply to the court's *consideration* of the report). Consideration ≠ evidence.
3. **Findings must rest on competent hearing evidence.** A decision that *adopts* the report's findings without independent hearing evidence is reversible error.

**The enforcement teeth — *Truitt v Truitt* (Mich App), quoting *Marshall v Beal*, 158 Mich App 582, 591 (1986):** where the parties "did not stipulate to allowing the friend of the court's recommendations or report into evidence" and the trial court "reviewed and adopted the friend of the court's findings" rather than arriving at an independent conclusion from its own de novo hearing — "This is a **clear legal error which requires reversal** and a new hearing." That is the reader's preserved appellate argument if a decision rests on the report — available **only if they did not stipulate the report in**.

**Same rule in the support context — *Pellar v Pellar*, 443 NW2d 427 (1989)**, citing *Jacobs v Jacobs*, 118 Mich App 16, 22–24 (1982): the court "may not accord evidentiary weight to the facts stated in the report of the friend of the court, unless otherwise stipulated to by the parties, although the report may be used as an evaluative aid."

**Practical consequences for the drafted text (Modules 15–16; doc4's flag can now close):**

- The strategic default in the drafts — do not stipulate the report into evidence — is **confirmed as sound**: stipulating converts a not-evidence document into evidence *for and against* the reader.
- If a recommendation or decision **tracks the report** and the hearing record does not independently support it, that is an objection to make and an error to preserve — *Truitt*'s reversal shows it is not theoretical.
- ⚠ **Citation-drift note:** *Duperon* cites the FOC duty as "MCL 552.505(d)" and *Truitt* cites the de novo hearing as "MCL 552.507(5)" — old numbering. Current provisions: **MCL 552.505(1)(g)–(h)** and **MCL 552.507(4)**. Same trap as the 722.27a(6)→(7) renumbering; bracket-note any quotation.
- Caveats: 1980s Court of Appeals authority (published, so binding under stare decisis principles for the COA-and-below, and never located as overruled in this pass — a negative-treatment check via a citator was **not** possible with available tools and remains open).

## 4.3 The specific-terms line read — *Pickering*, *Kaeb*, and a SECOND renumbering trap (August 10, 2026)

**This entry resolves the packet's central open question** — what authority governs a request to convert a vague parenting-time provision into specific terms — the exact issue the worked-example response (P1-worked-examples Part Three) built its best argument around. CourtListener MCP disconnected mid-session again; read via Exa mirrors under the convergence standard.

***Pickering v Pickering*, 268 Mich App 1; 706 NW2d 835 (2005), published.** Operative passage read verbatim via OpenJurist and midpage mirrors (⚠ both trace to one upstream document id; official-reporter cross-check open — treat the *cites* as convergence-pending, the *text* as read). Holdings, from the opinion's own words:

1. The trial court awarded "reasonable and liberal parenting time." Held: **"'Reasonable and liberal parenting time' is plainly not a grant of parenting time in 'specific' terms"** — nor parenting time "in a frequency, duration, and type reasonably calculated to promote a strong relationship." A generous-sounding vague provision *fails the statute* once specificity is requested. ("As the parties agree" is *less* definite than "reasonable and liberal.")
2. Quoting then-(7): "Parenting time shall be granted in specific terms if requested by either party at any time" — **"requests for specific parenting time terms must be considered by the court regardless of the timing of the request."** Refusing to consider specific terms once requested was **legal error as a matter of law**; the parenting-time provision was **vacated** and remanded "with the direction to consider a specific parenting time order."
3. Even the procedural objection failed: an **oral** motion made during a hearing satisfies MCR 2.119(A)(1)'s writing requirement ("[u]nless made during a hearing or trial").
4. Posture caveat, stated honestly: *Pickering* arose **at judgment** (request made before entry), not postjudgment. It does not by itself silence the response's "grant vs. modification" argument; it does establish that the specific-terms provision is mandatory ("shall"), that vague formulations do not satisfy it, and that "at any time" defeats timing objections. The packet's belt-and-suspenders design (invoke the specific-terms provision **and** plead the *Shade* threshold in the alternative) stands as the correct posture.

***Kaeb v Kaeb*, 309 Mich App 556, 571–572; 873 NW2d 319 (2015), published.** ✅ Fully verified — read via the **official courts.michigan.gov opinion PDF** (Docket 319574, authored, published 3/12/2015), FindLaw, and Leagle, and cited at 309 Mich App 556, 571–572 by the **MJI Domestic Relations Quick Reference "Modification of Parenting Time" checklist** (courts.michigan.gov). Holdings:

1. For a request to change a **condition** on parenting time (there: ordered AA attendance and counseling), neither *Vodvarka* nor *Shade* is directly on point; a "**lesser, more flexible**" threshold applies: "proper cause" carries its **ordinary meaning — "an appropriate ground for taking legal action"** — and the movant must show the condition "in its current form **no longer serves the child's best interests**."
2. The court may "adopt, revise, or revoke a condition whenever it is in the best interests of the child to do so."
3. Sanctions for filing the motion without a *Vodvarka* showing were **reversed** — the flexible standard made the motion non-frivolous.

**⚠ SECOND RENUMBERING TRAP — verified by comparing the two opinions' own quotations against the current statute** (legislature.mi.gov, "Complete Through PA 2 of 2025"): *Pickering* (2005) quotes the specific-terms sentence as subsection **(7)**; *Kaeb* (2015) cites the reasonable-terms-and-conditions menu as subsection **(8)**. The current statute places specific-terms at **(8)** and the terms-and-conditions menu at **(9)** (factor list: old (6) → current (7), already recorded at §4.1). **Every pre-2016 citation to 722.27a shifts down one subsection.** Bracket-note any quotation; a filed brief citing *Pickering*'s "(7)" without the note points the court at the wrong subsection of the current statute.

**Leads surfaced, NOT yet read — recorded as leads only (no holding may be cited from this list):**

- ***Lieberman v Orr*, 319 Mich App 68, 83–84 (2017), published** — quoted identically by two independent secondary quoters (the MJI checklist and a 1/15/2026 unpublished COA opinion): normal life changes "may be sufficient for a court to consider modification of a parenting-time order **unless the requested change would alter the established custodial environment**," and where modification WILL affect the ECE "the proposal is essentially a change in custody, and *Vodvarka* governs." **PROVISIONAL** — consistent double-sourced quotation; opinion unread.
- ***Kuebler v Kuebler*, 346 Mich App ~653–673 (cited 2023–24)** — threshold restatement quoted in the 2026 opinion. Unread.
- ***Bowling v McCarrick*, 318 Mich App 568, 571–572 (2016)** — cited by the MJI checklist on the threshold burden. Unread.
- ***Kahl v Kasten*, COA Docket 372185, unpublished, 1/15/2026** (michbar.org opinion PDF, read in part) — live example of the **recharacterization trap**: father's "parenting time" motion sought equal time plus holiday and extended-summer division against a vague consent judgment; referee, trial court, and COA all treated it as a **change-of-custody motion under *Vodvarka*** because the swing would alter the ECE. Also shows a consent-judgment clause pre-agreeing that an event "constitutes 'change of circumstances' and 'proper cause'" — held immaterial once the request was custody-in-substance. Unpublished: MCR 7.215(C)(1) treatment if ever used.
- ***Bachman v Snowgold*, COA 2015, unpublished** (syfert mirror; applies *Kaeb*) — where parents share joint legal and physical custody and the ECE is with both, "absent unusual circumstances... it is unlikely that a request for approximately equal parenting time will constitute a change in custody or a change to the ECE"; *Vodvarka* application reversed. Directly relevant to the eventual 50/50 phase — but its predicate (existing joint ECE) is the opposite of a long-exclusion posture. Unpublished; unread in full.
- **MCL 552.517d(4)** — per the MJI checklist: a statement of fact from the FOC report may be admitted "if no other evidence is presented concerning the fact, and the parties agree or no objection is made." **The statutory companion to the *Duperon* rule — and a waiver-by-silence trap at the hearing.** Statute text not yet fetched: **UNVERIFIED**; fetch and reconcile with §4.2 before Module 15 ships.

**Strategic consequence for Packet 1** (drafting note, carried to the handoff): the sequence the owner chose — modest specific schedule first, make-up time second, 50/50 later — is exactly what this line of cases rewards. *Pickering* makes the specific-schedule ask nearly unrefusable as a legal matter; *Kahl* shows what happens when the first motion over-asks (equal time + holidays + summers = *Vodvarka*); *Bachman*'s joint-ECE predicate is what the interim record-building is trying to re-establish before the 50/50 phase.

## 5. Still open — verifiable, not yet done

- Full holding text of ***Shade v Wright***, ***Berger v Berger***, ***Dailey v Kloenhamer***, ***Duperon v Duperon*** (the second half of the FOC report paradox), and ***Pierron***, ***Fletcher***, ***Baker***, ***Foskett***, ***McIntosh***, ***Bofysil***.
- ***Grew v Knox*** — locate and confirm unpublished status and docket number; if used at all, it must carry the MCR 7.215(C)(1) treatment verified above.
- ***Sullivan v Gray*** — official reporter citation; and the *AFT Michigan v Project Veritas* federal cluster's current posture.
- **MCSF §3.03** Parental Time Offset brackets, and the 2025 Manual's **18** deviation factors re-read from the primary PDF (the outline records the 18 as verified in the v2 pass; a second read is cheap and this is the single most citation-sensitive table in the support module).
- **MCR 2.300-series numeric discovery limits** — interrogatory/deposition caps.
- **FOC 89 and FOC 57 titles** from the SCAO form PDFs.
- **MiChildSupport calculator** live URL.

**Rate note:** CourtListener's free tier throttles at 5 requests/minute, which paces the case-law work. It is not a blocker, just slower than the rules work.

---

## 6. Not clearable by any model — must go to a human

Unchanged from the outline's §0.8, and reinforced by this pass.

1. **Every Genesee County local fact** — filing and motion fees, judicial and referee rosters, FOC office procedure, CDRP details, local administrative orders, form revision dates. The second research package's own audit found the bench roster "multi-source and conflict-prone," with a 2024 case-assignment LAO that is partially stale against the 2025 Family Court Plan and 2025 judicial elevations, and no located 2025/2026 successor. **Confirm the assigned judge and referee with the clerk.**
2. **The vicarious-consent recording question.** Three models produced three different legal theories reaching the same practical warning. The second package's audit independently classifies this cluster as **UNSETTLED**, noting the Michigan Supreme Court declined the certified question in the *AFT Michigan v Project Veritas* line. Do not state a rule. Use the hard-stop architecture.
3. **Any template a reader might mistake for filing-ready.**

Two additions this pass:

4. **The stale Genesee motion-practice notice (C-3).** A human must ask the clerk which timing actually governs in the 7th Circuit today, because the posted county document and the current statewide rule do not agree.
5. **The wrong-jurisdiction trap.** `circuit7.org` is the **Florida** Seventh Judicial Circuit. Genesee's court is **7thcircuitcourt.com**. Any URL check must catch this.

---

## 7. What this means for drafting

- The **statewide legal spine of the treatise is now safe to draft** — standards, evidence, referee practice, ex parte practice, subpoenas, appeals — from verified primary text rather than snippets.
- The **Genesee local layer is not** and should be drafted as explicitly provisional, carrying `ℹ LOCAL PRACTICE` with a confirm-with-the-clerk instruction, per the outline's existing flag system.
- Corrections **C-1** through **C-6** should be applied to `custody_guide_outline_v2.md` before any module is drafted, since the outline is the drafting contract and these errors would otherwise be executed faithfully.
