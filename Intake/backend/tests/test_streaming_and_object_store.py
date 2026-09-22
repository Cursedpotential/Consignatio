"""Streaming extraction and bucket reads. Byline: Claude Code · Opus 5 · 2026-09-22."""

import httpx
import pytest

from casebible_index.object_store import ObjectStore, ReadCounters, StoreCredentials
from casebible_index.stream_extract import StreamOutcome, extract_stream
from casebible_index.streaming import split_json_stream, split_xml_records

CREDENTIALS = StoreCredentials(
    access_key_id="0045fakekeyid0000000007",
    secret_access_key="fake-secret-value",
    endpoint_url="https://s3.us-west-004.example.com",
    region="us-west-004",
)


async def _windows(*chunks: bytes):
    for chunk in chunks:
        yield chunk


@pytest.mark.asyncio
async def test_plain_text_streams_in_pieces_without_a_size_cap():
    outcome = StreamOutcome()
    payload = ("line of evidence text\n" * 200_000).encode()
    assert len(payload) > 4 * 1024 * 1024  # larger than the deleted 8 MiB-era window
    pieces = [
        piece async for piece in extract_stream(
            "vault/big.txt", _windows(payload[:2_000_000], payload[2_000_000:]), outcome
        )
    ]
    assert outcome.status == "indexed"
    assert sum(len(piece) for piece in pieces) > 4_000_000
    assert len(pieces) > 1  # yielded in windows, not as one document


@pytest.mark.asyncio
async def test_archive_is_a_container_row_not_a_failure():
    outcome = StreamOutcome()
    stream = extract_stream("vault/Takeout.zip", _windows(b"PK\x03\x04"), outcome)
    assert [piece async for piece in stream] == []
    assert outcome.status == "container"


def test_json_array_splits_into_records():
    records = list(split_json_stream(iter(['[{"a": 1}, {"b": ', '2}]'])))
    assert len(records) == 2
    assert '"a"' in records[0] and '"b"' in records[1]


def test_sms_backup_xml_yields_one_block_per_record():
    import io

    document = (
        b'<?xml version="1.0"?><smses count="2">'
        b'<sms address="555" body="first message" date="1"/>'
        b'<sms address="556" body="second message" date="2"/>'
        b"</smses>"
    )
    blocks = list(split_xml_records(io.BytesIO(document)))
    assert len(blocks) == 2
    assert "first message" in blocks[0]
    assert "second message" in blocks[1]


@pytest.mark.asyncio
async def test_ranged_read_signs_and_counts_without_leaking_the_secret():
    seen = {}

    def serve(request):
        seen["auth"] = request.headers["authorization"]
        seen["range"] = request.headers.get("range")
        return httpx.Response(206, content=b"0123456789")

    counters = ReadCounters()
    async with httpx.AsyncClient(transport=httpx.MockTransport(serve)) as client:
        store = ObjectStore(CREDENTIALS, "salem-data", client, counters=counters)
        payload = await store.read_range("consignatio/vault/v1/a b.txt", 0, 10)
    assert payload == b"0123456789"
    assert seen["range"] == "bytes=0-9"
    assert seen["auth"].startswith("AWS4-HMAC-SHA256 Credential=")
    assert CREDENTIALS.secret_access_key not in seen["auth"]
    assert counters.snapshot() == {
        "b2_requests": 1, "b2_bytes_read": 10, "b2_objects_touched": 1
    }


@pytest.mark.asyncio
async def test_stream_yields_bounded_windows_and_counts_bytes():
    body = b"x" * 3_000_000

    def serve(request):
        return httpx.Response(200, content=body)

    counters = ReadCounters()
    async with httpx.AsyncClient(transport=httpx.MockTransport(serve)) as client:
        store = ObjectStore(CREDENTIALS, "salem-data", client, counters=counters)
        sizes = [len(window) async for window in store.stream("k.txt", window_bytes=1_000_000)]
    assert max(sizes) <= 1_000_000
    assert sum(sizes) == len(body)
    assert counters.bytes_read == len(body)


def test_a_moved_vault_object_keeps_its_identity():
    """Owner 2026-09-22 10:48: sorting and indexing happen at once, so a move must not
    drop and re-index the object. Only vault_key changes."""
    from casebible_index.catalog_source import CatalogObject
    from casebible_index.parquet_store import vault_document_id, vault_version_id
    from casebible_index.vault_source import VaultFile

    sha1 = "9d2e042d6a4f0d4909cdf47ac848c8636e298810"
    before = VaultFile(CatalogObject(key="consignatio/vault/v1/inbox/a.txt", byte_size=12,
                                     sha1=sha1))
    after = VaultFile(CatalogObject(key="consignatio/vault/v1/sorted/2019/a.txt",
                                    byte_size=12, sha1=sha1))
    assert before.identity == after.identity
    ids = [vault_document_id("vault", f.identity) for f in (before, after)]
    assert ids[0] == ids[1]
    versions = [
        vault_version_id(i, f.identity, embed_model="m", summary_model="s")
        for i, f in zip(ids, (before, after), strict=True)
    ]
    assert versions[0] == versions[1]
    # A different object is still a different document.
    other = VaultFile(CatalogObject(key="consignatio/vault/v1/inbox/a.txt", byte_size=13,
                                    sha1="0" * 40))
    assert vault_document_id("vault", other.identity) != ids[0]


def test_an_unsplittable_record_is_wrapped_not_refused():
    """A minified JSON record has no separator; the splitter returns it whole and the
    embedding provider rejects it with a 400. Streaming everything means cutting it."""
    from casebible_index.pipeline import ChunkAccumulator

    accumulator = ChunkAccumulator(chunk_size=2400, chunk_overlap=300)
    blob = "x" * 341_373  # the real worst case in the vault's 61 MB conversations.json
    chunks = accumulator.feed(blob) + accumulator.finish()
    assert chunks, "an unsplittable record must still produce chunks"
    assert max(len(chunk.text) for chunk in chunks) <= 2400
    assert sum(len(chunk.text) for chunk in chunks) >= len(blob)
    assert [chunk.ordinal for chunk in chunks] == list(range(len(chunks)))
