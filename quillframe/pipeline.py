"""End-to-end campaign pipeline: brief -> (social + images + voiceover) -> experiment log."""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from quillframe import config
from quillframe.brief import generate_brief_attempts, pick_brief
from quillframe.images import generate_images
from quillframe.logger import ExperimentLog
from quillframe.social import generate_social
from quillframe.utils import slugify
from quillframe.voice import synthesize

Progress = Callable[[str], None]


def _rel(path: str | None, run_dir: Path) -> str | None:
    return Path(path).relative_to(run_dir).as_posix() if path else None


async def run_campaign(
    brand_brief: str,
    out_root: Path | None = None,
    images: int | None = None,
    voice: str | None = None,
    progress: Progress | None = None,
) -> dict:
    """Run the whole pipeline and return the manifest (also saved as result.json)."""
    say = progress or (lambda _msg: None)
    started = time.perf_counter()
    out_root = out_root or config.OUTPUT_DIR
    run_dir = out_root / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(brand_brief)}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Brief: every model gets the same prompt, which doubles as the model comparison.
    say("Asking every configured text model for a campaign brief...")
    attempts = await generate_brief_attempts(brand_brief)
    chosen = pick_brief(attempts)
    brief = chosen.parsed
    say(f"Brief ready: '{brief.campaign_name}' (using {chosen.result.provider})")

    # 2. Social pack, images and voiceover are independent, so run them together.
    say("Generating social posts, images and voiceover in parallel...")

    async def social_task():
        try:
            pack, social_attempts = await generate_social(brief, brand_brief)
            return pack, social_attempts, None
        except Exception as e:  # noqa: BLE001 - a failed social pack should not lose the campaign
            return None, None, str(e)

    (pack, social_attempts, social_error), image_results, voice_result = await asyncio.gather(
        social_task(),
        generate_images(brief.image_prompts, run_dir / "images", images),
        synthesize(brief.voiceover_script, run_dir / "voiceover.mp3", voice),
    )
    if pack is None:
        say(f"Social pack skipped: {social_error}")

    # 3. Persist everything.
    (run_dir / "brief.json").write_text(brief.model_dump_json(indent=2), encoding="utf-8")
    if pack is not None:
        (run_dir / "social.json").write_text(pack.model_dump_json(indent=2), encoding="utf-8")

    total = time.perf_counter() - started
    log = ExperimentLog(brief.campaign_name, brand_brief)
    log.add_text_comparison("Text model comparison (campaign brief)", attempts, chosen.result.provider)
    log.add_social(social_attempts, social_error)
    log.add_images(image_results)
    log.add_voice(voice_result)
    log.write(run_dir / "EXPERIMENT_LOG.md", total)

    manifest = {
        "id": run_dir.name,
        "created": datetime.now().astimezone().isoformat(timespec="seconds"),
        "brand_brief": brand_brief,
        "brief": brief.model_dump(),
        "brief_provider": chosen.result.provider,
        "text_comparison": [
            {
                "provider": a.result.provider,
                "model": a.result.model,
                "latency_s": round(a.result.latency_s, 2),
                "valid": a.valid,
                "error": a.parse_error,
                "first_slogan": a.parsed.slogans[0] if a.valid else None,
            }
            for a in attempts
        ],
        "social": pack.model_dump() if pack else None,
        "social_error": social_error,
        "images": [
            {
                "provider": r.provider,
                "model": r.model,
                "index": r.index,
                "prompt": r.prompt,
                "file": _rel(r.path, run_dir),
                "latency_s": round(r.latency_s, 2),
                "error": r.error,
            }
            for r in image_results
        ],
        "voice": {
            "voice": voice_result.voice,
            "file": _rel(voice_result.path, run_dir),
            "latency_s": round(voice_result.latency_s, 2),
            "error": voice_result.error,
        },
        "log_file": "EXPERIMENT_LOG.md",
        "total_s": round(total, 1),
    }
    (run_dir / "result.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    say(f"Done in {total:.1f}s. Output folder: {run_dir}")
    return manifest


def list_campaigns(out_root: Path | None = None) -> list[dict]:
    """Manifests of previous runs, newest first."""
    out_root = out_root or config.OUTPUT_DIR
    manifests = []
    for path in sorted(out_root.glob("*/result.json"), reverse=True):
        try:
            manifests.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return manifests
