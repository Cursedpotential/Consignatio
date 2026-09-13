# Acquisition Ledger — 2026-09-07

> _Byline: Claude Code · Fable 5.1 · 2026-09-07_

Official primary-source acquisition pass for the Michigan custody-guide plugin, run against
the gaps `sources/README.md` documented (`mcl/` was empty; no SCAO forms, FOC/FOCB, MDHHS, or
Genesee-specific documents were archived). Every fetch below used a browser User-Agent per the
README's documented `courts.michigan.gov` UA-block workaround, and `curl --tlsv1.2` for
`legislature.mi.gov` per its documented TLS-chain issue. Both worked cleanly for every target —
**no WebFetch fallback was needed this pass**, and the `legislature.mi.gov` TLS failure recorded
in the README (dated pre-2026-09) did not reproduce from this machine.

Only new files under `primary/` (this pass's subfolders) and this ledger were written.
`primary/SHA256SUMS` was appended to, never rewritten.

## Summary

| Folder | Acquired | Not acquired | Bytes acquired |
|---|---:|---:|---:|
| `mcl/` | 39 | 0 | 954.5 KB |
| `scao-forms/` | 16 | 0 | 3.53 MB |
| `foc/` | 3 | 0 | 2.38 MB |
| `mdhhs/` | 3 | 0 | 674.6 KB |
| `genesee/` | 5 | 0 | 1014.9 KB |
| **Total** | **66** | **0** | **8.49 MB** |

Total download: **8.49 MB**, well under the 150 MB cap. Every target attempted
this pass was acquired — the NOT_ACQUIRED section below is empty because nothing failed, not
because anything was skipped.

## Retrieval method (what actually worked, 2026-09-07)

| Host | Strategy that worked | Notes |
|---|---|---|
| `courts.michigan.gov` | `curl -sS -L -A "<browser UA>"` | HTTP 200 on first try for every PDF target. The SPA-rendered form/rules **index** pages (`/SCAO-forms/circuit-court-forms/`, the old `/Administration/SCAO/Forms/Pages/Friend-of-the-Court-Index.aspx`) return client-side-only shells or 404 under curl — direct PDF/asset URLs (found via WebSearch, since the on-page JS index can't be scraped statically) worked fine. |
| `legislature.mi.gov` | `curl -sS -L -A "<browser UA>" --tlsv1.2` | HTTP 200 for all 39 MCL sections. The README's `CERTIFICATE_VERIFY_FAILED` note did not reproduce from this desktop — `--tlsv1.2` was sufficient, no Exa/WebFetch detour needed. |
| `dhhs.michigan.gov/OLMWEB` | `curl -sS -L -A "<browser UA>"` | Original host named in the task instructions worked directly (HTTP 200, valid `%PDF` magic bytes) — no fallback to the `mdhhs-pres-prod.michigan.gov` mirror surfaced by search was needed. |
| `7thcircuitcourt.com` | `curl -sS -L -A "<browser UA>"` | Server-rendered HTML (not a JS shell) — full local-administrative-order listing and Family Division page text came through directly. |
| `cms2.revize.com/.../geneseecountyjudicialcourt/...` | `curl -sS -L -A "<browser UA>"` | This is the Genesee court's own document CMS host (revize.com is a municipal-CMS platform; the URL was linked directly from `7thcircuitcourt.com`'s own local-administrative-orders page), not a third-party mirror. |
| `geneseecountymi.gov` | `curl -sS -L -A "<browser UA>"` | Server-rendered HTML, worked directly. |

Text extraction: `pdftotext -layout` (poppler, confirmed working — `pdftotext version 4.00`) for
every PDF; a plain tag-strip to text for the handful of server-rendered HTML pages (MCL sections,
the two `7thcircuitcourt.com` pages, the Genesee FOC page). No pypdf fallback was needed.

## Currency caveats

- Every `legislature.mi.gov` MCL page fetched this pass displays the banner **"Michigan Compiled
  Laws Complete Through PA 91 of 2026."** All 39 MCL sections below are verified only to that
  compilation point. Confirm no later public act has amended a section before relying on it in a
  filing.
- SCAO form revision dates are read off each form's own footer stamp (`Form FOC nn, Rev. m/yy`),
  not assumed from the search snippet — see the per-form table below.
- The FOCB Model Handbook's title page carries only the bare year **"2024"** (no month); the
  Michigan Parenting Time Guideline states **"Published: February 2021 / Last updated: March
  2022"** on its own face.
- MDHHS PSM sections carry a bulletin/effective-date stamp in their header row — recorded per
  document below (`PSM 711-4` and `PSM 713-01` both show **4-1-2024**; the current `PSM 000` table
  of contents shows **PSB 2026-002, 4-1-2026**).

## Notable findings

- **Genesee/7th Circuit is NOT a MiFILE court.** The acquired statewide e-filing court list
  (`genesee/mifile-court-list_efiling-status.pdf`, "Updated: 03/17/26") lists Genesee in neither
  Chart 1A (statewide MiFILE circuit courts) nor Chart 2 (non-statewide pilot courts) — this is
  the official page confirming the owner's statement, not an absence of evidence.
- **MCL 750.350a (parental kidnapping) was previously unverified.** `sources/README.md` records
  two prior Exa-fetch failures (`CRAWL_NETWORK_ERROR`) for this section. It fetched cleanly this
  pass via `curl --tlsv1.2` — full text is now archived at `mcl/mcl-750-350a.md`.
- **PSM section content differs slightly from the task's parenthetical labels.** `PSM 711-4`'s
  own header reads "CPS LEGAL REQUIREMENTS AND DEFINITIONS" (not "investigation"), and
  `PSM 713-01` reads "CPS INVESTIGATION - GENERAL INSTRUCTIONS" (not "disposition" — the
  disposition-titled section is actually `PSM 711-3`, per the acquired `PSM 000` table of
  contents). Both exact PSM numbers requested were fetched as specified; the mismatch is flagged
  here rather than silently substituted.
- **FOC 94 and FOC 106 are not motion/response forms.** FOC 94 is "Order Correcting Omission in
  Order" (a clerical-correction order) and FOC 106 is "Notice of Redirection or Abatement of
  Child Support" (an FOC-issued notice, not a party motion). Both were named as candidates in the
  task and are archived under `scao-forms/` for completeness, but neither meets the "motion/
  response" criterion in the strict sense — noted rather than silently dropped or silently
  counted as a match.
- **`sources/primary/SHA256SUMS` changed on disk mid-session**, apparently from a concurrent
  session (this repo is documented as shared across chats — see `AGENT_MEMORY.md`'s multi-chat
  git-discipline note). Not this task's doing. This pass only **appended** new lines at the
  bottom of whatever the file's live content was at append time — nothing above the append point
  was touched or reordered.

## `mcl/` — 39 of 39 acquired (was empty; now the highest-priority gap is closed)

All sections fetched from `legislature.mi.gov` via `curl --tlsv1.2 -A "<browser UA>"`, HTTP 200.
Each section is saved as both the raw HTML (`.html`) and a stripped-text `.md` extraction.
Fetch timestamp for the whole batch: see `results.jsonl`-derived timestamps below (all within
the same short window, 2026-09-07).

| Section | Subject | Last amendment (History line) | sha256 (html) | Size |
|---|---|---|---|---|
| MCL 722.21 | Child custody act; short title. | 1970, Act 91, Eff. Apr. 1, 1971 | `780be10c9352` | 18.7 KB |
| MCL 722.22 | Definitions. | ...t 327 , Imd. Eff. Dec. 28, 2005; Am. 2015, Act 51 , Eff. Sept. 7, 2015 | `b640e7ab2ca4` | 22.9 KB |
| MCL 722.23 | "Best interests of the child" defined. | ...Act 259, Imd. Eff. Nov. 29, 1993; Am. 2016, Act 95 , Eff. Aug. 1, 2016 | `c0719658e2ca` | 21.6 KB |
| MCL 722.24 | Child custody disputes; powers of court; appointment of lawyer-guardian ad litem. | ...996, Act 19 , Eff. June 1, 1996; Am. 1998, Act 482 , Eff. Mar. 1, 1999 | `0624e55dc3bb` | 20.6 KB |
| MCL 722.25 | Child custody dispute; controlling interests, presumption; award of custody to parent c... | ...Act 259, Imd. Eff. Nov. 29, 1993; Am. 2016, Act 96 , Eff. Aug. 1, 2016 | `145c577fd0f9` | 22.3 KB |
| MCL 722.26 | Liberal construction and application of act; purpose; provisions applicable to child cu... | ...5, Imd. Eff. Dec. 20, 1990; Am. 1993, Act 259, Imd. Eff. Nov. 29, 1993 | `1577b5182e3c` | 19.9 KB |
| MCL 722.26a | Joint custody. | Add. 1980, Act 434, Imd. Eff. Jan. 14, 1981 | `9fbc5d64f4be` | 21.2 KB |
| MCL 722.26b | Standing of guardian or limited guardian of child to bring action for custody of child;... | ...Act 259, Imd. Eff. Nov. 29, 1993; Am. 2000, Act 60 , Eff. Apr. 1, 2000 | `99633586209e` | 20.9 KB |
| MCL 722.26c | Custody action by third person; conditions. | Add. 1993, Act 259, Imd. Eff. Nov. 29, 1993 | `d2bf643237fd` | 20.4 KB |
| MCL 722.27 | Child custody disputes; powers of court; support order; enforcement of judgment or orde... | ...t 328 , Imd. Eff. Dec. 28, 2005; Am. 2015, Act 52 , Eff. Sept. 7, 2015 | `4403145e195b` | 26.0 KB |
| MCL 722.27a | Parenting time. | ...015, Act 50 , Eff. Sept. 7, 2015; Am. 2016, Act 96 , Eff. Aug. 1, 2016 | `9bea2d4f5826` | 32.5 KB |
| MCL 722.27b | Order for grandparenting time; circumstances; acknowledgment of parentage; commencement... | ..., Imd. Eff. Sept. 18, 2006; Am. 2009, Act 237 , Imd. Eff. Jan. 8, 2010 | `a7f4a67d14db` | 32.9 KB |
| MCL 722.28 | Child custody disputes; appeal, grounds. | 1970, Act 91, Eff. Apr. 1, 1971 | `bc864c13ad52` | 19.0 KB |
| MCL 722.29 | Transition to centralized receipt and disbursement of support and fees. | ... Act 91, Eff. Apr. 1, 1971; Am. 1999, Act 156 , Imd. Eff. Nov. 3, 1999 | `f47f5db8125a` | 19.3 KB |
| MCL 722.30 | Access to records or information by noncustodial parent. | Add. 1996, Act 304 , Eff. Jan. 1, 1997 | `03c000161aab` | 19.2 KB |
| MCL 722.31 | Legal residence change of child whose parental custody governed by court order. | Add. 2000, Act 422 , Imd. Eff. Jan. 9, 2001 | `df4d97bbe6e7` | 22.5 KB |
| MCL 722.1201 | Initial child-custody determination; jurisdiction. | 2001, Act 195 , Eff. Apr. 1, 2002 | `1e830fa24b4c` | 20.8 KB |
| MCL 722.1202 | Exclusive, continuing jurisdiction; condition; determination to decline jurisdiction; m... | 2001, Act 195 , Eff. Apr. 1, 2002 | `59459a74e5ae` | 20.3 KB |
| MCL 722.1203 | Modification of out-of-state child-custody determination; requirements. | 2001, Act 195 , Eff. Apr. 1, 2002 | `58586628e8fa` | 19.6 KB |
| MCL 722.1204 | Temporary emergency jurisdiction; communication with out-of-state court; duration of or... | 2001, Act 195 , Eff. Apr. 1, 2002 | `4f56ebc620ad` | 21.5 KB |
| MCL 722.1205 | Notice and hearing. | 2001, Act 195 , Eff. Apr. 1, 2002 | `dfdcf4214f21` | 19.7 KB |
| MCL 722.1206 | Commencement of out-of-state proceeding; jurisdiction; communication; dismissal of proc... | 2001, Act 195 , Eff. Apr. 1, 2002 | `2ce7af034bd0` | 21.0 KB |
| MCL 722.1207 | Determination of inconvenient forum. | 2001, Act 195 , Eff. Apr. 1, 2002 | `43a8fa09c184` | 21.3 KB |
| MCL 722.1208 | Unjustifiable conduct of parties; decision to decline exercise of jurisdiction; dismiss... | 2001, Act 195 , Eff. Apr. 1, 2002 | `15ceb910d040` | 20.7 KB |
| MCL 722.1209 | Pleading or sworn statement; information. | 2001, Act 195 , Eff. Apr. 1, 2002 | `f3131639e1d8` | 21.6 KB |
| MCL 722.1210 | Order to appear with or without child. | 2001, Act 195 , Eff. Apr. 1, 2002 | `517a2182f074` | 20.1 KB |
| MCL 600.2950 | Personal protection order; restraining or enjoining spouse, former spouse, individual w... | ...16, Act 296 , Eff. Jan. 2, 2017; Am. 2018, Act 146 , Eff. Aug. 8, 2018 | `996967273af6` | 45.6 KB |
| MCL 600.2950a | Personal protection order restraining or enjoining individual from engaging in conduct ... | ...16, Act 296 , Eff. Jan. 2, 2017; Am. 2018, Act 146 , Eff. Aug. 8, 2018 | `4bb7c9c4482e` | 47.7 KB |
| MCL 552.505 | Duties of friend of the court; failure of party to attend scheduled meeting; charging p... | ...ct 571 , Eff. June 1, 2003; Am. 2009, Act 233 , Imd. Eff. Jan. 8, 2010 | `db262bcbe27f` | 26.4 KB |
| MCL 552.511 | Initiating enforcement of support order and custody or parenting time order; procedure;... | ...02, Act 571 , Eff. June 1, 2003; Am. 2004, Act 567 , Eff. June 1, 2005 | `c2c53992b89d` | 23.4 KB |
| MCL 552.517 | Review of child support order after final judgment; modification order; calculations; p... | ...t 27 , Imd. Eff. June 20, 2019; Am. 2020, Act 349 , Eff. Dec. 30, 2021 | `842a049a68be` | 26.7 KB |
| MCL 552.519 | State friend of the court bureau; creation; supervision and direction; main office; dut... | ...3 , Imd. Eff. Jan. 8, 2010; Am. 2019, Act 27 , Imd. Eff. June 20, 2019 | `0b1a53f9f6a0` | 30.2 KB |
| MCL 552.605 | Child support order; deviation from formula; agreement. | Add. 2001, Act 106 , Eff. Sept. 30, 2001 | `8d8a99698d42` | 20.4 KB |
| MCL 750.539c | Eavesdropping upon private conversation. | Add. 1966, Act 319, Eff. Mar. 10, 1967 | `758b96de5aef` | 19.2 KB |
| MCL 750.539d | Installation, placement, or use of device for observing, recording, transmitting, photo... | ...6, Act 319, Eff. Mar. 10, 1967; Am. 2004, Act 156 , Eff. Sept. 1, 2004 | `e9813d2c9e55` | 21.0 KB |
| MCL 750.350a | Taking or retaining child by adoptive or natural parent; intent; violation as felony; p... | ...12, Act 548 , Eff. Apr. 1, 2013; Am. 2013, Act 220 , Eff. Jan. 1, 2014 | `67d2610bd9fb` | 24.8 KB |
| MCL 722.622 | Definitions. | ...018, Act 59 , Eff. June 12, 2018; Am. 2022, Act 67 , Eff. Nov. 1, 2022 | `f95553a62640` | 33.7 KB |
| MCL 722.623 | Individual required to report child abuse or neglect; report by telephone or online rep... | ...022, Act 47 , Eff. June 21, 2022; Am. 2022, Act 66 , Eff. Nov. 1, 2022 | `a8c8a67955a7` | 30.1 KB |
| MCL 722.628 | Referring report or commencing investigation; informing parent or legal guardian of inv... | ...016, Act 491 , Eff. Apr. 6, 2017; Am. 2022, Act 65 , Eff. Nov. 1, 2022 | `92d8bccbbc52` | 38.3 KB |

Source URL pattern: `https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-<sec-with-dashes>`
(e.g. `mcl-722-23`, `mcl-722-1204`). All fetched 2026-09-07 (see `results.jsonl` timestamps).

## `scao-forms/` — 16 acquired

| Form | Title | Rev./date on form | sha256 (pdf) | Size |
|---|---|---|---|---|
| MC 416 | UCCJEA Affidavit | 7/22 | `864476be3c6c` | 93.8 KB |
| MC 20 | Fee Waiver Request | 1/26 | `b9e91e0f5e42` | 118.6 KB |
| FOC 68 | Objection to Referee's Recommended Order | 3/21 | `40d7dd207145` | 130.0 KB |
| CC 375 | Petition for Personal Protection Order (Domestic Relationship) | 3/23 | `4cd3da236b76` | 145.2 KB |
| CC 376 | Personal Protection Order (Ex Parte) | 8/25 | `1a8a989f5124` | 372.6 KB |
| CC 379 | Motion to Modify, Extend, or Terminate PPO | 3/23 | `1759b1e043fe` | 293.6 KB |
| FOC 50 | Motion Regarding Support | 6/19 | `d139209829a1` | 360.9 KB |
| FOC 51 | Response to Motion Regarding Support | 6/17 | `4419167e6659` | 351.5 KB |
| FOC 65 | Motion Regarding Parenting Time | 6/17 | `b881baf77f34` | 350.7 KB |
| FOC 66 | Response to Motion Regarding Parenting Time | 6/17 | `16d3ebe02b26` | 333.7 KB |
| FOC 87 | Motion Regarding Custody | 6/18 | `e3278f483cb8` | 136.9 KB |
| FOC 88 | Response to Motion Regarding Custody | 6/17 | `8b990683fdf5` | 363.9 KB |
| FOC 89 | Order Regarding Custody and Parenting Time | 3/23 | `9960f8ec2376` | 143.5 KB |
| FOC 89a | Order Regarding Custody and Parenting Time (Following ADR) | 3/23 | `e1966fa661c4` | 147.9 KB |
| FOC 94 | Order Correcting Omission in Order (administrative, not a motion) | 6/17 | `b9b3c884f7fc` | 172.8 KB |
| FOC 106 | Notice of Redirection or Abatement of Child Support (FOC-issued notice, not a motion) | 12/24 | `15e32523c122` | 97.4 KB |

## `foc/` — 3 acquired

| Document | Date on document face | sha256 (pdf) | Size |
|---|---|---|---|
| Friend of the Court Model Handbook (FOCB/SCAO) | 2024 (title page; no month given) | `c18b05335f0d` | 403.4 KB |
| Michigan Parenting Time Guideline (FOCB) | Published Feb. 2021 / Last updated March 2022 | `4c14dad2245f` | 1.85 MB |
| INST FOC 68 — instructions for objecting to a referee's recommended order | Rev. 3/21 | `cd6564bfa876` | 135.3 KB |

## `mdhhs/` — 3 acquired

| Document | Title on document face | Effective/bulletin date | sha256 (pdf) | Size |
|---|---|---|---|---|
| PSM 000 | Children's Protective Services Manual Table of Contents | PSB 2026-002, 4-1-2026 | `3c259fb9a790` | 106.7 KB |
| PSM 711-4 | CPS Legal Requirements and Definitions | PSB 2024-001, 4-1-2024 | `833dacaf428f` | 198.6 KB |
| PSM 713-01 | CPS Investigation - General Instructions | PSB 2024-001, 4-1-2024 | `4e46a43b0fb0` | 369.2 KB |

## `genesee/` — 5 acquired

| File | What it is | sha256 | Size |
|---|---|---|---|
| `7thcircuitcourt_local-administrative-orders-index.html` | Local Administrative Orders index (2023-2026 listing) | `79aded662190` | 127.8 KB |
| `7thcircuitcourt_family-division.html` | Family Division page | `4ccc507bb255` | 45.0 KB |
| `genesee-fcp_c07-2025-04.pdf` | Family Court Plan (Joint LAO C07 2025-04J / P25 2025-02J, rescinds C07 2025-01J) | `aa3e1de54cce` | 158.3 KB |
| `mifile-court-list_efiling-status.pdf` | Statewide E-Filing Courts in Michigan list (Updated 03/17/26) — Genesee absent from both MiFILE charts | `bedca9f9c228` | 507.1 KB |
| `geneseecountymi_foc-online-forms-page.html` | Genesee County FOC online-forms page | `a781b3e2422f` | 176.7 KB |

## NOT_ACQUIRED

None. Every target attempted this pass (66 documents across 5 folders) was acquired on the
first or second retrieval strategy (plain `curl -A <browser UA>`, or `curl --tlsv1.2` for
`legislature.mi.gov`). No target required the python-requests fallback or WebFetch.

## Full source URL list

<details><summary>All 66 URLs fetched this pass (click to expand)</summary>

| File | URL |
|---|---|
| `mcl/mcl-722-21.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-21 |
| `mcl/mcl-722-22.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-22 |
| `mcl/mcl-722-23.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-23 |
| `mcl/mcl-722-24.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-24 |
| `mcl/mcl-722-25.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-25 |
| `mcl/mcl-722-26.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-26 |
| `mcl/mcl-722-26a.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-26a |
| `mcl/mcl-722-26b.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-26b |
| `mcl/mcl-722-26c.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-26c |
| `mcl/mcl-722-27.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27 |
| `mcl/mcl-722-27a.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27a |
| `mcl/mcl-722-27b.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-27b |
| `mcl/mcl-722-28.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-28 |
| `mcl/mcl-722-29.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-29 |
| `mcl/mcl-722-30.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-30 |
| `mcl/mcl-722-31.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-31 |
| `mcl/mcl-722-1201.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1201 |
| `mcl/mcl-722-1202.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1202 |
| `mcl/mcl-722-1203.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1203 |
| `mcl/mcl-722-1204.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1204 |
| `mcl/mcl-722-1205.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1205 |
| `mcl/mcl-722-1206.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1206 |
| `mcl/mcl-722-1207.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1207 |
| `mcl/mcl-722-1208.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1208 |
| `mcl/mcl-722-1209.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1209 |
| `mcl/mcl-722-1210.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-1210 |
| `mcl/mcl-600-2950.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-600-2950 |
| `mcl/mcl-600-2950a.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-600-2950a |
| `mcl/mcl-552-505.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-505 |
| `mcl/mcl-552-511.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-511 |
| `mcl/mcl-552-517.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-517 |
| `mcl/mcl-552-519.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-519 |
| `mcl/mcl-552-605.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-552-605 |
| `mcl/mcl-750-539c.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-750-539c |
| `mcl/mcl-750-539d.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-750-539d |
| `mcl/mcl-750-350a.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-750-350a |
| `mcl/mcl-722-622.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-622 |
| `mcl/mcl-722-623.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-623 |
| `mcl/mcl-722-628.html` | https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-722-628 |
| `scao-forms/mc416_uccjea-affidavit.pdf` | https://www.courts.michigan.gov/4a5228/siteassets/forms/scao-approved/mc416.pdf |
| `scao-forms/mc20_fee-waiver-request.pdf` | https://www.courts.michigan.gov/4a5cdb/siteassets/forms/scao-approved/mc20.pdf |
| `scao-forms/foc68_objection-to-referee-recommended-order.pdf` | https://www.courts.michigan.gov/4a75b2/siteassets/forms/scao-approved/foc68.pdf |
| `scao-forms/cc375_ppo-petition-domestic.pdf` | https://www.courts.michigan.gov/4a649f/siteassets/forms/scao-approved/cc375.pdf |
| `scao-forms/cc376_ppo-order.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/cc376.pdf |
| `scao-forms/cc379_ppo-motion-to-modify-extend-terminate.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/cc379.pdf |
| `scao-forms/foc50_motion-regarding-support.pdf` | https://www.courts.michigan.gov/4a7bfe/siteassets/forms/scao-approved/foc50.pdf |
| `scao-forms/foc51_response-to-motion-regarding-support.pdf` | https://www.courts.michigan.gov/499569/siteassets/forms/scao-approved/foc51.pdf |
| `scao-forms/foc65_motion-regarding-parenting-time.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc65.pdf |
| `scao-forms/foc66_response-to-motion-regarding-parenting-time.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc66.pdf |
| `scao-forms/foc87_motion-regarding-custody.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc87.pdf |
| `scao-forms/foc88_response-to-motion-regarding-custody.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc88.pdf |
| `scao-forms/foc89_order-regarding-custody-and-parenting-time.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc89.pdf |
| `scao-forms/foc89a_order-regarding-custody-and-parenting-time.pdf` | https://www.courts.michigan.gov/49282b/siteassets/forms/scao-approved/foc89a.pdf |
| `scao-forms/foc94_order-correcting-omission-in-order.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/foc94.pdf |
| `scao-forms/foc106_notice-of-redirection-or-abatement-of-child-support.pdf` | https://www.courts.michigan.gov/4ad065/siteassets/forms/scao-approved/foc106_new.pdf |
| `foc/focb-model-handbook_friend-of-the-court.pdf` | https://www.courts.michigan.gov/4a2945/siteassets/publications/pamphletsbrochures/focb/focb_hbk.pdf |
| `foc/michigan-parenting-time-guideline.pdf` | https://www.courts.michigan.gov/49422a/siteassets/court-administration/standardsguidelines/foc/pt_gdlns.pdf |
| `foc/foc68-instructions_objection-to-referee-recommended-order.pdf` | https://www.courts.michigan.gov/siteassets/forms/scao-approved/instfoc68.pdf |
| `mdhhs/psm-000_table-of-contents.pdf` | https://dhhs.michigan.gov/OLMWEB/ex/PS/Public/PSM/000.pdf |
| `mdhhs/psm-711-4_cps-legal-requirements-and-definitions.pdf` | https://dhhs.michigan.gov/OLMWEB/EXF/PS/Public/PSM/711-4.pdf |
| `mdhhs/psm-713-01_cps-investigation-general-instructions.pdf` | https://dhhs.michigan.gov/OLMWEB/ex/PS/Public/PSM/713-01.pdf |
| `genesee/7thcircuitcourt_local-administrative-orders-index.html` | https://7thcircuitcourt.com/general_information/local_administrative_orders.php |
| `genesee/7thcircuitcourt_family-division.html` | https://7thcircuitcourt.com/divisions/family_division.php |
| `genesee/genesee-fcp_c07-2025-04.pdf` | https://cms2.revize.com/revize/geneseecountyjudicialcourt/Documents/General%20Information/Local%20Administrative%20Orders/2025/C07%202025-04.pdf |
| `genesee/mifile-court-list_efiling-status.pdf` | https://www.courts.michigan.gov/494f83/siteassets/mifile/mifilecourtlist.pdf |
| `genesee/geneseecountymi_foc-online-forms-page.html` | https://www.geneseecountymi.gov/courts_and_law_enforcement/friend_of_the_court/online_forms.php |

</details>
