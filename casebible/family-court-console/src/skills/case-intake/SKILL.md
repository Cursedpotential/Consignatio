---
name: fct-case-intake
description: "(family-court-toolkit) Structured case intake questionnaire for Michigan family law custody disputes. Use at the start of any new case analysis to systematically gather facts before performing IRAC analysis. Ensures no critical factors are missed."
disable-model-invocation: true
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/case-intake` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Case Intake Questionnaire - Michigan Custody Dispute

Walk through this intake systematically. Ask questions in sections. Do NOT proceed to IRAC analysis until sufficient facts are gathered.

**Remind the user**: Use pseudonyms. We'll refer to you as Parent A and the other party as Parent B.

## Section 1: Procedural Status

Ask about:
- [ ] Current custody arrangement (legal and physical)
- [ ] Existing court orders (temporary, final, modifications)
- [ ] Pending motions or hearings (dates?)
- [ ] Which court/county
- [ ] FOC involvement (referee, mediator, investigator?)
- [ ] GAL appointed? If so, status of GAL report
- [ ] Any PPOs (active or past)?
- [ ] Pro se or represented? Opposing party represented?

## Section 2: Parent A Profile (User)

Ask about:
- [ ] Mental health diagnoses (bipolar, depression, anxiety, PTSD, etc.)
- [ ] Current treatment status (therapy, medication, compliance)
- [ ] Substance use history (past and current; sobriety duration)
- [ ] Employment/income stability
- [ ] Housing stability
- [ ] Criminal history (if any)
- [ ] Prior CPS involvement (if any)
- [ ] Parenting strengths (daily routine, school involvement, medical care)
- [ ] Known vulnerabilities the other side will raise

## Section 3: Parent B Profile (Opposing Party)

Ask about:
- [ ] Suspected/diagnosed mental health conditions (NPD, BPD, psychopathy indicators)
- [ ] Observable behavioral patterns (manipulation, control, DARVO, gaslighting)
- [ ] Substance use (current? relapses? documented?)
- [ ] Employment/income
- [ ] Housing situation
- [ ] Criminal history
- [ ] CPS involvement
- [ ] Parenting concerns (neglect, alienation, abuse, instability)
- [ ] Documentation available (texts, emails, recordings, witnesses)

## Section 4: The Children

For each child, ask:
- [ ] Age and gender
- [ ] Current school/grade performance
- [ ] Special needs (medical, educational, behavioral)
- [ ] Expressed preferences (if age-appropriate)
- [ ] Current living arrangement
- [ ] Relationship quality with each parent
- [ ] Observed impact of conflict on the child

## Section 5: High-Conflict Dynamics

Ask about:
- [ ] History of domestic violence (physical, emotional, financial, coercive control)
- [ ] Alienation behaviors (by either parent)
- [ ] False allegations (by either side - be neutral)
- [ ] Communication patterns between parents (hostile? no contact? parallel parenting?)
- [ ] Third-party involvement (new partners, grandparents, etc.)
- [ ] Police reports, incident documentation
- [ ] Pattern of litigation/court filings

## Section 6: Specific Legal Question

Ask:
- [ ] What is the PRIMARY issue you need help with right now?
- [ ] What outcome are you seeking?
- [ ] What is the most urgent deadline?
- [ ] What has already been tried?

## After Intake

Summarize the facts using Parent A/Parent B/Child conventions, then:
1. Identify the top 3 legal issues
2. Flag gaps in information that need to be filled
3. Recommend which analysis to perform first
4. Proceed to IRAC analysis using `${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/references/mcl-factor-mapper/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/references/irac-formatter/SKILL.md`

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — rewrote the mcl-factor-mapper/irac-formatter cross-reference above to the member `${CLAUDE_PLUGIN_ROOT}` path form (1 replacement). No other sibling-skill cross-reference (old `mi-`-prefixed names or `custody-intake`) was found in this file._
