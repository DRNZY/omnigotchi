"""Dev & GitHub Sentinel: Tracks streaks, commits, and project activity."""

import asyncio
import logging
import os
import subprocess
import time
from typing import Dict, Optional
import aiohttp

logger = logging.getLogger("omnigotchi.dev")


class DevModule:
    def __init__(self, username: str = "DRNZY", token: str = "", projects_dir: str = "~/Projects"):
        self.username = username
        self.token = token
        self.projects_dir = os.path.expanduser(projects_dir)
        self.cached_stats: Dict = {
            "streak_days": 1,
            "followers": 24,
            "public_repos": 10,
            "recent_commits_24h": 0,
            "last_repo": "",
            "last_commit_msg": "",
            "is_active_repo": False,
        }
        self.last_github_poll = 0
        self.last_local_scan = 0

    async def poll(self) -> Dict:
        now = time.time()
        # Scan local repos frequently (every 30s)
        if now - self.last_local_scan > 30:
            self._scan_local_git()
            self.last_local_scan = now

        # Poll GitHub API every 5 minutes (or 60s if token present)
        gh_interval = 60 if self.token else 300
        if now - self.last_github_poll > gh_interval:
            await self._poll_github()
            self.last_github_poll = now

        return self.cached_stats

    def _scan_local_git(self):
        """Scans local git repositories for commits in the last 24 hours."""
        if not os.path.exists(self.projects_dir):
            return

        total_recent_commits = 0
        most_recent_repo = ""
        latest_commit_time = 0
        latest_msg = ""

        try:
            for item in os.listdir(self.projects_dir):
                repo_path = os.path.join(self.projects_dir, item)
                git_dir = os.path.join(repo_path, ".git")
                if os.path.isdir(git_dir):
                    # Check git log --since="24 hours ago" --format="%ct|%s" -n 5
                    cmd = [
                        "git", "-C", repo_path, "log", "--since=24 hours ago",
                        "--format=%ct|%s", "-n", "5"
                    ]
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if res.returncode == 0 and res.stdout.strip():
                        lines = res.stdout.strip().split("\n")
                        total_recent_commits += len(lines)
                        for line in lines:
                            parts = line.split("|", 1)
                            if len(parts) == 2:
                                t = int(parts[0])
                                if t > latest_commit_time:
                                    latest_commit_time = t
                                    most_recent_repo = item
                                    latest_msg = parts[1]

            self.cached_stats["recent_commits_24h"] = total_recent_commits
            if most_recent_repo:
                self.cached_stats["last_repo"] = most_recent_repo
                self.cached_stats["last_commit_msg"] = latest_msg
                # Active if committed in last 2 hours
                self.cached_stats["is_active_repo"] = (time.time() - latest_commit_time) < 7200
        except Exception as e:
            logger.debug(f"Local git scan exception: {e}")

    async def _poll_github(self):
        """Fetches public user stats and events from GitHub."""
        if not self.username:
            return

        headers = {"User-Agent": "OmniGotchi-Desk-Companion"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"https://api.github.com/users/{self.username}"
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.cached_stats["followers"] = data.get("followers", self.cached_stats["followers"])
                        self.cached_stats["public_repos"] = data.get("public_repos", self.cached_stats["public_repos"])
                    elif resp.status == 403:
                        logger.debug("GitHub rate limit reached, using cached stats.")
        except Exception as e:
            logger.debug(f"GitHub fetch error: {e}")
