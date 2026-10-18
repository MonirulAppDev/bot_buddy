import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await ctx.new_page()
        print("Opening reel...")
        await page.goto("https://www.facebook.com/reel/1767246594345288", wait_until="networkidle")
        await asyncio.sleep(2)

        # Try to find close button
        elements = await page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('div[role="button"], i, svg'));
            return btns.map(b => ({
                tag: b.tagName,
                aria: b.getAttribute('aria-label'),
                className: b.className
            })).filter(x => x.aria || (x.className && typeof x.className === 'string' && x.className.includes('close')));
        }""")
        print("Buttons with aria or close:", elements[:10])

        # Try pressing Escape
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        # Try evaluating click on the X circle icon
        closed = await page.evaluate("""() => {
            const closeBtn = document.querySelector('div[aria-label="Close"], [aria-label="close"]');
            if (closeBtn) {
                closeBtn.click();
                return "clicked aria-label Close";
            }
            // Find modal close icon by SVG or circle
            const svgClose = document.querySelector('svg path[d*="18.707"], div[role="dialog"] div[role="button"]');
            if (svgClose) {
                svgClose.click();
                return "clicked svgClose";
            }
            return "not found";
        }""")
        print("Modal close result:", closed)
        await asyncio.sleep(2)
        await page.screenshot(path="backend/app/static/screenshots/reel_after_close_click.png")
        print("Saved reel_after_close_click.png")

        # Now check if video is playing and unmuted
        video_status = await page.evaluate("""() => {
            const v = document.querySelector('video');
            return v ? { paused: v.paused, currentTime: v.currentTime, muted: v.muted } : "no video";
        }""")
        print("Video status:", video_status)
        await browser.close()

asyncio.run(run())
