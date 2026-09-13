# Pro Se Custody Guide — Genesee County, Michigan

A self-help treatise on custody, parenting time, and child support for a self-represented
parent in the 7th Judicial Circuit Court, Family Division (Genesee County, Michigan).

**Status: verification pass 1 complete; treatise not yet drafted.**

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — corrected stale `toolkit-package/`, "194-file built plugin," and `html-app/` references below; see the corrected paragraph and this file's `## Corrected paths — 2026-09-07` section._

~~The repo now holds **two generations** of this project:~~

- **`/` (root)** — the *treatise* project: plan, research, drafting specification, council reviews.
- ~~**`toolkit-package/`** — a later, more advanced generation: a master prompt, a 74-source verified ledger and audit, four council reviews, a **built Claude Code plugin** (194 files, v1.1.1, with a credential-free CourtListener MCP integration), the toolkit source (54 files), and `html-app/` — a built browser app for the toolkit.~~ **Corrected 2026-09-07:** `toolkit-package/` no longer exists as a path in this plugin. Its content lives at `content/toolkit/` (the toolkit source — see `content/toolkit/manifest.json`). The CourtListener MCP integration is registered again in **this plugin's own root `.mcp.json`** (restored 2026-09-07 from the August build) as the `courtlistener` server, alongside the plugin's own `family-court-console` MCP server (`mcp-app/dist/server.js`) — it is not a separate "194-file built plugin." The `html-app/` browser app referenced in the original text was **never found on disk during the 2026-09-07 restoration; its status is unknown** — treat it as not present until located or rebuilt.
- **`GUARDRAILS.md`** — project governance: what this may and may not become, who decides what, the four evidence dispositions, the publication gate, and the maintenance clocks.
- **`critical_review_outline_v2.md`** — adversarial review of the v2 drafting spec itself.
- **`verification_ledger.md`** — results of the August 9, 2026 verification pass against primary sources.
- **`research_interference_coercive_control.md`** — research addendum mapping interference / coercive control / weaponized process onto recognized Michigan statutory hooks.
- **`LEGAL-RESEARCH-INTEGRATIONS.md`, `MICOURT-CASE-SEARCH-INTEGRATION.md`, `UPDATE_POLICY.md`, `MANIFEST-SCHEMA-NOTES.md`** — restored 2026-09-07; now at `content/custody-guide/` alongside this README (previously described, if at all, as living under the now-nonexistent `toolkit-package/`).

## Files

| File | What it is |
|---|---|
| `custody_guide_plan.md` | Project plan — purpose, audience, scope, pedagogy, disclaimer plan, style guide |
| `custody_guide_research.md` | Research compendium — statutes, case law, court rules, Genesee local practice, SCAO forms |
| `custody_guide_outline_v2.md` | **The drafting specification.** Part 0 governing spec + front matter + 29 modules + 15 appendices |
| `master_source_directory.md` | 213 unique source URLs across 14 categories, extracted Aug 9 2026 |
| `council/model-council-claude_opus_5_0.md` | Council review — evidentiary/procedural-mechanics angle |
| `council/model-council-gpt_5_6_sol.md` | Council review — systems/pathway angle |
| `council/model-council-gemini_3_1_pro.md` | Council review — topical-completeness angle |
| `council/model-council-synthesis.md` | Merged verdict and rebuild recommendation |

Filenames match the cross-references used inside the documents themselves
(`custody_guide_plan.md`, `custody_guide_research.md`, `model-council-*.md`), so internal
references resolve.

## Draft modules (`draft/`)

**25 draft files exist** under `draft/`, not the 7 or so implied by earlier prose in this README
(corrected 2026-09-07, restoration): FM-0 (1 file) + FM-1-6 front matter, 15 numbered modules, and
2 appendices (18 files together — see the caveat below on the exact count) + 6 Packet-1 (`P1-*`)
documents. See `draft/INDEX.md` for the full file-by-file list with title and purpose.

> _Amended: Claude Code · Fable 5.1 · 2026-09-07 — corrected: the count named in this section's
> original instruction ("19 modules/appendices + FM-0 + 6 Packet-1 docs" = 26) does not match the
> actual 25 files on disk (18 modules/appendices + FM-0 + 6 Packet-1 docs = 25, verified by
> `ls content/custody-guide/draft/ | wc -l`). The 25 total and the 18-modules/appendices figure are
> the verified numbers; treat the "19" figure as a superseded miscount, not a second real file._

None of the 25 are reviewed by an attorney or filing-ready. **Module 3 (UCCJEA), Module 17
(DV/CPS/PPO safety), and Module 28 (appeals) remain STILL UNDRAFTED** — see `draft/INDEX.md`.

## How this got here

1. Plan and research compendium drafted.
2. A v1 outline was drafted (not in this package — superseded).
3. Three models reviewed v1 independently. All three concluded v1 was **not safe to hand to a
   drafting model**: it taught strategy before proof, mirrored an attorney CLE's lesson
   numbering instead of the litigant's decision sequence, and omitted evidence/admissibility,
   subpoena practice, parenting-time enforcement, change of domicile, emergency ex parte
   practice, and appellate triage.
4. `custody_guide_outline_v2.md` is the rebuild: Sol's pathway spine, Opus's content map,
   Gemini's additions, with a 12-point drafting contract and 12 acceptance tests as the gate
   every module must pass. Nothing from any council report was dropped; conflicts are preserved
   side by side under `⊗ COUNCIL CONFLICT` notes.

## What v2 already contains

- **Part 0** — drafting contract, acceptance tests, two-tier flag system plus three hard labels,
  stop-and-seek-counsel gates, banned vocabulary, conflict-of-authority protocol.
- **Front matter** — the 48-hour triage router ("what happened today?" → module + clock + flag),
  safety override, pre-filing safety planning, Genesee quick-reference card.
- **Modules 1–29** across five parts: Choose the Path → Build Proof → Ask/Respond/Resolve →
  Try the Case → Orders/Enforce/Change/Review.
- **Appendices A–O.** Appendix N (Master Glossary) is **already fully drafted** — 231 terms,
  each with plain meaning, precise legal meaning, controlling source + URL, "do not confuse
  with," and owning module.

## Gates before drafting

Carried forward from outline §0.8:

- **Unverified ledger.** Exact *Vodvarka* / *Shade* citations and holdings; MCSF Parental Time
  Offset brackets (§3.03); MCR 2.300-series discovery limits; MCR 3.219; current text of
  MCR 3.207 and 3.210 post-ADM File 2021-27; MRE restyling effective date; full text of
  MCL 722.26a, 552.505a, 552.605b–c; holdings of *Shade*, *Berger*, *Dailey*; *Grew v Knox*
  (unpublished — persuasive only, MCR 7.215(C)(1)); whether any published Michigan opinion
  recognizes parental alienation as a freestanding doctrine (current research: none);
  FOC 89 / FOC 57 titles; **and every Genesee County local fact** (fees, judicial and referee
  rosters, FOC procedures, CDRP, MiFILE status, local administrative orders, form revision dates).
- **Verified in the v2 pass:** the 18 deviation factors in §1.04(E) of the 2025 MCSF Manual,
  fetched from the primary PDF (confirms the reduction from 20; resolves research §12 item 5).
- **Three items no model may settle — a Michigan family-law attorney must clear them before
  publication:** (1) the vicarious-consent recording question; (2) every Genesee County local
  fact; (3) any template a reader might mistake for filing-ready.

## Constraints that bind any drafting pass

- No template may be labeled "filing-ready." Every sample states the procedural posture and
  facts it assumes, plus a "do not use if" list.
- Never publish a competing unofficial version of an official SCAO or Genesee form — link the
  official form and supply drafting aids for the narrative attachments it does not generate.
- Clinical vocabulary ("narcissist," "alienator," "PAS") is banned from reader-facing templates.
  Conduct is pleaded under MCL 722.23(j) and MCL 722.27a(7), not as a syndrome.
- No exercise may ask the reader to interview, recruit, coach, diagnose, or emotionally rely on
  the child (acceptance test 8).
- Legal information, not legal advice — informational framing throughout, never imperative.
