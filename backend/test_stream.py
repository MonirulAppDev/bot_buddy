import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await ctx.new_page()

        telemetry = []
        page.on("request", lambda r: telemetry.append(r.url) if "bz" in r.url or "logging" in r.url else None)

        print("Navigating to reel...")
        await page.goto("https://www.facebook.com/reel/1767246594345288", wait_until="networkidle")
        await asyncio.sleep(2.5)

        cleanup_res = await page.evaluate("""() => {
            let removedCount = 0;
            // 1. Remove dialog modals
            const dialogs = document.querySelectorAll('div[role="dialog"]');
            dialogs.forEach(d => {
                d.remove();
                removedCount++;
            });

            // 2. Remove modal backdrops / overlays
            const overlays = document.querySelectorAll('div.x1n2onr6.x1ja2u2z.x78zum5.x2lah0s.xl56j7k.x6s0dn4.xozqiw3.x1q0g3np');
            overlays.forEach(o => o.remove());

            // 3. Remove aria-hidden attributes
            document.querySelectorAll('[aria-hidden="true"]').forEach(el => el.removeAttribute('aria-hidden'));

            // 4. Ensure video is unpaused and playing
            const v = document.querySelector('video');
            if (v) {
                v.muted = true;
                v.play().catch(() => {});
                return { removedCount, paused: v.paused, currentTime: v.currentTime };
            }
            return { removedCount, error: "no video" };
        }""")
        print("DOM Cleanup result:", cleanup_res)

        # Click the video element directly to trigger user engagement state
        try:
            await page.click("video", timeout=3000)
            print("Successfully clicked video canvas!")
        except Exception as e:
            print("Video click skipped:", e)

        # Let it stream 8 seconds
        await asyncio.sleep(8)

        final_info = await page.evaluate("""() => {
            const v = document.querySelector('video');
            return v ? { paused: v.paused, currentTime: v.currentTime, duration: v.duration } : null;
        }""")
        print("Final video info after 8s:", final_info)
        print("Telemetry requests captured:", len(telemetry))

        await page.screenshot(path="backend/app/static/screenshots/reel_clean_streaming.png")
        print("Saved reel_clean_streaming.png")
        await browser.close()

asyncio.run(run())
