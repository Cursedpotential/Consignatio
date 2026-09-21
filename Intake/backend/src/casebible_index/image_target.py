"""CocoIndex v1 root target for the image collection: named single + multi-vector objects.

> _Byline: Claude Code · Fable 5.1 · 2026-09-21_
Same contract as `weaviate_target.py` (idempotent objects, retirement marks `active=false`,
never deletes, schema provisioned outside the indexing process) but its own provider id,
collection and writer: the image index is a separate app and never shares the text
collection's identity. `image_maxsim` is a bag of 128-d vectors scored with MaxSim.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from uuid import UUID

import cocoindex as coco
import httpx

from .image_embedders import MULTI_DIMENSIONS

SINGLE_VECTOR = "image_single"
MULTI_VECTOR = "image_maxsim"
TEXT_PROPERTIES = (
    "source_id",
    "source_path",
    "filename",
    "content_sha256",
    "original_time",
    "original_time_source",
    "original_time_confidence",
    "device",
    "software",
    "gps",
    "ocr_text",
    "embed_single_model",
    "embed_multi_model",
    "notes",
)
BOOL_PROPERTIES = ("active", "is_screenshot", "original_time_conflict")


def collection_schema(collection: str) -> dict:
    """The schema this writer requires; provisioned explicitly by `image-provision`."""
    hnsw = {"distance": "cosine"}
    return {
        "class": collection,
        "properties": [{"name": name, "dataType": ["text"]} for name in TEXT_PROPERTIES]
        + [{"name": name, "dataType": ["boolean"]} for name in BOOL_PROPERTIES],
        "vectorConfig": {
            SINGLE_VECTOR: {
                "vectorizer": {"none": {}},
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": hnsw,
            },
            MULTI_VECTOR: {
                "vectorizer": {"none": {}},
                "vectorIndexType": "hnsw",
                "vectorIndexConfig": {**hnsw, "multivector": {"enabled": True}},
            },
        },
    }


@dataclass(frozen=True)
class ImageObjectSpec:
    properties: dict[str, str | bool]
    single: list[float]
    multi: list[list[float]] | None


@dataclass(frozen=True)
class ImageObjectAction:
    key: tuple[str, str, str]  # origin, collection, UUID
    spec: ImageObjectSpec | None


class ImageObjectWriter:
    def __init__(
        self, url: str, collection: str, single_dimensions: int, client: httpx.AsyncClient
    ):
        if not url.startswith(("http://", "https://")) or not collection.isidentifier():
            raise ValueError("Image index needs a Weaviate URL and a plain collection name")
        self.url = url.rstrip("/")
        self.collection = collection
        self.single_dimensions = single_dimensions
        self.client = client

    async def verify_schema(self) -> None:
        response = await self.client.get(f"{self.url}/v1/schema/{self.collection}")
        response.raise_for_status()
        schema = response.json()
        properties = {item["name"]: item["dataType"] for item in schema.get("properties", [])}
        for name in TEXT_PROPERTIES:
            if properties.get(name) != ["text"]:
                raise ValueError(f"Image collection missing text property: {name}")
        for name in BOOL_PROPERTIES:
            if properties.get(name) != ["boolean"]:
                raise ValueError(f"Image collection missing boolean property: {name}")
        vectors = schema.get("vectorConfig", {})
        for name in (SINGLE_VECTOR, MULTI_VECTOR):
            if vectors.get(name, {}).get("vectorizer") != {"none": {}}:
                raise ValueError(f"Named vector {name} must explicitly use the none vectorizer")
        multivector = vectors[MULTI_VECTOR].get("vectorIndexConfig", {}).get("multivector", {})
        if not multivector.get("enabled"):
            raise ValueError("image_maxsim must be a multi-vector index")

    def _check(self, spec: ImageObjectSpec) -> None:
        if len(spec.single) != self.single_dimensions or not all(
            math.isfinite(v) for v in spec.single
        ):
            raise ValueError("Invalid single image vector")
        if spec.multi is not None and (
            not spec.multi or any(len(v) != MULTI_DIMENSIONS for v in spec.multi)
        ):
            raise ValueError("Invalid MaxSim vector bag")

    async def apply(self, action: ImageObjectAction) -> None:
        origin, collection, object_id = action.key
        UUID(object_id)  # Bound path segment, never arbitrary input URL.
        if (origin, collection) != (self.url, self.collection):
            raise ValueError("Target identity changed; restore the original writer configuration")
        path = f"{origin}/v1/objects/{collection}/{object_id}"
        try:
            existing = await self.client.get(path)
            if existing.status_code != 404:
                existing.raise_for_status()
            if action.spec is None:
                if existing.status_code != 404:
                    result = await self.client.patch(
                        path,
                        json={
                            "class": collection,
                            "id": object_id,
                            "properties": {"active": False},
                        },
                    )
                    result.raise_for_status()
                return
            self._check(action.spec)
            vectors: dict[str, object] = {SINGLE_VECTOR: action.spec.single}
            if action.spec.multi is not None:
                vectors[MULTI_VECTOR] = action.spec.multi
            payload = {
                "class": collection,
                "id": object_id,
                "properties": {**action.spec.properties, "active": True},
                "vectors": vectors,
            }
            if existing.status_code == 404:
                result = await self.client.post(f"{origin}/v1/objects", json=payload)
                if result.status_code in {409, 422}:
                    check = await self.client.get(path)
                    check.raise_for_status()
                    result = await self.client.put(path, json=payload)
            else:
                result = await self.client.put(path, json=payload)
            result.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError("Weaviate image write failed; state remains retryable") from exc


IMAGE_WRITER = coco.ContextKey[ImageObjectWriter]("intake_images_weaviate_writer")


class ImageObjectHandler:
    def __init__(self):
        self.sink = coco.TargetActionSink.from_async_fn(self.apply_actions)

    async def apply_actions(
        self,
        context_provider: coco.ContextProvider,
        actions: Sequence[ImageObjectAction],
        /,
    ) -> None:
        writer = context_provider.get(IMAGE_WRITER)
        for action in actions:  # sequential: a MaxSim bag is ~0.4 MB per request
            await writer.apply(action)

    def reconcile(
        self,
        key: coco.StableKey,
        desired_target_state: ImageObjectSpec | coco.NonExistenceType,
        prev_possible_records: Collection[str],
        prev_may_be_missing: bool,
        /,
    ) -> coco.TargetReconcileOutput | None:
        if not isinstance(key, tuple) or len(key) != 3:
            raise ValueError("Invalid Weaviate image target identity")
        if coco.is_non_existence(desired_target_state):
            if not prev_possible_records and not prev_may_be_missing:
                return None
            return coco.TargetReconcileOutput(
                ImageObjectAction(key, None), self.sink, coco.NON_EXISTENCE
            )
        serialized = json.dumps(
            {
                "properties": desired_target_state.properties,
                "single": desired_target_state.single,
                "multi": desired_target_state.multi,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        if (
            prev_possible_records
            and not prev_may_be_missing
            and all(record == fingerprint for record in prev_possible_records)
        ):
            return None
        return coco.TargetReconcileOutput(
            ImageObjectAction(key, desired_target_state),
            self.sink,
            fingerprint,
        )


_provider = coco.register_root_target_states_provider(
    "intake/images/weaviate/object",
    ImageObjectHandler(),
)


@coco.fn
def declare_image(origin: str, collection: str, object_id: str, spec: ImageObjectSpec) -> None:
    coco.declare_target_state(
        _provider.target_state(
            (origin.rstrip("/"), collection, str(UUID(object_id))),
            spec,
        )
    )
