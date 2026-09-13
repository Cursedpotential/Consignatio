# Source Archive

Local copies of primary legal sources accessed during verification, so the drafting
phase quotes from files in this repo rather than re-fetching, and so any claim in the
treatise can be traced to a document that is under version control.

**Archived:** August 9, 2026.

---

## `primary/` — full documents held locally

| File | What it is | Currency stamp on the document face | Size |
|---|---|---|---|
| `michigan-court-rules_2026-07-31.pdf` | **Michigan Court Rules, complete, all chapters** — official SCAO consolidated PDF | "Updated July 31, 2026"; Chapters 2, 3, and 7 each stamped "Chapter Updated May 1, 2026" | 3.8 MB |
| `michigan-court-rules_2026-07-31.txt` | Text extraction of the above (`pdftotext -layout`) | — | 2.9 MB |
| `michigan-rules-of-evidence_2026-01-28.pdf` | **Michigan Rules of Evidence, complete** — official SCAO PDF | "Updated with MSC order(s) effective on 1/28/2026" | 442 KB |
| `michigan-rules-of-evidence_2026-01-28.txt` | Text extraction of the above | — | 81 KB |

`SHA256SUMS` fixes the PDFs so a later re-download can be diffed against what was
actually verified.

**Source URLs**

- MCR — `https://www.courts.michigan.gov/48ec32/siteassets/rules-instructions-administrative-orders/michigan-court-rules/michigan-court-rules.pdf`
- MRE — `https://www.courts.michigan.gov/498acb/siteassets/rules-instructions-administrative-orders/rules-of-evidence/michigan-rules-of-evidence.pdf`

Note the hex path segment (`48ec32`, `498acb`). These are CMS-generated and **have
changed before** — the second research package recorded a different MRE path
(`492ca5`). If a URL 404s, search `courts.michigan.gov` for the document title rather
than assuming it was withdrawn.

---

## How to retrieve these (this is the part that was previously wrong)

Every earlier pass in this project recorded `courts.michigan.gov` as `disallow_by_robots`
and reconstructed rule text from search snippets and secondary mirrors. That was a
**User-Agent block, not a robots wall**, and it is why the outline carries rule text
that in several places does not match the current rule.

**What works:**

```sh
curl -sS -L -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36" \
  -o michigan-court-rules.pdf \
  "https://www.courts.michigan.gov/48ec32/siteassets/rules-instructions-administrative-orders/michigan-court-rules/michigan-court-rules.pdf"

pdftotext -layout michigan-court-rules.pdf michigan-court-rules.txt
```

`pdftotext` comes from `poppler-utils` (`apt-get update && apt-get install -y poppler-utils`).

**What does not work, and why:**

| Method | Result |
|---|---|
| `WebFetch` against `courts.michigan.gov` | HTTP 503 — no browser UA |
| `curl`/`urllib` against `legislature.mi.gov` | `CERTIFICATE_VERIFY_FAILED — unable to get local issuer certificate`, including with `--cacert /root/.ccr/ca-bundle.crt`. The origin appears not to serve a complete chain. **Do not work around this by disabling TLS verification.** |
| Exa `web_fetch_exa` against `legislature.mi.gov` | **Works** — fetched server-side, outside this session's TLS path. This is the route used for every MCL section verified this pass. |
| `law.justia.com` direct | HTTP 403 to `WebFetch`; `CRAWL_INFRASTRUCTURE_ERROR` to Exa |

---

## Statutes (MCL) — referenced, not archived

MCL sections could not be saved locally because of the TLS limitation above. They were
read in full via Exa and the operative text is quoted verbatim in
`../verification_ledger.md` and `../research_interference_coercive_control.md`.

**Currency caveat carried forward:** the `legislature.mi.gov` pages retrieved display
the banner **"Michigan Compiled Laws Complete Through PA 2 of 2025."** Every MCL quote
in this project is verified only to that compilation point. Confirm no later public act
has amended these sections before publication.

Sections read in full this pass:

| Section | Subject | Last amendment shown |
|---|---|---|
| MCL 722.23 | Best interests of the child — factors (a)–(l) | 2016 PA 95 |
| MCL 722.26a | Joint custody | 1980 PA 434 |
| MCL 722.27 | Powers of the court; the ECE clause | 2015 PA 52 |
| MCL 722.27a | Parenting time; the separate (7) factor list; (9) order-terms menu | 2016 PA 96 |
| MCL 552.505a | Opening and closing an FOC case | 2009 PA 233 |
| MCL 552.507 | Referee powers; de novo hearing | — |
| MCL 552.605b | Support after age 18 | 2009 PA 193 |
| MCL 552.605c | Monthly support amounts; proration | 2009 PA 193 |
| MCL 552.641 | FOC response to custody/parenting-time violations; the 56-day provision | 2002 PA 568 |
| MCL 552.642 | Makeup parenting time; the 21-day deemed-agreement rule | 2002 PA 568 |
| MCL 552.644 | Civil contempt for parenting-time violations | 2014 PA 378 |
| MCL 400.1501 | Domestic violence definitions | 2023 PA 182 |
| MCL 600.2591 | Frivolous action costs and fees | 1986 PA 178 |
| MCL 600.2950 | Personal protection orders | — |
| MCL 750.411h | Stalking | 2023 PA 199 |

**Failed:** MCL 750.350a (parental kidnapping) — two Exa attempts returned
`CRAWL_NETWORK_ERROR`. Unverified.

---

## Case law — referenced, not archived

Verified through the CourtListener API (free tier, throttled at 5 requests/minute).
Citations and holdings are recorded in `../verification_ledger.md` §4. Full opinion
texts were not archived; `cluster_id` values are recorded in the ledger so any opinion
can be re-read directly.

---

## What is deliberately not here

- **Genesee County local documents.** Not archived here. Local facts are the one layer that
  must be confirmed with the clerk regardless of what any archive says — see
  `../verification_ledger.md` §6.
- **SCAO forms.** Link to the official form; never publish a competing version
  (outline §0.1 item 8). Archiving a form PDF here would invite exactly that.
- **ICLE materials.** Subscription, cite-only.

> **Plugin note:** the source **PDFs are not bundled in the plugin** (they are ~24 MB); a model reads the markdown, not the PDF. Structured **markdown** extractions ship instead (smaller and more usable than the PDFs). Run `fetch-sources.sh` to download the PDFs, and verify them against
> `SHA256SUMS`. The full PDFs also live in the repo at `Projects/custody-guide/sources/primary/`.
