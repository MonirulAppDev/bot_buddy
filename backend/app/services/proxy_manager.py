import asyncio
import concurrent.futures
import logging
import random
import re
import ssl
import time
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("proxy_manager")

PUBLIC_SOURCES = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
]


class ProxyManager:
    """Manages high-speed rotating HTTP/HTTPS proxy pool with live health checking and custom lists."""

    def __init__(self):
        self.auto_proxies: List[Dict[str, Any]] = []
        self.custom_proxies: List[Dict[str, Any]] = []
        self.mode: str = "auto"  # 'auto', 'custom', 'direct'
        self.last_fetched: float = 0
        self.is_fetching: bool = False

    def get_stats(self) -> Dict[str, Any]:
        active_count = len(self.custom_proxies) if self.mode == "custom" else len(self.auto_proxies)
        return {
            "mode": self.mode,
            "auto_proxies_count": len(self.auto_proxies),
            "custom_proxies_count": len(self.custom_proxies),
            "total_available": active_count,
            "is_fetching": self.is_fetching,
            "last_fetched": self.last_fetched,
            "sample_proxies": [p["display"] for p in (self.custom_proxies if self.mode == "custom" else self.auto_proxies)[:8]]
        }

    def set_mode(self, mode: str):
        if mode in ["auto", "custom", "direct"]:
            self.mode = mode
            logger.info(f"Proxy mode updated to: {self.mode}")

    def import_custom_proxies(self, raw_text: str) -> int:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        imported = []
        for line in lines:
            if "@" in line:
                auth, server = line.split("@", 1)
                user, pwd = auth.split(":", 1)
                clean_srv = server.strip().replace("http://", "").replace("https://", "")
                imported.append({
                    "server": f"http://{clean_srv}",
                    "username": user.strip(),
                    "password": pwd.strip(),
                    "display": clean_srv
                })
            elif line.count(":") == 3:
                parts = line.split(":")
                imported.append({
                    "server": f"http://{parts[0].strip()}:{parts[1].strip()}",
                    "username": parts[2].strip(),
                    "password": parts[3].strip(),
                    "display": f"{parts[0].strip()}:{parts[1].strip()}"
                })
            elif ":" in line:
                clean_line = line.strip().replace("http://", "").replace("https://", "")
                imported.append({
                    "server": f"http://{clean_line}",
                    "username": None,
                    "password": None,
                    "display": clean_line
                })
        self.custom_proxies = imported
        if imported:
            self.mode = "custom"
        logger.info(f"Imported {len(imported)} custom proxies. Switched mode to '{self.mode}'.")
        return len(imported)

    async def refresh_public_proxies(self, max_check: int = 300) -> int:
        """Fetch fresh public proxy lists and asynchronously validate live ones using high concurrency."""
        if self.is_fetching:
            return len(self.auto_proxies)

        self.is_fetching = True
        loop = asyncio.get_running_loop()

        def _worker_fetch_and_check() -> List[Dict[str, Any]]:
            raw_candidates = []
            ctx = ssl._create_unverified_context()
            for source in PUBLIC_SOURCES:
                try:
                    req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
                        lines = [l.strip() for l in resp.read().decode("utf-8", errors="ignore").splitlines() if l.strip() and ":" in l]
                        raw_candidates.extend(lines)
                except Exception as e:
                    logger.warning(f"Failed fetching proxies from {source}: {e}")

            raw_candidates = list(set(raw_candidates))
            random.shuffle(raw_candidates)
            candidates = raw_candidates[:max_check]

            with concurrent.futures.ThreadPoolExecutor(max_workers=75) as executor:
                results = list(executor.map(self._test_single_proxy, candidates))

            return [r for r in results if r is not None]

        try:
            valid_proxies = await loop.run_in_executor(None, _worker_fetch_and_check)
            if valid_proxies:
                self.auto_proxies = valid_proxies
                self.last_fetched = time.time()
                logger.info(f"Verified {len(valid_proxies)} live public proxies for rotating pool.")
            return len(self.auto_proxies)
        finally:
            self.is_fetching = False

    def _test_single_proxy(self, proxy_str: str) -> Optional[Dict[str, Any]]:
        t0 = time.time()
        clean = proxy_str.replace("http://", "").replace("https://", "").strip()
        try:
            handler = urllib.request.ProxyHandler({"http": f"http://{clean}", "https": f"http://{clean}"})
            opener = urllib.request.build_opener(handler)
            req = urllib.request.Request("http://httpbin.org/ip", headers={"User-Agent": "Mozilla/5.0"})
            with opener.open(req, timeout=2.5) as resp:
                if resp.status == 200:
                    latency = round((time.time() - t0) * 1000)
                    return {
                        "server": f"http://{clean}",
                        "username": None,
                        "password": None,
                        "display": clean,
                        "latency_ms": latency
                    }
        except Exception:
            pass
        return None

    def get_proxy_for_view(self, view_idx: int) -> Optional[Dict[str, Any]]:
        """Get assigned proxy configuration for Playwright context."""
        if self.mode == "direct":
            return None

        pool = self.custom_proxies if self.mode == "custom" and self.custom_proxies else self.auto_proxies
        if not pool:
            return None

        # Pick cyclically based on view_idx to ensure distinct IP per view
        chosen = pool[(view_idx - 1) % len(pool)]
        cfg = {"server": chosen["server"]}
        if chosen.get("username"):
            cfg["username"] = chosen["username"]
        if chosen.get("password"):
            cfg["password"] = chosen["password"]
        cfg["display"] = chosen.get("display", chosen["server"])
        return cfg


proxy_manager = ProxyManager()
