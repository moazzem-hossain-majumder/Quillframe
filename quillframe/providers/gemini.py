from __future__ import annotations

from quillframe import config
from quillframe.providers.base import TextProvider
from quillframe.utils import http_client, raise_for_status_verbose, request_with_retry

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(TextProvider):
    name = "gemini"

    def __init__(self) -> None:
        self.model = config.GEMINI_MODEL

    async def _call(self, prompt: str, json_mode: bool) -> str:
        body: dict = {"contents": [{"parts": [{"text": prompt}]}]}
        if json_mode:
            body["generationConfig"] = {"responseMimeType": "application/json"}
        async with http_client() as client:
            r = await request_with_retry(
                client,
                "POST",
                f"{BASE_URL}/models/{self.model}:generateContent",
                headers={"x-goog-api-key": config.GEMINI_API_KEY or ""},
                json=body,
            )
        raise_for_status_verbose(r)
        data = r.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"empty or blocked response: {str(data)[:200]}") from None
        return "".join(p.get("text", "") for p in parts)


async def list_models() -> list[str]:
    """Names of Gemini models usable with generateContent for this API key."""
    async with http_client() as client:
        r = await request_with_retry(
            client,
            "GET",
            f"{BASE_URL}/models",
            headers={"x-goog-api-key": config.GEMINI_API_KEY or ""},
            params={"pageSize": 200},
        )
    raise_for_status_verbose(r)
    names = [
        m["name"].removeprefix("models/")
        for m in r.json().get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    return sorted(names)
