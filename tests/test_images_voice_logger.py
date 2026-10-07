import asyncio

import httpx

from quillframe import config, utils
from quillframe.images import HuggingFaceProvider, PollinationsProvider, available_image_providers, generate_images
from quillframe.llm import JsonAttempt
from quillframe.logger import ExperimentLog
from quillframe.brief import CampaignBrief
from quillframe.providers.base import GenResult
from quillframe.voice import VoiceResult
from tests.fakes import BRIEF

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 2000


def mock(handler):
    utils.set_transport(httpx.MockTransport(handler))


def test_pollinations_saves_image(tmp_path):
    mock(lambda request: httpx.Response(200, content=PNG, headers={"content-type": "image/png"}))
    result = asyncio.run(PollinationsProvider().generate("a river", tmp_path / "image_1_pollinations", 1))
    assert result.error is None
    assert result.path.endswith(".png") and (tmp_path / "image_1_pollinations.png").read_bytes() == PNG


def test_non_image_response_is_reported(tmp_path):
    mock(lambda request: httpx.Response(200, text="rate limited", headers={"content-type": "text/plain"}))
    result = asyncio.run(PollinationsProvider().generate("a river", tmp_path / "x", 1))
    assert result.path is None and "expected an image" in result.error


def test_huggingface_sends_token(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "HF_TOKEN", "hf_abc")
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, content=PNG, headers={"content-type": "image/jpeg"})

    mock(handler)
    result = asyncio.run(HuggingFaceProvider().generate("a river", tmp_path / "img", 1))
    assert seen["auth"] == "Bearer hf_abc" and result.path.endswith(".jpg")


def test_image_providers_depend_on_token(monkeypatch):
    monkeypatch.setattr(config, "HF_TOKEN", None)
    assert [p.name for p in available_image_providers()] == ["pollinations"]
    monkeypatch.setattr(config, "HF_TOKEN", "t")
    assert [p.name for p in available_image_providers()] == ["pollinations", "huggingface"]


def test_generate_images_respects_count_and_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "HF_TOKEN", None)
    mock(lambda request: httpx.Response(200, content=PNG, headers={"content-type": "image/png"}))
    results = asyncio.run(generate_images(["a", "b", "c"], tmp_path / "images", n=2))
    assert len(results) == 2 and all(r.path for r in results)
    assert asyncio.run(generate_images(["a"], tmp_path / "none", n=0)) == []


def test_voice_failure_is_captured(monkeypatch, tmp_path):
    import sys

    monkeypatch.setitem(sys.modules, "edge_tts", None)  # makes `import edge_tts` fail
    from quillframe.voice import synthesize

    result = asyncio.run(synthesize("hello", tmp_path / "v.mp3"))
    assert result.path is None and result.error


def test_logger_renders_tables_and_escapes_pipes(tmp_path):
    brief = CampaignBrief.model_validate(BRIEF)
    attempts = [
        JsonAttempt(GenResult("gemini", "g-model", text="", latency_s=1.5), parsed=brief),
        JsonAttempt(GenResult("groq", "l-model", latency_s=0.5, error="HTTP 429: a|b"), parsed=None, parse_error="HTTP 429: a|b"),
    ]
    from quillframe.images import ImageResult

    log = ExperimentLog("River Lights", "line one\nline two")
    log.add_text_comparison("Text model comparison", attempts, "gemini")
    log.add_images([ImageResult("pollinations", "flux", 1, "prompt", str(tmp_path / "image_1_pollinations.png"), 2.0)])
    log.add_voice(VoiceResult("en-US-AriaNeural", str(tmp_path / "voiceover.mp3"), 1.0))
    log.add_social(None, "all failed")
    path = log.write(tmp_path / "EXPERIMENT_LOG.md", total_s=12.3)

    text = path.read_text(encoding="utf-8")
    assert "# Experiment log: River Lights" in text
    assert "Schema-valid answers: 1/2" in text
    assert "a\\|b" in text
    assert "[image_1_pollinations.png](images/image_1_pollinations.png)" in text
    assert "Skipped: all failed" in text
    assert "> line one\n> line two" in text
