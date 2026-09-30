"""OmniGotchi E-Ink Canvas Renderer (250x122 monochrome 1-bit)."""

import datetime
import math
from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont

from omnigotchi.core.brain import GotchiState


class GotchiRenderer:
    def __init__(self, width: int = 250, height: int = 122):
        self.width = width
        self.height = height
        self._init_fonts()
        self.footer_cycle = 0

    def _init_fonts(self):
        """Loads available system TTF fonts or falls back to default."""
        font_paths = [
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        ]
        bold_paths = [
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/LiberationMono-Bold.ttf",
        ]

        self.font_small = None
        self.font_medium = None
        self.font_bold = None
        self.font_face = None

        for p in font_paths:
            try:
                self.font_small = ImageFont.truetype(p, 9)
                self.font_medium = ImageFont.truetype(p, 10)
                self.font_face = ImageFont.truetype(p, 14)
                break
            except Exception:
                continue

        for p in bold_paths:
            try:
                self.font_bold = ImageFont.truetype(p, 10)
                break
            except Exception:
                continue

        # Fallback to default bitmap font if no TTF found
        if self.font_small is None:
            self.font_small = ImageFont.load_default()
        if self.font_medium is None:
            self.font_medium = ImageFont.load_default()
        if self.font_bold is None:
            self.font_bold = ImageFont.load_default()
        if self.font_face is None:
            self.font_face = ImageFont.load_default()

    def render(
        self,
        state: GotchiState,
        dev_data: Dict,
        audio_data: Dict,
        net_data: Dict,
        security_data: Optional[Dict] = None,
    ) -> Image.Image:
        """Composes and returns a 250x122 1-bit PIL image (0=black, 255=white)."""
        img = Image.new("1", (self.width, self.height), 255)
        draw = ImageDraw.Draw(img)
        sec = security_data or {}

        if state.display_mode == "sentinel":
            self._render_sentinel_hud(draw, state, net_data, sec)
        else:
            self._render_companion_hud(draw, state, dev_data, audio_data, net_data, sec)

        return img

    def _render_companion_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        dev_data: Dict,
        audio_data: Dict,
        net_data: Dict,
        security_data: Dict,
    ):
        # 1. Top Header Bar
        name_tag = f"{state.name.upper()} Lv.{state.level}"
        draw.text((4, 2), name_tag, font=self.font_bold, fill=0)

        # XP Bar
        xp_pct = min(1.0, max(0.0, state.xp / max(1, state.xp_next)))
        bar_x, bar_y, bar_w, bar_h = 75, 4, 38, 6
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=0, fill=255)
        fill_w = int(bar_w * xp_pct)
        if fill_w > 0:
            draw.rectangle([bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + bar_h - 1], fill=0)

        # Defcon & Clock
        now_str = datetime.datetime.now().strftime("%H:%M")
        defcon_str = f"DEFCON {state.defcon}"
        draw.text((self.width - 86, 2), f"{defcon_str} {now_str}", font=self.font_small, fill=0)

        # Top separator
        draw.line([(0, 14), (self.width, 14)], fill=0, width=1)

        # 2. Center Character Stage
        face_str = state.face or "( ^‿^ )"
        draw.text((10, 34), face_str, font=self.font_face, fill=0)

        if state.mood in ("DANCING", "MUSIC"):
            body_lines = ["  \\(   )/", "   /   \\ "]
        elif state.mood == "SLEEPING":
            body_lines = ["  ( -_- )", "  zzZZ..."]
        elif state.mood == "CODING":
            body_lines = ["  [💻=⌨️]", "  /     \\"]
        elif state.mood in ("SENTINEL", "DEFCON", "SHIELD"):
            body_lines = ["  [🛡️=📡]", "   /   \\ "]
        else:
            body_lines = ["  (  o  )", "   /   \\ "]

        draw.text((14, 56), body_lines[0], font=self.font_small, fill=0)
        draw.text((14, 68), body_lines[1], font=self.font_small, fill=0)

        mood_badge = f"[{state.mood}]"
        draw.text((12, 84), mood_badge, font=self.font_small, fill=0)

        # 3. Speech Bubble
        bx1, by1, bx2, by2 = 92, 20, 244, 98
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=4, outline=0, fill=255, width=1)
        draw.polygon([(bx1, 48), (bx1 - 5, 52), (bx1, 56)], fill=255, outline=0)
        draw.line([(bx1, 49), (bx1, 55)], fill=255, width=1)

        quote = state.quote or "..."
        lines = self._wrap_text(quote, max_chars=22)
        y_offset = by1 + 6
        for line in lines[:4]:
            draw.text((bx1 + 8, y_offset), line, font=self.font_medium, fill=0)
            y_offset += 14

        # 4. Footer
        draw.line([(0, 103), (self.width, 103)], fill=0, width=1)
        self.footer_cycle = (self.footer_cycle + 1) % 18
        is_playing = audio_data.get("is_playing", False)

        if is_playing:
            track = audio_data.get("title", "Track")[:18]
            artist = audio_data.get("artist", "Artist")[:14]
            fmt = audio_data.get("format", "FLAC")
            footer_text = f"♫ {track} - {artist} [{fmt}]"
        elif self.footer_cycle < 6:
            # Security summary
            lan_n = security_data.get("lan_hosts_count", 0)
            rf_n = security_data.get("wifi_aps_count", 0)
            status = security_data.get("defcon_status", "SECURE")[:14]
            footer_text = f"DEF: {status} | LAN:{lan_n} | RF:{rf_n}"
        elif self.footer_cycle < 12:
            commits = dev_data.get("recent_commits_24h", 0)
            streak = dev_data.get("streak_days", 1)
            footer_text = f"DEV: {commits} commits 24h | Streak: {streak}d"
        else:
            cpu = net_data.get("cpu_pct", 10)
            temp = net_data.get("temp_c", 40.0)
            ram = net_data.get("ram_pct", 30)
            footer_text = f"SYS: CPU {cpu}% | RAM {ram}% | {int(temp)}°C"

        draw.text((4, 107), footer_text[:40], font=self.font_small, fill=0)

    def _render_sentinel_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        net_data: Dict,
        security_data: Dict,
    ):
        """Renders dedicated Cyber Defense Tactical HUD on 250x122 display."""
        # Top Bar
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        draw.text((4, 2), f"🛡️ SENTINEL [DEFCON {state.defcon}]", font=self.font_bold, fill=0)
        draw.text((self.width - 50, 2), now_str, font=self.font_small, fill=0)
        draw.line([(0, 14), (self.width, 14)], fill=0, width=1)

        # Left Avatar Stage
        draw.text((8, 24), "( ◉_◉ )", font=self.font_face, fill=0)
        draw.text((10, 48), "[SENTINEL]", font=self.font_small, fill=0)
        draw.text((10, 62), f"Lv.{state.level} GUARD", font=self.font_small, fill=0)
        draw.text((10, 76), f"SCANS: {state.total_security_scans}", font=self.font_small, fill=0)

        # Vertical divider line
        draw.line([(82, 14), (82, 103)], fill=0, width=1)

        # Right Tactical Matrix Box
        lan_hosts = security_data.get("lan_hosts_count", 0)
        arp_ok = "OK" if not security_data.get("arp_spoof_detected", False) else "ALERT"
        wifi_aps = security_data.get("wifi_aps_count", 0)
        evil_twin = "0" if not security_data.get("evil_twin_detected", False) else "DETECTED"
        ssh_blocked = security_data.get("ssh_failed_attempts", 0)
        ports_count = len(security_data.get("open_ports", []))
        status_line = security_data.get("defcon_status", "ALL SHIELDS ACTIVE")[:22]

        draw.text((88, 20), f"• LAN NODES: {lan_hosts} (ARP: {arp_ok})", font=self.font_small, fill=0)
        draw.text((88, 34), f"• RF BEACONS: {wifi_aps} (TWIN: {evil_twin})", font=self.font_small, fill=0)
        draw.text((88, 48), f"• SSH BLOCKED: {ssh_blocked} attempts", font=self.font_small, fill=0)
        draw.text((88, 62), f"• OPEN PORTS: {ports_count} active", font=self.font_small, fill=0)
        draw.text((88, 76), f"• POSTURE: {status_line}", font=self.font_bold, fill=0)

        # Threat Level Bar
        threat_score = min(100, max(0, security_data.get("threat_score", 0)))
        draw.text((88, 89), "THREAT:", font=self.font_small, fill=0)
        draw.rectangle([136, 90, 240, 97], outline=0, fill=255)
        bar_fill = int((threat_score / 100.0) * 102)
        if bar_fill > 0:
            draw.rectangle([137, 91, 137 + bar_fill, 96], fill=0)

        # Footer
        draw.line([(0, 103), (self.width, 103)], fill=0, width=1)
        ping = int(net_data.get("ping_ms", 0))
        draw.text((4, 107), f"SHIELDS: ARP-GUARD • RF-SENTINEL | {ping}ms", font=self.font_small, fill=0)

    def _wrap_text(self, text: str, max_chars: int = 22) -> list:
        words = text.split(" ")
        lines = []
        cur_line = ""
        for w in words:
            if len(cur_line) + len(w) + 1 <= max_chars:
                cur_line = f"{cur_line} {w}".strip()
            else:
                if cur_line:
                    lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)
        return lines
