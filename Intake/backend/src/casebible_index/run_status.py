"""Small immutable run receipts; never interpret counts as corpus completeness."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .parquet_store import write_json_immutable


@dataclass
class RunStatus:
    source_id: str
    source_path: str
    run_id: str = field(default_factory=lambda: uuid4().hex)
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    files_observed: int = 0
    files_transformed: int = 0
    files_without_usable_text: int = 0
    failure_events: int = 0

    def save(self, output: Path, state: str) -> Path:
        now = datetime.now(UTC)
        payload = {
            **asdict(self), "state": state, "reported_at": now.isoformat(),
            "coverage": "unknown", "unchanged_files": None,
            "notes": "Supported-file scope only; transformations are not confirmed target writes",
        }
        path = output / "run-status" / (
            now.strftime("%Y%m%dT%H%M%S.%fZ") + "-" + self.run_id + ".json"
        )
        write_json_immutable(path, payload)
        return path


def latest_run_status(output: Path) -> dict:
    files = sorted((output / "run-status").glob("*.json"), reverse=True)
    if not files:
        return {"state": "never_reported", "coverage": "unknown"}
    selected = files[0]
    if selected.stat().st_size > 65536:
        raise ValueError("Run status exceeds size limit")
    return json.loads(selected.read_text(encoding="utf-8"))
