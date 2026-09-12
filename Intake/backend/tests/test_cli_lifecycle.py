from contextlib import contextmanager
from types import SimpleNamespace

import cocoindex as coco
import pytest

from casebible_index import cli, run_status


@pytest.mark.parametrize("failed", [False, True])
def test_index_closes_runtime_before_snapshot(monkeypatch, tmp_path, failed):
    import sys

    events = []

    @contextmanager
    def runtime():
        events.append("enter")
        yield
        events.append("close")

    monkeypatch.setattr(coco, "runtime", runtime)
    monkeypatch.setitem(
        sys.modules,
        "casebible_index.pipeline",
        SimpleNamespace(app=SimpleNamespace(update_blocking=lambda **kw: events.append("update"))),
    )
    settings = SimpleNamespace(
        output_dir=tmp_path,
        source_dir=tmp_path,
        source_id="synthetic",
        embed_model="test",
        summary_model="test",
        embed_dimensions=2,
    )
    monkeypatch.setattr(cli, "_settings", lambda *a: settings)

    def status(_):
        assert events == ["enter", "update", "close"]
        return {
            "state": "finished_with_errors" if failed else "finished",
            "failure_events": int(failed),
        }

    monkeypatch.setattr(run_status, "latest_run_status", status)
    monkeypatch.setattr(
        cli, "build_active_snapshot", lambda _: events.append("snapshot") or tmp_path / "snapshot"
    )
    monkeypatch.setattr(cli, "write_json_immutable", lambda *a: events.append("receipt"))
    if failed:
        with pytest.raises(RuntimeError, match="did not finish cleanly"):
            cli.index()
        assert "snapshot" not in events and "receipt" not in events
    else:
        cli.index()
        assert events == ["enter", "update", "close", "snapshot", "receipt"]
