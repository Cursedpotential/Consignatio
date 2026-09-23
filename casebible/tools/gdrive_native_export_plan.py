#!/usr/bin/env python3
# Byline: Claude Code · Fable 5.1 · 2026-09-14
"""Build export plans for native Google Docs/Sheets/Slides (Office + PDF) with the collision naming rule.

Naming rule (owner rules: every occurrence kept, never overwrite, Drive ID is identity; applied 2026-09-14):
  - unique native path                       -> "<name>.<ext>"          (same folder as the native)
  - same-path collision group, or a native   -> "<name> [gdoc-<id8>].<ext>"
    whose target name clashes with a real
    uploaded file (Drive) or an object on B2
Two passes are emitted per drive because `--drive-export-formats` yields one format per file:
  office pass: docx/xlsx/pptx ; pdf pass: pdf.

Inputs (run dir): <remote>.native-inventory.json (full listing incl. natives, Size == -1), /tmp/b2_<acct>.txt (B2 listing).
Outputs (run dir): native-export-<acct>-office.tsv and -pdf.tsv (driveId<TAB>dest path<TAB>size) usable by
gdrive_copyid_driver.py --dest-is-full, plus native-export-<acct>-idmap.tsv (id, native path, export names, mime).
Read-only; writes plan files only.
"""
import collections
import json
import sys

RUN = "/data/consignatio/migrations/gdrive-copy-20260913"
OFFICE = {"application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
          "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx"}


def main() -> int:
    for acct, remote in (("salemnet", "gd_salemnet"), ("salem85", "gd_salem85")):
        d = json.load(open(f"{RUN}/{remote}.native-inventory.json", encoding="utf-8"))
        natives = [o for o in d if o.get("Size", 0) == -1]
        real = {o["Path"] for o in d if o.get("Size", 0) != -1}
        b2 = {l.rstrip("\n") for l in open(f"/tmp/b2_{acct}.txt", encoding="utf-8")}
        group = collections.Counter(o["Path"] for o in natives)
        office_rows, pdf_rows, idmap, seen = [], [], [], set()
        for o in natives:
            ext = OFFICE.get(o["MimeType"])
            if not ext:
                print(f"skip unknown native mime {o['MimeType']} {o['Path']}", file=sys.stderr)
                continue
            p = o["Path"]
            stem = p[: -len(ext) - 1] if p.lower().endswith("." + ext) else p
            clash = group[p] > 1 or p in real or (stem + ".pdf") in real or p in b2 or (stem + ".pdf") in b2
            base = f"{stem} [gdoc-{o['ID'][:8]}]" if clash else stem
            off, pdf = f"{base}.{ext}", f"{base}.pdf"
            for t in (off, pdf):
                if t in seen or t in real or t in b2:
                    raise SystemExit(f"ABORT: generated name still collides: {t}")
                seen.add(t)
            office_rows.append((o["ID"], off)); pdf_rows.append((o["ID"], pdf))
            idmap.append((o["ID"], p, off, pdf, o["MimeType"], o.get("ModTime", "")))
        for name, rows in (("office", office_rows), ("pdf", pdf_rows)):
            with open(f"{RUN}/native-export-{acct}-{name}.tsv", "w", encoding="utf-8", newline="\n") as fh:
                for fid, dest in rows:
                    fh.write(f"{fid}\t{dest}\t-1\n")
        with open(f"{RUN}/native-export-{acct}-idmap.tsv", "w", encoding="utf-8", newline="\n") as fh:
            for r in idmap:
                fh.write("\t".join(r) + "\n")
        suffixed = sum(1 for r in idmap if "[gdoc-" in r[2])
        print(f"{acct}: natives={len(natives)} office={len(office_rows)} pdf={len(pdf_rows)} id-suffixed={suffixed} plain={len(idmap)-suffixed} all_targets_unique=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
