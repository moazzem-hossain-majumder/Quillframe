"""Command-line interface: python -m quillframe <command>"""
from __future__ import annotations

import argparse
import asyncio
import sys

from quillframe import __version__, config
from quillframe.compare import compare
from quillframe.images import available_image_providers
from quillframe.providers import NoProvidersError, available_providers


def _cmd_compare(args: argparse.Namespace) -> None:
    for r in asyncio.run(compare(args.prompt)):
        print(f"\n=== {r.provider} ({r.model}) | {r.latency_s:.2f}s ===")
        print(f"ERROR: {r.error}" if r.error else r.text)


def _cmd_campaign(args: argparse.Namespace) -> None:
    from quillframe.pipeline import run_campaign

    manifest = asyncio.run(
        run_campaign(
            args.brief,
            images=args.images,
            voice=args.voice,
            progress=lambda msg: print(f"  - {msg}"),
        )
    )
    brief = manifest["brief"]
    print(f"\nCampaign: {brief['campaign_name']}")
    print(f"Concept:  {brief['concept']}")
    for slogan in brief["slogans"]:
        print(f"  * {slogan}")
    print(f"\nOpen the experiment log: {config.OUTPUT_DIR / manifest['id'] / manifest['log_file']}")


def _cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    from quillframe.server import app

    print(f"Quillframe UI: http://{args.host}:{args.port}  (Ctrl+C to stop)")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


def _cmd_status(_args: argparse.Namespace) -> None:
    providers = available_providers()
    print(f"Quillframe {__version__}")
    print("\nText models:")
    if providers:
        for p in providers:
            print(f"  [ok] {p.name:<11} {p.model}")
    else:
        print("  none configured. Copy .env.example to .env and add at least one key.")
    print("\nImage providers:")
    for p in available_image_providers():
        print(f"  [ok] {p.name:<12} {p.model}")
    if not config.HF_TOKEN:
        print("  [--] huggingface  (set HF_TOKEN to enable)")
    print(f"\nVoice:  edge-tts, voice {config.EDGE_TTS_VOICE}")
    print(f"Output: {config.OUTPUT_DIR}")


def _cmd_models(_args: argparse.Namespace) -> None:
    from quillframe.providers.gemini import list_models

    if not config.GEMINI_API_KEY:
        sys.exit("Set GEMINI_API_KEY in .env first.")
    for name in asyncio.run(list_models()):
        print(name)
    print("\nPut one of these names in GEMINI_MODEL in your .env file.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quillframe", description="Quillframe: a multi-model creative AI workbench (free-tier APIs)"
    )
    parser.add_argument("--version", action="version", version=f"quillframe {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("compare", help="send one prompt to every configured text model")
    p.add_argument("prompt")
    p.set_defaults(func=_cmd_compare)

    p = sub.add_parser("campaign", help="run the full campaign pipeline from a brand brief")
    p.add_argument("brief", help="a short description of the brand / product")
    p.add_argument("--images", type=int, default=None, help="images per provider (default from .env, usually 2)")
    p.add_argument("--voice", default=None, help="edge-tts voice, e.g. en-US-GuyNeural or bn-BD-NabanitaNeural")
    p.set_defaults(func=_cmd_campaign)

    p = sub.add_parser("serve", help="start the web UI and API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=_cmd_serve)

    p = sub.add_parser("status", help="show which providers are configured")
    p.set_defaults(func=_cmd_status)

    p = sub.add_parser("models", help="list Gemini models available to your API key")
    p.set_defaults(func=_cmd_models)
    return parser


def main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):  # keep Windows consoles from choking on emoji / non-ASCII
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except NoProvidersError as e:
        sys.exit(str(e))
    except RuntimeError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
