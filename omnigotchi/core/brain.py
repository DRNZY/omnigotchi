"""Gotchi Brain: State Machine, Mood Resolver, and RPG Leveling Engine."""

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


@dataclass
class GotchiState:
    name: str = "DEDSEC"
    level: int = 1
    xp: int = 0
    xp_next: int = 100
    hunger: float = 100.0  # 100 is full, 0 is starving
    energy: float = 100.0  # 100 is energetic, 0 is exhausted
    happiness: float = 100.0
    mood: str = "DEDSEC"
    face: str = "[ X _ X ]"
    quote: str = "DedSec gives you truth."
    title: str = "Script Novice"
    badges: List[str] = field(default_factory=lambda: ["DEDSEC-ROOT", "CTOS-EXPLOIT", "BOUNTY-V1"])
    
    # Visual settings
    rotation: int = 0  # 0 or 180
    display_mode: str = "companion"  # "companion" or "sentinel"
    
    # Cybersecurity & DEFCON
    defcon: int = 5
    threat_status: str = "SECURE"
    
    # Life statistics
    total_commits: int = 0
    total_tracks_listened: int = 0
    total_pets: int = 0
    total_feeds: int = 0
    total_security_scans: int = 0
    created_at: float = field(default_factory=time.time)
    last_tick: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)


class GotchiBrain:
    def __init__(self, state_file: str, name: str = "Omni"):
        self.state_file = state_file
        self.state = self._load_or_create(name)
        self.last_quote_change = time.time()
        self.dance_step = 0

    def _load_or_create(self, name: str) -> GotchiState:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Filter only fields known to GotchiState
                    valid_keys = GotchiState.__dataclass_fields__.keys()
                    filtered = {k: v for k, v in data.items() if k in valid_keys}
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
        """Toggles between standard cyberpet companion and cyber defense sentinel HUD."""
        new_mode = "sentinel" if self.state.display_mode == "companion" else "companion"
        self.state.display_mode = new_mode
        self._save()
        return new_mode

    def gain_xp(self, amount: int, reason: str = "") -> bool:
        """Add XP and handle level-ups. Returns True if leveled up."""
        self.state.xp += amount
        leveled_up = False
        while self.state.xp >= self.state.xp_next:
            self.state.xp -= self.state.xp_next
            self.state.level += 1
            self.state.xp_next = int(self.state.xp_next * 1.35)
            self._update_title()
            leveled_up = True
            logger.info(f"Level up! Now Level {self.state.level} ({self.state.title})")

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

    def feed(self, amount: float = 30.0):
        self.state.hunger = min(100.0, self.state.hunger + amount)
        self.state.happiness = min(100.0, self.state.happiness + 15.0)
        self.state.total_feeds += 1
        self.gain_xp(15, "feed")
        self.state.mood = "HAPPY"
        self.state.face = "( ^‿^ )"
        self.state.quote = "Nom nom nom! Yummy bytes!"
        self.last_quote_change = time.time()
        self._save()

    def pet(self):
        self.state.happiness = min(100.0, self.state.happiness + 20.0)
        self.state.total_pets += 1
        self.gain_xp(10, "pet")
        self.state.mood = "HAPPY"
        self.state.face = "( ◕‿◕ )"
        self.state.quote = "Aww, thanks human! <3"
        self.last_quote_change = time.time()
        self._save()

    def record_security_scan(self, defcon: int, status: str):
        self.state.total_security_scans += 1
        self.state.defcon = defcon
        self.state.threat_status = status
        self.gain_xp(20, "security_scan")
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

        # Passive hunger decay: ~10% per hour
        hours_passed = dt / 3600.0
        self.state.hunger = max(0.0, self.state.hunger - (hours_passed * 10.0))

        # Check hour for night / sleep mode (between 00:00 and 07:00 if idle)
        import datetime
        current_hour = datetime.datetime.now().hour
        is_night = current_hour >= 0 and current_hour < 7
        is_playing = audio_data.get("is_playing", False)
        is_coding = dev_data.get("recent_commits_24h", 0) > 0 or dev_data.get("is_active_repo", False)
        high_ping = net_data.get("ping_ms", 0) > 250 or net_data.get("is_offline", False)
        is_starving = self.state.hunger < 20.0

        sec = security_data or {}
        defcon = sec.get("defcon_level", 5)
        arp_spoof = sec.get("arp_spoof_detected", False)
        evil_twin = sec.get("evil_twin_detected", False)
        self.state.defcon = defcon
        self.state.threat_status = sec.get("defcon_status", "SECURE")

        context = {}
        target_mood = "HAPPY"

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
        elif is_starving:
            target_mood = "HUNGRY"
        elif is_night and not is_playing and not is_coding:
            target_mood = "SLEEPING"
        else:
            if dev_data.get("streak_days", 0) > 2:
                target_mood = "HAPPY"
                context["streak_days"] = dev_data.get("streak_days")

        self.state.mood = target_mood

        # Update face & quote periodically (every 3.5s or when mood changes)
        if (now - self.last_quote_change) > 3.5 or self.state.face == "":
            self.state.face = get_random_face(target_mood)
            self.state.quote = get_random_quote(target_mood, context)
            self.last_quote_change = now

        self._save()
