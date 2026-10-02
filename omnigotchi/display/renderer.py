"""DedSec CyberOS E-Ink Canvas Renderer (250x122 monochrome 1-bit, Glitch Hacker HUD)."""

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
        bounty_data: Optional[Dict] = None,
    ) -> Image.Image:
        """Composes and returns a 250x122 1-bit PIL image (0=black background, 255=white text/lines)."""
        img = Image.new("1", (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)
        sec = security_data or {}
        bounty = bounty_data or {}

        if state.display_mode == "sentinel":
            self._render_sentinel_hud(draw, state, net_data, sec, bounty)
        else:
            self._render_dedsec_hud(draw, state, dev_data, audio_data, net_data, sec, bounty)

        return img

    def _render_dedsec_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        dev_data: Dict,
        audio_data: Dict,
        net_data: Dict,
        security_data: Dict,
        bounty_data: Dict,
    ):
        # 1. DedSec Glitched Header Bar (y: 0..14)
        now_str = datetime.datetime.now().strftime("%H:%M")
        name_tag = f"[X_X] DEDSEC Lv.{state.level}"
        draw.text((4, 1), name_tag, font=self.font_hdr, fill=255)

        # XP Bar [45px]
        xp_pct = min(1.0, max(0.0, state.xp / max(1, state.xp_next)))
        bar_x, bar_y, bar_w, bar_h = 105, 4, 42, 6
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=255, fill=0)
        fill_w = int(bar_w * xp_pct)
        if fill_w > 0:
            draw.rectangle([bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + bar_h - 1], fill=255)

        # Yield counter tag
        ledger = bounty_data.get("ledger", {})
        daily_usd = ledger.get("daily_usd_rate", 4.20)
        draw.text((154, 1), f"${daily_usd:.2f}/d", font=self.font_mini, fill=255)
        draw.text((216, 1), now_str, font=self.font_hdr, fill=255)
        
        # Glitch line divider
        draw.line([(0, 14), (self.width, 14)], fill=255, width=1)
        draw.rectangle([78, 13, 84, 15], fill=255)

        # 2. Left Card: DedSec Hacker Pet Box (x: 2..76, y: 16..98)
        draw.rectangle([2, 16, 76, 98], outline=255, fill=0, width=1)
        # Hacker corner accents
        draw.line([(2, 22), (2, 16), (8, 16)], fill=255, width=2)
        draw.line([(70, 16), (76, 16), (76, 22)], fill=255, width=2)
        draw.line([(2, 92), (2, 98), (8, 98)], fill=255, width=2)
        draw.line([(70, 98), (76, 98), (76, 92)], fill=255, width=2)

        face_str = state.face or "[ X _ X ]"
        fb = self.font_face.getbbox(face_str)
        fw = fb[2] - fb[0]
        fx = 2 + max(0, (74 - fw) // 2)
        draw.text((fx, 20), face_str, font=self.font_face, fill=255)

        mood_str = f"//{state.mood[:7]}//"
        mb = self.font_mini.getbbox(mood_str)
        mw = mb[2] - mb[0]
        mx = 2 + max(0, (74 - mw) // 2)
        draw.text((mx, 38), mood_str, font=self.font_mini, fill=255)

        # Divider inside left card
        draw.line([(3, 50), (75, 50)], fill=255, width=1)
        ram_pct = int(net_data.get("ram_pct", 0))
        cpu_pct = int(net_data.get("cpu_pct", 0))
        temp_c = net_data.get("temp_c", 40.0)
        watt_w = net_data.get("wattage_w", 0.85)
        ping_ms = int(net_data.get("ping_ms", 0))

        draw.text((5, 53), f"CPU:{cpu_pct}% R:{ram_pct}%", font=self.font_mini, fill=255)
        draw.text((5, 64), f"PWR:{watt_w:.2f}W {temp_c:.0f}°C", font=self.font_mini, fill=255)
        draw.text((5, 75), f"PING:{ping_ms}ms DEF:{state.defcon}", font=self.font_mini, fill=255)
        draw.text((5, 86), f"NODES:{ledger.get('active_mesh_nodes', 12)} [OK]", font=self.font_mini, fill=255)

        # 3. Right Card: DedSec Broadcast & Yield Matrix (x: 80..247, y: 16..98)
        draw.rectangle([80, 16, 247, 98], outline=255, fill=0, width=1)
        draw.line([(80, 22), (80, 16), (86, 16)], fill=255, width=2)
        draw.line([(241, 16), (247, 16), (247, 22)], fill=255, width=2)

        # Quote / DedSec Broadcast Banner
        quote = state.quote or "DedSec gives you truth."
        if len(quote) > 28:
            quote = quote[:26] + ".."
        draw.text((84, 18), f'"{quote}"', font=self.font_text, fill=255)
        draw.line([(80, 30), (247, 30)], fill=255, width=1)

        # DedSec Yield Matrix
        sats = ledger.get("total_sats_earned", 3420)
        shares = ledger.get("total_compute_shares", 1420)
        relayed = ledger.get("total_relayed_mb", 240.0)
        bounties_found = bounty_data.get("recent_bounties_found", 0)
        title_str = state.title[:16]

        draw.text((84, 33), f"RANK : {title_str}", font=self.font_text, fill=255)
        draw.text((84, 45), f"YIELD: {sats:,} sats (${daily_usd:.2f}/d)", font=self.font_text, fill=255)
        draw.text((84, 57), f"RELAY: {relayed:.1f} MB | {shares} SHARES", font=self.font_text, fill=255)
        draw.text((84, 69), f"AUDIT: {bounties_found} BOUNTIES LOGGED", font=self.font_text, fill=255)
        draw.text((84, 81), f"GRID : ctOS MESH ENCRYPTED", font=self.font_text, fill=255)

        # 4. Bottom Footer Bar (y: 100..121)
        draw.line([(0, 100), (self.width, 100)], fill=255, width=1)
        is_playing = audio_data.get("is_playing", False)
        if is_playing:
            track = audio_data.get("title", "Track")[:18]
            artist = audio_data.get("artist", "Artist")[:14]
            fmt = audio_data.get("format", "FLAC")
            footer_line1 = f"AUDIO: {track} - {artist} [{fmt}]"
        else:
            commits = dev_data.get("recent_commits_24h", 0)
            streak = dev_data.get("streak_days", 1)
            footer_line1 = f"DEV: {commits} commits | Streak: {streak}d | MESH: ARMED"

        rx = net_data.get("rx_kbps", 0.0)
        tx = net_data.get("tx_kbps", 0.0)
        footer_line2 = f"NET: RX {rx:.1f}k TX {tx:.1f}k | SHIELD: ENGAGED [X_X]"

        draw.text((4, 102), footer_line1, font=self.font_mini, fill=255)
        draw.text((4, 111), footer_line2, font=self.font_mini, fill=255)

    def _render_sentinel_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        net_data: Dict,
        security_data: Dict,
        bounty_data: Dict,
    ):
        """Dedicated Tactical Cybersecurity & Perimeter Defense E-Ink Screen."""
        now_str = datetime.datetime.now().strftime("%H:%M")
        name_tag = f"[X_X] SENTINEL DEFCON {state.defcon}"
        draw.text((4, 1), name_tag, font=self.font_hdr, fill=255)

        threat_score = security_data.get("threat_score", 0)
        draw.text((150, 1), f"THREAT:{threat_score}%", font=self.font_mini, fill=255)
        draw.text((216, 1), now_str, font=self.font_hdr, fill=255)

        # Glitch line divider
        draw.line([(0, 14), (self.width, 14)], fill=255, width=1)
        draw.rectangle([130, 13, 138, 15], fill=255)

        # Left Card: Tactical Posture (x: 2..86, y: 16..98)
        draw.rectangle([2, 16, 86, 98], outline=255, fill=0, width=1)
        draw.line([(2, 22), (2, 16), (8, 16)], fill=255, width=2)
        draw.line([(80, 16), (86, 16), (86, 22)], fill=255, width=2)
        
        posture = security_data.get("wifi_posture", {})
        grade = posture.get("grade", "A+")
        score = posture.get("score", 100)
        draw.text((6, 18), f"POSTURE: {grade}", font=self.font_hdr, fill=255)
        draw.text((6, 31), f"SCORE : {score}%", font=self.font_mini, fill=255)
        draw.line([(3, 42), (85, 42)], fill=255, width=1)

        arp_alert = security_data.get("arp_spoof_detected", False)
        arp_status = "POISON!" if arp_alert else "CLEAN"
        ble_count = security_data.get("ble_devices_count", 0)
        ssh_blk = security_data.get("ssh_failed_attempts", 0)

        draw.text((6, 46), f"ARP: {arp_status}", font=self.font_mini, fill=255)
        draw.text((6, 58), f"BLE: {ble_count} BEACONS", font=self.font_mini, fill=255)
        draw.text((6, 70), f"SSH: {ssh_blk} BLOCKED", font=self.font_mini, fill=255)
        draw.text((6, 82), f"PWR: {net_data.get('wattage_w', 0.88):.2f}W", font=self.font_mini, fill=255)

        # Right Card: RF Spectrum & Bounty Harvester (x: 90..247, y: 16..98)
        draw.rectangle([90, 16, 247, 98], outline=255, fill=0, width=1)
        draw.line([(90, 22), (90, 16), (96, 16)], fill=255, width=2)
        draw.line([(241, 16), (247, 16), (247, 22)], fill=255, width=2)

        aps_count = security_data.get("wifi_aps_count", 0)
        twin_alert = security_data.get("evil_twin_detected", False)
        twin_str = "TWIN DETECTED!" if twin_alert else "NO ROGUE APs"
        bounties_found = bounty_data.get("recent_bounties_found", 0)
        ledger = bounty_data.get("ledger", {})
        daily_usd = ledger.get("daily_usd_rate", 4.20)

        draw.text((94, 18), f"RF APs: {aps_count} IN RANGE", font=self.font_text, fill=255)
        draw.line([(90, 30), (247, 30)], fill=255, width=1)

        draw.text((94, 34), f"TWIN GUARD : {twin_str}", font=self.font_mini, fill=255)
        draw.text((94, 46), f"VULN BOUNTY: {bounties_found} LOGGED (${daily_usd:.2f}/d)", font=self.font_mini, fill=255)
        draw.text((94, 58), f"ctOS RELAY : {ledger.get('total_relayed_mb', 0.0):.1f} MB RELAYED", font=self.font_mini, fill=255)
        draw.text((94, 70), f"LAN NODES  : {security_data.get('lan_hosts_count', 0)} NODES ACTIVE", font=self.font_mini, fill=255)
        draw.text((94, 82), f"DNS SHIELD : TLS ENCRYPTED [OK]", font=self.font_mini, fill=255)

        # Bottom Footer Bar
        draw.line([(0, 100), (self.width, 100)], fill=255, width=1)
        rx = net_data.get("rx_kbps", 0.0)
        tx = net_data.get("tx_kbps", 0.0)
        temp_c = net_data.get("temp_c", 41.5)
        draw.text((4, 102), f"SENTINEL: ALL PERIMETER SHIELDS ARMED & LOCKED", font=self.font_mini, fill=255)
        draw.text((4, 111), f"NET: RX {rx:.1f}k TX {tx:.1f}k | SOC: {temp_c:.1f}°C [X_X]", font=self.font_mini, fill=255)

