#!/usr/bin/env python3
"""cb_prove.py — STAGE 2: prove which tables in casebible.duckdb are redundant. READ-ONLY.

Byline: Claude Code · Fable 5 · 2026-08-27   (spec: HANDOFF.md §4 Stage 2)

Six families were identified by identical row counts. For each family the WIDEST table is the
candidate survivor; every NARROW table must pass ALL THREE checks against it, or the family does
NOT collapse:
  (1) key is 1:1 in both tables            count(*) = count(distinct key)
  (2) anti-join on key is 0 rows BOTH ways
  (3) every narrow column exists in the wide table AND
      count(*) where narrow.col IS DISTINCT FROM wide.col (joined on key) = 0

Output: a report Matt reads (stdout + cb_prove_report_<stamp>.md next to this script).
No judgement calls, no "close enough". PASS/FAIL per check, per table, with the offending numbers.

Usage:  python cb_prove.py [--db E:\\AI_Workspace\\casebible\\casebible.duckdb] [--family survivors]
Opens the DuckDB file read_only=True. Writes nothing to the database.
"""
import argparse, datetime, pathlib, sys
import duckdb

DEFAULT_DB = r"E:\AI_Workspace\casebible\casebible.duckdb"

# family name -> (wide/survivor table, [narrow tables], candidate join keys in preference order)
FAMILIES = {
    "keyed_987529":     ("scored4",     ["base", "base2", "scored", "scored2", "keyed"],        [("bucket", "path"), ("md5", "path"), ("path",)]),
    "survivors_337067": ("junk4",       ["survivors", "surv4", "final_survivors"],              [("bucket", "path"), ("md5", "path"), ("path",)]),
    "media_76007":      ("resolved",    ["mcut", "media", "mfolder", "dated"],                  [("dest",), ("dest", "size")]),
    "sorted_41621":     ("sorted_best", ["sorted_best4", "in_sorted"],                          [("md5",)]),
    "local_1281563":    ("ns_unique",   ["local_files"],                                        [("source", "path"), ("path",)]),
    "paired_1260":      ("cube",        ["paired"],                                             [("dest",), ("datedir", "base")]),
}

def cols(con, t):
    return [r[0] for r in con.execute("select column_name from information_schema.columns where table_schema='main' and table_name=? order by ordinal_position", [t]).fetchall()]

def q1(con, sql):
    return con.execute(sql).fetchone()[0]

def pick_key(con, wide, narrow, candidates):
    cw, cn = set(cols(con, wide)), set(cols(con, narrow))
    for k in candidates:
        if set(k) <= cw and set(k) <= cn:
            return k
    return None

def keyexpr(k, alias):
    return ", ".join(f'{alias}."{c}"' for c in k)

def joincond(k):
    return " AND ".join(f'w."{c}" IS NOT DISTINCT FROM n."{c}"' for c in k)

def prove(con, fam, wide, narrows, candidates, out):
    out(f"\n## family {fam}  —  survivor candidate: `{wide}`")
    cw = cols(con, wide); nw = q1(con, f'select count(*) from "{wide}"')
    out(f"- `{wide}`: {nw:,} rows, {len(cw)} cols")
    fam_pass = True
    for n in narrows:
        cn = cols(con, n); nn = q1(con, f'select count(*) from "{n}"')
        out(f"\n### `{n}` ({nn:,} rows, {len(cn)} cols) vs `{wide}`")
        k = pick_key(con, wide, n, candidates)
        if not k:
            out(f"- FAIL: no shared key among {candidates} — cannot prove; family does NOT collapse"); fam_pass = False; continue
        out(f"- join key: {k}")
        # (1) 1:1
        dw = q1(con, f'select count(*) - count(distinct ({keyexpr(k,"w")})) from "{wide}" w')
        dn = q1(con, f'select count(*) - count(distinct ({keyexpr(k,"n")})) from "{n}" n')
        c1 = (dw == 0 and dn == 0)
        out(f"- check 1 (key 1:1): wide dup-rows={dw:,}  narrow dup-rows={dn:,}  -> {'PASS' if c1 else 'FAIL'}")
        # (2) anti-join both ways
        a = q1(con, f'select count(*) from "{n}" n where not exists (select 1 from "{wide}" w where {joincond(k)})')
        b = q1(con, f'select count(*) from "{wide}" w where not exists (select 1 from "{n}" n where {joincond(k)})')
        c2 = (a == 0 and b == 0)
        out(f"- check 2 (anti-join): narrow-not-in-wide={a:,}  wide-not-in-narrow={b:,}  -> {'PASS' if c2 else 'FAIL'}")
        # (3) column subset + value equality
        missing = [c for c in cn if c not in cw]
        diffs = {}
        for c in cn:
            if c in missing or c in k: continue
            diffs[c] = q1(con, f'select count(*) from "{n}" n join "{wide}" w on {joincond(k)} where n."{c}" IS DISTINCT FROM w."{c}"')
        bad = {c: v for c, v in diffs.items() if v}
        c3 = (not missing and not bad)
        out(f"- check 3 (columns): missing-in-wide={missing or 'none'}; value-diffs={bad or 'none'} (checked {len(diffs)} cols)  -> {'PASS' if c3 else 'FAIL'}")
        verdict = c1 and c2 and c3
        fam_pass &= verdict
        out(f"- **{n}: {'REDUNDANT — safe to collapse into ' + wide if verdict else 'NOT PROVEN — keep'}**")
    out(f"\n**FAMILY {fam}: {'ALL PASS — collapses to `' + wide + '`' if fam_pass else 'DOES NOT COLLAPSE (at least one check failed)'}**")
    return fam_pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--family", default=None, help="run one family only (name from FAMILIES)")
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    report = pathlib.Path(__file__).with_name(f"cb_prove_report_{stamp}.md")
    lines = [f"# cb_prove report — {stamp}", f"> _Byline: cb_prove.py · Claude Code · Fable 5 · read-only over `{a.db}`_", ""]
    def out(s): print(s); lines.append(s)
    fams = {a.family: FAMILIES[a.family]} if a.family else FAMILIES
    results = {}
    for fam, (wide, narrows, keys) in fams.items():
        try:
            results[fam] = prove(con, fam, wide, narrows, keys, out)
        except Exception as e:
            out(f"\n## family {fam}: ERROR {e!r} — treated as NOT PROVEN"); results[fam] = False
    out("\n# Summary")
    for fam, ok in results.items(): out(f"- {fam}: {'COLLAPSE' if ok else 'KEEP ALL'}")
    out("\nNothing was modified. Stage 3 (cb_collapse.py) may only touch families marked COLLAPSE.")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport -> {report}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
