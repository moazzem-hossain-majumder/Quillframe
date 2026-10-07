"""Test doubles that stand in for real providers."""
import json

from quillframe.providers.base import GenResult, TextProvider

BRIEF = {
    "campaign_name": "River Lights",
    "concept": "A short film where the river itself tells the story.",
    "tone": "warm, curious",
    "audience": "young festival-goers",
    "slogans": ["Follow the current", "Stories flow", "Dive in"],
    "visual_direction": "Teal water, golden dusk light, painterly textures.",
    "image_prompts": ["a river at dusk, painterly", "paper boats on water, soft light", "city skyline reflected in a river"],
    "voiceover_script": "Every river has a story. This one is yours to follow.",
}

SOCIAL = {
    "instagram": {"caption": "Dive in!", "hashtags": ["riverlights", "#film"]},
    "linkedin": {"caption": "Introducing River Lights.", "hashtags": ["animation"]},
    "x": {"caption": "Follow the current.", "hashtags": ["#film"]},
    "facebook": {"caption": "Join us.", "hashtags": ["#riverlights"]},
}


class FakeProvider(TextProvider):
    def __init__(self, name, text=None, error=None):
        self.name = name
        self.model = f"{name}-model"
        self._text = text
        self._error = error

    async def _call(self, prompt, json_mode):
        if self._error:
            raise RuntimeError(self._error)
        if callable(self._text):
            return self._text(prompt)
        return self._text


def smart_text(prompt: str) -> str:
    """Return a social pack for social prompts and a brief otherwise."""
    return json.dumps(SOCIAL if "social media strategist" in prompt else BRIEF)


def ok_result(name="fake"):
    return GenResult(name, f"{name}-model", text="hello", latency_s=0.1)
