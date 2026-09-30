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

    async def scan(self, duration_s: float = 3.0) -> Dict:
        """Runs a passive BLE advertisement sweep using bluetoothctl / hcitool."""
        loop = asyncio.get_event_loop()
        now = time.time()
        self.last_scan_time = now
        new_events = []

        try:
            # Query bluetoothctl devices
            cmd = ["bluetoothctl", "devices"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=2.0),
            )
            if res.returncode == 0 and res.stdout:
                for line in res.stdout.strip().split("\n"):
                    # Format: Device XX:XX:XX:XX:XX:XX DeviceName
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 2 and parts[0] == "Device":
                        mac = parts[1].upper()
                        name = parts[2] if len(parts) > 2 else "Unknown BLE"
                        
                        if mac not in self.discovered_devices:
                            self.discovered_devices[mac] = {
                                "mac": mac,
                                "name": name,
                                "rssi": -70,
                                "proximity": "Near",
                                "first_seen": now,
                                "last_seen": now,
                                "count": 1,
                            }
                        else:
                            dev = self.discovered_devices[mac]
                            dev["last_seen"] = now
                            dev["count"] += 1
                            if name != "Unknown BLE":
                                dev["name"] = name
                        
                        new_events.append((now, mac))

        except Exception as e:
            logger.debug(f"bluetoothctl scan error: {e}")

        # Check advertisement burst rate for flood/spam detection
        self.advertisement_history.extend(new_events)
        # Keep last 30 seconds of history
        cutoff = now - 30.0
        self.advertisement_history = [item for item in self.advertisement_history if item[0] >= cutoff]

        # Anomaly Detection: High rate of rotating random MACs in short burst
        recent_10s = [item for item in self.advertisement_history if item[0] >= now - 10.0]
        distinct_macs_10s = {item[1] for item in recent_10s}
        
        if len(recent_10s) > 40 and len(distinct_macs_10s) > 20:
            self.flood_detected = True
            self.flood_alert_msg = f"BLE Beacon Flood Detected ({len(distinct_macs_10s)} rotating IDs in 10s)"
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

        # Sort by last seen
        devices_list.sort(key=lambda x: x["last_seen"], reverse=True)

        return {
            "total_devices_seen": len(self.discovered_devices),
            "recent_devices": devices_list[:10],
            "flood_detected": self.flood_detected,
            "flood_alert_msg": self.flood_alert_msg,
            "last_scan_time": self.last_scan_time,
        }
