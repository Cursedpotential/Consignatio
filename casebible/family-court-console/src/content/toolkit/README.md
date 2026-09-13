# Genesee Family Court Toolkit

Version 1.1.0 | Build date: 2026-08-09 | Expiry date: 2027-02-05

This is an installable Agent Skill package for **legal information** related to contested family-law procedure in the Genesee County, Michigan 7th Judicial Circuit Court, Family Division. Start at `SKILL.md`, then run `python scripts/traceability_check.py .`.

## Install/use
Keep the directory intact; the skill needs `references/`, templates, checks, decision trees, scripts, ledger, and tests. Python standard library scripts require no credentials. `pytest` runs the quality suite.

## Scope
The package covers pro se hearing preparation; Michigan motion/discovery practice; FOC/referee/de novo workflow; lawful digital-evidence gating; DV/coercive-control context; reactive behavior; substance and protected records; evidence foundations; chronologies; and exhibits. It does **not** provide advice, outcome predictions, legal representation, unauthorized evidence access, or a final deadline.

> This package is legal **information**, not legal advice. It was assembled by an AI system and may be incomplete, out of date, or wrong for your case. No attorney-client relationship is created. Court rules, local administrative orders, judge policies, forms, and deadlines change without notice — **verify everything with the Genesee County Circuit Court clerk, the Friend of the Court, the official sources cited, and, wherever possible, a licensed Michigan attorney before you file or say anything.** Missing a deadline or filing the wrong document can permanently harm your case and your relationship with your children. If you are in danger, call 911; for domestic-violence help call the Michigan statewide hotline or a local program.

See `LIMITATIONS.md`, `references/00-how-to-use-references.md`, `ledger.json`, and `CHANGELOG.md`.

## Deep-research audit integration — 2026-08-09
The package now includes a source-audit report at `references/audit/deep-research-source-audit-2026-08-09.md` and its imported 74-record audit ledger at `references/audit/deep-research-source-ledger-2026-08-09.json`. The package ledger preserves its resource records and adds the audit records with provenance and dependent-file links.

The audit distinguishes fetched source text from robots-blocked, client-error, interactive-only, and mirror-only access. A source identity, search snippet, or successful URL response does **not** establish current operative wording. Read `references/audit/audit-primary-text-access-limits.md` before using a rule subdivision, form revision, local deadline, or support table.

High-priority audit modules: `audit-mifile-nonlisting.md`, `audit-roster-conflicts.md`, `audit-form-and-supplement-drift.md`, and `audit-recording-doctrine.md`.
