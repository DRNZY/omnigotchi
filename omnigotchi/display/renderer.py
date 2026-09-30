"""Pwnagotchi-inspired E-Ink Canvas Renderer (250x122 monochrome 1-bit, Obsidian Dark Mode)."""

import datetime
from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont

from omnigotchi.core.brain import GotchiState


class GotchiRenderer:
    def __init__(self, width: int = 250, height: int = 122):
        self.width = width
        self.height = height
        self._init_fonts()

    def _init_fonts(self):
        """Loads available system TTF fonts with clean fallbacks."""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/TTF/LiberationMono-Regular.ttf",
        ]
        bold_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/TTF/LiberationMono-Bold.ttf",
        ]

        self.font_tiny = None
        self.font_small = None
        self.font_medium = None
        self.font_bold = None
        self.font_face = None

        for p in font_paths:
            try:
                self.font_tiny = ImageFont.truetype(p, 8)
                self.font_small = ImageFont.truetype(p, 9)
                self.font_medium = ImageFont.truetype(p, 10)
                break
            except Exception:
                continue

        for p in bold_paths:
            try:
                self.font_bold = ImageFont.truetype(p, 9)
                self.font_face = ImageFont.truetype(p, 14)
                break
            except Exception:
                continue

        if self.font_tiny is None:
            self.font_tiny = ImageFont.load_default()
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
        """Composes and returns a 250x122 1-bit PIL image (0=black background, 255=white text/lines)."""
        # Dark Obsidian background (0 = Black)
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
        draw.text((3, 2), name_tag, font=self.font_bold, fill=255)

        # XP Bar [32px]
        xp_pct = min(1.0, max(0.0, state.xp / max(1, state.xp_next)))
        bar_x, bar_y, bar_w, bar_h = 58, 4, 32, 6
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=255, fill=0)
        fill_w = int(bar_w * xp_pct)
        if fill_w > 0:
            draw.rectangle([bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + bar_h - 1], fill=255)

        # Defcon & Clock
        defcon_str = f"DEFCON {state.defcon}"
        draw.text((96, 2), defcon_str, font=self.font_small, fill=255)
        draw.text((220, 2), now_str, font=self.font_bold, fill=255)
        draw.line([(0, 14), (self.width, 14)], fill=255, width=1)

        # 2. Left Card: Avatar + Real-Time Hardware Gauges (x: 2..80, y: 16..98)
        draw.rounded_rectangle([2, 16, 80, 98], radius=3, outline=255, fill=0, width=1)
        face_str = state.face or "( ◕ ‿ ◕ )"
        draw.text((5, 20), face_str, font=self.font_face, fill=255)
        mood_str = f"[{state.mood[:7]}]"
        draw.text((16, 42), mood_str, font=self.font_small, fill=255)

        # Divider inside left card
        draw.line([(4, 56), (78, 56)], fill=255, width=1)
        ram_pct = net_data.get("ram_pct", 0)
        cpu_pct = net_data.get("cpu_pct", 0)
        temp_c = net_data.get("temp_c", 40.0)
        watt_w = net_data.get("wattage_w", 0.85)
        ping_ms = int(net_data.get("ping_ms", 0))

        draw.text((5, 59), f"RAM {ram_pct}% CPU {cpu_pct}%", font=self.font_tiny, fill=255)
        draw.text((5, 71), f"{temp_c}°C   {watt_w}W", font=self.font_tiny, fill=255)
        draw.text((5, 83), f"PING: {ping_ms}ms", font=self.font_tiny, fill=255)

        # 3. Right Card: Speech Bubble + Full Vitals & Cyber Matrix (x: 84..247, y: 16..98)
        draw.rounded_rectangle([84, 16, 247, 98], radius=3, outline=255, fill=0, width=1)
        # Bubble pointer
        draw.polygon([(84, 27), (80, 30), (84, 33)], fill=0, outline=255)

        # Quote / Status dialogue
        quote = state.quote or "System running like silk."
        if len(quote) > 28:
            quote = quote[:26] + ".."
        draw.text((88, 19), f'"{quote}"', font=self.font_small, fill=255)
        draw.line([(84, 33), (247, 33)], fill=255, width=1)

        # Vitals Matrix Grid
        ram_used = net_data.get("ram_used_mb", 0)
        ram_total = net_data.get("ram_total_mb", 512)
        lan_hosts = security_data.get("lan_hosts_count", 0)
        arp_ok = "Clean" if not security_data.get("arp_spoof_detected", False) else "ALERT"
        wifi_aps = security_data.get("wifi_aps_count", 0)
        ssh_blocked = security_data.get("ssh_failed_attempts", 0)
        dns_ok = "SECURE" if not security_data.get("dns_hijack_detected", False) else "HIJACK"
        ports_count = len(security_data.get("open_ports", []))
        sec_status = security_data.get("defcon_status", "ALL SHIELDS NOMINAL")[:23]

        draw.text((88, 36), f"RAM : {ram_used}/{ram_total}MB ({ram_pct}%)", font=self.font_small, fill=255)
        draw.text((88, 48), f"SYS : CPU {cpu_pct}% ({watt_w}W) | PING: {ping_ms}ms", font=self.font_small, fill=255)
        draw.text((88, 60), f"NET : {lan_hosts} LAN (ARP:{arp_ok}) | {wifi_aps} RF APs", font=self.font_small, fill=255)
        draw.text((88, 72), f"SEC : SSH {ssh_blocked} blk | DNS OK | {ports_count} Ports", font=self.font_small, fill=255)
        draw.text((88, 84), f"STAT: {sec_status}", font=self.font_bold, fill=255)

        # 4. Bottom Footer Bar (y: 101..121)
        draw.line([(0, 101), (self.width, 101)], fill=255, width=1)
        is_playing = audio_data.get("is_playing", False)
        if is_playing:
            track = audio_data.get("title", "Track")[:20]
            artist = audio_data.get("artist", "Artist")[:15]
            fmt = audio_data.get("format", "FLAC")
            footer_line1 = f"♫ {track} - {artist} [{fmt}]"
        else:
            commits = dev_data.get("recent_commits_24h", 0)
            streak = dev_data.get("streak_days", 1)
            ssid = net_data.get("wifi_ssid", "LAN")[:12]
            footer_line1 = f"DEV: {commits} commits (24h) | Streak: {streak}d | Wi-Fi: {ssid}"

        rx = net_data.get("rx_kbps", 0.0)
        tx = net_data.get("tx_kbps", 0.0)
        uptime = net_data.get("uptime_str", "0h")
        footer_line2 = f"NET: RX {rx}k/s TX {tx}k/s | Up: {uptime} | {temp_c}°C"

        draw.text((3, 103), footer_line1[:46], font=self.font_tiny, fill=255)
        draw.text((3, 112), footer_line2[:46], font=self.font_tiny, fill=255)

    def _render_sentinel_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        net_data: Dict,
        security_data: Dict,
    ):
        """Renders clean Cyber Defense Tactical HUD in Dark Mode."""
        # Top Bar
        now_str = datetime.datetime.now().strftime("%H:%M")
        draw.text((3, 2), f"SENTINEL [DEFCON {state.defcon}]", font=self.font_bold, fill=255)
        draw.text((135, 2), f"SCANS:{state.total_security_scans}", font=self.font_tiny, fill=255)
        draw.text((220, 2), now_str, font=self.font_bold, fill=255)
        draw.line([(0, 14), (self.width, 14)], fill=255, width=1)

        # Left Stage: Avatar + Threat Level (x: 2..80, y: 16..98)
        draw.rounded_rectangle([2, 16, 80, 98], radius=3, outline=255, fill=0, width=1)
        face_str = state.face or "( ◉ _ ◉ )"
        draw.text((5, 20), face_str, font=self.font_face, fill=255)
        draw.text((10, 42), "[SENTINEL]", font=self.font_small, fill=255)

        draw.line([(4, 56), (78, 56)], fill=255, width=1)
        threat_score = min(100, max(0, security_data.get("threat_score", 0)))
        draw.text((5, 59), f"THREAT: {threat_score}%", font=self.font_tiny, fill=255)
        # Threat bar
        draw.rectangle([5, 71, 75, 77], outline=255, fill=0)
        t_fill = int((threat_score / 100.0) * 68)
        if t_fill > 0:
            draw.rectangle([6, 72, 6 + t_fill, 76], fill=255)
        temp_c = net_data.get("temp_c", 40.0)
        watt_w = net_data.get("wattage_w", 0.85)
        draw.text((5, 83), f"{temp_c}°C   {watt_w}W", font=self.font_tiny, fill=255)

        # Right Stage: Tactical Matrix Box (x: 84..247, y: 16..98)
        draw.rounded_rectangle([84, 16, 247, 98], radius=3, outline=255, fill=0, width=1)
        draw.polygon([(84, 27), (80, 30), (84, 33)], fill=0, outline=255)

        draw.text((88, 19), ">> TACTICAL DEFENSE MATRIX <<", font=self.font_bold, fill=255)
        draw.line([(84, 33), (247, 33)], fill=255, width=1)

        lan_hosts = security_data.get("lan_hosts_count", 0)
        arp_ok = "OK" if not security_data.get("arp_spoof_detected", False) else "ALERT"
        wifi_aps = security_data.get("wifi_aps_count", 0)
        evil_twin = "0" if not security_data.get("evil_twin_detected", False) else "WARN"
        ssh_blocked = security_data.get("ssh_failed_attempts", 0)
        dns_ok = "SECURE" if not security_data.get("dns_hijack_detected", False) else "HIJACK"
        ports_count = len(security_data.get("open_ports", []))
        status_line = security_data.get("defcon_status", "ALL SHIELDS NOMINAL")[:23]

        draw.text((88, 36), f"LAN NODES: {lan_hosts} (ARP:{arp_ok})", font=self.font_small, fill=255)
        draw.text((88, 48), f"RF BEACONS: {wifi_aps} (TWIN:{evil_twin})", font=self.font_small, fill=255)
        draw.text((88, 60), f"SSH SHIELD: {ssh_blocked} blk | DNS:{dns_ok}", font=self.font_small, fill=255)
        draw.text((88, 72), f"OPEN PORTS: {ports_count} active", font=self.font_small, fill=255)
        draw.text((88, 84), f"STATUS: {status_line}", font=self.font_bold, fill=255)

        # Footer
        draw.line([(0, 101), (self.width, 101)], fill=255, width=1)
        ping_ms = int(net_data.get("ping_ms", 0))
        cpu_pct = net_data.get("cpu_pct", 0)
        ram_pct = net_data.get("ram_pct", 0)
        draw.text((3, 103), "SHIELDS: ARP-GUARD * RF-RADAR * AUTH-SHIELD * DNS", font=self.font_tiny, fill=255)
        draw.text((3, 112), f"SYS: PING {ping_ms}ms | CPU {cpu_pct}% | RAM {ram_pct}% | {watt_w}W", font=self.font_tiny, fill=255)
