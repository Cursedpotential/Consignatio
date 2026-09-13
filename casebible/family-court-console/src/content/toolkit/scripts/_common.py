"""Shared helpers. Read-only inputs, standard library only."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
LIMITATIONS = [
 "Read-only by default: never alters originals or user accounts/devices.",
 "No credentials, login bypass, account access, or network writes are used.",
 "Outputs are informational and require human review; they are not legal advice.",
]
def banner(tool, extra=()):
    lines=[f'=== {tool}: LIMITATIONS ===']+LIMITATIONS+list(extra)
    return '\n'.join(lines)
def sha256_bytes(data): return hashlib.sha256(data).hexdigest()
def write_json(path, data):
    if path:
        p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n',encoding='utf-8')
def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
