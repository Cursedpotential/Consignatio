---
name: fct-custody-evaluation-summary
description: "(family-court-toolkit) Summarizes custody evaluation reports into a structured memorandum covering evaluator credentials, methodology, parental findings, recommendations, and best-interests factor mapping. Use when reviewing custody evaluations, preparing for custody hearings or settlement conferences, or onboarding to contested parenting matters."
tags:
- litigation
- summarization
- summary
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/custody-evaluation-summary` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Custody Evaluation Summary

Produces a structured memorandum from custody evaluation reports for quick reference in contested parenting matters.

## Prerequisites

Before starting, collect:

- Custody evaluation report(s) with evaluator identity/credentials
- Psychological assessments, if administered
- Home study documents, if separate from main report
- Applicable jurisdiction for best-interests statute mapping

## Quick Start

1. Extract evaluation overview metadata into a structured table
2. Catalog methodology (interviews, testing, home visits, collaterals)
3. Build side-by-side parental findings comparison
4. Summarize children's statements and observations
5. Extract custody and parenting-time recommendations
6. Map findings to jurisdictional best-interests factors
7. Note contested issues and credibility concerns
8. Flag safety concerns and next steps

## Memorandum Sections

### 1. Evaluation Overview

Extract into a table:

| Field | Extract |
|---|---|
| Evaluator | Name, credentials, license number |
| Evaluation dates | Start–end range |
| Appointing authority | Court-ordered / stipulated / party-retained |
| Report date | Final report date |
| Children | Names, DOBs, grade/school |
| Parents | Names, residences, household members |

### 2. Methodology

Check which procedures the evaluator employed:

- Parent interviews (number, total hours)
- Child interviews (format, observed/recorded)
- Psychological testing (instruments: MMPI-2, MCMI-IV, PAI, etc.)
- Home visits (dates, duration, attendees)
- Collateral contacts (list by name/role)
- Record review (medical, school, court, CPS, law enforcement)
- Parent-child observations (structured/unstructured)

Flag any standard element the evaluator omitted.

### 3. Findings by Parent

Side-by-side comparison for each parent:

| Category | Parent A | Parent B |
|---|---|---|
| Strengths | | |
| Concerns | | |
| Psychological testing results | | |
| Home environment | | |
| Parenting capacity | | |
| Mental health | | |
| Substance abuse | | |
| DV / abuse history | | |
| Willingness to co-parent | | |

### 4. Children's Statements and Observations

- Direct quotes where significant (age-appropriate only)
- Observed parent-child dynamics
- Child's expressed preferences (note age and maturity assessment)
- Emotional/behavioral concerns noted by evaluator

### 5. Collateral Source Input

| Source (Name/Role) | Key Information Provided |
|---|---|
| | |

### 6. Recommendations

| Element | Recommendation |
|---|---|
| Legal custody | Joint / sole — to whom |
| Physical custody | Primary residence / shared schedule |
| Regular parenting time | Weekday + weekend schedule |
| Holiday/vacation | Key provisions |
| Conditions/restrictions | Supervised visitation, therapy, substance monitoring |
| Therapeutic interventions | For children, parents, or family |
| Contingency plans | If evaluator provided any |
| Modification triggers | Circumstances warranting future review |

### 7. Best-Interests Factor Mapping

Map findings to the jurisdiction's statutory factors. Common factors (adjust per state):

| Statutory Factor | Evaluator Finding |
|---|---|
| Child's adjustment to home/school/community | |
| Mental and physical health of all parties | |
| Parental capacity for love, affection, guidance | |
| Child's reasonable preference (if sufficient maturity) | |
| History of DV or abuse | |
| Willingness to encourage other-parent relationship | |
| Stability and continuity of caregiving | |
| Other jurisdiction-specific factors | |

### 8. Contested Issues and Credibility

- Where recommendations align or conflict with each parent's position
- Methodology or conclusion concerns raised by either party
- If multiple evaluations exist: side-by-side comparison of differing findings

### 9. Next Steps

- Immediate safety concerns requiring urgent intervention
- Transition timeline for recommended arrangements
- Support services and follow-up evaluation schedule

## Pitfalls and Checks

- **Objectivity** — Present findings without advocacy; do not opine on correctness
- **Attribution** — Use direct quotes for significant observations; cite page numbers
- **Jurisdiction** — Confirm the correct best-interests statute before mapping; factors vary by state
- **Sensitivity** — Redact or flag children's statements inappropriate for filings
- **Multiple evaluations** — Present side-by-side comparisons; do not privilege one over another

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — removed a leftover "Key changes made" editorial/changelog block (porting notes about this file's own prior edit) that did not belong in shipped skill content._

## Added 2026-09-07 from Drive intake (source: assignment__b646b8d0.docx, assignment__981b4c31.docx)

### Independent expert evaluation vs. an FOC-conducted evaluation (Michigan)

All citations `[VERIFY]` — not independently read during this intake:

- Michigan trial courts have discretion to order a psychological evaluation by an independent
  court-appointed expert, but are **not required** to when the FOC's own investigation is adequate.
  *Taylor v Ungaro*, No. 355930 (Mich App June 17, 2021) (unpublished) — upheld denial of an independent
  evaluator where the FOC investigator's report was thorough and the concerns raised were not "unusual or
  extraordinary."
- Whichever source performs the evaluation, the court retains a **non-delegable duty to independently
  determine the child's best interests** — *Harvey v Harvey*, 470 Mich 186 (2004).
- A psychological evaluation, from the FOC or an independent expert, is **evidence to be weighed, not
  conclusive** on any statutory factor — *McIntosh v McIntosh*, 282 Mich App 471 (2009), which cites
  *Harvey* for the non-delegable-duty point above.
- **Practical framing for a motion requesting an independent evaluator:** ground the request in a specific,
  articulable gap in the FOC's competence or scope (e.g., a need for forensic psychological expertise beyond
  standard FOC investigator training) rather than a general preference for a "second opinion" — *Taylor*
  suggests courts deny requests framed as the latter when the FOC's work was otherwise adequate.

> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — Drive intake mining, see
> `content/custody-guide/sources/DRIVE-INTAKE-LEDGER-2026-09-07.md`._
