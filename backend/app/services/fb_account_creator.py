import asyncio
import logging
import random
import uuid
from faker import Faker
from playwright.async_api import async_playwright

logger = logging.getLogger("fb_account_creator")


async def attempt_fb_registration(headless: bool = False) -> dict:
    """Automated Facebook account registration bot attempt using Playwright.
    Fills out realistic random name, birthdate, password, and email.
    Note: Facebook will prompt for SMS verification / Captcha.
    """
    fake = Faker("en_US")
    first_name = fake.first_name()
    last_name = fake.last_name()
    # Random realistic birth date between 1992 and 2002
    birth_year = str(random.randint(1992, 2002))
    birth_month = str(random.randint(1, 12))
    birth_day = str(random.randint(1, 28))
    password = f"BotBuddy@{uuid.uuid4().hex[:6]}!"
    fake_email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(100, 9999)}@gmail.com"

    logger.info(f"Attempting to register bot account: {first_name} {last_name}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        try:
            # Navigate to Facebook registration
            await page.goto("https://www.facebook.com/r.php", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2)

            # Accept cookies if prompt appears
            try:
                cookie_btn = page.locator('button:has-text("Allow all cookies"), button:has-text("Only allow essential cookies")').first
                if await cookie_btn.count() > 0:
                    await cookie_btn.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # Fill First Name & Last Name
            if await page.locator('input[name="firstname"]').count() > 0:
                await page.fill('input[name="firstname"]', first_name)
                await asyncio.sleep(0.5)
                await page.fill('input[name="lastname"]', last_name)
                await asyncio.sleep(0.5)

            # Fill Birthday
            if await page.locator('select[name="birthday_day"]').count() > 0:
                await page.select_option('select[name="birthday_day"]', birth_day)
                await page.select_option('select[name="birthday_month"]', birth_month)
                await page.select_option('select[name="birthday_year"]', birth_year)
                await asyncio.sleep(0.5)

            # Select Gender (1: Female, 2: Male)
            gender_val = str(random.choice([1, 2]))
            gender_radio = page.locator(f'input[name="sex"][value="{gender_val}"]')
            if await gender_radio.count() > 0:
                await gender_radio.click()
                await asyncio.sleep(0.5)

            # Fill Email
            if await page.locator('input[name="reg_email__"]').count() > 0:
                await page.fill('input[name="reg_email__"]', fake_email)
                await asyncio.sleep(0.5)
                # Confirmation email field if appears
                if await page.locator('input[name="reg_email_confirmation__"]').count() > 0:
                    await page.fill('input[name="reg_email_confirmation__"]', fake_email)
                    await asyncio.sleep(0.5)

            # Fill Password
            if await page.locator('input[name="reg_passwd__"]').count() > 0:
                await page.fill('input[name="reg_passwd__"]', password)
                await asyncio.sleep(1)

            # Click Sign Up button
            signup_btn = page.locator('button[name="websubmit"]')
            if await signup_btn.count() > 0:
                await signup_btn.click()
                await asyncio.sleep(5)

            # Take screenshot of the outcome
            screenshot_path = "app/static/screenshots/last_reg_attempt.png"
            await page.screenshot(path=screenshot_path)

            cookies = await context.cookies()
            c_user = next((c for c in cookies if c["name"] == "c_user"), None)

            await browser.close()

            if c_user:
                return {
                    "success": True,
                    "c_user": c_user["value"],
                    "account_name": f"{first_name} {last_name}",
                    "message": "Account registered and session cookie captured!"
                }
            else:
                return {
                    "success": False,
                    "account_name": f"{first_name} {last_name}",
                    "screenshot": "/static/screenshots/last_reg_attempt.png",
                    "reason": "Facebook demanded SMS OTP / Phone verification / Captcha as expected by its security firewall."
                }

        except Exception as e:
            await browser.close()
            return {"success": False, "error": str(e)}
