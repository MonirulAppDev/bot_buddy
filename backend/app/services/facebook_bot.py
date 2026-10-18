import asyncio
import os
import re
import uuid
import logging
from typing import Any

logger = logging.getLogger("facebook_bot")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def parse_cookie_string(cookie_str: str) -> list[dict[str, Any]]:
    """Parse standard cookie header string into Playwright cookie objects."""
    cookies = []
    pairs = cookie_str.split(";")
    for pair in pairs:
        if "=" in pair:
            key, val = pair.strip().split("=", 1)
            cookies.append({
                "name": key.strip(),
                "value": val.strip(),
                "domain": ".facebook.com",
                "path": "/"
            })
    return cookies


async def execute_real_facebook_like(
    post_url: str,
    cookie_str: str,
    headless: bool = True,
    screenshot_dir: str = "app/static/screenshots"
) -> dict[str, Any]:
    """Launch Playwright, inject Facebook session cookies, navigate to post, and click real Like button."""
    from playwright.async_api import async_playwright

    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_name = f"like_{uuid.uuid4().hex[:8]}.png"
    screenshot_path = os.path.join(screenshot_dir, screenshot_name)

    cookies = parse_cookie_string(cookie_str)
    if not cookies:
        return {"success": False, "error": "No valid cookies found in cookie string"}

    has_c_user = any(c["name"] == "c_user" for c in cookies)
    if not has_c_user:
        return {
            "success": False,
            "error": "Cookie string must contain 'c_user' (Facebook User ID) and 'xs' (session token)."
        }

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ]
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        await context.add_cookies(cookies)

        page = await context.new_page()

        try:
            logger.info(f"Navigating to real Facebook URL: {post_url}")
            await page.goto(post_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3)

            # Check if redirected to login / checkpoint
            current_url = page.url
            if "login" in current_url or "checkpoint" in current_url:
                await page.screenshot(path=screenshot_path)
                await browser.close()
                return {
                    "success": False,
                    "error": "Facebook session expired or checkpoint required. Please update cookies.",
                    "screenshot": f"/static/screenshots/{screenshot_name}"
                }

            # Selectors for Facebook Like button on photos/posts
            like_selectors = [
                'div[aria-label="Like"][role="button"]',
                'div[aria-label="like"][role="button"]',
                'div[aria-label="Like"][tabindex="0"]',
                'div[aria-label="Like, Love, Care, Haha, Wow, Sad, Angry"][role="button"]',
                'span:has-text("Like")',
                'div[role="button"]:has-text("Like")'
            ]

            button_found = False
            for sel in like_selectors:
                elem = page.locator(sel).first
                if await elem.count() > 0 and await elem.is_visible():
                    # Check if already liked
                    aria_pressed = await elem.get_attribute("aria-pressed")
                    if aria_pressed == "true":
                        logger.info("Post was already liked by this account.")
                        await page.screenshot(path=screenshot_path)
                        await browser.close()
                        return {
                            "success": True,
                            "already_liked": True,
                            "message": "Already liked by this account",
                            "screenshot": f"/static/screenshots/{screenshot_name}"
                        }

                    logger.info(f"Clicking like button using selector: {sel}")
                    await elem.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    await elem.click()
                    button_found = True
                    break

            if not button_found:
                # Fallback: search for Like button in viewport
                await page.screenshot(path=screenshot_path)
                await browser.close()
                return {
                    "success": False,
                    "error": "Like button not found or post might be private/restricted.",
                    "screenshot": f"/static/screenshots/{screenshot_name}"
                }

            # Wait to ensure reaction is registered
            await asyncio.sleep(2)
            await page.screenshot(path=screenshot_path)
            await browser.close()

            return {
                "success": True,
                "message": "Successfully clicked Like on Facebook!",
                "screenshot": f"/static/screenshots/{screenshot_name}"
            }

        except Exception as e:
            logger.error(f"Error during Facebook like automation: {e}")
            try:
                await page.screenshot(path=screenshot_path)
            except Exception:
                pass
            await browser.close()
            return {
                "success": False,
                "error": str(e),
                "screenshot": f"/static/screenshots/{screenshot_name}" if os.path.exists(screenshot_path) else None
            }
