---
name: fct-mcl-factor-mapper
description: "(family-court-toolkit) Maps case facts to all 12 MCL 722.23 best interest factors with evidence strength ratings. Use when analyzing custody disputes, preparing for hearings, or building factor-by-factor arguments."
allowed-tools: Read, WebSearch, WebFetch
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/mcl-factor-mapper` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# MCL 722.23 Best Interest Factor Mapper

When invoked, systematically map the provided case facts to ALL 12 best interest factors. Never skip a factor - if facts are insufficient, flag it as a gap.

## The 12 Factors (MCL 722.23)

For each factor, provide:
1. **Factor text** (verbatim from statute)
2. **Parent A evidence** (strengths + weaknesses)
3. **Parent B evidence** (strengths + weaknesses)
4. **Rating**: Strong A | Lean A | Neutral | Lean B | Strong B | Insufficient Facts
5. **Key case law** supporting the analysis
6. **Strategic note** on how to strengthen or defend

### Factor Template

```
## Factor (a): Love, Affection, Emotional Ties
**Statute**: "The love, affection, and other emotional ties existing between the parties involved and the child."

**Parent A**:
- Strengths: [evidence]
- Weaknesses: [evidence]
- Defense for weaknesses: [strategy]

**Parent B**:
- Strengths: [evidence]
- Weaknesses: [evidence]
- Attack vectors: [strategy]

**Rating**: [rating]
**Key Authority**: [case cite]
**Strategic Note**: [recommendation]
```

### All 12 Factors to Map:
(a) Love, affection, emotional ties
(b) Capacity to give love, affection, guidance, continuation of education/religion
(c) Capacity to provide food, clothing, medical care, material needs
(d) Length of time in stable, satisfactory environment; desirability of maintaining continuity
(e) Permanence as a family unit of existing or proposed custodial home
(f) Moral fitness of the parties
(g) Mental and physical health of the parties
(h) Home, school, and community record of the child
(i) Reasonable preference of the child (if old enough)
(j) Willingness and ability to facilitate a close and continuing parent-child relationship with the other parent (except DV)
(k) Domestic violence regardless of directed at child
(l) Any other factor considered by the court to be relevant

## After Mapping

Provide a **Summary Matrix** showing all 12 factors at a glance, then identify:
- **Strongest factors** for Parent A (top 3)
- **Most vulnerable factors** for Parent A (top 3)
- **Factors needing more evidence**
- **Recommended motion strategy** based on factor balance
