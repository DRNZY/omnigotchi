"""Main Async Engine and Multi-Task Scheduler for OmniGotchi."""

import asyncio
import logging
from typing import Optional
from PIL import Image

from omnigotchi.config import GotchiConfig
from omnigotchi.core.brain import GotchiBrain
from omnigotchi.display.mock_driver import MockEPaperDriver
from omnigotchi.display.renderer import GotchiRenderer
from omnigotchi.modules.audio_module import AudioModule
from omnigotchi.modules.dev_module import DevModule
from omnigotchi.modules.net_module import NetModule
from omnigotchi.web.server import GotchiWebServer

logger = logging.getLogger("omnigotchi.engine")


class GotchiEngine:
    def __init__(self, config: GotchiConfig, use_hardware: bool = False):
        self.config = config
        self.use_hardware = use_hardware
        
        # Core subsystems
        self.brain = GotchiBrain(state_file=config.state_file, name=config.name)
        self.renderer = GotchiRenderer(width=config.display_width, height=config.display_height)
        
        # Modules
        self.dev_module = DevModule(
            username=config.github_user,
            token=config.github_token,
            projects_dir=config.projects_dir,
        )
        self.audio_module = AudioModule(cadence_url=config.cadence_url)
        self.net_module = NetModule(target_host=config.ping_host, timeout_s=config.ping_timeout_s)

        # Display Driver
        if use_hardware:
            from omnigotchi.display.epaper_driver import EPaperHardwareDriver
            self.display_driver = EPaperHardwareDriver(
                model=config.epd_model,
                width=config.display_width,
                height=config.display_height,
            )
        else:
            self.display_driver = MockEPaperDriver(
                width=config.display_width,
                height=config.display_height,
            )

        # Web Companion
        self.web_server = None
        if config.web_enabled:
            self.web_server = GotchiWebServer(self, host=config.web_host, port=config.web_port)

        # Live telemetry caches
        self.dev_data = {}
        self.audio_data = {}
        self.net_data = {}
        self.current_image: Optional[Image.Image] = None
        self.partial_count = 0
        self.running = False

    async def start(self):
        """Starts all async polling and rendering tasks."""
        self.running = True
        logger.info(f"Starting OmniGotchi engine (Hardware={self.use_hardware})...")

        # Initial fast telemetry poll
        self.dev_data = await self.dev_module.poll()
        self.audio_data = await self.audio_module.poll()
        self.net_data = await self.net_module.poll()

        # Render first initial frame
        self.trigger_render(partial=False)

        # Start web companion if enabled
        if self.web_server:
            await self.web_server.start()

        # Spawn concurrent async worker tasks
        tasks = [
            asyncio.create_task(self._dev_worker()),
            asyncio.create_task(self._audio_worker()),
            asyncio.create_task(self._net_worker()),
            asyncio.create_task(self._render_worker()),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        if self.web_server:
            await self.web_server.stop()
        if hasattr(self.display_driver, "sleep"):
            self.display_driver.sleep()
        logger.info("OmniGotchi engine stopped cleanly.")

    def trigger_render(self, partial: bool = True):
        """Immediately renders and refreshes display."""
        self.brain.resolve_mood(self.dev_data, self.audio_data, self.net_data)
        img = self.renderer.render(
            self.brain.state,
            self.dev_data,
            self.audio_data,
            self.net_data,
        )
        self.current_image = img

        # Determine full vs partial refresh
        self.partial_count += 1
        is_partial = partial and (self.partial_count < self.config.partial_refresh_limit)
        if not is_partial:
            self.partial_count = 0

        self.display_driver.display(img, partial=is_partial)

    async def _render_worker(self):
        while self.running:
            try:
                self.trigger_render(partial=True)
            except Exception as e:
                logger.error(f"Render error: {e}")
            await asyncio.sleep(self.config.screen_refresh_interval)

    async def _dev_worker(self):
        while self.running:
            try:
                self.dev_data = await self.dev_module.poll()
            except Exception as e:
                logger.debug(f"Dev poll error: {e}")
            await asyncio.sleep(self.config.dev_poll_interval)

    async def _audio_worker(self):
        while self.running:
            try:
                self.audio_data = await self.audio_module.poll()
            except Exception as e:
                logger.debug(f"Audio poll error: {e}")
            await asyncio.sleep(self.config.audio_poll_interval)

    async def _net_worker(self):
        while self.running:
            try:
                self.net_data = await self.net_module.poll()
            except Exception as e:
                logger.debug(f"Net poll error: {e}")
            await asyncio.sleep(self.config.net_poll_interval)
