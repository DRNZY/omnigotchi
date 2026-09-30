"""WiFi Security Auditor & RF Spectrum Analyzer for OmniGotchi."""

import asyncio
import csv
import io
import logging
import os
import re
import subprocess
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("omnigotchi.wifi_auditor")


class WiFiAuditor:
    """Defensive Wi-Fi Security Posture Auditor, RF Spectrum Analyzer & Wardriving Logger."""

    def __init__(self, interface: str = "wlan0"):
        self.interface = interface
        self.discovered_aps: Dict[str, Dict] = {}  # BSSID -> AP Data
        self.current_connection_audit: Dict = {}
        self.last_scan_time: float = 0.0

    async def scan_and_audit(self) -> Dict:
        """Performs passive Wi-Fi scan, evaluates security posture, spectrum, and clones."""
        aps = await self._scan_aps_nmcli()
        if not aps:
            aps = await self._scan_aps_iwlist()

        now = time.time()
        self.last_scan_time = now

        # Update discovered APs catalog (for wardriving log)
        for ap in aps:
            bssid = ap["bssid"].upper()
            if bssid not in self.discovered_aps:
                self.discovered_aps[bssid] = {
                    "bssid": bssid,
                    "ssid": ap["ssid"],
                    "channel": ap["channel"],
                    "signal": ap["signal"],
                    "security": ap["security"],
                    "wpa_ver": ap.get("wpa_ver", "WPA2"),
                    "cipher": ap.get("cipher", "CCMP"),
                    "pmf": ap.get("pmf", "Unknown"),
                    "wps": ap.get("wps", False),
                    "first_seen": now,
                    "last_seen": now,
                }
            else:
                self.discovered_aps[bssid]["last_seen"] = now
                self.discovered_aps[bssid]["signal"] = ap["signal"]

        # Run Security Evaluations
        posture = self._evaluate_security_posture(aps)
        spectrum = self._calculate_spectrum_matrix(aps)
        clones = self._detect_cloned_rogue_aps(aps)
        conn_audit = await self.audit_connected_network()

        return {
            "ap_count": len(aps),
            "aps": aps[:16],
            "total_catalog_count": len(self.discovered_aps),
            "posture": posture,
            "spectrum": spectrum,
            "clones": clones,
            "connected_audit": conn_audit,
            "last_scan_time": self.last_scan_time,
        }

    async def _scan_aps_nmcli(self) -> List[Dict]:
        """Queries NetworkManager for detailed AP telemetry."""
        loop = asyncio.get_event_loop()
        aps = []
        try:
            cmd = ["nmcli", "-t", "-f", "BSSID,SSID,CHAN,SIGNAL,SECURITY,WPA-FLAGS", "dev", "wifi", "list"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=2.5),
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    cleaned = line.replace("\\:", ":")
                    raw_fields = cleaned.split(":")
                    if len(raw_fields) >= 5:
                        if len(raw_fields) >= 10:
                            bssid = ":".join(raw_fields[0:6])
                            ssid = raw_fields[6]
                            chan = raw_fields[7]
                            sig_str = raw_fields[8]
                            sec = raw_fields[9]
                            wpa_flags = raw_fields[10] if len(raw_fields) > 10 else ""
                        else:
                            bssid = raw_fields[0]
                            ssid = raw_fields[1] if len(raw_fields) > 1 else ""
                            chan = raw_fields[2] if len(raw_fields) > 2 else "1"
                            sig_str = raw_fields[3] if len(raw_fields) > 3 else "50"
                            sec = raw_fields[4] if len(raw_fields) > 4 else "OPEN"
                            wpa_flags = ""

                        if not ssid:
                            ssid = "<Hidden SSID>"

                        signal = int(sig_str) if sig_str.isdigit() else 50
                        sec_clean = sec.strip() if sec else "OPEN"

                        # Parse cipher and WPA version
                        wpa_ver = "OPEN"
                        if "WPA3" in sec_clean:
                            wpa_ver = "WPA3"
                        elif "WPA2" in sec_clean:
                            wpa_ver = "WPA2"
                        elif "WPA" in sec_clean:
                            wpa_ver = "WPA1"
                        elif "WEP" in sec_clean:
                            wpa_ver = "WEP"

                        cipher = "CCMP"
                        if "TKIP" in sec_clean or "TKIP" in wpa_flags:
                            cipher = "TKIP"
                        elif "WEP" in sec_clean:
                            cipher = "WEP"

                        aps.append({
                            "bssid": bssid.upper(),
                            "ssid": ssid,
                            "channel": chan,
                            "signal": signal,
                            "security": sec_clean,
                            "wpa_ver": wpa_ver,
                            "cipher": cipher,
                            "pmf": "Required" if "WPA3" in sec_clean else "Optional/None",
                            "wps": "WPS" in sec_clean or "WPS" in wpa_flags,
                            "is_open": sec_clean == "OPEN" or sec_clean == "--",
                        })
        except Exception as e:
            logger.debug(f"nmcli scan error: {e}")

        return aps

    async def _scan_aps_iwlist(self) -> List[Dict]:
        """Fallback passive scan using iwlist or /proc/net/wireless."""
        loop = asyncio.get_event_loop()
        aps = []
        try:
            cmd = ["iwlist", self.interface, "scan"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=2.5),
            )
            if res.returncode == 0:
                cur_ap: Dict = {}
                for line in res.stdout.split("\n"):
                    line = line.strip()
                    if "Cell " in line and "Address:" in line:
                        if cur_ap and "bssid" in cur_ap:
                            aps.append(cur_ap)
                        parts = line.split("Address:")
                        cur_ap = {
                            "bssid": parts[1].strip().upper() if len(parts) > 1 else "",
                            "ssid": "<Hidden SSID>",
                            "channel": "1",
                            "signal": 50,
                            "security": "OPEN",
                            "wpa_ver": "OPEN",
                            "cipher": "None",
                            "pmf": "None",
                            "wps": False,
                            "is_open": True,
                        }
                    elif "ESSID:" in line and cur_ap:
                        ssid = line.split("ESSID:")[1].strip('"')
                        cur_ap["ssid"] = ssid if ssid else "<Hidden SSID>"
                    elif "Channel:" in line and cur_ap:
                        cur_ap["channel"] = line.split("Channel:")[1].strip()
                    elif "Quality=" in line and cur_ap:
                        m = re.search(r"Signal level=(-?\d+)", line)
                        if m:
                            dbm = int(m.group(1))
                            cur_ap["signal"] = max(0, min(100, 2 * (dbm + 100)))
                    elif "IE: IEEE 802.11i/WPA2" in line and cur_ap:
                        cur_ap["security"] = "WPA2"
                        cur_ap["wpa_ver"] = "WPA2"
                        cur_ap["is_open"] = False
                    elif "IE: WPA Version 1" in line and cur_ap:
                        cur_ap["security"] = "WPA1"
                        cur_ap["wpa_ver"] = "WPA1"
                        cur_ap["is_open"] = False

                if cur_ap and "bssid" in cur_ap:
                    aps.append(cur_ap)
        except Exception:
            pass
        return aps

    def _evaluate_security_posture(self, aps: List[Dict]) -> Dict:
        """Evaluates RF environment security rating and highlights legacy vulnerabilities."""
        if not aps:
            return {
                "score": 100,
                "grade": "A+",
                "summary": "No active RF beacons detected",
                "open_count": 0,
                "wep_count": 0,
                "wpa1_count": 0,
                "wpa2_count": 0,
                "wpa3_count": 0,
                "wps_count": 0,
            }

        open_count = sum(1 for ap in aps if ap.get("is_open"))
        wep_count = sum(1 for ap in aps if ap.get("wpa_ver") == "WEP")
        wpa1_count = sum(1 for ap in aps if ap.get("wpa_ver") == "WPA1" or ap.get("cipher") == "TKIP")
        wpa2_count = sum(1 for ap in aps if ap.get("wpa_ver") == "WPA2")
        wpa3_count = sum(1 for ap in aps if ap.get("wpa_ver") == "WPA3")
        wps_count = sum(1 for ap in aps if ap.get("wps"))

        # Calculate score deduction
        deductions = (open_count * 15) + (wep_count * 25) + (wpa1_count * 10) + (wps_count * 5)
        score = max(10, min(100, 100 - deductions))

        if score >= 90:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 40:
            grade = "D"
        else:
            grade = "F"

        return {
            "score": score,
            "grade": grade,
            "summary": f"{wpa3_count} WPA3, {wpa2_count} WPA2, {open_count} Open, {wps_count} WPS",
            "open_count": open_count,
            "wep_count": wep_count,
            "wpa1_count": wpa1_count,
            "wpa2_count": wpa2_count,
            "wpa3_count": wpa3_count,
            "wps_count": wps_count,
        }

    def _calculate_spectrum_matrix(self, aps: List[Dict]) -> Dict:
        """Groups APs by frequency bands and popular channels to identify RF congestion."""
        channels: Dict[str, int] = {"1": 0, "6": 0, "11": 0, "5ghz": 0, "other": 0}
        for ap in aps:
            ch_str = str(ap.get("channel", "1"))
            if ch_str.isdigit():
                ch = int(ch_str)
                if ch == 1:
                    channels["1"] += 1
                elif ch == 6:
                    channels["6"] += 1
                elif ch == 11:
                    channels["11"] += 1
                elif ch > 14:
                    channels["5ghz"] += 1
                else:
                    channels["other"] += 1
            else:
                channels["other"] += 1
        return channels

    def _detect_cloned_rogue_aps(self, aps: List[Dict]) -> List[Dict]:
        """Detects Evil Twin APs with identical SSID but conflicting security or MAC prefixes."""
        clones = []
        ssid_groups: Dict[str, List[Dict]] = {}
        for ap in aps:
            ssid = ap.get("ssid", "")
            if ssid and ssid != "<Hidden SSID>":
                ssid_groups.setdefault(ssid, []).append(ap)

        for ssid, group in ssid_groups.items():
            if len(group) > 1:
                # Check for security mismatch (e.g. one encrypted, one OPEN)
                sec_types = {ap.get("security") for ap in group}
                if len(sec_types) > 1:
                    clones.append({
                        "ssid": ssid,
                        "reason": "Security Mismatch (Possible Evil Twin)",
                        "instances": group,
                    })
                # Check for disparate vendor MAC OUI prefixes
                ouis = {ap["bssid"][:8] for ap in group if len(ap.get("bssid", "")) >= 8}
                if len(ouis) > 1 and len(group) >= 2:
                    clones.append({
                        "ssid": ssid,
                        "reason": "Mismatched Hardware Vendors across duplicate SSIDs",
                        "instances": group,
                    })

        return clones

    async def audit_connected_network(self) -> Dict:
        """Deep security audit of the currently connected Wi-Fi AP."""
        loop = asyncio.get_event_loop()
        audit_res = {
            "connected": False,
            "ssid": "Not Connected",
            "bssid": "",
            "channel": "",
            "frequency_mhz": 0,
            "signal_dbm": 0,
            "signal_pct": 0,
            "security": "UNKNOWN",
            "pmf_status": "Unknown (802.11w)",
            "pmf_protected": False,
            "wpa3_supported": False,
            "cipher": "CCMP",
            "gateway_arp_clean": True,
            "security_grade": "A",
            "recommendations": [],
        }

        try:
            cmd = ["iw", "dev", self.interface, "link"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=1.5),
            )
            if res.returncode == 0 and "Connected to" in res.stdout:
                audit_res["connected"] = True
                lines = res.stdout.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("Connected to"):
                        audit_res["bssid"] = line.split()[2].upper()
                    elif line.startswith("SSID:"):
                        audit_res["ssid"] = line.split("SSID:")[1].strip()
                    elif line.startswith("freq:"):
                        audit_res["frequency_mhz"] = int(line.split()[1])
                    elif line.startswith("signal:"):
                        sig_match = re.search(r"(-?\d+)\s*dBm", line)
                        if sig_match:
                            dbm = int(sig_match.group(1))
                            audit_res["signal_dbm"] = dbm
                            audit_res["signal_pct"] = max(0, min(100, 2 * (dbm + 100)))

        except Exception:
            pass

        # Check PMF support via wpa_cli if available
        try:
            cmd = ["wpa_cli", "-i", self.interface, "status"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=1.5),
            )
            if res.returncode == 0 and res.stdout:
                out = res.stdout
                if "pairwise_cipher=CCMP" in out or "pairwise_cipher=GCMP" in out:
                    audit_res["cipher"] = "AES-CCMP/GCMP (Strong)"
                elif "pairwise_cipher=TKIP" in out:
                    audit_res["cipher"] = "TKIP (Weak/Legacy)"
                    audit_res["recommendations"].append("Upgrade AP cipher from TKIP to AES-CCMP")

                if "pmf=2" in out or "pmf=REQUIRED" in out:
                    audit_res["pmf_status"] = "Enforced (802.11w Required)"
                    audit_res["pmf_protected"] = True
                elif "pmf=1" in out or "pmf=CAPABLE" in out:
                    audit_res["pmf_status"] = "Enabled (802.11w Optional)"
                    audit_res["pmf_protected"] = True
                else:
                    audit_res["pmf_status"] = "Disabled / Not Enforced"
                    audit_res["recommendations"].append("Enable Protected Management Frames (PMF / 802.11w) on your router to protect against deauth anomalies.")

                if "key_mgmt=SAE" in out or "WPA3" in out:
                    audit_res["wpa3_supported"] = True
                    audit_res["security"] = "WPA3-Personal (SAE)"
                elif "WPA2" in out or "key_mgmt=WPA-PSK" in out:
                    audit_res["security"] = "WPA2-Personal (PSK)"
        except Exception:
            pass

        # Grade the current network
        recs = audit_res["recommendations"]
        if audit_res["wpa3_supported"] and audit_res["pmf_protected"]:
            audit_res["security_grade"] = "A+"
        elif audit_res["pmf_protected"]:
            audit_res["security_grade"] = "A"
        elif audit_res["cipher"].startswith("AES"):
            audit_res["security_grade"] = "B+"
        else:
            audit_res["security_grade"] = "C"

        self.current_connection_audit = audit_res
        return audit_res

    def export_wigle_csv(self) -> str:
        """Exports all discovered Wi-Fi access points in standard Wigle CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Wigle Header standard
        writer.writerow(["WigleWifi-1.4", "appRelease=OmniGotchi-2.0", "model=RaspberryPi", "release=Linux", "device=OmniGotchi", "display=E-Ink", "board=PiZero2W", "brand=Raspberry"])
        writer.writerow(["MAC", "SSID", "AuthMode", "FirstSeen", "Channel", "RSSI", "CurrentLatitude", "CurrentLongitude", "AltitudeMeters", "AccuracyMeters", "Type"])

        for bssid, data in self.discovered_aps.items():
            first_seen_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.get("first_seen", time.time())))
            writer.writerow([
                bssid,
                data.get("ssid", "<Hidden>"),
                f"[{data.get('wpa_ver', 'WPA2')}-{data.get('cipher', 'CCMP')}]",
                first_seen_str,
                data.get("channel", "1"),
                data.get("signal", 50) - 100,  # Approximate dBm
                0.0,
                0.0,
                0.0,
                0.0,
                "WIFI",
            ])

        return output.getvalue()
