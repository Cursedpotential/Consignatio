# Project Guardrails and Expectations

**Status:** binding on every drafting pass, human or model.
**Adopted:** August 9, 2026.
**Relationship to other documents:** `custody_guide_outline_v2.md` Part 0 governs *how a module is built*. This document governs *what the project is allowed to become, who decides what, and when anything may reach a reader.* Where the two conflict, this document controls.

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — §3.1 CourtListener MCP path corrected (`toolkit-package/plugin/.mcp.json` no longer exists; registered in this plugin's own root `.mcp.json`)._

---

## 0. Amendment — August 9, 2026: two audiences, two gates

This document was written assuming publication to strangers. The project owner has clarified the primary use is **their own case**, without funds for counsel. That changes which gates apply when:

- **Working documents for the owner's own case:** the attorney-review gate does **not** block work. The owner bears their own risk and makes their own calls. What survives regardless: no sentence asserting a specific recording is lawful (unsettled law, criminal exposure); no template labeled filing-ready; unrecoverable-error points (jurisdictional deadlines, CPS/criminal overlap, UCCJEA) are stated plainly with pointers to **free** resources — Genesee Legal Resource Center, Legal Services of Eastern Michigan, YWCA PPO assistance, Michigan Legal Help, limited-scope referral — not to unaffordable full representation.
- **Anything later published for other readers:** the full §5 publication gate applies as written, including attorney review.

Local facts unconfirmable on a given day (weekends, office hours) are handled by the **PROVISIONAL** disposition — draft, mark, confirm when the office opens. Waiting is never required to keep working. See `PRE-DRAFTING-CHECKLIST.md` §E for the consolidated clerk-call list.

**Owner decision, August 9, 2026 (evening):** clerk confirmation is **not a drafting gate at all** — it is a **check-before-quoting / check-before-filing step that belongs to the owner**. Drafting proceeds through every clerk-dependent fact; the `ℹ PROVISIONAL` mark means exactly one thing to the reader: *verify this specific item with the court before you say it in a filing or rely on it at a counter.* No pass may hold work waiting on the clerk, and no pass may remove a PROVISIONAL mark without recording who confirmed the fact and when.

## 1. What this is

A self-help treatise on custody, parenting time, and child support for a self-represented parent in the 7th Judicial Circuit Court, Family Division, Genesee County, Michigan.

**It is legal information. It is not legal advice, and it never becomes legal advice.** No attorney-client relationship is created by it. It cannot be tailored to a reader's facts, and any sentence that starts to do so is a defect.

## 2. What this is not, and must never drift into

| Not | Why it matters |
|---|---|
| **A substitute for a lawyer** | The guide's own hard-stop matrix (outline §0.4, Appendix K) exists because some situations are unsurvivable without counsel. Every draft must make continuing pro se look like the *choice* it is, not the default. |
| **A filing service** | No template may be labeled "filing-ready." Every sample states the procedural posture and facts it assumes plus a "do not use if" list. |
| **A competing version of an official form** | Link the SCAO or Genesee form. Supply drafting aids only for the narrative attachments those forms do not generate. |
| **A weapon** | Every strategy carries its own limiter in the same section — not in a distant caveat. See §7. |
| **A diagnosis** | "Narcissist," "alienator," "PAS," and "coercive control" are banned as pleaded labels. The reader pleads dated conduct, the order term breached, and the statutory factor. |
| **A general Michigan guide** | Statewide law is labeled statewide; Genesee practice is labeled Genesee; one judge's policy is never generalized to all judges. |

## 3. Who decides what

The single most important guardrail. **A model's confidence is not authority.**

| Question type | Decided by | Evidence required |
|---|---|---|
| What a statute or court rule says | The drafting model, from **primary text in `sources/primary/`** | Verbatim quote + the document's own currency stamp |
| What a published case holds | The drafting model, from **the opinion itself** | Citation verified + holding read, not summarized from a secondary source |
| Whether a proposition is settled | **Nobody, if the sources conflict.** Present both positions under `⊗ COUNCIL CONFLICT` and route to counsel | — |
| Any Genesee County local fact | **The clerk, the FOC, or the assigned judge's chambers.** No model, ever | Named person or office, date of the call, what they said |
| The vicarious-consent recording question | **A licensed Michigan attorney.** No model, ever | Signed verification note replacing the `🔒` block |
| Whether a template is safe to publish | **A licensed Michigan attorney** | Same |
| Scope, sequencing, what ships | **The project owner** | — |

**Corollary:** if a drafting pass cannot satisfy the evidence column, it does not write the sentence. It writes the flag.

## 3.1 Research tooling — what each tool may and may not establish

| Tool | Legitimate use | Explicitly **not** authority for |
|---|---|---|
| **Archived primary PDFs** (`sources/primary/`) | Statute, court rule, evidence rule, local court rule, and formula text | Anything after the document's own currency stamp |
| **CourtListener MCP** (~~`toolkit-package/plugin/.mcp.json`~~ **corrected 2026-09-07: registered in this plugin's own root `.mcp.json` as the `courtlistener` server, restored 2026-09-07 from the August build; `toolkit-package/` no longer exists**, credential-free HTTP endpoint) | **Discovery** of opinions; citation, court, date, published/unpublished status | **It is not a citator.** It cannot support a Shepardize/KeyCite-style claim or any statement about negative treatment. Search results are leads, not holdings — read the opinion. |
| **MiCOURT Case Search** | **Assessed and deliberately not activated.** Requires OneCourtID/JIS permission, a subscription key, OAuth2 client credentials, and a court key; Starter returns only 10 results with no expansion | Docket metadata **never** establishes a holding, opinion text, reporter citation, publication status, or precedential weight. Never convert case-search metadata into legal authority. Never search sealed, suppressed, adoption, or otherwise restricted records. |
| **Exa / general web fetch** | Reaching primary hosts this environment cannot (e.g. `legislature.mi.gov`) | A secondary summary is never a substitute for the primary text it describes |

**Credential rule:** no API key, subscription key, client secret, OneCourtID, or OAuth credential goes into this repository, a prompt, or a commit — ever.

## 4. The four dispositions

Outline §0.3's flag tiers describe *reader-facing risk*. This is the separate, internal question of *what we actually know*. Every factual claim carries exactly one:

| Disposition | Meaning | May it ship? |
|---|---|---|
| **VERIFIED** | Quoted from an archived primary source, with that document's currency stamp recorded | Yes |
| **PROVISIONAL** | Sourced to the best available document, but the source is secondary, stale, or locally unconfirmable. Ships **only** with a visible marker naming what is unconfirmed and who can confirm it | Yes, marked |
| **CONFLICTED** | Sources disagree. Both positions stated; no resolution asserted | Yes, as a conflict |
| **UNVERIFIED** | We do not know | **No.** Cut it or flag it — never smooth it into confident prose |

**PROVISIONAL exists to solve a real contradiction.** Acceptance Test 2 demands a primary source and verification date for every claim, while §0.8 says every Genesee local fact is unconfirmable by any model. Read strictly, no Genesee module could ever ship — which would destroy the guide's reason for existing, since local specificity is precisely what a pro se parent cannot get elsewhere. Without this fourth state, the tests get quietly ignored during drafting, which would destroy their force everywhere else.

## 5. Publication gate

Nothing reaches a reader until all of the following are true. This list is the definition of "done" for the project, not for a module.

- [ ] Every **UNVERIFIED** claim is cut or visibly flagged.
- [ ] Every deadline appears in Appendix A with its **triggering event** named — entry, mailing, service, filing, notice sent, or occurrence — and the consequence of missing it.
- [ ] Every load-bearing legal proposition cites an **archived primary source**, not a commercial mirror.
- [ ] A **licensed Michigan attorney** has cleared: the recording module, every template, and the deadline table.
- [ ] Every **Genesee local fact** carries a confirmation date and the office that confirmed it, or is marked PROVISIONAL.
- [ ] The **safety override** appears in front matter and at the head of every module touching DV, PPO, CPS, or exchanges.
- [ ] No template is labeled filing-ready; every one carries its "do not use if" list.
- [ ] The **edition date** and the flag legend appear on the first page.

## 6. Maintenance

The guide has two clocks, and conflating them is how self-help material rots.

| Layer | Half-life | Review trigger |
|---|---|---|
| Statewide statutes, court rules, evidence rules, published cases | Long — years | Re-run `sources/fetch-sources.sh`, diff against `SHA256SUMS`, check each document's currency stamp |
| **Genesee local facts** — fees, judge and referee assignments, FOC procedure, local administrative orders, MiFILE status, form revisions | **Short — months** | Re-confirm with the clerk; treat anything older than **180 days** as stale |

Time-sensitive facts live in **one** change-controlled appendix and are referenced elsewhere, never restated in prose (Acceptance Test 12). Appendix M currently does not meet this standard and must be built out before publication.

Two known live risks: `courts.michigan.gov` URLs carry CMS-generated hex path segments that **have already changed once** in this project's lifetime (a 404 means moved, not withdrawn); and the Genesee motion-practice notice posted on the court's own site states only the MCR 2.119(C)(4) **filing** deadline while omitting the (C)(1) **service** periods — accurate but incomplete, which is its own kind of trap.

## 7. Symmetry rule

Every enforcement tool in this guide can be aimed at the reader:

- Best-interest factor (j) cannot be scored against **reasonable protective action** against sexual assault or domestic violence.
- MCL 552.644(3) defines "good cause" to include **child or party safety**.
- MCL 750.411h excludes conduct serving a **legitimate purpose** from harassment.
- MCL 600.2591 and MCR 3.215(F)(3) sanction **the reader's** frivolous filings.
- MCL 552.641(2)(a) closes the FOC route to a parent with repeated unwarranted complaints and unpaid costs.
- MCR 3.206(D)(2)(b) shifts fees **either** direction.

**Drafting rule: each strategy carries its own limiter in the same section.** Acceptance Test 9 is satisfied structurally, never by a disclaimer at the end.

## 8. The child

Acceptance Test 8, restated because it is absolute: **no exercise, template, or suggestion may ask the reader to interview, recruit, coach, debrief, task, diagnose, or emotionally rely on the child.** No recording of the child. No sending a child anywhere with a device. This is not a balancing test.

## 9. Escalation — stop and route out

Drafting stops and the text refers the reader outward on: immediate danger; any CPS or police contact; criminal exposure; a PPO where the reader is respondent; UCCJEA or interstate facts; any recording question; ICWA/MIFPA indicators; appellate deadlines; and any situation the guide did not contemplate.

**The scope boundary is stated plainly rather than silently omitted** — a reader who falls outside must be told so, and told where to go.

## 10. Sequencing

Adopted from `critical_review_outline_v2.md` §8. Before any module is drafted:

1. Fix **Appendix A** — corrections A-1 through A-6 and the five missing rows.
2. Re-anchor load-bearing citations to `sources/primary/`; apply verification-ledger corrections C-1 through C-6.
3. Add the **PROVISIONAL** disposition to Part 0.
4. Fold in gaps **G-1 through G-9**.
5. Define **Volume 1** and its ship criteria.

**Volume 1** is the reader's first 60 days: Front Matter, Modules 1–2, 4–10, 12–16, 26, and Appendices A, C, N. Trial practice, support, domicile, and appeals defer to Volume 2. The project's realistic failure mode is not a dangerous book — the gates are good enough to prevent that — it is a book that never finishes.

## 11a. Case-facts hygiene (added August 9, 2026 — Pass 1 finding)

The repo now carries material adjacent to a live case. Verified **private** on August 9, 2026; it stays private, and visibility is re-checked before any sharing decision. Even so:

- **Procedural posture only.** No narrative grievances, no characterizations of the other parent, no third-party names, and **never the child's name or birthdate** — anywhere, including commit messages and file names.
- **Every committed sentence must survive being read aloud in court.** Litigation-adjacent materials have a way of surfacing; write accordingly.
- The neutral posture wording in `DRAFTING-HANDOFF.md` §1 is the template for how case facts are recorded.

## 11. Standing instruction to any drafting model

1. Quote primary text from `sources/primary/`. Do not paraphrase an operative legal standard.
2. Do not write a case holding from memory. Read the opinion or do not cite it.
3. Do not resolve a `⊗ COUNCIL CONFLICT` or a `🔒 ATTORNEY MUST VERIFY` block. Carry it forward.
4. Do not state a Genesee fee, phone number, address, judge, referee, or form revision without a source and a date.
5. When the outline and this document conflict, follow this document and say so.
6. When you find an error in the outline, the research, the ledger, or **your own earlier output**, correct it in place and record it. This project has already corrected itself six times; that is the process working.
7. Prefer cutting a claim to hedging it. A reader in crisis cannot act on a hedge.
