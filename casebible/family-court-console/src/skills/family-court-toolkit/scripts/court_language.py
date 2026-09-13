#!/usr/bin/env python3
"""Byline: Claude Code · Fable 5.1 · 2026-09-07
CLI twin of the court_language_review MCP tool. Same lexicon
(content/tools/court-language/lexicon.json), same deterministic review logic,
same safe_phrasebank loaded from EXAMPLES.md. Does not rewrite anything --
see `references/court-language/SKILL.md` for the rewrite protocol.

Usage:
  court_language.py review <file|-> --doc affidavit [--json]
  court_language.py phrasebank <doc_type>
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE = <plugin root>/skills/family-court-toolkit/scripts — three levels up to the plugin root.
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
LEXICON_PATH = os.path.join(PLUGIN_ROOT, "content", "tools", "court-language", "lexicon.json")
EXAMPLES_PATH = os.path.join(PLUGIN_ROOT, "skills", "family-court-toolkit", "references", "court-language", "EXAMPLES.md")

SEVERITY_WEIGHT = {"stop": 30, "fix": 10, "soften": 3}
PROFILE_VIOLATION_WEIGHT = 8

ARGUMENT_WORDS = re.compile(r"\b(therefore|thus|accordingly|clearly (?:demonstrates|shows|proves)|proves that|the court should find|it is clear that)\b", re.I)
HISTORY_RECAP = re.compile(r"\b(remember when|you always|in the past|this is exactly why|ever since|for years|every time we|the whole time we were)\b", re.I)
DATE_TOKEN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\b", re.I)
CITATION_TOKEN = re.compile(r"\b(exhibit|ex\.|record|transcript|page \d+|MCR|MCL)\b", re.I)
FACT_STRUCTURE = re.compile(r"\bF\s*:|\bA\s*:|\bC\s*:|\bT\s*:")
FINDING_TOKEN = re.compile(r"\bfinding\b|\bMCR 3\.215", re.I)


def load_lexicon():
    with open(LEXICON_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_phrasebanks():
    with open(EXAMPLES_PATH, encoding="utf-8") as f:
        md = f.read()
    banks = {}
    for section in re.split(r"^## ", md, flags=re.M)[1:]:
        doc_type = section.split("\n", 1)[0].strip()
        m = re.search(r"### Safe phrasebank\s*\n((?:- .*\n?)+)", section)
        if not m:
            continue
        bullets = []
        for line in m.group(1).splitlines():
            line = line.strip()
            if line.startswith("- "):
                text = line[2:].strip()
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                bullets.append(text)
        banks[doc_type] = bullets
    return banks


def find_matches(text, lexicon):
    findings = []
    for entry in lexicon["entries"]:
        try:
            pattern = re.compile(entry["pattern"], re.I)
        except re.error:
            continue
        for m in pattern.finditer(text):
            start, end = m.span()
            pad_start, pad_end = max(0, start - 15), min(len(text), end + 15)
            excerpt = re.sub(r"\s+", " ", text[pad_start:pad_end]).strip()
            if len(excerpt) > 60:
                excerpt = excerpt[:59] + "…"
            findings.append({
                "category": entry["category"],
                "severity": entry["severity"],
                "span": [start, end],
                "excerpt": excerpt,
                "why": entry["why"],
                "suggested_rewrite": entry["rewrite_pattern"],
            })
    findings.sort(key=lambda f: f["span"][0])
    return findings


def count_sentences(text):
    matches = re.findall(r"[^.!?]+[.!?]+", text)
    return len(matches) if matches else (1 if text.strip() else 0)


def split_paragraphs(text):
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def check_profile_violations(text, doc_type):
    violations = []
    if doc_type == "affidavit":
        for para in split_paragraphs(text):
            if count_sentences(para) > 3:
                violations.append(f'Paragraph exceeds ~3 sentences for an affidavit: "{para[:50]}..." -- split into one fact per numbered paragraph.')
        if ARGUMENT_WORDS.search(text):
            violations.append('Affidavit contains argument language (e.g. "therefore", "clearly demonstrates") -- affidavits state facts only.')
    elif doc_type == "motion_brief":
        if DATE_TOKEN.search(text) and not CITATION_TOKEN.search(text):
            violations.append("A dated factual claim appears with no exhibit/record/rule citation nearby.")
    elif doc_type == "testimony_answer":
        if count_sentences(text) > 2:
            violations.append("Answer runs longer than 2 sentences -- a testimony answer should be short and responsive.")
    elif doc_type == "message_to_other_parent":
        if HISTORY_RECAP.search(text):
            violations.append("Message recaps relationship history -- BIFF messages carry no history.")
        if count_sentences(text) > 5:
            violations.append("Message runs longer than ~5 sentences -- BIFF messages should be brief (2-5 sentences).")
    elif doc_type == "incident_log":
        if not FACT_STRUCTURE.search(text):
            violations.append("Entry does not use the FACT structure (Facts / Action / Context / Time).")
    elif doc_type == "objection_to_recommendation":
        if not FINDING_TOKEN.search(text):
            violations.append("No specific finding or MCR 3.215 cite located -- name the specific finding objected to.")
    return violations


def build_rewrite_plan(findings, violations, doc_type, doc_profile):
    plan = [f'Use the {doc_type} template in TEMPLATES.md and the worked examples under "## {doc_type}" in EXAMPLES.md.']
    if doc_profile:
        plan.append(f"Follow the doc-type recipe: {doc_profile['rewrite_recipe']}")
    for f in findings:
        if f["severity"] == "stop":
            plan.append(f'STOP — remove or fully rewrite "{f["excerpt"]}" ({f["category"]}): {f["suggested_rewrite"]}')
    for f in findings:
        if f["severity"] == "fix":
            plan.append(f'Fix "{f["excerpt"]}" ({f["category"]}): {f["suggested_rewrite"]}')
    for f in findings:
        if f["severity"] == "soften":
            plan.append(f'Soften "{f["excerpt"]}" ({f["category"]}): {f["suggested_rewrite"]}')
    for v in violations:
        plan.append(f"Structural fix: {v}")
    plan.append("Never add a fact the source text did not contain.")
    plan.append('Re-run this review on the rewritten text until score >= 90 and stop_flags is empty.')
    return plan


def review(text, doc_type):
    lexicon = load_lexicon()
    findings = find_matches(text, lexicon)
    violations = check_profile_violations(text, doc_type)
    stop_flags = sorted({f["category"] for f in findings if f["severity"] == "stop"})
    score = 100
    for f in findings:
        score -= SEVERITY_WEIGHT[f["severity"]]
    score -= len(violations) * PROFILE_VIOLATION_WEIGHT
    score = max(0, min(100, score))
    doc_profile = lexicon["doc_profiles"].get(doc_type)
    phrasebanks = load_phrasebanks()
    return {
        "doc_type": doc_type,
        "score": score,
        "stop_flags": stop_flags,
        "findings": findings,
        "profile_violations": violations,
        "rewrite_plan": build_rewrite_plan(findings, violations, doc_type, doc_profile),
        "safe_phrasebank": phrasebanks.get(doc_type, [])[:20],
    }


def render_markdown(result):
    lines = [f"# Court-language review — {result['doc_type']}", "",
              f"**Score:** {result['score']}/100" + (f" — STOP flags: {', '.join(result['stop_flags'])}" if result['stop_flags'] else " — no stop flags"), ""]
    lines.append("## Findings")
    if result["findings"]:
        for f in result["findings"]:
            lines.append(f'- [{f["severity"].upper()}] {f["category"]}: "{f["excerpt"]}" — {f["why"]}')
    else:
        lines.append("None.")
    lines.append("")
    if result["profile_violations"]:
        lines.append("## Profile violations")
        for v in result["profile_violations"]:
            lines.append(f"- {v}")
        lines.append("")
    lines.append("## Rewrite plan")
    for step in result["rewrite_plan"]:
        lines.append(f"1. {step}")
    lines.append("")
    lines.append("## Safe phrasebank")
    for phrase in result["safe_phrasebank"]:
        lines.append(f"- {phrase}")
    return "\n".join(lines)


def cmd_review(argv):
    if not argv:
        print("usage: court_language.py review <file|-> --doc <doc_type> [--json]", file=sys.stderr)
        return 1
    path = argv[0]
    doc_type = argv[argv.index("--doc") + 1] if "--doc" in argv else None
    if not doc_type:
        print("missing --doc <doc_type>", file=sys.stderr)
        return 1
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    result = review(text, doc_type)
    if "--json" in argv:
        print(json.dumps(result, indent=2))
    else:
        print(render_markdown(result))
    return 0


def cmd_phrasebank(argv):
    if not argv:
        print("usage: court_language.py phrasebank <doc_type>", file=sys.stderr)
        return 1
    banks = load_phrasebanks()
    doc_type = argv[0]
    for phrase in banks.get(doc_type, []):
        print(f"- {phrase}")
    if doc_type not in banks:
        print(f"unknown doc_type '{doc_type}'. known: {', '.join(sorted(banks))}", file=sys.stderr)
        return 1
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "review":
        return cmd_review(rest)
    if cmd == "phrasebank":
        return cmd_phrasebank(rest)
    print(f"unknown command '{cmd}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
