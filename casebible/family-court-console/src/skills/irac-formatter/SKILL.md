---
name: fct-irac-formatter
description: "(family-court-toolkit) Enforces strict IRAC format for Michigan family law analysis. Use to structure any legal analysis output into proper Issue-Rule-Analysis-Conclusion format with required disclaimer and citations."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/irac-formatter` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# IRAC Output Formatter for Michigan Family Law

Every substantive legal analysis MUST be formatted using this template. No exceptions.

## Required Header (EVERY response)

```
---
**PROFESSIONAL RESEARCH USE ONLY.** Not legal advice. No attorney-client
relationship is formed. Unauthorized Practice of Law (UPL) is prohibited
under MRPC 1.6. Anonymize all PII; user assumes all risks.
---
```

## IRAC Structure

### I - ISSUE
- Restate the legal question clearly and specifically
- Include pseudonymized facts (Parent A, Parent B, Child)
- Frame in terms of the applicable MCL/MCR provision
- Example: "Whether Parent B's documented NPD traits and alcohol relapse constitute a change in circumstances under MCL 722.27(1)(c) sufficient to warrant custody modification, where Parent A has maintained treatment compliance for bipolar disorder."

### R - RULE
- **Primary authority first**: Verbatim MCL/MCR text
- **Case law**: Published MSC/MCOA opinions with:
  - Case name, docket number, date
  - Specific holding relevant to the issue
  - Parenthetical explanation
- **Secondary sources**: MJI benchbook sections, FOCB policy, MDHHS protocols
- Use superscript notation for source categories: ^1^ (benchbooks), ^4^ (MDHHS), ^5^ (practice guides)
- **Flag unverified citations**: Mark as [UNVERIFIED] if not independently confirmed

### A - ANALYSIS
Structure analysis in subsections:
1. **Legal Application**: Apply rule to facts
2. **Psychological Mapping**: Connect DSM-5 criteria to legal standards
3. **Vulnerability Matrix**:
   - Parent A strengths/weaknesses + defenses
   - Parent B strengths/weaknesses + attack vectors
4. **MCL 722.23 Factor Impact**: Which factors are affected and how
5. **Evidentiary Considerations**: What evidence supports/undermines the position
6. **Counterargument Anticipation**: What the other side will argue

### C - CONCLUSION
- **Priority-ranked tactical recommendations** (numbered)
- **Motion templates/outlines** where applicable
- **Risk assessment**: Low/Medium/High for each recommendation
- **Timeline**: Procedural deadlines and sequencing
- **Gaps**: Facts or research still needed (frame as questions)

## Citation Format

```
MCL 722.23(a) (love, affection, emotional ties)
MCR 3.210(A) (custody jurisdiction)
Vodvarka v Grasmeyer, 259 Mich App 499, 509; 675 NW2d 847 (2003)
MJI Family Division Benchbook, Ch. 5, Section 5.3^1^
```

## PII Rules
- Parent A = user/client perspective
- Parent B = opposing party
- Children = by age/gender only
- No real names, addresses, case numbers, SSNs, or DOBs in output
