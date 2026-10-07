"""Central configuration. Values come from environment variables or a local .env file."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# utf-8-sig tolerates the invisible BOM that Windows Notepad can add to .env files
load_dotenv(ROOT / ".env", encoding="utf-8-sig")
load_dotenv(encoding="utf-8-sig")  # also honour a .env in the current working directory


def _get(name: str, default: str | None = None) -> str | None:
    """Read an env var; empty or whitespace-only values count as unset."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _get_int(name: str, default: int) -> int:
    try:
        return int(_get(name, str(default)))
    except ValueError:
        return default


# --- Text models (all have a free tier) ------------------------------------
GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")

GROQ_API_KEY = _get("GROQ_API_KEY")
GROQ_MODEL = _get("GROQ_MODEL", "llama-3.3-70b-versatile")

OPENROUTER_API_KEY = _get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = _get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# Provider tried first when a single answer is needed (gemini | groq | openrouter)
TEXT_PRIMARY = _get("TEXT_PRIMARY", "gemini")

# --- Images ----------------------------------------------------------------
POLLINATIONS_MODEL = _get("POLLINATIONS_MODEL", "flux")
HF_TOKEN = _get("HF_TOKEN")
HF_IMAGE_MODEL = _get("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
IMAGES_PER_CAMPAIGN = _get_int("IMAGES_PER_CAMPAIGN", 2)

# --- Voice -----------------------------------------------------------------
EDGE_TTS_VOICE = _get("EDGE_TTS_VOICE", "en-US-AriaNeural")

# --- Output ----------------------------------------------------------------
_out = Path(_get("OUTPUT_DIR", "outputs"))
OUTPUT_DIR = _out if _out.is_absolute() else ROOT / _out
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
