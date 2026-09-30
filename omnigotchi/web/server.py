"""Lightweight aiohttp Web Dashboard & Live Screen Mirror for OmniGotchi with Cybersecurity Sentinel."""

import io
import json
import logging
from typing import TYPE_CHECKING
from aiohttp import web

if TYPE_CHECKING:
    from omnigotchi.core.scheduler import GotchiEngine

logger = logging.getLogger("omnigotchi.web")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OmniGotchi Cyber Defense Sentinel</title>
  <style>
    :root {
      --bg: #0b0c10;
      --card: #151821;
      --subtle: #1c202c;
      --border: #282f42;
      --text: #e1e6f0;
      --muted: #838ea3;
      --accent: #58a6ff;
      --green: #3fb950;
      --gold: #d29922;
      --red: #f85149;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
    body { background: var(--bg); color: var(--text); padding: 24px; display: flex; justify-content: center; }
    .container { max-width: 680px; width: 100%; display: flex; flex-direction: column; gap: 16px; }
    
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 12px; }
    h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; display: flex; align-items: center; gap: 8px; }
    .badges { display: flex; gap: 8px; }
    .badge { font-size: 11px; padding: 3px 8px; border-radius: 999px; background: #238636; color: #fff; font-weight: 600; }
    .defcon-badge { font-size: 11px; padding: 3px 8px; border-radius: 999px; background: #1f6feb; color: #fff; font-weight: 700; }
    
    /* E-Ink Display Frame */
    .screen-wrapper {
      background: #c3c7c5;
      padding: 12px;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6);
      border: 3px solid #333;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .screen-header { width: 100%; max-width: 500px; display: flex; justify-content: space-between; margin-bottom: 6px; }
    .screen-label { color: #333; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .screen-rot { color: #444; font-size: 11px; font-family: monospace; font-weight: 700; }
    .screen-img {
      width: 100%;
      max-width: 500px;
      aspect-ratio: 250 / 122;
      image-rendering: pixelated;
      border: 2px solid #222;
      background: #fff;
    }

    /* Action Buttons */
    .actions { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
    button {
      padding: 10px 8px;
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--text);
      font-size: 13px;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    button:hover { background: #212638; border-color: var(--accent); }
    button:active { transform: scale(0.98); }
    .btn-primary { background: #238636; border-color: #2ea043; color: white; }
    .btn-primary:hover { background: #2ea043; }
    .btn-defend { background: #1f6feb; border-color: #388bfd; color: white; }
    .btn-defend:hover { background: #388bfd; }

    /* Stats Grid */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
    .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }
    .card-val { font-size: 16px; font-weight: 700; }
    
    /* Security Section */
    .sec-section { background: var(--subtle); border: 1px solid var(--border); border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
    .sec-header { display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 700; color: var(--accent); }
    .sec-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11px; }
    .sec-item { background: rgba(0,0,0,0.3); padding: 6px 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.05); }
    .sec-item-title { color: var(--muted); font-size: 10px; text-transform: uppercase; margin-bottom: 2px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>OmniGotchi <span class="badge" id="lvl-badge">Lv. 1</span></h1>
      <div class="badges">
        <span class="defcon-badge" id="defcon-badge">DEFCON 5 SECURE</span>
      </div>
    </header>

    <div class="screen-wrapper">
      <div class="screen-header">
        <span class="screen-label">Waveshare 2.13" E-Ink Live Mirror</span>
        <span class="screen-rot" id="rot-label">0° • COMPANION</span>
      </div>
      <img src="/api/screen.png" alt="Live Screen" class="screen-img" id="live-screen">
    </div>

    <div class="actions">
      <button onclick="sendAction('pet')">🐾 Pet (+10)</button>
      <button class="btn-primary" onclick="sendAction('feed')">🍕 Feed (+15)</button>
      <button class="btn-defend" onclick="sendAction('scan')">🛡️ Scan LAN & RF</button>
      <button onclick="sendAction('flip')">🔄 Flip (180°)</button>
    </div>

    <div class="actions" style="grid-template-columns: repeat(2, 1fr);">
      <button onclick="sendAction('mode')">🖥️ Toggle HUD (Companion / Sentinel)</button>
      <button onclick="sendAction('recover')">⚡ Unstick & Clear Display</button>
    </div>

    <div class="sec-section">
      <div class="sec-header">
        <span>CYBERSECURITY SENTINEL & RADAR</span>
        <span id="threat-score-label">THREAT: 0%</span>
      </div>
      <div class="sec-grid">
        <div class="sec-item">
          <div class="sec-item-title">LAN Devices</div>
          <div id="lan-val" style="font-weight:700;">-- Nodes</div>
        </div>
        <div class="sec-item">
          <div class="sec-item-title">Wi-Fi Beacons</div>
          <div id="rf-val" style="font-weight:700;">-- APs</div>
        </div>
        <div class="sec-item">
          <div class="sec-item-title">ARP & Twin Guard</div>
          <div id="arp-val" style="font-weight:700; color: var(--green);">SECURE</div>
        </div>
        <div class="sec-item">
          <div class="sec-item-title">SSH Guard</div>
          <div id="ssh-val" style="font-weight:700;">0 Blocked</div>
        </div>
        <div class="sec-item">
          <div class="sec-item-title">Open Ports</div>
          <div id="ports-val" style="font-weight:700;">-- Ports</div>
        </div>
        <div class="sec-item">
          <div class="sec-item-title">Pi Vitals</div>
          <div id="soc-val" style="font-weight:700;">--°C</div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <div class="card-title">Mood & Personality</div>
        <div class="card-val" id="mood-val">HAPPY</div>
      </div>
      <div class="card">
        <div class="card-title">Title & Rank</div>
        <div class="card-val" id="title-val">Script Novice</div>
      </div>
      <div class="card">
        <div class="card-title">XP Progress</div>
        <div class="card-val" id="xp-val">0 / 100</div>
      </div>
      <div class="card">
        <div class="card-title">Ping & Wi-Fi</div>
        <div class="card-val" id="ping-val">-- ms</div>
      </div>
    </div>
  </div>

  <script>
    function refreshScreen() {
      const img = document.getElementById('live-screen');
      img.src = '/api/screen.png?t=' + Date.now();
    }
    setInterval(refreshScreen, 2000);

    async function updateStats() {
      try {
        const res = await fetch('/api/stats');
        if (res.ok) {
          const data = await res.json();
          document.getElementById('lvl-badge').innerText = 'Lv. ' + data.brain.level;
          document.getElementById('defcon-badge').innerText = 'DEFCON ' + data.brain.defcon + ' ' + (data.security?.defcon_status || 'SECURE');
          document.getElementById('rot-label').innerText = (data.brain.rotation || 0) + '° • ' + (data.brain.display_mode || 'companion').toUpperCase();
          document.getElementById('mood-val').innerText = data.brain.mood + ' ' + data.brain.face;
          document.getElementById('title-val').innerText = data.brain.title;
          document.getElementById('xp-val').innerText = data.brain.xp + ' / ' + data.brain.xp_next;
          document.getElementById('ping-val').innerText = data.net.ping_ms + ' ms • ' + data.net.wifi_ssid;

          if (data.security) {
            document.getElementById('lan-val').innerText = data.security.lan_hosts_count + ' Nodes';
            document.getElementById('rf-val').innerText = data.security.wifi_aps_count + ' APs';
            document.getElementById('arp-val').innerText = data.security.arp_spoof_detected ? 'POISON ALERT' : 'SECURE';
            document.getElementById('arp-val').style.color = data.security.arp_spoof_detected ? 'var(--red)' : 'var(--green)';
            document.getElementById('ssh-val').innerText = data.security.ssh_failed_attempts + ' Blocked';
            document.getElementById('ports-val').innerText = data.security.open_ports?.length + ' Active';
            document.getElementById('threat-score-label').innerText = 'THREAT: ' + (data.security.threat_score || 0) + '%';
          }
          if (data.net) {
            document.getElementById('soc-val').innerText = data.net.temp_c + '°C • ' + data.net.cpu_pct + '% CPU';
          }
        }
      } catch (e) {}
    }
    setInterval(updateStats, 2000);
    updateStats();

    async function sendAction(act) {
      await fetch('/api/action/' + act, { method: 'POST' });
      updateStats();
      setTimeout(refreshScreen, 150);
    }
  </script>
</body>
</html>
"""


class GotchiWebServer:
    def __init__(self, engine: "GotchiEngine", host: str = "0.0.0.0", port: int = 8000):
        self.engine = engine
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()
        self.runner = None
        self.site = None

    def _setup_routes(self):
        self.app.router.add_get("/", self._handle_index)
        self.app.router.add_get("/api/screen.png", self._handle_screen_png)
        self.app.router.add_get("/api/stats", self._handle_stats_json)
        self.app.router.add_post("/api/action/pet", self._handle_pet)
        self.app.router.add_post("/api/action/feed", self._handle_feed)
        self.app.router.add_post("/api/action/flip", self._handle_flip)
        self.app.router.add_post("/api/action/scan", self._handle_scan)
        self.app.router.add_post("/api/action/mode", self._handle_mode)
        self.app.router.add_post("/api/action/recover", self._handle_recover)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"OmniGotchi Web Companion running on http://{self.host}:{self.port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    async def _handle_index(self, request: web.Request) -> web.Response:
        return web.Response(text=HTML_TEMPLATE, content_type="text/html")

    async def _handle_screen_png(self, request: web.Request) -> web.Response:
        img = self.engine.current_image
        if img is None:
            # Generate fallback frame if not yet rendered
            self.engine.trigger_render(partial=False)
            img = self.engine.current_image
            if img is None:
                return web.Response(status=503)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return web.Response(
            body=buf.getvalue(),
            content_type="image/png",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    async def _handle_stats_json(self, request: web.Request) -> web.Response:
        data = {
            "brain": {
                "name": self.engine.brain.state.name,
                "level": self.engine.brain.state.level,
                "xp": self.engine.brain.state.xp,
                "xp_next": self.engine.brain.state.xp_next,
                "mood": self.engine.brain.state.mood,
                "face": self.engine.brain.state.face,
                "quote": self.engine.brain.state.quote,
                "title": self.engine.brain.state.title,
                "hunger": self.engine.brain.state.hunger,
                "happiness": self.engine.brain.state.happiness,
                "rotation": self.engine.brain.state.rotation,
                "display_mode": self.engine.brain.state.display_mode,
                "defcon": self.engine.brain.state.defcon,
                "threat_status": self.engine.brain.state.threat_status,
                "total_security_scans": self.engine.brain.state.total_security_scans,
            },
            "dev": self.engine.dev_data,
            "audio": self.engine.audio_data,
            "net": self.engine.net_data,
            "security": self.engine.security_data,
        }
        return web.Response(
            text=json.dumps(data),
            content_type="application/json",
            headers={"Cache-Control": "no-cache"},
        )

    async def _handle_pet(self, request: web.Request) -> web.Response:
        self.engine.brain.pet()
        self.engine.trigger_render()
        return web.Response(text=json.dumps({"ok": True}), content_type="application/json")

    async def _handle_feed(self, request: web.Request) -> web.Response:
        self.engine.brain.feed()
        self.engine.trigger_render()
        return web.Response(text=json.dumps({"ok": True}), content_type="application/json")

    async def _handle_flip(self, request: web.Request) -> web.Response:
        new_rot = self.engine.flip_screen()
        return web.Response(text=json.dumps({"ok": True, "rotation": new_rot}), content_type="application/json")

    async def _handle_scan(self, request: web.Request) -> web.Response:
        sec_data = await self.engine.scan_security()
        return web.Response(text=json.dumps({"ok": True, "security": sec_data}), content_type="application/json")

    async def _handle_mode(self, request: web.Request) -> web.Response:
        mode = self.engine.toggle_display_mode()
        return web.Response(text=json.dumps({"ok": True, "mode": mode}), content_type="application/json")

    async def _handle_recover(self, request: web.Request) -> web.Response:
        self.engine.recover_display()
        return web.Response(text=json.dumps({"ok": True, "recovered": True}), content_type="application/json")
