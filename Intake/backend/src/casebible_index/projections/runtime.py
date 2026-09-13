"""Privileged Intake graph factory; secrets never enter Settings or API responses."""

from __future__ import annotations

import asyncio
import os

from ..secrets import get_secret
from .surreal import SurrealGraphClient, SurrealGraphConfig


def graph_config_from_env() -> SurrealGraphConfig:
    config = SurrealGraphConfig(
        endpoint=os.getenv("INTAKE_SURREAL_URL", ""),
        namespace="consignatio",
        database="intake",
        username="intake_runtime",
        password=get_secret("INTAKE_SURREAL_PASSWORD") or "",
    )
    config.validate()
    return config


async def connect_graph() -> SurrealGraphClient:
    async with asyncio.timeout(30):
        return await SurrealGraphClient.connect(graph_config_from_env())
