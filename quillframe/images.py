"""Image generation with free providers, compared side by side."""
from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import quote

from quillframe import config
from quillframe.utils import http_client, raise_for_status_verbose, request_with_retry

_EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp"}


@dataclass
class ImageResult:
    provider: str
    model: str
    index: int
    prompt: str
    path: str | None = None
    latency_s: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _image_from_response(response) -> tuple[bytes, str]:
    raise_for_status_verbose(response)
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if not content_type.startswith("image/"):
        raise RuntimeError(f"expected an image but got '{content_type or 'unknown'}': {response.text[:150]}")
    return response.content, _EXTENSIONS.get(content_type, ".png")


class ImageProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def _fetch(self, prompt: str, seed: int) -> tuple[bytes, str]:
        """Return (image bytes, file extension)."""

    async def generate(self, prompt: str, out_stem: Path, index: int) -> ImageResult:
        start = time.perf_counter()
        try:
            data, ext = await self._fetch(prompt, seed=index)
            if len(data) < 500:
                raise RuntimeError("image response was suspiciously small")
            path = out_stem.with_suffix(ext)
            path.write_bytes(data)
            return ImageResult(self.name, self.model, index, prompt, str(path), time.perf_counter() - start)
        except Exception as e:  # noqa: BLE001
            message = f"{type(e).__name__}: {e}".rstrip(": ")
            return ImageResult(self.name, self.model, index, prompt, None, time.perf_counter() - start, message)


class PollinationsProvider(ImageProvider):
    """Pollinations.ai: free image generation that needs no API key."""

    name = "pollinations"

    def __init__(self) -> None:
        self.model = config.POLLINATIONS_MODEL

    async def _fetch(self, prompt: str, seed: int) -> tuple[bytes, str]:
        url = f"https://image.pollinations.ai/prompt/{quote(prompt[:600], safe='')}"
        params = {"width": 1024, "height": 1024, "model": self.model, "seed": seed, "nologo": "true"}
        async with http_client(timeout=120) as client:
            r = await request_with_retry(client, "GET", url, retries=3, params=params)
        return _image_from_response(r)


class HuggingFaceProvider(ImageProvider):
    """Hugging Face serverless inference (free token required)."""

    name = "huggingface"

    def __init__(self) -> None:
        self.model = config.HF_IMAGE_MODEL

    async def _fetch(self, prompt: str, seed: int) -> tuple[bytes, str]:
        url = f"https://router.huggingface.co/hf-inference/models/{self.model}"
        async with http_client(timeout=120) as client:
            r = await request_with_retry(
                client,
                "POST",
                url,
                retries=3,  # models can return 503 while they warm up
                headers={"Authorization": f"Bearer {config.HF_TOKEN}"},
                json={"inputs": prompt},
            )
        return _image_from_response(r)


def available_image_providers() -> list[ImageProvider]:
    providers: list[ImageProvider] = [PollinationsProvider()]
    if config.HF_TOKEN:
        providers.append(HuggingFaceProvider())
    return providers


async def generate_images(prompts: list[str], out_dir: Path, n: int | None = None) -> list[ImageResult]:
    """Generate up to n images per provider. Providers run concurrently, prompts sequentially
    per provider (free tiers rate-limit parallel requests)."""
    n = config.IMAGES_PER_CAMPAIGN if n is None else n
    prompts = prompts[: max(n, 0)]
    if not prompts:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)

    async def run(provider: ImageProvider) -> list[ImageResult]:
        results = []
        for i, prompt in enumerate(prompts, start=1):
            if i > 1:
                await asyncio.sleep(2.0)
            results.append(await provider.generate(prompt, out_dir / f"image_{i}_{provider.name}", i))
        return results

    groups = await asyncio.gather(*(run(p) for p in available_image_providers()))
    return [result for group in groups for result in group]
