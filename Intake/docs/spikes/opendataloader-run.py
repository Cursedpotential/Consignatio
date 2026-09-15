#!/usr/bin/env python3
"""Bounded live spike runner: OpenDataLoader PDF fast mode vs pypdf.
Runs INSIDE the opendataloader-spike container on ovh-files, against
read-only mounted inputs. Writes outputs under /work/out.
Byline: Claude Code · Sonnet 5 · 2026-09-14
"""
import json
import os
import time
import glob
import subprocess  # noqa: F401 (used for CalledProcessError below)

INPUT_DIR = "/work/inputs"
OUT_DIR = "/work/out"
os.makedirs(OUT_DIR, exist_ok=True)

pdfs = sorted(glob.glob(os.path.join(INPUT_DIR, "**", "*.pdf"), recursive=True))
print(f"Found {len(pdfs)} PDFs:")
for p in pdfs:
    print(" -", p, os.path.getsize(p), "bytes")

import opendataloader_pdf

t0 = time.time()
convert_error = None
try:
    opendataloader_pdf.convert(
        pdfs,
        output_dir=OUT_DIR,
        format=["json", "markdown"],
    )
except subprocess.CalledProcessError as e:
    convert_error = str(e)
    print(f"\nWARNING: convert() raised (batch had bad-input file(s)): {e}")
elapsed = time.time() - t0
print(f"\nFast-mode conversion of {len(pdfs)} files took {elapsed:.2f}s total, "
      f"{elapsed/len(pdfs):.2f}s/file average (convert_error={convert_error is not None})")
print("Output dir listing:", os.listdir(OUT_DIR))

# Per-file stats
summary = []
for p in pdfs:
    base = os.path.splitext(os.path.basename(p))[0]
    json_path_candidates = glob.glob(os.path.join(OUT_DIR, f"{base}*.json"))
    md_path_candidates = glob.glob(os.path.join(OUT_DIR, f"{base}*.md")) + \
        glob.glob(os.path.join(OUT_DIR, f"{base}*.markdown"))
    json_bytes = os.path.getsize(json_path_candidates[0]) if json_path_candidates else None
    md_bytes = os.path.getsize(md_path_candidates[0]) if md_path_candidates else None
    n_elements = None
    n_tables = None
    pages = None
    sample_element = None
    if json_path_candidates:
        try:
            with open(json_path_candidates[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            # Structure introspection - print top-level keys once
            if not summary:
                print("\nTop-level JSON keys for first file:", list(data.keys()))
            def walk(node, acc):
                if isinstance(node, dict):
                    acc.append(node)
                    for v in node.values():
                        walk(v, acc)
                elif isinstance(node, list):
                    for v in node:
                        walk(v, acc)
            all_nodes = []
            walk(data, all_nodes)
            n_elements = sum(1 for n in all_nodes if "type" in n or "category" in n)
            n_tables = sum(1 for n in all_nodes if str(n.get("type", n.get("category", ""))).lower() == "table")
            pages = data.get("pages") or data.get("page_count")
            if pages is None and isinstance(data.get("pages"), list):
                pages = len(data["pages"])
            for n in all_nodes:
                if str(n.get("type", n.get("category", ""))).lower() == "table":
                    sample_element = n
                    break
            if sample_element is None and all_nodes:
                sample_element = all_nodes[0]
        except Exception as e:
            print(f"  JSON parse error for {base}: {e}")
    summary.append({
        "file": os.path.basename(p),
        "size_bytes": os.path.getsize(p),
        "json_bytes": json_bytes,
        "md_bytes": md_bytes,
        "n_elements": n_elements,
        "n_tables": n_tables,
        "pages": pages,
    })
    if sample_element:
        with open(os.path.join(OUT_DIR, f"{base}.sample_element.json"), "w", encoding="utf-8") as f:
            json.dump(sample_element, f, indent=2, default=str)

with open(os.path.join(OUT_DIR, "_summary.json"), "w", encoding="utf-8") as f:
    json.dump({"elapsed_total_s": elapsed, "files": summary}, f, indent=2, default=str)

print("\n=== SUMMARY ===")
for s in summary:
    print(s)

# pypdf comparison for two files
import pypdf

compare_files = [p for p in pdfs if "rule-3204" in p or "FAQ2013-01" in p][:2]
if len(compare_files) < 2:
    compare_files = pdfs[:2]

for p in compare_files:
    base = os.path.splitext(os.path.basename(p))[0]
    try:
        reader = pypdf.PdfReader(p)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        out_txt = os.path.join(OUT_DIR, f"{base}.pypdf.txt")
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\npypdf extracted {len(text)} chars from {base} ({len(reader.pages)} pages) -> {out_txt}")
    except Exception as e:
        print(f"\npypdf FAILED on {base}: {e}")

# Control: also try pypdf on the corrupted KnowledgeBase files that OpenDataLoader rejected
print("\n=== pypdf control on OpenDataLoader-rejected files ===")
for p in pdfs:
    base = os.path.basename(p)
    if base not in {s["file"] for s in summary if s["json_bytes"]}:
        try:
            reader = pypdf.PdfReader(p)
            print(f"  {base}: pypdf opened OK, {len(reader.pages)} pages (unexpected - ODL rejected it)")
        except Exception as e:
            print(f"  {base}: pypdf ALSO FAILED: {type(e).__name__}: {e}")

print("\nDONE")
