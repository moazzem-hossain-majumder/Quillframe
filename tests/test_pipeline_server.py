import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from quillframe import config, llm, pipeline, server
from quillframe.images import ImageResult
from quillframe.voice import VoiceResult
from tests.fakes import FakeProvider, smart_text


@pytest.fixture
def fake_world(monkeypatch):
    """Two fake text models plus fake image/voice generators that write real files."""
    providers = [FakeProvider("alpha", text=smart_text), FakeProvider("beta", text="garbage")]
    monkeypatch.setattr(llm, "available_providers", lambda: providers)
    import quillframe.compare as compare_module

    monkeypatch.setattr(compare_module, "available_providers", lambda: providers)

    async def fake_images(prompts, out_dir, n=None):
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for i, prompt in enumerate(prompts[: (2 if n is None else n)], start=1):
            path = out_dir / f"image_{i}_fake.png"
            path.write_bytes(b"x" * 600)
            results.append(ImageResult("fake", "fake-model", i, prompt, str(path), 0.2))
        return results

    async def fake_voice(text, out_path, voice=None):
        out_path.write_bytes(b"audio")
        return VoiceResult(voice or "test-voice", str(out_path), 0.1)

    monkeypatch.setattr(pipeline, "generate_images", fake_images)
    monkeypatch.setattr(pipeline, "synthesize", fake_voice)
    return providers


def test_pipeline_writes_all_artifacts(fake_world, tmp_path):
    steps = []
    manifest = asyncio.run(pipeline.run_campaign("A studio launching a river film", out_root=tmp_path, progress=steps.append))

    run_dir = tmp_path / manifest["id"]
    for name in ["brief.json", "social.json", "result.json", "EXPERIMENT_LOG.md", "voiceover.mp3", "images/image_1_fake.png"]:
        assert (run_dir / name).exists(), name

    assert manifest["brief"]["campaign_name"] == "River Lights"
    assert manifest["brief_provider"] == "alpha"
    assert [c["valid"] for c in manifest["text_comparison"]] == [True, False]
    assert manifest["images"][0]["file"] == "images/image_1_fake.png"
    assert manifest["social"]["instagram"]["hashtags"][0] == "#riverlights"
    assert json.loads((run_dir / "result.json").read_text(encoding="utf-8"))["id"] == manifest["id"]
    assert steps and "Done" in steps[-1]
    assert [m["id"] for m in pipeline.list_campaigns(tmp_path)] == [manifest["id"]]


def test_pipeline_survives_social_failure(fake_world, tmp_path, monkeypatch):
    def only_brief(prompt):
        if "social media strategist" in prompt:
            return "not json at all"
        return smart_text(prompt)

    providers = [FakeProvider("alpha", text=only_brief)]
    monkeypatch.setattr(llm, "available_providers", lambda: providers)
    manifest = asyncio.run(pipeline.run_campaign("A studio launching a river film", out_root=tmp_path))
    assert manifest["social"] is None and manifest["social_error"]
    assert "Skipped" in (tmp_path / manifest["id"] / "EXPERIMENT_LOG.md").read_text(encoding="utf-8")


def test_pipeline_fails_clearly_when_no_model_gives_valid_brief(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "available_providers", lambda: [FakeProvider("a", text="nope")])
    with pytest.raises(RuntimeError, match="No model returned valid output"):
        asyncio.run(pipeline.run_campaign("A studio launching a river film", out_root=tmp_path))


def test_server_endpoints(fake_world, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "TEXT_PRIMARY", "alpha")
    client = TestClient(server.app)

    assert "Quillframe" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200

    health = client.get("/api/health").json()
    assert health["status"] == "ok" and health["image"][0]["provider"] == "pollinations"

    compared = client.post("/api/compare", json={"prompt": "hello"}).json()["results"]
    assert [r["provider"] for r in compared] == ["alpha", "beta"]

    assert client.post("/api/compare", json={"prompt": ""}).status_code == 422
    assert client.post("/api/campaign", json={"brief": "short"}).status_code == 422
    assert client.get("/api/campaigns/..%2Fetc/log").status_code in (400, 404)


def test_server_campaign_and_log(fake_world, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(pipeline.config, "OUTPUT_DIR", tmp_path)
    client = TestClient(server.app)

    response = client.post("/api/campaign", json={"brief": "A studio launching a river film", "images": 1})
    assert response.status_code == 200
    run_id = response.json()["id"]

    log = client.get(f"/api/campaigns/{run_id}/log")
    assert log.status_code == 200 and "Experiment log" in log.text
    assert any(c["id"] == run_id for c in client.get("/api/campaigns").json()["campaigns"])


def test_server_reports_missing_keys(monkeypatch):
    import quillframe.compare as compare_module

    monkeypatch.setattr(compare_module, "available_providers", lambda: [])
    monkeypatch.setattr(llm, "available_providers", lambda: [])
    client = TestClient(server.app)
    assert client.post("/api/compare", json={"prompt": "hi"}).status_code == 400
    assert client.post("/api/campaign", json={"brief": "A studio launching a river film"}).status_code == 400
