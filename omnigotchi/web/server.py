"""Lightweight aiohttp Web Dashboard & Live Screen Mirror for OmniGotchi."""

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
  <title>OmniGotchi Live Companion</title>
  <style>
    :root {
      --bg: #0d0e11;
      --card: #15181e;
      --border: #2b303c;
      --text: #e1e4ea;
      --muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
      --gold: #d29922;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
    body { background: var(--bg); color: var(--text); padding: 24px; display: flex; justify-content: center; }
    .container { max-width: 640px; width: 100%; display: flex; flex-direction: column; gap: 20px; }
    
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 12px; }
    h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; display: flex; align-items: center; gap: 8px; }
    .badge { font-size: 11px; padding: 3px 8px; border-radius: 999px; background: #238636; color: #fff; font-weight: 600; }
    
    /* E-Ink Display Frame */
    .screen-wrapper {
      background: #c3c7c5;
      padding: 12px;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
      border: 3px solid #333;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .screen-label { color: #444; font-size: 11px; font-weight: 700; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
    .screen-img {
      width: 100%;
      max-width: 500px;
      aspect-ratio: 250 / 122;
      image-rendering: pixelated;
      border: 2px solid #222;
      background: #fff;
    }

    /* Stats Grid */
    .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 14px; }
    .card-title { font-size: 12px; color: var(--muted); text-transform: uppercase; font-weight: 600; margin-bottom: 6px; }
    .card-val { font-size: 18px; font-weight: 700; }

    /* Action Buttons */
    .actions { display: flex; gap: 12px; }
    button {
      flex: 1;
      padding: 12px;
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    button:hover { background: #21262d; border-color: var(--accent); }
    button:active { transform: scale(0.98); }
    .btn-primary { background: #238636; border-color: #2ea043; color: white; }
    .btn-primary:hover { background: #2ea043; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>OmniGotchi <span class="badge" id="lvl-badge">Lv. 1</span></h1>
      <div style="font-size: 13px; color: var(--muted);" id="status-line">Connected</div>
    </header>

    <div class="screen-wrapper">
      <div class="screen-label">Waveshare 2.13" E-Ink Live Mirror (250x122)</div>
      <img src="/api/screen.png" alt="Live Screen" class="screen-img" id="live-screen">
    </div>

    <div class="actions">
      <button onclick="sendAction('pet')">🐾 Pet Omni (+10 XP)</button>
      <button class="btn-primary" onclick="sendAction('feed')">🍕 Feed Bytes (+15 XP)</button>
      <button onclick="sendAction('flip')">🔄 Flip Screen (180°)</button>
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
        <div class="card-title">Network & Screen</div>
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
          document.getElementById('mood-val').innerText = data.brain.mood + ' ' + data.brain.face;
          document.getElementById('title-val').innerText = data.brain.title;
          document.getElementById('xp-val').innerText = data.brain.xp + ' / ' + data.brain.xp_next;
          document.getElementById('ping-val').innerText = data.net.ping_ms + ' ms • ' + (data.brain.rotation || 0) + '°';
        }
      } catch (e) {}
    }
    setInterval(updateStats, 2000);
    updateStats();

    async function sendAction(act) {
      await fetch('/api/action/' + act, { method: 'POST' });
      updateStats();
      refreshScreen();
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
            return web.Response(status=404)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return web.Response(body=buf.getvalue(), content_type="image/png")

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
            },
            "dev": self.engine.dev_data,
            "audio": self.engine.audio_data,
            "net": self.engine.net_data,
        }
        return web.Response(text=json.dumps(data), content_type="application/json")

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
