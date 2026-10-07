from __future__ import annotations

from quillframe import config
from quillframe.providers.openai_compat import OpenAICompatProvider


class GroqProvider(OpenAICompatProvider):
    name = "groq"
    base_url = "https://api.groq.com/openai/v1"

    def __init__(self) -> None:
        self.model = config.GROQ_MODEL

    def api_key(self) -> str:
        return config.GROQ_API_KEY or ""
