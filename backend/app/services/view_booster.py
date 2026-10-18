import asyncio
import datetime
import logging
import random
from typing import Any, Callable, Dict, List
from playwright.async_api import async_playwright

logger = logging.getLogger("view_booster")

DEVICE_PROFILES = [
    {
        "name": "iPhone 15 Pro (Safari Mobile)",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 393, "height": 852},
        "is_mobile": True
    },
    {
        "name": "Samsung Galaxy S24 (Chrome Mobile)",
        "user_agent": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
        "viewport": {"width": 412, "height": 915},
        "is_mobile": True
    },
    {
        "name": "Google Pixel 8 (Chrome Mobile)",
        "user_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
        "viewport": {"width": 412, "height": 892},
        "is_mobile": True
    },
    {
        "name": "Windows 11 (Chrome Desktop)",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "is_mobile": False
    },
    {
        "name": "MacBook Pro (Safari Desktop)",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "viewport": {"width": 1440, "height": 900},
        "is_mobile": False
    },
    {
        "name": "iPad Pro 12.9 (Safari Tablet)",
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
        "viewport": {"width": 1024, "height": 1366},
        "is_mobile": True
    }
]


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
    min_dwell: float,
    max_dwell: float,
    semaphore: asyncio.Semaphore
) -> Dict[str, Any]:
    """Execute a single high-retention impression with realistic human browsing & referrer behavior."""
    async with semaphore:
        profile = random.choice(DEVICE_PROFILES)
        referrer = random.choice(ORGANIC_REFERRERS)
        dwell_time = round(random.uniform(min_dwell, max_dwell), 1)

        extra_headers = {"Referer": referrer} if referrer else {}

        context = await browser.new_context(
            user_agent=profile["user_agent"],
            viewport=profile["viewport"],
            is_mobile=profile["is_mobile"],
            locale="en-US",
            extra_http_headers=extra_headers
        )
        page = await context.new_page()

        try:
            logger.info(f"[View #{view_idx}] Navigating via {profile['name']} (Ref: {referrer or 'Direct'})...")
            await page.goto(post_url, wait_until="domcontentloaded", timeout=35000)

            # Wait initial render
            await asyncio.sleep(random.uniform(1.5, 2.8))

            # Simulate human behavior: realistic scroll down to content
            scroll_amount = random.randint(200, 480)
            await page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(2.0)

            # Check if video element is present to trigger play for video/reel views
            try:
                video_locator = page.locator("video").first
                if await video_locator.count() > 0 and await video_locator.is_visible():
                    await video_locator.click(timeout=1500)
                    logger.info(f"[View #{view_idx}] Triggered video player element for video view count!")
            except Exception:
                pass

            # Simulate secondary reading scroll
            await page.mouse.wheel(0, random.randint(100, 250))
            
            # Hold dwell time for organic reach & algorithm retention
            remaining_dwell = max(1.5, dwell_time - 5.0)
            await asyncio.sleep(remaining_dwell)

            # Slight scroll adjustment
            await page.mouse.wheel(0, -random.randint(60, 150))
            await asyncio.sleep(0.8)

            ref_label = referrer.replace("https://", "").replace("/", "") if referrer else "Direct/App"

            return {
                "view_idx": view_idx,
                "device": profile["name"],
                "viewport": f"{profile['viewport']['width']}x{profile['viewport']['height']}",
                "referrer": ref_label,
                "dwell_seconds": dwell_time,
                "status": "SUCCESS",
                "message": f"Delivered {dwell_time}s organic impression via {ref_label}",
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }

        except Exception as e:
            logger.warning(f"[View #{view_idx}] Impression failed: {e}")
            return {
                "view_idx": view_idx,
                "device": profile["name"],
                "viewport": f"{profile['viewport']['width']}x{profile['viewport']['height']}",
                "dwell_seconds": 0,
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
    dwell_seconds: float = 6.0,
    concurrency: int = 3,
    on_progress: Callable[[Dict[str, Any]], None] | None = None
) -> Dict[str, Any]:
    """Launch full concurrent view boosting campaign."""
    min_dwell = max(4.0, dwell_seconds - 1.5)
    max_dwell = dwell_seconds + 2.5

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
                # Small staggered delay between starting workers to look organic
                await asyncio.sleep(random.uniform(0.3, 0.9))

                async def worker_wrapper(idx=i):
                    res = await execute_single_view(
                        browser=browser,
                        post_url=post_url,
                        view_idx=idx,
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
    dwell_seconds: float = 6.0,
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

