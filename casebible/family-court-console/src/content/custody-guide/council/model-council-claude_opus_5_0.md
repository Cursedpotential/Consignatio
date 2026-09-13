# Critical Review and Revised Skeleton — *Michigan Pro Se Custody / Parenting-Time / Child Support Treatise* (Genesee County)

**Reviewer:** Council model (Claude Opus 5.0 seat)
**Review target:** `custody_guide_outline.md` (701 lines). `custody_guide_plan.md` and `custody_guide_research.md` read for context only.
**Date of review:** August 9, 2026
**Analytical angle taken:** The outline is critiqued primarily through the **evidentiary and procedural-mechanics layer** — the layer that actually decides pro se custody cases and that this outline almost entirely omits. Secondary angles: enforcement law, the appeal-deadline cliff, and the "consent trap" architecture of Michigan domestic-relations practice.

---

## 0. Method and posture

I verified every load-bearing legal assertion I make below against a primary or near-primary source and cite it inline. Where the outline's own research file flagged an item as unverified and I could not verify it either, I say so explicitly rather than papering over it. Two Michigan state domains (`courts.michigan.gov` search paths and `legislature.mi.gov` search paths) were intermittently robots-blocked during this session, so several rule texts were obtained from `courtrules.net` and cross-checked against SCAO benchbook HTML and State Bar sources.

I did **not** rewrite the other two documents. Where the plan document's constraints (ICLE lesson mirroring, out-of-scope list) are themselves the source of a defect in the outline, I say so — because a critique of the outline that refuses to touch the constraint that caused the defect is useless.

---

## 1. VERDICT

**Short answer: No. A drafting model could execute this outline and produce a document that reads like a competent treatise and is quietly dangerous.** It would be genuinely useful on orientation, vocabulary, and Genesee logistics. It would fail — in a way the reader could not detect — at the three points where pro se custody cases are actually won or lost.

### 1.1 What the outline gets right

- The Genesee-specific layer (praecipe practice, FOC 68 objection window, motion-day mechanics, MiFILE, fee waiver) is the single highest-value thing a pro se guide can contain, and the outline knows it. Most published self-help material stops at the state level and leaves the reader stranded at the counter.
- The exercise taxonomy in the plan (fill-in template, worked example, evidence log, practice script, red-flag spotting) is pedagogically sound and unusually good for legal self-help.
- Separating the *standards* lesson (Lesson 7: ECE, *Vodvarka*, joint vs. sole) is defensible as a reference spine.
- Treating disclaimers as content rather than boilerplate is correct and rare.

### 1.2 Where it fails in practice — four structural failures

**Failure 1 — The outline has no theory of admissibility, and therefore no theory of proof.**

The outline's central evidentiary strategy is the "custody journal" (§4.1) plus texts, emails, and OFW logs (§4.2), fed into a "best-interest evidence matrix" (§1.1). Nowhere does it explain how any of that gets *into evidence*. This is not a stylistic omission; it is the difference between a reader who wins and a reader who stands at a podium holding a three-ring binder that the judge will not look at.

Three hard facts the outline does not contain:

- **The Michigan Rules of Evidence apply at referee hearings.** MCR 3.215(D)(1): "The Michigan Rules of Evidence apply to referee hearings" ([MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215)). The outline's §2.5 treats the referee hearing as an informal step. For most Genesee pro se parents the referee hearing *is* the case; it is also their first and often only contested evidentiary proceeding.
- **Michigan has no self-authentication route for electronic evidence.** Michigan's MRE 902 self-authentication list runs (1)–(11) and does **not** include the certified-electronic-record provisions that exist federally as FRE 902(13)–(14) ([Michigan Rules of Evidence, SCAO](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf); compare [FRE 902](https://www.law.cornell.edu/rules/fre/rule_902)). Every text message, screenshot, call log, and OurFamilyWizard export must be authenticated by live testimony under MRE 901. There is no certificate shortcut. A guide that tells a reader to "print your texts and bring them" without teaching an MRE 901 foundation script is setting them up.
- **The custody journal is, in the author's own hands, largely inadmissible self-serving hearsay.** A contemporaneous log is enormously valuable — as a *memory-refresher* under MRE 612, as impeachment, as the backbone of the reader's own live testimony, and as the raw material for a timeline exhibit. It is generally not an exhibit in itself when offered by its author for the truth of its contents. The outline presents journaling as if the journal were the evidence. It is not; the reader's testimony is the evidence, and the journal is the scaffolding.

**Failure 2 — The outline misstates what the "de novo" judicial hearing actually is.**

The outline (§2.5) tells the reader that on objection to a referee recommendation the judge "does not defer to the referee's findings but rehears the matter fresh." That is materially misleading. Under MCR 3.215(F)(2), the court "may, in its discretion: (a) prohibit a party from presenting evidence on findings of fact to which no objection was filed; (b) determine that the referee's finding was conclusive as to a fact to which no objection was filed; (c) prohibit a party from introducing new evidence or calling new witnesses unless there is an adequate showing that the evidence was not available at the referee hearing" ([MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215)). The judicial hearing is *de novo in name and constrained in practice*. The court must allow the parties to present live evidence, but it may also rely on the referee-hearing record.

Three consequences the outline never surfaces, each of which can end a case:

- **Objections must be specific.** MCR 3.215(E)(4) requires an objection to "include a clear and concise statement of the specific findings or application of law to which an objection is made." A generic "I object to the whole recommendation" invites the court to treat unobjected findings as conclusive.
- **Failing to build a record at the referee hearing is often unrecoverable.** Because new evidence can be barred absent a showing of unavailability, the reader who "saves it for the judge" may never get to present it.
- **A bad objection is sanctionable.** MCR 3.215(F)(3) permits costs and attorney fees where an objection is found frivolous or filed to delay. The outline's tone encourages objecting as a default posture with no counterweight.

**Failure 3 — Appeals are declared out of scope, which is an error of a different kind than the others.**

The plan document places appeals to the Court of Appeals out of scope. Every other out-of-scope call (property division, PPO respondent defense, non-Michigan law) is defensible. This one is not, because appellate deadlines are **jurisdictional and short**, and a reader who does not know they exist loses the right permanently while reading a guide that never mentioned it.

- A claim of appeal must be filed within 21 days ([MCR 7.204](https://www.courtrules.net/michigan/michigan-court-rules/rule-7-202) chapter context; MCR 7.204(A)(1)(a)).
- Critically, in domestic relations there is an **appeal-of-right / leave asymmetry** the reader must know: a postjudgment order is "final" — and thus appealable of right — when it "grants or denies a motion to change legal custody, physical custody, or domicile," under MCR 7.202(6)(a)(iii) ([MCR 7.202](https://www.courtrules.net/michigan/michigan-court-rules/rule-7-202)). An order resolving **parenting time only** generally is not, and requires an application for leave. An alienated parent's most common loss — a parenting-time reduction — is therefore *not* appealable of right, while a custody loss is. No pro se reader will guess this.
- The standard of review is deliberately hostile to appeals: under MCL 722.28 the reviewing court affirms unless the findings are against the great weight of the evidence, there was a palpable abuse of discretion, or there was clear legal error on a major issue ([MCL 722.28](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-28)).
- *Rains v Rains*, 301 Mich App 313 (2013), holds an order need not literally change custody to "affect" custody for appellate purposes ([opinion PDF](https://www.courts.michigan.gov/4a399b/siteassets/case-documents/uploads/opinions/final/coa/20130613_c312243(55)_rptr_90o-312243-final.pdf)).

The correct scope call is not "teach appellate practice." It is: **teach the deadline, the appeal-of-right/leave distinction, the standard of review, and how to preserve error at trial — then hand off to counsel.** A one-page module prevents an irreversible harm; omitting it causes one.

**Failure 4 — Enforcement, the tool an alienated parent uses most, is a bullet fragment.**

The outline compresses parenting-time enforcement into part of §3.4. In lived practice, a parent facing alienation spends far more time on denied exchanges than on trial. Michigan gives that parent a detailed statutory machine the outline never describes:

- On a written parenting-time complaint the FOC must apply the makeup parenting-time policy, commence civil contempt, or move to modify ([MCL 552.641](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-641)).
- The makeup policy has specifics a reader can weaponize: makeup time must be of the same type and duration, taken within one year, **the denied parent chooses when**, with one week's notice for weekend/weekday time and 28 days' notice for holiday or summer time; the other parent has 21 days to respond to the FOC notice and **failure to respond is treated as agreement** ([MCL 552.642](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-642); [SCAO/FOCB memo 2025-02 on FOC 16](https://www.courts.michigan.gov/4a4d85/siteassets/court-administration/focb-memoranda/2025/2025-02.pdf)).
- Contempt remedies escalate concretely: additional terms, modified parenting time, makeup time, fine up to $100, jail up to 45 days for a first finding and 90 for subsequent, work-release, license suspension, community corrections placement, FOC supervision ([MCL 552.644](https://law.justia.com/codes/michigan/2006/mcl-chap552/mcl-552-644.html); [MJI Contempt Benchbook ch. 5](https://www.courts.michigan.gov/49aeda/siteassets/publications/benchbooks/contempt/contemptresponsivehtml5.zip/Contempt/Ch_5_Common_Forms_of_Contempt/Contempt_for_Violation_of_Parenting_Time_Order.htm)).
- Bad-faith sanctions escalate $250 / $500 / $1,000 plus costs, and license suspension carries a 21-day window to request a modification hearing ([MCL 552.645](https://law.justia.com/codes/michigan/chapter-552/statute-act-295-of-1982/section-552-645/)).
- SCAO's own 2024–25 training material is titled "Custody and Parenting Time Enforcement Myths" ([MJI material](https://www.courts.michigan.gov/4a509e/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/custody-and-parenting-time-enforcement-myths/custody-and-parenting-time-enforcement-myths-material.pdf)) — the myths it corrects are precisely the ones a guide like this will propagate if enforcement is treated as an afterthought.

### 1.3 Bottom line

The outline is executable in the sense that a drafting model will produce prose from it. It is not executable in the sense of producing a *legally sound* treatise, because the drafting model will faithfully reproduce a document with no admissibility layer, a misstatement of MCR 3.215(F), no appellate deadline, and a two-line treatment of the enforcement statute that governs the reader's daily life. Roughly **35–40% of the substantive content a Genesee pro se custody litigant needs is absent**, and the absent portion is disproportionately the part that is irreversible when gotten wrong.

---

## 2. GAPS — substantive omissions

Ordered by decision-relevance, not by the order the task listed them.

### 2.1 Evidence and admissibility for pro se litigants — the largest gap

**(a) A foundations module does not exist and must.** The reader needs, in plain language and with scripts: relevance (MRE 401/402), the hearsay definition and why "she told me he said" fails, the party-opponent exclusion (MRE 801(d)(2)) — which is the single most useful rule for a parent, because *anything the other parent said or wrote is admissible against them* — present sense impression and excited utterance (MRE 803(1)–(2)), records of regularly conducted activity (MRE 803(6)) for school and medical records, public records (MRE 803(8)), recorded recollection (MRE 803(5)), and refreshing recollection (MRE 612).

**(b) No self-authentication of digital evidence.** As noted above, Michigan's MRE 902 stops at (11) and has not adopted the FRE 902(13)/(14) certification route ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf); [SCAO Evidence Benchbook, Foundation](https://staging.courts.michigan.gov/4a50d8/siteassets/publications/benchbooks/evidence/evidenceresponsivehtml5.zip/Evidence/Ch_1_General/Foundation.htm)). The guide must teach an MRE 901 foundation script for: a text-message thread, a screenshot, an email, a photograph, a voicemail, an OFW/TalkingParents export, and a social-media post. This is the most valuable single page the treatise could contain and it is entirely missing.

**(c) MRE 803A (tender-years) does not apply in custody cases.** It reaches only criminal and juvenile delinquency proceedings ([SCAO Sexual Assault Benchbook, Tender-Years Exception](https://www.courts.michigan.gov/4a3004/siteassets/publications/benchbooks/sabb/sabbresponsivehtml5.zip/SABB/Ch_6_Evidence/Tender-Years_Exception.htm)). This is devastating to the outline's Lesson 5 as written: the alienation module's implicit evidentiary theory is "the child said Mom told him I don't love him." That statement is hearsay in a custody case, and the tender-years exception the reader will find on the internet does not save it. The guide must teach the legitimate routes instead: the statement offered **not for its truth** but for effect on the listener or as circumstantial evidence of the child's state of mind (MRE 803(3)); the child's own in camera interview; a court-appointed evaluator or LGAL; and the party-opponent route when the alienating statement was made by the other parent directly.

**(d) The in camera child interview is a partial exception the reader should understand.** MRE 1101(b)(6) provides that the rules of evidence do not apply to "in camera proceedings in child-custody matters" ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf)), and MCR 3.210(C)(5) permits the court to interview the child privately with questioning limited to the reasonable-preference factor ([MCR 3.210](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-210)). The reader needs both halves: the interview exists, and it is *narrow* — it is not a channel for the child to narrate the other parent's misconduct.

**(e) The FOC report paradox.** This is subtle, consequential, and absent. MRE 1101(b)(9) says the rules of evidence do not apply to "the court's consideration of a report or recommendation submitted by the friend of the court under MCL 552.505(1)(g) or (h)" ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf)). But *Duperon v Duperon*, 175 Mich App 77, 79 (1989), holds the FOC report "is not admissible as evidence unless both parties agree to admit it in evidence," may be used only for background and context, and the court's custody findings "must be based upon competent evidence adduced at the hearing" ([Duperon](https://www.casemine.com/judgement/us/59148af2add7b0493451a3c2); applied in [COA 2002 opinion, michbar](http://www.michbar.org/file/opinions/appeals/2002/081602/16034.pdf)). The practical teaching: **a favorable FOC report does not carry your burden, and an unfavorable one is not evidence against you — but only if you don't stipulate it in.** MCR 3.210(C)(6) guarantees the opportunity to review the report and file objections before decision ([MCR 3.210](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-210)). The same non-admissibility-absent-stipulation rule applies to an LGAL's written report under MCL 722.24(3) ([SCAO third-person custody checklist](https://www.courts.michigan.gov/48dbed/siteassets/publications/benchbooks/qrms/family/domestic-relations/child-custody-dispute-involving-third-person-checklist.pdf)).

**(f) The hearsay-waiver trap in evaluation orders.** A Michigan appellate panel held a mother waived hearsay objections to an evaluator's report where the *appointment order itself* provided that the parties waived hearsay objections, she submitted to the evaluation, and she did not object at admission ([State Bar e-Journal summary](https://www.michbar.org/opinions/content_search_detail/EJournalNumber/86190)). A pro se parent will sign a stipulated evaluation order without reading this clause. The guide must teach the reader to read the appointment order for a waiver clause before signing.

### 2.2 Recording law — the outline's guidance is dangerously incomplete

The outline mentions recording in §4.1 without resolving it. The actual Michigan position has two halves and the second half is where the felony lives.

- **Participant recording is lawful.** MCL 750.539c is drafted as all-party consent, but *Sullivan v Gray*, 117 Mich App 476; 324 NW2d 58 (1982), construes "eavesdrop" to exclude a participant to the conversation ([Sullivan v Gray](https://law.justia.com/cases/michigan/court-of-appeals-published/1982/57301.html)). The State Bar's ethics opinion RI-309 proceeds on the same understanding ([SBM RI-309](https://www.michbar.org/opinions/ethics/numbered_opinions/ri-309)). After years of uncertainty — the Michigan Supreme Court declined to answer the certified question in 2021 ([MSC docket 162121](https://www.courts.michigan.gov/c/courts/msc/case/162121/)) — the Eastern District of Michigan granted summary judgment in *AFT Michigan v Project Veritas* on March 30, 2026, confirming Michigan remains a one-party-consent state for participants and that a person whose presence is apparent counts as a party whether or not they speak ([Butzel](https://www.butzel.com/alert-butzel-prevails-in-long-running-michigan-eavesdropping-statute-litigation); [Detroit News](https://www.detroitnews.com/story/news/politics/2026/04/03/federal-judge-upholds-michigans-one-party-consent-recording-law/89449448007/); [Michigan Lawyers Weekly](https://milawyersweekly.com/news/2026/05/04/fraud-infiltration-project-veritas/)).
- **Non-participant recording is a felony.** *Sullivan* is explicit that a participant's consent does not authorize a **third party** to record. Punishment under MCL 750.539c runs to 2 years and/or $2,000, and MCL 750.539d separately criminalizes installing a device to observe or record in a private place.

**The specific trap this creates, which no self-help guide I have seen states plainly:** the single most common recording idea an alienated parent has — *send the child to the other parent's house with a phone recording, or a hidden recorder in a backpack* — is **non-participant recording and is felony conduct**, not a clever evidence strategy. So is placing a recording device in a car the other parent uses, or in the other parent's home. The guide must state this in a boxed warning, not in a footnote. Secondary points to include: a lawfully made participant recording still must be authenticated under MRE 901; some judges react badly to recordings of children even when lawful; and a recording of the other parent is a party-opponent statement under MRE 801(d)(2) and therefore not hearsay.

### 2.3 Subpoena practice — the outline's discovery module rests on a false premise

MCR 2.506(B)(1) provides that a subpoena signed by an attorney of record **or by the clerk of the court** has the same force as a judge's order, and MCR 2.506(C)(1) requires service at least 2 days before appearance, or **14 days before** when documents are requested ([MCR 2.506](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-506)); the form is [MC 11](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc11.pdf).

But for *discovery* subpoenas the rule is different, and this is the trap: MCR 2.305(A)(1) provides that "a represented party may issue a subpoena to a non-party… **An unrepresented party may move the court for issuance of non-party discovery subpoenas**" ([MCR 2.305](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-305)). The outline's §2.1 discovery module assumes the reader can serve subpoenas the way a lawyer does. They cannot — they must file a motion. The correct teaching is the two-track distinction: **clerk-issued MC 11 for testimony and documents at a hearing or trial; motion to the court for pre-hearing non-party discovery subpoenas.**

Related and missing: subpoenaing school and medical records (and the FERPA/HIPAA overlay); subpoenaing MDHHS/CPS records, which has its own process and generally contemplates an attorney-signed subpoena with proof of representation ([MDHHS subpoena page](https://www.michigan.gov/mdhhs/inside-mdhhs/legal/subpoena)); subpoenaing law enforcement CAD logs and incident reports; the mechanics of paying witness fees and mileage; and the interaction between a subpoena for records and the business-records foundation under MRE 803(6).

### 2.4 Change of domicile / 100-mile rule — absent entirely

MCL 722.31 is nowhere in the outline. For a parent litigating against a high-conflict ex, a relocation motion is one of the two or three most likely future events in the case.

- The court must consider the five factors in MCL 722.31(4)(a)–(e), which include the degree to which the move will improve quality of life, whether the moving parent's motive is to frustrate parenting time, whether a realistic modified schedule preserves the relationship, financial motive, and **domestic violence** ([MCL 722.31](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-31)).
- Exceptions in MCL 722.31(3) where the parents' residences are already more than 100 miles apart, or the move brings them closer.
- The analysis is sequenced: preponderance on the (4) factors, then whether the move alters the ECE, and only if it does, clear and convincing evidence on best interests — a sequence appellate courts have remanded for skipping ([Speaker Law, 100-mile rule procedural misstep](https://www.speakerlaw.com/blog/100-mile-rule-procedural-misstep-requires-remand-re-evaluation); [SCAO Changing Child's Legal Residence checklist](https://www.courts.michigan.gov/48dc1e/siteassets/publications/benchbooks/qrms/family/domestic-relations/changing-childs-legal-residence-checklist.pdf)).

### 2.5 Contempt and enforcement — see §1.2 Failure 4. Needs a full lesson, not a bullet.

Add also the intake channel: a parenting-time complaint under MCL 552.511b ([MCL 552.511b](https://law.justia.com/codes/michigan/chapter-552/statute-act-294-of-1982/section-552-511b/)) and the MDHHS-facing description of the process ([MDHHS parenting time](https://www.michigan.gov/mdhhs/adult-child-serv/child-sup/how-do-i/get-parenting-time)).

### 2.6 Attorney fees — absent, and this is a strategic loss

MCR 3.206(D) provides two independent routes: (1) the moving party is unable to bear the expense of the action and the other party is able to pay; and (2) the fees were incurred because the other party **refused to comply with a previous order despite having the ability to comply**. Requests must be supported by actual evidence, not "unsubstantiated assertions" ([Michigan Court of Appeals, 2026](https://www.michbar.org/Portals/0/opinions/appeals/2026/030926/85341.pdf); [State Bar e-Journal](https://www.michbar.org/opinions/content_search_detail/EJournalNumber/86151/P/LDS); background at [Michigan Bar Journal](https://www.michbar.org/file/barjournal/article/documents/pdf4article883.pdf); see also MCL 552.13(1)).

Two nuances the guide must handle honestly: a pro se party generally cannot recover a fee for their own time (there is no fee to shift), **but** route (2) is precisely designed for the situation the reader is in — a party who violates orders — and a fee award can fund limited-scope counsel for the next stage. That reframing turns a "not for you" rule into a live tactic.

### 2.7 GAL vs. LGAL vs. custody evaluator — conflated in the outline

Lesson 5.3 mentions LGAL and MCR 3.219 without distinguishing three different animals with three different functions and three different evidentiary statuses:
- **LGAL** — a lawyer-guardian ad litem represents the child's *best interests* and is the child's attorney in a defined sense; the LGAL's written report is not admissible unless all parties stipulate (MCL 722.24(3), per the [SCAO checklist](https://www.courts.michigan.gov/48dbed/siteassets/publications/benchbooks/qrms/family/domestic-relations/child-custody-dispute-involving-third-person-checklist.pdf)).
- **GAL** — a broader investigative appointee, not necessarily an attorney.
- **Attorney for the child** — represents the child's *expressed preference*.
- **Custody evaluator / psychological evaluator** — a court-appointed or party-retained expert whose report is hearsay and whose admission is governed by the appointment order (see the waiver trap at §2.1(f)) and MRE 702/703.

The strategic teaching absent from the outline: **who to ask for, when, and who pays.** Requesting an LGAL in an alienation case is frequently the highest-leverage motion an alienated pro se parent can file, because it creates an independent voice that the court will actually listen to. It also costs money and can backfire.

### 2.8 CPS involvement — declared out of scope, but the interaction cannot be

The plan puts CPS proceedings out of scope. Abuse/neglect adjudications, yes. But the *interaction* between a CPS investigation and a custody case is unavoidable for this reader and is not covered:

- CPS classifies investigations into five categories under MCL 722.628d; Categories I–III mean a preponderance finding of abuse or neglect, and Category V means the referral was based on false or erroneous information ([MDHHS CPS investigation process](https://www.michigan.gov/mdhhs/adult-child-serv/abuse-neglect/childrens/report-process/investigation-process-and-results/childrens-protective-services-investigation-process); [MDHHS PSM 713-01](https://mdhhs-pres-prod.michigan.gov/olmweb/EX/PS/Public/PSM/713-01.pdf)).
- **A Category V finding is a document a falsely accused parent should obtain and use.** The outline's false-allegations module (§4.3) never mentions that the categorization exists.
- Central registry placement can be challenged; MDHHS must hold a hearing to determine by a preponderance whether a record should be amended or expunged under MCL 722.627j(9) ([Child Protective Proceedings Benchbook](https://www.courts.michigan.gov/49bf88/siteassets/publications/benchbooks/cpp/cpp.pdf)).
- **CPS must notify the local FOC office** when there is an open FOC case and the investigation produces a preponderance finding, an emergency removal, court jurisdiction, or other safety-jeopardizing circumstances — and CPS **may** notify the FOC when a parent has made **three unfounded child abuse reports** ([SCAO FOCB memorandum on mandated reporters](https://www.courts.michigan.gov/4a8510/siteassets/court-administration/focb-memoranda/2012/mandatedreporters.pdf)). For a parent facing serial false referrals from a high-conflict ex, that last provision is a concrete, citable remedy the outline does not contain.

### 2.9 Emergency ex parte practice — thin

The outline references temporary orders but not the ex parte framework and its short clock. MCR 3.207(B) requires an objection or motion to rescind or modify within **14 days after service**; the FOC then attempts resolution within 14 days and a hearing is set within 21 days of the motion. The form is [FOC 61, Objection to Ex Parte Order and Motion to Rescind or Modify](https://www.courts.michigan.gov/496b3f/siteassets/forms/scao-approved/foc61.pdf), with FOC 62 as the modifying order; plain-language explanation at [Michigan Legal Help](https://michiganlegalhelp.org/resources/family/ex-parte-orders-family-court); rule text at [MCR 3.207](https://casetext.com/rule/michigan-court-rules/michigan-court-rules/chapter-3-special-proceedings-and-actions/subchapter-3200-domestic-relations-actions/rule-3207-ex-parte-temporary-and-protective-orders). **VERIFY BEFORE RELYING:** amendments to MCR 3.207 and 3.210 have been under consideration in ADM File 2021-27 ([proposed amendment](https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/proposed-and-recently-adopted-orders-on-admin-matters/proposed-orders/2021-27_2024-09-11_formor_propamdmcr3.207-3.210.pdf)); the drafting model must confirm current text before the guide states these numbers.

Also missing: the countervailing rule that a court may not enter an order changing an ECE without first holding an evidentiary hearing on clear and convincing evidence (MCR 3.210(C)(1)) — which is the reader's defense when the *other* side gets an ex parte order flipping the children.

### 2.10 Parenting-time factors as distinct from best-interest factors

The outline treats MCL 722.23 as the only factor list. There is a second one: MCL 722.27a(7) lists the factors the court may consider in setting the frequency, duration, and type of parenting time — special needs, nursing infants, likelihood of abuse or neglect of the child, likelihood of abuse of a parent, travel burden, whether a parent can be expected to comply with the order, whether a parent has frequently failed to exercise time, and threatened or actual detention/concealment, with an express carve-out that a custodial parent's temporary residence in a DV shelter is not evidence of intent to conceal ([MCL 722.27a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27a); [SCAO Establishing Parenting Time checklist](https://www.courts.michigan.gov/4ab6e0/siteassets/publications/benchbooks/qrms/family/domestic-relations/establishing-parenting-time-checklist.pdf)). Factors (f) and (g) — compliance and failure to exercise — are the alienated parent's statutory hooks, and they are not in the outline.

### 2.11 The temporary-order / ECE trap — the single most important missing strategic warning

The outline covers ECE as doctrine (Lesson 7.1) but never as a *trap*. The trap: an established custodial environment is a question of fact about how the child actually lives, and "it makes no difference whether that environment was created by a court order, without a court order, in violation of a court order, or by a court order that was subsequently reversed" (*Hayes v Hayes*, 209 Mich App 385, 388 (1995), quoted in [COA unpublished opinion](https://cases.justia.com/michigan/court-of-appeals-unpublished/302626-7.pdf?ts=1396126000); see also [Hayes summary](https://case-law.vlex.com/vid/hayes-v-hayes-docket-887302332)). SCAO's own judicial training states that temporary orders "do not automatically create ECE (and sometimes they do)" ([MJI/FOCB ECE material](https://www.courts.michigan.gov/4adec3/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/developing-an-understanding-of-the-established-custodial-environment/nov2024_mjifocb_ecematerial_zubac2.pdf)); Wayne County's judicial training says flatly that custody orders alone do not establish a custodial environment ([3rd Circuit custody training](https://www.3rdcc.org/docs/default-source/divisions/family-juvenile/custody-training--juvenile-revised.pdf?sfvrsn=f36622ca_0)).

**Operational consequence for the reader:** if you agree to a temporary order giving the other parent primary care "just for now," and the case takes 14 months, you may have to overcome by **clear and convincing evidence** an ECE that your own signature helped create. This warning belongs on page one of the strategy lesson, not buried in a doctrine lesson at the back. It is the highest-value single sentence in the entire treatise and the outline does not contain it.

### 2.12 Other genuine omissions, briefly

- **Tax and dependency exemption.** Michigan courts have general authority to allocate the federal dependency exemption (*Fear v Rogers*, 207 Mich App 642, 645 (1994), discussed at [Kershaw Vititoe & Jedinak](https://www.monroecountylawyers.com/blog/2019/10/who-gets-to-claim-the-tax-exemptions-for-minor-children-in-michigan/)), **but federal law controls execution**: the noncustodial parent must attach a signed Form 8332 or substantially similar document, regardless of what the state order says ([IRS, Dependents FAQ](https://www.irs.gov/faqs/filing-requirements-status-dependents/dependents/dependents-7); [Form 8332](https://www.irs.gov/pub/irs-pdf/f8332.pdf)). And Form 8332 does **not** transfer head-of-household status, the child and dependent care credit, or the EITC ([Michigan Legal Help](https://michiganlegalhelp.org/resources/income-tax/am-i-eligible-child-tax-credit)). The practical drafting tip: build the Form 8332 obligation, and a conditioning clause tied to support compliance, into the judgment language.
- **Stays pending appeal and stays of enforcement** (MCR 7.209 family) — omitted along with appeals.
- **Frivolous-filing exposure running against the reader** — MCR 1.109(E)(5)–(7) signature/verification and MCL 600.2591 sanctions. A guide that encourages aggressive motion practice owes the reader the downside.
- **Motions for reconsideration** (MCR 2.119(F), 21 days) — the cheap first move before an appeal, and a common way to preserve issues.
- **Right of first refusal, exchange logistics, supervised parenting time and supervised exchange providers** in Genesee County.
- **Support modification mechanics** — the FOC review cycle, the change-of-circumstances threshold, imputation of income to a voluntarily underemployed high-conflict ex, and the surcharge/arrearage machinery. The outline's §1.2 covers formula but not the litigation of income.
- **The psychological/self-management dimension.** The plan lists this nowhere. Litigating while alienated produces documented, predictable failure modes: over-filing, emotional testimony that reads as instability under best-interest factor (g) (mental and physical health), retaliatory motion practice that funds the other side's fee request under MCR 3.206(D)(1)(b), and burnout mid-case. A short module on affect management in the courtroom, on not litigating from the amygdala, and on when to stop filing is not soft content — it is factor-(g) risk management.

---

## 3. STRUCTURAL CRITIQUE

### 3.1 Mirroring ICLE's lesson numbering is the outline's central design error

ICLE's structure is organized around **the lawyer's workflow across a whole matter**: strategy, pretrial, judgment. That works for a practitioner who already knows the law and needs a task sequence. The pro se reader is in a categorically different position: they arrive **mid-crisis, at a specific procedural moment**, needing to know what to do in the next 14 days.

The mirroring produces three concrete defects:

1. **The foundational standards are at the back (Lesson 7).** ECE and *Vodvarka* are the framework that determines whether the reader has a case at all. A reader who reads Lesson 1 without Lesson 7 will build a strategy on a burden they don't understand. Standards must come first, or be folded into Lesson 1.
2. **Chronology fights the reader's actual entry points.** A reader whose ex just denied three exchanges does not need "Lesson 1: case strategy." They need enforcement. The outline has no entry-point routing.
3. **It creates a fictitious linearity.** ICLE's "Lesson 3: obtain final judgment" implies trial is the destination. For a high-conflict case the realistic destination is a long series of postjudgment motions. The outline's structure makes the postjudgment phase — where this reader will spend years — look like an appendix.

**Recommendation:** abandon ICLE mirroring in the reader-facing structure. Keep a **crosswalk appendix** mapping the new modules to ICLE lesson numbers, which preserves whatever institutional value the mirroring had (traceability for the author) without imposing a practitioner's mental model on a layperson.

### 3.2 Module granularity is inverted

The outline gives roughly equal weight to: mediation (§3.1), which most high-conflict cases either skip or fail; and enforcement (a bullet in §3.4), which this reader will use repeatedly. Meanwhile Lesson 6 ("pro se procedural survival") is a grab-bag of five loosely related topics — court rules, filing, fees, referees, limited-scope representation — that ranges from a two-paragraph topic (fee waivers) to a topic that deserves its own lesson (referee practice).

Granularity should follow **frequency of use × irreversibility of error**, not topical symmetry. On that metric:
- Referee practice and objection procedure: full lesson.
- Evidence foundations: full lesson.
- Enforcement: full lesson.
- Mediation: one short module.
- Fee waivers: a half-page in a logistics module.

### 3.3 Lesson 6 is misplaced

Procedural survival — how to file, what a praecipe is, what motion day looks like, how to address the court — is **orientation content**. It belongs immediately after the front matter, before any substantive lesson. A reader who does not know how to file cannot execute Lesson 1. Putting it sixth is an artifact of the ICLE mirroring.

### 3.4 The appendices are close to right but incomplete

- **Appendix A (form directory)** — good, but it must be a *populated table* with SCAO form number, title, current revision date, direct URL, and a "when you use it" column. A list of form numbers is a research assignment handed back to the reader.
- **Appendix D (glossary with terms only, definitions deferred)** — this is a defect, not a design choice. Deferring definitions to the drafting model with no controlled vocabulary guarantees the treatise will define "de novo," "ECE," and "proper cause" inconsistently across seven lessons. The glossary must be drafted **first** and every lesson must use its definitions verbatim.
- **Missing appendices:** (i) a **master deadline table** — every clock in the guide in one place, with the rule cite and the consequence of missing it; (ii) **evidence foundation scripts**, verbatim, for each exhibit type; (iii) a **motion-practice anatomy** with an annotated model motion, brief, notice of hearing, and proof of service; (iv) a **"what to do in the next 48 hours" triage router** keyed to the reader's situation; (v) a **when-you-must-hire-a-lawyer** list with hard triggers.

### 3.5 The front matter's "safety-first override" is right and should be strengthened into a structural element

The instinct is correct. It should not be a front-matter paragraph but a **recurring interstitial**: every module that could produce a dangerous action in a DV context (documentation, recording, confrontation about alienation, enforcement motions, mediation, relocation objections) needs its own DV variant box, because readers do not read front matter.

---

## 4. RISK REVIEW

I distinguish four risk classes. The ones that worry me most are not the obvious ones.

### 4.1 Criminal exposure created by following the guide

**Highest-severity risk in the document.** The outline tells the reader to document aggressively (§4.1) without bounding the methods. Foreseeable reader actions that are crimes:

- Sending a child into the other parent's home with a recording device — non-participant recording, felony exposure under MCL 750.539c per *Sullivan v Gray* ([Sullivan](https://law.justia.com/cases/michigan/court-of-appeals-published/1982/57301.html)).
- Installing a recording or observation device in the other parent's home or vehicle — MCL 750.539d.
- Accessing the other parent's email, phone, or social media accounts using remembered or shared credentials — this is the most common pro se evidence-gathering method and it is unlawful access; it also destroys the reader's credibility and can taint the evidence.
- GPS tracking the other parent's vehicle.

**Required mitigation:** a boxed, unmissable "Do Not Do These Things" module placed *before* the documentation module, with the statutory cites and the consequences stated in plain terms — criminal charge, evidence excluded, credibility destroyed, factor (g) and factor (j) damage, and potential PPO exposure.

### 4.2 Irreversible procedural loss

- **The 21-day appeal deadline** the guide never mentions (see §1.2 Failure 3).
- **The 21-day referee objection deadline** — the outline has it, correctly, but does not warn that the recommended order becomes final if no written objection is filed within 21 days after service under MCR 3.215(E)(1)(b)(ii) ([MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215)).
- **The 14-day ex parte objection deadline** under MCR 3.207(B).
- **Failure to build a record at the referee hearing**, which MCR 3.215(F)(2) may make unrecoverable.
- **Signing a stipulated temporary order that creates an adverse ECE** (see §2.11).
- **Signing an evaluation appointment order containing a hearsay waiver** (see §2.1(f)).

Each of these is a place where a reader following the outline as written can lose permanently without ever knowing a decision was made.

### 4.3 Bad-strategy traps the outline actively encourages

**(a) Leading with alienation.** Lesson 5 is a substantial portion of the guide and is framed as an affirmative theory. In practice, a pro se parent who opens by telling a judge "this is parental alienation" is heard as the high-conflict party. Michigan has no "parental alienation" cause of action; the conduct is relevant through best-interest factor (j) (willingness to facilitate a close relationship with the other parent) and through the parenting-time compliance factors in MCL 722.27a(7)(f)–(g). **The guide must teach the reader to plead conduct and let the court name it** — specific denied exchanges, specific messages, specific interference with medical and school access — rather than to plead a syndrome. As written, Lesson 5 will produce readers who sound like the internet.

**(b) Alienation "experts."** §5.3 contemplates experts without warning that the field is contested, that reunification-therapy and PAS-based expert testimony draws MRE 702 challenges, and that a retained alienation expert is expensive and can be neutralized on cross. An LGAL request is usually the better and cheaper move.

**(c) Volume as strategy.** Nothing in the outline discourages over-filing. MCR 3.215(F)(3) sanctions frivolous objections; MCR 3.206(D)(1)(b) lets the *other* party recover fees caused by noncompliance; MCR 1.109(E) and MCL 600.2591 sanction frivolous filings. A high-conflict litigant reading an empowering guide will file too much. The guide owes them a "when not to file" module.

**(d) Confrontation as documentation.** A reader taught to "document everything" will start texting the other parent to bait admissions. This produces bad exhibits, escalates conflict, and reads badly on factor (j). BIFF is mentioned in §4.2; the anti-pattern is not.

### 4.4 Safety risks in DV contexts

- The documentation module can produce exactly the behavior — surveillance, confrontation, provocation — that escalates danger. The DV interstitial must appear *inside* that module.
- Enforcement motions and contempt filings can trigger retaliation; the guide must pair enforcement instruction with safety planning and the option of FOC-mediated makeup time rather than direct contact.
- Mediation in a DV case has screening and opt-out considerations the outline does not address.
- The statutory protection that a custodial parent's temporary residence with the child in a DV shelter is **not** evidence of intent to conceal ([MCL 722.27a(7)(h)](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27a)) should be stated explicitly for a reader who fled and fears it will be used against them.
- **The guide should not assume the reader is the non-abusive party.** A treatise this specific will be read by both kinds of parent. That is an argument for teaching *process and proof* rather than for supplying tactics keyed to an assumed victim posture.

### 4.5 Where "VERIFY BEFORE RELYING" flags are insufficient

The flag mechanism is being asked to do work it cannot do. Three problems:

1. **It shifts the burden to the least-capable party.** A pro se reader in crisis cannot verify a court rule. If the drafting model cannot verify a fact, the guide should either omit it or state it as "confirm at the FOC counter before you rely on this" with a *specific* place to confirm — not a generic caution.
2. **It is applied to the wrong items.** The research file flags 15 items, mostly rule texts and case holdings — the *most* verifiable category. It does not flag the volatile category: **fee amounts, judicial and referee assignments, local administrative orders, office hours, form revision dates, and MiFILE/e-service status.** Those change without notice and are exactly what a Genesee-specific guide stakes its value on.
3. **Uniform flagging conveys uniform risk, which is false.** A wrong statement about mediation costs the reader an afternoon; a wrong statement about the objection deadline costs them the case. The guide needs a **two-tier system**: `⚠ TIME-CRITICAL — independently confirm before acting` for anything with a jurisdictional or forfeiture consequence, and `ℹ LOCAL PRACTICE — may have changed` for logistics. Every deadline in the guide should carry the first tier and appear in the master deadline table.

Additionally, the edition-stamp mechanism should be strengthened into a **"verified as of" date on each module**, plus an explicit statement that Michigan restyled its Rules of Evidence effective January 1, 2024, so pre-2024 secondary sources may cite superseded rule text and numbering. **VERIFY BEFORE RELYING:** the drafting model should confirm the restyling effective date against the SCAO adopting order ([ADM 2021-10 order text via ICLE](https://www.icle.org/contentfiles/MILawNews/rules/MRE/2021-10_2023-09-20_formor_amdmre.pdf)) before stating it.

---

## 5. REVISED OUTLINE

Design principles: (1) **orientation before doctrine, doctrine before tactics, tactics before forms**; (2) every module carries objectives, a deliverable, and an exercise; (3) evidence is a spine, not a chapter; (4) every deadline appears twice — in context and in the master table; (5) glossary is written first and used verbatim; (6) ICLE numbering survives only as a crosswalk appendix.

---

### FRONT MATTER

- **F.0 — How to Use This Guide in the Next 48 Hours (Triage Router).** A decision table: *"I was just served" / "I have a hearing this week" / "My ex denied parenting time" / "I got an ex parte order taking my kids" / "I've been accused of abuse" / "The FOC report just came out against me" / "I lost and want to appeal" / "I'm afraid for my safety."* Each routes to specific modules and states the governing deadline. **This is the most important page in the book.**
- **F.1 — Master Disclaimer as Content.** What this guide is, what it cannot be, what a lawyer does that this cannot, and the specific circumstances in which continuing pro se is a mistake.
- **F.2 — Safety Override.** DV, stalking, and threat scenarios; what to do first; Genesee/Flint resources.
- **F.3 — Edition and Verification Statement.** Verified-as-of date; two-tier flag legend (`⚠ TIME-CRITICAL`, `ℹ LOCAL PRACTICE`); note on the 2024 MRE restyling.
- **F.4 — Genesee Quick-Reference Card.** 7th Circuit Family Division and FOC addresses, phone, hours, MiFILE portal, motion-day mechanics, praecipe procedure, current filing fees. `ℹ LOCAL PRACTICE`

---

### MODULE 1 — HOW THIS SYSTEM ACTUALLY WORKS (Orientation)
*Replaces old Lesson 6; moved to the front.*

- **1.1 Who Is Who.** Judge, domestic relations referee, FOC caseworker, FOC investigator, LGAL/GAL/child's attorney, evaluator, mediator, clerk. What each can and cannot decide.
- **1.2 The Two Tracks.** Referee track vs. judge track; when each applies; why the referee hearing is usually the real trial.
- **1.3 Filing Mechanics.** MiFILE and paper filing; caption and format under MCR 1.109; the praecipe; notice of hearing; proof of service; the 9-day service rule for motions. `ℹ LOCAL PRACTICE`
- **1.4 Fees and Waivers.** Filing and motion fee schedule; fee waiver (MC 20) — eligibility, form, what happens next. `ℹ LOCAL PRACTICE`
- **1.5 Courtroom Conduct and Self-Presentation.** Forms of address; where to stand; what to bring; what judges read as instability; time discipline.
- **1.6 Getting Some Help Without Hiring Full Counsel.** Limited-scope appearance (MCR 2.117(B), form MC 516); ghostwriting; consulting-only arrangements; Genesee legal aid, MSU/UM law clinics, Michigan Legal Help, SBM lawyer referral. `ℹ LOCAL PRACTICE`
- *Deliverable:* a completed practice motion caption + notice of hearing + proof of service.
- *Exercise:* red-flag spotting — five filing errors that get a motion rejected at the counter.

---

### MODULE 2 — THE STANDARDS THAT DECIDE YOUR CASE
*Moved from old Lesson 7 to the front. Nothing downstream makes sense without it.*

- **2.1 The Established Custodial Environment.** MCL 722.27(1)(c) definition; ECE can exist in one home, both, or neither; ECE is a question of *fact about how the child lives*, not about what an order says — *Hayes v Hayes*, 209 Mich App 385 (1995).
  - **⚠ BOXED WARNING — THE TEMPORARY ORDER TRAP.** Agreeing to a temporary order that makes the other parent the primary caregiver can create an ECE you must later overcome by **clear and convincing evidence**. Never sign a "just for now" order without reading this section. Cite [MJI/FOCB ECE training](https://www.courts.michigan.gov/4adec3/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/developing-an-understanding-of-the-established-custodial-environment/nov2024_mjifocb_ecematerial_zubac2.pdf).
- **2.2 The Two Burdens.** Preponderance vs. clear and convincing; which applies when; why the court must decide ECE *before* reaching best interests.
- **2.3 The Gatekeeper: Proper Cause or Change of Circumstances.** *Vodvarka* (custody) vs. *Shade* (parenting time) thresholds; why most pro se modification motions die here; what facts clear the bar. `⚠` — the drafting model must verify *Vodvarka v Grasmeyer*, 259 Mich App 499 (2003) and *Shade v Wright*, 291 Mich App 17 (2010) citations and holdings directly.
- **2.4 The Twelve Best-Interest Factors.** MCL 722.23(a)–(l), each with (i) what it means, (ii) what evidence proves it, (iii) how a high-conflict opponent attacks it. Factor (j) flagged as the alienation factor; factor (k) as DV; factor (g) as the reader's own credibility exposure.
- **2.5 The Parenting-Time Factors — a Separate List.** MCL 722.27a(7)(a)–(i); factors (f) and (g) as the compliance hooks ([MCL 722.27a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27a); [SCAO checklist](https://www.courts.michigan.gov/4ab6e0/siteassets/publications/benchbooks/qrms/family/domestic-relations/establishing-parenting-time-checklist.pdf)).
- **2.6 Joint vs. Sole; Legal vs. Physical.** MCL 722.26a; the ability-to-cooperate requirement and why it cuts against joint legal custody in high-conflict cases — including against the reader.
- *Deliverable:* Best-Interest Evidence Matrix — 12 factors × (my evidence / their likely evidence / witness / exhibit / admissibility route).
- *Exercise:* worked example — apply *Vodvarka* to three fact patterns, two of which fail.

---

### MODULE 3 — EVIDENCE: HOW TO PROVE ANYTHING
*New. The spine of the treatise. Placed before all tactical modules.*

- **3.1 Where the Rules Apply — and Where They Don't.** **MRE apply at referee hearings (MCR 3.215(D)(1))** and at trial. They do **not** apply to in camera child interviews (MRE 1101(b)(6)) or to the court's consideration of an FOC report under MCL 552.505(1)(g)/(h) (MRE 1101(b)(9)) ([Michigan Rules of Evidence](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf)).
- **3.2 Relevance and the Judge's Patience.** MRE 401/402/403; why "everything bad she ever did" loses.
- **3.3 Hearsay in Ninety Seconds.** The definition; the four questions to ask before offering any statement.
- **3.4 The Rule That Wins Cases: Party-Opponent Statements.** MRE 801(d)(2) — **anything the other parent said, texted, emailed, or posted is not hearsay when you offer it against them.** Worked examples.
- **3.5 The Exceptions You Will Actually Use.** MRE 803(1) present sense impression, 803(2) excited utterance, 803(3) then-existing state of mind, 803(4) statements for medical diagnosis, 803(5) recorded recollection, 803(6) business records (school, medical, therapy), 803(8) public records (police reports, CPS documents — with the law-enforcement caveat).
- **3.6 ⚠ The Child-Hearsay Problem.** **MRE 803A (tender-years) does not apply in custody cases** — it reaches only criminal and juvenile delinquency proceedings ([SCAO Benchbook](https://www.courts.michigan.gov/4a3004/siteassets/publications/benchbooks/sabb/sabbresponsivehtml5.zip/SABB/Ch_6_Evidence/Tender-Years_Exception.htm)). What to do instead: non-truth purposes, MRE 803(3), the in camera interview (MCR 3.210(C)(5), limited to reasonable preference), an LGAL, a treating therapist, or the party-opponent route.
- **3.7 Authentication — There Is No Shortcut in Michigan.** MRE 901; Michigan's MRE 902 has no equivalent of FRE 902(13)/(14), so digital records cannot be self-authenticated by certificate ([Michigan MRE](https://www.courts.michigan.gov/492ca5/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf); [FRE 902](https://www.law.cornell.edu/rules/fre/rule_902)). **Verbatim foundation scripts** for: text thread, screenshot, email, photo with metadata, voicemail, OFW/TalkingParents export, social-media post, school record, medical record, police report.
- **3.8 Your Custody Journal — What It Is and Isn't.** It is memory-refresher material (MRE 612), impeachment material, recorded recollection in narrow circumstances (MRE 803(5)), and the outline for your own testimony. **It is generally not an exhibit when you offer it for its truth.** How to keep one that survives cross-examination: contemporaneous, factual, dated, no conclusions, no editorializing, no retroactive additions.
- **3.9 ⚠ RECORDING — READ BEFORE YOU RECORD.**
  - Lawful: recording a conversation **you are part of** — *Sullivan v Gray*, 117 Mich App 476 (1982) ([Sullivan](https://law.justia.com/cases/michigan/court-of-appeals-published/1982/57301.html)); confirmed for participants in *AFT Michigan v Project Veritas* (E.D. Mich., Mar. 30, 2026) ([Butzel](https://www.butzel.com/alert-butzel-prevails-in-long-running-michigan-eavesdropping-statute-litigation); [Detroit News](https://www.detroitnews.com/story/news/politics/2026/04/03/federal-judge-upholds-michigans-one-party-consent-recording-law/89449448007/)).
  - **Felony:** recording a conversation you are **not** part of — including **sending your child with a recorder** into the other parent's home; and installing a device in a private place (MCL 750.539c, 750.539d). Penalty up to 2 years and/or $2,000.
  - Also unlawful/self-defeating: accessing the other parent's accounts, GPS-tracking their vehicle, reading their mail.
  - Even lawful recordings must be authenticated (§3.7) and can antagonize a judge.
- **3.10 Exhibits and Trial Binders.** Numbering, pre-marking, copies for court/witness/opponent, exhibit list, stipulations to admissibility, objections you will hear and how to respond.
- *Deliverable:* an exhibit list with an admissibility route stated for every item.
- *Exercise:* practice script — lay the foundation for a text thread, out loud, three times.

---

### MODULE 4 — YOUR STRATEGY AND YOUR THEORY OF THE CASE
*Old Lesson 1, now downstream of standards and evidence.*

- **4.1 Define the Outcome.** What you are actually asking for, in order language.
- **4.2 Build the Theory.** One sentence a judge can repeat; how conduct evidence maps onto factors.
- **4.3 The Case Assessment.** Honest strengths/weaknesses; what your opponent will say about you; factor (g) self-audit.
- **4.4 Cost, Time, and Energy Budget.** Realistic timeline for a contested Genesee custody case; what each stage costs; when to spend on limited-scope counsel.
- **4.5 Settlement Posture.** What is worth trading; why joint legal custody with a non-cooperative party often fails; what to never concede (ECE-affecting temporary terms, hearsay waivers in evaluation orders, open-ended relocation consent).
- *Deliverable:* one-page case theory memo.

---

### MODULE 5 — CHILD SUPPORT
*Old Lesson 1.2, expanded.*

- **5.1 The Michigan Child Support Formula.** Income determination, overnights, the offset, health care and child care. `⚠` — the drafting model must verify current MCSF manual section numbers and the current supplement year directly against SCAO before stating any section number or bracket.
- **5.2 Proving the Other Parent's Income.** Documents to demand; imputation for voluntary unemployment or underemployment; the self-employed/cash-income problem; what the FOC will and won't dig for.
- **5.3 Deviation.** The statutory deviation factors and how to request one on the record.
- **5.4 Modification, Review, and Arrears.** The FOC review cycle; retroactivity limits; surcharge; enforcement against you and by you.
- **5.5 FOC Services — Opt In or Opt Out.** What opting out actually costs you.
- *Deliverable:* completed income worksheet with source documents identified.

---

### MODULE 6 — MOTIONS, TEMPORARY ORDERS, AND EMERGENCIES
*Old Lesson 2.3, expanded, with ex parte practice added.*

- **6.1 Anatomy of a Motion.** Motion, brief, notice of hearing, proposed order, proof of service; MCR 1.109(E) signature and verification — **and the sanctions exposure it creates** (MCL 600.2591).
- **6.2 Temporary Orders.** What they do; the ECE consequence (cross-ref 2.1); how to structure a temporary order that protects your position.
- **6.3 Ex Parte Orders — Getting One.** Grounds; the irreparable-injury showing; why most are denied; the credibility cost of an unsupported request.
- **6.4 ⚠ Ex Parte Orders — Fighting One.** **14 days from service** to file an objection or motion to rescind or modify (MCR 3.207(B)); FOC resolution attempt within 14 days; hearing within 21 days of motion. Form [FOC 61](https://www.courts.michigan.gov/496b3f/siteassets/forms/scao-approved/foc61.pdf); plain-language walkthrough at [Michigan Legal Help](https://michiganlegalhelp.org/resources/family/ex-parte-orders-family-court). `⚠ VERIFY` — amendments proposed in [ADM 2021-27](https://www.courts.michigan.gov/siteassets/rules-instructions-administrative-orders/proposed-and-recently-adopted-orders-on-admin-matters/proposed-orders/2021-27_2024-09-11_formor_propamdmcr3.207-3.210.pdf).
- **6.5 Your Shield: The Evidentiary Hearing Requirement.** A court may not enter an order changing an ECE without first holding an evidentiary hearing on clear and convincing evidence — MCR 3.210(C)(1) ([MCR 3.210](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-210)). Contested custody hearing within 56 days; decision within 28 days after the hearing.
- **6.6 Motions for Reconsideration.** MCR 2.119(F), 21 days; palpable-error standard; when it is worth filing.
- **6.7 ⚠ When NOT to File.** Sanctions under MCR 1.109(E) and MCL 600.2591; fee exposure under MCR 3.206(D); the judicial-patience budget; the "three motions rule of thumb."
- *Deliverable:* a complete motion packet, ready to file.
- *Exercise:* self-assessment — score a draft motion against a 10-point rejection checklist.

---

### MODULE 7 — DISCOVERY AND GETTING THE DOCUMENTS
*Old Lesson 2.1, corrected.*

- **7.1 What Discovery Is For in a Custody Case.** Discovery is usually about income, records, and third-party accounts — not about winning the narrative.
- **7.2 Party Discovery.** Interrogatories, requests for production, requests to admit; the MCR 2.300-series limits and timing. `⚠ VERIFY` current numeric limits.
- **7.3 ⚠ Subpoenas — the Two-Track Rule for Pro Se Litigants.**
  - **Hearing/trial subpoenas:** MCR 2.506(B)(1) — a subpoena signed by an attorney of record **or the clerk of the court** has the force of a judge's order; as a pro se party you obtain a **clerk-issued** [MC 11](https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc11.pdf). Serve at least **2 days** before testimony, **14 days** before when documents are requested ([MCR 2.506](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-506)).
  - **Discovery subpoenas to non-parties:** MCR 2.305(A)(1) — "a represented party may issue a subpoena to a non-party… **An unrepresented party may move the court for issuance of non-party discovery subpoenas**" ([MCR 2.305](https://www.courtrules.net/michigan/michigan-court-rules/rule-2-305)). **You must file a motion. You cannot self-issue.**
- **7.4 Getting Specific Records.** School (and FERPA); medical and therapy (and HIPAA/privilege, including the child's therapist); police reports and CAD logs; employment and payroll; MDHHS/CPS records and their separate process ([MDHHS subpoena](https://www.michigan.gov/mdhhs/inside-mdhhs/legal/subpoena)); phone records; bank records.
- **7.5 Connecting Discovery to Admissibility.** Every subpoena should be planned backward from the MRE 803(6) or 803(8) foundation you will need — including subpoenaing the *custodian of records*, not just the records.
- **7.6 When the Other Side Won't Comply.** Motion to compel; costs; the fee hook in MCR 3.206(D)(1)(b).
- *Deliverable:* a discovery plan mapping each needed fact → source → mechanism → admissibility route.

---

### MODULE 8 — THE FRIEND OF THE COURT
*Old Lesson 2.2, expanded, with the report paradox added.*

- **8.1 What Genesee FOC Does.** Investigation, recommendation, enforcement, support administration. `ℹ LOCAL PRACTICE`
- **8.2 The Custody/Parenting-Time Investigation.** What the investigator does; the interview; what to bring; what to never say; whether the FOC must address ECE (it is not statutorily required, though a judge may request it — [MJI Investigation Myths](https://www.courts.michigan.gov/4a2436/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/custody-parenting-time-investigation-myths/custody-and-parenting-time-investigation-myths_material.pdf)); [SCAO Custody and Parenting Time Investigation Manual](https://www.courts.michigan.gov/4932e6/siteassets/publications/manuals/foc/cp_investigationmnl.pdf).
- **8.3 ⚠ The FOC Report Paradox.** The judge may *read* the report — MRE 1101(b)(9) — but the report "is not admissible as evidence unless both parties agree to admit it," may be used only for background and context, and the court's findings must rest on competent evidence adduced at the hearing (*Duperon v Duperon*, 175 Mich App 77, 79 (1989)) ([Duperon](https://www.casemine.com/judgement/us/59148af2add7b0493451a3c2)). **Practical rules: (i) a favorable report does not carry your burden — put in your proofs anyway; (ii) do not stipulate to admission of an unfavorable report; (iii) you have the right to review it and object before decision (MCR 3.210(C)(6)).**
- **8.4 Objecting to the Recommendation.** Grounds; how to write an objection that is specific enough; timing.
- *Deliverable:* an FOC interview preparation sheet and a draft objection.

---

### MODULE 9 — THE REFEREE HEARING AND THE OBJECTION
*Promoted to a full module. Old §2.5.*

- **9.1 What a Referee Hearing Actually Is.** **The Michigan Rules of Evidence apply** (MCR 3.215(D)(1)). Treat it as a trial. A record is made electronically or stenographically, and you may make a contemporaneous copy (MCR 3.215(D)(4)) ([MCR 3.215](https://www.courtrules.net/michigan/michigan-court-rules/rule-3-215)).
- **9.2 Building the Record.** Why everything must go in here; how to make an offer of proof when evidence is excluded; how to get an objection and a ruling on the record.
- **9.3 The Recommendation.** Referee must issue findings and a recommendation within 21 days; **the recommended order becomes final if no written objection is filed within 21 days after service** (MCR 3.215(E)(1)).
- **9.4 ⚠ Writing an Objection That Works.** MCR 3.215(E)(4) — the objection "must include a clear and concise statement of the specific findings or application of law to which an objection is made." Template: identify the finding, state why it is wrong, cite the record.
- **9.5 ⚠ What "De Novo" Really Means.** The judicial hearing must be held within 21 days of the objection. The court **must** allow the parties to present live evidence — but under MCR 3.215(F)(2) it **may** prohibit evidence on unobjected findings, **may** treat unobjected findings as conclusive, and **may** bar new evidence or new witnesses absent a showing they were unavailable at the referee hearing. If you rely on the referee-hearing record, you must give notice and you pay for the transcript.
- **9.6 ⚠ The Cost of a Bad Objection.** MCR 3.215(F)(3) — costs and attorney fees if the objection is found frivolous or filed for delay.
- **9.7 Interim Effect.** MCR 3.215(G) limits on giving interim effect by administrative order — notably not for orders changing custody or domicile.
- *Deliverable:* a completed, specific written objection with record cites.
- *Exercise:* red-flag spotting — three defective objections and why each fails.

---

### MODULE 10 — ENFORCEMENT: WHEN THEY VIOLATE THE ORDER
*New full module. The tool this reader will use most.*

- **10.1 Two Doors.** FOC complaint vs. your own motion to show cause. Trade-offs: cost, speed, control, safety.
- **10.2 The FOC Route.** File a written parenting-time complaint (MCL 552.511b); the FOC must apply the makeup policy, commence civil contempt, or move to modify ([MCL 552.641](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-641)); FOC 16 notice ([FOCB memo 2025-02](https://www.courts.michigan.gov/4a4d85/siteassets/court-administration/focb-memoranda/2025/2025-02.pdf)).
- **10.3 Makeup Parenting Time — the Details That Give You Leverage.** Same type and duration; within one year; **the denied parent chooses when**; one week's notice for weekend/weekday time, 28 days for holiday or summer; the other parent has 21 days to respond and **failure to respond counts as agreement** ([MCL 552.642](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-642)).
- **10.4 Contempt.** Elements: valid order, notice, ability to comply, willful noncompliance. Remedies under MCL 552.644: additional terms, modified parenting time, makeup time, fine up to $100, jail up to 45 days first / 90 subsequent, work release, license suspension, community corrections, FOC supervision ([MCL 552.644](https://law.justia.com/codes/michigan/2006/mcl-chap552/mcl-552-644.html); [MJI Contempt Benchbook ch. 5](https://www.courts.michigan.gov/49aeda/siteassets/publications/benchbooks/contempt/contemptresponsivehtml5.zip/Contempt/Ch_5_Common_Forms_of_Contempt/Contempt_for_Violation_of_Parenting_Time_Order.htm)). Bad-faith sanctions escalate $250/$500/$1,000 plus costs; license suspension carries a 21-day hearing-request window ([MCL 552.645](https://law.justia.com/codes/michigan/chapter-552/statute-act-295-of-1982/section-552-645/)).
- **10.5 Proving a Denial.** The enforcement evidence packet: the order, the schedule, the exchange log, the messages, the third-party witness, the police "keep the peace" report. Foundation cross-ref to Module 3.
- **10.6 Myths.** Support and parenting time are independent — you may not withhold either because of the other; police generally will not enforce a custody order at the curb; a child "refusing to go" is not a defense but is a serious factual problem ([MJI Enforcement Myths](https://www.courts.michigan.gov/4a509e/siteassets/educational-materials/mji/court-professional/videos-and-webinars/2024-2025/custody-and-parenting-time-enforcement-myths/custody-and-parenting-time-enforcement-myths-material.pdf)).
- **10.7 Safety Overlay.** Enforcement can trigger retaliation; when to route through the FOC instead of direct contact.
- *Deliverable:* an enforcement packet — exchange log, motion to show cause, exhibit list.

---

### MODULE 11 — HIGH-CONFLICT AND ABUSIVE OPPONENTS
*Old Lesson 4, restructured so documentation follows evidence law.*

- **11.1 Communication Discipline.** Single channel (OFW/TalkingParents/AppClose); BIFF method; never respond in kind; the anti-pattern of baiting for admissions.
- **11.2 Documentation That Survives Cross-Examination.** Cross-ref 3.8. Contemporaneous, factual, dated, no conclusions.
- **11.3 ⚠ Do Not Do These Things.** Boxed: non-participant recording (felony), device installation, account access, GPS tracking, involving the child as an intelligence asset, disparagement in the child's presence. Cross-ref 3.9.
- **11.4 Domestic Violence.** Safety planning; PPO basics and the Genesee PPO process; how DV enters the custody analysis through MCL 722.23(k) and MCL 722.27a(7)(c)–(d); the DV-shelter protection in MCL 722.27a(7)(h) ([MCL 722.27a](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27a)); local resources. `ℹ LOCAL PRACTICE`
- **11.5 Managing Yourself.** Affect regulation in the courtroom; why factor (g) is your exposure; the over-filing spiral; therapy as both self-care and evidence risk (records may be discoverable); financial and time budgeting; support networks.
- *Deliverable:* a communication protocol and a one-page safety plan.

---

### MODULE 12 — FALSE ALLEGATIONS AND CPS
*Old §4.3, substantially expanded.*

- **12.1 The First 24 Hours.** Do not contact the accuser; do not talk to police without counsel; **this is a hard stop — consult a criminal attorney**; preserve everything; continue to comply with all orders.
- **12.2 How a CPS Investigation Works.** The five categories under MCL 722.628d; Category I–III mean a preponderance finding; **Category V means the referral was based on false or erroneous information** ([MDHHS CPS process](https://www.michigan.gov/mdhhs/adult-child-serv/abuse-neglect/childrens/report-process/investigation-process-and-results/childrens-protective-services-investigation-process); [PSM 713-01](https://mdhhs-pres-prod.michigan.gov/olmweb/EX/PS/Public/PSM/713-01.pdf)).
- **12.3 Getting and Using the Outcome.** How to request your determination letter; how to get CPS records into the custody case (subpoena route, Module 7.4); central registry expungement — MDHHS must hold a hearing on a preponderance standard under MCL 722.627j(9) ([Child Protective Proceedings Benchbook](https://www.courts.michigan.gov/49bf88/siteassets/publications/benchbooks/cpp/cpp.pdf)).
- **12.4 ⚠ Serial False Reports — a Concrete Remedy.** CPS must notify the local FOC of specified findings when there is an open FOC case, and **may notify the FOC when a parent has made three unfounded child abuse reports** ([SCAO FOCB memorandum](https://www.courts.michigan.gov/4a8510/siteassets/court-administration/focb-memoranda/2012/mandatedreporters.pdf)). How to raise this pattern under best-interest factor (j).
- **12.5 Rebuilding Credibility.** Supervised parenting time as a bridge; voluntary evaluations (and their risks); how not to over-argue innocence in family court.
- **12.6 Scope Boundary.** This module does not cover defending an abuse/neglect petition or a criminal charge. Hire counsel.

---

### MODULE 13 — ALIENATION AND INTERFERENCE
*Old Lesson 5, reframed away from syndrome-pleading.*

- **13.1 ⚠ Frame It as Conduct, Not a Diagnosis.** Michigan has no "parental alienation" cause of action. The conduct is relevant through MCL 722.23(j) (willingness to facilitate the other parent's relationship) and MCL 722.27a(7)(f)–(g) (compliance and failure to exercise). **Plead specific acts; let the court name the pattern.** A pro se parent who leads with "alienation" is often heard as the high-conflict party.
- **13.2 The Interference Inventory.** Denied exchanges; blocked calls; withheld school and medical information; unilateral schedule changes; disparagement; enrolling the child in activities during your time; refusing to add you as an emergency contact; the "child refuses" pattern.
- **13.3 Proving It.** Records with a clean admissibility route: school and medical records under MRE 803(6) and attendance/pickup logs; the other parent's own messages under MRE 801(d)(2); third-party exchange witnesses; provider testimony; the exchange log.
- **13.4 ⚠ The Child's Statements.** Cross-ref 3.6 — MRE 803A does not apply here. The legitimate routes and their limits.
- **13.5 Who Can Speak for the Child.** LGAL vs. GAL vs. attorney for the child vs. custody/psychological evaluator: role, appointment mechanism, cost, who pays, and evidentiary status — an LGAL's report is not admissible unless all parties stipulate (MCL 722.24(3), per the [SCAO checklist](https://www.courts.michigan.gov/48dbed/siteassets/publications/benchbooks/qrms/family/domestic-relations/child-custody-dispute-involving-third-person-checklist.pdf)). **For most pro se alienation cases an LGAL request is the highest-leverage motion available.** `⚠ VERIFY` MCR 3.219 file-access provisions before stating them.
- **13.6 ⚠ Before You Sign the Evaluation Order.** Read it for a **hearsay-waiver clause**; submitting to the evaluation and failing to object at admission can waive your objection ([SBM e-Journal summary](https://www.michbar.org/opinions/content_search_detail/EJournalNumber/86190)). Also negotiate: scope, who pays, collateral contacts, access to raw data, and deposition rights.
- **13.7 Experts and Their Limits.** MRE 702/703; why PAS-framed expert testimony draws challenges; cost; the cross-examination risk.
- **13.8 Remedies Realistically Available.** Makeup time, compensatory time, contempt, a parenting coordinator, therapy orders, a change in legal custody, and — rarely — a custody change. What courts actually grant.
- *Deliverable:* an interference inventory table with admissibility route per row.

---

### MODULE 14 — MEDIATION AND SETTLEMENT
*Old Lesson 3.1, compressed.*

- **14.1 When Mediation Is Ordered.** MCR 3.216; the Genesee CDRP. `ℹ LOCAL PRACTICE`
- **14.2 DV Screening and Opt-Out.** How to raise safety concerns; shuttle mediation; when to decline.
- **14.3 Preparing.** Your must-haves, trade-ables, and walk-aways.
- **14.4 ⚠ Reading a Proposed Consent Order Before You Sign.** ECE implications; hearsay waivers; relocation consent; vague language that becomes unenforceable; who drafts; entry mechanics.
- *Deliverable:* a settlement-parameters worksheet.

---

### MODULE 15 — TRIAL
*Old Lessons 3.2–3.3, consolidated.*

- **15.1 Pretrial Mechanics.** Pretrial statement, witness list, exhibit list, trial brief; the 56-day and 28-day timing rules in MCR 3.210(C).
- **15.2 Witnesses.** Who is credible to a family judge (teachers, doctors, coaches, neighbors) and who is not (your mother, your new partner, your best friend, standing alone); subpoenaing them (Module 7.3); preparing them without coaching.
- **15.3 Direct Examination of Yourself.** Narrative structure; using MRE 612 to refresh from your journal; not editorializing.
- **15.4 Cross-Examination.** Short leading questions; one fact per question; when to stop; not arguing with the witness.
- **15.5 Getting Exhibits In.** Live execution of the Module 3.7 scripts.
- **15.6 Objections.** The six you will make and the six you will hear, with responses.
- **15.7 Closing.** Structure it factor by factor.
- **15.8 ⚠ Preserving Error.** Object, state grounds, make an offer of proof, get a ruling on the record — because without it there is nothing to appeal.
- *Deliverable:* a complete trial notebook.
- *Exercise:* practice script — five-minute direct of yourself, timed.

---

### MODULE 16 — THE ORDER AND WHAT COMES AFTER
*Old §3.4, plus what the outline omitted.*

- **16.1 Findings and the Order.** The court must make findings on each best-interest factor; decision within 28 days of a contested custody hearing (MCR 3.210(C)(3)).
- **16.2 Drafting the Judgment or Order.** Specificity as self-defense: exact times, exact locations, holiday tables, transportation, right of first refusal, communication protocol, decision-making allocation, information-access clauses, **the dependency-exemption clause and a Form 8332 execution obligation** ([IRS Form 8332](https://www.irs.gov/pub/irs-pdf/f8332.pdf); [IRS FAQ](https://www.irs.gov/faqs/filing-requirements-status-dependents/dependents/dependents-7)), and a change-of-address/relocation notice clause.
- **16.3 Entry Mechanics.** The seven-day rule / settle-order practice; objections to a proposed order.
- **16.4 Attorney Fees.** MCR 3.206(D) — the need-and-ability route and the **noncompliance route**; the evidence a request requires; honest note that a pro se party generally cannot recover for their own time, and the strategic use of a noncompliance award to fund limited-scope counsel ([COA 2026 opinion](https://www.michbar.org/Portals/0/opinions/appeals/2026/030926/85341.pdf); [Michigan Bar Journal](https://www.michbar.org/file/barjournal/article/documents/pdf4article883.pdf)).
- **16.5 Living Under the Order.** Calendar it; comply exactly even when they don't; document.

---

### MODULE 17 — RELOCATION AND CHANGE OF DOMICILE
*New.*

- **17.1 The 100-Mile Rule.** MCL 722.31 — legal residence changes of more than 100 miles require court approval or consent; exceptions where the residences are already more than 100 miles apart or the move brings them closer ([MCL 722.31](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-31)).
- **17.2 The Five Factors.** MCL 722.31(4)(a)–(e), including the domestic-violence factor.
- **17.3 The Four-Step Analysis.** Factors by preponderance → does the move alter the ECE → if yes, clear and convincing best interests → modified parenting-time schedule ([Speaker Law](https://www.speakerlaw.com/blog/100-mile-rule-procedural-misstep-requires-remand-re-evaluation); [SCAO checklist](https://www.courts.michigan.gov/48dc1e/siteassets/publications/benchbooks/qrms/family/domestic-relations/changing-childs-legal-residence-checklist.pdf)).
- **17.4 Out-of-State Moves and the Jurisdiction Overlay.** UCCJEA basics; why leaving first is catastrophic.
- **17.5 Opposing a Move.** Evidence that matters; proposing a workable long-distance schedule as a fallback.
- *Deliverable:* a relocation response outline.

---

### MODULE 18 — WHEN YOU LOSE: RECONSIDERATION, APPEAL, AND STAY
*New. Explicitly reverses the plan's out-of-scope call, limited to preservation and deadlines.*

- **18.1 ⚠ THE 21-DAY CLIFF.** A claim of appeal must be filed within 21 days (MCR 7.204(A)(1)(a)). **This deadline is jurisdictional. Miss it and the right is gone.** Put this on the reader's calendar the day any adverse final order enters.
- **18.2 ⚠ Appeal of Right vs. Leave — the Domestic-Relations Asymmetry.** A postjudgment order is final and appealable of right when it "grants or denies a motion to change legal custody, physical custody, or domicile" (MCR 7.202(6)(a)(iii)) ([MCR 7.202](https://www.courtrules.net/michigan/michigan-court-rules/rule-7-202)); MCR 7.203(A)(1) limits the appeal to that portion. **An order changing only parenting time generally requires an application for leave.** See *Rains v Rains*, 301 Mich App 313 (2013) on when an order "affects" custody ([opinion](https://www.courts.michigan.gov/4a399b/siteassets/case-documents/uploads/opinions/final/coa/20130613_c312243(55)_rptr_90o-312243-final.pdf)).
- **18.3 The Standard of Review — Why Most Appeals Lose.** MCL 722.28: affirm unless the findings are against the great weight of the evidence, there was a palpable abuse of discretion, or clear legal error on a major issue ([MCL 722.28](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-28); overview at [Michigan Bar Journal](https://www.michbar.org/file/barjournal/article/documents/pdf4article3753.pdf)).
- **18.4 Motions for Reconsideration First.** MCR 2.119(F), 21 days; cheaper, faster, and sometimes sufficient.
- **18.5 Stays.** The order remains in effect during appeal unless stayed; how to request one.
- **18.6 ⚠ HARD STOP — GET A LAWYER.** Appellate practice is a specialty. This module exists to protect the deadline and preserve the record, not to teach you to write a brief. Options: appellate limited-scope consultation, SBM referral, law school appellate clinics.

---

### APPENDICES

- **Appendix A — Master Deadline Table.** Every clock in one place: 9-day motion service; 14-day ex parte objection (MCR 3.207(B)); 14-day document-subpoena notice (MCR 2.506(C)(1)); 21-day referee recommendation and 21-day objection (MCR 3.215(E)); 21-day judicial hearing (MCR 3.215(F)(1)); 21-day makeup-PT response (MCL 552.642); 21-day reconsideration (MCR 2.119(F)); 21-day claim of appeal (MCR 7.204); 28-day holiday/summer makeup notice; 28-day post-hearing decision and 56-day contested hearing (MCR 3.210(C)). Each row: deadline, trigger event, rule cite, **consequence of missing it**.
- **Appendix B — Form Directory.** Populated table: SCAO number, title, revision date, direct URL, when used, common errors. Includes MC 11, MC 20, MC 516, FOC 16, FOC 61, FOC 62, FOC 68, IRS Form 8332. `ℹ` revision dates must be re-verified at publication.
- **Appendix C — Evidence Foundation Scripts.** Verbatim Q&A scripts per exhibit type (from Module 3.7), formatted for reading at the podium.
- **Appendix D — Model Documents.** Annotated motion, brief, notice of hearing, proof of service, objection to referee recommendation, motion to show cause, motion for LGAL appointment, motion for issuance of non-party subpoenas (MCR 2.305(A)(1)), objection to ex parte order, proposed order.
- **Appendix E — Genesee County Resource Directory.** Court, FOC, CDRP, legal aid, DV services, supervised visitation and exchange providers, co-parenting and reunification therapists, self-help resources. `ℹ LOCAL PRACTICE — verify all contact information before publication.`
- **Appendix F — Master Glossary.** Drafted **first**, with definitions, used verbatim throughout. Minimum terms: adjournment; affidavit; best interests of the child; burden of proof; change of circumstances; clear and convincing evidence; consent order; contempt (civil vs. criminal); custody (legal / physical / joint / sole); de novo hearing; deviation; discovery; domicile; established custodial environment (ECE); ex parte; evidentiary hearing; exhibit; findings of fact; Friend of the Court; foundation; GAL; hearsay; imputation of income; in camera; interrogatory; judgment; LGAL; makeup parenting time; mediation; motion; MCSF; notice of hearing; objection; offer of proof; order to show cause; parenting time; party-opponent statement; praecipe; preponderance of the evidence; privilege; pro se / self-represented; proof of service; proper cause; referee; request for production; sanctions; self-authentication; show cause; stay; stipulation; subpoena (trial vs. discovery); temporary order; testimony; UCCJEA; *Vodvarka* threshold.
- **Appendix G — Do Not Do These Things.** Consolidated criminal- and credibility-risk list with statutory cites.
- **Appendix H — When You Must Hire a Lawyer.** Hard triggers: criminal charge or police interview; abuse/neglect petition; any appeal; interstate or UCCJEA jurisdiction dispute; termination of parental rights; expert-versus-expert psychological evaluation; a custody change already granted against you.
- **Appendix I — ICLE Crosswalk.** Maps each module above to the original ICLE lesson numbering, preserving traceability without imposing a practitioner's structure on the reader.

---

## 6. Verification ledger — what I confirmed, and what remains open

**Confirmed against primary or near-primary sources in this review:** MCR 3.215(D)(1), (D)(4), (E)(1), (E)(4), (F)(1)–(3), (G); MCR 3.210(C)(1), (C)(3), (C)(5), (C)(6), (C)(8); MCR 2.506(B)(1), (C)(1); MCR 2.305(A)(1); MCR 7.202(6)(a)(iii); MCR 3.207(B); MCR 3.206(D); MCL 722.27a(7); MCL 722.28; MCL 722.31; MCL 552.641, 552.642, 552.644, 552.645; MCL 722.628d and the CPS category scheme; MRE 902 contents and the absence of a FRE 902(13)/(14) analogue; MRE 1101(b)(6) and (b)(9); the criminal/juvenile-only scope of MRE 803A; *Duperon* (FOC report inadmissible absent agreement); *Hayes* (ECE independent of court orders); *Sullivan v Gray* and the 2026 *AFT Michigan v Project Veritas* ruling; MCL 722.24(3) LGAL report inadmissibility; the CPS→FOC notification provisions including the three-unfounded-reports provision; IRC §152(e)/Form 8332 mechanics.

**Still unverified and flagged for the drafting model — do not state these without independent confirmation:** exact *Vodvarka* and *Shade* citations and holdings; current MCSF manual section numbers, deviation-factor list, and offset brackets; MCR 2.300-series numeric discovery limits; MCR 3.219 file-access provisions; the current text of MCR 3.207 and 3.210 in light of ADM File 2021-27; the MRE restyling effective date; all Genesee County specifics — filing and motion fees, judicial and referee assignments, FOC office procedures, CDRP details, MiFILE/e-service status, and local administrative orders; SCAO form revision dates; the currency of the 2000-era Michigan Parenting Time Guideline.

**Most important single recommendation, if only one change is made:** insert Module 3 (Evidence) and the boxed temporary-order/ECE warning in Module 2.1. Everything else in this critique is improvement; those two are the difference between a guide that helps and a guide that misleads.
