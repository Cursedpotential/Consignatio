"""Intake image index: its own CocoIndex v1 app, state, collection and lock.

> _Byline: Claude Code · Fable 5.1 · 2026-09-21_
Owner direction 2026-09-21 (docs/PROPOSAL-2026-09-21-IMAGE-INDEX.md): borrow the shape of the
CocoIndex image-search / ColPali / multi-format examples, keep vectors in Weaviate (MaxSim),
use a cheap hosted embedder, Tesseract as the text fallback, original timestamps and device as
first-class facts. Option C: a single vector for every image, a Jina MaxSim bag for screenshots.
Source bytes are read, never modified. Every setting is `INTAKE_IMAGES_*`; nothing is shared
with the text indexer's app name, state directory, lock or collection.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import cocoindex as coco
import httpx
from cocoindex.connectors import localfs
from cocoindex.resources.file import FileLike, PatternFilePathMatcher

from .image_embedders import JINA_MODEL, SINGLE_DIMENSIONS, ImageEmbedders
from .image_facts import read_image_facts
from .image_target import IMAGE_WRITER, ImageObjectSpec, ImageObjectWriter, declare_image
from .secrets import get_secret
from .source_runtime import source_lock

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff")
_EXCLUDED_SEGMENTS = frozenset({".git", ".review_hold", "to_be_deleted", "__pycache__"})
_SIDECAR_SUFFIXES = (".json", ".supplemental-metadata.json")
EMBEDDERS = coco.ContextKey[ImageEmbedders]("intake_images_embedders")
COUNTS = coco.ContextKey[dict]("intake_images_counts")


@dataclass(frozen=True)
class ImageSettings:
    source_dir: Path
    source_id: str
    state_dir: Path
    weaviate_url: str
    collection: str
    single_provider: str
    maxsim: str  # "screenshots" | "all" | "none"
    ocr: bool
    max_file_bytes: int
    max_ocr_chars: int
    max_inflight: int

    @classmethod
    def from_env(cls) -> ImageSettings:
        source = Path(os.getenv("INTAKE_IMAGES_SOURCE_DIR", "") or ".")
        return cls(
            source_dir=source,
            source_id=os.getenv("INTAKE_IMAGES_SOURCE_ID", ""),
            state_dir=Path(os.getenv("INTAKE_IMAGES_STATE_DIR", "") or "output/image-index"),
            weaviate_url=os.getenv("INTAKE_IMAGES_WEAVIATE_URL", "").rstrip("/"),
            collection=os.getenv("INTAKE_IMAGES_COLLECTION", "IntakeImageV1"),
            single_provider=os.getenv("INTAKE_IMAGES_SINGLE_PROVIDER", "nim"),
            maxsim=os.getenv("INTAKE_IMAGES_MAXSIM", "screenshots"),
            ocr=os.getenv("INTAKE_IMAGES_OCR", "1") == "1",
            max_file_bytes=int(os.getenv("INTAKE_IMAGES_MAX_FILE_BYTES", str(25 * 1024 * 1024))),
            max_ocr_chars=int(os.getenv("INTAKE_IMAGES_MAX_OCR_CHARS", "20000")),
            max_inflight=int(os.getenv("INTAKE_IMAGES_MAX_INFLIGHT", "2")),
        )

    def validate(self) -> None:
        if not os.getenv("INTAKE_IMAGES_SOURCE_DIR") or not self.source_dir.is_dir():
            raise ValueError("INTAKE_IMAGES_SOURCE_DIR must name an existing directory")
        if not self.source_id:
            raise ValueError(
                "INTAKE_IMAGES_SOURCE_ID is required: a stable name for this source tree"
            )
        if not self.weaviate_url:
            raise ValueError("INTAKE_IMAGES_WEAVIATE_URL is required")
        if self.single_provider not in SINGLE_DIMENSIONS:
            raise ValueError("INTAKE_IMAGES_SINGLE_PROVIDER must be 'nim' or 'google'")
        if self.maxsim not in {"screenshots", "all", "none"}:
            raise ValueError("INTAKE_IMAGES_MAXSIM must be screenshots, all or none")


def _sidecar_text(path: Path) -> str | None:
    """A Google Takeout sidecar sits beside the image as `<name>.json`."""
    for suffix in _SIDECAR_SUFFIXES:
        candidate = path.with_name(path.name + suffix)
        try:
            if candidate.is_file() and candidate.stat().st_size <= 65536:
                return candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return None


@coco.fn(memo=True)
async def process_image(
    file: FileLike,
    *,
    source_dir: Path,
    source_id: str,
    origin: str,
    collection: str,
    maxsim: str,
    ocr: bool,
    max_file_bytes: int,
    max_ocr_chars: int,
) -> None:
    source_path = file.file_path.resolve()
    if source_path.stat().st_size > max_file_bytes:
        raise ValueError("Image exceeds INTAKE_IMAGES_MAX_FILE_BYTES")
    content = await file.read()
    relative_path = source_path.relative_to(source_dir.resolve()).as_posix()
    facts = read_image_facts(
        source_path,
        source_path.name,
        takeout_sidecar_json=_sidecar_text(source_path),
        ocr=ocr,
        max_ocr_chars=max_ocr_chars,
    )
    embedders = coco.use_context(EMBEDDERS)
    extension = source_path.suffix
    single = await embedders.embed_single(content, extension)
    wants_multi = maxsim == "all" or (maxsim == "screenshots" and facts.is_screenshot)
    multi = await embedders.embed_multi(content) if wants_multi else None
    time = facts.original_time
    declare_image(
        origin,
        collection,
        str(uuid5(NAMESPACE_URL, f"intake-image:{source_id}:{relative_path}")),
        ImageObjectSpec(
            properties={
                "source_id": source_id,
                "source_path": relative_path,
                "filename": source_path.name,
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "original_time": time.value or "",
                "original_time_source": time.source or "",
                "original_time_confidence": time.confidence or "",
                "original_time_conflict": time.conflict,
                "device": facts.device,
                "software": facts.software,
                "gps": facts.gps,
                "is_screenshot": facts.is_screenshot,
                "ocr_text": facts.ocr_text,
                "embed_single_model": embedders.single_model,
                "embed_multi_model": JINA_MODEL if multi is not None else "",
                "notes": "; ".join(facts.notes),
            },
            single=single,
            multi=multi,
        ),
    )
    counts = coco.use_context(COUNTS)
    counts["indexed"] += 1
    counts["with_maxsim"] += multi is not None
    counts["without_original_time"] += not time.resolved


@coco.fn
async def app_main(settings: ImageSettings) -> None:
    files = localfs.walk_dir(
        settings.source_dir,
        recursive=True,
        path_matcher=PatternFilePathMatcher(
            included_patterns=[f"**/*{ext}" for ext in IMAGE_EXTENSIONS]
            + [f"**/*{ext.upper()}" for ext in IMAGE_EXTENSIONS],
            excluded_patterns=[f"**/{segment}/**" for segment in sorted(_EXCLUDED_SEGMENTS)],
        ),
        live=False,
    )
    handle = await coco.mount_each(
        process_image,
        files.items(),
        source_dir=settings.source_dir,
        source_id=settings.source_id,
        origin=settings.weaviate_url,
        collection=settings.collection,
        maxsim=settings.maxsim,
        ocr=settings.ocr,
        max_file_bytes=settings.max_file_bytes,
        max_ocr_chars=settings.max_ocr_chars,
    )
    await handle.ready()


_settings = ImageSettings.from_env()


@coco.lifespan
async def coco_lifespan(builder: coco.EnvironmentBuilder) -> AsyncIterator[None]:
    _settings.validate()
    _settings.state_dir.mkdir(parents=True, exist_ok=True)
    builder.settings.db_path = _settings.state_dir / "cocoindex.db"
    single_key = get_secret(
        "NVIDIA_API_KEY" if _settings.single_provider == "nim" else "GOOGLE_API_KEY"
    )
    if not single_key:
        raise ValueError("The single-vector provider's API key is not configured")
    jina_key = get_secret("JINA_API_KEY")
    if _settings.maxsim != "none" and not jina_key:
        raise ValueError("JINA_API_KEY is required unless INTAKE_IMAGES_MAXSIM=none")
    counts = {"indexed": 0, "with_maxsim": 0, "without_original_time": 0}
    builder.provide(COUNTS, counts)
    with source_lock(_settings.state_dir / "locks", "images-" + _settings.source_id):
        weaviate_key = get_secret("INTAKE_WEAVIATE_API_KEY")
        headers = {"Authorization": f"Bearer {weaviate_key}"} if weaviate_key else {}
        async with (
            httpx.AsyncClient(timeout=180.0, follow_redirects=False) as provider_client,
            httpx.AsyncClient(
                headers=headers, timeout=60.0, follow_redirects=False
            ) as weaviate_client,
        ):
            builder.provide(
                EMBEDDERS,
                ImageEmbedders(
                    provider_client,
                    _settings.single_provider,
                    single_key,
                    jina_key if _settings.maxsim != "none" else None,
                ),
            )
            writer = ImageObjectWriter(
                _settings.weaviate_url,
                _settings.collection,
                SINGLE_DIMENSIONS[_settings.single_provider],
                weaviate_client,
            )
            await writer.verify_schema()
            builder.provide(IMAGE_WRITER, writer)
            try:
                yield
            finally:
                (_settings.state_dir / "last-run.json").write_text(
                    json.dumps(
                        {
                            "source_id": _settings.source_id,
                            "collection": _settings.collection,
                            "single_provider": _settings.single_provider,
                            **counts,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )


app = coco.App(
    coco.AppConfig(
        name="IntakeImages_" + hashlib.sha256(_settings.source_id.encode()).hexdigest()[:16],
        max_inflight_components=_settings.max_inflight,
    ),
    app_main,
    settings=_settings,
)
