---
name: fct-case-research
description: "(family-court-toolkit) Structured Michigan case law research workflow with verification. Use when searching for case authority, verifying citations, or building legal arguments requiring specific Michigan precedent."
context: fork
agent: Explore
allowed-tools: WebSearch, WebFetch, Read, Grep
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/case-research` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Michigan Case Law Research Protocol

Execute this research workflow for any Michigan family law question. Follow ALL steps - do not skip verification.

## Step 1: Frame the Research Question

- State the specific legal issue
- Identify the applicable MCL/MCR provisions
- List key search terms (legal + factual)

## Step 2: Primary Authority Search

### Statutes & Rules
1. Search for current MCL text at legislature.mi.gov
2. Check for recent amendments (last 2 years)
3. Verify MCR provisions at courts.mi.gov

### Case Law (PUBLISHED ONLY)
Search in this order:
1. **Michigan Supreme Court (MSC)**: Google Scholar → filter Michigan → Supreme Court
2. **Michigan Court of Appeals (MCOA)**: Google Scholar → filter Michigan → Court of Appeals → Published only
3. **Cross-reference**: courts.mi.gov/opinions-orders

For each case found:
```
Case: [Name], [Mich/Mich App citation]; [NW2d citation] ([year])
Docket: [number]
Holding: [1-2 sentence summary]
Relevance: [how it applies to the research question]
Status: [Current / Modified by X / Overruled by Y]
```

### CRITICAL: Verify each citation
- Check that the case actually exists (search by docket number)
- Confirm it hasn't been overruled or significantly modified
- Mark any unverifiable citation as [UNVERIFIED - MANUAL CHECK REQUIRED]

## Step 3: Secondary Authority Search

Check these sources for supporting material:
- MJI Benchbooks (Family Division, Evidence, DV)
- FOCB Policy memoranda
- MDHHS/CPS protocols
- SCAO administrative orders and forms
- ICLE publications (if accessible)

## Step 4: Opposing Authority Search

**Always research the other side:**
- Search for cases reaching opposite conclusions
- Identify distinguishing facts
- Note any trend in recent decisions
- Flag if the area of law is unsettled

## Step 5: Compile Results

Return findings in this format:

```
## RESEARCH RESULTS: [Topic]

### Research Question
[Precise question]

### Primary Authority
#### Favorable
1. [Citation + holding + relevance]

#### Unfavorable/Distinguishable
1. [Citation + holding + why distinguishable]

### Secondary Authority
1. [Source + relevant section]

### Statutory Framework
- [MCL/MCR provisions with key language]

### Research Gaps
- [What couldn't be found or verified]

### Recommended Next Steps
- [Additional research or fact development needed]
```

## HARD RULES
- NEVER cite unpublished Michigan Court of Appeals opinions as binding authority
- NEVER fabricate case names, docket numbers, or holdings
- ALWAYS flag uncertainty: "I could not independently verify this citation"
- ALWAYS note the date of your search for currency purposes
- Michigan jurisdiction ONLY - refuse federal or other state research

## Added 2026-09-07 from Drive intake (source: case-law-index, case_law_table.md, and related AI-chat research leads)

Every citation below is `[VERIFY]` — none of these opinions have been independently read or Shepardized by
this member; treat this as a research lead list, not confirmed authority. De-identified: no party names.

### Seminal Michigan custody case leads (by topic)

**Established Custodial Environment (ECE) / proper cause / change of circumstances**
- *Vodvarka v Grasmeyer*, 259 Mich App 499; 675 NW2d 847 (2003) — defines "proper cause" (has or could have
  a significant effect on the child's life) and "change of circumstances" (material, post-order change);
  already cross-referenced in `order-modification`. `[VERIFY]`
- *Fletcher v Fletcher*, 447 Mich 871; 526 NW2d 889 (1994) — three-tiered standard of review; ECE defined as
  an environment of significant duration where the child looks to the custodian for guidance, discipline,
  necessities, and comfort; once ECE exists, the movant needs clear and convincing evidence to change it.
  `[VERIFY]`
- *Shade v Wright*, 291 Mich App 17; 805 NW2d 1 (2010) — a more expansive change-of-circumstances standard
  applies to parenting-time-only modifications that do not alter the ECE. `[VERIFY]`
- *Sims v Verbrugge*, 322 Mich App 205; 911 NW2d 233 (2017) — ECE analysis does not apply to an *initial*
  custody determination (only to modifying an existing one). `[VERIFY]`
- *Remy v Remy*, 295 Mich App 146; 818 NW2d 792 (2011) — a temporary custody order can itself establish an
  ECE. `[VERIFY]`
- *Polasky v Polasky*, 309 Mich App 383; 871 NW2d 819 (2015) — lead on the "a parent who wrongfully withholds
  contact cannot benefit from an ECE established through that wrongful conduct" argument. `[VERIFY]`

**Parental alienation / gatekeeping (Factor j)**
- *Martin v Martin*, 331 Mich App 224; 952 NW2d 530 (2020) — a parent's interference with parenting time and
  enlistment of a child to monitor the other parent supported a custody change under factors (j) and (l).
  `[VERIFY]`
- *Kuebler v Kuebler*, 346 Mich App 633; 13 NW3d 339 (2023) — fabricated or exaggerated abuse allegations
  used to justify restricting the other parent's access can constitute manipulative/alienating conduct
  warranting a custody change. `[VERIFY]`
- *Amawi v Deming*, No. 362538 (Mich App July 20, 2023) (unpublished) — cited alongside *Martin*/*Kuebler* on
  alienation as a basis to modify custody; unpublished, persuasive only. `[VERIFY — unpublished]`

**"As parties agree" / parenting-time specificity (see also `parenting-plan`)**
- *Simon v Simon*, No. 371011 (Mich App Dec 17, 2024) (unpublished) — an "as mutually agreed" schedule may be
  inadequate once a parent requests specificity under MCL 722.27a. `[VERIFY — unpublished]`
- *Jensen v Thiel*, No. 371728 (Mich App Jan 17, 2025) (unpublished) — courts must adopt agreed parenting-time
  terms unless clear and convincing evidence shows they are not in the child's best interests. `[VERIFY — unpublished]`
- *Arquette v Carr*, No. 370691 (Mich App Nov 26, 2024) (unpublished) — "specific terms" means explicit,
  particular, and definite; "reasonable and liberal parenting time" does not meet that standard. `[VERIFY — unpublished]`

**Independent psychological evaluation vs. FOC (see also `custody-evaluation-summary`)**
- *Harvey v Harvey*, 470 Mich 186; 680 NW2d 835 (2004) — the circuit court has a non-delegable duty to
  independently determine the child's best interests regardless of FOC or ADR involvement. `[VERIFY]`
- *Taylor v Ungaro*, No. 355930 (Mich App June 17, 2021) (unpublished) — trial courts may but need not appoint
  an independent psychological expert when the FOC investigation is thorough. `[VERIFY — unpublished]`
- *McIntosh v McIntosh*, 282 Mich App 471; 768 NW2d 325 (2009) — psychological evaluations, whichever source,
  are evidence to be weighed, not conclusive on any factor. `[VERIFY]`

**Other leads surfaced in the intake (not yet cross-checked against any archived primary)**
- *Ireland v Smith* — appears in the source material under two different citations, 214 Mich App 235 (1995)
  and 451 Mich 457 (1996), which are almost certainly the Court of Appeals and Supreme Court dispositions of
  the *same* case (facilitation-principle / moral-fitness holding). A third, clearly wrong variant —
  "547 Mich. 270 (2021)" — also appears in the source material; Michigan's official reporter has not reached
  volume 547 as of this writing, so that citation is almost certainly an AI hallucination. Do not cite any of
  these until the real reporter citation and year are confirmed. `[VERIFY — citation conflict, one variant
  suspected fabricated]`
- *Diez v Davey*, 307 Mich App 366 (2014) — moral-fitness factor can reach a parent's choice of household
  associates when it affects the child. `[VERIFY]`
- *Meadows v Meadows*, 194 Mich App 670 (1992) — an early Michigan case recognizing parental alienation as a
  custody concern. `[VERIFY]`
- *Welch v Grew*, Mich Ct App No. 357161 (2021) and *Heusser v Heusser*, Mich Ct App No. 354343 (2021) —
  both unpublished; cited in source material for "stonewalling"/"withholding information" as Factor (j)/(k)
  evidence. `[VERIFY — unpublished, high priority since both were only found in un-vetted AI chat exports]`
- *Brown v Brown*, 332 Mich App 1 (2020) — cited for adopting the Domestic Violence Prevention and Treatment
  Act (MCL 400.1501(d)) definition of "domestic violence," which is not limited to physical violence and
  includes mental harm/control tactics, for use in custody proceedings. `[VERIFY]`

### Non-violent coercive control matrix (42-entry reference)

A Drive-intake file (`case_law_table.md`, mirrored in `Untitled document__354451de.docx`) contains a
42-entry matrix mapping non-violent coercive-control behaviors (child weaponization, stonewalling,
professional sabotage, identity destruction, triangulation, future-faking, economic abuse, substance
weaponization) to Michigan case law, the FOC Custody and Parenting Time Investigation Manual, and MJI
benchbook language, each with a source citation and short quote. It is a well-organized research lead list
but every entry is `[VERIFY]` — none of the underlying opinions or manual pages were independently
re-confirmed during this intake. Useful as a starting index for `behavioral-pattern-analyzer` /
`manipulation-patterns` work; do not cite an entry in a filing without pulling and reading the actual source
first.

> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — Drive intake mining, see
> `content/custody-guide/sources/DRIVE-INTAKE-LEDGER-2026-09-07.md`._
