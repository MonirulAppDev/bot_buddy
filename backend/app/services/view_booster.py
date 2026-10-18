import asyncio
import datetime
import logging
import random
from typing import Any, Callable, Dict, List
from playwright.async_api import async_playwright

from app.services.device_pool import get_unique_device_batch, get_device_pool_size
from app.services.proxy_manager import proxy_manager
from app.services.stealth import build_stealth_injection_script, generate_wifi_profile

logger = logging.getLogger("view_booster")

ORGANIC_REFERRERS = [
    "https://www.google.com/",
    "https://m.facebook.com/",
    "https://l.facebook.com/",
    "https://t.co/",
    "https://www.bing.com/",
    None
]


class ViewBoosterManager:
    """Manages active view boosting sessions with live progress tracking."""
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def get_task(self, task_id: str) -> Dict[str, Any] | None:
        return self.active_tasks.get(task_id)


manager = ViewBoosterManager()


async def execute_single_view(
    browser,
    post_url: str,
    view_idx: int,
    device_profile: Dict[str, Any],
    min_dwell: float,
    max_dwell: float,
    semaphore: asyncio.Semaphore
) -> Dict[str, Any]:
    """Execute a single authentic impression with 100% unique device hardware, rotating IPv4 proxy, and simulated WiFi identity."""
    async with semaphore:
        referrer = random.choice(ORGANIC_REFERRERS)
        dwell_time = round(random.uniform(min_dwell, max_dwell), 1)

        # Generate unique simulated WiFi & Network parameters
        wifi_profile = generate_wifi_profile(view_idx)

        # Dynamic stealth injection script with WebRTC protection, Canvas entropy, GPU & Battery spoofing
        stealth_script = build_stealth_injection_script(device_profile, wifi_profile, view_idx)

        extra_headers = {}
        if referrer:
            extra_headers["Referer"] = referrer
        extra_headers["Accept-Language"] = "en-US,en;q=0.9,bn;q=0.8"

        proxy_cfg = proxy_manager.get_proxy_for_view(view_idx)
        proxy_display = proxy_cfg["display"] if proxy_cfg else "Direct (Stealth)"

        async def _attempt(use_proxy: bool) -> Dict[str, Any]:
            context_kwargs: Dict[str, Any] = {
                "user_agent": device_profile["user_agent"],
                "viewport": device_profile["viewport"],
                "device_scale_factor": device_profile.get("device_scale_factor", 2.0),
                "is_mobile": device_profile.get("is_mobile", True),
                "has_touch": device_profile.get("has_touch", True),
                "locale": "en-US",
                "extra_http_headers": extra_headers
            }
            if use_proxy and proxy_cfg:
                p_arg: Dict[str, str] = {"server": proxy_cfg["server"]}
                if proxy_cfg.get("username"):
                    p_arg["username"] = proxy_cfg["username"]
                if proxy_cfg.get("password"):
                    p_arg["password"] = proxy_cfg["password"]
                context_kwargs["proxy"] = p_arg

            current_ip = proxy_display if use_proxy else "Direct (Stealth)"
            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()

            # Inject full deep hardware and WiFi stealth before any page JavaScript executes
            await page.add_init_script(stealth_script)

            try:
                logger.info(
                    f"[View #{view_idx}] {device_profile['name']} visiting {post_url} "
                    f"[IP: {current_ip} | WiFi: {wifi_profile['local_ipv4']} | GPU: {device_profile.get('webgl_renderer')} | Ref: {referrer or 'Direct'}]..."
                )
                await page.goto(post_url, wait_until="domcontentloaded", timeout=35000)

                # Human-like initial pause
                await asyncio.sleep(random.uniform(2.0, 3.0))

                # Dismiss login popups / modals
                # Comprehensive login popup & backdrop removal
                try:
                    await page.keyboard.press("Escape")
                    await page.evaluate("""() => {
                        // Remove modal dialogs and dark overlays completely
                        document.querySelectorAll('div[role="dialog"]').forEach(d => d.remove());
                        document.querySelectorAll('div.__fb-light-mode').forEach(d => d.style.pointerEvents = 'none');
                        document.querySelectorAll('[aria-hidden="true"]').forEach(el => el.removeAttribute('aria-hidden'));
                    }""")
                except Exception:
                    pass

                # Simulate unobscured video stream playback
                is_video = False
                video_time = 0.0
                try:
                    video_res = await page.evaluate("""() => {
                        const v = document.querySelector('video');
                        if (v) {
                            v.muted = true;
                            v.play().catch(() => {});
                            return true;
                        }
                        return false;
                    }""")
                    if video_res:
                        is_video = True
                except Exception:
                    pass

                # Natural reading & watch loop
                elapsed = 3.0
                scroll_count = 0
                while elapsed < dwell_time:
                    step_sleep = min(random.uniform(2.5, 4.0), dwell_time - elapsed)
                    await asyncio.sleep(step_sleep)
                    elapsed += step_sleep

                    if is_video:
                        try:
                            await page.evaluate("""() => {
                                const dialog = document.querySelector('div[role="dialog"]');
                                if (dialog) dialog.remove();
                                const v = document.querySelector('video');
                                if (v && v.paused) {
                                    v.muted = true;
                                    v.play().catch(() => {});
                                }
                            }""")
                        except Exception:
                            pass

                    # Human scroll jitters
                    scroll_count += 1
                    if scroll_count % 2 == 1:
                        await page.mouse.wheel(0, random.randint(120, 280))
                    else:
                        await page.mouse.wheel(0, -random.randint(40, 90))

                if is_video:
                    try:
                        video_time = await page.evaluate("() => { const v = document.querySelector('video'); return v ? v.currentTime : 0; }")
                    except Exception:
                        video_time = dwell_time

                ref_label = referrer.replace("https://", "").replace("/", "") if referrer else "Direct/App"

                return {
                    "view_idx": view_idx,
                    "device": device_profile["name"],
                    "platform": device_profile.get("platform", "Mobile"),
                    "viewport": f"{device_profile['viewport']['width']}x{device_profile['viewport']['height']}",
                    "proxy": current_ip,
                    "wifi_ip": wifi_profile["local_ipv4"],
                    "wifi_mac": wifi_profile["mac_address"],
                    "wifi_ssid": wifi_profile["ssid"],
                    "webgl_gpu": device_profile.get("webgl_renderer", "Generic GPU"),
                    "cores_ram": f"{device_profile.get('hardware_concurrency', 8)}C / {device_profile.get('device_memory', 8)}GB",
                    "referrer": ref_label,
                    "dwell_seconds": dwell_time,
                    "is_video": is_video,
                    "video_streamed_sec": round(video_time, 1) if is_video else 0,
                    "status": "SUCCESS",
                    "message": f"Watched Reel for {dwell_time}s ({device_profile['name']}) [IP: {current_ip} | WiFi: {wifi_profile['local_ipv4']}]",
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                }
            finally:
                await context.close()

        # Try with assigned rotating proxy; if network error, fallback to direct stealth so view is never lost
        try:
            return await _attempt(use_proxy=bool(proxy_cfg))
        except Exception as e:
            if proxy_cfg:
                logger.warning(f"[View #{view_idx}] Proxy {proxy_display} error: {e}. Falling back to direct stealth connection...")
                try:
                    return await _attempt(use_proxy=False)
                except Exception as ex2:
                    logger.error(f"[View #{view_idx}] Impression failed: {ex2}")
                    return {
                        "view_idx": view_idx,
                        "device": device_profile["name"],
                        "platform": device_profile.get("platform", "Mobile"),
                        "viewport": f"{device_profile['viewport']['width']}x{device_profile['viewport']['height']}",
                        "proxy": f"{proxy_display} (Failed)",
                        "wifi_ip": wifi_profile["local_ipv4"],
                        "wifi_mac": wifi_profile["mac_address"],
                        "wifi_ssid": wifi_profile["ssid"],
                        "webgl_gpu": device_profile.get("webgl_renderer", "Generic GPU"),
                        "cores_ram": f"{device_profile.get('hardware_concurrency', 8)}C / {device_profile.get('device_memory', 8)}GB",
                        "referrer": "N/A",
                        "dwell_seconds": 0,
                        "is_video": False,
                        "video_streamed_sec": 0,
                        "status": "FAILED",
                        "message": str(ex2)[:100],
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                    }
            else:
                logger.warning(f"[View #{view_idx}] Impression failed: {e}")
                return {
                    "view_idx": view_idx,
                    "device": device_profile["name"],
                    "platform": device_profile.get("platform", "Mobile"),
                    "viewport": f"{device_profile['viewport']['width']}x{device_profile['viewport']['height']}",
                    "proxy": "Direct (Stealth)",
                    "wifi_ip": wifi_profile["local_ipv4"],
                    "wifi_mac": wifi_profile["mac_address"],
                    "wifi_ssid": wifi_profile["ssid"],
                    "webgl_gpu": device_profile.get("webgl_renderer", "Generic GPU"),
                    "cores_ram": f"{device_profile.get('hardware_concurrency', 8)}C / {device_profile.get('device_memory', 8)}GB",
                    "referrer": "N/A",
                    "dwell_seconds": 0,
                    "is_video": False,
                    "video_streamed_sec": 0,
                    "status": "FAILED",
                    "message": str(e)[:100],
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                }


async def run_view_booster_campaign(
    task_id: str,
    post_url: str,
    quantity: int,
    dwell_seconds: float = 12.0,
    concurrency: int = 3,
    on_progress: Callable[[Dict[str, Any]], None] | None = None
) -> Dict[str, Any]:
    """Launch full concurrent view boosting campaign using unique device fingerprints with zero redundancy."""
    min_dwell = max(5.0, dwell_seconds - 2.5)
    max_dwell = dwell_seconds + 3.0

    task_record = {
        "task_id": task_id,
        "target_url": post_url,
        "total_requested": quantity,
        "delivered": 0,
        "failed": 0,
        "status": "RUNNING",
        "proxy_mode": proxy_manager.mode,
        "active_proxies": len(proxy_manager.custom_proxies) if proxy_manager.mode == "custom" else len(proxy_manager.auto_proxies),
        "started_at": datetime.datetime.now().isoformat(),
        "completed_at": None,
        "logs": []
    }
    manager.active_tasks[task_id] = task_record

    # Guarantee unique device batch of size quantity from our 650+ device pool
    device_batch = get_unique_device_batch(quantity)

    # Ensure proxy pool is primed if auto mode is on and auto_proxies is empty
    if proxy_manager.mode == "auto" and len(proxy_manager.auto_proxies) < 15:
        logger.info("Initializing public rotating proxy pool before campaign launch...")
        try:
            await proxy_manager.refresh_public_proxies(max_check=300)
            task_record["active_proxies"] = len(proxy_manager.auto_proxies)
        except Exception as e:
            logger.warning(f"Could not prime proxy pool: {e}")

    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars"
            ]
        )

        try:
            tasks = []
            for i in range(1, quantity + 1):
                device = device_batch[i - 1]
                # Stagger worker launches slightly
                await asyncio.sleep(random.uniform(0.4, 1.0))

                async def worker_wrapper(idx=i, dev=device):
                    res = await execute_single_view(
                        browser=browser,
                        post_url=post_url,
                        view_idx=idx,
                        device_profile=dev,
                        min_dwell=min_dwell,
                        max_dwell=max_dwell,
                        semaphore=semaphore
                    )
                    if res["status"] == "SUCCESS":
                        task_record["delivered"] += 1
                    else:
                        task_record["failed"] += 1

                    task_record["logs"].append(res)
                    if on_progress:
                        try:
                            on_progress(task_record)
                        except Exception:
                            pass

                tasks.append(asyncio.create_task(worker_wrapper()))

            await asyncio.gather(*tasks)

        finally:
            await browser.close()

    task_record["status"] = "COMPLETED"
    task_record["completed_at"] = datetime.datetime.now().isoformat()
    return task_record


def run_campaign_in_thread(
    task_id: str,
    post_url: str,
    quantity: int,
    dwell_seconds: float = 12.0,
    concurrency: int = 3
) -> Dict[str, Any]:
    """Runs the Playwright campaign inside a ProactorEventLoop thread on Windows."""
    import sys
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            run_view_booster_campaign(
                task_id=task_id,
                post_url=post_url,
                quantity=quantity,
                dwell_seconds=dwell_seconds,
                concurrency=concurrency
            )
        )
    finally:
        loop.close()
