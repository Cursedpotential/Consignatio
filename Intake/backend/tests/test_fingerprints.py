from __future__ import annotations

import hashlib
from pathlib import Path

import duckdb

from casebible_index.atomic_units import detect_atomic_units
from casebible_index.config import Settings
from casebible_index.fingerprints import (
    normalize_text_for_fingerprint,
    text_simhash64,
    write_fingerprints,
)
from casebible_index.inventory import write_inventory


def settings_for(source: Path, output: Path) -> Settings:
    return Settings(
        source_dir=source,
        source_id="fingerprint-test",
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


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def test_hashes_exact_and_normalized_text_duplicates_without_selecting_winner(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    write(source / "a.txt", "Hello world\n")
    write(source / "nested" / "b.txt", "Hello world\n")
    write(source / "c.txt", "HELLO    world")
    write(source / "empty.txt", "")
    settings = settings_for(source, output)

    inventory = write_inventory(settings)
    result = write_fingerprints(settings, inventory.path, batch_size=2)

    connection = duckdb.connect(":memory:")
    try:
        a = connection.execute(
            "SELECT md5, sha256, blake3, copy_quality FROM read_parquet(?) "
            "WHERE relative_path = 'a.txt'",
            [str(result.files_path)],
        ).fetchone()
        exact = connection.execute(
            "SELECT member_count, exact_identity_proposable, canonical_selection_allowed, "
            "review_state FROM read_parquet(?)",
            [str(result.exact_groups_path)],
        ).fetchone()
        dispositions = connection.execute(
            "SELECT DISTINCT dedup_disposition FROM read_parquet(?)",
            [str(result.exact_members_path)],
        ).fetchall()
        text_group = connection.execute(
            "SELECT member_count, distinct_binary_count FROM read_parquet(?)",
            [str(result.text_equivalent_groups_path)],
        ).fetchone()
        empty_quality = connection.execute(
            "SELECT copy_quality FROM read_parquet(?) WHERE relative_path = 'empty.txt'",
            [str(result.files_path)],
        ).fetchone()[0]
    finally:
        connection.close()

    content = (source / "a.txt").read_bytes()
    assert a[0] == hashlib.md5(content, usedforsecurity=False).hexdigest()
    assert a[1] == hashlib.sha256(content).hexdigest()
    assert len(a[2]) == 64
    assert a[3] == "good_unverified"
    assert exact == (2, True, False, "review_required")
    assert dispositions == [("review_required",)]
    assert text_group == (3, 2)
    assert empty_quality == "bad_zero_byte"


def test_reuses_unchanged_hashes_and_builds_package_duplicate_groups(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    for root in ("Chat Export A", "Chat Export B"):
        write(source / root / "conversations.json", "[]")
        write(source / root / "chat.html", "<html>same</html>")
    settings = settings_for(source, output)

    first_inventory = write_inventory(settings)
    detect_atomic_units(settings, first_inventory.path)
    first = write_fingerprints(settings, first_inventory.path, batch_size=2)
    second_inventory = write_inventory(settings)
    second = write_fingerprints(settings, second_inventory.path, batch_size=2)

    assert first.hashed_count == 4
    assert second.hashed_count == 4
    assert second.reused_count == 4
    assert second.package_groups_path is not None
    connection = duckdb.connect(":memory:")
    try:
        package_group = connection.execute(
            "SELECT unit_count, review_state FROM read_parquet(?)",
            [str(second.package_groups_path)],
        ).fetchone()
    finally:
        connection.close()
    assert package_group == (2, "review_required")


def test_simhash_is_stable_for_normalized_text() -> None:
    left = normalize_text_for_fingerprint("Parenting\n TIME")
    right = normalize_text_for_fingerprint("parenting time")
    assert left == right
    assert text_simhash64(left) == text_simhash64(right)
