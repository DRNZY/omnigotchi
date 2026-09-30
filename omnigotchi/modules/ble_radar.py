"""Bluetooth Low Energy (BLE) Radar, Device Proximity & Beacon Anomaly Monitor for OmniGotchi."""

import asyncio
import logging
import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("omnigotchi.ble_radar")


class BleRadar:
    """Defensive BLE Advertisement Monitor, Proximity Tracker & Beacon Anomaly Detector."""

    def __init__(self, adapter: str = "hci0"):
        self.adapter = adapter
        self.discovered_devices: Dict[str, Dict] = {}  # MAC -> Device Info
        self.advertisement_history: List[Tuple[float, str]] = []  # (timestamp, mac)
        self.flood_detected: bool = False
        self.flood_alert_msg: str = "BLE Spectrum Normal"
        self.last_scan_time: float = 0.0

    async def scan(self, duration_s: float = 2.0) -> Dict:
        """Runs an active BLE advertisement discovery sweep using bluetoothctl."""
        loop = asyncio.get_event_loop()
        now = time.time()
        self.last_scan_time = now
        new_events = []

        try:
            # 1. Run short scan sweep
            cmd_scan = ["bluetoothctl", "--timeout", str(int(duration_s)), "scan", "on"]
            scan_res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd_scan, capture_output=True, text=True, timeout=duration_s + 1.0),
            )
            if scan_res.stdout:
                for line in scan_res.stdout.split("\n"):
                    # Format: [NEW] Device XX:XX:XX:XX:XX:XX Name or [CHG] Device XX:XX:XX:XX:XX:XX RSSI: -65
                    if "Device " in line:
                        parts = line.split()
                        try:
                            idx = parts.index("Device")
                            if idx + 1 < len(parts):
                                mac = parts[idx + 1].upper()
                                name = " ".join(parts[idx + 2:]) if len(parts) > idx + 2 else "Unknown BLE"
                                rssi = -70
                                if "RSSI:" in line:
                                    r_idx = parts.index("RSSI:")
                                    if r_idx + 1 < len(parts):
                                        rssi = int(parts[r_idx + 1])

                                self._record_device(mac, name, rssi, now)
                                new_events.append((now, mac))
                        except Exception:
                            pass

            # 2. Query known paired/discovered catalog
            cmd_list = ["bluetoothctl", "devices"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd_list, capture_output=True, text=True, timeout=1.5),
            )
            if res.returncode == 0 and res.stdout:
                for line in res.stdout.strip().split("\n"):
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 2 and parts[0] == "Device":
                        mac = parts[1].upper()
                        name = parts[2] if len(parts) > 2 else "Unknown BLE"
                        self._record_device(mac, name, -70, now)

        except Exception as e:
            logger.debug(f"BLE radar scan error: {e}")

        # Check advertisement burst rate for flood/spam detection
        self.advertisement_history.extend(new_events)
        cutoff = now - 30.0
        self.advertisement_history = [item for item in self.advertisement_history if item[0] >= cutoff]

        recent_10s = [item for item in self.advertisement_history if item[0] >= now - 10.0]
        distinct_macs_10s = {item[1] for item in recent_10s}
        
        if len(recent_10s) > 40 and len(distinct_macs_10s) > 20:
            self.flood_detected = True
            self.flood_alert_msg = f"BLE Beacon Flood Detected ({len(distinct_macs_10s)} IDs in 10s)"
            logger.warning(self.flood_alert_msg)
        else:
            self.flood_detected = False
            self.flood_alert_msg = "BLE Spectrum Clean"

        # Calculate proximity
        devices_list = []
        for mac, dev in self.discovered_devices.items():
            rssi = dev.get("rssi", -75)
            if rssi >= -60:
                proximity = "Immediate"
            elif rssi >= -80:
                proximity = "Near"
            else:
                proximity = "Far"
            dev["proximity"] = proximity
            devices_list.append(dev)

        devices_list.sort(key=lambda x: x["last_seen"], reverse=True)

        return {
            "total_devices_seen": len(self.discovered_devices),
            "recent_devices": devices_list[:12],
            "flood_detected": self.flood_detected,
            "flood_alert_msg": self.flood_alert_msg,
            "last_scan_time": self.last_scan_time,
        }

    def _record_device(self, mac: str, name: str, rssi: int, ts: float):
        if mac not in self.discovered_devices:
            self.discovered_devices[mac] = {
                "mac": mac,
                "name": name,
                "rssi": rssi,
                "proximity": "Near",
                "first_seen": ts,
                "last_seen": ts,
                "count": 1,
            }
        else:
            dev = self.discovered_devices[mac]
            dev["last_seen"] = ts
            dev["count"] += 1
            if rssi != -70:
                dev["rssi"] = rssi
            if name not in ("Unknown BLE", "Device", ""):
                dev["name"] = name
