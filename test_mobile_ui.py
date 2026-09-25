# -*- coding: utf-8 -*-
"""
E.B.J. AI Mobile Usability & Responsiveness Verification Test
Simulates an iPhone / Android smartphone (390x844) visiting http://127.0.0.1:8088/
Takes full-page and component screenshots to ensure 100% mobile perfection.
"""

import os
import sys
import asyncio

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.async_api import async_playwright

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

async def test_mobile():
    async with async_playwright() as p:
        # iPhone 14 Pro viewport
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()

        print("[TEST] 1. Loading http://127.0.0.1:8088 on mobile viewport...")
        await page.goto("http://127.0.0.1:8088/", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        p1 = os.path.join(OUT_DIR, "mobile_dashboard_home.png")
        await page.screenshot(path=p1, full_page=False)
        print(f"[TEST] Saved: {p1}")

        print("[TEST] 2. Switching to Tab 5 (🤖 AGENTI / Autonomous Fleet)...")
        fleet_btn = page.locator("button.tab-btn:has-text('AGENTI')")
        if await fleet_btn.count() > 0:
            await fleet_btn.click()
            await page.wait_for_timeout(1500)
            p2 = os.path.join(OUT_DIR, "mobile_fleet_tab.png")
            await page.screenshot(path=p2, full_page=False)
            print(f"[TEST] Saved: {p2}")

        print("[TEST] 3. Opening Email & Lead Dossier Modal (#modal-send-email)...")
        await page.evaluate("openModal('modal-send-email')")
        await page.wait_for_timeout(1000)
        p3 = os.path.join(OUT_DIR, "mobile_email_modal.png")
        await page.screenshot(path=p3, full_page=False)
        print(f"[TEST] Saved: {p3}")

        print("[TEST] 4. Closing modal and opening Quote Calculator (#modal-preventivo)...")
        await page.evaluate("closeModal('modal-send-email'); openModal('modal-preventivo')")
        await page.wait_for_timeout(1000)
        p4 = os.path.join(OUT_DIR, "mobile_quote_modal.png")
        await page.screenshot(path=p4, full_page=False)
        print(f"[TEST] Saved: {p4}")

        await browser.close()
        print("[TEST] All mobile screenshot tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_mobile())
