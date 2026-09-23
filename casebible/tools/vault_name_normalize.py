#!/usr/bin/env python3
"""Byline: Claude Code · Fable 5.1 · 2026-09-16

Directory-name normalizer for the vault/v1 twin-structure reconciliation.
Written from the real names in vault_dirnames_depth4.txt (269 depth-1,
2,546 depth-2, 6,146 depth-3, 11,855 depth-4 dirs), not from guesses.

Read-only. Input: the `vault_dirnames_depth.py` listing. Output: candidate
groups of directories whose normalized path is identical, with the raw
names, depth, files, bytes, and a UNIT flag when the group is made of atomic
export units (Takeout / Facebook / Meta / Snapchat / .obsidian) that must be
linked, never merged.

usage: vault_name_normalize.py <depth listing.txt> [--json out.json]
"""
import re, sys, json, collections

# ---- 1. provenance / dedupe tags added by our own tools -------------------
RE_SOURCE_TAG = re.compile(r"\s*\[(?:gdrive|local|r2|onedrive|md5|sha1)-[^\]]+\]\s*$", re.I)
RE_HASH_TAG   = re.compile(r"\s*\[[0-9a-f]{8}\]\s*$", re.I)

# ---- 2. copy / numbering suffixes -----------------------------------------
RE_COPY = re.compile(
    r"(?:\s*[-_ ]\s*copy(?:\s*\(?\d+\)?)?|\s*\(copy(?:\s*\d+)?\)|\s*\(\d+\)|\s+-\s+\d+|\s+\d{1,2})$",
    re.I)
RE_GLUED_DIGIT = re.compile(r"(?<=[A-Za-z_])\d$")          # Evidence1, AI_Chats1, Takeout Data1
RE_DUP_WORD    = re.compile(r"[_ -]*(?:DUPLICATES?|dedup\d*|_DUPLICATE)$", re.I)
RE_TBD         = re.compile(r"^_?(?:TO_BE_DELETED|REVIEW_HOLD|SWEPT|sync-conflicts)\d*$", re.I)

# ---- 3. dates / timestamps / export ids ------------------------------------
RE_TAKEOUT_ROOT = re.compile(r"^takeout-(\d{8}T\d{6}Z)-(\d{3})$", re.I)
RE_FB_ROOT      = re.compile(r"^facebook-([a-z0-9]+)-(\d{4}-\d{2}-\d{2})(?:-([A-Za-z0-9]{8}))?", re.I)
RE_META_ROOT    = re.compile(r"^meta-(\d{4}-[A-Za-z]{3}-\d{2}-\d{2}-\d{2}-\d{2})$", re.I)
RE_SNAP_ROOT    = re.compile(r"^Snap[_ ]?Export[_ ]?(\d{4}-\d{2}-\d{2})?$", re.I)
RE_DRIVE_DL     = re.compile(r"^drive-download-\d{8}T\d{6}Z-\d+-\d{3}(?:\s*-\s*\d+)?$", re.I)
RE_MYDATA       = re.compile(r"^mydata~\d{13}", re.I)
RE_STAMP        = re.compile(r"\d{8}T\d{6}Z")
RE_DATE         = re.compile(r"\b(?:20\d{2}[-_. ]?\d{2}[-_. ]?\d{2}|\d{2}-\d{2}-\d{2}|20\d{2}-[A-Za-z]{3}-\d{2})\b")
RE_YEAR_ONLY    = re.compile(r"^(?:19|20)\d{2}$")           # Google Photos/2018 — keep as is
RE_RECUP        = re.compile(r"^recup_dir\.\d+$", re.I)     # PhotoRec carve dirs — keep as is
RE_TAKEOUT_N    = re.compile(r"^Takeout(?:\s*[-_ ]?\s*(\d{1,2}|\(copy\s*\d*\)|\(\d+\)))?$", re.I)

# ---- 4. word-level synonyms (applied after suffix stripping) ---------------
SYNONYMS = [
    (re.compile(r"^(?:case ?bible|casebible|case bible backups?|case bible backup .*|casebible-sorted|d/casebible)$", re.I), "case bible"),
    (re.compile(r"^(?:evidence ?vault|evidence|evidence_data|evidence_&_timelines|evidence_analysis|evidence1)$", re.I), "evidence"),
    (re.compile(r"^(?:court|court_papers|court papers|court_active|court filings|court_filings|court & legal project|court and legal project)$", re.I), "court"),
    (re.compile(r"^(?:archives?|\d+_archive|backups?|_backup_import|recovered|recovered files|\.recovered|_recovery(?:_\d+)?)$", re.I), "archive"),
    (re.compile(r"^(?:google ?takeout(?: files)?|google-takeout|takeout data|takeout)$", re.I), "takeout"),
    (re.compile(r"^(?:google photos|photos|pictures|images|photo_recovery|imported photos|dcim)$", re.I), "photos"),
    (re.compile(r"^(?:legal_knowledge_base_obsidian|legal knowledge base obsidian|legal_reference|legal_research|legal)$", re.I), "legal kb"),
    (re.compile(r"^(?:fb|facebook|facebook data|fb exports|fb data|social backup|meta)$", re.I), "facebook"),
    (re.compile(r"^(?:snap|snap data|snapchat|snap export)$", re.I), "snapchat"),
    (re.compile(r"^(?:documents|docs|\.docs|_documents_misc)$", re.I), "documents"),
    (re.compile(r"^(?:downloads?|downloaded apps)$", re.I), "downloads"),
    (re.compile(r"^(?:new folder(?: with items)?|untitled folder|new folder with items)$", re.I), "new folder"),
    (re.compile(r"^(?:ai_chats|raw ai chats|chats|ai convos)$", re.I), "ai chats"),
    (re.compile(r"^(?:onedrive|no sync)$", re.I), "onedrive"),
]

def unit_key(name):
    """Return (unit_type, unit_id) if the directory name IS an atomic export unit root."""
    m = RE_TAKEOUT_ROOT.match(name)
    if m: return ("takeout-export", f"{m.group(1)}-{m.group(2)}")
    m = RE_FB_ROOT.match(name)
    if m: return ("facebook-export", f"{m.group(1)}-{m.group(2)}-{m.group(3) or '?'}")
    m = RE_META_ROOT.match(name)
    if m: return ("meta-export", m.group(1))
    m = RE_SNAP_ROOT.match(name)
    if m: return ("snapchat-export", m.group(1) or "?")
    if name.lower() == ".obsidian": return ("obsidian-vault", "")
    if RE_TAKEOUT_N.match(name) and name.lower() != "takeout": return ("takeout-sibling", name.lower())
    if RE_MYDATA.match(name): return ("google-mydata", name.split()[0])
    return None

def normalize_component(name):
    raw = name
    if RE_YEAR_ONLY.match(name) or RE_RECUP.match(name):
        return name.lower(), None
    unit = unit_key(name)
    n = RE_SOURCE_TAG.sub("", name)
    n = RE_HASH_TAG.sub("", n)
    if unit:
        return f"<{unit[0]}>", unit
    n = RE_DUP_WORD.sub("", n)
    if RE_TBD.match(n):
        return "<hold>", None
    n = RE_DRIVE_DL.sub("drive-download", n)
    n = RE_STAMP.sub("", n)
    n = RE_DATE.sub("", n)
    n = re.sub(r"\b(?:backup|bkp|copy|old|new|final|latest)\b", "", n, flags=re.I)
    for _ in range(2):
        n = RE_COPY.sub("", n)
        n = RE_GLUED_DIGIT.sub("", n)
    n = re.sub(r"[\s_\-\.]+", " ", n).strip().lower()
    n = n.strip(" -_()[]")
    for rx, canon in SYNONYMS:
        if rx.match(n):
            n = canon; break
    return n or raw.lower(), None

def normalize_path(path):
    comps, units = [], []
    for c in path.split("/"):
        k, u = normalize_component(c)
        comps.append(k)
        if u: units.append((c, u))
    return "/".join(comps), units

def parse_listing(fn):
    rows = []
    for line in open(fn, encoding="utf-8", errors="replace"):
        m = re.match(r"^\s*([\d.]+) GB\s+(\d+) files\s+(.*)$", line.rstrip("\n"))
        if m: rows.append((m.group(3), int(m.group(2)), float(m.group(1))))
    return rows

def main():
    fn = sys.argv[1]
    rows = parse_listing(fn)
    groups = collections.defaultdict(list)
    for path, files, gb in rows:
        norm, units = normalize_path(path)
        groups[norm].append({"path": path, "files": files, "gb": gb, "units": [u[1][0] for u in units]})
    cands = {k: v for k, v in groups.items() if len(v) > 1}
    out = []
    for k, members in sorted(cands.items(), key=lambda kv: -sum(m["gb"] for m in kv[1])):
        is_unit = any(m["units"] for m in members)
        out.append({"key": k, "unit_group": is_unit, "n": len(members),
                    "gb": round(sum(m["gb"] for m in members), 2),
                    "files": sum(m["files"] for m in members), "members": members})
    print(f"dirs {len(rows)}  normalized keys {len(groups)}  candidate groups {len(out)} "
          f"(unit groups {sum(1 for g in out if g['unit_group'])})")
    for g in out[:80]:
        tag = "UNIT" if g["unit_group"] else "    "
        print(f"\n{tag} {g['gb']:9.2f} GB {g['files']:8d} files  n={g['n']}  key={g['key']}")
        for m in sorted(g["members"], key=lambda m: -m["gb"])[:8]:
            print(f"        {m['gb']:8.2f} GB {m['files']:7d}  {m['path']}")
    if "--json" in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w", encoding="utf-8"), indent=1)

if __name__ == "__main__":
    main()
