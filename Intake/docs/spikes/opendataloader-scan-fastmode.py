#!/usr/bin/env python3
"""Fast-mode baseline on an image-only scanned PDF (no OCR expected).
Byline: Claude Code · Sonnet 5 · 2026-09-14
"""
import glob
import os
import opendataloader_pdf

INPUT_DIR = "/work/inputs-scan"
OUT_DIR = "/work/out-scan"
os.makedirs(OUT_DIR, exist_ok=True)

pdfs = sorted(glob.glob(os.path.join(INPUT_DIR, "**", "*.pdf"), recursive=True))
print("Files:", pdfs)

try:
    opendataloader_pdf.convert(pdfs, output_dir=OUT_DIR, format=["json", "markdown"])
except Exception as e:
    print("convert() raised:", e)

for p in pdfs:
    base = os.path.splitext(os.path.basename(p))[0]
    md = os.path.join(OUT_DIR, f"{base}.md")
    if os.path.exists(md):
        with open(md, encoding="utf-8") as f:
            content = f.read()
        print(f"\n=== {base}.md ({len(content)} chars) ===")
        print(content[:1000])
    else:
        print(f"\n=== {base}: no markdown produced ===")
