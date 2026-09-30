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
    ) -> Image.Image:
        """Composes and returns a 250x122 1-bit PIL image (0=black, 255=white)."""
        # Create white background canvas
        img = Image.new("1", (self.width, self.height), 255)
        draw = ImageDraw.Draw(img)

        # 1. Top Header Bar
        self._draw_header(draw, state, net_data)

        # 2. Center Stage: Pet Face on Left & Speech Bubble on Right
        self._draw_character_and_bubble(draw, state)

        # 3. Bottom Footer: Live Context Status Pill
        self._draw_footer(draw, state, dev_data, audio_data, net_data)

        return img

    def _draw_header(self, draw: ImageDraw.ImageDraw, state: GotchiState, net_data: Dict):
        # Name and Level badge
        name_tag = f"{state.name.upper()} Lv.{state.level}"
        draw.text((4, 2), name_tag, font=self.font_bold, fill=0)

        # XP Bar: [40px width]
        xp_pct = min(1.0, max(0.0, state.xp / max(1, state.xp_next)))
        bar_x, bar_y, bar_w, bar_h = 75, 4, 38, 6
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=0, fill=255)
        fill_w = int(bar_w * xp_pct)
        if fill_w > 0:
            draw.rectangle([bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + bar_h - 1], fill=0)

        # Ping & Clock on Right
        now_str = datetime.datetime.now().strftime("%H:%M")
        ping_ms = net_data.get("ping_ms", 0)
        ping_str = f"{int(ping_ms)}ms" if ping_ms < 999 else "OFFLINE"
        
        stat_right = f"{ping_str}  {now_str}"
        draw.text((self.width - 68, 2), stat_right, font=self.font_small, fill=0)

        # Dividing top line
        draw.line([(0, 14), (self.width, 14)], fill=0, width=1)

    def _draw_character_and_bubble(self, draw: ImageDraw.ImageDraw, state: GotchiState):
        # Character Stage (Center-Left: x: 4 to 88, y: 16 to 100)
        face_str = state.face or "( ^‿^ )"
        draw.text((10, 36), face_str, font=self.font_face, fill=0)

        # Cute ASCII pet body under face
        if state.mood in ("DANCING", "MUSIC"):
            body_lines = ["  \\(   )/", "   /   \\ "]
        elif state.mood == "SLEEPING":
            body_lines = ["  ( -_- )", "  zzZZ..."]
        elif state.mood == "CODING":
            body_lines = ["  [💻=⌨️]", "  /     \\"]
        else:
            body_lines = ["  (  o  )", "   /   \\ "]

        draw.text((14, 58), body_lines[0], font=self.font_small, fill=0)
        draw.text((14, 70), body_lines[1], font=self.font_small, fill=0)

        # Mood badge under pet
        mood_badge = f"[{state.mood}]"
        draw.text((12, 85), mood_badge, font=self.font_small, fill=0)

        # Speech Bubble (Center-Right: x: 92 to 244, y: 20 to 98)
        bx1, by1, bx2, by2 = 92, 22, 244, 98
        # Bubble rounded box
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=4, outline=0, fill=255, width=1)

        # Little triangle pointer pointing left to pet
        draw.polygon([(bx1, 48), (bx1 - 5, 52), (bx1, 56)], fill=255, outline=0)
        draw.line([(bx1, 49), (bx1, 55)], fill=255, width=1)  # erase inner line

        # Wrapped text inside bubble
        quote = state.quote or "..."
        lines = self._wrap_text(quote, max_chars=22)
        y_offset = by1 + 6
        for line in lines[:4]:
            draw.text((bx1 + 8, y_offset), line, font=self.font_medium, fill=0)
            y_offset += 14

    def _draw_footer(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        dev_data: Dict,
        audio_data: Dict,
        net_data: Dict,
    ):
        # Dividing bottom line
        draw.line([(0, 103), (self.width, 103)], fill=0, width=1)

        self.footer_cycle = (self.footer_cycle + 1) % 15
        is_playing = audio_data.get("is_playing", False)

        # Footer Mode logic
        if is_playing:
            track = audio_data.get("title", "Track")[:18]
            artist = audio_data.get("artist", "Artist")[:14]
            fmt = audio_data.get("format", "FLAC")
            footer_text = f"♫ {track} - {artist} [{fmt}]"
        elif self.footer_cycle < 8:
            # Dev Stats
            commits = dev_data.get("recent_commits_24h", 0)
            followers = dev_data.get("followers", 24)
            streak = dev_data.get("streak_days", 1)
            footer_text = f"DEV: {commits} commits 24h | Streak: {streak}d | ★ {followers}"
        else:
            # Net & Host Vitals
            cpu = net_data.get("cpu_pct", 10)
            temp = net_data.get("temp_c", 40.0)
            ram = net_data.get("ram_pct", 30)
            footer_text = f"SYS: CPU {cpu}% | RAM {ram}% | {int(temp)}°C"

        draw.text((4, 107), footer_text[:40], font=self.font_small, fill=0)

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
