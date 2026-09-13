from __future__ import annotations

import json

from test_legacy_catalog import make_manifest
from typer.testing import CliRunner

from casebible_index.cli import app
from casebible_index.projections import runtime


def test_catalog_validation_never_connects(monkeypatch, tmp_path):
    async def forbidden():
        raise AssertionError("Validation must not connect")

    monkeypatch.setattr(runtime, "connect_graph", forbidden)
    result = CliRunner().invoke(app, ["graph-project-catalog", str(make_manifest(tmp_path))])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "validated"


def test_catalog_apply_sanitizes_connection_failure(monkeypatch, tmp_path):
    async def fail():
        raise RuntimeError("secret-that-must-not-appear")

    monkeypatch.setattr(runtime, "connect_graph", fail)
    result = CliRunner().invoke(
        app, ["graph-project-catalog", str(make_manifest(tmp_path)), "--apply"]
    )
    assert result.exit_code == 1
    assert "secret-that-must-not-appear" not in result.output


def test_invalid_catalog_exits_nonzero(tmp_path):
    result = CliRunner().invoke(app, ["graph-project-catalog", str(tmp_path / "absent.json")])
    assert result.exit_code == 1
