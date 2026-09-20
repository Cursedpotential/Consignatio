#!/usr/bin/env python3
"""vault_twins_groups_load.py
Flatten the parent session's normalized-name candidate-groups JSON
(docs/receipts/2026-09-16-vault-twins-candidates.json) into a TSV suitable
for `COPY raw_duck.vault_twins_groups FROM STDIN`.

Columns: group_key, unit_group, member_path, member_depth, member_files, member_gb, member_units_json

Byline: Claude Code . Sonnet 5 . 2026-09-16
"""
import json
import sys


def esc(s):
    if s is None:
        return ""
    return str(s).replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "docs/receipts/2026-09-16-vault-twins-candidates.json"
    with open(src, "r", encoding="utf-8") as f:
        groups = json.load(f)

    n_groups = 0
    n_members = 0
    for g in groups:
        n_groups += 1
        key = g["key"]
        unit_group = "t" if g.get("unit_group") else "f"
        for m in g.get("members", []):
            n_members += 1
            path = m["path"]
            depth = path.count("/") + 1
            files = m.get("files", 0)
            gb = m.get("gb", 0.0)
            units = json.dumps(m.get("units", []))
            print("\t".join([
                esc(key), unit_group, esc(path), str(depth), str(files), str(gb), esc(units)
            ]))
    print(f"# groups={n_groups} members={n_members}", file=sys.stderr)


if __name__ == "__main__":
    main()
