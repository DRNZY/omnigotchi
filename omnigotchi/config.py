"""OmniGotchi Configuration Module."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GotchiConfig:
    # Gotchi identity
    name: str = "Omni"
    personality: str = "curious"  # curious, sassy, chill, nerdy
    
    # User accounts & paths
    github_user: str = "DRNZY"
    github_token: str = os.environ.get("GITHUB_TOKEN", "")
    projects_dir: str = os.path.expanduser("~/Projects")
    
    # Cadence & Audio integration
    cadence_url: str = os.environ.get("CADENCE_URL", "http://127.0.0.1:3001")
    audio_enabled: bool = True
    
    # Network Sentinel targets
    ping_host: str = "1.1.1.1"
    ping_timeout_s: float = 1.5
    
    # Display configuration (Waveshare 2.13" / 2.14" E-Ink standard)
    display_width: int = 250
    display_height: int = 122
    rotation: int = 0  # 0, 90, 180, 270
    epd_model: str = "2in13_V4"  # 2in13_V2, 2in13_V3, 2in13_V4, mock
    partial_refresh_limit: int = 25  # full refresh every N cycles to prevent ghosting
    
    # Polling & Tick intervals (seconds)
    screen_refresh_interval: float = 3.0
    dev_poll_interval: float = 60.0
    audio_poll_interval: float = 2.0
    net_poll_interval: float = 8.0
    
    # Web server & companion
    web_enabled: bool = True
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    
    # State storage
    state_dir: str = field(
        default_factory=lambda: str(Path.home() / ".config" / "omnigotchi")
    )

    @property
    def state_file(self) -> str:
        return str(Path(self.state_dir) / "state.json")

    @classmethod
    def load(cls) -> "GotchiConfig":
        cfg = cls()
        os.makedirs(cfg.state_dir, exist_ok=True)
        return cfg
