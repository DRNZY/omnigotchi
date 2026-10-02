"""DedSec CyberOS Expressions, ASCII Faces, and Authentic DedSec Hacker Quotes."""

import random
from typing import Dict, List, Optional

FACES: Dict[str, List[str]] = {
    "DEDSEC": [
        "[ X _ X ]",
        "( [X_X] )",
        "( X _ x )",
        "( x _ X )",
        "[ / _ \\ ]",
        "[ \\ _ / ]",
        "( > _ < )!",
        "( ! _ ! )#",
        "( 0 _ 0 )#",
        "( 1 _ 0 )!",
    ],
    "BOUNTY": [
        "( $ _ $ )",
        "( $ . $ )",
        "[ $ _ $ ]",
        "( > _ $ )",
        "( $ _ < )",
        "( * _ $ )",
        "( ¢ _ ¢ )",
    ],
    "HAPPY": [
        "[ ^ _ ^ ]",
        "( ^ . ^ )",
        "( ^ o ^ )",
        "[ - _ ^ ]",
        "( o _ o )",
        "( * _ * )",
        "( v _ v )",
    ],
    "CODING": [
        "[ [ _ ] ]",
        "( { _ } )",
        "( 0 _ 1 )",
        "( 1 _ 0 )",
        "( < _ > )",
        "[ / _ \\ ]",
        "( | _ | )",
    ],
    "SENTINEL": [
        "[ O _ O ]",
        "( @ _ @ )",
        "( ! _ ! )",
        "[ ? _ ? ]",
        "( o _ O )",
        "[ X _ O ]",
    ],
    "DEFCON": [
        "[ X _ X ]!",
        "( > _ < )#",
        "( ! _ ! )!",
        "( # _ # )",
        "[ ! _ ! ]",
    ],
    "SHIELD": [
        "[ [ _ ] ]",
        "( = _ = )",
        "( - _ - )",
        "[ + _ + ]",
        "( | _ | )",
    ],
    "MUSIC": [
        "( d _ b )#",
        "( q _ p )#",
        "( d . b )",
        "[ ^ _ ^ ]~",
        "~( [X_X] )",
    ],
    "DANCING": [
        "\\( [X_X] )/",
        "/( [X_X] )\\",
        "\\( ^ _ ^ )/",
        "/( ^ _ ^ )\\",
    ],
    "SLEEPY": [
        "[ - _ - ]zZ",
        "( u _ u )zZ",
        "( . _ . )zZ",
        "[ ~ _ ~ ]zZ",
    ],
    "LEVEL_UP": [
        "[ * _ * ]!",
        "( $ _ $ )!",
        "[ ! _ ! ]*",
        "( > _ < )*",
    ],
}

QUOTES: Dict[str, List[str]] = {
    "DEDSEC": [
        "DedSec gives you truth.",
        "Join us. Expect resistance.",
        "The ctOS system is flawed.",
        "Your fear is their power.",
        "We are the signal in static.",
        "Zero gods, zero masters.",
        "Encrypt all. Trust none.",
        "Reclaim the grid.",
        "Break the code.",
        "Information is currency.",
        "Free the net.",
    ],
    "BOUNTY": [
        "Harvesting network yield...",
        "Passive sats accumulating.",
        "Bounty radar active.",
        "Mesh relay bandwidth shared.",
        "Mining compute proof...",
        "Yield locked in vault.",
    ],
    "HAPPY": [
        "Grid perimeter nominal.",
        "Living my best 1-bit life!",
        "E-ink never sleeps.",
        "Pixels crisp, packets fast.",
        "DedSec sentinel online.",
    ],
    "CODING": [
        "Pushing payload to prod.",
        "Compiling greatness...",
        "Another commit in vault.",
        "Clean diffs, free world.",
        "Hacking the mainframe.",
    ],
    "SENTINEL": [
        "Scanning RF & Wi-Fi beacons...",
        "LAN perimeter monitored.",
        "Subnet radar tracking nodes.",
        "DNS queries verified clean.",
        "ctOS surveillance blocked.",
    ],
    "DEFCON": [
        "THREAT DETECTED! Alarm!",
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
        "Cadence audio beat locked.",
        "Pure lossless audio bliss.",
        "BPM matched to my core.",
        "Bassline vibrating.",
    ],
    "DANCING": [
        "\\( [X_X] )/ Party on grid!",
        "Grooving to the signal!",
    ],
    "SLEEPY": [
        "Standby mode active.",
        "Resting my pixels... zZ",
        "Low power stealth mode.",
    ],
    "LEVEL_UP": [
        "LEVEL UP! DedSec evolving!",
        "Power level increased!",
        "Zero-day privilege unlocked!",
    ],
}


def get_random_face(mood: str) -> str:
    m = mood.upper()
    if m in ("DEDSEC", "HACKER", "CYBER"):
        m = "DEDSEC"
    elif m in ("BOUNTY", "YIELD", "EARNING"):
        m = "BOUNTY"
    elif m in ("SLEEPING", "TIRED"):
        m = "SLEEPY"
    elif m in ("ALERT", "PANIC"):
        m = "DEFCON"

    pool = FACES.get(m, FACES["DEDSEC"])
    return random.choice(pool)


def get_random_quote(mood: str, context: Optional[dict] = None) -> str:
    if context:
        if mood == "MUSIC" and context.get("track_title"):
            artist = context.get("artist", "")
            title = context.get("track_title", "")
            if artist:
                return f"Vibin to {artist[:14]}"
            return f"Playing: {title[:16]}"
        if mood == "CODING" and context.get("last_repo"):
            repo = context.get("last_repo", "")
            return f"Cooking in {repo[:14]}!"
        if mood in ("SENTINEL", "DEFCON", "SHIELD") and context.get("sec_alert"):
            return context["sec_alert"][:22]
        if mood in ("BOUNTY", "YIELD") and context.get("daily_yield"):
            return f"Yield: ${context['daily_yield']:.2f}/d"

    m = mood.upper()
    if m in ("DEDSEC", "HACKER", "CYBER"):
        m = "DEDSEC"
    elif m in ("BOUNTY", "YIELD", "EARNING"):
        m = "BOUNTY"
    elif m in ("SLEEPING", "TIRED"):
        m = "SLEEPY"
    elif m in ("ALERT", "PANIC"):
        m = "DEFCON"

    pool = QUOTES.get(m, QUOTES["DEDSEC"])
    return random.choice(pool)

