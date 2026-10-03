"""Comprehensive test suite for OmniGotchi with WiFi Auditor and BLE Radar."""

import asyncio
import os
import tempfile
import unittest
from PIL import Image

from omnigotchi.config import GotchiConfig
from omnigotchi.core.brain import GotchiBrain, GotchiState
from omnigotchi.display.mock_driver import MockEPaperDriver
from omnigotchi.display.renderer import GotchiRenderer
from omnigotchi.modules.audio_module import AudioModule
from omnigotchi.modules.ble_radar import BleRadar
from omnigotchi.modules.bounty_engine import BountyEngine
from omnigotchi.modules.dev_module import DevModule
from omnigotchi.modules.net_module import NetModule
from omnigotchi.modules.security_module import SecurityModule
from omnigotchi.modules.wifi_auditor import WiFiAuditor


class TestOmniGotchi(unittest.IsolatedAsyncioTestCase):

    def test_brain_state_and_leveling(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            state_file = tf.name

        try:
            brain = GotchiBrain(state_file=state_file, name="OmniTest")
            self.assertEqual(brain.state.name, "OmniTest")
            self.assertEqual(brain.state.level, 1)
            self.assertEqual(brain.state.xp, 0)

            # Gain XP without level up
            leveled = brain.gain_xp(50, "test")
            self.assertFalse(leveled)
            self.assertEqual(brain.state.xp, 50)
            self.assertEqual(brain.state.level, 1)

            # Gain XP with level up (threshold is 100)
            leveled = brain.gain_xp(60, "test")
            self.assertTrue(leveled)
            self.assertEqual(brain.state.level, 2)
            self.assertEqual(brain.state.xp, 10)

            # Test siphon and overclock
            initial_siphon = brain.state.siphon_power
            brain.siphon(20)
            self.assertGreaterEqual(brain.state.siphon_power, initial_siphon)
            self.assertEqual(brain.state.total_siphons, 1)

            brain.overclock()
            self.assertEqual(brain.state.overclock_level, 2)

            # Test 3-way display mode cycle
            self.assertEqual(brain.state.display_mode, "infiltrator")
            mode = brain.toggle_display_mode()
            self.assertEqual(mode, "sentinel")
            mode = brain.toggle_display_mode()
            self.assertEqual(mode, "terminal")
            mode = brain.toggle_display_mode()
            self.assertEqual(mode, "infiltrator")

            # Verify state reloaded from file correctly
            brain2 = GotchiBrain(state_file=state_file, name="OmniTest")
            self.assertEqual(brain2.state.level, 2)
            self.assertEqual(brain2.state.total_siphons, 1)
            self.assertEqual(brain2.state.overclock_level, 2)
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)

    def test_mood_resolution(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            state_file = tf.name

        try:
            brain = GotchiBrain(state_file=state_file)

            # 1. Test music playing -> MUSIC / DANCING
            dev_data = {"recent_commits_24h": 0, "is_active_repo": False}
            audio_data = {"is_playing": True, "title": "IGOR'S THEME", "artist": "Tyler, The Creator"}
            net_data = {"ping_ms": 15.0, "is_offline": False}

            brain.resolve_mood(dev_data, audio_data, net_data)
            self.assertIn(brain.state.mood, ("MUSIC", "DANCING"))

            # 2. Test high ping / lagging -> LAGGING
            audio_data["is_playing"] = False
            net_data["ping_ms"] = 500.0
            brain.resolve_mood(dev_data, audio_data, net_data)
            self.assertEqual(brain.state.mood, "LAGGING")

            # 3. Test active coding -> CODING
            net_data["ping_ms"] = 20.0
            dev_data["recent_commits_24h"] = 5
            dev_data["is_active_repo"] = True
            brain.resolve_mood(dev_data, audio_data, net_data)
            self.assertEqual(brain.state.mood, "CODING")

            # 4. Test security alert -> DEFCON
            sec_data = {"defcon_level": 2, "defcon_status": "EVIL TWIN DETECTED", "evil_twin_detected": True}
            brain.resolve_mood(dev_data, audio_data, net_data, security_data=sec_data)
            self.assertEqual(brain.state.mood, "DEFCON")
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)

    def test_canvas_renderer(self):
        renderer = GotchiRenderer(width=250, height=122)
        state = GotchiState(
            name="Omni",
            level=3,
            xp=45,
            xp_next=100,
            mood="HAPPY",
            face="( ^ _ ^ )",
            quote="Testing 1-bit E-Ink graphics!",
        )
        dev_data = {"recent_commits_24h": 2, "followers": 24, "streak_days": 5}
        audio_data = {"is_playing": False}
        net_data = {"ping_ms": 18.2, "cpu_pct": 14, "temp_c": 42.0, "ram_pct": 28}
        sec_data = {"defcon_level": 5, "lan_hosts_count": 8, "wifi_aps_count": 3}

        # Infiltrator mode (default)
        state.display_mode = "infiltrator"
        img = renderer.render(state, dev_data, audio_data, net_data, sec_data)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (250, 122))
        self.assertEqual(img.mode, "1")

        # Sentinel mode
        state.display_mode = "sentinel"
        img_sentinel = renderer.render(state, dev_data, audio_data, net_data, sec_data)
        self.assertIsInstance(img_sentinel, Image.Image)
        self.assertEqual(img_sentinel.size, (250, 122))
        self.assertEqual(img_sentinel.mode, "1")

        # Terminal mode
        state.display_mode = "terminal"
        img_term = renderer.render(state, dev_data, audio_data, net_data, sec_data)
        self.assertIsInstance(img_term, Image.Image)
        self.assertEqual(img_term.size, (250, 122))
        self.assertEqual(img_term.mode, "1")

    def test_mock_driver_and_ascii(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            preview_path = tf.name

        try:
            driver = MockEPaperDriver(width=250, height=122, preview_path=preview_path)
            renderer = GotchiRenderer(width=250, height=122)
            state = GotchiState()
            img = renderer.render(state, {}, {}, {"ping_ms": 12})

            driver.display(img)
            self.assertTrue(os.path.exists(preview_path))
            self.assertGreater(os.path.getsize(preview_path), 0)

            ascii_output = driver.render_ascii_terminal(img)
            self.assertIsInstance(ascii_output, str)
            self.assertGreater(len(ascii_output), 100)
            self.assertIn("┌", ascii_output)
            self.assertIn("└", ascii_output)
        finally:
            if os.path.exists(preview_path):
                os.unlink(preview_path)

    async def test_wifi_auditor_and_wardriving(self):
        auditor = WiFiAuditor()
        res = await auditor.scan_and_audit()
        self.assertIsInstance(res, dict)
        self.assertIn("posture", res)
        self.assertIn("spectrum", res)
        self.assertIn("clones", res)

        csv_out = auditor.export_wigle_csv()
        self.assertIn("WigleWifi-1.4", csv_out)

    async def test_ble_radar(self):
        radar = BleRadar()
        res = await radar.scan(duration_s=0.5)
        self.assertIsInstance(res, dict)
        self.assertIn("flood_detected", res)
        self.assertIn("flood_alert_msg", res)

    async def test_modules_polling(self):
        dev_mod = DevModule(username="DRNZY")
        dev_stats = await dev_mod.poll()
        self.assertIsInstance(dev_stats, dict)
        self.assertIn("followers", dev_stats)
        self.assertIn("recent_commits_24h", dev_stats)

        audio_mod = AudioModule(cadence_url="http://127.0.0.1:9999")
        audio_stats = await audio_mod.poll()
        self.assertIsInstance(audio_stats, dict)
        self.assertIsInstance(audio_stats["is_playing"], bool)

        net_mod = NetModule(target_host="1.1.1.1")
        net_stats = await net_mod.poll()
        self.assertIsInstance(net_stats, dict)
        self.assertIn("ping_ms", net_stats)
        self.assertIn("cpu_pct", net_stats)

        sec_mod = SecurityModule()
        sec_stats = await sec_mod.poll()
        self.assertIsInstance(sec_stats, dict)
        self.assertIn("defcon_level", sec_stats)
        self.assertIn("lan_hosts_count", sec_stats)
        self.assertIn("wifi_aps_count", sec_stats)
        self.assertIn("active_shields", sec_stats)

    async def test_bounty_engine_and_yield_ledger(self):
        engine = BountyEngine()
        initial_usd = engine.ledger.total_usd_earned
        
        # Test yield tick
        engine.tick_yield(elapsed_sec=60.0, rx_kbps=120.0, tx_kbps=45.0)
        self.assertGreater(engine.ledger.total_usd_earned, initial_usd)
        self.assertGreater(engine.ledger.total_relayed_mb, 0.0)
        self.assertGreaterEqual(engine.ledger.total_compute_shares, 1)

        # Test vulnerability scan and report generation
        report = await engine.scan_vulnerabilities()
        self.assertIsNotNone(report)
        self.assertTrue(report.id.startswith("DEDSEC-"))
        self.assertGreaterEqual(report.total_findings, 1)
        self.assertIsInstance(report.summary, str)

        stats = engine.get_stats()
        self.assertIn("ledger", stats)
        self.assertIn("latest_report", stats)
        self.assertEqual(stats["latest_report"]["id"], report.id)


if __name__ == "__main__":
    unittest.main()
