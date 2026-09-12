from __future__ import annotations

from pathlib import Path

import duckdb

from casebible_index.atomic_units import detect_atomic_units
from casebible_index.config import Settings
from casebible_index.inventory import write_inventory


def settings_for(source: Path, output: Path) -> Settings:
    return Settings(
        source_dir=source,
        source_id="recovery-test",
        output_dir=output,
        nim_base_url="https://example.test/v1",
        embed_model="embed",
        summary_model="summary",
        embed_dimensions=3,
        chunk_size=100,
        chunk_overlap=10,
        summary_max_chars=1000,
        embed_batch_size=4,
        max_concurrency=1,
        timeout_seconds=2,
        max_retries=0,
    )


def write(path: Path, value: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def test_detects_and_nests_export_units_without_reading_binary_content(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    write(source / "FB Data" / "Export A" / "your_facebook_activity" / "messages" / "a.json")
    write(source / "FB Data" / "Export B" / "your_facebook_activity" / "posts" / "b.json")
    write(source / "Google Takeout" / "Takeout 2" / "Mail" / "mail.mbox")
    write(source / "ChatGPT" / "conversations.json", "[]")
    write(source / "ChatGPT" / "chat.html", "<html></html>")
    write(source / "iMessage Export" / "messages.csv", "text\nhello")
    write(source / "FB Data" / "Export A" / "nested.zip", "binary-placeholder")
    config = settings_for(source, output)

    inventory = write_inventory(config, batch_size=2)
    result = detect_atomic_units(config, inventory.path)
    connection = duckdb.connect(":memory:")
    try:
        units = connection.execute(
            "SELECT unit_type, platform, root_path, parent_unit_id, copy_independently "
            "FROM read_parquet(?)",
            [str(result.units_path)],
        ).fetchall()
        edges = connection.execute(
            "SELECT count() FROM read_parquet(?)", [str(result.edges_path)]
        ).fetchone()[0]
    finally:
        connection.close()

    unit_types = {row[0] for row in units}
    platforms = {row[1] for row in units}
    assert {"facebook_dyi", "google_takeout", "chat_export", "archive_file"} <= unit_types
    assert {"chatgpt", "imessage"} <= platforms
    assert edges >= 1
    assert any(parent is not None and not independent for _, _, _, parent, independent in units)
