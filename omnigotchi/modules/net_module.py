"""Network Sentinel: Latency, Wi-Fi RSSI, System Vitals, RAM, Wattage & Bandwidth."""

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
            "ram_used_mb": 0,
            "ram_total_mb": 512,
            "temp_c": 40.0,
            "wattage_w": 0.85,
            "rx_kbps": 0.0,
            "tx_kbps": 0.0,
            "uptime_str": "0h",
        }
        self.start_time = time.time()
        self.last_net_bytes = self._get_network_bytes()
        self.last_net_time = time.time()

    async def poll(self) -> Dict:
        # Measure socket connection latency to target_host:53 / 80
        ping = await self._measure_latency()
        self.cached_state["ping_ms"] = ping
        self.cached_state["is_offline"] = (ping >= 999.0)

        # Host system vitals
        try:
            cpu = int(psutil.cpu_percent(interval=None))
            vmem = psutil.virtual_memory()
            self.cached_state["cpu_pct"] = cpu
            self.cached_state["ram_pct"] = int(vmem.percent)
            self.cached_state["ram_used_mb"] = int(vmem.used / (1024 * 1024))
            self.cached_state["ram_total_mb"] = int(vmem.total / (1024 * 1024))
            
            # Dynamic power draw model for Pi Zero 2 W / SBC (0.7W base + CPU load scaling + Wi-Fi TX)
            est_wattage = 0.72 + (cpu / 100.0) * 0.95 + 0.15
            self.cached_state["wattage_w"] = round(est_wattage, 2)
        except Exception:
            pass

        # CPU Temperature (works on Pi & Linux)
        self.cached_state["temp_c"] = self._get_cpu_temp()

        # Bandwidth sample
        now = time.time()
        cur_bytes = self._get_network_bytes()
        dt = max(0.1, now - self.last_net_time)
        rx_diff = max(0, cur_bytes[0] - self.last_net_bytes[0])
        tx_diff = max(0, cur_bytes[1] - self.last_net_bytes[1])
        self.cached_state["rx_kbps"] = round((rx_diff / 1024.0) / dt, 1)
        self.cached_state["tx_kbps"] = round((tx_diff / 1024.0) / dt, 1)
        self.last_net_bytes = cur_bytes
        self.last_net_time = now

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

    def _get_network_bytes(self) -> tuple:
        """Reads cumulative RX/TX bytes from /proc/net/dev."""
        rx_total, tx_total = 0, 0
        if os.path.exists("/proc/net/dev"):
            try:
                with open("/proc/net/dev", "r") as f:
                    lines = f.readlines()[2:]
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 10:
                            rx_total += int(parts[1])
                            tx_total += int(parts[9])
                return rx_total, tx_total
            except Exception:
                pass
        return 0, 0

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
                self.cached_state["wifi_ssid"] = res.stdout.strip()[:12]
        except Exception:
            pass
