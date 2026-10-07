"""Model arena: send one prompt to every configured text model concurrently."""
from __future__ import annotations

import asyncio

from quillframe.providers import GenResult, NoProvidersError, available_providers


async def compare(prompt: str, json_mode: bool = False) -> list[GenResult]:
    providers = available_providers()
    if not providers:
        raise NoProvidersError()
    return list(await asyncio.gather(*(p.generate(prompt, json_mode) for p in providers)))
