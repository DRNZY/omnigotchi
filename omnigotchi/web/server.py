"""DedSec CyberOS Web Dashboard & Live Screen Mirror for OmniGotchi.

Features authentic Watch Dogs DedSec styling (Electric Cyan, Acid Green, Glitch Magenta),
live Satoshi & USD yield counters, active bandwidth/compute relay tracking, and white-hat
bug bounty report extraction.
"""

from dataclasses import asdict
import io
import json
import logging
import time
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
  <title>DEDSEC // TECHNO-STREET OPERATIVE DECK</title>
  <style>
    :root {
      --bg: #06070a;
      --panel: #0a0e17;
      --card: #0f1522;
      --border: #1a2336;
      --cyan: #00F0FF;
      --green: #00FF66;
      --magenta: #FF0055;
      --yellow: #FFE600;
      --text: #f0f6fc;
      --muted: #7284a8;
      --dither: #182236;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Courier New", "Lucida Console", Monaco, monospace; }
    body {
      background: var(--bg);
      color: var(--text);
      padding: 18px;
      display: flex;
      justify-content: center;
      background-image: 
        radial-gradient(var(--border) 15%, transparent 16%),
        radial-gradient(rgba(0, 240, 255, 0.05) 15%, transparent 16%);
      background-size: 16px 16px, 32px 32px;
      background-position: 0 0, 8px 8px;
      min-height: 100vh;
    }
    .container { max-width: 840px; width: 100%; display: flex; flex-direction: column; gap: 14px; }

    /* Scanline and CRT Glitch Overlay */
    .scanlines {
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.35) 50%);
      background-size: 100% 4px;
      z-index: 999;
      pointer-events: none;
      opacity: 0.7;
    }

    /* Chromatic Aberration Text Effect */
    .glitch-text {
      position: relative;
      display: inline-block;
      text-shadow: -1.5px 0 var(--magenta), 1.5px 0 var(--cyan);
      letter-spacing: 1.5px;
    }

    /* Stencil Cutout Header */
    header {
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 14px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: relative;
      border-left: 5px solid var(--magenta);
      clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px));
      box-shadow: 0 0 20px rgba(255, 0, 85, 0.1);
    }
    .brand { display: flex; align-items: center; gap: 14px; }
    
    /* Interactive Wrench LED Goggles */
    .wrench-goggles {
      display: flex;
      gap: 4px;
      padding: 4px 6px;
      background: #000;
      border: 2px solid var(--cyan);
      cursor: pointer;
      box-shadow: 0 0 10px rgba(0,240,255,0.4);
      user-select: none;
      transition: transform 0.1s ease;
    }
    .wrench-goggles:hover { transform: scale(1.05); }
    .goggle-lens {
      width: 26px;
      height: 22px;
      background: #050508;
      border: 1px solid var(--cyan);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--cyan);
      font-weight: 900;
      font-size: 14px;
      text-shadow: 0 0 6px var(--cyan);
    }

    h1 { font-size: 16px; font-weight: 900; letter-spacing: 1px; color: #fff; text-transform: uppercase; }
    .motto { font-size: 10px; color: var(--yellow); letter-spacing: 0.5px; margin-top: 2px; font-weight: bold; }
    .header-badges { display: flex; gap: 8px; align-items: center; }
    
    .badge {
      font-size: 10px;
      font-weight: 800;
      padding: 4px 8px;
      background: rgba(0,240,255,0.12);
      border: 1px solid var(--cyan);
      color: var(--cyan);
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .badge-stencil {
      background: var(--yellow);
      color: #000;
      font-weight: 900;
      border: none;
      clip-path: polygon(4px 0, 100% 0, calc(100% - 4px) 100%, 0 100%);
    }

    /* Live Display Mirror Frame */
    .display-box {
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      border-top: 3px solid var(--green);
      position: relative;
    }
    .display-header {
      width: 100%;
      max-width: 520px;
      display: flex;
      justify-content: space-between;
      font-size: 10px;
      color: var(--muted);
      font-weight: 700;
      letter-spacing: 1px;
    }
    .screen-img {
      width: 100%;
      max-width: 520px;
      aspect-ratio: 250 / 122;
      image-rendering: pixelated;
      border: 2px solid #28344a;
      background: #000;
      box-shadow: 0 0 25px rgba(0,255,102,0.15);
    }

    /* Yield & Bounty Matrix Panel */
    .bounty-panel {
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      border-left: 5px solid var(--green);
      clip-path: polygon(0 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%);
    }
    .panel-title {
      font-size: 11px;
      font-weight: 900;
      color: var(--green);
      letter-spacing: 1px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      text-transform: uppercase;
    }
    .bounty-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }
    .bounty-tile {
      background: var(--card);
      border: 1px solid var(--border);
      padding: 10px;
      position: relative;
    }
    .bounty-tile-lbl { font-size: 9px; color: var(--muted); text-transform: uppercase; margin-bottom: 2px; font-weight: bold; }
    .bounty-tile-val { font-size: 14px; font-weight: 900; color: #fff; }
    .val-green { color: var(--green); text-shadow: 0 0 8px rgba(0,255,102,0.5); }
    .val-cyan { color: var(--cyan); text-shadow: 0 0 8px rgba(0,240,255,0.5); }
    .val-yellow { color: var(--yellow); text-shadow: 0 0 6px rgba(255,230,0,0.4); }

    /* Action Controls Grid */
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }
    button, a.btn {
      padding: 9px 8px;
      background: var(--card);
      border: 1px solid var(--border);
      color: var(--text);
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
      text-decoration: none;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.12s ease;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    button:hover, a.btn:hover {
      background: rgba(0, 240, 255, 0.18);
      border-color: var(--cyan);
      color: var(--cyan);
      box-shadow: 0 0 12px rgba(0,240,255,0.3);
    }
    button:active, a.btn:active { transform: scale(0.97); }
    .btn-bounty {
      background: rgba(0, 255, 102, 0.14);
      border-color: var(--green);
      color: var(--green);
    }
    .btn-bounty:hover {
      background: rgba(0, 255, 102, 0.28);
      color: #fff;
      box-shadow: 0 0 14px rgba(0,255,102,0.5);
    }
    .btn-magenta {
      background: rgba(255, 0, 85, 0.14);
      border-color: var(--magenta);
      color: var(--magenta);
    }
    .btn-magenta:hover {
      background: rgba(255, 0, 85, 0.3);
      color: #fff;
      box-shadow: 0 0 14px rgba(255,0,85,0.5);
    }
    .btn-cyan {
      background: rgba(0, 240, 255, 0.14);
      border-color: var(--cyan);
      color: var(--cyan);
    }

    /* Terminal Console Box */
    .console-box {
      border: 1px solid var(--border);
      background: #030407;
      padding: 12px;
      font-size: 11px;
      line-height: 1.4;
      max-height: 160px;
      overflow-y: auto;
      border-left: 5px solid var(--magenta);
    }
    .log-line { color: var(--muted); font-size: 10px; }
    .log-line span.cyan { color: var(--cyan); }
    .log-line span.green { color: var(--green); }
    .log-line span.magenta { color: var(--magenta); }
    .log-line span.yellow { color: var(--yellow); }
    .log-line span.white { color: #fff; font-weight: bold; }
  </style>
</head>
<body>
  <div class="scanlines"></div>
  <div class="container">
    <!-- Header -->
    <header>
      <div class="brand">
        <div class="wrench-goggles" id="wrench-avatar" onclick="cycleWrenchEye()" title="Click to cycle Wrench LED goggle expression!">
          <div class="goggle-lens" id="goggle-l">X</div>
          <div class="goggle-lens" id="goggle-r">X</div>
        </div>
        <div>
          <h1 class="glitch-text">DEDSEC // TECHNO-STREET OPERATOR</h1>
          <div class="motto">"DedSec has given you the truth. Do with it what you will."</div>
        </div>
      </div>
      <div class="header-badges">
        <span class="badge badge-stencil" id="lvl-badge">LV. 1 NOVICE</span>
        <span class="badge" id="defcon-badge">DEFCON 5 SECURE</span>
      </div>
    </header>

    <!-- Live E-Ink Canvas Mirror -->
    <div class="display-box">
      <div class="display-header">
        <span>// 1-BIT DITHERED E-PAPER CANVAS (250x122)</span>
        <span id="rot-label">HW: 0° • INFILTRATOR</span>
      </div>
      <img src="/api/screen.png" alt="DedSec E-Ink Screen" class="screen-img" id="live-screen">
    </div>

    <!-- Passive Micro-Yield & White-Hat Bounty Matrix -->
    <div class="bounty-panel">
      <div class="panel-title">
        <span>⚡ PASSIVE YIELD & BOUNTY HARVEST MATRIX</span>
        <span id="mesh-nodes-lbl" style="font-size:10px; color:var(--muted);">MESH: 12 RELAY NODES</span>
      </div>
      <div class="bounty-grid">
        <div class="bounty-tile">
          <div class="bounty-tile-lbl">Total Yield ($)</div>
          <div class="bounty-tile-val val-green" id="yield-usd">$0.00</div>
        </div>
        <div class="bounty-tile">
          <div class="bounty-tile-lbl">Satoshi Balance</div>
          <div class="bounty-tile-val val-yellow" id="yield-sats">0 SATS</div>
        </div>
        <div class="bounty-tile">
          <div class="bounty-tile-lbl">Daily Yield Rate</div>
          <div class="bounty-tile-val val-cyan" id="yield-rate">$4.20 / d</div>
        </div>
        <div class="bounty-tile">
          <div class="bounty-tile-lbl">Relayed Volume</div>
          <div class="bounty-tile-val" id="yield-mb">0.0 MB</div>
        </div>
      </div>
    </div>

    <!-- Tactical Actions Grid -->
    <div class="actions-grid">
      <button class="btn-bounty" onclick="triggerHarvest()">💰 Harvest Vulns</button>
      <button class="btn-cyan" onclick="runTool('audit_wifi')">📡 Audit Wi-Fi</button>
      <button class="btn-cyan" onclick="runTool('scan_ble')">📶 BLE Radar</button>
      <button onclick="sendAction('scan')">🛡️ Full Scan</button>
    </div>

    <div class="actions-grid">
      <button class="btn-cyan" onclick="sendAction('siphon')">⚡ Siphon Mesh (+20)</button>
      <button class="btn-bounty" onclick="sendAction('overclock')">⚙️ Overclock Core (+15)</button>
      <button class="btn-magenta" onclick="sendAction('mode')">🖥️ Cycle Deck Mode</button>
      <button onclick="sendAction('flip')">🔄 Flip (180°)</button>
    </div>

    <div class="actions-grid">
      <button onclick="sendAction('recover')">⚡ Unstick E-Ink</button>
      <a class="btn" href="/api/tools/wardrive.csv" download="wardrive.csv">📥 Wardrive CSV</a>
      <button onclick="fetchReports()">📜 Bounty Reports</button>
      <button onclick="fetchTelemetry()">🔍 Raw Telemetry</button>
    </div>

    <!-- Real-time DedSec Console Log -->
    <div class="console-box" id="console-log">
      <div class="log-line"><span class="magenta">[DEDSEC-WEBPUNK]</span> Techno-Street Operative Deck active on Raspberry Pi Zero 2 W.</div>
      <div class="log-line"><span class="green">[YIELD-ENGINE]</span> Bandwidth & compute proof-of-uptime accumulator initialized ($4.20/d).</div>
      <div class="log-line"><span class="cyan">[SENTINEL]</span> Local perimeter defense listening on wlan0. All shields nominal.</div>
    </div>
  </div>

  <script>
    const WRENCH_EXPRESSIONS = ['X_X', '>_<', '*_*', '!_!', '$_$', '^_^', '?_?', 'O_O', '#_#', '-_-'];
    let curExpIdx = 0;

    function setWrenchEyes(exp) {
      const parts = exp.split('_');
      document.getElementById('goggle-l').innerText = parts[0] || 'X';
      document.getElementById('goggle-r').innerText = parts[1] || parts[0] || 'X';
    }

    function cycleWrenchEye() {
      curExpIdx = (curExpIdx + 1) % WRENCH_EXPRESSIONS.length;
      const exp = WRENCH_EXPRESSIONS[curExpIdx];
      setWrenchEyes(exp);
      logMsg('WRENCH', 'Goggle HUD expression set to: [' + exp + ']', 'magenta');
    }

    function logMsg(tag, msg, color) {
      const box = document.getElementById('console-log');
      const now = new Date().toTimeString().split(' ')[0];
      const div = document.createElement('div');
      div.className = 'log-line';
      div.innerHTML = `<span class="${color}">[${now}] [${tag}]</span> ${msg}`;
      box.appendChild(div);
      box.scrollTop = box.scrollHeight;
    }

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
          document.getElementById('lvl-badge').innerText = 'LV. ' + data.brain.level + ' ' + (data.brain.title || 'OPERATOR').toUpperCase();
          document.getElementById('defcon-badge').innerText = 'DEFCON ' + data.brain.defcon + ' ' + (data.security?.defcon_status || 'SECURE');
          document.getElementById('rot-label').innerText = 'HW: ' + (data.brain.rotation || 0) + '° • ' + (data.brain.display_mode || 'infiltrator').toUpperCase();

          if (data.brain && data.brain.face) {
            setWrenchEyes(data.brain.face);
          }

          if (data.bounty && data.bounty.ledger) {
            const l = data.bounty.ledger;
            document.getElementById('yield-usd').innerText = '$' + (l.total_usd_earned || 0).toFixed(3);
            document.getElementById('yield-sats').innerText = (l.total_sats_earned || 0).toLocaleString() + ' SATS';
            document.getElementById('yield-rate').innerText = '$' + (l.daily_usd_rate || 4.20).toFixed(2) + ' / d';
            document.getElementById('yield-mb').innerText = (l.total_relayed_mb || 0).toFixed(1) + ' MB';
            document.getElementById('mesh-nodes-lbl').innerText = 'MESH: ' + (l.active_mesh_nodes || 12) + ' NODES • SHARES: ' + (l.total_compute_shares || 0);
          }
        }
      } catch (e) {}
    }
    setInterval(updateStats, 2500);
    updateStats();

    async function sendAction(act) {
      logMsg('ACTION', 'Dispatching command: ' + act, 'cyan');
      await fetch('/api/action/' + act, { method: 'POST' });
      updateStats();
      setTimeout(refreshScreen, 200);
    }

    async function triggerHarvest() {
      logMsg('BOUNTY', 'Launching white-hat vulnerability harvest across local perimeter...', 'green');
      const res = await fetch('/api/action/harvest', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        const r = data.bounty?.latest_report;
        if (r) {
          logMsg('BOUNTY-DONE', `Audit complete: ${r.total_findings} findings (Crit: ${r.critical_count}, High: ${r.high_count}). Value: $${r.estimated_bounty_usd.toFixed(2)}`, 'green');
          alert(`DEDSEC BOUNTY HARVEST COMPLETE\\n\\nFindings: ${r.total_findings}\\nCritical: ${r.critical_count}\\nHigh: ${r.high_count}\\nEst. Value: $${r.estimated_bounty_usd.toFixed(2)}\\n\\n${r.summary}`);
        }
      }
      updateStats();
      setTimeout(refreshScreen, 200);
    }

    async function runTool(tool) {
      logMsg('TOOL', 'Executing tactical sentinel tool: ' + tool, 'cyan');
      const res = await fetch('/api/tools/' + tool, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        logMsg('TOOL-DONE', tool.toUpperCase() + ' finished with success.', 'green');
      }
      updateStats();
      setTimeout(refreshScreen, 200);
    }

    async function fetchReports() {
      const res = await fetch('/api/bounty/reports');
      if (res.ok) {
        const data = await res.json();
        const win = window.open('', '_blank');
        win.document.write('<pre style="background:#06070a;color:#00FF66;padding:20px;font-family:monospace;">' + JSON.stringify(data, null, 2) + '</pre>');
      }
    }

    async function fetchTelemetry() {
      const res = await fetch('/api/security/telemetry');
      if (res.ok) {
        const data = await res.json();
        const win = window.open('', '_blank');
        win.document.write('<pre style="background:#06070a;color:#00F0FF;padding:20px;font-family:monospace;">' + JSON.stringify(data, null, 2) + '</pre>');
      }
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
        self.app.router.add_get("/api/security/telemetry", self._handle_security_telemetry)
        self.app.router.add_get("/api/tools/wardrive.csv", self._handle_export_wardrive)
        self.app.router.add_get("/api/bounty/stats", self._handle_bounty_stats)
        self.app.router.add_get("/api/bounty/reports", self._handle_bounty_reports)
        self.app.router.add_get("/api/bounty/report/{id}", self._handle_single_report)
        self.app.router.add_get("/api/bounty/report/{id}/markdown", self._handle_report_markdown)

        # Actions
        self.app.router.add_post("/api/action/siphon", self._handle_siphon)
        self.app.router.add_post("/api/action/overclock", self._handle_overclock)
        self.app.router.add_post("/api/action/pet", self._handle_pet)
        self.app.router.add_post("/api/action/feed", self._handle_feed)
        self.app.router.add_post("/api/action/flip", self._handle_flip)
        self.app.router.add_post("/api/action/scan", self._handle_scan)
        self.app.router.add_post("/api/action/mode", self._handle_mode)
        self.app.router.add_post("/api/action/recover", self._handle_recover)
        self.app.router.add_post("/api/action/harvest", self._handle_harvest)

        # Tools
        self.app.router.add_post("/api/tools/audit_wifi", self._handle_audit_wifi)
        self.app.router.add_post("/api/tools/scan_ble", self._handle_scan_ble)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"OmniGotchi DedSec CyberOS Web Companion running on http://{self.host}:{self.port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    async def _handle_index(self, request: web.Request) -> web.Response:
        return web.Response(text=HTML_TEMPLATE, content_type="text/html")

    async def _handle_screen_png(self, request: web.Request) -> web.Response:
        img = self.engine.current_image
        if img is None:
            self.engine.trigger_render(partial=False)
            img = self.engine.current_image
            if img is None:
                return web.Response(status=503)
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("L")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return web.Response(
            body=buf.getvalue(),
            content_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Access-Control-Allow-Origin": "*",
            },
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
                "siphon_power": self.engine.brain.state.siphon_power,
                "overclock_level": self.engine.brain.state.overclock_level,
                "system_integrity": self.engine.brain.state.system_integrity,
                "rotation": self.engine.brain.state.rotation,
                "display_mode": self.engine.brain.state.display_mode,
                "defcon": self.engine.brain.state.defcon,
                "threat_status": self.engine.brain.state.threat_status,
                "total_siphons": self.engine.brain.state.total_siphons,
                "total_harvests": self.engine.brain.state.total_harvests,
                "total_security_scans": self.engine.brain.state.total_security_scans,
            },
            "dev": self.engine.dev_data,
            "audio": self.engine.audio_data,
            "net": self.engine.net_data,
            "security": self.engine.security_data,
            "bounty": self.engine.bounty_data,
        }
        return web.Response(
            text=json.dumps(data),
            content_type="application/json",
            headers={"Cache-Control": "no-cache"},
        )

    async def _handle_bounty_stats(self, request: web.Request) -> web.Response:
        return web.Response(
            text=json.dumps(self.engine.bounty_data),
            content_type="application/json",
            headers={"Cache-Control": "no-cache"},
        )

    async def _handle_bounty_reports(self, request: web.Request) -> web.Response:
        reports = [asdict(r) for r in self.engine.bounty_engine.reports]
        return web.Response(
            text=json.dumps(reports),
            content_type="application/json",
            headers={"Cache-Control": "no-cache"},
        )

    async def _handle_single_report(self, request: web.Request) -> web.Response:
        report_id = request.match_info.get("id")
        for r in self.engine.bounty_engine.reports:
            if r.id == report_id:
                return web.Response(
                    text=json.dumps(asdict(r)),
                    content_type="application/json",
                    headers={"Cache-Control": "no-cache"},
                )
        return web.Response(status=404, text=json.dumps({"error": "Report not found"}), content_type="application/json")

    async def _handle_report_markdown(self, request: web.Request) -> web.Response:
        report_id = request.match_info.get("id")
        for r in self.engine.bounty_engine.reports:
            if r.id == report_id:
                lines = [
                    f"# DEDSEC WHITE-HAT VULNERABILITY AUDIT REPORT: {r.id}",
                    f"**Generated:** {time.ctime(r.timestamp)}",
                    f"**Target Perimeter:** {r.target_network}",
                    f"**Total Findings:** {r.total_findings} (Critical: {r.critical_count}, High: {r.high_count}, Medium: {r.medium_count}, Low: {r.low_count})",
                    f"**Estimated Bug Bounty Value:** ${r.estimated_bounty_usd:.2f} USD",
                    "",
                    "## Executive Summary",
                    f"{r.summary}",
                    "",
                    "## Vulnerability Findings & Remediation Roadmap",
                ]
                for f in r.findings:
                    lines.extend([
                        f"### [{f.get('severity', 'INFO')}] {f.get('title')}",
                        f"- **Target/Port:** `{f.get('target')}`",
                        f"- **CVE Reference:** `{f.get('cve_ref') or 'N/A'}`",
                        f"- **Estimated Value:** ${f.get('bounty_value_usd', 0.0):.2f}",
                        f"- **Description:** {f.get('description')}",
                        f"- **Remediation:** {f.get('remediation')}",
                        "",
                    ])
                return web.Response(
                    text="\n".join(lines),
                    content_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="dedsec_bounty_{r.id}.md"'},
                )
        return web.Response(status=404, text="Report not found", content_type="text/plain")

    async def _handle_security_telemetry(self, request: web.Request) -> web.Response:
        return web.Response(
            text=json.dumps(self.engine.security_data, indent=2),
            content_type="application/json",
            headers={"Cache-Control": "no-cache"},
        )

    async def _handle_export_wardrive(self, request: web.Request) -> web.Response:
        csv_data = self.engine.security_module.wifi_auditor.export_wigle_csv()
        return web.Response(
            text=csv_data,
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="omnigotchi_wardrive.csv"'},
        )

    async def _handle_siphon(self, request: web.Request) -> web.Response:
        self.engine.brain.siphon()
        self.engine.trigger_render()
        return web.Response(text=json.dumps({"ok": True, "siphon_power": self.engine.brain.state.siphon_power}), content_type="application/json")

    async def _handle_overclock(self, request: web.Request) -> web.Response:
        self.engine.brain.overclock()
        self.engine.trigger_render()
        return web.Response(text=json.dumps({"ok": True, "overclock_level": self.engine.brain.state.overclock_level}), content_type="application/json")

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

    async def _handle_harvest(self, request: web.Request) -> web.Response:
        bounty_data = await self.engine.scan_bounty()
        return web.Response(text=json.dumps({"ok": True, "bounty": bounty_data}), content_type="application/json")

    async def _handle_audit_wifi(self, request: web.Request) -> web.Response:
        res = await self.engine.audit_wifi()
        return web.Response(text=json.dumps({"ok": True, "wifi_audit": res}), content_type="application/json")

    async def _handle_scan_ble(self, request: web.Request) -> web.Response:
        res = await self.engine.scan_ble()
        return web.Response(text=json.dumps({"ok": True, "ble_scan": res}), content_type="application/json")

    async def _handle_mode(self, request: web.Request) -> web.Response:
        mode = self.engine.toggle_display_mode()
        return web.Response(text=json.dumps({"ok": True, "mode": mode}), content_type="application/json")

    async def _handle_recover(self, request: web.Request) -> web.Response:
        self.engine.recover_display()
        return web.Response(text=json.dumps({"ok": True, "recovered": True}), content_type="application/json")
