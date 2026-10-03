"""DedSec CyberDeck Brain: State Machine, Exploit Progression, and System Telemetry Engine."""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from omnigotchi.core.quotes import get_random_face, get_random_quote

logger = logging.getLogger("omnigotchi.brain")

TITLES = [
    (1, "Script Novice"),
    (3, "Mesh Infiltrator"),
    (5, "ctOS Disruptor"),
    (8, "Bounty Hunter"),
    (12, "Grid Reclaimer"),
    (16, "DedSec Operator"),
    (20, "Zero-Day Architect"),
]

MODES = ["infiltrator", "sentinel", "terminal"]


@dataclass
class GotchiState:
    name: str = "DEDSEC"
    level: int = 1
    xp: int = 0
    xp_next: int = 100
    
    # DedSec System Telemetry
    siphon_power: float = 100.0  # 0 to 100%
    overclock_level: int = 1     # 1 to 5
    system_integrity: float = 100.0
    mood: str = "DEDSEC"
    face: str = "[ ☠ _ ☠ ]"
    quote: str = "DedSec gives you truth."
    title: str = "Script Novice"
    badges: List[str] = field(default_factory=lambda: ["DEDSEC-ROOT", "CTOS-EXPLOIT", "BOUNTY-V1", "ZERO-DAY"])
    
    # Visual settings & 3 CyberOS Modes
    rotation: int = 0  # 0 or 180
    display_mode: str = "infiltrator"  # "infiltrator", "sentinel", or "terminal"
    
    # Cybersecurity & DEFCON
    defcon: int = 5
    threat_status: str = "SECURE"
    
    # Exploit & Yield statistics
    total_siphons: int = 0
    total_harvests: int = 0
    total_security_scans: int = 0
    total_commits: int = 0
    total_tracks_listened: int = 0
    created_at: float = field(default_factory=time.time)
    last_tick: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)


class GotchiBrain:
    def __init__(self, state_file: str, name: str = "DEDSEC"):
        self.state_file = state_file
        self.state = self._load_or_create(name)
        self.last_quote_change = time.time()
        self.dance_step = 0

    def _load_or_create(self, name: str) -> GotchiState:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    valid_keys = GotchiState.__dataclass_fields__.keys()
                    filtered = {k: v for k, v in data.items() if k in valid_keys}
                    # Migrate legacy modes
                    if filtered.get("display_mode") == "companion":
                        filtered["display_mode"] = "infiltrator"
                    return GotchiState(**filtered)
            except Exception as e:
                logger.warning(f"Could not load state, creating fresh: {e}")
        st = GotchiState(name=name)
        self._save(st)
        return st

    def _save(self, st: Optional[GotchiState] = None):
        if st is None:
            st = self.state
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(asdict(st), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def toggle_display_mode(self) -> str:
        """Cycles through the 3 DedSec CyberOS display modes."""
        cur = self.state.display_mode
        if cur == "infiltrator":
            next_mode = "sentinel"
        elif cur == "sentinel":
            next_mode = "terminal"
        else:
            next_mode = "infiltrator"
        self.state.display_mode = next_mode
        self._save()
        logger.info(f"DedSec CyberOS mode switched to: {next_mode.upper()}")
        return next_mode

    def set_display_mode(self, mode: str) -> str:
        if mode in MODES:
            self.state.display_mode = mode
            self._save()
        return self.state.display_mode

    def gain_xp(self, amount: int, reason: str = "") -> bool:
        """Add XP and handle hacker rank progression."""
        self.state.xp += amount
        leveled_up = False
        while self.state.xp >= self.state.xp_next:
            self.state.xp -= self.state.xp_next
            self.state.level += 1
            self.state.xp_next = int(self.state.xp_next * 1.35)
            self._update_title()
            leveled_up = True
            logger.info(f"Rank Upgrade! Now Level {self.state.level} ({self.state.title})")

        if leveled_up:
            self.state.mood = "LEVEL_UP"
            self.state.face = get_random_face("LEVEL_UP")
            self.state.quote = get_random_quote("LEVEL_UP")
            self.last_quote_change = time.time()

        self._save()
        return leveled_up

    def add_xp(self, amount: int, reason: str = "") -> bool:
        return self.gain_xp(amount, reason)

    def _update_title(self):
        current_title = TITLES[0][1]
        for min_lvl, title in TITLES:
            if self.state.level >= min_lvl:
                current_title = title
        self.state.title = current_title

    def siphon(self, amount: float = 25.0):
        """Siphons ctOS mesh cycles, boosts siphon power, and awards XP."""
        self.state.siphon_power = min(100.0, self.state.siphon_power + amount)
        self.state.total_siphons += 1
        self.gain_xp(20, "siphon")
        self.state.mood = "INFILTRATOR"
        self.state.face = "[ X _ X ]"
        self.state.quote = "ctOS bandwidth siphoned. Sats credited."
        self.last_quote_change = time.time()
        self._save()

    def overclock(self):
        """Toggles hardware overclock multiplier for maximum mesh yield."""
        self.state.overclock_level = (self.state.overclock_level % 5) + 1
        self.gain_xp(15, "overclock")
        self.state.mood = "OVERCLOCK"
        self.state.face = "[ * _ * ]"
        self.state.quote = f"Core Overclock Level {self.state.overclock_level} engaged."
        self.last_quote_change = time.time()
        self._save()

    # Backwards-compatible aliases for legacy triggers
    def feed(self, amount: float = 30.0):
        self.siphon(amount)

    def pet(self):
        self.overclock()

    def record_security_scan(self, defcon: int, status: str):
        self.state.total_security_scans += 1
        self.state.defcon = defcon
        self.state.threat_status = status
        self.gain_xp(25, "security_scan")
        self._save()

    def resolve_mood(
        self,
        dev_data: dict,
        audio_data: dict,
        net_data: dict,
        security_data: Optional[dict] = None,
        now: Optional[float] = None,
    ):
        """Calculates current mood based on tri-core & security telemetry."""
        if now is None:
            now = time.time()

        dt = now - self.state.last_tick
        self.state.last_tick = now

        # Decay siphon power slowly over time
        hours_passed = dt / 3600.0
        self.state.siphon_power = max(10.0, self.state.siphon_power - (hours_passed * 8.0))

        import datetime
        current_hour = datetime.datetime.now().hour
        is_night = current_hour >= 0 and current_hour < 7
        is_playing = audio_data.get("is_playing", False)
        is_coding = dev_data.get("recent_commits_24h", 0) > 0 or dev_data.get("is_active_repo", False)
        high_ping = net_data.get("ping_ms", 0) > 250 or net_data.get("is_offline", False)

        sec = security_data or {}
        defcon = sec.get("defcon_level", 5)
        arp_spoof = sec.get("arp_spoof_detected", False)
        evil_twin = sec.get("evil_twin_detected", False)
        self.state.defcon = defcon
        self.state.threat_status = sec.get("defcon_status", "SECURE")

        context = {}
        target_mood = "DEDSEC"

        # Security threats take top priority
        if defcon <= 2 or arp_spoof or evil_twin:
            target_mood = "DEFCON"
            context["sec_alert"] = sec.get("defcon_status", "DEFENSE ALERT")
        elif high_ping:
            target_mood = "LAGGING"
            context["ping_ms"] = net_data.get("ping_ms", 999)
        elif is_playing:
            self.dance_step = (self.dance_step + 1) % 4
            target_mood = "DANCING" if self.dance_step in (1, 3) else "MUSIC"
            context["track_title"] = audio_data.get("title", "")
            context["artist"] = audio_data.get("artist", "")
        elif is_coding and not is_night:
            target_mood = "CODING"
            context["last_repo"] = dev_data.get("last_repo", "")
        elif self.state.display_mode == "sentinel":
            target_mood = "SENTINEL"
        elif is_night and not is_playing and not is_coding:
            target_mood = "SLEEPING"
        else:
            target_mood = "DEDSEC"

        self.state.mood = target_mood

        # Update face & quote periodically (every 4s or when mood changes)
        if (now - self.last_quote_change) > 4.0 or self.state.face == "":
            self.state.face = get_random_face(target_mood)
            self.state.quote = get_random_quote(target_mood, context)
            self.last_quote_change = now

        self._save()
