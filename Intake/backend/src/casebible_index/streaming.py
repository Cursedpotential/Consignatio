"""Streaming text extraction with bounded memory.

> Byline: Claude Code · Opus 5 · 2026-09-22 (owner 2026-09-19/09-20: stream everything;
> a whole-document-in-memory reader is a defect to replace, not a limit to cap around)

Two shapes of source:

* **Text-like** (``.txt``, ``.md``, ``.csv``, ``.log``, ``.jsonl`` …) — decoded and yielded
  in bounded windows split on line boundaries. Peak memory is one window plus one line.
* **Container files** — an ``.xml`` SMS backup or a large ``.json`` is a sequence of
  records, not one document. The splitters below yield one record at a time:
  ``smsbackuprestore`` ``<sms>``/``<mms>``/``<call>`` elements the way the SBV Go parser
  treats them, and JSON arrays / NDJSON element by element.

Formats that genuinely need random access (PDF, DOCX, RTF) are staged through a
disk-backed spool, so process memory stays bounded even when the object does not fit in
RAM. That is a deliberate, documented exception: it is bounded memory, not a byte cap.
"""

from __future__ import annotations

import io
import json
import re
import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator, Iterator

from charset_normalizer import from_bytes

WINDOW_BYTES = 1 * 1024 * 1024
_RECORD_TAGS = ("sms", "mms", "call", "record", "message", "entry", "item")
_WS = re.compile(r"[ \t]+\n")
_BLANKS = re.compile(r"\n{4,}")

# Streamed formats never touch a spool; everything else does.
STREAMABLE_EXTENSIONS = frozenset({
    ".csv", ".jsonl", ".log", ".markdown", ".md", ".rst", ".text", ".tsv", ".txt",
    ".yaml", ".yml", ".xml", ".json", ".htm", ".html",
})


def normalize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    return _BLANKS.sub("\n\n\n", _WS.sub("\n", text)).strip()


class IncrementalDecoder:
    """Decode a byte stream to text without holding the whole stream.

    The encoding is sniffed once from the first window (charset-normalizer, the same
    detector the non-streaming extractor uses) and then applied incrementally, so a
    multi-byte character split across two windows is not corrupted.
    """

    def __init__(self) -> None:
        self._decoder: io.IncrementalNewlineDecoder | None = None
        self._raw = None
        self._encoding = "utf-8"

    def _start(self, window: bytes) -> None:
        import codecs

        best = from_bytes(window[:65536]).best()
        self._encoding = (best.encoding if best is not None else "utf-8") or "utf-8"
        try:
            self._raw = codecs.getincrementaldecoder(self._encoding)(errors="replace")
        except LookupError:
            self._encoding = "utf-8"
            self._raw = codecs.getincrementaldecoder("utf-8")(errors="replace")

    def feed(self, window: bytes, *, final: bool = False) -> str:
        if self._raw is None:
            self._start(window)
        assert self._raw is not None
        return self._raw.decode(window, final)

    @property
    def encoding(self) -> str:
        return self._encoding


async def text_windows(
    byte_windows: AsyncIterator[bytes], *, window_chars: int = 1_000_000
) -> AsyncIterator[str]:
    """Yield decoded text in bounded pieces, cut on the last newline in each piece."""
    decoder = IncrementalDecoder()
    carry = ""
    async for window in byte_windows:
        carry += decoder.feed(window)
        while len(carry) >= window_chars:
            cut = carry.rfind("\n", 0, window_chars)
            if cut <= 0:
                cut = window_chars
            piece, carry = carry[:cut], carry[cut:]
            if piece.strip():
                yield piece
    carry += decoder.feed(b"", final=True)
    if carry.strip():
        yield carry


def split_json_stream(text_pieces: Iterator[str]) -> Iterator[str]:
    """Yield top-level records from a JSON array or NDJSON, one at a time.

    A bracket-depth scanner that respects strings and escapes. Neither the array nor the
    accumulated records are ever held whole; only the element being assembled is.
    """
    buffer = ""
    depth = 0
    in_string = False
    escaped = False
    started = False
    for piece in text_pieces:
        for char in piece:
            if not started:
                if char in "{[":
                    if char == "[" and depth == 0:
                        started = True
                        continue
                    started = True
                elif char.isspace():
                    continue
                else:
                    started = True
            if in_string:
                buffer += char
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
                buffer += char
                continue
            if char in "{[":
                depth += 1
                buffer += char
                continue
            if char in "}]":
                depth -= 1
                if depth < 0:
                    depth = 0
                    buffer = ""
                    continue
                buffer += char
                if depth == 0:
                    record = buffer.strip()
                    buffer = ""
                    if record:
                        yield _render_json_record(record)
                continue
            if depth == 0:
                if char in ",\n\r":
                    record = buffer.strip()
                    buffer = ""
                    if record:
                        yield _render_json_record(record)
                    continue
                buffer += char
                continue
            buffer += char
    tail = buffer.strip().rstrip(",")
    if tail:
        yield _render_json_record(tail)


def _render_json_record(record: str) -> str:
    try:
        return json.dumps(json.loads(record), ensure_ascii=False, indent=1)
    except ValueError:
        return record


def split_xml_records(handle: io.BufferedIOBase) -> Iterator[str]:
    """Yield one text block per record element of a record-per-element XML file.

    ``iterparse`` with ``clear()`` on the completed element keeps the tree from growing:
    the SMS backup's ``<sms>`` / ``<mms>`` / ``<call>`` elements are the record boundary
    SBV uses, so a 1 GB backup streams at constant memory.
    """
    root = None
    for event, element in ET.iterparse(handle, events=("start", "end")):
        if event == "start" and root is None:
            root = element
            continue
        if event != "end":
            continue
        tag = element.tag.rsplit("}", 1)[-1].casefold()
        if tag not in _RECORD_TAGS:
            continue
        parts = [f"{name}: {value}" for name, value in element.attrib.items() if value]
        parts.extend(value.strip() for value in element.itertext() if value.strip())
        element.clear()
        if root is not None:
            root.clear()
        block = "\n".join(parts).strip()
        if block:
            yield block
