#!/usr/bin/env python3
"""Byline: Claude Code · Fable 5.1 · 2026-09-07
CLI twin of the survival_guide MCP tool. Reads the same JSON knowledge base
(content/tools/survival-guide/events/*.json) and mechanically fills the
template with the fields the context pack actually carries — no LLM step, so
the opening-statement and question-type sections (which need live model
authorship from case facts) are left as pointers back to the MCP tool + the
`survival-guide` skill member, not fabricated.

Usage:
  survival_guide.py list
  survival_guide.py <event> [--card] [--out file.md]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE = <plugin root>/skills/family-court-toolkit/scripts — three levels up to the plugin root.
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EVENTS_DIR = os.path.join(PLUGIN_ROOT, "content", "tools", "survival-guide", "events")

RELEASE_WARNING = (
    "Legal information, not legal advice. No attorney-client relationship is created. This CLI "
    "output is a mechanical fill of the context pack, not a model-authored guide -- for the full "
    "guide (opening statements, question-and-answer registers, case-facts merge) use the "
    "survival_guide MCP tool with a calling model, per the `survival-guide` skill member. If you or "
    "a child are in immediate danger, call 911. National Domestic Violence Hotline: 1-800-799-7233."
)


def load_events():
    events = {}
    for name in sorted(os.listdir(EVENTS_DIR)):
        if name.endswith(".json"):
            with open(os.path.join(EVENTS_DIR, name), encoding="utf-8") as f:
                data = json.load(f)
            events[data["id"]] = data
    return events


def cmd_list(events):
    for eid, data in events.items():
        print(f"{eid:<38} {data['title']}")


def bullets(items, prefix="- "):
    return "\n".join(f"{prefix}{item}" for item in items) if items else "(none in context pack)"


def deadlines_table(deadlines):
    lines = ["| Label | Rule preset | Cite | Status |", "|---|---|---|---|"]
    for d in deadlines:
        lines.append(f"| {d['label']} | {d.get('rule_preset') or '-'} | {d['cite']} | {d['status']} |")
    return "\n".join(lines)


def traps_table(traps):
    lines = ["| Trap | Safe move |", "|---|---|"]
    for t in traps:
        lines.append(f"| {t['trap']} | {t['safe_move']} |")
    return "\n".join(lines)


def render_full(data):
    who = data.get("who_is_in_the_room") or data.get("who_reads_it") or []
    return f"""{RELEASE_WARNING}

# {data['title']}

## 1. What This Is
{data['what_it_is']}

## 2. Who Is In The Room / Who Reads This
{bullets(who)}

## 3. Sequence
{bullets(data['sequence'])}

## 4. Prepare / Bring
{bullets(data['prepare'])}

## 5. Opening Statement / Framing Options
[Not filled by the CLI -- this section needs live model authorship from case_facts. Use the
`survival_guide` MCP tool with a calling model, and see `references/referee-hearing-survival/SKILL.md`
for the four-register pattern (minimal / contextual / soft emotional note / boundary-setting).]

## 6. Question Types & Safe Answers
[Not filled by the CLI -- same reason as section 5. See
`references/referee-hearing-survival/SKILL.md` S2 for the minimal/clarifying/contextual/boundary
register.]

## 7. Trap Questions & Safe Moves
{traps_table(data['traps'])}

## 8. Do Not List
{bullets(data['do_not'])}

## 9. Court-Safe Phrases
Openers:
{bullets(data['phrases']['openers'])}

Closers:
{bullets(data['phrases']['closers'])}

## 10. Deadlines
{deadlines_table(data['deadlines'])}
(Every date here is PROVISIONAL -- run it through `calculate_planning_date` with the matching
`rule_preset` before relying on it.)

## 11. Exit Checklist
{bullets(data['exit_checklist'])}

## 12. Stop and Seek Counsel
{bullets(data['safety_gates'])}

## 13. Sources
{bullets([f"{s['file']} -- {s['section']}" for s in data['sources']])}
"""


def render_card(data):
    trap_lines = "\n".join(f"- {t['trap']} -> {t['safe_move']}" for t in data["traps"][:3])
    return f"""{RELEASE_WARNING}

# {data['title']} -- Hearing Day Card

**Bring:**
{bullets(data['prepare'])}

**Three asks:** 1. ___ 2. ___ 3. ___ (fill from your own motion/objection; the CLI cannot invent these)

**Trap questions (top 3):**
{trap_lines}

**Do not:**
{bullets(data['do_not'])}

**Deadlines:**
{deadlines_table(data['deadlines'])}

**If you freeze:** pause, ask to repeat the question, look at your one-page chronology, say "I need a
moment to find the date."

**Stop conditions:**
{bullets(data['safety_gates'])}
"""


def main(argv):
    events = load_events()
    if not argv or argv[0] == "list":
        cmd_list(events)
        return 0
    event = argv[0]
    if event not in events:
        print(f"Unknown event '{event}'. Run 'survival_guide.py list' for valid ids.", file=sys.stderr)
        return 1
    card = "--card" in argv
    out_path = None
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    data = events[event]
    text = render_card(data) if card else render_full(data)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {out_path}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
