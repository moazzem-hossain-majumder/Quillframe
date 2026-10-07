from __future__ import annotations

from quillframe.providers.base import TextProvider
from quillframe.utils import http_client, raise_for_status_verbose, request_with_retry


class OpenAICompatProvider(TextProvider):
    """Base for any service exposing an OpenAI-style /chat/completions endpoint."""

    base_url: str
    supports_json_mode: bool = True
    extra_headers: dict[str, str] = {}

    def api_key(self) -> str:
        raise NotImplementedError

    async def _call(self, prompt: str, json_mode: bool) -> str:
        body: dict = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if json_mode and self.supports_json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key()}", **self.extra_headers}
        async with http_client() as client:
            r = await request_with_retry(
                client, "POST", f"{self.base_url}/chat/completions", headers=headers, json=body
            )
        raise_for_status_verbose(r)
        data = r.json()
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"unexpected response shape: {str(data)[:200]}") from None
