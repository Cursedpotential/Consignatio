import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import cocoindex as coco
import httpx
import pytest
from cocoindex.connectors import localfs
from cocoindex.resources.file import FileMetadata

from casebible_index.filesystem_search import WeaviateSearchConfig
from casebible_index.pipeline import BoundedLocalFile, read_bounded
from casebible_index.weaviate_target import (
    WEAVIATE_WRITER,
    ObjectAction,
    ObjectHandler,
    ObjectSpec,
    WeaviateObjectWriter,
    declare_chunk,
)

SPEC = ObjectSpec({"text": "synthetic"}, {"text_nim": [1.0, 0.0, 0.0]})
KEY = ("https://search.example", "IntakeTestChunks", str(uuid4()))


def test_target_reconciliation_and_uncertain_retry():
    handler = ObjectHandler()
    first = handler.reconcile(KEY, SPEC, [], True)
    assert first is not None
    assert handler.reconcile(KEY, SPEC, [first.tracking_record], False) is None
    assert handler.reconcile(KEY, SPEC, [first.tracking_record], True) is not None
    assert handler.reconcile(KEY, SPEC, ["old-fingerprint"], False) is not None
    retirement = handler.reconcile(KEY, coco.NON_EXISTENCE, [first.tracking_record], False)
    assert retirement.action.spec is None
    assert coco.is_non_existence(retirement.tracking_record)
    assert handler.reconcile(KEY, coco.NON_EXISTENCE, [], False) is None


@pytest.mark.asyncio
async def test_upsert_replay_and_retirement_never_delete():
    objects = {}
    methods = []

    def serve(request):
        methods.append(request.method)
        if request.method == "GET":
            return httpx.Response(200, json=objects[KEY[2]]) if objects else httpx.Response(404)
        payload = json.loads(request.content)
        if request.method in {"POST", "PUT"}:
            objects[KEY[2]] = payload
        elif request.method == "PATCH":
            objects[KEY[2]]["properties"].update(payload["properties"])
        else:
            raise AssertionError("Unexpected destructive method")
        return httpx.Response(200, json=payload)

    config = WeaviateSearchConfig(KEY[0], KEY[1], "text_nim", 3)
    async with httpx.AsyncClient(transport=httpx.MockTransport(serve)) as client:
        writer = WeaviateObjectWriter(config, client)
        await writer.apply(ObjectAction(KEY, SPEC))
        await writer.apply(ObjectAction(KEY, SPEC))
        assert len(objects) == 1
        assert objects[KEY[2]]["properties"]["active"] is True
        await writer.apply(ObjectAction(KEY, None))
        assert objects[KEY[2]]["properties"]["active"] is False
        assert objects[KEY[2]]["properties"]["text"] == "synthetic"
        await writer.apply(ObjectAction(KEY, SPEC))
        assert objects[KEY[2]]["properties"]["active"] is True
    assert "DELETE" not in methods


@pytest.mark.asyncio
async def test_failed_write_propagates_for_coco_retry():
    config = WeaviateSearchConfig(KEY[0], KEY[1], "text_nim", 3)
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda _: httpx.Response(503, text="sensitive provider body")
    )) as client:
        with pytest.raises(RuntimeError, match="retryable") as exc:
            await WeaviateObjectWriter(config, client).apply(ObjectAction(KEY, SPEC))
        assert "sensitive" not in str(exc.value)


class FakeFile:
    def __init__(self, size, content):
        self.reported = size
        self.content = content
        self.read_sizes = []

    async def size(self):
        return self.reported

    async def read(self, size):
        self.read_sizes.append(size)
        return self.content[:size]


@pytest.mark.asyncio
async def test_size_limit_checks_before_read_and_caps_growth():
    oversized = FakeFile(1000, b"unexpected")
    with pytest.raises(ValueError, match="exceeds"):
        await read_bounded(oversized, 10)
    assert oversized.read_sizes == []
    growing = FakeFile(2, b"x" * 1000)
    with pytest.raises(ValueError, match="grew"):
        await read_bounded(growing, 10)
    assert growing.read_sizes == [11]
    exact = FakeFile(10, b"x" * 10)
    assert await read_bounded(exact, 10) == b"x" * 10


@pytest.mark.asyncio
async def test_coco_fingerprint_is_bounded_before_processor_runs(monkeypatch):
    reads = []

    async def unexpected_read(self, size=-1):
        reads.append(size)
        return b"x" * size

    monkeypatch.setattr(localfs.File, "_read_impl", unexpected_read)
    file = BoundedLocalFile(localfs.FilePath(path=Path("E:/synthetic-not-read")), 10)
    file._metadata = FileMetadata(size=1000, modified_time=datetime(2026, 1, 1))
    with pytest.raises(ValueError, match="before fingerprint"):
        await file.content_fingerprint()
    assert reads == []


@coco.fn
async def _synthetic_target_main(rows: list[ObjectSpec]) -> None:
    for row in rows:
        declare_chunk(KEY[0], KEY[1], KEY[2], row)


@pytest.mark.asyncio
async def test_real_coco_runtime_applies_then_retires_target():
    """Real v1 engine; only remote transport mocked. State retained on E:, no deletion."""
    folder = Path(__file__).resolve().parents[1] / "output" / "synthetic-target-tests" / uuid4().hex
    folder.mkdir(parents=True)
    actions = []

    class Recorder:
        async def apply(self, action):
            actions.append(action)

    context = coco.ContextProvider()
    context.provide(WEAVIATE_WRITER, Recorder())
    environment = coco.Environment(
        coco.Settings(db_path=folder / "state", lmdb_map_size=16 * 1024 * 1024),
        context_provider=context, name="test_" + uuid4().hex,
    )
    rows = [SPEC]
    app = coco.App(
        coco.AppConfig(name="SyntheticTarget", environment=environment, max_inflight_components=2),
        _synthetic_target_main, rows=rows,
    )
    await app.update()
    assert len(actions) == 1 and actions[0].spec == SPEC
    await app.update()
    assert len(actions) == 1
    rows.clear()
    await app.update(full_reprocess=True)
    assert len(actions) == 2 and actions[-1].spec is None
