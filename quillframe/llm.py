"""Structured-output helpers: ask models for JSON and validate it against a schema."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from quillframe.providers import GenResult, NoProvidersError, available_providers
from quillframe.utils import extract_json

T = TypeVar("T", bound=BaseModel)


@dataclass
class JsonAttempt:
    result: GenResult
    parsed: BaseModel | None = None
    parse_error: str | None = None

    @property
    def valid(self) -> bool:
        return self.parsed is not None


def _parse(result: GenResult, model_cls: type[T]) -> JsonAttempt:
    if result.error:
        return JsonAttempt(result, None, result.error)
    try:
        # pydantic's ValidationError and json.JSONDecodeError are both ValueErrors
        return JsonAttempt(result, model_cls.model_validate(extract_json(result.text)))
    except ValueError as e:
        return JsonAttempt(result, None, f"invalid JSON/schema: {str(e)[:200]}")


async def run_json_all(prompt: str, model_cls: type[T]) -> list[JsonAttempt]:
    """Run the prompt on every provider concurrently; parse and validate each answer."""
    providers = available_providers()
    if not providers:
        raise NoProvidersError()
    results = await asyncio.gather(*(p.generate(prompt, json_mode=True) for p in providers))
    return [_parse(r, model_cls) for r in results]


async def run_json_first(prompt: str, model_cls: type[T]) -> tuple[T, list[JsonAttempt]]:
    """Try providers one by one (primary first) until one returns valid output."""
    providers = available_providers()
    if not providers:
        raise NoProvidersError()
    attempts: list[JsonAttempt] = []
    for provider in providers:
        attempt = _parse(await provider.generate(prompt, json_mode=True), model_cls)
        attempts.append(attempt)
        if attempt.valid:
            return attempt.parsed, attempts  # type: ignore[return-value]
    raise RuntimeError(summarize_failures(attempts))


def summarize_failures(attempts: list[JsonAttempt]) -> str:
    details = "; ".join(f"{a.result.provider}: {a.parse_error}" for a in attempts)
    return f"No model returned valid output ({details})"
