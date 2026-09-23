# Byline: Claude Code · Opus 5 · 2026-09-16 07:18 EDT (session propria-79)
"""Steps 3 and 5 of the owner's 2026-09-16 order (07:11–07:13):
  "First, clean the intake. Then clean the vault. Then what's not in the vault … still lives in intake — move it.
   Then clean the intake again. Then verify that there's one copy in the vault."

plan    : fresh intake + vault listings (after steps 1–2) → move manifest for every object still in intake.
          dest = consignatio/vault/v1/<path inside its source root> (casebible-* strips 1 segment, gdrive/local/onedrive
          strip 2). Same name already in the vault with the same size → nothing to copy (already there).
          Same name with a different size → " [<source>]" before the extension (nothing is overwritten).
moved   : after the copy, list intake keys whose vault dest is present with equal size → delete list.
onecopy : vault listing WITH the sha1 B2 already stores (no download, no rehash) → counts objects sharing sha1+size;
          objects without a stored sha1 (multipart uploads) are checked by file name + size.
"""
import argparse
import collections
import csv
import json
import os
import sys

VAULT_PREFIX = "consignatio/vault/v1/"
INTAKE_PREFIX = "consignatio/intake/raw-dedupe/v1/source-buckets/"


def load(path, prefix):
    with open(path, encoding="utf-8") as fh:
        return {prefix + i["Path"]: i for i in json.load(fh)}


def dest_for(key):
    rel = key[len(INTAKE_PREFIX):]
    parts = rel.split("/")
    strip = 1 if parts[0].startswith("casebible-") else 2
    return parts[:strip], "/".join(parts[strip:])


def tagged(path, tag):
    head, name = os.path.split(path)
    stem, ext = os.path.splitext(name)
    return os.path.join(head, f"{stem} [{tag}]{ext}").replace("\\", "/")


def cmd_plan(a):
    intake = load(a.intake, INTAKE_PREFIX)
    vault = load(a.vault, VAULT_PREFIX)
    rows, present, renamed = [], 0, 0
    taken = {k: int(v["Size"]) for k, v in vault.items()}
    for key, item in sorted(intake.items()):
        size = int(item["Size"])
        root, rel = dest_for(key)
        dest = VAULT_PREFIX + rel
        if taken.get(dest) == size:
            present += 1
            continue
        if dest in taken:
            dest = VAULT_PREFIX + tagged(rel, "-".join(root))
            n = 2
            while dest in taken:
                dest = VAULT_PREFIX + tagged(rel, f"{'-'.join(root)}-{n}")
                n += 1
            renamed += 1
        taken[dest] = size
        rows.append({"canonical_key": key, "dest_key": dest, "size": size})
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["canonical_key", "dest_key", "size"])
        w.writeheader()
        w.writerows(rows)
    print(f"intake objects left: {len(intake):,} / {sum(int(i['Size']) for i in intake.values()) / 1e9:,.2f} GB")
    print(f"already in vault at the same path and size: {present:,}")
    print(f"to copy into the vault: {len(rows):,} / {sum(r['size'] for r in rows) / 1e9:,.2f} GB (tagged to avoid a name clash: {renamed:,})")


def cmd_moved(a):
    intake = load(a.intake, INTAKE_PREFIX)
    vault = load(a.vault, VAULT_PREFIX)
    planned = {}
    with open(a.manifest, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            planned[r["canonical_key"]] = r["dest_key"]
    delete, stay = [], []
    for key, item in intake.items():
        size = int(item["Size"])
        root, rel = dest_for(key)
        dest = planned.get(key, VAULT_PREFIX + rel)
        v = vault.get(dest)
        (delete if v is not None and int(v["Size"]) == size else stay).append(key)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.writelines(k + "\n" for k in sorted(delete))
    print(f"intake objects confirmed in the vault (name + size): {len(delete):,}; NOT confirmed (stay): {len(stay):,}")
    for k in stay[:20]:
        print("  STAYS", k)


def cmd_onecopy(a):
    with open(a.vault, encoding="utf-8") as fh:
        items = json.load(fh)
    by_hash = collections.defaultdict(list)
    by_name = collections.defaultdict(list)
    no_hash = 0
    for i in items:
        sha1 = (i.get("Hashes") or {}).get("sha1", "")
        if sha1 and sha1 != "none":
            by_hash[(sha1, int(i["Size"]))].append(i["Path"])
        else:
            no_hash += 1
            by_name[(os.path.basename(i["Path"]), int(i["Size"]))].append(i["Path"])
    dup_hash = {k: v for k, v in by_hash.items() if len(v) > 1 and k[1] > 0}
    dup_name = {k: v for k, v in by_name.items() if len(v) > 1 and k[1] > 0}
    extra = sum(len(v) - 1 for v in dup_hash.values()) + sum(len(v) - 1 for v in dup_name.values())
    extra_gb = (sum((len(v) - 1) * k[1] for k, v in dup_hash.items()) + sum((len(v) - 1) * k[1] for k, v in dup_name.items())) / 1e9
    total = sum(int(i["Size"]) for i in items) / 1e9
    print(f"vault: {len(items):,} objects / {total:,.1f} GB · with stored sha1 {len(items) - no_hash:,} · without {no_hash:,}")
    print(f"extra copies (same sha1+size): {sum(len(v) - 1 for v in dup_hash.values()):,}")
    print(f"extra copies (no sha1, same name+size): {sum(len(v) - 1 for v in dup_name.values()):,}")
    print(f"ONE-COPY {'PASS' if extra == 0 else 'FAIL'}: extra copies {extra:,} / {extra_gb:,.2f} GB")
    for k, v in list(dup_hash.items())[:10]:
        print("  DUP", k[1], v[:3])
    return 0 if extra == 0 else 2


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--intake", required=True); p.add_argument("--vault", required=True); p.add_argument("--out", required=True)
    m = sub.add_parser("moved"); m.add_argument("--intake", required=True); m.add_argument("--vault", required=True); m.add_argument("--manifest", required=True); m.add_argument("--out", required=True)
    o = sub.add_parser("onecopy"); o.add_argument("--vault", required=True)
    a = ap.parse_args()
    sys.exit({"plan": cmd_plan, "moved": cmd_moved, "onecopy": cmd_onecopy}[a.cmd](a) or 0)


if __name__ == "__main__":
    main()
