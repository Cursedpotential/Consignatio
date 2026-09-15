#!/usr/bin/env python3
"""Bake-off parity check vs FINDINGS.md (2026-09-11) reference file A.

File: _18102689630__1___1_.pdf / "+18102689630 (1) (1).pdf"
36,025 bytes, sha256 f18e250e5aca784f..., Stirling-PDF v1.1.1, 24 pages.
Known ground truth (FINDINGS.md): 22 show-ops, 33 glyphs total, all one
distinct byte (0x6E in ZapfDingbats /F4) which decodes to U+25A0 BLACK SQUARE
for correct readers. This script checks OpenDataLoader (fast mode, text +
markdown + json) and pypdf (control) against that ground truth.

Byline: Claude Code · Sonnet 5 · 2026-09-14
"""
import glob
import os
import unicodedata

INPUT = "/work/inputs-bakeoff/+18102689630 (1) (1).pdf"
OUT_DIR = "/work/out-bakeoff"
os.makedirs(OUT_DIR, exist_ok=True)

import opendataloader_pdf

try:
    opendataloader_pdf.convert([INPUT], output_dir=OUT_DIR, format=["text", "markdown", "json"])
    odl_ok = True
except Exception as e:
    odl_ok = False
    print("OpenDataLoader convert() raised:", e)

base = os.path.splitext(os.path.basename(INPUT))[0]
txt_path = os.path.join(OUT_DIR, f"{base}.txt")
md_path = os.path.join(OUT_DIR, f"{base}.md")
json_path = os.path.join(OUT_DIR, f"{base}.json")

print("Output files present:", [p for p in (txt_path, md_path, json_path) if os.path.exists(p)])


def analyze(name, text):
    idx = text.find("Nvm she pooped")
    if idx == -1:
        print(f"[{name}] 'Nvm she pooped' NOT FOUND in output")
        return
    # look at the next up-to-10 chars after the phrase for the glyph
    tail = text[idx:idx + 40]
    print(f"[{name}] context after phrase: {tail!r}")
    after = text[idx + len("Nvm she pooped"):idx + len("Nvm she pooped") + 5]
    for ch in after:
        if ch not in (" ", "\n", "\t"):
            print(f"[{name}] first non-space char after phrase: {ch!r} "
                  f"U+{ord(ch):04X} name={unicodedata.name(ch, '?')}")
            break
    # Count all non-ASCII chars in the whole document text (proxy for the
    # 33 glyphs from the single substituted byte, per FINDINGS.md ground truth)
    non_ascii = [c for c in text if ord(c) > 127]
    black_squares = sum(1 for c in non_ascii if c == "■")
    print(f"[{name}] total non-ASCII chars in doc: {len(non_ascii)}; "
          f"of which U+25A0 (BLACK SQUARE): {black_squares}")
    from collections import Counter
    print(f"[{name}] non-ASCII char histogram: {Counter(non_ascii)}")


if os.path.exists(txt_path):
    with open(txt_path, encoding="utf-8") as f:
        analyze("OpenDataLoader text", f.read())
if os.path.exists(md_path):
    with open(md_path, encoding="utf-8") as f:
        analyze("OpenDataLoader markdown", f.read())

# pypdf control
import pypdf

reader = pypdf.PdfReader(INPUT)
full_text = "\n".join((p.extract_text() or "") for p in reader.pages)
with open(os.path.join(OUT_DIR, f"{base}.pypdf.txt"), "w", encoding="utf-8") as f:
    f.write(full_text)
analyze("pypdf", full_text)

print("\nDONE")
