"""Audio Sentinel: Listens to Cadence Desktop & MPRIS Linux media players."""

import asyncio
import logging
import subprocess
from typing import Dict
import aiohttp

logger = logging.getLogger("omnigotchi.audio")


class AudioModule:
    def __init__(self, cadence_url: str = "http://127.0.0.1:3001"):
        self.cadence_url = cadence_url.rstrip("/")
        self.cached_state: Dict = {
            "is_playing": False,
            "title": "",
            "artist": "",
            "album": "",
            "format": "",
            "source": "None",
        }

    async def poll(self) -> Dict:
        # Try Cadence Desktop HTTP / SSE first
        cadence_active = await self._poll_cadence()
        if not cadence_active:
            # Fallback to system MPRIS / playerctl if available
            self._poll_mpris()

        return self.cached_state

    async def _poll_cadence(self) -> bool:
        url = f"{self.cadence_url}/api/status"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=1.0)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.cached_state = {
                            "is_playing": data.get("isPlaying", False),
                            "title": data.get("title", ""),
                            "artist": data.get("artist", ""),
                            "album": data.get("album", ""),
                            "format": data.get("format", "FLAC"),
                            "source": "Cadence",
                        }
                        return True
        except Exception:
            pass
        return False

    def _poll_mpris(self):
        """Queries MPRIS playerctl for now-playing media."""
        try:
            # Check player status
            res = subprocess.run(
                ["playerctl", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=0.5,
            )
            if res.returncode == 0 and res.stdout.strip().lower() == "playing":
                title_res = subprocess.run(
                    ["playerctl", "metadata", "--format", "{{title}}|||{{artist}}|||{{album}}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5,
                )
                if title_res.returncode == 0 and title_res.stdout.strip():
                    parts = title_res.stdout.strip().split("|||")
                    self.cached_state = {
                        "is_playing": True,
                        "title": parts[0] if len(parts) > 0 else "Unknown Title",
                        "artist": parts[1] if len(parts) > 1 else "Unknown Artist",
                        "album": parts[2] if len(parts) > 2 else "",
                        "format": "Audio",
                        "source": "MPRIS",
                    }
                    return
        except Exception:
            pass

        self.cached_state = {
            "is_playing": False,
            "title": "",
            "artist": "",
            "album": "",
            "format": "",
            "source": "None",
        }
