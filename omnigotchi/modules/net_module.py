"""Network Sentinel: Latency, Wi-Fi RSSI, System Vitals & Health."""

import asyncio
import logging
import os
import socket
import subprocess
import time
from typing import Dict
import psutil

logger = logging.getLogger("omnigotchi.net")


class NetModule:
    def __init__(self, target_host: str = "1.1.1.1", timeout_s: float = 1.0):
        self.target_host = target_host
        self.timeout_s = timeout_s
        self.cached_state: Dict = {
            "ping_ms": 0.0,
            "is_offline": False,
            "wifi_ssid": "LAN",
            "wifi_signal_pct": 100,
            "cpu_pct": 0,
            "ram_pct": 0,
            "temp_c": 40.0,
            "uptime_str": "0h",
        }
        self.start_time = time.time()

    async def poll(self) -> Dict:
        # Measure socket connection latency to target_host:53 / 80
        ping = await self._measure_latency()
        self.cached_state["ping_ms"] = ping
        self.cached_state["is_offline"] = (ping >= 999.0)

        # Host system vitals
        try:
            self.cached_state["cpu_pct"] = int(psutil.cpu_percent(interval=None))
            self.cached_state["ram_pct"] = int(psutil.virtual_memory().percent)
        except Exception:
            pass

        # CPU Temperature (works on Pi & Linux)
        self.cached_state["temp_c"] = self._get_cpu_temp()

        # Uptime
        up_s = int(time.time() - self.start_time)
        hours = up_s // 3600
        mins = (up_s % 3600) // 60
        self.cached_state["uptime_str"] = f"{hours}h{mins}m"

        # Wi-Fi SSID / RSSI
        self._get_wifi_info()

        return self.cached_state

    async def _measure_latency(self) -> float:
        """Measures TCP connection latency in milliseconds."""
        loop = asyncio.get_event_loop()
        start = time.perf_counter()
        try:
            # Connect to 1.1.1.1:53 (Cloudflare DNS) or 8.8.8.8
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)
            sock.settimeout(self.timeout_s)
            
            await asyncio.wait_for(
                loop.sock_connect(sock, (self.target_host, 53)),
                timeout=self.timeout_s
            )
            sock.close()
            elapsed = (time.perf_counter() - start) * 1000.0
            return round(elapsed, 1)
        except Exception:
            return 999.0

    def _get_cpu_temp(self) -> float:
        thermal_paths = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/devices/virtual/thermal/thermal_zone0/temp",
        ]
        for p in thermal_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        raw = int(f.read().strip())
                        return round(raw / 1000.0, 1)
                except Exception:
                    pass
        return 42.0

    def _get_wifi_info(self):
        """Extracts Wi-Fi info via nmcli / iwgetid if present."""
        try:
            res = subprocess.run(
                ["iwgetid", "-r"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=0.3
            )
            if res.returncode == 0 and res.stdout.strip():
                self.cached_state["wifi_ssid"] = res.stdout.strip()[:10]
        except Exception:
            pass
