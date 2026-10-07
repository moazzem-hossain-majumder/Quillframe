from __future__ import annotations

from quillframe import config
from quillframe.providers.base import GenResult, TextProvider
from quillframe.providers.gemini import GeminiProvider
from quillframe.providers.groq import GroqProvider
from quillframe.providers.openrouter import OpenRouterProvider

__all__ = [
    "GenResult",
    "TextProvider",
    "NoProvidersError",
    "available_providers",
]


class NoProvidersError(RuntimeError):
    """Raised when no text-model API key is configured."""

    def __init__(self) -> None:
        super().__init__(
            "No text-model API keys found. Copy .env.example to .env and add at least one "
            "key (GEMINI_API_KEY, GROQ_API_KEY or OPENROUTER_API_KEY)."
        )


def available_providers() -> list[TextProvider]:
    """Providers whose API key is configured, with the primary provider first."""
    found: list[TextProvider] = []
    if config.GEMINI_API_KEY:
        found.append(GeminiProvider())
    if config.GROQ_API_KEY:
        found.append(GroqProvider())
    if config.OPENROUTER_API_KEY:
        found.append(OpenRouterProvider())
    primary = (config.TEXT_PRIMARY or "").lower()
    found.sort(key=lambda p: p.name != primary)  # stable: primary first, rest keep order
    return found
