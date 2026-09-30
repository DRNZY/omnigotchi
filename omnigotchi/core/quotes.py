"""Dialogue and quote system for OmniGotchi."""

import random
from typing import Dict, List

QUOTES: Dict[str, List[str]] = {
    "HAPPY": [
        "Vibes are clean.",
        "Living my best 1-bit life!",
        "E-ink never sleeps.",
        "System is running like silk.",
        "Everything nominal, human.",
        "Feeling sharp today!",
    ],
    "CODING": [
        "Ship it to prod!",
        "Another commit in the vault.",
        "Git push --force? Just kidding.",
        "Green tests make me purr.",
        "Clean diffs, happy life.",
        "Keep cooking that codebase!",
        "Compiling greatness...",
    ],
    "MUSIC": [
        "This track is heat!",
        "Pure lossless audio bliss.",
        "Cadence is bumping!",
        "BPM matched to my heartbeat.",
        "Turning up the volume!",
        "Audiophile grade tunes.",
    ],
    "DANCING": [
        "(ノ^_^)ノ ♪ ♫",
        "Grooving to the bassline!",
        "Don't stop the music!",
        "Feeling the rhythm!",
        "Step, turn, kick!",
    ],
    "HUNGRY": [
        "Code me a snack?",
        "No commits today? I'm starving!",
        "Need fresh tokens...",
        "Feed me some git activity.",
        "My energy is dropping!",
    ],
    "LAGGING": [
        "Ping is through the roof!",
        "Packet loss detected...",
        "Where did the packets go?",
        "Internet is choking.",
        "DNS looking sluggish.",
    ],
    "SLEEPING": [
        "Zzz... dreaming of RAM...",
        "Standby mode active.",
        "Resting my pixels.",
        "Low power nap... zzz",
        "Night shift on duty.",
    ],
    "LEVEL_UP": [
        "LEVEL UP! I'm evolving!",
        "Power level increased!",
        "Unlocked new byte powers!",
        "XP bar maxed out!",
    ],
    "STREAK": [
        "Streak protected! Legend.",
        "Consistency is king.",
        "Days on fire! Keep going!",
    ],
    "SENTINEL": [
        "Scanning RF & Wi-Fi beacons...",
        "LAN perimeter monitored.",
        "Zero rogue APs in range.",
        "Defensive radar spinning.",
        "Monitoring network packets.",
    ],
    "DEFCON": [
        "THREAT DETECTED! On alert.",
        "Suspicious ARP broadcast!",
        "Rogue AP beacon flagged!",
        "Defending local network!",
        "Shields up! Defcon elevated.",
    ],
    "SHIELD": [
        "All network nodes secured.",
        "Firewall hardened & active.",
        "ARP cache locked tight.",
        "Port sentinel all green.",
    ],
}

FACES: Dict[str, List[str]] = {
    "HAPPY": ["( ^‿^ )", "( ◕‿◕ )", "( ˘‿˘ )"],
    "CODING": ["(⌐■_■)", "( ಠ_ಠ )", "( •_•)>⌐■-■"],
    "MUSIC": ["( ♪‿♪ )", "( ♫_♫ )", "( ◕_◕)♫"],
    "DANCING": ["(ノ^_^)ノ", "＼(^_^)／", "ヾ(^_^)ノ"],
    "HUNGRY": ["( •́ ̯•̀ )", "( ◞‸◟ )", "( ⊙_⊙ )"],
    "LAGGING": ["( >_< )", "( @ _ @ )", "( ; _ ; )"],
    "SLEEPING": ["( -_- ) zzz", "( u_u ) .zZ", "( ¯_¯ ) zZ"],
    "LEVEL_UP": ["( ★‿★ )", "( ✧∀✧ )", "( ʘ‿ʘ )★"],
    "ALERT": ["( Ò_Ó )", "( ⚆_⚆ )", "( ! _ ! )"],
    "SENTINEL": ["( ◉_◉ )", "( ⊙_⊙ )", "( 🔍_🔍 )"],
    "DEFCON": ["( ⚆_⚆ )", "( Ò_Ó )", "( ⚠️_⚠️ )"],
    "SHIELD": ["( 🛡️_🛡️ )", "( 🔒_🔒 )", "( ▀̿Ĺ̯▀̿ ̿)"],
}


def get_random_face(mood: str) -> str:
    pool = FACES.get(mood, FACES["HAPPY"])
    return random.choice(pool)


def get_random_quote(mood: str, context: dict = None) -> str:
    if context:
        if mood == "MUSIC" and context.get("track_title"):
            title = context.get("track_title", "")
            artist = context.get("artist", "")
            if artist:
                return f"Vibin' to {artist[:16]}"
            return f"Playing: {title[:18]}"
        if mood == "CODING" and context.get("last_repo"):
            repo = context.get("last_repo", "")
            return f"Cooking in {repo[:16]}!"
        if mood == "STREAK" and context.get("streak_days"):
            days = context.get("streak_days", 1)
            return f"{days}-day streak! Fire!"
        if mood == "LAGGING" and context.get("ping_ms"):
            ping = context.get("ping_ms", 999)
            return f"High ping: {int(ping)}ms!"
        if mood in ("SENTINEL", "DEFCON", "SHIELD") and context.get("sec_alert"):
            return context["sec_alert"][:22]

    pool = QUOTES.get(mood, QUOTES["HAPPY"])
    return random.choice(pool)
