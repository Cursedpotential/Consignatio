from __future__ import annotations

from pathlib import Path

import pytest

from casebible_index.config import Settings
from casebible_index.tui import CaseBibleTui


def settings_for(source: Path, output: Path) -> Settings:
    return Settings(
        source_dir=source,
        source_id="tui-test",
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


@pytest.mark.asyncio
async def test_tui_starts_with_isolated_identity_and_source_mutation_disabled(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    app = CaseBibleTui(settings_for(source, tmp_path / "output"))

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        identity = str(app.query_one("#identity").render())
        summary = str(app.query_one("#summary").render())

    assert "casebible-corpus" in identity
    assert ".cocoindex_code" in identity
    assert '"source_mutation": "disabled"' in summary
