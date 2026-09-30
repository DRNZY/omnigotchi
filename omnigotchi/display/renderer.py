"""Pwnagotchi-inspired E-Ink Canvas Renderer (250x122 monochrome 1-bit, Obsidian Dark Mode)."""

import datetime
import os
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont

from omnigotchi.core.brain import GotchiState


class GotchiRenderer:
    def __init__(self, width: int = 250, height: int = 122):
        self.width = width
        self.height = height
        self._init_fonts()

    def _init_fonts(self):
        """Loads clean, futuristic TTF fonts with robust fallbacks for sharp 1-bit rendering."""
        local_asset_font = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts" / "DejaVuSans.ttf"
        font_paths = [
            str(local_asset_font),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]

        font_file = None
        for p in font_paths:
            if os.path.exists(p):
                font_file = p
                break

        if font_file:
            self.font_hdr = ImageFont.truetype(font_file, 10)
            self.font_face = ImageFont.truetype(font_file, 11)
            self.font_text = ImageFont.truetype(font_file, 9)
            self.font_mini = ImageFont.truetype(font_file, 8)
        else:
            self.font_hdr = ImageFont.load_default()
            self.font_face = ImageFont.load_default()
            self.font_text = ImageFont.load_default()
            self.font_mini = ImageFont.load_default()

    def render(
        self,
        state: GotchiState,
        dev_data: Dict,
        audio_data: Dict,
        net_data: Dict,
        security_data: Optional[Dict] = None,
    ) -> Image.Image:
        """Composes and returns a 250x122 1-bit PIL image (0=black background, 255=white text/lines)."""
        img = Image.new("1", (self.width, self.height), 0)
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
        # 1. Top Header Bar (y: 0..14)
        now_str = datetime.datetime.now().strftime("%H:%M")
        name_tag = f"{state.name.upper()} Lv.{state.level}"
        draw.text((4, 1), name_tag, font=self.font_hdr, fill=255)

        # XP Bar [50px]
        xp_pct = min(1.0, max(0.0, state.xp / max(1, state.xp_next)))
        bar_x, bar_y, bar_w, bar_h = 70, 4, 50, 6
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=255, fill=0)
        fill_w = int(bar_w * xp_pct)
        if fill_w > 0:
            draw.rectangle([bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + bar_h - 1], fill=255)

        # Wi-Fi SSID & Clock
        ssid = net_data.get("wifi_ssid", "LAN")[:12]
        draw.text((130, 1), ssid, font=self.font_mini, fill=255)
        draw.text((216, 1), now_str, font=self.font_hdr, fill=255)
        draw.line([(0, 14), (self.width, 14)], fill=255, width=1)

        # 2. Left Card: Avatar + Real-Time Hardware Gauges (x: 2..74, y: 16..98)
        draw.rounded_rectangle([2, 16, 74, 98], radius=3, outline=255, fill=0, width=1)
        face_str = state.face or "( ^ _ ^ )"
        fb = self.font_face.getbbox(face_str)
        fw = fb[2] - fb[0]
        fx = 2 + max(0, (72 - fw) // 2)
        draw.text((fx, 20), face_str, font=self.font_face, fill=255)

        mood_str = f"[{state.mood[:8]}]"
        mb = self.font_mini.getbbox(mood_str)
        mw = mb[2] - mb[0]
        mx = 2 + max(0, (72 - mw) // 2)
        draw.text((mx, 38), mood_str, font=self.font_mini, fill=255)

        # Divider inside left card
        draw.line([(3, 50), (73, 50)], fill=255, width=1)
        ram_pct = int(net_data.get("ram_pct", 0))
        cpu_pct = int(net_data.get("cpu_pct", 0))
        temp_c = net_data.get("temp_c", 40.0)
        watt_w = net_data.get("wattage_w", 0.85)
        ping_ms = int(net_data.get("ping_ms", 0))

        draw.text((5, 53), f"CPU: {cpu_pct}%", font=self.font_mini, fill=255)
        draw.text((5, 64), f"RAM: {ram_pct}%", font=self.font_mini, fill=255)
        draw.text((5, 75), f"PWR: {watt_w:.2f}W", font=self.font_mini, fill=255)
        draw.text((5, 86), f"{temp_c:.1f}°C {ping_ms}ms", font=self.font_mini, fill=255)

        # 3. Right Card: Speech Bubble + Full Clean Vitals (x: 78..247, y: 16..98)
        draw.rounded_rectangle([78, 16, 247, 98], radius=3, outline=255, fill=0, width=1)

        # Quote / Status dialogue
        quote = state.quote or "Living my best 1-bit life!"
        if len(quote) > 28:
            quote = quote[:26] + ".."
        draw.text((82, 18), f'"{quote}"', font=self.font_text, fill=255)
        draw.line([(78, 30), (247, 30)], fill=255, width=1)

        # Clean Vitals Matrix Grid
        ram_used = int(net_data.get("ram_used_mb", 0))
        ram_total = int(net_data.get("ram_total_mb", 512))
        uptime_str = net_data.get("uptime_str", "0h")
        title_str = state.title[:18]

        draw.text((82, 33), f"RANK: {title_str}", font=self.font_text, fill=255)
        draw.text((82, 45), f"RAM : {ram_used}/{ram_total}MB ({ram_pct}%)", font=self.font_text, fill=255)
        draw.text((82, 57), f"LINK: {ssid} ({ping_ms}ms)", font=self.font_text, fill=255)
        draw.text((82, 69), f"FEED: {int(state.hunger)}% | JOY: {int(state.happiness)}%", font=self.font_text, fill=255)
        draw.text((82, 81), f"UP  : {uptime_str} | STAT: ONLINE", font=self.font_text, fill=255)

        # 4. Bottom Footer Bar (y: 100..121)
        draw.line([(0, 100), (self.width, 100)], fill=255, width=1)
        is_playing = audio_data.get("is_playing", False)
        if is_playing:
            track = audio_data.get("title", "Track")[:20]
            artist = audio_data.get("artist", "Artist")[:15]
            fmt = audio_data.get("format", "FLAC")
            footer_line1 = f"AUD: {track} - {artist} [{fmt}]"
        else:
            commits = dev_data.get("recent_commits_24h", 0)
            streak = dev_data.get("streak_days", 1)
            footer_line1 = f"DEV: {commits} commits | Streak: {streak}d | Lv.{state.level}"

        rx = net_data.get("rx_kbps", 0.0)
        tx = net_data.get("tx_kbps", 0.0)
        footer_line2 = f"NET: RX {rx}k TX {tx}k | {temp_c:.1f}°C | {watt_w:.2f}W"

        draw.text((4, 102), footer_line1, font=self.font_mini, fill=255)
        draw.text((4, 111), footer_line2, font=self.font_mini, fill=255)

    def _render_sentinel_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        net_data: Dict,
        security_data: Dict,
    ):
        """Companion display remains clean; heavy sentinel metrics route solely to OmniHUD."""
        self._render_companion_hud(draw, state, {}, {}, net_data, security_data)
