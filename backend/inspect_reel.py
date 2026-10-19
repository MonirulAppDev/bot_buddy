import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page.goto("https://www.facebook.com/reel/1767246594345288", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Get all text
        body_text = await page.inner_text("body")
        lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        print("Total lines found:", len(lines))
        for l in lines:
            if any(w in l.lower() for w in ["view", "play", "monirul", "like", "share", "comment"]):
                print("Line:", l)

        await page.screenshot(path="backend/app/static/screenshots/reel_live_count.png")
        print("Screenshot saved to backend/app/static/screenshots/reel_live_count.png")
        await browser.close()

asyncio.run(main())
