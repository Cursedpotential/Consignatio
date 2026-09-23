#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Split the OneDrive inventories into copy-now / hash-first / zero lists. Runs ON the VPS.

Why: OneDrive only exposes quickxor hashes, which nothing else in the corpus has, and the R2
`casebible-quarantine/onedrive/` tree is an earlier copy of the same files — so 319k of 323k
OneDrive files collide by size with the catalog (measured 2026-09-14). Size alone decides nothing;
the collision set must be content-hashed server-side (streamed on the VPS, never through the
laptop's OneDrive client) before anything is copied. Files whose size matches nothing in the
catalog are new by construction and can be copied without a hash pass.

Inputs:
  <inventory dir>/<scope>.lsjson   rclone lsjson -R --hash output per OneDrive scope
  <known sizes file>               one integer per line (distinct sizes from raw_duck.r2_files)
Outputs (in <out dir>):
  <scope>.new.list      paths with a size unseen in the catalog       -> copy directly (--files-from-raw)
  <scope>.collide.list  paths whose size exists in the catalog        -> hash first (rclone hashsum --download)
  <scope>.zero.list     0-byte paths                                  -> catalog only, never copied
  onedrive-plan-summary.tsv  per-scope counts and bytes
Read-only against the sources; writes plan files only.
"""
import json
import os
import sys

SCOPES = ("AI_Space", "Case_Bible", "Documents_CSV", "Documents_Disk_Drill")


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    inv_dir, known_file, out_dir = sys.argv[1:4]
    known = {int(l) for l in open(known_file, encoding="utf-8") if l.strip()}
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for scope in SCOPES:
        objs = json.load(open(os.path.join(inv_dir, f"{scope}.lsjson"), encoding="utf-8"))
        buckets = {"new": [], "collide": [], "zero": []}
        nbytes = {"new": 0, "collide": 0, "zero": 0}
        for o in objs:
            if o.get("IsDir"):
                continue
            size = o["Size"]
            kind = "zero" if size == 0 else ("collide" if size in known else "new")
            buckets[kind].append(o["Path"])
            nbytes[kind] += size
        for kind, paths in buckets.items():
            with open(os.path.join(out_dir, f"{scope}.{kind}.list"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("".join(p + "\n" for p in paths))
        rows.append((scope, len(buckets["new"]), nbytes["new"], len(buckets["collide"]), nbytes["collide"], len(buckets["zero"])))
    with open(os.path.join(out_dir, "onedrive-plan-summary.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("scope\tnew_files\tnew_bytes\tcollide_files\tcollide_bytes\tzero_files\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
            print(f"{r[0]}: new={r[1]} ({r[2]/1e9:.1f} GB) collide={r[3]} ({r[4]/1e9:.1f} GB) zero={r[5]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
