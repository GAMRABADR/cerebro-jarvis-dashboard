# -*- coding: utf-8 -*-
import asyncio
import os
from playwright.async_api import async_playwright

async def run_ui_test():
    os.makedirs('screenshots', exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({'width': 1280, 'height': 850})

        # 1. Load /traslochi
        print('[UI TEST 1] Loading http://127.0.0.1:8088/traslochi ...')
        res = await page.goto('http://127.0.0.1:8088/traslochi', wait_until='domcontentloaded')
        print(f'Status: {res.status}')
        assert res.status == 200

        # Wait for cards to render
        await page.wait_for_selector('.lead-card', timeout=6000)
        cards = await page.query_selector_all('.lead-card')
        print(f'Total lead cards rendered on UI: {len(cards)}')
        assert len(cards) > 0

        # 2. Test City Pill click (Milano)
        print('[UI TEST 2] Filtering by Milano...')
        await page.click('.city-pill:has-text("Milano")')
        await page.wait_for_timeout(500)
        milano_cards = await page.query_selector_all('.lead-card')
        print(f'Milano cards rendered: {len(milano_cards)}')
        assert len(milano_cards) > 0

        # 3. Test Service Pill click (Sgomberi)
        print('[UI TEST 3] Filtering by Sgomberi...')
        await page.click('.city-pill:has-text("TUTTE LE CITTÀ")')
        await page.wait_for_timeout(300)
        await page.click('.service-pill:has-text("Sgomberi")')
        await page.wait_for_timeout(500)
        sgomberi_cards = await page.query_selector_all('.lead-card')
        print(f'Sgomberi cards rendered: {len(sgomberi_cards)}')
        assert len(sgomberi_cards) > 0

        # Reset filters
        await page.click('.service-pill:has-text("TUTTI I SERVIZI")')
        await page.wait_for_timeout(300)

        # 4. Take Screenshot of Cockpit
        screenshot_path = 'screenshots/traslochi_multi_city_cockpit.png'
        await page.screenshot(path=screenshot_path)
        print(f'[UI TEST 4] Saved screenshot to {screenshot_path}')

        await browser.close()
        print('UI TEST COMPLETED SUCCESSFULLY WITH 100% PASS!')

asyncio.run(run_ui_test())
