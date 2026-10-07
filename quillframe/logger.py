"""Experiment logger: turns every run into a markdown report comparing the tools used."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from quillframe.images import ImageResult
from quillframe.llm import JsonAttempt
from quillframe.voice import VoiceResult


def _cell(value, limit: int = 90) -> str:
    text = str(value if value is not None else "").replace("|", "\\|").replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


class ExperimentLog:
    def __init__(self, title: str, brand_brief: str) -> None:
        self.title = title
        self.brand_brief = brand_brief
        self.created = datetime.now().astimezone()
        self._sections: list[str] = []

    def add_text_comparison(self, heading: str, attempts: list[JsonAttempt], chosen: str | None) -> None:
        rows = []
        for a in attempts:
            first_slogan = ""
            if a.valid and hasattr(a.parsed, "slogans"):
                first_slogan = a.parsed.slogans[0]
            rows.append(
                [
                    a.result.provider,
                    a.result.model,
                    f"{a.result.latency_s:.2f}",
                    "yes" if a.valid else "no",
                    first_slogan or (a.parse_error or ""),
                ]
            )
        body = _table(["Provider", "Model", "Latency (s)", "Valid output", "First slogan / error"], rows)
        valid = [a for a in attempts if a.valid]
        notes = [f"- Schema-valid answers: {len(valid)}/{len(attempts)}"]
        if valid:
            fastest = min(valid, key=lambda a: a.result.latency_s)
            notes.append(f"- Fastest valid answer: {fastest.result.provider} ({fastest.result.latency_s:.2f}s)")
        if chosen:
            notes.append(f"- Used for the campaign: {chosen}")
        self._sections.append(f"## {heading}\n\n{body}\n\n" + "\n".join(notes))

    def add_social(self, attempts: list[JsonAttempt] | None, error: str | None = None) -> None:
        if not attempts:
            self._sections.append(f"## Social media pack\n\nSkipped: {error or 'no output'}")
            return
        rows = [
            [a.result.provider, a.result.model, f"{a.result.latency_s:.2f}", "yes" if a.valid else "no", a.parse_error or ""]
            for a in attempts
        ]
        table = _table(["Provider", "Model", "Latency (s)", "Valid output", "Error"], rows)
        self._sections.append(f"## Social media pack\n\nProviders were tried in order until one gave valid output.\n\n{table}")

    def add_images(self, results: list[ImageResult]) -> None:
        if not results:
            self._sections.append("## Image generation\n\nSkipped (0 images requested).")
            return
        rows = []
        for r in results:
            link = f"[{Path(r.path).name}](images/{Path(r.path).name})" if r.path else ""
            rows.append([r.provider, r.model, r.index, f"{r.latency_s:.2f}", link or "failed", r.error or "", r.prompt])
        table = _table(["Provider", "Model", "Prompt #", "Latency (s)", "File", "Error", "Prompt"], rows)
        notes = []
        for provider in dict.fromkeys(r.provider for r in results):
            group = [r for r in results if r.provider == provider]
            ok = [r for r in group if r.path]
            line = f"- {provider}: {len(ok)}/{len(group)} succeeded"
            if ok:
                line += f", average {sum(r.latency_s for r in ok) / len(ok):.2f}s per image"
            notes.append(line)
        self._sections.append(f"## Image generation\n\n{table}\n\n" + "\n".join(notes))

    def add_voice(self, result: VoiceResult) -> None:
        if result.path:
            detail = f"- Voice: `{result.voice}`\n- Latency: {result.latency_s:.2f}s\n- File: [{Path(result.path).name}]({Path(result.path).name})"
        else:
            detail = f"- Voice: `{result.voice}`\n- Failed: {result.error}"
        self._sections.append(f"## Voiceover (edge-tts)\n\n{detail}")

    def render(self, total_s: float | None = None) -> str:
        header = [
            f"# Experiment log: {self.title}",
            "",
            f"- Date: {self.created.strftime('%Y-%m-%d %H:%M %Z')}",
        ]
        if total_s is not None:
            header.append(f"- Total pipeline time: {total_s:.1f}s")
        header += ["", "**Brand brief**", "", "> " + self.brand_brief.replace("\n", "\n> "), ""]
        footer = [
            "## Your notes",
            "",
            "Add your own observations here (which model followed instructions best, which image looked best, what you would try next).",
            "",
            "- ",
        ]
        return "\n".join(header) + "\n" + "\n\n".join(self._sections + ["\n".join(footer)]) + "\n"

    def write(self, path: Path, total_s: float | None = None) -> Path:
        path.write_text(self.render(total_s), encoding="utf-8")
        return path
