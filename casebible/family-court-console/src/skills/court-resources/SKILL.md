---
name: fct-court-resources
description: "(family-court-toolkit) Michigan One Court of Justice resource directory. Courts.michigan.gov navigation, SCAO forms, published opinions, court rules, benchbooks, free case law sites, Genesee County 7th Circuit resources, and self-help tools."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/court-resources` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Michigan Court & Legal Research Resources

Comprehensive directory of Michigan legal resources for AI agents. Genesee County (7th Judicial Circuit) specific where applicable.

## Michigan One Court of Justice (courts.michigan.gov)

### Published Opinions
| Court | URL | Coverage |
|-------|-----|----------|
| Supreme Court | https://www.courts.michigan.gov/courts/supreme-court/opinions/ | 1945-present |
| Court of Appeals | https://www.courts.michigan.gov/courts/court-of-appeals/opinions/ | 1965-present |

- Searchable by case name, date, docket number, topic
- Published opinions only have precedential value
- Download as PDF for citation
- **Agent use**: Search for keywords like `"722.23" custody "best interest"`

### SCAO Forms (State Court Administrative Office)
- **Forms index**: https://www.courts.michigan.gov/administration/scao/forms/
- **URL pattern**: `https://www.courts.michigan.gov/siteassets/forms/[category]/[formcode].pdf`
- All forms freely downloadable as PDF

**Key Family Law Forms:**

| Code | Form Name | Use |
|------|-----------|-----|
| MC 01 | Summons and Complaint | Initiating domestic relations case |
| MC 03 | Judgment of Divorce | Final divorce judgment |
| CC 302 | Uniform Child Custody Jurisdiction Enforcement Act Affidavit | Required in custody cases |
| FOC 10 | Motion and Verification (FOC) | FOC motions |
| FOC 39 | Uniform Support Order | Child support orders |
| FOC 50 | Objection to Referee's Recommended Order | Objecting to FOC recommendation |
| FOC 61 | Response to Show Cause | Responding to contempt |
| FOC 65 | Motion Regarding Support | Modifying support |
| FOC 84 | Motion Regarding Parenting Time | Modifying parenting time |
| FOC 89 | Motion Regarding Custody | Modifying custody |
| CC 375 | Petition for PPO (Domestic) | Filing domestic PPO |
| CC 376 | Petition for PPO (Stalking) | Filing stalking PPO |
| CC 380 | PPO (Domestic Relationship) | The actual PPO order |
| CC 381 | PPO (Non-Domestic Stalking) | Stalking PPO order |

### Michigan Court Rules (MCR)
- **Full text**: https://www.courts.michigan.gov/rules-administration/court-rules/
- **Chapter 3 - Domestic Relations**: https://www.courts.michigan.gov/rules-administration/court-rules/chapter-3-special-proceedings/subchapter-32-domestic-relations/

**Key Rules:**

| Rule | Subject |
|------|---------|
| MCR 3.201 | Applicability of domestic relations rules |
| MCR 3.206 | Initiating a family case |
| MCR 3.210 | Custody proceedings |
| MCR 3.211 | Determining custody |
| MCR 3.213 | Mediation in custody disputes |
| MCR 3.214 | Change of domicile (100-mile rule) |
| MCR 3.215 | Child support |
| MCR 3.217 | Friend of the Court |
| MCR 2.302-2.313 | Discovery procedures |
| MCR 2.310 | Document production requests |
| MCR 2.312 | Requests for Admission |
| MCR 2.313 | Discovery sanctions |
| MCR 2.116 | Summary disposition |
| MCR 2.119 | Motion practice |

### Benchbooks & QRMs (Michigan Judicial Institute)
- **Hub**: https://www.courts.michigan.gov/education/mji/resources/benchbooks/

| Resource | Description | Custody Relevance |
|----------|-------------|-------------------|
| Family Division Benchbook | Custody, support, divorce procedures | Ch. 2 (Custody) — primary reference |
| Domestic Violence Benchbook | PPO, evidence, safety planning | Ch. 4 (PPO procedures) |
| Child Protective Proceedings Benchbook | Termination, placements | Maps to MCL 712A |
| Evidence Benchbook | MRE summaries, hearsay exceptions | Authentication (MRE 901), hearsay |
| Quick Reference Manuals | Checklists, flowcharts | Procedure validation |

All benchbooks are free PDFs.

### Self-Help Resources
- **Michigan Courts self-help**: https://www.courts.michigan.gov/self-help/
- Filing instructions, glossary, guides for pro se litigants

### ADR (Alternative Dispute Resolution)
- **SCAO ADR programs**: https://www.courts.michigan.gov/administration/scao/programs/adr/
- MCR 3.213 compliance for custody mediation

---

## Michigan Compiled Laws (MCL)

- **Primary site**: https://www.legislature.mi.gov
- **MCL browse**: https://www.legislature.mi.gov/Laws/MCL
- **Direct lookup pattern**: `https://www.legislature.mi.gov/Laws/MCL?objectName=MCL-[chapter]-[section]`
  - Example: `MCL-722-23` for Best Interest Factors

**Key Family Law Statutes:**

| MCL | Subject |
|-----|---------|
| 722.21-722.31 | Child Custody Act |
| 722.23 | Best Interest Factors (a)-(l) |
| 722.25 | Custody order requirements |
| 722.27 | Modification of custody orders |
| 722.27a | Domestic violence considerations |
| 722.31 | Change of domicile |
| 552.1-552.45 | Divorce Act |
| 552.101-552.163 | Support and Parenting Time Enforcement Act |
| 600.2950 | Personal Protection Orders (domestic) |
| 600.2950a | Personal Protection Orders (stalking) |
| 722.621-722.638 | Child Protection Law |
| 750.81 | Domestic violence assault |
| 750.81a | Aggravated domestic violence |
| 750.411h | Stalking |
| 750.411i | Aggravated stalking |

---

## Free Case Law Research Sites

### Tier 1: Primary (Official / Comprehensive)

| Site | URL | Michigan Coverage | Best For |
|------|-----|-------------------|----------|
| Michigan Courts Opinions | https://www.courts.michigan.gov/opinions/ | MSC + MCOA, 1945/1965-present | Official published opinions |
| Michigan Legislature | https://www.legislature.mi.gov/Laws/MCL | Full MCL, session laws, admin code | Statute lookup |
| Google Scholar | https://scholar.google.com | MI appellate/supreme ~1950-present | Keyword case searches |
| CourtListener | https://www.courtlistener.com | MI courts ~1990s-present, API available | API queries, recent opinions |

**Google Scholar search tips:**
- Filter to Michigan: Select "Michigan courts" under state filter
- Family law query: `"MCL 722.23" "best interest" custody`
- PPO query: `"600.2950" "personal protection order" domestic violence`

### Tier 2: Secondary (Useful Free Supplements)

| Site | URL | Michigan Coverage | Best For |
|------|-----|-------------------|----------|
| Justia | https://law.justia.com/cases/michigan/ | MI cases ~1950-present, MCL annotations | Statute + case cross-reference |
| Justia MI Statutes | https://law.justia.com/codes/michigan/ | Full MCL with annotations | Annotated statutes |
| Justia MI Court Rules | https://law.justia.com/codes/michigan/court-rules/ | Full MCR | Court rules lookup |
| Leagle | https://www.leagle.com | Selected MI appellate ~1990s-present | Quick citation lookup |
| FindLaw MI | https://www.findlaw.com/state/michigan-law.html | Summaries, statute overviews | Overview/secondary |

### Tier 3: Membership/Limited

| Site | URL | Access | Notes |
|------|-----|--------|-------|
| Casemaker | https://www.casemaker.com | MI State Bar members only | Full MCL, cases, admin code |
| Fastcase | https://www.fastcase.com | MI State Bar members only | Multi-state case search |
| Casetext | https://casetext.com | Paid only (Thomson Reuters) | Skip — no free tier |

### Research Libraries

| Resource | URL | Notes |
|----------|-----|-------|
| Library of Michigan Law Library | https://www.michigan.gov/libraryofmichigan/public/law | On-site/public terminals |
| UMich Law LibGuides | https://libguides.law.umich.edu/free_and_low_cost | Curated free legal site lists |
| LOC Guide to MI Law | https://guides.loc.gov/law-us-michigan | Annotated links |

---

## Genesee County / 7th Judicial Circuit

### Court
- **7th Circuit Court**: https://7thcircuitgenesee.org/
- **Family Division**: https://7thcircuitgenesee.org/divisions/family-division/
- **Local Rules & Admin Orders**: https://7thcircuitgenesee.org/local-rules-administrative-orders/
- **Forms**: https://7thcircuitgenesee.org/forms/
- **Judges & Standing Orders**: https://7thcircuitgenesee.org/judges-standing-orders/
- **E-Filing (MiFILE)**: https://mifile.mi.gov/

### Clerk
- **Address**: 900 S. Saginaw St., Rm. 201, Flint, MI 48502
- **Phone**: (810) 257-3226

### Friend of the Court (Genesee County)
- **Website**: https://www.geneseecounty.gov/departments/friend_of_the_court/
- **Address**: 900 S. Saginaw St., Flint, MI 48502
- **Phone**: (810) 257-3528
- **Handbook**: https://www.geneseecounty.gov/departments/friend_of_the_court/handbook.php
- **Mediation**: https://www.geneseecounty.gov/departments/friend_of_the_court/mediation.php

### Legal Aid
- **Legal Services of Eastern Michigan (LSEM)**: https://lsem.org/
  - Flint office: 5331 Lapeer Rd., Flint, MI 48507
  - Phone: (810) 234-2621 / Intake: 1-888-783-8190
  - Family law clinics for custody/divorce

---

## Self-Help / Pro Se Resources

| Resource | URL | Description |
|----------|-----|-------------|
| Michigan Legal Help | https://michiganlegalhelp.org | Interactive forms, guides, court info |
| Michigan Legal Help - Family | https://michiganlegalhelp.org/resources/family | Custody, divorce, PPO, support |
| Michigan Legal Help - DV | https://michiganlegalhelp.org/resources/family/domestic-violence | DV-specific resources |
| Michigan Courts Self-Help | https://www.courts.michigan.gov/self-help/ | Filing guides, glossary |

---

## Agent Research Protocol

When researching Michigan law:

1. **Statute lookup**: legislature.mi.gov -> MCL direct URL
2. **Case law search**: Google Scholar (filter MI) -> keyword search
3. **Court rules**: courts.michigan.gov -> MCR chapter/section
4. **Forms**: courts.michigan.gov -> SCAO forms index
5. **Benchbook reference**: courts.michigan.gov -> MJI benchbooks
6. **Genesee-specific**: 7thcircuitgenesee.org -> local rules/forms
7. **Verify currency**: Check opinion not overruled, statute not amended
8. **Cross-reference**: Use Justia for annotated statutes, CourtListener API for recent opinions

**Citation format**: Bluebook standard for all Michigan citations.
