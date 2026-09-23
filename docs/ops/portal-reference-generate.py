#!/usr/bin/env python3
"""
Portal reference generator — scrapes gethomepage/homepage docs at a given git
tag and emits a local, offline options reference (Markdown + JSON Schemas +
VS Code snippets) for the Propria portal editor.

Byline: Claude Code · Sonnet 5 · 2026-09-15
Owner ask (2026-09-15 01:21 EDT, via coordinator): "show me the individual
options" — not a framed docs site. This script is the rerunnable generator;
rerun it after any Homepage image upgrade with --tag matching the new
release (resolve the running tag first, e.g.
`docker exec homepage cat /app/package.json | grep version`, then look up
`vX.Y.Z` in https://github.com/gethomepage/homepage/tags).

Usage:
    python3 portal-reference-generate.py --tag v1.13.2 --out OUTDIR

Output layout under OUTDIR:
    VERSION.txt
    reference/index.md
    reference/settings-keys.md
    reference/services-fields.md
    reference/bookmarks-fields.md
    reference/info-widgets.md
    reference/service-widgets.md
    schemas/settings.schema.json
    schemas/services.schema.json
    schemas/bookmarks.schema.json
    schemas/widgets.schema.json
    snippets/homepage.code-snippets

This is a documentation-generation tool, not a strict YAML validator: the
emitted JSON Schemas are intentionally loose (additionalProperties: true)
so they drive autocomplete + hover text without rejecting valid configs
this script's heuristics didn't anticipate.
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

RAW_BASE = "https://raw.githubusercontent.com/gethomepage/homepage/{tag}/{path}"
API_TREE = "https://api.github.com/repos/gethomepage/homepage/git/trees/{tag}?recursive=1"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "portal-reference-generate/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def fetch_doc(tag: str, path: str) -> str:
    return fetch(RAW_BASE.format(tag=tag, path=path))


def list_docs(tag: str, prefix: str) -> list:
    data = json.loads(fetch(API_TREE.format(tag=tag)))
    return sorted(
        t["path"] for t in data["tree"]
        if t["path"].startswith(prefix) and t["path"].endswith(".md")
        and not t["path"].endswith("/index.md")
    )


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
    return fm


YAML_BLOCK_RE = re.compile(r"```ya?ml\n(.*?)```", re.S)
LINE_RE = re.compile(r"^(?P<indent>\s*)(?:- )?(?P<key>[A-Za-z][A-Za-z0-9_]*):\s*(?P<val>[^#\n]*?)\s*(?:#\s*(?P<comment>.*))?$")
ALLOWED_RE = re.compile(r"[Aa]llowed (?:values|options)[:\s]*`?\[?([^`\]\n]+)\]?`?")
DEFAULT_RE = re.compile(r"defaults? (?:is|to)\s+`?([^`,.\n]+)`?")


def extract_fields_from_yaml(block: str) -> list:
    """Extract {key, example, description, default, allowed} for each
    'key: value # comment' line in a fenced yaml block. Best-effort;
    designed for gethomepage's consistently-commented widget examples."""
    fields = []
    seen = set()
    for raw_line in block.splitlines():
        m = LINE_RE.match(raw_line)
        if not m:
            continue
        key = m.group("key")
        val = (m.group("val") or "").strip()
        comment = (m.group("comment") or "").strip()
        if key in ("http", "https"):  # skip URL fragments misparsed as keys
            continue
        dedupe_key = (key, comment)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        allowed = None
        am = ALLOWED_RE.search(comment)
        if am:
            allowed = [a.strip(" `\"'") for a in re.split(r",| or ", am.group(1)) if a.strip(" `\"'")]
        default = None
        dm = DEFAULT_RE.search(comment)
        if dm:
            default = dm.group(1).strip(" `\"'")
        fields.append({
            "key": key,
            "example": val,
            "description": comment,
            "default": default,
            "allowed": allowed,
            "line": raw_line.strip(),
        })
    return fields


HEADING_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.M)


def split_sections(text: str) -> list:
    """Split a doc (after frontmatter) into (level, title, body) sections by
    ## / ### headings."""
    body = FRONTMATTER_RE.sub("", text, count=1)
    matches = list(HEADING_RE.finditer(body))
    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((len(m.group(1)), m.group(2).strip(), body[start:end]))
    return sections


def first_paragraph(body: str) -> str:
    for para in body.strip().split("\n\n"):
        para = para.strip()
        if para and not para.startswith("```") and not para.startswith("!!!") and not para.startswith("<img"):
            return " ".join(para.split())
    return ""


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def gen_config_reference(tag: str, doc_path: str, out_md: Path, title: str) -> dict:
    """Heading-based extraction for services.md / settings.md / bookmarks.md.
    Returns {property_name: {description, example, default, allowed}} scanned
    from every yaml block's top-level keys, cross-referenced to whichever
    section heading contains it (for description context)."""
    text = fetch_doc(tag, doc_path)
    sections = split_sections(text)
    lines = [f"# {title}", "", f"_Source: `{doc_path}` @ `{tag}`. Generated by portal-reference-generate.py — do not hand-edit._", ""]
    schema_props = {}
    for level, heading, body in sections:
        desc = first_paragraph(body)
        blocks = YAML_BLOCK_RE.findall(body)
        anchor = slugify(heading)
        lines.append(f"{'#' * (level + 1)} {heading} {{#{anchor}}}")
        lines.append("")
        if desc:
            lines.append(desc)
            lines.append("")
        for block in blocks:
            fields = extract_fields_from_yaml(block)
            top_level_fields = [f for f in fields if not block.splitlines()[0].startswith(" ")]  # heuristic marker unused
            for f in fields:
                key = f["key"]
                if key not in schema_props:
                    schema_props[key] = {
                        "description": f["description"] or desc or heading,
                        "example": f["example"],
                        "default": f["default"],
                        "allowed": f["allowed"],
                        "heading": heading,
                    }
            lines.append("```yaml")
            lines.append(block.rstrip("\n"))
            lines.append("```")
            lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return schema_props


def gen_widget_docs(tag: str, doc_paths: list, category_title: str, out_md: Path) -> dict:
    """Per-file extraction for docs/widgets/{info,services}/*.md — one
    heading per widget type, one sub-entry per field. Returns
    {widget_type: {description, fields: [...]}}"""
    lines = [f"# {category_title}", "", f"_Source: `docs/widgets/*` @ `{tag}`. Generated by portal-reference-generate.py — do not hand-edit._", ""]
    widgets = {}
    for path in doc_paths:
        wtype = Path(path).stem
        try:
            text = fetch_doc(tag, path)
        except Exception as e:
            print(f"  ! failed {path}: {e}", file=sys.stderr)
            continue
        fm = parse_frontmatter(text)
        wtitle = fm.get("title", wtype)
        wdesc = fm.get("description", "")
        blocks = YAML_BLOCK_RE.findall(text)
        # prefer the block that contains "type: <wtype>" (service widgets) or
        # the first block (info widgets, no "type:" line)
        primary = None
        for b in blocks:
            if re.search(rf"type:\s*{re.escape(wtype)}\b", b):
                primary = b
                break
        if primary is None and blocks:
            primary = blocks[0]
        fields = [f for f in (extract_fields_from_yaml(primary) if primary else []) if f["key"] != "widget"]
        widgets[wtype] = {"title": wtitle, "description": wdesc, "fields": fields, "doc": path}

        anchor = slugify(wtype)
        lines.append(f"## {wtitle} (`{wtype}`) {{#{anchor}}}")
        lines.append("")
        if wdesc:
            lines.append(wdesc)
            lines.append("")
        lines.append(f"Source doc: `{path}`")
        lines.append("")
        if primary:
            lines.append("Full example:")
            lines.append("```yaml")
            lines.append(primary.rstrip("\n"))
            lines.append("```")
            lines.append("")
        if fields:
            lines.append("Individual options:")
            lines.append("")
            for f in fields:
                bits = [f"- **`{f['key']}`**"]
                if f["example"]:
                    bits.append(f"— example: `{f['example']}`")
                if f["default"]:
                    bits.append(f"— default: `{f['default']}`")
                if f["allowed"]:
                    bits.append(f"— allowed: {', '.join('`' + a + '`' for a in f['allowed'])}")
                lines.append(" ".join(bits))
                if f["description"]:
                    lines.append(f"  - {f['description']}")
            lines.append("")
        lines.append("---")
        lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return widgets


def build_schema(title: str, description: str, props: dict) -> dict:
    schema_props = {}
    for key, info in props.items():
        p = {"description": info.get("description") or ""}
        if info.get("allowed"):
            p["enum"] = info["allowed"]
        if info.get("default") is not None:
            p["default"] = info["default"]
        schema_props[key] = p
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": title,
        "description": description,
        "type": "object",
        "additionalProperties": True,
        "properties": schema_props,
    }


def build_widget_type_schema(widgets: dict, title: str) -> dict:
    type_enum = []
    one_of = []
    for wtype, info in sorted(widgets.items()):
        type_enum.append(wtype)
        props = {"type": {"const": wtype}}
        for f in info["fields"]:
            p = {"description": f["description"] or ""}
            if f["allowed"]:
                p["enum"] = f["allowed"]
            if f["default"] is not None:
                p["default"] = f["default"]
            props[f["key"]] = p
        one_of.append({
            "properties": props,
            "required": ["type"],
        })
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": title,
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "type": {"enum": type_enum, "description": "Widget type — see the bottom-panel reference for its fields."}
        },
        "anyOf": one_of if one_of else [{}],
    }


def build_snippets(widgets: dict, prefix: str) -> dict:
    out = {}
    for wtype, info in sorted(widgets.items()):
        body_lines = ["widget:", f"  type: {wtype}"]
        for f in info["fields"][:12]:
            example = f["example"] or ""
            body_lines.append(f"  {f['key']}: {example}" if example else f"  {f['key']}: ")
        out[f"{prefix}: {wtype}"] = {
            "prefix": wtype,
            "body": body_lines,
            "description": info.get("description") or info.get("title") or wtype,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="gethomepage/homepage git tag, e.g. v1.13.2")
    ap.add_argument("--out", required=True, help="output directory (e.g. a workspace's .portal-reference)")
    args = ap.parse_args()

    out = Path(args.out)
    (out / "reference").mkdir(parents=True, exist_ok=True)
    (out / "schemas").mkdir(parents=True, exist_ok=True)
    (out / "snippets").mkdir(parents=True, exist_ok=True)

    print(f"Generating portal reference for gethomepage {args.tag} -> {out}")

    settings_props = gen_config_reference(args.tag, "docs/configs/settings.md", out / "reference" / "settings-keys.md", "settings.yaml keys")
    services_props = gen_config_reference(args.tag, "docs/configs/services.md", out / "reference" / "services-fields.md", "services.yaml service entry fields")
    bookmarks_props = gen_config_reference(args.tag, "docs/configs/bookmarks.md", out / "reference" / "bookmarks-fields.md", "bookmarks.yaml fields")

    info_paths = list_docs(args.tag, "docs/widgets/info/")
    service_paths = list_docs(args.tag, "docs/widgets/services/")
    print(f"  {len(info_paths)} info widgets, {len(service_paths)} service widgets")
    info_widgets = gen_widget_docs(args.tag, info_paths, "Info (top-bar) widgets", out / "reference" / "info-widgets.md")
    service_widgets = gen_widget_docs(args.tag, service_paths, "Service widgets", out / "reference" / "service-widgets.md")

    # Homepage API notes (customapi + documented endpoints) — folded into info reference index
    api_notes = (
        "# Homepage API notes\n\n"
        f"_Source: `docs/widgets/services/customapi.md`, `docs/widgets/authoring/api.md` @ `{args.tag}`._\n\n"
        "## customapi widget\n\nSee `service-widgets.md#customapi` for the full field-by-field breakdown "
        "(`mappings`, `format`, `display`, `remap`, `scale`, `prefix`, `suffix`, `headers`, `requestBody`).\n\n"
        "## Documented HTTP endpoints\n\n"
        "Homepage does not publish a general-purpose public REST API beyond what the frontend calls "
        "internally (`/api/services`, `/api/widgets`, `/api/hash`, `/api/socket`) — these are undocumented "
        "internal Next.js API routes used by the SPA itself, not a stable public contract. Treat them as "
        "read-only and subject to change between releases; the customapi widget is the supported way to "
        "surface a third-party API's data.\n"
    )
    (out / "reference" / "homepage-api-notes.md").write_text(api_notes, encoding="utf-8")

    # Index with outline links
    index_lines = [
        "# Portal options reference — index",
        "",
        f"Generated for gethomepage/homepage `{args.tag}` on {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z.",
        "Rerun with `python3 portal-reference-generate.py --tag <vX.Y.Z> --out <dir>` after any image upgrade.",
        "",
        "## Categories",
        "",
        "- [Services fields](services-fields.md) — every `services.yaml` service-entry key",
        "- [Settings keys](settings-keys.md) — every `settings.yaml` key",
        "- [Bookmarks fields](bookmarks-fields.md) — every `bookmarks.yaml` key",
        f"- [Info widgets](info-widgets.md) — {len(info_widgets)} top-bar widget types",
        f"- [Service widgets](service-widgets.md) — {len(service_widgets)} service widget types",
        "- [Homepage API notes](homepage-api-notes.md) — customapi + internal endpoints",
        "",
        "Open this file's Outline view (bottom of the Explorer, or `Ctrl+Shift+O`) to jump by heading.",
        "",
    ]
    (out / "reference" / "index.md").write_text("\n".join(index_lines), encoding="utf-8")

    # Schemas
    (out / "schemas" / "settings.schema.json").write_text(
        json.dumps(build_schema("Homepage settings.yaml", "Application-level Homepage settings", settings_props), indent=2), encoding="utf-8")
    (out / "schemas" / "bookmarks.schema.json").write_text(
        json.dumps(build_schema("Homepage bookmarks.yaml", "Bookmark entry fields", bookmarks_props), indent=2), encoding="utf-8")
    services_schema = build_schema("Homepage services.yaml (entry fields)", "Service entry fields; widget.type drives the widget-specific schema", services_props)
    services_schema["properties"]["widget"] = {"description": "Service widget config — see widgets.schema.json for per-type fields", "$ref": "./widgets.schema.json"}
    (out / "schemas" / "services.schema.json").write_text(json.dumps(services_schema, indent=2), encoding="utf-8")
    (out / "schemas" / "widgets.schema.json").write_text(
        json.dumps(build_widget_type_schema({**info_widgets, **service_widgets}, "Homepage widget (info + service)"), indent=2), encoding="utf-8")

    # Snippets
    snippets = {}
    snippets.update(build_snippets(info_widgets, "homepage-info-widget"))
    snippets.update(build_snippets(service_widgets, "homepage-service-widget"))
    (out / "snippets" / "homepage.code-snippets").write_text(json.dumps(snippets, indent=2), encoding="utf-8")

    (out / "VERSION.txt").write_text(
        f"gethomepage/homepage {args.tag}\ngenerated {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z by portal-reference-generate.py\n",
        encoding="utf-8")

    print("Done.")


if __name__ == "__main__":
    main()
