---
title: vault/v1 twin reconciliation — content overlap, per-group headroom, unit safety
date: 2026-09-16
status: analysis
tags: [consignatio, vault, twins, dedup, catalog, raw_duck, receipt]
sources:
  - raw_duck.vault_twins_groups (2,131 groups, casebible/tools/vault_name_normalize.py)
  - raw_duck.vault_twins_pairs / vault_twins_overlap (vault_twins_05_overlap.sql)
  - raw_duck.vault_twins_group_summary (vault_twins_07_group_summary.sql)
  - raw_duck.vault_twins_unit_safety (vault_twins_08_unit_safety.sql, vault_units_v2 = 711 units)
  - raw_duck.vault_twins_rehome (vault_twins_06_rehome.sql) — launched 09:45 EDT, results appended below when done
---

> _Byline: Claude Code · Fable 5.1 · 2026-09-16 09:50 EDT (analysis tables built by Claude Code · Sonnet 5, same morning). Read-only analysis. No object was moved, copied or deleted._

## What was asked

Owner 07:51–07:52 EDT: collapse same-name and numbered/copy twins inside `b2:salem-data/consignatio/vault/v1/` to one root, without mangling atomic units. Step 1 (one root) is materialized. This receipt is the content check behind step 2: which name-twins are actually the same bytes, which are separate exports that merely share a name, and how much a merge would collapse.

## Method

1. **Candidates.** 20,816 directories at depth 1–4 → normalizer keys → **2,131 groups** (286 flagged UNIT by name pattern). Every group is a set of directories whose normalized name matches; nothing else is assumed.
2. **Identity of a file across two directories** (brief): same sha1, else same md5, regardless of relative path; if neither side has a hash (51 objects of 1,677,487), same relative path + size.
3. **Pairs.** All same-group member pairs, 74,382. Ancestor/descendant pairs are flagged `dropped_nested` and never compared. **0 flagged** (verified live 08:45 and again after the 08:55 `starts_with` hardening, 0 diffs).
4. **Pair class.** IDENTICAL (no unique files either side), SUBSET (one side fully contained), PARTIAL (shared content and unique files both sides), DISJOINT (no shared content).
5. **Per-group headroom** (07): pairwise numbers inflate on big groups (101 members → 5,050 pairs), so the group view sums each distinct content key once: `dup_bytes = total_bytes − distinct_bytes` is what merge-to-one-copy would collapse.
6. **Unit safety** (08): a group is `UNIT_OVERLAP_UNSAFE` if any member is, contains, or sits inside a recognized atomic unit (`vault_units_v2`, 711 roots); `ALL_MEMBERS_ARE_UNITS` if every member is itself a unit root; else `NO_UNIT_OVERLAP`.

## Headline

| measure | value |
|---|---|
| groups / members compared | 2,131 / 74,382 pairs |
| pairs IDENTICAL / SUBSET / PARTIAL / DISJOINT | 52,356 / 3,242 / 7,913 / 10,871 |
| groups with at least one IDENTICAL pair | 776 |
| total bytes across all group members | 5,089 GB (4,799 non-unit + 290 unit groups) |
| collapsible (duplicate) bytes, union view | **642 GB** (621 non-unit + 21 unit) |
| of which in `NO_UNIT_OVERLAP` groups (mergeable without unit reasoning) | **32.2 GB in 1,328 groups** |
| of which in `UNIT_OVERLAP_UNSAFE` groups | 565 GB in 508 groups |
| of which in `ALL_MEMBERS_ARE_UNITS` groups | 23.4 GB in 9 groups |
| groups where every pair is IDENTICAL | 607 (176 safe / 430 unit-unsafe / 1 all-units), 2,138 extra copies, 0.6 GB |

**Reading.** Almost all of the apparent 642 GB of duplication sits in groups that touch atomic units: the `takeout` family alone shows 407 GB "duplicate" across 15 roots, but those roots are different Google exports of the same accounts (Photos re-exported, Drive re-exported), i.e. corroborating copies that stay separate units and get *linked*, not merged. The merge headroom that needs no unit reasoning is ~32 GB, and the byte-identical whole-directory twins that are trivially collapsible amount to well under 1 GB, because the graded copy already stored each payload once. The consolidation win is structural (one tree, fewer names), not storage.

## Pair classes by group type

| unit_group | class | pairs | common GB | unique GB |
|---|---|---|---|---|
| no | IDENTICAL | 50,779 | 11.30 | 0 |
| no | SUBSET | 2,515 | 5.35 | 332 |
| no | PARTIAL | 6,758 | 51.70 | 35,814 |
| no | DISJOINT | 8,977 | 0 | 12,614 |
| yes | IDENTICAL | 1,577 | 2.81 | 0 |
| yes | SUBSET | 727 | 18.76 | 57 |
| yes | PARTIAL | 1,155 | 8.24 | 272 |
| yes | DISJOINT | 1,894 | 0 | 4,215 |

(Pairwise GB double-count members that sit in many pairs; use the union view for sizing.)

## Unit safety vs normalizer flag

| normalizer says UNIT | safety class | groups |
|---|---|---|
| no | NO_UNIT_OVERLAP | 1,328 |
| no | UNIT_OVERLAP_UNSAFE | 508 |
| no | ALL_MEMBERS_ARE_UNITS | 9 |
| yes | NO_UNIT_OVERLAP | 92 |
| yes | UNIT_OVERLAP_UNSAFE | 171 |
| yes | ALL_MEMBERS_ARE_UNITS | 23 |

The name-pattern flag misses 517 groups that touch units; the unit table, not the name, decides safety.

## Top 30 groups by collapsible bytes

| group_key | unit | safety | n | files | total GB | dup GB | pair classes | trunk (largest member) |
|---|---|---|---|---|---|---|---|---|
| takeout | no | UNSAFE | 15 | 190,142 | 1,385.09 | 406.85 | D51 I1 P43 S10 | Takeout [gdrive-salemnet] |
| archive | no | UNSAFE | 6 | 164,346 | 735.58 | 33.99 | D11 P4 | Archive |
| moved/evidence/facebook/facebook | no | UNSAFE | 4 | 108,344 | 40.70 | 30.05 | D5 P1 | moved/Evidence/FB Exports/FB DATA |
| photos | no | SAFE | 5 | 162,413 | 113.62 | 28.93 | D5 P5 | Photos |
| archive/takeout | no | UNSAFE | 3 | 67,304 | 680.07 | 24.60 | D2 P1 | Archive/Takeout Data |
| archive/takeout/takeout | no | ALL-UNITS | 3 | 66,604 | 678.77 | 23.38 | P3 | Archive/Takeout Data/Google Takeout |
| documents | no | UNSAFE | 3 | 23,232 | 40.79 | 11.91 | P3 | Documents |
| takeout/takeout | no | UNSAFE | 101 | 97,519 | 204.18 | 10.90 | D1333 I440 P2943 S334 | Takeout [gdrive-salemnet]/Takeout |
| review hold/duplicates/<hold> | no | UNSAFE | 3 | 17,488 | 38.01 | 10.51 | I1 S2 | .review_hold/duplicates/swept |
| takeout/takeout/photos | no | UNSAFE | 30 | 46,264 | 26.93 | 10.36 | D82 I326 P26 S1 | Takeout/Takeout/Google Photos |
| moved/court/facebook/<facebook-export> | yes | UNSAFE | 16 | 40,879 | 11.64 | 7.84 | D39 I4 P59 S18 | moved/court/fb/Facebook-…-2025-08-18 |
| facebook | no | UNSAFE | 2 | 27,410 | 38.58 | 4.70 | D1 | fb |
| takeout/downloads | no | UNSAFE | 3 | 9,596 | 6.81 | 4.08 | I1 S2 | Takeout/Downloads 2 |
| takeout/<takeout-sibling> | yes | ALL-UNITS | 35 | 36,687 | 29.10 | 3.75 | D561 I2 P17 S15 | Takeout/Takeout 5 |
| case bible | no | UNSAFE | 3 | 4,831 | 6.64 | 1.98 | D2 P1 | Case Bible |
| takeout/salemnma | no | UNSAFE | 3 | 690 | 3.54 | 1.81 | I1 S2 | Google takeout files/salemnma [local-D-Backup] |
| takeout/salemnma/drive | no | UNSAFE | 3 | 354 | 3.52 | 1.80 | I1 S2 | …/salemnma [local-D-Backup]/Drive |
| triage/archive | no | UNSAFE | 2 | 903 | 4.34 | 1.70 | D1 | Triage/Recovered Files |
| facebook/<facebook-export> | yes | ALL-UNITS | 4 | 15,886 | 5.30 | 1.50 | D2 P4 | fb/Facebook-…-2025-08-18 |
| court | no | UNSAFE | 3 | 19,947 | 48.44 | 1.38 | D2 P1 | Court & Legal Project |
| snapchat | no | UNSAFE | 2 | 936 | 2.25 | 1.34 | D1 | snap data |
| folder | no | UNSAFE | 2 | 4,319 | 9.71 | 1.27 | D1 | New Folder |
| takeout/photos | no | UNSAFE | 6 | 28,407 | 6.82 | 1.04 | D8 P5 S2 | Takeout [local-D-Backup]/Google Photos |
| evidence | no | UNSAFE | 2 | 46,513 | 504.88 | 0.75 | P1 | EvidenceVault |
| takeout/<takeout-sibling>/drive | yes | UNSAFE | 8 | 208 | 5.46 | 0.73 | D28 | Takeout/Takeout 2/Drive |
| takeout/<takeout-sibling>/drive/takeout | yes | UNSAFE | 7 | 206 | 5.46 | 0.73 | D21 | Takeout/Takeout 2/Drive/Takeout |
| takeout/downloads/<google-mydata> | yes | UNSAFE | 20 | 3,831 | 1.32 | 0.69 | D36 I7 P119 S28 | …/Downloads 2/mydata~1744328466072 (1) |
| takeout/<takeout-sibling>/takeout | yes | UNSAFE | 8 | 3,537 | 1.40 | 0.67 | D25 P1 S2 | …/Takeout (3)/Takeout 4 [local-D-Backup] |
| takeout/<takeout-sibling>/takeout/photos | yes | UNSAFE | 4 | 3,096 | 1.33 | 0.66 | D4 S2 | …/Takeout 4 [local-D-Backup]/Google Photos |
| <hold> | no | UNSAFE | 5 | 14,020 | 8.13 | 0.66 | D4 P6 | _SWEPT |

Pair classes: D = DISJOINT, I = IDENTICAL, P = PARTIAL, S = SUBSET, number = pairs.

Notes on the big ones:
- **takeout (15 roots, 407 GB dup)** and **takeout/takeout (101 members)**: 51 of 105 root pairs are DISJOINT and 43 PARTIAL. These are different export dates of the same accounts. Treat as separate units, record the cross-links in the catalog, do not merge.
- **archive / archive/takeout / archive/takeout/takeout (≈700 GB)**: `Archive`, `Archive/Takeout Data/{Google Takeout, Takeout, Takeout Data1}` are export packages that were archived whole; the three-member group where every member is a unit root is PARTIAL on all three pairs, so they are distinct exports too.
- **moved/evidence/facebook/facebook (30 GB dup)** and **facebook** (`fb` vs the FB DATA trunk): FB exports copied under several names; the pairs are DISJOINT/PARTIAL because each is a different export or a subset; the identical file payloads are already single in B2 storage.
- **photos (SAFE, 29 GB dup, 5 members)**: the one large group with no unit inside. `Photos`, `Photos/photo_recovery/Photos`, `Imported Photos`… share 54,612 duplicate files. This is the first real merge candidate.
- **evidence (505 GB)**: `EvidenceVault` vs `Evidence`, one PARTIAL pair, only 0.75 GB overlapping. These are not twins; the `evidence` synonym fold is a false grouping.

## Safe-to-merge groups (NO_UNIT_OVERLAP, non-unit), top 15 by collapsible bytes

| group_key | n | files | total GB | dup GB | dup files | pair classes | trunk |
|---|---|---|---|---|---|---|---|
| photos | 5 | 162,413 | 113.62 | 28.93 | 54,612 | D5 P5 | Photos |
| obsidian vault/obsidian | 3 | 8,017 | 1.02 | 0.48 | 5,796 | S3 | Obsidian Vault/.obsidian [local-D-Backup] |
| obsidian vault/obsidian/plugins | 3 | 7,750 | 1.01 | 0.48 | 5,595 | S3 | …/.obsidian [local-D-Backup]/plugins |
| takeout/photos/a | 2 | 480 | 0.60 | 0.30 | 240 | I1 | Takeout [local-D-Backup]/Google Photos/A |
| photos/photo recovery/photos | 2 | 50,048 | 24.63 | 0.27 | 6,151 | P1 | Photos/photo_recovery/Photos |
| photos/photos | 2 | 187 | 0.47 | 0.23 | 95 | D1 | Photos/Imported Photos |
| takeout/photos/fuck man | 2 | 9,884 | 1.30 | 0.14 | 4,826 | S1 | Takeout [local-D-Backup]/Google Photos/Fuck man |
| evidence/messaging | 2 | 1,370 | 5.83 | 0.11 | 281 | D1 | EvidenceVault/messaging |
| takeout/photos/untitled | 14 | 1,285 | 1.42 | 0.10 | 638 | D84 I6 S1 | Takeout [local-D-Backup]/Google Photos/Untitled |
| takeout/photos/google photos convo | 2 | 492 | 0.13 | 0.06 | 246 | I1 | …/Google Photos/Google photos convo |
| <hold>/person info backup 2026 03 12 | 3 | 290 | 0.22 | 0.05 | 59 | D1 P1 S1 | _TO_BE_DELETED2/Person_Info_Backup_2026-03-12 |
| <hold>/person info backup 2026 03 12/ai chats | 3 | 185 | 0.21 | 0.05 | 47 | D1 S2 | …/Person_Info_Backup_2026-03-12/chats |
| legal kb | 3 | 1,608 | 0.62 | 0.05 | 856 | D2 P1 | Legal_Knowledge_Base_Obsidian1 |
| desktop/new folder | 2 | 44 | 0.08 | 0.04 | 22 | D1 | Desktop/untitled folder 2 |
| court/court | 2 | 239 | 0.49 | 0.03 | 33 | P1 | Court & Legal Project/Court |

Whole-directory identical twins in the safe class: **176 groups, 243 extra copies, 0.40 GB** — the cheapest first collapse. List them with:

```sql
select gs.* from raw_duck.vault_twins_group_summary gs
join raw_duck.vault_twins_unit_safety s using (group_key)
where s.safety_class = 'NO_UNIT_OVERLAP'
  and exists (select 1 from raw_duck.vault_twins_overlap o where o.group_key = gs.group_key)
  and not exists (select 1 from raw_duck.vault_twins_overlap o where o.group_key = gs.group_key and o.class <> 'IDENTICAL')
order by gs.dup_bytes desc;
```

## Caveats

- Nested pairs: 0 today; the exclusion is structural in `vault_twins_05_overlap.sql` (`WHERE NOT dropped_nested`), so a broader normalizer cannot leak nested pairs into the classes. Re-run `select count(*) from raw_duck.vault_twins_pairs where dropped_nested` after any regex change.
- `vault_twins_08_unit_safety.sql` containment test switched from `LIKE … || '/%'` to `starts_with` at 09:58 EDT (962 paths contain `_`, a LIKE wildcard); table rebuilt in one transaction, 0 of 2,131 groups changed class. Same fix as 05.
- Synonym folds that produced false twins and should be tightened before proposals: `archive` (Archive + recovered + Backups), `evidence` (EvidenceVault vs Evidence), generic `folder` / `photos` / `documents`.
- The identity rule ignores relative path for hashed files, so a PARTIAL pair can be two different folder layouts of the same photos; `path_conflict_files` in `vault_twins_overlap` counts same-path-different-content cases per pair.

## Next (owner decisions, nothing moves without GO)

1. Merge proposal for the `NO_UNIT_OVERLAP` groups, starting with `photos` (29 GB) and the 176 fully identical groups; proposal = trunk member kept, other members' occurrences recorded in `source_occurrences`, then server-side copy into the merged path, nothing deleted.
2. Unit-touching groups: link, don't merge; write the cross-export relationships as catalog rows.
3. Tighten the three synonym folds above and re-run 04→08 (idempotent, minutes).
4. Re-home classification of the 52 GB quarantine-class content: `vault_twins_06_rehome.sql`, running at time of writing; results appended below.

## Re-home results (10:00 EDT)

`vault_twins_06_rehome.sql` ran on ovh-files (log `/opt/casebible/logs/vault_twins_06_rehome.log`). 15 quarantine/hold/delete-class roots resolved at depth 1 plus `Triage/_recovered`: **43,266 files, 48.8 GB** (owner estimate 52 GB / 42k). Each file classified against the rest of the vault: HAS-HOME-IN-VAULT = same sha1/md5 exists outside quarantine; PATH-TWIN-ONLY = only a same-basename file exists; ORPHAN = neither.

| class | files | GB | meaning |
|---|---|---|---|
| HAS-HOME-IN-VAULT | 42,918 | 48.49 | a byte-identical copy already lives in the vault proper |
| PATH-TWIN-ONLY | 138 | 0.22 | same file name elsewhere, different bytes |
| ORPHAN | 210 | 0.08 | nothing else in the vault matches |

By root: `.review_hold` 25,700 / 39.5 GB homed (17 orphans); `_SWEPT` 12,767 / 6.1 GB homed (1 orphan); `_TO_BE_DELETED2` 1,116 / 1.8 GB homed; `NOT FUCKING TRSASH` 1,260 / 0.4 GB homed; `Triage/_recovered` 873 homed; `_dedup` 916 homed + 147 orphans + 13 path-twins; `_Quarantine - zero filled` 3 homed + 44 orphans + 119 path-twins. Homes are spread across `Archive` (18,692), `4tb` (7,115), `_backup_import` (3,417, 19.8 GB), `Case Bible`, `onedrive`, `fb`, `Court & Legal Project`, `Evidence`.

What the small classes are:
- **`_Quarantine - zero filled` path-twins (119)**: the quarantined object is the zero-filled payload and the real-bytes copy exists under the same name elsewhere (e.g. `Takeout 5/…/20220828_162333.mp4` ↔ `Archive/Takeout Data/…/Family/20220828_162333.mp4`). Expected; the good copy is already in the vault.
- **`_Quarantine - zero filled` orphans (44, 0.07 GB)**: zero-filled payloads with **no other copy anywhere in the vault** — mostly `Takeout 5/Google Photos/Photos from 2022/IMG_55xx.{HEIC,MP4}` (Aug 2022 iPhone captures) plus 14 JSON sidecars, 2 CSV, 2 PDF. These are the confirmed losses from the Drive restore; only an outside source (device, iCloud, another export) can recover them.
- **`_dedup` orphans (147)**: `.js` / `.cts` / `.py` / `__target__` — dev-tool remnants (node_modules-class); junk, not evidence.
- **`.review_hold` orphans (17)**: `__target__`, `.py`, `.terms` build artifacts.

Implication for step 2: 99.5 % of quarantine-class bytes already have a home in the vault, so the quarantine roots can be retired from the tree by recording each file's occurrence against its `example_home` in the catalog and leaving the bytes where the graded copy put them; nothing needs to move to keep them. The 44 zero-filled orphans go on the loss list; the 164 dev-junk orphans go to the junk policy.
