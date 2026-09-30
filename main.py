#!/usr/bin/env python3
"""OmniGotchi CLI and Main Entrypoint."""

import argparse
import asyncio
import logging
import sys

from omnigotchi.config import GotchiConfig
from omnigotchi.core.scheduler import GotchiEngine


def parse_args():
    parser = argparse.ArgumentParser(description="OmniGotchi: Autonomous E-Ink Cyberpet")
    parser.add_argument("--hardware", action="store_true", help="Enable Waveshare E-Paper hardware output")
    parser.add_argument("--preview", action="store_true", help="Print live ANSI ASCII preview to terminal on tick")
    parser.add_argument("--port", type=int, default=8000, help="Web companion port (default: 8000)")
    parser.add_argument("--no-web", action="store_true", help="Disable web dashboard")
    parser.add_argument("--name", type=str, default="Omni", help="Gotchi pet name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging")
    return parser.parse_args()


async def main():
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = GotchiConfig.load()
    config.name = args.name
    config.web_port = args.port
    if args.no_web:
        config.web_enabled = False

    engine = GotchiEngine(config=config, use_hardware=args.hardware)

    if args.preview and not args.hardware:
        # Wrap trigger_render to also print ASCII preview to terminal
        orig_trigger = engine.trigger_render

        def preview_trigger(partial=True):
            orig_trigger(partial=partial)
            if hasattr(engine.display_driver, "render_ascii_terminal"):
                ascii_art = engine.display_driver.render_ascii_terminal()
                print("\033[2J\033[H" + ascii_art, flush=True)

        engine.trigger_render = preview_trigger

    try:
        await engine.start()
    except KeyboardInterrupt:
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
