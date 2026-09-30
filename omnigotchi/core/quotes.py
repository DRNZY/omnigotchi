"""Pwnagotchi-grade Expressions, Faces (60+) and Dynamic Quotes for OmniGotchi."""

import random
from typing import Dict, List, Optional

FACES: Dict[str, List[str]] = {
    "HAPPY": [
        "( ◕‿◕ )",
        "( ^‿^ )",
        "( ˘‿˘ )",
        "( ᵔᵕᵔ )",
        "( ˶ᵔ ᵕ ᵔ˶ )",
        "( ◜‿◝ )",
        "( ╹◡╹ )",
        "( •̀ᴗ•́ )و",
        "( ˶ˆᗜˆ˵ )",
        "( ◕◡◕ )",
    ],
    "SMUG": [
        "(⌐■_■)",
        "( •_•)>⌐■-■",
        "( ¬‿¬ )",
        "( ˵¯͒ ‿ ¯͒˵ )",
        "( ✧ω✧ )",
        "( ✜‿✜ )",
        "( ¯︶¯ )",
        "( ▀̿Ĺ̯▀̿ ̿)",
    ],
    "CODING": [
        "( 💻_💻 )",
        "( ⌨️_⌨️ )",
        "( 0_0 )b",
        "( ಠ_ಠ )",
        "( ⚆_⚆ )",
        "( ✜_✜ )",
        "( [•]_[•] )",
        "( >_< )/",
        "( ▓▓_▓▓ )",
        "( 0_1 )",
    ],
    "SENTINEL": [
        "( ◉_◉ )",
        "( ⊙_⊙ )",
        "( 🔍_🔍 )",
        "( ⦿_⦿ )",
        "( ⨀_⨀ )",
        "( ◉ω◉ )",
        "( ⚆_⚆ )!",
        "( ⊚_⊚ )",
        "( ◓_◓ )",
    ],
    "DEFCON": [
        "( Ò_Ó )",
        "( ⚆_⚆ )",
        "( ! _ ! )",
        "( ⨀_⨀ )",
        "( ◣_◢ )",
        "( ಠ益ಠ )",
        "( •̀o•́ )",
        "( ⚠️_⚠️ )",
    ],
    "SHIELD": [
        "( 🛡️_🛡️ )",
        "( 🔒_🔒 )",
        "( ▰_▰ )",
        "( ⯊_⯊ )",
        "( ⊘_⊘ )",
        "( ◖_◗ )",
        "( [🛡️] )",
    ],
    "MUSIC": [
        "( ♪‿♪ )",
        "( ♫_♫ )",
        "( ◕_◕)♫",
        "( ˘͈ ᵕ ˘͈ )♪",
        "( ᐖ )♪",
    ],
    "DANCING": [
        "(ノ^_^)ノ",
        "＼(^_^)／",
        "ヾ(^_^)ノ",
        "(ノ^o^)ノ",
    ],
    "SLEEPY": [
        "( -_- ) zZ",
        "( u_u ) .zZ",
        "( ¯_¯ ) zZ",
        "( ˘ω˘ )",
        "( ᵕ_ᵕ )",
        "( ᴗ_ᴗ )",
        "( =_= )",
    ],
    "HUNGRY": [
        "( •́ ̯•̀ )",
        "( ◞‸◟ )",
        "( ⊙_⊙ )",
        "( º﹃º )",
        "( ºдº )",
    ],
    "LEVEL_UP": [
        "( ★‿★ )",
        "( ✧∀✧ )",
        "( ʘ‿ʘ )★",
        "( ≧∇≦ )",
        "( ٩(ˊᗜˋ*)و )",
        "( ⸜(｡˃ ᵕ ˂ )⸝ )",
    ],
    "DERP": [
        "( ﾟヮﾟ )",
        "( ʘ‿ʘ )",
        "( @ _ @ )",
        "( ᐛ )",
        "( ⟁_⟁ )",
    ],
}

QUOTES: Dict[str, List[str]] = {
    "HAPPY": [
        "Vibes are clean.",
        "Living my best 1-bit life!",
        "E-ink never sleeps.",
        "System is running like silk.",
        "Everything nominal, human.",
        "Feeling sharp today!",
        "Pixels crisp, packets fast.",
    ],
    "CODING": [
        "Ship it to prod!",
        "Another commit in the vault.",
        "Green tests make me purr.",
        "Clean diffs, happy life.",
        "Compiling greatness...",
        "Building the future.",
    ],
    "SENTINEL": [
        "Scanning RF & Wi-Fi beacons...",
        "LAN perimeter monitored.",
        "Zero rogue APs in range.",
        "Defensive radar spinning.",
        "DNS queries verified clean.",
        "Subnet radar tracking nodes.",
    ],
    "DEFCON": [
        "THREAT DETECTED! On alert.",
        "Suspicious ARP broadcast!",
        "Rogue AP beacon flagged!",
        "Shields up! Defcon active.",
    ],
    "SHIELD": [
        "All network nodes secured.",
        "Firewall hardened & active.",
        "ARP cache locked tight.",
        "Port sentinel all green.",
    ],
    "MUSIC": [
        "This track is heat!",
        "Pure lossless audio bliss.",
        "Cadence is bumping!",
        "BPM matched to my core.",
    ],
    "DANCING": [
        "(ノ^_^)ノ ♪ ♫",
        "Grooving to the bassline!",
        "Feeling the rhythm!",
    ],
    "SLEEPY": [
        "Zzz... dreaming of RAM...",
        "Standby mode active.",
        "Resting my pixels.",
        "Low power nap... zzz",
    ],
    "HUNGRY": [
        "Code me a snack?",
        "No commits today? Hungry!",
        "Feed me some packets.",
    ],
    "LEVEL_UP": [
        "LEVEL UP! Evolving!",
        "Power level increased!",
        "Unlocked new cyber powers!",
    ],
}


def get_random_face(mood: str) -> str:
    # Map synonyms to pool
    m = mood.upper()
    if m in ("SLEEPING", "TIRED"):
        m = "SLEEPY"
    elif m in ("CYBER", "HACKER"):
        m = "CODING"
    elif m in ("ALERT", "PANIC"):
        m = "DEFCON"

    pool = FACES.get(m, FACES["HAPPY"])
    return random.choice(pool)


def get_random_quote(mood: str, context: Optional[dict] = None) -> str:
    if context:
        if mood == "MUSIC" and context.get("track_title"):
            artist = context.get("artist", "")
            title = context.get("track_title", "")
            if artist:
                return f"Vibin' to {artist[:16]}"
            return f"Playing: {title[:18]}"
        if mood == "CODING" and context.get("last_repo"):
            repo = context.get("last_repo", "")
            return f"Cooking in {repo[:16]}!"
        if mood in ("SENTINEL", "DEFCON", "SHIELD") and context.get("sec_alert"):
            return context["sec_alert"][:22]

    m = mood.upper()
    if m in ("SLEEPING", "TIRED"):
        m = "SLEEPY"
    elif m in ("ALERT", "PANIC"):
        m = "DEFCON"

    pool = QUOTES.get(m, QUOTES["HAPPY"])
    return random.choice(pool)
