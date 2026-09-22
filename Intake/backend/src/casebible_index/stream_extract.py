"""Dispatch a source object to a streaming text producer.

> Byline: Claude Code · Opus 5 · 2026-09-22

``extract_stream`` yields text pieces for any supported extension with bounded memory.
Formats that need random access are staged through a disk spool first; the spool is
deleted after the object is processed, and the source object is never modified.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .extractors import extract_text
from .streaming import (
    STREAMABLE_EXTENSIONS,
    WINDOW_BYTES,
    normalize,
    split_json_stream,
    split_xml_records,
    text_windows,
)

SPOOL_EXTENSIONS = frozenset({".pdf", ".docx", ".eml", ".rtf"})
ARCHIVE_EXTENSIONS = frozenset({".zip", ".tar", ".tgz", ".gz", ".7z", ".rar"})


@dataclass
class StreamOutcome:
    status: str = "indexed"
    method: str = "streamed_text"
    media_type: str = "text/plain"
    page_count: int | None = None
    notes: tuple[str, ...] = ()


def media_type_for(extension: str) -> str:
    return {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".eml": "message/rfc822",
        ".html": "text/html",
        ".htm": "text/html",
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".pdf": "application/pdf",
        ".rtf": "application/rtf",
        ".xml": "application/xml",
        ".zip": "application/zip",
    }.get(extension, "text/plain")


async def _spool(windows: AsyncIterator[bytes], suffix: str) -> Path:
    descriptor, name = tempfile.mkstemp(prefix="intake-spool-", suffix=suffix)
    os.close(descriptor)
    path = Path(name)
    handle = await asyncio.to_thread(open, path, "wb")
    try:
        async for window in windows:
            await asyncio.to_thread(handle.write, window)
    finally:
        await asyncio.to_thread(handle.close)
    return path


async def extract_stream(
    key: str,
    windows: AsyncIterator[bytes],
    outcome: StreamOutcome,
    *,
    window_bytes: int = WINDOW_BYTES,
) -> AsyncIterator[str]:
    """Yield normalized text pieces for one object. Peak memory is one window."""
    extension = PurePosixPath(key).suffix.casefold()
    outcome.media_type = media_type_for(extension)

    if extension in ARCHIVE_EXTENSIONS:
        outcome.status = "container"
        outcome.method = "archive_container"
        outcome.notes = ("Archive listed as a container; members are indexed separately.",)
        return

    if extension in SPOOL_EXTENSIONS:
        spool = await _spool(windows, extension)
        try:
            content = await asyncio.to_thread(spool.read_bytes)
            extracted = await asyncio.to_thread(extract_text, Path(key), content)
            outcome.status = extracted.status
            outcome.method = extracted.extraction_method
            outcome.page_count = extracted.page_count
            outcome.notes = extracted.notes
            if extracted.text:
                yield extracted.text
        finally:
            await asyncio.to_thread(spool.unlink, True)
        return

    if extension not in STREAMABLE_EXTENSIONS:
        outcome.status = "unsupported"
        outcome.method = "unsupported"
        outcome.notes = (f"Unsupported text extension: {extension or '<none>'}",)
        return

    if extension == ".xml":
        spool = await _spool(windows, extension)
        try:
            outcome.method = "xml_record_stream"
            produced = False
            handle = await asyncio.to_thread(open, spool, "rb")
            try:
                iterator = split_xml_records(handle)
                while True:
                    block = await asyncio.to_thread(next, iterator, None)
                    if block is None:
                        break
                    produced = True
                    yield normalize(block)
            finally:
                await asyncio.to_thread(handle.close)
            if not produced:
                # Not a record-per-element document: fall back to windowed decoding.
                outcome.method = "xml_text_stream"
                handle = await asyncio.to_thread(open, spool, "rb")
                try:
                    while True:
                        window = await asyncio.to_thread(handle.read, window_bytes)
                        if not window:
                            break
                        piece = normalize(window.decode("utf-8", errors="replace"))
                        if piece:
                            produced = True
                            yield piece
                finally:
                    await asyncio.to_thread(handle.close)
            if not produced:
                outcome.status = "skipped_no_text"
                outcome.notes = ("No usable text was extracted.",)
        finally:
            await asyncio.to_thread(spool.unlink, True)
        return

    produced = False
    if extension in {".json", ".jsonl"}:
        outcome.method = "json_record_stream"
        buffer: list[str] = []

        async def pieces() -> AsyncIterator[str]:
            async for piece in text_windows(windows):
                yield piece

        # The splitter is synchronous; feed it one decoded piece at a time.
        pending: list[str] = []
        async for piece in pieces():
            pending.append(piece)
            for record in split_json_stream(iter(pending)):
                produced = True
                text = normalize(record)
                if text:
                    yield text
            pending = []
        del buffer
    elif extension in {".htm", ".html"}:
        outcome.method = "html_text_stream"
        async for piece in text_windows(windows):
            from bs4 import BeautifulSoup  # local import: only HTML pays for it

            from .streaming import normalize as _normalize

            soup = BeautifulSoup(piece, "html.parser")
            for element in soup(["script", "style", "noscript"]):
                element.decompose()
            text = _normalize(soup.get_text("\n", strip=True))
            if text:
                produced = True
                yield text
    else:
        outcome.method = "decoded_text_stream"
        async for piece in text_windows(windows):
            text = normalize(piece)
            if text:
                produced = True
                yield text

    if not produced:
        outcome.status = "skipped_no_text"
        outcome.notes = ("No usable text was extracted.",)
