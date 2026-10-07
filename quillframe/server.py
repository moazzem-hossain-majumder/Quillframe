"""FastAPI backend and static web UI."""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from quillframe import __version__, config
from quillframe.compare import compare
from quillframe.images import available_image_providers
from quillframe.pipeline import list_campaigns, run_campaign
from quillframe.providers import NoProvidersError, available_providers

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Quillframe", version=__version__, description="Multi-model creative AI workbench")


class CompareRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


class CampaignRequest(BaseModel):
    brief: str = Field(min_length=10, max_length=4000)
    images: int | None = Field(default=None, ge=0, le=3)
    voice: str | None = Field(default=None, max_length=100)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": __version__,
        "text": [{"provider": p.name, "model": p.model} for p in available_providers()],
        "image": [{"provider": p.name, "model": p.model} for p in available_image_providers()],
        "voice": {"engine": "edge-tts", "default_voice": config.EDGE_TTS_VOICE},
    }


@app.post("/api/compare")
async def api_compare(req: CompareRequest):
    try:
        results = await compare(req.prompt)
    except NoProvidersError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"results": [r.to_dict() for r in results]}


@app.post("/api/campaign")
async def api_campaign(req: CampaignRequest):
    try:
        return await run_campaign(req.brief, images=req.images, voice=req.voice)
    except NoProvidersError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@app.get("/api/campaigns")
async def api_campaigns():
    return {"campaigns": list_campaigns()}


@app.get("/api/campaigns/{run_id}/log", response_class=PlainTextResponse)
async def api_campaign_log(run_id: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise HTTPException(status_code=400, detail="invalid campaign id")
    path = config.OUTPUT_DIR / run_id / "EXPERIMENT_LOG.md"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="log not found")
    return path.read_text(encoding="utf-8")


app.mount("/outputs", StaticFiles(directory=config.OUTPUT_DIR), name="outputs")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")
