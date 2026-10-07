from __future__ import annotations

from quillframe import config
from quillframe.providers.openai_compat import OpenAICompatProvider


class OpenRouterProvider(OpenAICompatProvider):
    """OpenRouter exposes several free models (ids ending in ':free')."""

    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    supports_json_mode = False  # not every free model accepts response_format; we parse tolerantly
    extra_headers = {"X-Title": "Quillframe"}

    def __init__(self) -> None:
        self.model = config.OPENROUTER_MODEL

    def api_key(self) -> str:
        return config.OPENROUTER_API_KEY or ""
