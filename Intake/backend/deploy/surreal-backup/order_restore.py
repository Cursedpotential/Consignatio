#!/usr/bin/env python3
"""Reorder recognized Surreal exports without changing statement bytes or schema."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


def statements(text: str) -> tuple[list[str], str]:
    result, start, i = [], 0, 0
    quote = None
    stack = []
    while i < len(text):
        char = text[i]
        if quote:
            if char == "\\":
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if text.startswith(("--", "//"), i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0 or "/*" in text[i + 2 : end]:
                raise ValueError("Unsupported or unclosed block comment")
            i = end + 2
            continue
        if char in "'\"`":
            quote = char
        elif char == "⟨":
            quote = "⟩"
        elif char in "([{":
            stack.append(char)
        elif char in ")]}":
            if not stack or {")": "(", "]": "[", "}": "{"}[char] != stack.pop():
                raise ValueError("Unbalanced export delimiters")
        elif char == ";" and not stack:
            result.append(text[start : i + 1])
            start = i + 1
        i += 1
    if quote or stack:
        raise ValueError("Unclosed export statement")
    return result, text[start:]


def split_prefix(statement: str) -> tuple[str, str]:
    offset = 0
    while True:
        match = re.match(
            r"\s+|--[^\n]*(?:\n|$)|//[^\n]*(?:\n|$)|/\*.*?\*/", statement[offset:], re.S
        )
        if not match:
            return statement[:offset], statement[offset:]
        offset += match.end()


def reorder(raw: bytes) -> tuple[bytes, dict]:
    text = raw.decode("utf-8")
    chunks, tail = statements(text)
    if split_prefix(tail)[1]:
        raise ValueError("Unterminated export statement")
    schema, data = [], {}
    kinds, dependencies = {}, {}
    imports = 0
    for chunk in chunks:
        prefix, body = split_prefix(chunk)
        if re.fullmatch(r"OPTION IMPORT\s*;", body):
            imports += 1
            schema.append(chunk)
        elif body.startswith("DEFINE "):
            if not re.match(
                r"DEFINE (?:USER|ACCESS|TABLE|FIELD|INDEX|EVENT|PARAM|FUNCTION|"
                r"ANALYZER|API|CONFIG|BUCKET|MODULE)\b",
                body,
            ):
                raise ValueError("Unrecognized schema definition")
            table = re.match(
                r"DEFINE TABLE(?: OVERWRITE| IF NOT EXISTS)? (\w+)\s+"
                r"TYPE (NORMAL|RELATION)\b",
                body,
            )
            if body.startswith("DEFINE TABLE") and not table:
                raise ValueError("Unsupported table declaration")
            if table:
                name, kind = table.groups()
                if name in kinds:
                    raise ValueError("Duplicate table definition")
                kinds[name] = kind
                dependencies.setdefault(name, set())
                data.setdefault(name, [])
                if kind == "RELATION":
                    ends = re.search(
                        r"\bIN ([\w| ]+?) OUT ([\w| ]+?) "
                        r"(?:ENFORCED |SCHEMAFULL|SCHEMALESS)",
                        body,
                    )
                    if not ends:
                        raise ValueError("Unsupported relation endpoint declaration")
                    dependencies[name].update(re.findall(r"\w+", "|".join(ends.groups())))
            field = re.match(
                r"DEFINE FIELD.*? ON(?: TABLE)? (\w+) TYPE (?:option<)?record<([^>]+)>", body
            )
            if field:
                dependencies.setdefault(field[1], set()).update(re.findall(r"\w+", field[2]))
            schema.append(chunk)
        elif re.match(r"INSERT(?: RELATION)?\s+\[", body):
            headers = re.findall(r"^-- TABLE DATA: (\w+)\s*$", prefix, re.M)
            if not headers or headers[-1] not in kinds:
                raise ValueError("Data has no recognized table header")
            data[headers[-1]].append(chunk)
        else:
            raise ValueError("Unrecognized export statement; refusing heuristic rewrite")
    if imports != 1 or not kinds:
        raise ValueError("Expected one OPTION IMPORT and explicit tables")
    for name, deps in dependencies.items():
        deps.discard(name)  # Self-reference is resolved within that table's INSERT batch.
        if deps - kinds.keys():
            raise ValueError("Export refers to undefined table dependencies")
        if kinds[name] == "RELATION":
            deps.update(table for table, kind in kinds.items() if kind == "NORMAL")
    order, pending = [], set(kinds)
    while pending:
        ready = sorted(name for name in pending if not (dependencies[name] & pending))
        if not ready:
            raise ValueError("Cyclic table dependencies require a separately reviewed restore")
        order.extend(ready)
        pending.difference_update(ready)
    ordered = schema + [chunk for table in order for chunk in data[table]]
    # Multiset equality proves no statement was lost or duplicated by reordering.
    if sorted(ordered) != sorted(chunks):
        raise ValueError("Statement preservation check failed")
    result = ("".join(ordered) + tail).encode("utf-8")
    return result, {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "derived_sha256": hashlib.sha256(result).hexdigest(),
        "statements": len(chunks),
        "tables": len(kinds),
        "data_order": order,
    }


def main() -> None:
    source, target = map(Path, sys.argv[1:])
    if source.resolve() == target.resolve():
        raise ValueError("Derived restore must have a distinct path")
    original = source.read_bytes()
    derived, receipt = reorder(original)
    if source.read_bytes() != original:
        raise ValueError("Source export changed during analysis")
    with target.open("xb") as output:
        output.write(derived)
    with target.with_suffix(".receipt.json").open("x", encoding="utf-8") as output:
        json.dump(receipt, output, indent=2)
    print(json.dumps(receipt))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Do not render an exception that might contain an export statement or secret.
        print(
            f"Dependency ordering failed ({type(exc).__name__}); source retained", file=sys.stderr
        )
        raise SystemExit(1) from None
