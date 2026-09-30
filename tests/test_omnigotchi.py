"""Comprehensive test suite for OmniGotchi."""

import os
import tempfile
import pytest
from PIL import Image

from omnigotchi.config import GotchiConfig
from omnigotchi.core.brain import GotchiBrain, GotchiState
from omnigotchi.display.mock_driver import MockEPaperDriver
from omnigotchi.display.renderer import GotchiRenderer
from omnigotchi.modules.audio_module import AudioModule
from omnigotchi.modules.dev_module import DevModule
from omnigotchi.modules.net_module import NetModule
from omnigotchi.modules.security_module import SecurityModule


def test_brain_state_and_leveling():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        state_file = tf.name

    try:
        brain = GotchiBrain(state_file=state_file, name="OmniTest")
        assert brain.state.name == "OmniTest"
        assert brain.state.level == 1
        assert brain.state.xp == 0

        # Gain XP without level up
        leveled = brain.gain_xp(50, "test")
        assert not leveled
        assert brain.state.xp == 50
        assert brain.state.level == 1

        # Gain XP with level up (threshold is 100)
        leveled = brain.gain_xp(60, "test")
        assert leveled
        assert brain.state.level == 2
        assert brain.state.xp == 10

        # Test feeding and petting
        initial_hunger = brain.state.hunger
        brain.feed(20)
        assert brain.state.hunger >= initial_hunger
        assert brain.state.total_feeds == 1

        brain.pet()
        assert brain.state.total_pets == 1

        # Test display mode toggle
        mode = brain.toggle_display_mode()
        assert mode == "sentinel"
        mode = brain.toggle_display_mode()
        assert mode == "companion"

        # Verify state reloaded from file correctly
        brain2 = GotchiBrain(state_file=state_file, name="OmniTest")
        assert brain2.state.level == 2
        assert brain2.state.total_feeds == 1
        assert brain2.state.total_pets == 1
    finally:
        if os.path.exists(state_file):
            os.unlink(state_file)


def test_mood_resolution():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        state_file = tf.name

    try:
        brain = GotchiBrain(state_file=state_file)

        # 1. Test music playing -> MUSIC / DANCING
        dev_data = {"recent_commits_24h": 0, "is_active_repo": False}
        audio_data = {"is_playing": True, "title": "IGOR'S THEME", "artist": "Tyler, The Creator"}
        net_data = {"ping_ms": 15.0, "is_offline": False}

        brain.resolve_mood(dev_data, audio_data, net_data)
        assert brain.state.mood in ("MUSIC", "DANCING")

        # 2. Test high ping / lagging -> LAGGING
        audio_data["is_playing"] = False
        net_data["ping_ms"] = 500.0
        brain.resolve_mood(dev_data, audio_data, net_data)
        assert brain.state.mood == "LAGGING"

        # 3. Test active coding -> CODING
        net_data["ping_ms"] = 20.0
        dev_data["recent_commits_24h"] = 5
        dev_data["is_active_repo"] = True
        brain.resolve_mood(dev_data, audio_data, net_data)
        assert brain.state.mood == "CODING"

        # 4. Test security alert -> DEFCON
        sec_data = {"defcon_level": 2, "defcon_status": "EVIL TWIN DETECTED", "evil_twin_detected": True}
        brain.resolve_mood(dev_data, audio_data, net_data, security_data=sec_data)
        assert brain.state.mood == "DEFCON"
    finally:
        if os.path.exists(state_file):
            os.unlink(state_file)


def test_canvas_renderer():
    renderer = GotchiRenderer(width=250, height=122)
    state = GotchiState(
        name="Omni",
        level=3,
        xp=45,
        xp_next=100,
        mood="HAPPY",
        face="( ^‿^ )",
        quote="Testing 1-bit E-Ink graphics!",
    )
    dev_data = {"recent_commits_24h": 2, "followers": 24, "streak_days": 5}
    audio_data = {"is_playing": False}
    net_data = {"ping_ms": 18.2, "cpu_pct": 14, "temp_c": 42.0, "ram_pct": 28}
    sec_data = {"defcon_level": 5, "lan_hosts_count": 8, "wifi_aps_count": 3}

    # Companion mode
    img = renderer.render(state, dev_data, audio_data, net_data, sec_data)
    assert isinstance(img, Image.Image)
    assert img.size == (250, 122)
    assert img.mode == "1"

    # Sentinel mode
    state.display_mode = "sentinel"
    img_sentinel = renderer.render(state, dev_data, audio_data, net_data, sec_data)
    assert isinstance(img_sentinel, Image.Image)
    assert img_sentinel.size == (250, 122)
    assert img_sentinel.mode == "1"


def test_mock_driver_and_ascii():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        preview_path = tf.name

    try:
        driver = MockEPaperDriver(width=250, height=122, preview_path=preview_path)
        renderer = GotchiRenderer(width=250, height=122)
        state = GotchiState()
        img = renderer.render(state, {}, {}, {"ping_ms": 12})

        driver.display(img)
        assert os.path.exists(preview_path)
        assert os.path.getsize(preview_path) > 0

        ascii_output = driver.render_ascii_terminal(img)
        assert isinstance(ascii_output, str)
        assert len(ascii_output) > 100
        assert "┌" in ascii_output
        assert "└" in ascii_output
    finally:
        if os.path.exists(preview_path):
            os.unlink(preview_path)


@pytest.mark.asyncio
async def test_modules_polling():
    dev_mod = DevModule(username="DRNZY")
    dev_stats = await dev_mod.poll()
    assert isinstance(dev_stats, dict)
    assert "followers" in dev_stats
    assert "recent_commits_24h" in dev_stats

    audio_mod = AudioModule(cadence_url="http://127.0.0.1:9999")
    audio_stats = await audio_mod.poll()
    assert isinstance(audio_stats, dict)
    assert audio_stats["is_playing"] is False

    net_mod = NetModule(target_host="1.1.1.1")
    net_stats = await net_mod.poll()
    assert isinstance(net_stats, dict)
    assert "ping_ms" in net_stats
    assert "cpu_pct" in net_stats

    sec_mod = SecurityModule()
    sec_stats = await sec_mod.poll()
    assert isinstance(sec_stats, dict)
    assert "defcon_level" in sec_stats
    assert "lan_hosts_count" in sec_stats
    assert "wifi_aps_count" in sec_stats
    assert "active_shields" in sec_stats
