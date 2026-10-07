import asyncio
import json

import pytest

from quillframe import llm
from quillframe.brief import CampaignBrief, generate_brief_attempts, pick_brief
from quillframe.compare import compare
from quillframe.providers import NoProvidersError
from quillframe.social import Post, SocialPack, generate_social
from tests.fakes import BRIEF, SOCIAL, FakeProvider, smart_text


def use(monkeypatch, *providers):
    monkeypatch.setattr(llm, "available_providers", lambda: list(providers))
    import quillframe.compare as compare_module

    monkeypatch.setattr(compare_module, "available_providers", lambda: list(providers))


def test_brief_coerces_string_into_list():
    data = {**BRIEF, "slogans": "Just one", "image_prompts": "just one prompt"}
    brief = CampaignBrief.model_validate(data)
    assert brief.slogans == ["Just one"] and brief.image_prompts == ["just one prompt"]


def test_brief_attempts_mark_valid_and_invalid(monkeypatch):
    good = FakeProvider("good", text=f"```json\n{json.dumps(BRIEF)}\n```")
    broken = FakeProvider("broken", text="I cannot do that")
    failing = FakeProvider("failing", error="boom")
    use(monkeypatch, good, broken, failing)

    attempts = asyncio.run(generate_brief_attempts("a brand brief for testing"))
    assert [a.valid for a in attempts] == [True, False, False]
    assert attempts[2].parse_error.startswith("RuntimeError: boom")
    assert pick_brief(attempts).result.provider == "good"


def test_pick_brief_raises_when_nothing_valid(monkeypatch):
    use(monkeypatch, FakeProvider("a", text="nope"), FakeProvider("b", error="down"))
    attempts = asyncio.run(generate_brief_attempts("a brand brief for testing"))
    with pytest.raises(RuntimeError, match="No model returned valid output"):
        pick_brief(attempts)


def test_no_providers_raises_helpful_error(monkeypatch):
    use(monkeypatch)
    with pytest.raises(NoProvidersError, match=".env"):
        asyncio.run(compare("hello"))


def test_social_falls_back_to_next_provider(monkeypatch):
    use(monkeypatch, FakeProvider("first", text="not json"), FakeProvider("second", text=json.dumps(SOCIAL)))
    brief = CampaignBrief.model_validate(BRIEF)
    pack, attempts = asyncio.run(generate_social(brief, "brand"))
    assert [a.valid for a in attempts] == [False, True]
    assert pack.instagram.hashtags == ["#riverlights", "#film"]


def test_hashtag_normalization():
    assert Post(caption="x", hashtags="one, #two  three").hashtags == ["#one", "#two", "#three"]
    assert isinstance(SocialPack.model_validate(SOCIAL), SocialPack)
