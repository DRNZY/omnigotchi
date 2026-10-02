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
  <title>DEDSEC // CYBEROS PI OPERATOR</title>
  <style>
    :root {
      --bg: #06070a;
      --panel: #0d1017;
      --card: #121722;
      --border: #1e2638;
      --cyan: #00F0FF;
      --green: #00FF66;
      --magenta: #FF0055;
      --yellow: #FFE600;
      --text: #e6edf3;
      --muted: #6e7d9b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Courier New", "Lucida Console", Monaco, monospace; }
    body {
      background: var(--bg);
      color: var(--text);
      padding: 20px;
      display: flex;
      justify-content: center;
      background-image: 
        linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
      background-size: 24px 24px;
      min-height: 100vh;
    }
    .container { max-width: 820px; width: 100%; display: flex; flex-direction: column; gap: 14px; }

    /* Scanline effect */
    .scanlines {
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
      background-size: 100% 4px;
      z-index: 999;
      pointer-events: none;
      opacity: 0.6;
    }

    /* Header */
    header {
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 12px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: relative;
      border-left: 4px solid var(--cyan);
    }
    .brand { display: flex; align-items: center; gap: 10px; }
    .skull { font-size: 16px; color: var(--cyan); font-weight: bold; text-shadow: 0 0 8px rgba(0,240,255,0.6); }
    h1 { font-size: 16px; font-weight: 800; letter-spacing: 1px; color: #fff; }
    .motto { font-size: 10px; color: var(--muted); letter-spacing: 0.5px; }
    .header-badges { display: flex; gap: 8px; align-items: center; }
    .badge {
      font-size: 10px;
      font-weight: 700;
      padding: 3px 8px;
      background: rgba(0,240,255,0.1);
      border: 1px solid var(--cyan);
      color: var(--cyan);
    }
    .badge-alert {
      background: rgba(255,0,85,0.15);
      border: 1px solid var(--magenta);
      color: var(--magenta);
    }

    /* Live Display Mirror Frame */
    .display-box {
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      border-top: 2px solid var(--green);
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
      border: 2px solid #222c3d;
      background: #000;
      box-shadow: 0 0 20px rgba(0,240,255,0.1);
    }

    /* Yield & Bounty Matrix Panel */
    .bounty-panel {
      border: 1px solid var(--border);
      background: var(--panel);
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      border-left: 4px solid var(--green);
    }
    .panel-title {
      font-size: 12px;
      font-weight: 800;
      color: var(--green);
      letter-spacing: 1px;
      display: flex;
      justify-content: space-between;
      align-items: center;
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
    }
    .bounty-tile-lbl { font-size: 9px; color: var(--muted); text-transform: uppercase; margin-bottom: 2px; }
    .bounty-tile-val { font-size: 14px; font-weight: 800; color: #fff; }
    .val-green { color: var(--green); text-shadow: 0 0 6px rgba(0,255,102,0.4); }
    .val-cyan { color: var(--cyan); text-shadow: 0 0 6px rgba(0,240,255,0.4); }
    .val-yellow { color: var(--yellow); }

    /* Action Controls */
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
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.1s ease;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    button:hover, a.btn:hover {
      background: rgba(0, 240, 255, 0.15);
      border-color: var(--cyan);
      color: var(--cyan);
      box-shadow: 0 0 10px rgba(0,240,255,0.2);
    }
    button:active, a.btn:active { transform: scale(0.98); }
    .btn-bounty {
      background: rgba(0, 255, 102, 0.12);
      border-color: var(--green);
      color: var(--green);
    }
    .btn-bounty:hover {
      background: rgba(0, 255, 102, 0.25);
      color: #fff;
      box-shadow: 0 0 12px rgba(0,255,102,0.4);
    }
    .btn-cyan {
      background: rgba(0, 240, 255, 0.12);
      border-color: var(--cyan);
      color: var(--cyan);
    }

    /* Terminal Console */
    .console-box {
      border: 1px solid var(--border);
      background: #040508;
      padding: 12px;
      font-size: 11px;
      line-height: 1.4;
      max-height: 160px;
      overflow-y: auto;
      border-left: 4px solid var(--magenta);
    }
    .log-line { color: var(--muted); font-size: 10px; }
    .log-line span.cyan { color: var(--cyan); }
    .log-line span.green { color: var(--green); }
    .log-line span.magenta { color: var(--magenta); }
    .log-line span.white { color: #fff; font-weight: bold; }
  </style>
</head>
<body>
  <div class="scanlines"></div>
  <div class="container">
    <!-- Header -->
    <header>
      <div class="brand">
        <span class="skull">[ X_X ]</span>
        <div>
          <h1>DEDSEC // CYBEROS OPERATOR</h1>
          <div class="motto">"DedSec has given you the truth. Do with it what you will."</div>
        </div>
      </div>
      <div class="header-badges">
        <span class="badge" id="lvl-badge">LV. 1 NOVICE</span>
        <span class="badge" id="defcon-badge">DEFCON 5 SECURE</span>
      </div>
    </header>

    <!-- Live E-Ink Canvas Mirror -->
    <div class="display-box">
      <div class="display-header">
        <span>// PHYSICAL E-PAPER MIRROR (250x122 1-BIT)</span>
        <span id="rot-label">HW: 0° • COMPANION</span>
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
      <button onclick="sendAction('pet')">🐾 Inject Pet (+10)</button>
      <button onclick="sendAction('feed')">🍕 Feed Bytes (+15)</button>
      <button onclick="sendAction('flip')">🔄 Flip (180°)</button>
      <button onclick="sendAction('mode')">🖥️ Toggle Mode</button>
    </div>

    <div class="actions-grid">
      <button onclick="sendAction('recover')">⚡ Unstick E-Ink</button>
      <a class="btn" href="/api/tools/wardrive.csv" download="wardrive.csv">📥 Wardrive CSV</a>
      <button onclick="fetchReports()">📜 Bounty Reports</button>
      <button onclick="fetchTelemetry()">🔍 Raw Telemetry</button>
    </div>

    <!-- Real-time DedSec Console Log -->
    <div class="console-box" id="console-log">
      <div class="log-line"><span class="cyan">[DEDSEC-INIT]</span> DedSec CyberOS Sentinel loaded on Raspberry Pi Zero 2 W.</div>
      <div class="log-line"><span class="green">[YIELD-ENGINE]</span> Bandwidth & compute proof-of-uptime accumulator initialized ($4.20/d).</div>
      <div class="log-line"><span class="magenta">[SENTINEL]</span> Local perimeter defense listening on wlan0. All shields nominal.</div>
    </div>
  </div>

  <script>
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
          document.getElementById('rot-label').innerText = 'HW: ' + (data.brain.rotation || 0) + '° • ' + (data.brain.display_mode || 'companion').toUpperCase();

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
