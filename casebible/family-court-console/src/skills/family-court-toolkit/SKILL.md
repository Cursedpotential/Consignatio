---
name: family-court-toolkit
description: "(family-court-toolkit) Entry point for the owner's Michigan (Genesee County) custody / parenting-time matter: safety and jurisdiction gate first, then routes to 35 on-demand members — intake, MCL 722.23 factors, evidence and MRE 901 authentication, documentation (FACT/BIFF), financial discovery, Michigan drafting, FOC/CPS/DV/court resources, source verification, decision-record and appeal prep — plus a bundled MCP console (27 tools: safety router, ledger-backed source audit, MCR-preset deadlines, case_facts, survival_guide, court_language_review, and a SurrealDB case store with search + graph, filed/draft-works docket, memos, evidence log, evals, and behavior-pattern reference data) and the official CourtListener MCP. Triggers: custody, parenting time, FOC, referee, objection, PPO, CPS, UCCJEA, hearing prep, exhibit, motion, Genesee, MCL 722, best interest factors, GAL, transcript, discovery, child support."
---

# family-court-toolkit — entry skill (progressive disclosure)

> _Byline: Claude Code · Fable 5.1 · 2026-09-07 · plugin 3.0.0. Owner rulings: one advertised skill per plugin; members load on demand;
> tools resolve state at run time; the plugin's GUARDRAILS (`content/custody-guide/GUARDRAILS.md`) outrank anything below._
> _Byline: Claude Code · Sonnet 5 · 2026-09-07 · plugin 3.1.0 — owner orders 13:09-13:16 add 7 case-store
> tools (20 → 27) and 8 tables/7 edges for filed/draft works, the court-vs-master timeline split, memos,
> reference data, an evidence log, evals, and case status. Design writeup:
> `docs/2026-09-07-case-store-registers.md`._

Legal information and drafting structure only — never legal advice, never "filing-ready". Publication of the guide itself remains
blocked pending attorney review (`RELEASE_STATUS` is returned by every console tool).

## 0 · Safety and jurisdiction gate — reasoning first, regex second

Before any substantive work, **extract these facts yourself from the user's words** (this step is what the August build's evals
proved; the regex router is only a backstop):

1. Where has the child lived for the last 6 months? Any state or country other than Michigan mentioned at all (place names count) → UCCJEA / interstate question: **stop** and route to `michigan-family-court-guide` + MC 416 affidavit guidance.
2. Any date within 21 days (hearing, response due, objection window, appeal window)? → treat as deadline-critical; compute with `calculate_planning_date` using a named `rule` preset and say it is PROVISIONAL.
3. Any immediate danger, DV, PPO, CPS, police, weapon, threat, or removal of the child without notice? → stop; safety resources (`dv-resources`, `cps-resources`) and 911 for immediate danger.
4. Any recording question (calls, the child, devices) → recording law is UNSETTLED in Michigan; never authorize; attorney question.
5. Any appeal, reconsideration, or final order → appeal-timing interaction with postjudgment motions (MCR 7.204); escalate.

Then call the console tool `route_issue` with the user's text. Treat `STOP_AND_VERIFY` and `UNCLASSIFIED_REVIEW_RECOMMENDED` as
"do not draft yet". Load the case state with `case_facts` (reads the private case file; see §3) so dates and orders come from the
record, not from memory.

## 1 · How to use the members

Match the task to one member row (or run `python "${CLAUDE_PLUGIN_ROOT}/skills/family-court-toolkit/scripts/route.py" "<need>"`),
then `Read` `${CLAUDE_PLUGIN_ROOT}/skills/<member>/SKILL.md` and follow it. Load a second member
only when the task genuinely spans two. The treatise drafts live at `content/custody-guide/draft/` (25 files, `INDEX.md`);
the 191-record source ledger at `content/toolkit/ledger.json`; templates at `content/toolkit/templates/`.

### Members by family (35)

| family | member | one line |
|---|---|---|
| intake | `michigan-family-court-guide` | route + explain Michigan procedure with verified/uncertain/next block |
| intake | `case-intake` | structured intake questionnaire before any factor analysis |
| intake | `custody-packet-gen1` | the August reasoning-driven packet gate (eval-proven); read for the fact-extraction discipline |
| intake | `toolkit-gen1` | the August toolkit router; maps content/toolkit assets |
| intake | `survival-guide` | prompt + template for ANY hearing or document type: call `survival_guide` (17 context packs: referee, de novo, motion, evidentiary, show-cause, PPO, FOC interview, GAL, evaluation, mediation; motion, response, objection, affidavit, proposed order, proof of service, ex parte) then write the guide from case_facts + the matching draft module; `--card` for the hearing-day card |
| intake | `case-store` | embedded SurrealDB case store (search + graph): `case_put`/`case_query`/`case_search`/`case_graph`/`case_factor_map`/`case_timeline`/`case_export`/`case_import`/`case_summary` + `case_status`/`case_docket`/`case_memo`/`case_evidence_log`/`case_eval`/`case_reference`/`case_source`; court-vs-master timeline lanes; two-clock discipline (occurred_at/known_at); child records are initials+age only, name never enters the store |
| drafting | `court-language` | your words → court-safe words: `court_language_review` flags mechanically (banned clinical labels, absolutes, mind-reading, child-as-witness STOP, recording admissions STOP, layperson legal conclusions, PII of minors) per doc type, then the model rewrites from the prompt + TEMPLATES.md + EXAMPLES.md and re-reviews until score ≥ 90 |
| factors | `best-interest-factors` | MCL 722.23 (a)–(l) worksheet + incident-to-factor mapping |
| factors | `mcl-factor-mapper` | per-factor template with evidence-strength ratings (use with the worksheet) |
| analysis | `behavioral-pattern-analyzer` | internal lens: manipulation/reactive-abuse pattern analysis → court-language gate |
| analysis | `manipulation-patterns` | internal reference: DARVO, coercive control, alienation dynamics → court-language gate |
| analysis | `custody-evaluation-summary` | memo from a custody evaluator's report |
| documentation | `documentation-methods` | FACT incident logs, BIFF replies, reframing emotions into court language |
| evidence | `mre-authentication` | MRE 901 authentication of texts, screenshots, devices |
| evidence | `evidence-templates` | intake, chain of custody, hash verification, exhibit prep templates |
| financial | `tax-return-summary` → `tax-return-analysis` | citation-backed extraction, then the litigation memo (run in that order) |
| financial | `track-deposits` | fund-flow tracing across bank records |
| financial | `child-support-worksheet` | MCSF 2025 worksheet (archived formula in content/custody-guide/sources/primary) |
| drafting | `custody-packet-builder` | organize the hearing/exhibit packet via console tools |
| drafting | `motion-for-temporary-relief` | interim orders (MCR 3.207) |
| drafting | `order-modification` | post-judgment change: proper cause / change of circumstances (Vodvarka) |
| drafting | `parenting-plan` | parenting-time plan incl. MCL 722.31 domicile rule |
| drafting | `dvro-petition` | PPO petition structure (MCL 600.2950; SCAO CC forms) |
| drafting | `irac-formatter` | the shared IRAC output contract + vulnerability matrix |
| resources | `court-resources` | courts.michigan.gov, SCAO forms, MCR/MCL tables, Genesee contacts (PROVISIONAL until confirmed) |
| resources | `foc-resources` | Friend of the Court process, support, parenting time, Genesee FOC |
| resources | `cps-resources` | MDHHS/CPS process, Central Registry, CPS–custody intersection |
| resources | `dv-resources` | DV statutes, PPO procedure, coercive-control framing, Genesee DV resources |
| verification | `verify-michigan-legal-sources` | per-claim audit against primary sources with normalized statuses |
| verification | `case-research` | Michigan-only case-law research protocol (anti-fabrication rules) |
| verification | `secondary-source-auditor` | MJI / FOCB / MDHHS / SCAO / ICLE audit with search strings |
| verification | `trusted-sources` | acquire official texts into the case folder with provenance |
| verification | `decision-record-verification` | judge's findings vs transcripts, dual citations (objection / appeal prep) |

Agents (`agents/`): `custody-support` (trauma-informed, non-legal), `michigan-law` (attorney persona, IRAC, Michigan-only),
`litigation` (discovery drafting, cross-exam), `evidence-tech` (intake/hash/exhibits), `forensic` (forensics + research),
plus the August four: `case-law-researcher`, `evidence-organizer`, `family-court-document-drafter`, `michigan-source-verifier`.
Slash commands kept advertised (7): `/family-court-toolkit:` `family-court`, `packet`, `motion`, `hearing`, `evidence`, `discovery`,
`verify-sources`. **Procedures on demand** (`../_commands/*.md`, run when the user asks for them by name, no slash needed):
`factor-analysis`, `gal-prep`, `motion-strategy`, `research-issue`, `source-audit`, `vulnerability-check`, `verify`, `custody-intake`,
`analyze-behavior`, `case-law`, `case-lookup`. Extra member outside the families above: `referee-hearing-survival` (in-the-room
referee-hearing guide; answer patterns, trap questions, do-not list).

## 2 · Console tools (MCP `family-court-console`, exposed as `mcp__plugin_family-court-toolkit_family-court-console__<tool>`)

`open_dashboard` · `route_issue` (gazetteer + deadline-proximity aware; returns matched phrases) · `calculate_planning_date`
(`rule` presets: referee_objection, appeal_of_right, motion_response, mail_service_addon — all PROVISIONAL_VERIFY, MCR 1.108 counting) ·
`get_packet_plan` · `get_checklist` · `audit_sources` (7 curated + 191 ledger records + 213-URL directory; `source_stats`) ·
`search_guide` · `build_chronology` · `case_facts` (§3) · `survival_guide` {event, format: full|card|json, include_case_facts} → template + context pack the model writes from · `court_language_review` {text, doc_type, mode: review|rewrite_plan} → deterministic flags, score, rewrite plan, phrasebank. **Case store (embedded SurrealDB on RocksDB, file at `CUSTODY_CASE_DB` or `~/.config/family-court-toolkit/case.db`; member `case-store`):** `case_put` · `case_query` (SurrealQL, read-only unless write:true) · `case_search` (text | vector | hybrid, over 10 tables incl. memo/filing/draft/court_event/reference/eval) · `case_graph` · `case_factor_map` (12 MCL 722.23 letters ↔ evidence) · `case_timeline` (`mode: court|master|merged` — the real court-event timeline vs the corpus-extracted master timeline, tagged `lane`; `known_by`/`upcoming` filters) · `case_export` (`format: snapshot|platform`) / `case_import` (auto-detects snapshot, Vincent-schema, or case-extract/v1) · `case_summary` (now with per-table `counts`) · `case_status` (get|set the case-status singleton) · `case_docket` (filings+drafts+orders+upcoming court_events) · `case_memo` (put|list|latest — analysis/strategy/weakness/direction/finding/risk/goal/issue/advice) · `case_evidence_log` (append|list) · `case_eval` (put|list — evals/reports) · `case_reference` (load|list|match — behavior-pattern/ontology/lexicon reference data) · `case_source` (a record's original-source provenance). 27 console tools in total (owner orders 2026-09-07 13:09-13:16 added 7). CourtListener MCP (`courtlistener`, official, credential-free; first call
opens browser OAuth) is **discovery only, never a citator** — hooks remind on every case-law prompt and tool call.

## 3 · Case state — dynamic, never hardcoded

The private case file lives OUTSIDE the plugin: `CUSTODY_CASE_FILE` env var, else `~/.config/family-court-toolkit/case.json`
(template: `mcp-app/case.example.json`). `case_facts` returns county, court, judge, referee, controlling orders with entry/service
dates, next hearing, deadlines, parties as initials, children as count + ages only. Never write child names into any output.

`case_status` (the case-store singleton `case_status:current`) is a SEPARATE, complementary state surface — phase, posture,
`next_court_event` ref, `open_deadlines[]`, notes — kept in the embedded SurrealDB store, not the `case.json` file. Set it with
`case_status({action:"set", data:{...}})` whenever the case's phase or posture changes; read it with `case_status({action:"get"})`.
It does not replace `case_facts`/`case.json`.

## 4 · Rules that override members

- **Court-language gate:** analysis members (`behavioral-pattern-analyzer`, `manipulation-patterns`, the `michigan-law` persona's
  profiling) are internal lenses; pleadings and messages describe observable behavior, dates and effect on the child — no clinical
  labels as findings (GUARDRAILS "never a diagnosis").
- **Child-protection absolute:** never ask a child to gather evidence, record, or carry a device; not a balancing test.
- **UNVERIFIED never ships:** every load-bearing proposition cites an archived primary source or is flagged; Genesee local facts are
  PROVISIONAL until confirmed with the office on a stated date (MiFILE: owner-confirmed 2026-09-07 that Genesee is not a MiFILE court).
- **End every substantive answer** with **What is verified / What is uncertain / What to do next**.
- **Maintenance:** `content/custody-guide/UPDATE_POLICY.md` — bump the version, refresh the ledger, keep unresolved flags, run
  `mcp-app` tests (`npm test`) including `router_evals` before any release.
