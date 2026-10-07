"""Voiceover with edge-tts (free, no API key; needs an internet connection)."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path

from quillframe import config


@dataclass
class VoiceResult:
    voice: str
    path: str | None = None
    latency_s: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


async def synthesize(text: str, out_path: Path, voice: str | None = None) -> VoiceResult:
    voice = voice or config.EDGE_TTS_VOICE
    start = time.perf_counter()
    try:
        import edge_tts  # imported lazily so the rest of the app works without it

        out_path.parent.mkdir(parents=True, exist_ok=True)
        await edge_tts.Communicate(text, voice).save(str(out_path))
        if not out_path.exists() or out_path.stat().st_size == 0:
            raise RuntimeError("no audio was produced")
        return VoiceResult(voice, str(out_path), time.perf_counter() - start)
    except Exception as e:  # noqa: BLE001
        message = f"{type(e).__name__}: {e}".rstrip(": ")
        return VoiceResult(voice, None, time.perf_counter() - start, message)
