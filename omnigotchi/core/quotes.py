"""Pwnagotchi-grade Expressions, Faces (75+) and Dynamic Quotes for OmniGotchi."""

import random
from typing import Dict, List, Optional

FACES: Dict[str, List[str]] = {
    "HAPPY": [
        "( ^ _ ^ )",
        "( ^ . ^ )",
        "( ^ o ^ )",
        "( ^ - ^ )",
        "( o _ o )",
        "( o . o )",
        "( * _ * )",
        "( * . * )",
        "( 3 _ 3 )",
        "( 3 . 3 )",
        "( u _ u )",
        "( v _ v )",
    ],
    "SMUG": [
        "( - _ ^ )",
        "( ^ _ - )",
        "( > _ ^ )",
        "( ^ _ < )",
        "( ~ _ ^ )",
        "( ^ _ ~ )",
        "( = _ ^ )",
        "( ^ _ = )",
        "( ¬ _ ¬ )",
        "( ¬ _ ^ )",
    ],
    "CODING": [
        "( [ _ ] )",
        "( { _ } )",
        "( 0 _ 0 )",
        "( 0 _ 1 )",
        "( 1 _ 0 )",
        "( < _ > )",
        "( > _ < )",
        "( / _ \\ )",
        "( \\ _ / )",
        "( | _ | )",
    ],
    "SENTINEL": [
        "( O _ O )",
        "( O . O )",
        "( @ _ @ )",
        "( @ . @ )",
        "( ! _ ! )",
        "( ! . ! )",
        "( ? _ ? )",
        "( ? . ? )",
        "( o _ O )",
        "( O _ o )",
    ],
    "DEFCON": [
        "( > _ < )",
        "( > . < )",
        "( ! _ ! )",
        "( X _ X )",
        "( x _ x )",
        "( * _ * )",
        "( # _ # )",
        "( $ _ $ )",
    ],
    "SHIELD": [
        "( [ _ ] )",
        "( = _ = )",
        "( = . = )",
        "( - _ - )",
        "( - . - )",
        "( + _ + )",
        "( + . + )",
    ],
    "MUSIC": [
        "( d _ b )",
        "( q _ p )",
        "( d . b )",
        "( q . p )",
        "( ^ _ ^ )~",
        "~( ^ _ ^ )",
    ],
    "DANCING": [
        "\\( ^ _ ^ )/",
        "/( ^ _ ^ )\\",
        "\\( o _ o )/",
        "/( o _ o )\\",
        "\\( * _ * )/",
    ],
    "SLEEPY": [
        "( - _ - )zZ",
        "( u _ u )zZ",
        "( v _ v )zZ",
        "( . _ . )zZ",
        "( ~ _ ~ )zZ",
    ],
    "HUNGRY": [
        "( . _ . )",
        "( . . . )",
        "( o _ . )",
        "( . _ o )",
        "( ; _ ; )",
        "( T _ T )",
    ],
    "LEVEL_UP": [
        "( * _ * )!",
        "( ^ _ ^ )*",
        "( $ _ $ )!",
        "( ! _ ! )*",
        "( > _ < )*",
    ],
    "DERP": [
        "( @ _ o )",
        "( o _ @ )",
        "( ? _ o )",
        "( o _ ? )",
        "( ~ _ o )",
        "( o _ ~ )",
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
        "\\( ^ _ ^ )/ Party on!",
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
                return f"Vibin to {artist[:14]}"
            return f"Playing: {title[:16]}"
        if mood == "CODING" and context.get("last_repo"):
            repo = context.get("last_repo", "")
            return f"Cooking in {repo[:14]}!"
        if mood in ("SENTINEL", "DEFCON", "SHIELD") and context.get("sec_alert"):
            return context["sec_alert"][:22]

    m = mood.upper()
    if m in ("SLEEPING", "TIRED"):
        m = "SLEEPY"
    elif m in ("ALERT", "PANIC"):
        m = "DEFCON"

    pool = QUOTES.get(m, QUOTES["HAPPY"])
    return random.choice(pool)
