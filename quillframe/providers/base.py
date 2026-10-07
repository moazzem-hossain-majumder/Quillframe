from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass


@dataclass
class GenResult:
    provider: str
    model: str
    text: str = ""
    latency_s: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class TextProvider(ABC):
    """A text-generation backend. Subclasses implement _call(); generate() never raises."""

    name: str
    model: str

    @abstractmethod
    async def _call(self, prompt: str, json_mode: bool) -> str:
        """Call the provider's API and return the generated text."""

    async def generate(self, prompt: str, json_mode: bool = False) -> GenResult:
        start = time.perf_counter()
        try:
            text = await self._call(prompt, json_mode)
            return GenResult(self.name, self.model, text=text, latency_s=time.perf_counter() - start)
        except Exception as e:  # noqa: BLE001 - failures are data for the comparison, not crashes
            message = f"{type(e).__name__}: {e}".rstrip(": ")
            return GenResult(self.name, self.model, error=message, latency_s=time.perf_counter() - start)
