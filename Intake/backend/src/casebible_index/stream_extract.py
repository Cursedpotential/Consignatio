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


async def _disk_windows(path: Path, window_bytes: int) -> AsyncIterator[bytes]:
    handle = await asyncio.to_thread(open, path, "rb")
    try:
        while True:
            window = await asyncio.to_thread(handle.read, window_bytes)
            if not window:
                break
            yield window
    finally:
        await asyncio.to_thread(handle.close)


async def extract_stream(
    key: str,
    windows: AsyncIterator[bytes],
    outcome: StreamOutcome,
    *,
    window_bytes: int = WINDOW_BYTES,
) -> AsyncIterator[str]:
    """Yield normalized text pieces for one object. Peak memory is one window.

    Every object is spooled to disk first and then read back in windows. Reading straight
    from the bucket response looked leaner, but it holds one HTTP response open for as long
    as the consumer takes — and the consumer embeds every chunk, which for a 61 MB chat
    export is minutes. The connection died mid-object and lost the whole file. The spool
    makes the network read short and contiguous; memory is still one window, and the spool
    is removed as soon as the object is done. Byline: Claude Code · Opus 5 · 2026-09-22.
    """
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
            xml_notes: list[str] = []
            handle = await asyncio.to_thread(open, spool, "rb")
            try:
                iterator = split_xml_records(handle, xml_notes)
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
            outcome.notes = outcome.notes + tuple(xml_notes)
            if not produced:
                outcome.status = "skipped_no_text"
                outcome.notes = outcome.notes + ("No usable text was extracted.",)
        finally:
            await asyncio.to_thread(spool.unlink, True)
        return

    produced = False
    spool = await _spool(windows, extension)
    try:
        if extension in {".json", ".jsonl"}:
            outcome.method = "json_record_stream"
            pending: list[str] = []
            async for piece in text_windows(_disk_windows(spool, window_bytes)):
                pending.append(piece)
                for record in split_json_stream(iter(pending)):
                    text = normalize(record)
                    if text:
                        produced = True
                        yield text
                pending = []
        elif extension in {".htm", ".html"}:
            outcome.method = "html_text_stream"
            from bs4 import BeautifulSoup  # local import: only HTML pays for it

            async for piece in text_windows(_disk_windows(spool, window_bytes)):
                soup = BeautifulSoup(piece, "html.parser")
                for element in soup(["script", "style", "noscript"]):
                    element.decompose()
                text = normalize(soup.get_text("\n", strip=True))
                if text:
                    produced = True
                    yield text
        else:
            outcome.method = "decoded_text_stream"
            async for piece in text_windows(_disk_windows(spool, window_bytes)):
                text = normalize(piece)
                if text:
                    produced = True
                    yield text
    finally:
        await asyncio.to_thread(spool.unlink, True)

    if not produced:
        outcome.status = "skipped_no_text"
        outcome.notes = ("No usable text was extracted.",)
