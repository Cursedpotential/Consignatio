#!/usr/bin/env python3
"""Lexical member lookup for this plugin. Usage: route.py "<query>" [--limit N]. Prints member, score, path, summary."""
import os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); refs = os.path.dirname(os.path.dirname(here))  # members are sibling skills (restored 2026-09-07)
entry_self = os.path.basename(os.path.dirname(here))
args = [a for a in sys.argv[1:] if not a.startswith('--')]; limit = 5
if '--limit' in sys.argv: limit = int(sys.argv[sys.argv.index('--limit') + 1])
q = set(re.findall(r'[a-z0-9]+', ' '.join(args).lower()))
out = []
for m in sorted(os.listdir(refs)):
    if m == entry_self: continue
    p = os.path.join(refs, m, 'SKILL.md')
    if not os.path.exists(p): continue
    s = open(p, encoding='utf-8', errors='replace').read()
    fm = s.split('---', 2)[1] if s.startswith('---') else s[:1500]
    desc = re.search(r'description:\s*(.*)', fm); desc = desc.group(1).strip().strip('"\'') if desc else ''
    words = set(re.findall(r'[a-z0-9]+', (m + ' ' + desc + ' ' + s[:4000]).lower()))
    name_hits = sum(3 for t in q if t in m.lower())
    score = name_hits + len(q & words)
    if score: out.append((score, m, p, desc[:160]))
for score, m, p, d in sorted(out, reverse=True)[:limit]:
    print(f"{score:>3}  {m:<40} {p}\n     {d}")
if not out: print("no member matched; read SKILL.md member table")
