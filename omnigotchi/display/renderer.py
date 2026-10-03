"""DedSec CyberOS E-Ink Canvas Renderer (250x122 monochrome 1-bit, Techno-Street Art & Webpunk HUD)."""

import datetime
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont

from omnigotchi.core.brain import GotchiState
from omnigotchi.display.dither import (
    draw_dither_rect,
    draw_glitch_bar,
    draw_halftone_strip,
    draw_stencil_badge,
    draw_wrench_mask,
)


class GotchiRenderer:
    def __init__(self, width: int = 250, height: int = 122):
        self.width = width
        self.height = height
        self._init_fonts()

    def _init_fonts(self):
        """Loads authentic cyberpunk and pixel TTF fonts (Silkscreen & ShareTechMono)."""
        fonts_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"
        silkscreen_bold = fonts_dir / "Silkscreen-Bold.ttf"
        share_mono = fonts_dir / "ShareTechMono-Regular.ttf"
        jetbrains_bold = fonts_dir / "JetBrainsMono-Bold.ttf"

        def _get_font(path: Path, size: int):
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size)
                except Exception:
                    pass
            return ImageFont.load_default()

        # Dedicated font roles
        self.font_pixel_hdr = _get_font(silkscreen_bold, 8)
        self.font_pixel_lg = _get_font(silkscreen_bold, 10)
        self.font_mono_bold = _get_font(jetbrains_bold, 10)
        self.font_mono_text = _get_font(share_mono, 10)
        self.font_mono_mini = _get_font(share_mono, 9)
        self.font_mini = _get_font(share_mono, 8)
        self.font_face = _get_font(jetbrains_bold, 12)

    def render(
        self,
        state: GotchiState,
        dev_data: Dict,
        audio_data: Dict,
        net_data: Dict,
        security_data: Optional[Dict] = None,
        bounty_data: Optional[Dict] = None,
    ) -> Image.Image:
        """Composes and returns a 250x122 1-bit PIL image (0=black, 255=white)."""
        img = Image.new("1", (self.width, self.height), 0)
        draw = ImageDraw.Draw(img)
        sec = security_data or {}
        bounty = bounty_data or {}

        mode = state.display_mode.lower()
        if mode == "sentinel":
            self._render_sentinel_hud(draw, state, net_data, sec, bounty)
        elif mode == "terminal":
            self._render_terminal_hud(draw, state, net_data, sec, bounty)
        else:  # "infiltrator" (default)
            self._render_infiltrator_hud(draw, state, dev_data, audio_data, net_data, sec, bounty)

        return img

    def _render_infiltrator_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        dev_data: Dict,
        audio_data: Dict,
        net_data: Dict,
        security_data: Dict,
        bounty_data: Dict,
    ):
        """Mode 1: Watch Dogs 2 SF Webpunk & Techno-Street Art Infiltrator Deck."""
        now_str = datetime.datetime.now().strftime("%H:%M")
        ledger = bounty_data.get("ledger", {})
        daily_usd = ledger.get("daily_usd_rate", 4.20)
        sats = ledger.get("total_sats_earned", 3420)
        shares = ledger.get("total_compute_shares", 1420)
        relayed = ledger.get("total_relayed_mb", 240.0)

        # 1. Inverted Stencil Header Bar (y: 0..13) with Cut Corners
        draw.rectangle([0, 0, self.width, 13], fill=255)
        draw.point((0, 0), fill=0)
        draw.point((self.width - 1, 0), fill=0)
        draw.text((4, 1), f"DEDSEC // ctOS Lv.{state.level}", font=self.font_pixel_hdr, fill=0)

        # Dithered XP Meter Box
        xp_pct = min(1.0, max(0.0, state.xp / max(1, state.xp_next)))
        bar_x, bar_y, bar_w, bar_h = 118, 3, 36, 7
        draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], outline=0, fill=255)
        fill_w = int(bar_w * xp_pct)
        if fill_w > 0:
            draw_dither_rect(draw, (bar_x + 1, bar_y + 1, bar_x + fill_w, bar_y + bar_h - 1), density=0.75, invert=True)

        draw.text((158, 1), f"+${daily_usd:.2f}/d", font=self.font_pixel_hdr, fill=0)
        draw.text((216, 1), now_str, font=self.font_pixel_hdr, fill=0)

        # 2. Left Card: Animated Wrench Mask Goggles & SoC Box (x: 2..80, y: 16..98)
        draw.rectangle([2, 16, 80, 98], outline=255, fill=0)
        # Corner stencil notches
        draw.line([(2, 22), (2, 16), (8, 16)], fill=255, width=2)
        draw.line([(74, 16), (80, 16), (80, 22)], fill=255, width=2)
        draw.line([(2, 92), (2, 98), (8, 98)], fill=255, width=2)
        draw.line([(74, 98), (80, 98), (80, 92)], fill=255, width=2)

        # Render Wrench Mask with active LED expression
        expr = state.face or "X_X"
        draw_wrench_mask(draw, cx=41, cy=32, expression=expr, mood_tag=state.mood, font_mini=self.font_mini)

        # Stencil Mood Sticker under Wrench Mask
        mood_str = f"// {state.mood[:8]} //"
        draw.text((8, 50), mood_str, font=self.font_mini, fill=255)

        # Dithered Divider
        draw_dither_rect(draw, (4, 60, 78, 61), density=0.5)

        cpu_pct = int(net_data.get("cpu_pct", 0))
        temp_c = net_data.get("temp_c", 40.0)
        watt_w = net_data.get("wattage_w", 0.85)
        nodes = ledger.get("active_mesh_nodes", 12)

        draw.text((5, 63), f"CPU: {cpu_pct}%", font=self.font_mini, fill=255)
        draw.text((5, 71), f"PWR: {watt_w:.2f}W", font=self.font_mini, fill=255)
        draw.text((5, 79), f"SOC: {temp_c:.0f}°C", font=self.font_mini, fill=255)
        draw.text((5, 87), f"NODE:{nodes}[OK]", font=self.font_mini, fill=255)

        # 3. Right Card: Wheat-paste Poster & Tactical Siphon Grid (x: 84..247, y: 16..98)
        # Drop shadow dither on bottom and right
        draw_dither_rect(draw, (86, 99, 247, 100), density=0.5)
        draw_dither_rect(draw, (248, 18, 249, 99), density=0.5)

        draw.rectangle([84, 16, 247, 98], outline=255, fill=0)
        draw.line([(84, 22), (84, 16), (90, 16)], fill=255, width=2)
        draw.line([(241, 16), (247, 16), (247, 22)], fill=255, width=2)

        # Target Header with Stencil Badge
        draw.text((88, 18), f"GRID : ctOS MESH [ARMED]", font=self.font_mono_bold, fill=255)
        draw.line([(84, 30), (247, 30)], fill=255, width=1)

        draw.text((88, 33), f"RANK  : {state.title[:18]}", font=self.font_mono_text, fill=255)
        draw.text((88, 46), f"YIELD : {sats:,} sats (+${daily_usd:.2f})", font=self.font_mono_text, fill=255)
        draw.text((88, 59), f"SIPHON: {relayed:.1f}MB | {shares} SHARES", font=self.font_mono_text, fill=255)
        draw.text((88, 72), f"BOUNTY: {bounty_data.get('recent_bounties_found', 0)} HARVESTS", font=self.font_mono_text, fill=255)
        draw.text((88, 85), f"STATUS: DEFCON {state.defcon} {security_data.get('defcon_status', 'SECURE')[:6]}", font=self.font_mono_text, fill=255)

        # 4. Bottom Terminal Footer Bar (y: 101..121) with Glitch Artifact
        draw_glitch_bar(draw, 101, self.width, glitch_offset=6, step=8)

        quote = state.quote or "JOIN US. EXPECT RESISTANCE."
        if len(quote) > 34:
            quote = quote[:32] + ".."
        rx = net_data.get("rx_kbps", 0.0)
        tx = net_data.get("tx_kbps", 0.0)

        draw.text((3, 103), f'> "{quote}"', font=self.font_mini, fill=255)
        draw.text((3, 112), f"> NET: RX {rx:.1f}k TX {tx:.1f}k | SIPHON: ARMED [X_X]", font=self.font_mini, fill=255)

    def _render_sentinel_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        net_data: Dict,
        security_data: Dict,
        bounty_data: Dict,
    ):
        """Mode 2: Watch Dogs Chicago Dark-Ops Paranoia Threat Sentinel."""
        now_str = datetime.datetime.now().strftime("%H:%M")
        threat_score = security_data.get("threat_score", 0)

        # Inverted Header Bar
        draw.rectangle([0, 0, self.width, 13], fill=255)
        draw.text((3, 1), f"SENTINEL // DEFCON {state.defcon}", font=self.font_pixel_hdr, fill=0)
        draw.text((148, 1), f"RISK:{threat_score}%", font=self.font_pixel_hdr, fill=0)
        draw.text((216, 1), now_str, font=self.font_pixel_hdr, fill=0)

        # Left Card: Posture & Defenses (x: 2..86, y: 16..98)
        draw.rectangle([2, 16, 86, 98], outline=255, fill=0, width=1)
        draw.line([(2, 22), (2, 16), (8, 16)], fill=255, width=2)
        draw.line([(80, 16), (86, 16), (86, 22)], fill=255, width=2)

        posture = security_data.get("wifi_posture", {})
        grade = posture.get("grade", "A+")
        score = posture.get("score", 100)
        draw.text((6, 18), f"POSTURE: {grade}", font=self.font_mono_bold, fill=255)
        draw.text((6, 31), f"SCORE  : {score}%", font=self.font_mono_mini, fill=255)
        draw.line([(3, 43), (85, 43)], fill=255, width=1)

        arp_alert = security_data.get("arp_spoof_detected", False)
        arp_str = "POISON!" if arp_alert else "CLEAN"
        ble_count = security_data.get("ble_devices_count", 0)
        ssh_blk = security_data.get("ssh_failed_attempts", 0)

        draw.text((6, 47), f"ARP : {arp_str}", font=self.font_mono_mini, fill=255)
        draw.text((6, 59), f"BLE : {ble_count} BEACONS", font=self.font_mono_mini, fill=255)
        draw.text((6, 71), f"SSH : {ssh_blk} BLOCKED", font=self.font_mono_mini, fill=255)
        draw.text((6, 83), f"PWR : {net_data.get('wattage_w', 0.88):.2f}W", font=self.font_mono_mini, fill=255)

        # Right Card: RF Spectrum & Threat Matrix (x: 90..247, y: 16..98)
        draw.rectangle([90, 16, 247, 98], outline=255, fill=0, width=1)
        draw.line([(90, 22), (90, 16), (96, 16)], fill=255, width=2)
        draw.line([(241, 16), (247, 16), (247, 22)], fill=255, width=2)

        aps_count = security_data.get("wifi_aps_count", 0)
        twin_alert = security_data.get("evil_twin_detected", False)
        twin_str = "TWIN DETECTED!" if twin_alert else "NO ROGUE APs"
        bounties = bounty_data.get("recent_bounties_found", 0)

        draw.text((94, 18), f"RF RADAR: {aps_count} APs SCANNED", font=self.font_mono_bold, fill=255)
        draw.line([(90, 30), (247, 30)], fill=255, width=1)

        draw.text((94, 34), f"TWIN GUARD : {twin_str}", font=self.font_mono_mini, fill=255)
        draw.text((94, 46), f"HARVEST    : {bounties} VULNS FOUND", font=self.font_mono_mini, fill=255)
        draw.text((94, 58), f"LAN NODES  : {security_data.get('lan_hosts_count', 0)} ACTIVE HOSTS", font=self.font_mono_mini, fill=255)
        draw.text((94, 70), f"DNS SHIELD : TLS ENCRYPTED [OK]", font=self.font_mono_mini, fill=255)

        # Dithered Spectrum Graph (CH 1 / 6 / 11)
        draw.text((94, 82), "SPECTRUM   : ", font=self.font_mono_mini, fill=255)
        draw_dither_rect(draw, (168, 83, 184, 91), density=0.75)
        draw.text((170, 83), "1", font=self.font_mini, fill=0)
        draw_dither_rect(draw, (188, 83, 204, 91), density=0.50)
        draw.text((190, 83), "6", font=self.font_mini, fill=0)
        draw_dither_rect(draw, (208, 83, 228, 91), density=0.25)
        draw.text((210, 83), "11", font=self.font_mini, fill=255)

        # Bottom Footer Bar
        draw_glitch_bar(draw, 101, self.width, glitch_offset=3, step=5)
        rx = net_data.get("rx_kbps", 0.0)
        tx = net_data.get("tx_kbps", 0.0)
        draw.text((3, 103), f"> SENTINEL: ALL PERIMETER SHIELDS ARMED & ISOLATED", font=self.font_mini, fill=255)
        draw.text((3, 112), f"> NET: RX {rx:.1f}k TX {tx:.1f}k | SOC: {net_data.get('temp_c', 40.0):.1f}°C [X_X]", font=self.font_mini, fill=255)

    def _render_terminal_hud(
        self,
        draw: ImageDraw.ImageDraw,
        state: GotchiState,
        net_data: Dict,
        security_data: Dict,
        bounty_data: Dict,
    ):
        """Mode 3: Fullscreen DedSec Root CLI & Live Exploit Stream."""
        now_str = datetime.datetime.now().strftime("%H:%M")
        ledger = bounty_data.get("ledger", {})

        # Header
        draw.rectangle([0, 0, self.width, 13], fill=255)
        draw.text((3, 1), f"DEDSEC ROOT SHELL // tty1", font=self.font_pixel_hdr, fill=0)
        draw.text((216, 1), now_str, font=self.font_pixel_hdr, fill=0)

        # Shell frame
        draw.rectangle([2, 16, self.width - 3, self.height - 3], outline=255, fill=0)
        # Dithered vertical scrollbar on right
        draw_dither_rect(draw, (self.width - 6, 18, self.width - 4, self.height - 5), density=0.35)

        # Terminal Lines
        sats = ledger.get("total_sats_earned", 3420)
        daily = ledger.get("daily_usd_rate", 4.20)
        relayed = ledger.get("total_relayed_mb", 240.0)
        bounties = bounty_data.get("recent_bounties_found", 0)

        draw.text((6, 18), "root@dedsec-pi02w:~# ./siphon_mesh.sh", font=self.font_mono_mini, fill=255)
        draw.text((6, 31), f"[OK] ctOS MESH INFILTRATED ({ledger.get('active_mesh_nodes', 12)} NODES)", font=self.font_mono_mini, fill=255)
        draw.text((6, 44), f"[OK] YIELD SIPHON: +${daily:.2f}/d ({sats:,} SATS)", font=self.font_mono_mini, fill=255)
        draw.text((6, 57), f"[OK] RELAY TRANSFERRED: {relayed:.1f} MB [{ledger.get('total_compute_shares', 120)} SHARES]", font=self.font_mono_mini, fill=255)
        draw.text((6, 70), f"[OK] VULN HARVEST: {bounties} TARGETS PERIMETER AUDITED", font=self.font_mono_mini, fill=255)
        draw.text((6, 83), f"[OK] RADAR: {security_data.get('wifi_aps_count', 0)} APs, {security_data.get('ble_devices_count', 0)} BLE BEACONS", font=self.font_mono_mini, fill=255)
        draw.text((6, 96), f"[OK] SHIELDS: ARP-GUARD, PMF, DNS-TLS [LOCKED]", font=self.font_mono_mini, fill=255)
        draw.text((6, 108), "root@dedsec-pi02w:~# _", font=self.font_mono_bold, fill=255)
