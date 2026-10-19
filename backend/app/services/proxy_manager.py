import asyncio
import concurrent.futures
import logging
import random
import re
import socket
import ssl
import time
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("proxy_manager")

SOCKS5_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
]

HTTP_SOURCES = [
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
]


class ProxyManager:
    """Manages high-speed rotating SOCKS5 and HTTP/HTTPS proxy pool with live health checking and custom lists."""

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
            proto = "socks5" if "socks5://" in line else "http"
            clean = line.replace("socks5://", "").replace("http://", "").replace("https://", "").strip()
            if "@" in clean:
                auth, server = clean.split("@", 1)
                user, pwd = auth.split(":", 1)
                imported.append({
                    "server": f"{proto}://{server.strip()}",
                    "username": user.strip(),
                    "password": pwd.strip(),
                    "display": server.strip()
                })
            elif clean.count(":") == 3:
                parts = clean.split(":")
                imported.append({
                    "server": f"{proto}://{parts[0].strip()}:{parts[1].strip()}",
                    "username": parts[2].strip(),
                    "password": parts[3].strip(),
                    "display": f"{parts[0].strip()}:{parts[1].strip()}"
                })
            elif ":" in clean:
                imported.append({
                    "server": f"{proto}://{clean}",
                    "username": None,
                    "password": None,
                    "display": clean
                })
        self.custom_proxies = imported
        if imported:
            self.mode = "custom"
        logger.info(f"Imported {len(imported)} custom proxies. Switched mode to '{self.mode}'.")
        return len(imported)

    async def refresh_public_proxies(self, max_check: int = 500) -> int:
        """Fetch fresh public SOCKS5 and HTTP proxy lists and asynchronously validate live ones using high concurrency."""
        if self.is_fetching:
            return len(self.auto_proxies)

        self.is_fetching = True
        loop = asyncio.get_running_loop()

        def _worker_fetch_and_check() -> List[Dict[str, Any]]:
            ordered_candidates = []
            seen = set()
            ctx = ssl._create_unverified_context()
            for source in SOCKS5_SOURCES:
                try:
                    req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
                        lines = [l.strip() for l in resp.read().decode("utf-8", errors="ignore").splitlines() if l.strip() and ":" in l]
                        for line in lines:
                            if line not in seen:
                                seen.add(line)
                                ordered_candidates.append(line)
                except Exception as e:
                    logger.warning(f"Failed fetching proxies from {source}: {e}")

            candidates = ordered_candidates[:max_check]

            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                results = list(executor.map(self._test_socks5_proxy, candidates))

            valid = [r for r in results if r is not None]
            # Shuffle verified proxies so sequential requests distribute across various geolocations
            random.shuffle(valid)
            return valid

        try:
            valid_proxies = await loop.run_in_executor(None, _worker_fetch_and_check)
            if valid_proxies:
                self.auto_proxies = valid_proxies
                self.last_fetched = time.time()
                logger.info(f"Verified {len(valid_proxies)} live public SOCKS5 proxies for rotating pool.")
            return len(self.auto_proxies)
        finally:
            self.is_fetching = False

    def _test_socks5_proxy(self, proxy_str: str) -> Optional[Dict[str, Any]]:
        clean = proxy_str.replace("socks5://", "").replace("http://", "").strip()
        parts = clean.split(":")
        if len(parts) != 2:
            return None
        ip, port_str = parts[0], parts[1]
        try:
            port = int(port_str)
        except ValueError:
            return None

        t0 = time.time()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.5)
            s.connect((ip, port))
            # SOCKS5 greeting: version 5, 1 auth method, no auth
            s.sendall(b"\x05\x01\x00")
            res = s.recv(2)
            if res == b"\x05\x00":
                # SOCKS5 connect request to 1.1.1.1:80
                s.sendall(b"\x05\x01\x00\x01\x01\x01\x01\x01\x00\x50")
                conn_res = s.recv(10)
                if conn_res and conn_res[1] == 0:
                    latency = round((time.time() - t0) * 1000)
                    s.close()
                    return {
                        "server": f"socks5://{ip}:{port}",
                        "username": None,
                        "password": None,
                        "display": f"{ip}:{port} (SOCKS5)",
                        "latency_ms": latency
                    }
            s.close()
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
