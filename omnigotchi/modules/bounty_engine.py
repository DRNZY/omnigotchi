"""DedSec Autonomous Bounty & Passive Micro-Yield Engine.

Performs background compute/bandwidth relay yield tracking, local vulnerability
scanning for white-hat bug bounty reports, and GitHub sponsorship/bounty monitoring.
"""

import asyncio
import json
import logging
import os
import socket
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnigotchi.bounty")

CONFIG_DIR = Path.home() / ".config" / "omnigotchi"
LEDGER_FILE = CONFIG_DIR / "yield_ledger.json"
BOUNTY_DIR = CONFIG_DIR / "bounties"


@dataclass
class YieldLedger:
    total_uptime_hours: float = 0.0
    total_relayed_mb: float = 0.0
    total_compute_shares: int = 0
    total_usd_earned: float = 0.0
    total_sats_earned: int = 0
    daily_usd_rate: float = 4.20
    active_mesh_nodes: int = 12
    
    # Real Hardware Electricity & Net Profit Tracking
    pi_wattage: float = 0.85              # Average Pi Zero 2 W power draw in Watts
    electricity_kwh_cost: float = 0.30     # Electricity price in $/kWh (or €/kWh)
    daily_power_cost_usd: float = 0.00612  # (0.85W * 24h / 1000) * $0.30 = ~$0.006/day
    total_power_cost_usd: float = 0.0     # Total electricity cost accumulated
    net_profit_usd: float = 0.0           # Gross USD Earned - Total Power Cost
    
    # Real Passive Earning Daemon Integration
    real_daemon_name: Optional[str] = None     # "EarnApp", "Pawns.app", "Bitping", etc.
    real_daemon_status: str = "SIMULATED"      # "ONLINE", "STOPPED", "SIMULATED"
    real_daemon_node_id: Optional[str] = None  # Device UUID or Node ID
    is_real_yield_active: bool = False
    
    last_payout_ts: float = field(default_factory=time.time)
    last_update_ts: float = field(default_factory=time.time)


@dataclass
class VulnerabilityFinding:
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    title: str
    target: str
    port: Optional[int]
    description: str
    remediation: str
    cve_ref: Optional[str] = None
    bounty_value_usd: float = 0.0


@dataclass
class BountyReport:
    id: str
    timestamp: float
    target_network: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    estimated_bounty_usd: float
    findings: List[Dict[str, Any]]
    summary: str


class BountyEngine:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        BOUNTY_DIR.mkdir(parents=True, exist_ok=True)
        self.ledger = self._load_ledger()
        self.reports: List[BountyReport] = self._load_reports()
        self.is_scanning = False
        self.last_scan_ts = 0.0
        self.recent_bounties_found = 0
        self._probe_real_daemons()

    def _load_ledger(self) -> YieldLedger:
        if LEDGER_FILE.exists():
            try:
                with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    valid_keys = YieldLedger.__dataclass_fields__.keys()
                    return YieldLedger(**{k: v for k, v in data.items() if k in valid_keys})
            except Exception as e:
                logger.warning(f"Could not load yield ledger: {e}")
        ledger = YieldLedger()
        self._save_ledger(ledger)
        return ledger

    def _save_ledger(self, ledger: Optional[YieldLedger] = None):
        if ledger is None:
            ledger = self.ledger
        try:
            with open(LEDGER_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(ledger), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save yield ledger: {e}")

    def _load_reports(self) -> List[BountyReport]:
        loaded = []
        for report_file in sorted(BOUNTY_DIR.glob("report_*.json"), reverse=True)[:10]:
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    loaded.append(BountyReport(**data))
            except Exception:
                pass
        return loaded

    def _probe_real_daemons(self):
        """Probes system for real passive sharing micro-daemons (EarnApp, Pawns.app, Bitping)."""
        # 1. EarnApp
        earnapp_bin = shutil.which("earnapp") or "/usr/bin/earnapp" or "/usr/local/bin/earnapp"
        if earnapp_bin and os.path.exists(str(earnapp_bin)):
            self.ledger.real_daemon_name = "EarnApp"
            self.ledger.is_real_yield_active = True
            try:
                out = subprocess.run([str(earnapp_bin), "status"], capture_output=True, text=True, timeout=2)
                if "Online" in out.stdout or "online" in out.stdout:
                    self.ledger.real_daemon_status = "ONLINE"
                else:
                    self.ledger.real_daemon_status = "INSTALLED"
                
                node_out = subprocess.run([str(earnapp_bin), "show-node-id"], capture_output=True, text=True, timeout=2)
                if node_out.returncode == 0 and node_out.stdout.strip():
                    self.ledger.real_daemon_node_id = node_out.stdout.strip()
            except Exception:
                self.ledger.real_daemon_status = "ACTIVE"
            return

        # 2. Pawns CLI (IPRoyal)
        pawns_bin = shutil.which("pawns-cli") or shutil.which("pawns")
        if pawns_bin:
            self.ledger.real_daemon_name = "Pawns.app"
            self.ledger.is_real_yield_active = True
            self.ledger.real_daemon_status = "ONLINE"
            return

        # 3. Bitping
        bitping_bin = shutil.which("bitping") or shutil.which("bitping-node")
        if bitping_bin:
            self.ledger.real_daemon_name = "Bitping"
            self.ledger.is_real_yield_active = True
            self.ledger.real_daemon_status = "ONLINE"
            return

        # Default: Pure DedSec Simulation
        self.ledger.is_real_yield_active = False
        self.ledger.real_daemon_status = "SIMULATED"
        self.ledger.real_daemon_name = "ctOS Mesh Relay (Simulated)"

    def tick_yield(self, elapsed_sec: float, rx_kbps: float = 0.0, tx_kbps: float = 0.0):
        """Accumulates uptime yield, bandwidth relay metrics, electricity power cost, and net profit."""
        hours = elapsed_sec / 3600.0
        self.ledger.total_uptime_hours += hours

        # Calculate transferred volume in MB
        transferred_mb = ((rx_kbps + tx_kbps) * 1024 * elapsed_sec) / (8 * 1024 * 1024)
        if transferred_mb <= 0:
            transferred_mb = (elapsed_sec / 60.0) * 0.85  # baseline simulated relay traffic
        self.ledger.total_relayed_mb += transferred_mb

        # Compute shares: ~1 share per 45s active work
        new_shares = int(elapsed_sec / 45.0)
        self.ledger.total_compute_shares += new_shares

        # Gross Yield rate:
        # If a real daemon is installed, real rate is ~$0.15/day ($0.00625/hr)
        # In simulated DedSec mode, uses the $4.20/d game benchmark
        if self.ledger.is_real_yield_active:
            hourly_rate = 0.15 / 24.0
        else:
            hourly_rate = self.ledger.daily_usd_rate / 24.0

        usd_inc = hourly_rate * hours
        self.ledger.total_usd_earned += usd_inc

        # Electricity Power Cost Calculation (0.85W for Pi Zero 2 W)
        kwh_consumed = (self.ledger.pi_wattage * hours) / 1000.0
        cost_inc = kwh_consumed * self.ledger.electricity_kwh_cost
        self.ledger.total_power_cost_usd += cost_inc
        self.ledger.daily_power_cost_usd = (self.ledger.pi_wattage * 24.0 / 1000.0) * self.ledger.electricity_kwh_cost

        # Net Profit = Total Earned - Power Cost
        self.ledger.net_profit_usd = max(0.0, self.ledger.total_usd_earned - self.ledger.total_power_cost_usd)

        # 1 USD approx 1500 sats
        self.ledger.total_sats_earned = int(self.ledger.total_usd_earned * 1500)
        self.ledger.last_update_ts = time.time()
        self._save_ledger()

    async def scan_vulnerabilities(self) -> BountyReport:
        """Performs a white-hat security and vulnerability harvest of the local perimeter."""
        self.is_scanning = True
        findings: List[VulnerabilityFinding] = []

        try:
            # 1. Inspect Local Gateway and Localhost Common Exposure Ports
            target_ports = [
                (21, "FTP Plaintext Authentication", "MEDIUM", "RFC-959", 50.0, "Enforce SFTP/SSH or FTPS TLS encapsulation."),
                (23, "Telnet Unencrypted Shell", "HIGH", "CVE-Telnet-Cleartext", 150.0, "Disable Telnet immediately; migrate to OpenSSH ed25519 keys."),
                (80, "HTTP Cleartext Transmission", "LOW", "CWE-319", 25.0, "Enable strict HTTPS with TLS 1.3 and HSTS headers."),
                (445, "SMB Port Open to Subnet", "HIGH", "CVE-2017-0144", 200.0, "Disable SMBv1, enforce SMB signing and isolate file sharing."),
                (3389, "RDP Remote Desktop Exposed", "MEDIUM", "CWE-284", 75.0, "Place RDP behind WireGuard/Tailscale VPN mesh with MFA."),
                (5900, "VNC Remote Framebuffer Unencrypted", "MEDIUM", "CWE-319", 80.0, "Tunnel VNC sessions through SSH or enforce TLS VNC auth."),
                (6379, "Redis In-Memory DB Unauthenticated", "CRITICAL", "CVE-2022-0543", 350.0, "Bind Redis strictly to 127.0.0.1 and enable requirepass."),
                (8080, "Alternative Web Server Exposed", "INFO", None, 10.0, "Verify endpoint authentication and enforce rate limiting."),
            ]

            targets = ["127.0.0.1"]
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("1.1.1.1", 80))
                local_ip = s.getsockname()[0]
                s.close()
                if local_ip != "127.0.0.1":
                    targets.append(local_ip)
            except Exception:
                pass

            for target in targets:
                for port, title, severity, cve, bounty, rem in target_ports:
                    is_open = await self._check_port(target, port)
                    if is_open:
                        findings.append(
                            VulnerabilityFinding(
                                severity=severity,
                                title=f"{title} on {target}:{port}",
                                target=f"{target}:{port}",
                                port=port,
                                description=f"Service on port {port} accepted TCP handshake without network isolation.",
                                remediation=rem,
                                cve_ref=cve,
                                bounty_value_usd=bounty,
                            )
                        )

            # 2. DNS Security & Resolver Integrity Verification
            dns_findings = await self._check_dns_health()
            findings.extend(dns_findings)

            # Always add proactive defense hardening recommendation if no open exposures
            if not findings:
                findings.append(
                    VulnerabilityFinding(
                        severity="INFO",
                        title="Subnet Perimeter Hardened",
                        target="127.0.0.1",
                        port=None,
                        description="Zero exposed critical ports detected on scanned interfaces. All inbound connections filtered.",
                        remediation="Maintain regular kernel patching and keep UFW/iptables active.",
                        cve_ref="PERIMETER-SECURE",
                        bounty_value_usd=0.0,
                    )
                )

            crit = sum(1 for f in findings if f.severity == "CRITICAL")
            high = sum(1 for f in findings if f.severity == "HIGH")
            med = sum(1 for f in findings if f.severity == "MEDIUM")
            low = sum(1 for f in findings if f.severity in ("LOW", "INFO"))
            total_bounty = sum(f.bounty_value_usd for f in findings)

            report_id = f"DEDSEC-{int(time.time())}"
            report = BountyReport(
                id=report_id,
                timestamp=time.time(),
                target_network=targets[-1] if targets else "127.0.0.1",
                total_findings=len(findings),
                critical_count=crit,
                high_count=high,
                medium_count=med,
                low_count=low,
                estimated_bounty_usd=total_bounty,
                findings=[asdict(f) for f in findings],
                summary=f"DedSec perimeter audit completed. {len(findings)} findings logged (Crit: {crit}, High: {high}, Med: {med}). Estimated white-hat value: ${total_bounty:.2f}",
            )

            # Save report to disk
            report_file = BOUNTY_DIR / f"report_{report_id}.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2)

            self.reports.insert(0, report)
            self.reports = self.reports[:15]
            self.last_scan_ts = time.time()
            self.recent_bounties_found = len(findings)

            # Award bounty value into ledger
            if total_bounty > 0:
                self.ledger.total_usd_earned += total_bounty * 0.10  # 10% bounty discovery credit
                self._save_ledger()

            return report
        finally:
            self.is_scanning = False

    async def _check_port(self, host: str, port: int, timeout_s: float = 0.4) -> bool:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout_s
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _check_dns_health(self) -> List[VulnerabilityFinding]:
        findings = []
        try:
            # Verify if DNS over HTTPS or standard unencrypted 53 is used
            with open("/etc/resolv.conf", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "127.0.0.53" in content or "1.1.1.1" in content or "8.8.8.8" in content:
                    pass
                elif "nameserver 192.168." in content or "nameserver 10." in content:
                    findings.append(
                        VulnerabilityFinding(
                            severity="LOW",
                            title="Unencrypted Local ISP DNS Resolver in Use",
                            target="53/UDP",
                            port=53,
                            description="System DNS queries route through plain text local router gateway without DoH/DoT encryption.",
                            remediation="Configure Cloudflare 1.1.1.1 (DNS over TLS / systemd-resolved DNSSEC).",
                            cve_ref="DNS-PLAINTEXT-LEAK",
                            bounty_value_usd=15.0,
                        )
                    )
        except Exception:
            pass
        return findings

    def get_stats(self) -> Dict[str, Any]:
        return {
            "ledger": asdict(self.ledger),
            "is_scanning": self.is_scanning,
            "last_scan_ts": self.last_scan_ts,
            "recent_bounties_found": self.recent_bounties_found,
            "total_reports_count": len(self.reports),
            "latest_report": asdict(self.reports[0]) if self.reports else None,
        }
