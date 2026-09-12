"""CocoIndex v1 root target: idempotent objects, recoverable retirement.

Implements the public TargetHandler/TargetActionSink protocol. Retired derived
records are marked inactive, never deleted; source paths are never written.
Schema must be provisioned explicitly outside the indexing process.
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

from .filesystem_search import WeaviateSearchConfig


@dataclass(frozen=True)
class ObjectSpec:
    properties: dict[str, str | bool]
    vectors: dict[str, list[float]]


@dataclass(frozen=True)
class ObjectAction:
    key: tuple[str, str, str]  # origin, collection, UUID
    spec: ObjectSpec | None


class WeaviateObjectWriter:
    def __init__(self, config: WeaviateSearchConfig, client: httpx.AsyncClient):
        config.validate()
        self.config = config
        self.client = client

    async def verify_schema(self) -> None:
        response = await self.client.get(
            f"{self.config.url.rstrip('/')}/v1/schema/{self.config.collection}"
        )
        response.raise_for_status()
        schema = response.json()
        properties = {item["name"]: item["dataType"] for item in schema.get("properties", [])}
        for name in ("source_id", "source_path", "document_id", "chunk_id", "filename", "text",
                     "embed_model"):
            if properties.get(name) != ["text"]:
                raise ValueError(f"Filesystem collection missing text property: {name}")
        if properties.get("active") != ["boolean"]:
            raise ValueError("Filesystem collection requires an active boolean property")
        vector = schema.get("vectorConfig", {}).get(self.config.target_vector, {})
        if vector.get("vectorizer") != {"none": {}}:
            raise ValueError("Named text vector must explicitly use the none vectorizer")

    async def apply(self, action: ObjectAction) -> None:
        origin, collection, object_id = action.key
        UUID(object_id)  # Bound path segment, never arbitrary input URL.
        if (origin, collection) != (self.config.url.rstrip("/"), self.config.collection):
            raise ValueError("Target identity changed; restore the original writer configuration")
        if action.spec is not None:
            vector = action.spec.vectors.get(self.config.target_vector, [])
            if len(vector) != self.config.dimensions or not all(math.isfinite(v) for v in vector):
                raise ValueError("Invalid target vector")
            if not any(vector):
                raise ValueError("Zero target vector")
        path = f"{origin}/v1/objects/{collection}/{object_id}"
        try:
            existing = await self.client.get(path)
            if existing.status_code != 404:
                existing.raise_for_status()
            if action.spec is None:
                if existing.status_code != 404:
                    result = await self.client.patch(path, json={
                        "class": collection, "id": object_id, "properties": {"active": False},
                    })
                    result.raise_for_status()
                return
            payload = {
                "class": collection, "id": object_id,
                "properties": {**action.spec.properties, "active": True},
                "vectors": action.spec.vectors,
            }
            if existing.status_code == 404:
                result = await self.client.post(f"{origin}/v1/objects", json=payload)
                # A raced/retried create is resolved only if this exact ID now exists.
                if result.status_code in {409, 422}:
                    check = await self.client.get(path)
                    check.raise_for_status()
                    result = await self.client.put(path, json=payload)
            else:
                result = await self.client.put(path, json=payload)
            result.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError("Weaviate target write failed; state remains retryable") from exc


WEAVIATE_WRITER = coco.ContextKey[WeaviateObjectWriter]("intake_filesystem_weaviate_writer")


class ObjectHandler:
    def __init__(self):
        self.sink = coco.TargetActionSink.from_async_fn(self.apply_actions)

    async def apply_actions(
        self, context_provider: coco.ContextProvider, actions: Sequence[ObjectAction], /,
    ) -> None:
        writer = context_provider.get(WEAVIATE_WRITER)
        # Sequential bounded I/O: no batch-wide unbounded gather or request bodies.
        for action in actions:
            await writer.apply(action)

    def reconcile(
        self, key: coco.StableKey, desired_target_state: ObjectSpec | coco.NonExistenceType,
        prev_possible_records: Collection[str], prev_may_be_missing: bool, /,
    ) -> coco.TargetReconcileOutput | None:
        if not isinstance(key, tuple) or len(key) != 3:
            raise ValueError("Invalid Weaviate target identity")
        if coco.is_non_existence(desired_target_state):
            if not prev_possible_records and not prev_may_be_missing:
                return None
            return coco.TargetReconcileOutput(
                ObjectAction(key, None), self.sink, coco.NON_EXISTENCE,
            )
        serialized = json.dumps({
            "properties": desired_target_state.properties, "vectors": desired_target_state.vectors,
        }, sort_keys=True, separators=(",", ":"), allow_nan=False)
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        if prev_possible_records and not prev_may_be_missing and all(
            record == fingerprint for record in prev_possible_records
        ):
            return None
        return coco.TargetReconcileOutput(
            ObjectAction(key, desired_target_state), self.sink, fingerprint,
        )


_provider = coco.register_root_target_states_provider(
    "intake/filesystem/weaviate/object", ObjectHandler(),
)


@coco.fn
def declare_chunk(origin: str, collection: str, object_id: str, spec: ObjectSpec) -> None:
    coco.declare_target_state(_provider.target_state(
        (origin.rstrip("/"), collection, str(UUID(object_id))), spec,
    ))
