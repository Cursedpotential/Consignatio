import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from casebible_index.run_status import RunStatus, latest_run_status
from casebible_index.source_runtime import SourceBusyError, resolve_source_alias, source_lock

ROOT = Path(__file__).resolve().parents[1]


def test_mount_aliases_converge_without_accessing_mounts():
    registry = ROOT / "source-registry.example.json"
    first = resolve_source_alias(Path("V:/raw/small"), "casebible", registry)
    second = resolve_source_alias(Path("Y:/raw/small"), "casebible", registry)
    assert first == second
    assert first[1] == "r2all/raw/small"
    with pytest.raises(ValueError, match="conflicts"):
        resolve_source_alias(Path("Y:/raw"), "other-store", registry)


def test_known_mounts_require_explicit_registry():
    with pytest.raises(ValueError, match="REGISTRY"):
        resolve_source_alias(Path("V:/raw"), "made-up-id", None)
    local = Path("E:/synthetic")
    assert resolve_source_alias(local, "fixture", None) == (local, "fixture")


def test_lock_excludes_another_process_and_releases():
    folder = ROOT / "output" / "synthetic-runtime-tests" / uuid4().hex
    with source_lock(folder, "same-source"):
        with pytest.raises(SourceBusyError), source_lock(folder, "same-source"):
            pytest.fail("Duplicate lock acquired")
        command = (
            "from pathlib import Path\n"
            "from casebible_index.source_runtime import source_lock,SourceBusyError\n"
            "try:\n"
            f" with source_lock(Path({str(folder)!r}), 'same-source'): raise SystemExit(9)\n"
            "except SourceBusyError: print('busy')\n"
        )
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        result = subprocess.run(
            [sys.executable, "-c", command], capture_output=True, text=True,
            timeout=15, check=True, **options,
        )
        assert result.stdout.strip() == "busy"
        with source_lock(folder, "different-source"):
            pass
    with source_lock(folder, "same-source"):
        pass
    assert len(list(folder.glob("*.lock"))) == 2  # Retained, not deleted.


def test_status_is_explicitly_not_coverage():
    folder = ROOT / "output" / "synthetic-runtime-tests" / uuid4().hex
    assert latest_run_status(folder)["state"] == "never_reported"
    progress = RunStatus("fixture", "E:/synthetic")
    progress.files_observed = 9
    progress.files_transformed = 4
    progress.files_without_usable_text = 1
    progress.failure_events = 2
    progress.save(folder, "finished_with_errors")
    report = latest_run_status(folder)
    assert report["coverage"] == "unknown"
    assert report["unchanged_files"] is None
    assert report["files_observed"] == 9
    assert report["failure_events"] == 2
