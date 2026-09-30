"""Pwnagotchi-inspired E-Ink Canvas Renderer (250x122 monochrome 1-bit)."""

import datetime
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
                self.font_face = ImageFont.truetype(p, 15)
                break
            except Exception:
                continue

        for p in bold_paths:
            try:
                self.font_bold = ImageFont.truetype(p, 10)
                break
            except Exception:
                continue

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
        # 1. Top Header Bar (No seconds: strictly HH:MM)
        now_str = datetime.datetime.now().strftime("%H:%M")
        name_tag = f"{state.name.upper()} Lv.{state.level}"
        draw.text((4, 2), name_tag, font=self.font_bold, fill=0)

        # XP Bar [40px]
        xp_pct = min(1.0, max(0.0, state.xp / max(1, state.xp_next)))
        bar_x, bar_y, bar_w, bar_h = 74, 4, 36, 6
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=0, fill=255)
        fill_w = int(bar_w * xp_pct)
        if fill_w > 0:
            draw.rectangle([bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + bar_h - 1], fill=0)

        # Defcon & Clock (Right aligned)
        defcon_str = f"DEFCON {state.defcon}"
        draw.text((self.width - 86, 2), f"{defcon_str}  {now_str}", font=self.font_small, fill=0)
        draw.line([(0, 14), (self.width, 14)], fill=0, width=1)

        # 2. Pwnagotchi-style Center Avatar Card (No body, just big expressive face)
        ax1, ay1, ax2, ay2 = 4, 18, 86, 99
        draw.rounded_rectangle([ax1, ay1, ax2, ay2], radius=4, outline=0, fill=255, width=1)

        # Center the cute face
        face_str = state.face or "( ◕‿◕ )"
        # Face display centered vertically
        draw.text((ax1 + 6, ay1 + 22), face_str, font=self.font_face, fill=0)

        # Mood badge pill under the face
        mood_text = f"[{state.mood[:8]}]"
        draw.text((ax1 + 12, ay2 - 16), mood_text, font=self.font_small, fill=0)

        # 3. Speech Bubble on Right
        bx1, by1, bx2, by2 = 92, 18, 245, 99
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=4, outline=0, fill=255, width=1)
        # Bubble pointer
        draw.polygon([(bx1, 46), (bx1 - 5, 50), (bx1, 54)], fill=255, outline=0)
        draw.line([(bx1, 47), (bx1, 53)], fill=255, width=1)

        # Wrapped dialogue text
        quote = state.quote or "..."
        lines = self._wrap_text(quote, max_chars=22)
        y_offset = by1 + 6
        for line in lines[:4]:
            draw.text((bx1 + 7, y_offset), line, font=self.font_medium, fill=0)
            y_offset += 14

        # 4. Bottom Footer Bar (Cycling multi-source vitals)
        draw.line([(0, 103), (self.width, 103)], fill=0, width=1)
        self.footer_cycle = (self.footer_cycle + 1) % 16
        is_playing = audio_data.get("is_playing", False)

        if is_playing:
            track = audio_data.get("title", "Track")[:18]
            artist = audio_data.get("artist", "Artist")[:14]
            fmt = audio_data.get("format", "FLAC")
            footer_text = f"AUD: {track} - {artist} [{fmt}]"
        elif self.footer_cycle < 5:
            # Security Status
            lan_n = security_data.get("lan_hosts_count", 0)
            rf_n = security_data.get("wifi_aps_count", 0)
            status = security_data.get("defcon_status", "SECURE")[:14]
            footer_text = f"SEC: {status} | LAN:{lan_n} | RF:{rf_n}"
        elif self.footer_cycle < 10:
            # System Vitals & Wattage
            cpu = net_data.get("cpu_pct", 10)
            ram = net_data.get("ram_pct", 30)
            temp = int(net_data.get("temp_c", 40.0))
            watt = net_data.get("wattage_w", 0.85)
            footer_text = f"SYS: CPU {cpu}% | RAM {ram}% | {temp}C | {watt}W"
        else:
            # Dev Stats
            commits = dev_data.get("recent_commits_24h", 0)
            streak = dev_data.get("streak_days", 1)
            footer_text = f"DEV: {commits} commits 24h | Streak: {streak}d"

        draw.text((4, 107), footer_text[:42], font=self.font_small, fill=0)

    def _render_sentinel_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        net_data: Dict,
        security_data: Dict,
    ):
        """Renders clean Cyber Defense Tactical HUD with no seconds and crisp layout."""
        # Top Bar (Strictly HH:MM)
        now_str = datetime.datetime.now().strftime("%H:%M")
        draw.text((4, 2), f"SENTINEL [DEFCON {state.defcon}]", font=self.font_bold, fill=0)
        draw.text((self.width - 40, 2), now_str, font=self.font_small, fill=0)
        draw.line([(0, 14), (self.width, 14)], fill=0, width=1)

        # Left Avatar Stage
        ax1, ay1, ax2, ay2 = 4, 18, 76, 99
        draw.rounded_rectangle([ax1, ay1, ax2, ay2], radius=4, outline=0, fill=255, width=1)

        face_str = state.face or "( ◉_◉ )"
        draw.text((ax1 + 4, ay1 + 18), face_str, font=self.font_face, fill=0)
        draw.text((ax1 + 6, ay2 - 28), "[SENTINEL]", font=self.font_small, fill=0)
        draw.text((ax1 + 6, ay2 - 14), f"SCANS:{state.total_security_scans}", font=self.font_small, fill=0)

        # Right Tactical Matrix Box
        bx1, by1, bx2, by2 = 82, 18, 245, 99
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=4, outline=0, fill=255, width=1)

        lan_hosts = security_data.get("lan_hosts_count", 0)
        arp_ok = "OK" if not security_data.get("arp_spoof_detected", False) else "ALERT"
        wifi_aps = security_data.get("wifi_aps_count", 0)
        evil_twin = "0" if not security_data.get("evil_twin_detected", False) else "WARN"
        ssh_blocked = security_data.get("ssh_failed_attempts", 0)
        ports_count = len(security_data.get("open_ports", []))
        status_line = security_data.get("defcon_status", "ALL SHIELDS OK")[:20]

        draw.text((bx1 + 6, by1 + 5), f"- LAN NODES: {lan_hosts} (ARP:{arp_ok})", font=self.font_small, fill=0)
        draw.text((bx1 + 6, by1 + 18), f"- RF BEACONS: {wifi_aps} (TWIN:{evil_twin})", font=self.font_small, fill=0)
        draw.text((bx1 + 6, by1 + 31), f"- SSH SHIELD: {ssh_blocked} blocked", font=self.font_small, fill=0)
        draw.text((bx1 + 6, by1 + 44), f"- OPEN PORTS: {ports_count} active", font=self.font_small, fill=0)
        draw.text((bx1 + 6, by1 + 57), f"- {status_line}", font=self.font_bold, fill=0)

        # Threat meter line
        threat_score = min(100, max(0, security_data.get("threat_score", 0)))
        draw.text((bx1 + 6, by1 + 69), "THREAT:", font=self.font_small, fill=0)
        draw.rectangle([bx1 + 50, by1 + 70, bx2 - 6, by1 + 76], outline=0, fill=255)
        bar_fill = int((threat_score / 100.0) * (bx2 - bx1 - 58))
        if bar_fill > 0:
            draw.rectangle([bx1 + 51, by1 + 71, bx1 + 51 + bar_fill, by1 + 75], fill=0)

        # Footer
        draw.line([(0, 103), (self.width, 103)], fill=0, width=1)
        ping = int(net_data.get("ping_ms", 0))
        watt = net_data.get("wattage_w", 0.85)
        draw.text((4, 107), f"SHIELDS: ARP-GUARD * RF-RADAR | {ping}ms | {watt}W", font=self.font_small, fill=0)

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
