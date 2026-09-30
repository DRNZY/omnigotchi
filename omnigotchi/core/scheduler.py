"""Main Async Engine and Multi-Task Scheduler for OmniGotchi with Cybersecurity Sentinel."""

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
from omnigotchi.modules.security_module import SecurityModule
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
        self.security_module = SecurityModule()

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
        self.security_data = {}
        self.current_image: Optional[Image.Image] = None
        self.partial_count = 0
        self.running = False
        self.render_lock = asyncio.Lock()

    async def start(self):
        """Starts all async polling and rendering tasks."""
        self.running = True
        logger.info(f"Starting OmniGotchi engine with Cyber Sentinel (Hardware={self.use_hardware})...")

        # Initial fast telemetry poll
        self.dev_data = await self.dev_module.poll()
        self.audio_data = await self.audio_module.poll()
        self.net_data = await self.net_module.poll()
        self.security_data = await self.security_module.poll()

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
            asyncio.create_task(self._security_worker()),
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

    def flip_screen(self) -> int:
        """Toggles rotation between 0 and 180 degrees and refreshes screen."""
        cur = self.brain.state.rotation
        new_rot = 180 if cur == 0 else 0
        self.brain.state.rotation = new_rot
        self.brain._save()
        self.trigger_render(partial=False)
        logger.info(f"Screen flipped to {new_rot} degrees")
        return new_rot

    def toggle_display_mode(self) -> str:
        """Toggles display mode between 'companion' and 'sentinel'."""
        mode = self.brain.toggle_display_mode()
        self.trigger_render(partial=False)
        logger.info(f"Display mode switched to {mode}")
        return mode

    async def scan_security(self) -> dict:
        """Triggers an on-demand deep cybersecurity scan and updates display."""
        self.security_data = await self.security_module.poll()
        self.brain.record_security_scan(
            self.security_data.get("defcon_level", 5),
            self.security_data.get("defcon_status", "SECURE"),
        )
        self.trigger_render(partial=False)
        return self.security_data

    async def audit_wifi(self) -> dict:
        """Triggers an on-demand deep Wi-Fi security audit and awards XP."""
        wifi_data = await self.security_module.wifi_auditor.scan_and_audit()
        self.security_data["wifi_posture"] = wifi_data["posture"]
        self.security_data["connected_wifi_audit"] = wifi_data["connected_audit"]
        self.security_data["channel_spectrum"] = wifi_data["spectrum"]
        self.brain.gain_xp(25, "wifi_audit")
        self.trigger_render(partial=False)
        return wifi_data

    async def scan_ble(self) -> dict:
        """Triggers an on-demand BLE radar scan and awards XP."""
        ble_data = await self.security_module.ble_radar.scan()
        self.security_data["ble_devices_count"] = ble_data["total_devices_seen"]
        self.security_data["ble_devices"] = ble_data["recent_devices"]
        self.security_data["ble_flood_detected"] = ble_data["flood_detected"]
        self.security_data["ble_alert_msg"] = ble_data["flood_alert_msg"]
        self.brain.gain_xp(20, "ble_scan")
        self.trigger_render(partial=False)
        return ble_data

    def recover_display(self):
        """Forces display driver recovery and redraws full frame."""
        if hasattr(self.display_driver, "recover"):
            self.display_driver.recover()
        self.trigger_render(partial=False)

    def trigger_render(self, partial: bool = True):
        """Immediately renders and updates image cache & physical display."""
        try:
            self.brain.resolve_mood(
                self.dev_data,
                self.audio_data,
                self.net_data,
                self.security_data,
            )
            img = self.renderer.render(
                self.brain.state,
                self.dev_data,
                self.audio_data,
                self.net_data,
                self.security_data,
            )

            # Web & OmniHUD mirror image (always straight and upright on computer)
            self.current_image = img

            # Physical hardware display image (rotated to match IRL HAT orientation)
            hw_img = img
            if self.brain.state.rotation != 0:
                hw_img = img.rotate(self.brain.state.rotation, expand=False)

            # Determine full vs partial refresh
            self.partial_count += 1
            is_partial = partial and (self.partial_count < self.config.partial_refresh_limit)
            if not is_partial:
                self.partial_count = 0

            self.display_driver.display(hw_img, partial=is_partial)
        except Exception as e:
            logger.error(f"Render trigger failed: {e}")

    async def _render_worker(self):
        while self.running:
            try:
                self.trigger_render(partial=True)
            except Exception as e:
                logger.error(f"Render error: {e}")
            await asyncio.sleep(self.config.screen_refresh_interval)

    async def _security_worker(self):
        while self.running:
            try:
                self.security_data = await self.security_module.poll()
            except Exception as e:
                logger.debug(f"Security worker poll error: {e}")
            await asyncio.sleep(20.0)

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
