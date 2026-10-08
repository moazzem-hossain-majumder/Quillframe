"""Small shared helpers: HTTP with retries, tolerant JSON extraction, slugs."""
from __future__ import annotations

import asyncio
import json
import re
import unicodedata

import httpx

RETRY_BASE_DELAY = 2.0  # seconds; doubled on every retry (tests set this to 0)
RETRY_STATUSES = {402, 429, 500, 502, 503, 504}

_transport: httpx.AsyncBaseTransport | None = None


def set_transport(transport: httpx.AsyncBaseTransport | None) -> None:
    """Inject a custom httpx transport (used by the tests to mock the network)."""
    global _transport
    _transport = transport


def http_client(timeout: float = 60.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout, transport=_transport, follow_redirects=True)


async def request_with_retry(
    client: httpx.AsyncClient, method: str, url: str, retries: int = 2, **kwargs
) -> httpx.Response:
    """Send a request, retrying rate-limit (429) and transient 5xx responses."""
    for attempt in range(retries + 1):
        response = await client.request(method, url, **kwargs)
        if response.status_code in RETRY_STATUSES and attempt < retries:
            await asyncio.sleep(RETRY_BASE_DELAY * (2**attempt))
            continue
        return response
    return response  # pragma: no cover


def raise_for_status_verbose(response: httpx.Response) -> None:
    """Like raise_for_status(), but the message includes the API's error body."""
    if response.is_error:
        body = response.text.strip().replace("\n", " ")[:300]
        raise RuntimeError(f"HTTP {response.status_code}: {body}")


def extract_json(text: str):
    """Parse a JSON object out of model output.

    Handles plain JSON, ```json fenced blocks, and JSON surrounded by prose.
    Raises ValueError when nothing parseable is found.
    """
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object found in model output")
    depth, in_string, escaped = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("unbalanced JSON object in model output")


def slugify(text: str, max_len: int = 40) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")[:max_len].strip("-")
    return slug or "campaign"
