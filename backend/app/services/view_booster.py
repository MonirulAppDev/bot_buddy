import asyncio
import datetime
import logging
import random
from typing import Any, Callable, Dict, List
from playwright.async_api import async_playwright

from app.services.device_pool import get_unique_device_batch, get_device_pool_size

logger = logging.getLogger("view_booster")

ORGANIC_REFERRERS = [
    "https://www.google.com/",
    "https://m.facebook.com/",
    "https://l.facebook.com/",
    "https://t.co/",
    "https://www.bing.com/",
    None
]

# Advanced Anti-Bot Stealth injection to evade Facebook automation detection
STEALTH_SCRIPT = """
(() => {
    // 1. Remove navigator.webdriver flag
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    delete navigator.__proto__.webdriver;

    // 2. Mock Chrome runtime object
    window.chrome = {
        app: { isInstalled: false, InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' } },
        runtime: { PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android' } },
        loadTimes: () => {},
        csi: () => {}
    };

    // 3. Emulate realistic plugins array
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }
        ]
    });

    // 4. Overwrite notification permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
})();
"""


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
    """Execute a single authentic impression with anti-bot evasion and zero device duplication."""
    async with semaphore:
        referrer = random.choice(ORGANIC_REFERRERS)
        dwell_time = round(random.uniform(min_dwell, max_dwell), 1)

        extra_headers = {}
        if referrer:
            extra_headers["Referer"] = referrer
        extra_headers["Accept-Language"] = "en-US,en;q=0.9,bn;q=0.8"

        context = await browser.new_context(
            user_agent=device_profile["user_agent"],
            viewport=device_profile["viewport"],
            device_scale_factor=device_profile.get("device_scale_factor", 2.0),
            is_mobile=device_profile.get("is_mobile", True),
            has_touch=device_profile.get("has_touch", True),
            locale="en-US",
            extra_http_headers=extra_headers
        )

        page = await context.new_page()

        # Inject stealth evasions before page script executes
        await page.add_init_script(STEALTH_SCRIPT)

        try:
            logger.info(f"[View #{view_idx}] {device_profile['name']} visiting {post_url} (Ref: {referrer or 'Direct'})...")
            await page.goto(post_url, wait_until="domcontentloaded", timeout=40000)

            # Human-like initial reading pause
            await asyncio.sleep(random.uniform(2.0, 3.0))

            # Automatically dismiss any login modals / overlays
            try:
                await page.keyboard.press("Escape")
            except Exception:
                pass

            # Simulate video stream playback if on Reel / Video
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
                    logger.info(f"[View #{view_idx}] Triggered video playback on Reel!")
            except Exception:
                pass

            # Natural incremental reading actions during dwell time
            elapsed = 3.0
            scroll_count = 0
            while elapsed < dwell_time:
                step_sleep = min(random.uniform(2.5, 4.0), dwell_time - elapsed)
                await asyncio.sleep(step_sleep)
                elapsed += step_sleep

                # Keep video continuously unpaused if modal tried to stop it
                if is_video:
                    try:
                        await page.evaluate("""() => {
                            const v = document.querySelector('video');
                            if (v && v.paused) {
                                v.muted = true;
                                v.play().catch(() => {});
                            }
                        }""")
                    except Exception:
                        pass

                # Human-like micro scrolls and mouse moves
                scroll_count += 1
                if scroll_count % 2 == 1:
                    await page.mouse.wheel(0, random.randint(120, 300))
                else:
                    await page.mouse.wheel(0, -random.randint(40, 100))

            # Read final video playback progress if available
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
                "referrer": ref_label,
                "dwell_seconds": dwell_time,
                "is_video": is_video,
                "video_streamed_sec": round(video_time, 1) if is_video else 0,
                "status": "SUCCESS",
                "message": f"Watched Reel for {dwell_time}s ({device_profile['name']})",
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }

        except Exception as e:
            logger.warning(f"[View #{view_idx}] Impression failed: {e}")
            return {
                "view_idx": view_idx,
                "device": device_profile["name"],
                "platform": device_profile.get("platform", "Mobile"),
                "viewport": f"{device_profile['viewport']['width']}x{device_profile['viewport']['height']}",
                "referrer": "N/A",
                "dwell_seconds": 0,
                "is_video": False,
                "video_streamed_sec": 0,
                "status": "FAILED",
                "message": str(e)[:100],
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        finally:
            await context.close()


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
        "started_at": datetime.datetime.now().isoformat(),
        "completed_at": None,
        "logs": []
    }
    manager.active_tasks[task_id] = task_record

    # Guarantee unique device batch of size quantity from our 650+ device pool
    device_batch = get_unique_device_batch(quantity)

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
                await asyncio.sleep(random.uniform(0.4, 1.2))

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
