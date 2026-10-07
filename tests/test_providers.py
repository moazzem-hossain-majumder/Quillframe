import asyncio
import json

import httpx

from quillframe import config, utils
from quillframe.providers import available_providers
from quillframe.providers.gemini import GeminiProvider
from quillframe.providers.groq import GroqProvider
from quillframe.providers.openrouter import OpenRouterProvider


def mock(handler):
    utils.set_transport(httpx.MockTransport(handler))


def test_gemini_parses_response_and_sends_json_mode(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "key")
    seen = {}

    def handler(request):
        seen["key"] = request.headers["x-goog-api-key"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "hi "}, {"text": "there"}]}}]})

    mock(handler)
    result = asyncio.run(GeminiProvider().generate("hello", json_mode=True))
    assert result.text == "hi there" and result.error is None
    assert seen["key"] == "key"
    assert seen["body"]["generationConfig"]["responseMimeType"] == "application/json"


def test_groq_sends_json_response_format(monkeypatch):
    monkeypatch.setattr(config, "GROQ_API_KEY", "gk")
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    mock(handler)
    result = asyncio.run(GroqProvider().generate("hello", json_mode=True))
    assert result.text == "ok"
    assert seen["auth"] == "Bearer gk"
    assert seen["body"]["response_format"] == {"type": "json_object"}


def test_openrouter_never_sends_response_format(monkeypatch):
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", "ok")
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "fine"}}]})

    mock(handler)
    assert asyncio.run(OpenRouterProvider().generate("hello", json_mode=True)).text == "fine"
    assert "response_format" not in seen["body"]


def test_retries_on_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(config, "GROQ_API_KEY", "gk")
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, json={"error": "slow down"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "finally"}}]})

    mock(handler)
    result = asyncio.run(GroqProvider().generate("hello"))
    assert result.text == "finally" and calls["n"] == 3


def test_http_error_becomes_result_error_not_exception(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "bad")
    mock(lambda request: httpx.Response(404, json={"error": {"message": "model not found"}}))
    result = asyncio.run(GeminiProvider().generate("hello"))
    assert result.text == ""
    assert "404" in result.error and "model not found" in result.error


def test_blocked_gemini_response_reports_clear_error(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "key")
    mock(lambda request: httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}}))
    result = asyncio.run(GeminiProvider().generate("hello"))
    assert "empty or blocked" in result.error


def test_available_providers_follow_keys_and_primary(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", None)
    monkeypatch.setattr(config, "GROQ_API_KEY", None)
    monkeypatch.setattr(config, "OPENROUTER_API_KEY", None)
    assert available_providers() == []

    monkeypatch.setattr(config, "GEMINI_API_KEY", "a")
    monkeypatch.setattr(config, "GROQ_API_KEY", "b")
    monkeypatch.setattr(config, "TEXT_PRIMARY", "groq")
    assert [p.name for p in available_providers()] == ["groq", "gemini"]
