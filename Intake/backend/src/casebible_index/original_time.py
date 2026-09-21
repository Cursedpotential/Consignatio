# ruff: noqa: E501, SIM105  (vendored verbatim from the legal workdesk; keep diffable)
"""Resolve when an image was originally captured, and say how we know.

> _Byline: Claude Code · Fable 5.1 · 2026-09-21_
VENDORED from the legal workdesk (`Legal-desktop/api/legal_workspace/services/original_time.py`,
commit ee67000) so Intake's indexer and the workdesk tool resolve time the same way. Change it
there first, then copy. Owner requirement 2026-09-21: screenshots often show no date, so ordering
a series of shots of one conversation depends on the original capture time. Filesystem dates are
never candidates: the corpus restore re-stamped files in batches.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta, timezone

from pydantic import BaseModel

# exiftool tag (after the group) -> (source label, confidence, rank). Lower rank wins.
_EMBEDDED = (
    ("DateTimeOriginal", "exif_capture_time", "high", 10),
    ("SubSecDateTimeOriginal", "exif_capture_time", "high", 10),
    ("DateCreated", "xmp_date_created", "high", 30),
    ("CreationTime", "png_creation_time", "medium", 32),
    ("Creation Time", "png_creation_time", "medium", 32),
    ("CreationDate", "container_creation_date", "medium", 34),
    ("CreateDate", "embedded_create_date", "medium", 36),
    ("MediaCreateDate", "embedded_create_date", "medium", 36),
    ("DateTimeDigitized", "exif_digitized_time", "medium", 38),
)
# Groups whose dates describe the file on disk, not the capture.
_IGNORED_GROUPS = frozenset({"System", "File", "ExifTool"})

_EXIF_DT = re.compile(
    r"^(\d{4})[:\-](\d{2})[:\-](\d{2})[ T](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?\s*(Z|[+\-]\d{2}:?\d{2})?$"
)
# Screenshot_20240312-141502, Screenshot_2024-03-12-14-15-02, IMG_20240312_141502,
# PXL_20240312_141502123, signal-2024-03-12-141502, "Screenshot 2024-03-12 141502".
_NAME_DT = re.compile(
    r"(?<!\d)(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})[-_ T.]?(\d{2})[-_.:]?(\d{2})[-_.:]?(\d{2})(?:\d{3})?(?!\d)"
)
_NAME_DATE = re.compile(r"(?<!\d)(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})(?!\d)")  # IMG-20240312-WA0001
_NAME_EPOCH = re.compile(r"(?<!\d)(1[4-9]\d{8})(\d{3})?(?!\d)")  # Messenger/Facebook style names

_CONFLICT = timedelta(hours=26)  # wider than any timezone spread between naive and UTC values


class TimeCandidate(BaseModel):
    value: str
    source: str
    field: str
    confidence: str
    timezone_known: bool
    precision: str = "second"


class OriginalTime(BaseModel):
    resolved: bool
    value: str | None = None
    source: str | None = None
    confidence: str | None = None
    timezone_known: bool = False
    precision: str | None = None
    conflict: bool = False
    note: str
    candidates: list[TimeCandidate]


def _offset(text: str | None) -> timezone | None:
    if not text:
        return None
    if text == "Z":
        return UTC
    sign = -1 if text[0] == "-" else 1
    digits = text[1:].replace(":", "")
    return timezone(sign * timedelta(hours=int(digits[:2]), minutes=int(digits[2:4])))


def _parse_embedded(raw: object, fallback_offset: str | None) -> datetime | None:
    match = _EXIF_DT.match(str(raw).strip())
    if not match:
        return None
    year, month, day, hour, minute, second, zone = match.groups()
    try:
        # Naive on purpose: EXIF times are device-local wall-clock unless an offset is present.
        value = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))  # noqa: DTZ001
    except ValueError:
        return None
    tz = _offset(zone) or _offset(fallback_offset)
    return value.replace(tzinfo=tz) if tz else value


def _sort_key(value: datetime) -> datetime:
    return (
        value.replace(tzinfo=None)
        if value.tzinfo is None
        else value.astimezone(UTC).replace(tzinfo=None)
    )


def resolve_original_time(
    fields: dict[str, object], filename: str, takeout_sidecar_json: str | None = None
) -> OriginalTime:
    """Pick the best original capture time from embedded metadata, a Takeout sidecar and the name."""
    found: list[tuple[int, datetime, TimeCandidate]] = []

    def add(
        rank: int,
        when: datetime,
        source: str,
        field: str,
        confidence: str,
        precision: str = "second",
    ) -> None:
        found.append(
            (
                rank,
                when,
                TimeCandidate(
                    value=when.isoformat(),
                    source=source,
                    field=field,
                    confidence=confidence,
                    timezone_known=when.tzinfo is not None,
                    precision=precision,
                ),
            )
        )

    by_tag = {key.split(":", 1)[-1]: value for key, value in fields.items()}
    original_offset = by_tag.get("OffsetTimeOriginal")
    for key, raw in fields.items():
        group, _, tag = key.partition(":")
        if group in _IGNORED_GROUPS:
            continue
        for wanted, source, confidence, rank in _EMBEDDED:
            if tag == wanted:
                offset = (
                    str(original_offset)
                    if wanted.endswith("Original") and original_offset
                    else None
                )
                when = _parse_embedded(raw, offset)
                if when:
                    add(rank, when, source, key, confidence)

    if takeout_sidecar_json:
        try:
            sidecar = json.loads(takeout_sidecar_json)
        except ValueError as exc:
            raise ValueError("takeout_sidecar_json is not valid JSON") from exc
        for field, rank in (("photoTakenTime", 20), ("creationTime", 44)):
            stamp = (
                (sidecar.get(field) or {}).get("timestamp") if isinstance(sidecar, dict) else None
            )
            if stamp and str(stamp).isdigit():
                source = "takeout_photo_taken_time" if rank == 20 else "takeout_upload_time"
                add(
                    rank,
                    datetime.fromtimestamp(int(stamp), UTC),
                    source,
                    f"sidecar:{field}",
                    "high" if rank == 20 else "low",
                )

    stem = filename.rsplit(".", 1)[0]
    named = _NAME_DT.search(stem)
    if named:
        try:
            add(
                50,
                datetime(*(int(part) for part in named.groups())),
                "filename_timestamp",  # noqa: DTZ001
                "filename",
                "medium",
            )
        except ValueError:
            named = None
    if not named:
        epoch = _NAME_EPOCH.search(stem)
        dated = _NAME_DATE.search(stem)
        if epoch:
            add(
                55,
                datetime.fromtimestamp(int(epoch.group(1)), UTC),
                "filename_epoch",
                "filename",
                "medium",
            )
        elif dated:
            try:
                add(
                    60,
                    datetime(*(int(part) for part in dated.groups())),
                    "filename_date",  # noqa: DTZ001
                    "filename",
                    "low",
                    "day",
                )
            except ValueError:
                pass

    if not found:
        return OriginalTime(
            resolved=False,
            note=(
                "No original time in the file or its name. Look for the catalog's source "
                "occurrence, a Takeout sidecar, or a visible clock/date in the OCR text."
            ),
            candidates=[],
        )
    found.sort(key=lambda item: (item[0], _sort_key(item[1])))
    _, best_when, best = found[0]
    # An upload time is expected to trail the capture, so it never counts as a disagreement.
    second_precision = [
        when
        for _, when, cand in found
        if cand.precision == "second" and cand.source != "takeout_upload_time"
    ]
    conflict = bool(second_precision) and (
        max(map(_sort_key, second_precision)) - min(map(_sort_key, second_precision)) > _CONFLICT
    )
    note = (
        "Timezone unknown: the value is the device's local wall-clock time."
        if best_when.tzinfo is None
        else ""
    )
    if conflict:
        note = (note + " " if note else "") + (
            "Candidates disagree by more than a day: the file may have been edited, re-saved or re-stamped."
        )
    return OriginalTime(
        resolved=True,
        value=best.value,
        source=best.source,
        confidence=best.confidence,
        timezone_known=best.timezone_known,
        precision=best.precision,
        conflict=conflict,
        note=note or "Resolved from the source closest to the capturing device.",
        candidates=[cand for _, _, cand in found],
    )
