#!/usr/bin/env python3
"""Run OmniGotchi in Desktop Simulator mode with instant terminal and web preview."""

import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from omnigotchi.config import GotchiConfig
from omnigotchi.core.scheduler import GotchiEngine


async def run_simulator():
    print("\n========================================================")
    print("      OmniGotchi E-Ink Desktop Simulator & Live Mirror   ")
    print("========================================================")
    print("-> Web Dashboard & Screen Mirror: http://localhost:8000")
    print("-> Resolution: 250 x 122 (1-bit monochrome)")
    print("-> Press Ctrl+C to stop.\n")

    config = GotchiConfig.load()
    config.web_port = 8000
    config.screen_refresh_interval = 2.0

    engine = GotchiEngine(config=config, use_hardware=False)

    orig_trigger = engine.trigger_render

    def preview_trigger(partial=True):
        orig_trigger(partial=partial)
        if hasattr(engine.display_driver, "render_ascii_terminal"):
            ascii_art = engine.display_driver.render_ascii_terminal()
            sys.stdout.write("\033[2J\033[H")  # Clear screen
            sys.stdout.write(ascii_art + "\n")
            sys.stdout.write(f"OmniGotchi Live | Level {engine.brain.state.level} ({engine.brain.state.title}) | Mood: {engine.brain.state.mood}\n")
            sys.stdout.write("Web Mirror: http://localhost:8000\n")
            sys.stdout.flush()

    engine.trigger_render = preview_trigger

    try:
        await engine.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(run_simulator())
