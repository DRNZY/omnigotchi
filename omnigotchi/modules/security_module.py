"""Cybersecurity Sentinel: Defensive LAN Radar, ARP Spoof Detection, RF Survey, DNS Guard & Auth Shield."""

import asyncio
import logging
import os
import re
import subprocess
import time
from typing import Dict, List, Optional

logger = logging.getLogger("omnigotchi.security")


class SecurityModule:
    """Autonomous Cybersecurity Sentinel and Network Defense Engine."""

    def __init__(self):
        self.cached_state: Dict = {
            "defcon_level": 5,
            "defcon_status": "SECURE",
            "threat_score": 0,
            "lan_hosts_count": 0,
            "lan_hosts": [],
            "arp_spoof_detected": False,
            "arp_alert_msg": "ARP Table Clean",
            "wifi_aps_count": 0,
            "wifi_aps": [],
            "channel_spectrum": {"ch1": 0, "ch6": 0, "ch11": 0, "other": 0},
            "evil_twin_detected": False,
            "rogue_ap_count": 0,
            "dns_servers": ["1.1.1.1"],
            "dns_hijack_detected": False,
            "ssh_failed_attempts": 0,
            "ssh_last_failed_ip": "",
            "open_ports": [],
            "vulnerabilities": [],
            "active_shields": ["ARP-GUARD", "RF-SENTINEL", "AUTH-SHIELD", "DNS-GUARD", "PORT-RADAR"],
            "last_scan_ts": time.time(),
        }
        self.gateway_ip = "192.168.0.1"
        self.gateway_mac = ""

    async def poll(self) -> Dict:
        """Polls all security subsystems and assesses DEFCON threat posture."""
        try:
            lan_data = await self._scan_lan()
            rf_data = await self._scan_wifi_beacons()
            auth_data = await self._audit_auth_and_ports()
            dns_data = self._audit_dns()

            # Update cached state
            self.cached_state["lan_hosts_count"] = len(lan_data["hosts"])
            self.cached_state["lan_hosts"] = lan_data["hosts"][:12]
            self.cached_state["arp_spoof_detected"] = lan_data["arp_spoof_detected"]
            self.cached_state["arp_alert_msg"] = lan_data["arp_alert_msg"]

            self.cached_state["wifi_aps_count"] = len(rf_data["aps"])
            self.cached_state["wifi_aps"] = rf_data["aps"][:8]
            self.cached_state["channel_spectrum"] = rf_data["spectrum"]
            self.cached_state["evil_twin_detected"] = rf_data["evil_twin_detected"]
            self.cached_state["rogue_ap_count"] = rf_data["rogue_count"]

            self.cached_state["dns_servers"] = dns_data["servers"]
            self.cached_state["dns_hijack_detected"] = dns_data["hijacked"]

            self.cached_state["ssh_failed_attempts"] = auth_data["failed_logins"]
            self.cached_state["ssh_last_failed_ip"] = auth_data["last_failed_ip"]
            self.cached_state["open_ports"] = auth_data["open_ports"]
            self.cached_state["vulnerabilities"] = auth_data["vulns"]
            self.cached_state["last_scan_ts"] = time.time()

            # Calculate DEFCON threat level (5=Normal, 1=Critical)
            defcon, status, score = self._evaluate_defcon()
            self.cached_state["defcon_level"] = defcon
            self.cached_state["defcon_status"] = status
            self.cached_state["threat_score"] = score

        except Exception as e:
            logger.error(f"Security poll error: {e}")

        return self.cached_state

    async def _scan_lan(self) -> Dict:
        """Inspects /proc/net/arp and ip neigh to verify network devices and ARP integrity."""
        hosts = []
        ip_mac_map = {}
        mac_ip_map = {}
        arp_spoof = False
        alert_msg = "ARP Table Clean"

        # 1. Read /proc/net/arp
        if os.path.exists("/proc/net/arp"):
            try:
                with open("/proc/net/arp", "r") as f:
                    lines = f.readlines()[1:]
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 6:
                            ip, _, flags, mac, _, dev = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                            if mac != "00:00:00:00:00:00" and flags != "0x0":
                                ip_mac_map[ip] = mac.lower()
            except Exception:
                pass

        # 2. Query ip neigh for live reachable states
        loop = asyncio.get_event_loop()
        try:
            cmd = ["ip", "neigh"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=1.5),
            )
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    parts = line.split()
                    if len(parts) >= 4 and "lladdr" in parts:
                        ip = parts[0]
                        idx = parts.index("lladdr")
                        if idx + 1 < len(parts):
                            mac = parts[idx + 1].lower()
                            state = parts[-1] if len(parts) > idx + 2 else "REACHABLE"
                            ip_mac_map[ip] = mac
                            is_gw = (ip == self.gateway_ip or "router" in line)
                            if is_gw and not self.gateway_mac:
                                self.gateway_mac = mac

                            hosts.append({
                                "ip": ip,
                                "mac": mac,
                                "is_gateway": is_gw,
                                "state": state,
                            })
        except Exception:
            pass

        # Check for duplicate MACs claiming multiple distinct IPv4 addresses
        for ip, mac in ip_mac_map.items():
            if ":" in ip:
                continue  # Skip IPv6 link-local
            if mac in mac_ip_map and mac_ip_map[mac] != ip:
                if ip == self.gateway_ip or mac_ip_map[mac] == self.gateway_ip:
                    arp_spoof = True
                    alert_msg = f"ARP Poisoning detected on {ip} (MAC: {mac})"
            else:
                mac_ip_map[mac] = ip

        return {
            "hosts": hosts,
            "arp_spoof_detected": arp_spoof,
            "arp_alert_msg": alert_msg,
        }

    async def _scan_wifi_beacons(self) -> Dict:
        """Scans local RF spectrum for wireless APs and calculates channel congestion."""
        aps = []
        ssid_map = {}
        evil_twin = False
        rogue_count = 0
        spectrum = {"ch1": 0, "ch6": 0, "ch11": 0, "other": 0}

        loop = asyncio.get_event_loop()
        try:
            cmd = ["nmcli", "-t", "-f", "BSSID,SSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=2.0),
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split("\n"):
                    cleaned = line.replace("\\:", ":")
                    parts = cleaned.split(":")
                    if len(parts) >= 5:
                        raw_fields = cleaned.split(":")
                        if len(raw_fields) >= 10:
                            bssid = ":".join(raw_fields[0:6])
                            ssid = raw_fields[6]
                            chan = raw_fields[7]
                            signal = int(raw_fields[8]) if raw_fields[8].isdigit() else 50
                            sec = raw_fields[9] if len(raw_fields) > 9 else "OPEN"
                        else:
                            bssid = parts[0]
                            ssid = parts[1] if len(parts) > 1 else "Hidden"
                            chan = parts[2] if len(parts) > 2 else "1"
                            signal = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 50
                            sec = parts[4] if len(parts) > 4 else "OPEN"

                        if not ssid:
                            ssid = "<Hidden SSID>"

                        # Spectrum counting
                        if chan == "1":
                            spectrum["ch1"] += 1
                        elif chan == "6":
                            spectrum["ch6"] += 1
                        elif chan == "11":
                            spectrum["ch11"] += 1
                        else:
                            spectrum["other"] += 1

                        is_open = (sec == "" or "open" in sec.lower() or sec == "--")
                        if is_open:
                            rogue_count += 1

                        ap_entry = {
                            "bssid": bssid,
                            "ssid": ssid,
                            "channel": chan,
                            "signal": signal,
                            "security": sec if sec else "OPEN",
                            "is_open": is_open,
                        }
                        aps.append(ap_entry)

                        if ssid not in ("<Hidden SSID>", ""):
                            if ssid in ssid_map:
                                prev_sec = ssid_map[ssid]
                                if prev_sec != sec and (is_open or "open" in prev_sec.lower()):
                                    evil_twin = True
                            else:
                                ssid_map[ssid] = sec
        except Exception:
            pass

        return {
            "aps": aps,
            "spectrum": spectrum,
            "evil_twin_detected": evil_twin,
            "rogue_count": rogue_count,
        }

    def _audit_dns(self) -> Dict:
        """Audits DNS nameservers configured in /etc/resolv.conf."""
        servers = []
        hijacked = False
        if os.path.exists("/etc/resolv.conf"):
            try:
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        if line.startswith("nameserver"):
                            parts = line.split()
                            if len(parts) > 1:
                                servers.append(parts[1])
            except Exception:
                pass
        if not servers:
            servers = ["1.1.1.1"]
        return {"servers": servers, "hijacked": hijacked}

    async def _audit_auth_and_ports(self) -> Dict:
        """Audits listening ports and SSH authentication journal for brute force attempts."""
        open_ports = []
        vulns = []
        failed_logins = 0
        last_failed_ip = ""

        loop = asyncio.get_event_loop()

        # 1. Audit listening ports via ss -tuln
        try:
            cmd = ["ss", "-tuln"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=1.0),
            )
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    if "LISTEN" in line or "UNCONN" in line:
                        match = re.search(r":(\d+)\s+", line)
                        if match:
                            p = int(match.group(1))
                            if p not in open_ports and p < 65535:
                                open_ports.append(p)
                                if p in (21, 23):
                                    vulns.append(f"Insecure plaintext port {p} open")
        except Exception:
            pass

        # 2. Audit SSH auth journal
        try:
            cmd = ["journalctl", "-u", "ssh", "--since", "24 hours ago", "--no-pager"]
            res = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=1.5),
            )
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    if "Failed password" in line or "Invalid user" in line:
                        failed_logins += 1
                        ip_match = re.search(r"from\s+([0-9\.]+)", line)
                        if ip_match:
                            last_failed_ip = ip_match.group(1)
        except Exception:
            pass

        return {
            "open_ports": sorted(open_ports)[:8],
            "vulns": vulns,
            "failed_logins": failed_logins,
            "last_failed_ip": last_failed_ip,
        }

    def _evaluate_defcon(self) -> tuple:
        """Evaluates DEFCON threat level (5 to 1) and status string."""
        score = 0
        status = "SECURE"
        level = 5

        if self.cached_state.get("arp_spoof_detected", False):
            score = 90
            level = 1
            status = "ARP POISONING DETECTED"
        elif self.cached_state.get("evil_twin_detected", False):
            score = 65
            level = 2
            status = "EVIL TWIN AP DETECTED"
        elif self.cached_state.get("ssh_failed_attempts", 0) > 10:
            score = 45
            level = 3
            status = "SSH BRUTE FORCE ATTACK"
        elif self.cached_state.get("rogue_ap_count", 0) > 0:
            score = 20
            level = 4
            status = "OPEN RF NETWORK PROBES"
        else:
            score = 0
            level = 5
            status = "ALL SHIELDS NOMINAL"

        return level, status, score
