from __future__ import annotations

import io
import json
from pathlib import Path

from docx import Document

from casebible_index.extractors import extract_text


def test_extracts_plain_html_json_and_docx() -> None:
    plain = extract_text(Path("note.txt"), b"alpha\r\n\r\nbeta")
    assert plain.status == "indexed"
    assert plain.text == "alpha\n\nbeta"

    html = extract_text(Path("page.html"), b"<h1>Title</h1><script>bad()</script><p>Body</p>")
    assert html.status == "indexed"
    assert "Title" in html.text and "Body" in html.text and "bad()" not in html.text

    structured = extract_text(Path("data.json"), json.dumps({"name": "Example"}).encode())
    assert structured.extraction_method == "json_normalized"
    assert '"Example"' in structured.text

    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph("Document paragraph")
    document.save(buffer)
    docx = extract_text(Path("document.docx"), buffer.getvalue())
    assert docx.extraction_method == "python_docx"
    assert docx.text == "Document paragraph"


def test_unknown_extension_is_not_treated_as_text() -> None:
    result = extract_text(Path("photo.jpg"), b"not really a photo")
    assert result.status == "unsupported"
    assert result.text == ""
