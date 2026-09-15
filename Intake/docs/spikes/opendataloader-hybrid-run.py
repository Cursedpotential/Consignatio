#!/usr/bin/env python3
"""Hybrid docling-fast (mode=full, tesseract OCR) on the image-only scanned PDF.
Byline: Claude Code · Sonnet 5 · 2026-09-14
"""
import time
import opendataloader_pdf

SCAN_PDF = "/work/inputs-scan/CaseManagement/filings/Scan 10 Jul 23 · 15·15·37.pdf"
OUT_DIR = "/work/out-hybrid"

t0 = time.time()
try:
    opendataloader_pdf.convert(
        [SCAN_PDF],
        output_dir=OUT_DIR,
        format=["json", "markdown"],
        hybrid="docling-fast",
        hybrid_mode="full",
        hybrid_url="http://127.0.0.1:5002",
    )
    ok = True
except Exception as e:
    ok = False
    print("convert() raised:", e)
elapsed = time.time() - t0
print(f"elapsed={elapsed:.2f}s ok={ok}")

if ok:
    import os
    md_path = os.path.join(OUT_DIR, "Scan 10 Jul 23 · 15·15·37.md")
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    print(f"\n=== hybrid OCR markdown ({len(content)} chars) ===")
    print(content[:2000])
