#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Collect the local zero-filled (corrupt) rows from dedupe-plan TSVs into one CSV for corrupt_recovery_count.sql.

A plan row with class = excluded_zero and size > 0 is an all-zero payload (a dehydrated-placeholder backup);
size = 0 rows are empty files, not corruption, and are left out. Output columns match the hold manifest:
store, container, path, size, hash_kind, hash, reason.

Usage: local_zero_rows.py <out.csv> <store>=<plan.tsv> | scan:<store>=<zero_scan.tsv> [...]
  plan input : dedupe-plan TSV (class = excluded_zero, size > 0)
  scan input : zero_scan.py output (path, size, mtime, attrs) — the 2026-09-13 all-zero scans of F: and D:, which
               are the record of what was quarantined (F:'s zero files were moved before F: was re-hashed, so the
               F: plans no longer carry them). The F: scan has the bare-drive-root bug (first character of the top
               folder dropped: "ase/…", "isk Drill/…"); basenames are intact, which is all the count keys on.
               <store> may be "auto-F" to route rows by top folder: ase→local/F-case, isk Drill→local/F-Disk-Drill.
"""
import csv
import sys

F_TOP = {"ase": ("local/F-case", "case"), "isk Drill": ("local/F-Disk-Drill", "Disk Drill")}


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    out = sys.argv[1]
    n = 0
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["store", "container", "path", "size", "hash_kind", "hash", "reason"])
        for arg in sys.argv[2:]:
            if arg.startswith("scan:"):
                store, scan = arg[5:].split("=", 1)
                with open(scan, encoding="utf-8", newline="") as src:
                    for r in csv.DictReader(src, delimiter="\t", quoting=csv.QUOTE_NONE):
                        if int(r["size"]) <= 0:
                            continue
                        path, st = r["path"], store
                        if store == "auto-F":
                            top, _, rest = path.partition("/")
                            st, fixed = F_TOP.get(top, ("local/F-unknown", top))
                            path = fixed + "/" + rest
                        w.writerow([st, "", path, r["size"], "", "", "all_zero_payload"])
                        n += 1
                continue
            store, plan = arg.split("=", 1)
            with open(plan, encoding="utf-8", newline="") as src:
                for r in csv.DictReader(src, delimiter="\t"):   # DuckDB writes RFC CSV with a tab delimiter
                    if r["class"] == "excluded_zero" and int(r["size"]) > 0:
                        w.writerow([store, "", r["path"], r["size"], "md5", r["md5"], "all_zero_payload"])
                        n += 1
    print(f"local zero-filled rows: {n} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
