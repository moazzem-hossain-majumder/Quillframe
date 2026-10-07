"""Campaign brief engine: turn a short brand brief into a structured creative concept."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from quillframe.llm import JsonAttempt, run_json_all, summarize_failures


def _as_list(value):
    """Models sometimes return a single string where a list is expected."""
    if isinstance(value, str):
        return [value]
    return value


class CampaignBrief(BaseModel):
    campaign_name: str
    concept: str
    tone: str
    audience: str
    slogans: list[str] = Field(min_length=1)
    visual_direction: str
    image_prompts: list[str] = Field(min_length=1)
    voiceover_script: str

    _wrap_slogans = field_validator("slogans", mode="before")(_as_list)
    _wrap_prompts = field_validator("image_prompts", mode="before")(_as_list)


def build_brief_prompt(brand_brief: str) -> str:
    return f"""You are a creative director at an animation and creative-technology studio.
Turn the brand brief below into a campaign concept.

BRAND BRIEF:
{brand_brief}

Return ONLY a JSON object with exactly these keys:
- "campaign_name": a short, memorable campaign name
- "concept": 2-3 sentences describing the big idea
- "tone": a few adjectives describing the voice
- "audience": who the campaign speaks to
- "slogans": a list of 3 distinct slogans
- "visual_direction": 1-2 sentences on look and feel (palette, mood, style)
- "image_prompts": a list of 3 detailed, standalone text-to-image prompts. Describe subject,
  composition, lighting and style. Do not ask for any text, letters or logos inside the images.
- "voiceover_script": a 40-60 word spoken script, plain sentences only, no stage directions
"""


async def generate_brief_attempts(brand_brief: str) -> list[JsonAttempt]:
    """Run the brief prompt on every available model (this doubles as the model comparison)."""
    return await run_json_all(build_brief_prompt(brand_brief), CampaignBrief)


def pick_brief(attempts: list[JsonAttempt]) -> JsonAttempt:
    """Choose the first valid attempt (providers are ordered primary-first)."""
    for attempt in attempts:
        if attempt.valid:
            return attempt
    raise RuntimeError(summarize_failures(attempts))
