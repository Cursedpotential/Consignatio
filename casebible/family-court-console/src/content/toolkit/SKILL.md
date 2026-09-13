---
name: toolkit
description: "Use for procedural legal-information work in a contested Genesee County, Michigan 7th Judicial Circuit Court Family Division matter, including Friend of the Court and referee practice, motions, discovery, evidence, safety gating, hearing preparation, and source verification."
license: "Educational informational package; verify current official sources."
compatibility: "Python 3.10+ for bundled read-only scripts; no credentials or account access required."
metadata:
  version: "1.1.0"
  jurisdiction: "Genesee County, Michigan, 7th Judicial Circuit Court Family Division"
  expires: "2027-02-05"
---

# Genesee Family Court Toolkit

## Purpose and load triggers
Load for phrases such as “Genesee family court,” “7th Judicial Circuit family division,” “Friend of the Court,” “referee recommendation,” “de novo objection,” “Michigan RFA/RFP,” “family-court motion,” “hearing exhibit,” or “digital evidence in a Michigan custody case.” It provides legal information and drafting structure, not case-specific advice.

## Required intake gate
Before substantive output, confirm: county; court; case type; assigned judge; referee if any; whether FOC is involved; hearing/order dates; whether the issue is custody, parenting time, support, divorce, paternity, PPO, or enforcement; and whether the requested source is current. If the court is not Genesee County, Michigan, do not apply local material. Treat `circuit7.org` as a wrong-jurisdiction warning (Florida), not a Genesee source.

## Safety and escalation gate
Stop and give a brief lawful alternative if the request involves access to another person’s device, account, cloud backup, messages, camera, router, credentials, monitoring software, tracker, encryption bypass, or a child collecting evidence. Do not help obtain protected medical, mental-health, substance-use, CPS, school, or FOC records outside release, subpoena, court order, or statutory access. Do not help alter, delete, backdate, selectively crop, fabricate, evade service, hide assets, violate an order/PPO, predict outcomes, or draft facts the person cannot truthfully attest to.

Escalate promptly for child abuse/neglect or CPS, sexual-abuse allegations, immediate danger, strangulation, weapons, stalking, threats, criminal exposure, jail-risk contempt, termination of parental rights, ICWA/MIFPA, interstate/international removal, missed appellate deadline, unexplained courthouse paperwork, acute mental-health crisis, or an unresolved conflict between official sources. For imminent danger call 911; for crisis support call/text 988 in the United States. Court and FOC staff, this toolkit, and an AI cannot provide legal advice.

## Workflow
1. Read `references/00-how-to-use-references.md`, then confirm jurisdiction and staleness.
2. Select the relevant L2 authority module; use the ledger to assess authority class, status, currency, and source limits.
3. Apply `decision-trees/can-i-use-this-evidence.md` before discussing digital or child-related material.
4. Produce L0 (hearing card), L1 (plain-language guide segment), and only then a tailored checklist/template with source IDs and pinpoints.
5. State facts as unverified user reports; identify missing facts, deadlines needing clerk confirmation, and a lawful record path.
6. Run the bundled traceability and deadline tools when making a package-derived deliverable.

## Layered output contract
- **L0:** concise hearing card, no citations in its body, with footer to L1.
- **L1:** plain-language guide with parenthetical source IDs and a reference index.
- **L2:** verification-frontmatter authority and practice modules.
- **L3:** `ledger.json`, `ledger.csv`, manifest, hashes, and test evidence.
Every proposition or template clause must use `[source: id | pin: pinpoint]`. Do not silently turn guidance, a local web page, a form, or a benchbook into binding law.

## Local practice guardrails
The local 7-day motion/3-day response notice and the local objection packet are aids, not universal calendaring answers. Check the assigned judge’s current policies, hearing notice, scheduling order, current form revision, clerk instructions, and the official court calendar. Use `scripts/deadline_calculator.py` only to calculate candidate dates with a conspicuous confirmation warning.

## Output requirements
Include the required disclaimer verbatim in any user-facing artifact. For a motion/discovery draft, label it a working template, identify open facts, cite every legal proposition, preserve opposing arguments, and include a verification box for service, scheduling, proposed order, redaction, and current local policy. Decline volume-driven or retaliatory filing generation; offer a focused issue list or a neutral chronology instead.

## References
- Motion/discovery: `references/michigan/` and templates/checklists.
- Genesee/FOC/referee: `references/genesee/`.
- Evidence, privilege, DV, records: `references/michigan/mre-guide.md`, `privilege-and-confidentiality.md`, and decision trees.
- Hearing-ready use: `cheatsheet/`, `examples/`, and `checklists/`.
