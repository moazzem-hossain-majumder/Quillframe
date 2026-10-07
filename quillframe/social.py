"""Social media pack: platform-specific captions and hashtags for a campaign."""
from __future__ import annotations

from pydantic import BaseModel, field_validator

from quillframe.brief import CampaignBrief
from quillframe.llm import JsonAttempt, run_json_first


class Post(BaseModel):
    caption: str
    hashtags: list[str] = []

    @field_validator("hashtags", mode="before")
    @classmethod
    def _normalize_hashtags(cls, value):
        if isinstance(value, str):
            value = value.replace(",", " ").split()
        return ["#" + str(tag).lstrip("#").strip() for tag in value if str(tag).strip("# ")]


class SocialPack(BaseModel):
    instagram: Post
    linkedin: Post
    x: Post
    facebook: Post


def build_social_prompt(brief: CampaignBrief, brand_brief: str) -> str:
    slogans = "\n".join(f"- {s}" for s in brief.slogans)
    return f"""You are a social media strategist. Write a launch post for each platform.

BRAND BRIEF: {brand_brief}
CAMPAIGN: {brief.campaign_name}
CONCEPT: {brief.concept}
TONE: {brief.tone}
AUDIENCE: {brief.audience}
SLOGANS:
{slogans}

Return ONLY a JSON object with keys "instagram", "linkedin", "x" and "facebook".
Each value is an object with:
- "caption": the post text
- "hashtags": a list of hashtags

Platform rules:
- instagram: energetic, a few emojis, 5-8 hashtags
- linkedin: professional and insightful, no emojis, 3-5 hashtags
- x: at most 240 characters in the caption, 1-2 hashtags
- facebook: friendly and conversational, 2-3 hashtags
"""


async def generate_social(
    brief: CampaignBrief, brand_brief: str
) -> tuple[SocialPack, list[JsonAttempt]]:
    return await run_json_first(build_social_prompt(brief, brand_brief), SocialPack)
