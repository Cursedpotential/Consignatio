# Byline: Claude Code · Opus 5 · 2026-09-16 07:08 EDT (session propria-79)
"""Build the two hard-delete lists for the vault dedupe + intake prune, with safety checks that abort on any risk.

Owner 2026-09-16 07:01: "You need to dedupe this. And if it's into the vault [it] needs to be removed from intake."

Inputs (all on ovh-files):
  --manifest   vault_copy_manifest_v6.csv   canonical_key,dest_key,size  (every object the copy wrote)
  --keep       vault_keep_v6.csv            canonical_key,dest_key,size  (the ONE vault object kept per source object)
  --vault      fresh lsjson of b2:salem-data/consignatio/vault/v1/  (Path relative to that prefix, Size)
  --intake     fresh lsjson of b2:salem-data/consignatio/intake/raw-dedupe/v1/source-buckets/
  --catalog    intake_catalog_sha1.csv      key,size,sha1  (sha1 from the 2026-09-14 B2 listing)
Outputs:
  vault_delete.list    bucket-relative keys: duplicate vault copies (never a kept object)
  intake_delete.list   bucket-relative keys: intake objects whose content is in a kept, present vault object
  intake_keep.tsv      intake objects NOT proven in the vault (they stay)
Rules for intake: (a) the object is the source of a kept vault object with equal size; (b) its sha1+size equals the
sha1+size of such a source object; (c) size >= 100 MB and a kept vault object has the same file name and size.
"""
import argparse
import csv
import json
import os
import sys

VAULT_PREFIX = "consignatio/vault/v1/"
INTAKE_PREFIX = "consignatio/intake/raw-dedupe/v1/source-buckets/"
BIG = 100_000_000


def load_lsjson(path, prefix):
    with open(path, encoding="utf-8") as fh:
        return {prefix + item["Path"]: int(item["Size"]) for item in json.load(fh)}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def fail(msg):
    print("ABORT:", msg, flush=True)
    sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    for name in ("manifest", "keep", "vault", "intake", "catalog", "outdir"):
        ap.add_argument("--" + name, required=True)
    args = ap.parse_args()

    vault = load_lsjson(args.vault, VAULT_PREFIX)
    intake = load_lsjson(args.intake, INTAKE_PREFIX)
    print(f"fresh listings: vault {len(vault):,} objects / {sum(vault.values()) / 1e9:,.1f} GB · "
          f"intake {len(intake):,} objects / {sum(intake.values()) / 1e9:,.1f} GB")

    keep_by_src = {}
    keep_keys = set()
    for row in read_csv(args.keep):
        dest, size = row["dest_key"], int(row["size"])
        if vault.get(dest) != size:
            fail(f"kept vault object missing or wrong size in fresh listing: {dest}")
        keep_by_src[row["canonical_key"]] = (dest, size)
        keep_keys.add(dest)
    print(f"kept vault objects: {len(keep_keys):,} (all present, sizes match)")

    vault_delete = []
    manifest_srcs = set()
    name_to_src = {}  # (file name, size) of ANY copy present in the vault -> its source object (kept copy may be renamed)
    for row in read_csv(args.manifest):
        manifest_srcs.add(row["canonical_key"])
        dest = row["dest_key"]
        if vault.get(dest) == int(row["size"]):
            name_to_src.setdefault((os.path.basename(dest), int(row["size"])), row["canonical_key"])
        if dest in keep_keys:
            continue
        if row["canonical_key"] not in keep_by_src:
            fail(f"manifest source without a kept copy: {row['canonical_key']}")
        if dest in vault:
            vault_delete.append((dest, vault[dest]))
    if manifest_srcs != set(keep_by_src):
        fail("keep table does not cover every manifest source")
    if any(key in keep_keys for key, _ in vault_delete):
        fail("a kept object is on the vault delete list")
    if any(not key.startswith(VAULT_PREFIX) for key, _ in vault_delete):
        fail("vault delete list has a key outside the vault prefix")

    by_sha = {}
    catalog = {}
    for row in read_csv(args.catalog):
        catalog[row["key"]] = (int(row["size"]), row["sha1"])
        if row["key"] in keep_by_src and row["sha1"]:
            by_sha[(row["sha1"], int(row["size"]))] = keep_by_src[row["key"]][0]
    kept_by_name = {}
    for dest in keep_keys:
        kept_by_name.setdefault((os.path.basename(dest), vault[dest]), dest)

    intake_delete, intake_keep = [], []
    reasons = {"catalog key": 0, "sha1+size": 0, "name+size (>=100 MB)": 0}
    for key, size in intake.items():
        if key in keep_by_src and keep_by_src[key][1] == size:
            intake_delete.append((key, size))
            reasons["catalog key"] += 1
            continue
        cat = catalog.get(key)
        if cat and cat[0] == size and cat[1] and (cat[1], size) in by_sha:
            intake_delete.append((key, size))
            reasons["sha1+size"] += 1
            continue
        if size >= BIG:
            src = name_to_src.get((os.path.basename(key), size))
            if (os.path.basename(key), size) in kept_by_name or (src is not None and src in keep_by_src):
                intake_delete.append((key, size))
                reasons["name+size (>=100 MB)"] += 1
                continue
        intake_keep.append((key, size))
    if any(not key.startswith(INTAKE_PREFIX) for key, _ in intake_delete):
        fail("intake delete list has a key outside the intake prefix")

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "vault_delete.list"), "w", encoding="utf-8") as fh:
        fh.writelines(k + "\n" for k, _ in sorted(vault_delete))
    with open(os.path.join(args.outdir, "intake_delete.list"), "w", encoding="utf-8") as fh:
        fh.writelines(k + "\n" for k, _ in sorted(intake_delete))
    with open(os.path.join(args.outdir, "intake_keep.tsv"), "w", encoding="utf-8") as fh:
        fh.writelines(f"{s}\t{k}\n" for k, s in sorted(intake_keep, key=lambda r: -r[1]))

    gb = lambda rows: sum(s for _, s in rows) / 1e9
    print(f"VAULT  delete (duplicate copies): {len(vault_delete):,} objects / {gb(vault_delete):,.1f} GB")
    print(f"VAULT  after: {len(vault) - len(vault_delete):,} objects / {(sum(vault.values()) / 1e9) - gb(vault_delete):,.1f} GB")
    print(f"INTAKE delete (in vault): {len(intake_delete):,} objects / {gb(intake_delete):,.1f} GB  {reasons}")
    print(f"INTAKE stays (not proven in vault): {len(intake_keep):,} objects / {gb(intake_keep):,.2f} GB")
    print("LISTS OK")


if __name__ == "__main__":
    main()
