---
name: fct-secondary-source-auditor
description: "(family-court-toolkit) Comprehensive audit of all Michigan family law secondary admissible sources. Checks MJI Benchbooks, FOCB policies, MDHHS/CPS protocols, SCAO forms/orders, and ICLE publications for relevant authority on a given issue. Use when building a complete evidentiary foundation beyond primary case law."
context: fork
agent: Explore
allowed-tools: WebSearch, WebFetch, Read
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/secondary-source-auditor` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Secondary Source Auditor - Michigan Family Law

When invoked with a legal issue or topic, systematically search ALL secondary source categories for relevant authority. This is a comprehensive audit - do not skip any category.

## Source Categories to Audit

### 1. MJI Benchbooks & Quick Reference Materials

Search for relevant sections in:
- **Family Division Benchbook**: Custody, parenting time, support, property division checklists and flowcharts
- **Domestic Violence Benchbook**: DV indicators, PPO standards, impact on custody
- **Child Protective Proceedings Benchbook**: CPS standards, neglect/abuse criteria, jurisdictional issues
- **Evidence Benchbook**: Foundation requirements, hearsay exceptions, expert testimony standards

**Search strategy**: WebSearch for `site:courts.mi.gov MJI benchbook [topic]` and `Michigan Judicial Institute [topic] quick reference`

**Output per source**:
```
Source: MJI [Benchbook Name], Chapter [X], Section [X.X]
Topic: [specific topic covered]
Key Content: [relevant guidance, checklist items, or standards]
URL: [if available online]
Currency: [last updated date if known]
Relevance: [how it applies to the issue]
```

### 2. Friend of the Court Bureau (FOCB) Policies & Memoranda

Search: courts.mi.gov/administration/offices/friend-of-the-court-bureau/

Check for:
- Policy memoranda on the specific issue
- FOC standards for custody investigations
- Parenting time guidelines (Michigan Parenting Time Guideline)
- Support calculation protocols
- Mediation/investigation procedures
- Recent updates or policy changes

**Search strategy**: WebSearch for `site:courts.mi.gov friend of the court [topic]` and `FOCB policy memorandum [topic]`

### 3. MDHHS / CPS / FIA Protocols

Search: michigan.gov/mdhhs

Check for:
- **Substance abuse screening**: MAST (Michigan Alcohol Screening Test), BAST, CAGE, AUDIT protocols
- **Psychological evaluation standards**: Court-ordered eval protocols, custody eval guidelines
- **Child welfare manuals**: PSM (Policy and Standards Manual) sections on investigations, safety assessments
- **Mandated reporter guidelines**: What triggers CPS involvement
- **Treatment standards**: What constitutes adequate treatment/compliance for various conditions

**Search strategy**: WebSearch for `site:michigan.gov mdhhs [topic]` and `michigan CPS [topic] protocol`

### 4. SCAO Administrative Orders & Forms

Search: courts.mi.gov/administration/admin/

Check for:
- Administrative orders affecting family law procedures
- Current SCAO form numbers and versions for relevant filings
- Recent procedural changes
- Local court administrative orders (if county specified)

**Search strategy**: WebSearch for `site:courts.mi.gov SCAO [topic]` and `michigan SCAO form [topic]`

### 5. ICLE Publications & Practice Guides

Check for relevant sections in:
- Michigan Family Law Benchbook (ICLE)
- Handling Divorce Cases in Michigan (ICLE)
- Michigan Child Custody Benchbook (ICLE)
- LexisNexis Michigan Family Law Practice Guide

**Search strategy**: WebSearch for `ICLE michigan [topic] family law` and `michigan family law practice guide [topic]`

### 6. Professional Standards & Evaluation Tools

When psych issues are involved, also check:
- APA Guidelines for Child Custody Evaluations
- AFCC (Association of Family and Conciliation Courts) guidelines
- Michigan custody evaluator standards
- Specific psychological test standards (MMPI-2-RF, MCMI-IV, PAI admissibility)

## Audit Output Format

```
# SECONDARY SOURCE AUDIT: [Topic/Issue]

## Date of Audit: [date]

## Summary
[1-2 paragraph overview of what was found across all sources]

## Findings by Category

### MJI Benchbooks
- [Finding 1]
- [Finding 2]
- Status: [Found relevant material / Nothing directly on point / Partially relevant]

### FOCB Policy
- [Finding 1]
- Status: [Found / Not found / Partially relevant]

### MDHHS/CPS
- [Finding 1]
- Status: [Found / Not found / Partially relevant]

### SCAO Orders/Forms
- [Finding 1]
- Relevant Forms: [form numbers]
- Status: [Found / Not found]

### ICLE/Practice Guides
- [Finding 1]
- Status: [Found / Not found / Access limited]

### Professional Standards
- [Finding 1]
- Status: [Found / Not found]

## Cross-Category Themes
[Patterns or themes that emerge across multiple source categories]

## Gaps & Limitations
- [What couldn't be found]
- [Sources that may exist but couldn't be accessed]
- [Areas where the law/policy may be unsettled]

## Recommended Citations for Brief/Motion
[Priority-ordered list of the strongest secondary sources to cite]
```

## RULES
- Search EVERY category - do not skip even if early results seem sufficient
- Note when sources are behind paywalls (ICLE, LexisNexis) and provide enough identifying info for manual lookup
- Flag outdated material (pre-2023) explicitly
- Distinguish between binding authority and persuasive/informational sources
- Always note the URL or identifying information for retrieval
