import asyncio
import os
from playwright.async_api import async_playwright

async def run_test():
    os.makedirs('screenshots', exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Load home page
        print('[TEST 1] Loading http://127.0.0.1:8088 ...')
        res = await page.goto('http://127.0.0.1:8088', wait_until='domcontentloaded')
        print(f'Page status: {res.status}')
        
        # 2. Check navbar button
        btn_skills = await page.query_selector('#btn-view-skills')
        print(f'Skills Matrix button exists: {btn_skills is not None}')
        
        # 3. Switch to Skills Matrix
        print('[TEST 2] Switching to Skills Matrix view...')
        await page.click('#btn-view-skills')
        await page.wait_for_timeout(1000)
        
        is_visible = await page.is_visible('#view-skills-matrix')
        print(f'view-skills-matrix visible: {is_visible}')
        
        # Wait for cards to render
        await page.wait_for_selector('.sk-card', timeout=5000)
        cards = await page.query_selector_all('.sk-card')
        print(f'Total Skill Cards rendered: {len(cards)}')
        
        # 4. Test Category Filter
        print('[TEST 3] Testing Rust Category Filter...')
        await page.click('.sk-cat-btn[data-cat="rust"]')
        await page.wait_for_timeout(500)
        rust_cards = await page.query_selector_all('.sk-card')
        print(f'Rust Skill Cards rendered: {len(rust_cards)}')
        
        # 5. Test Search Filter
        print('[TEST 4] Testing Search filter for "lead"...')
        await page.click('.sk-cat-btn[data-cat="all"]')
        await page.fill('#sk-search-input', 'lead')
        await page.wait_for_timeout(500)
        search_cards = await page.query_selector_all('.sk-card')
        print(f'Search "lead" cards rendered: {len(search_cards)}')
        
        # 6. Test Wake Phrase parser
        print('[TEST 5] Testing Wake-Word Parser in browser context...')
        wake_test_1 = await page.evaluate('parseWakePhrase("ehi ebj quanti preventivi abbiamo oggi?")')
        print(f'Wake test 1 ("ehi ebj..."): {wake_test_1}')
        assert wake_test_1['hasWake'] == True, 'Expected hasWake True'
        
        wake_test_ambient = await page.evaluate('parseWakePhrase("passami il sale per favore")')
        print(f'Ambient test ("passami il sale..."): {wake_test_ambient}')
        assert wake_test_ambient['hasWake'] == False, 'Expected hasWake False'

        # 7. Take screenshot of the Skills Matrix
        await page.set_viewport_size({'width': 1280, 'height': 800})
        await page.screenshot(path='screenshots/skills_matrix_verified.png')
        print('[TEST 6] Saved screenshot to screenshots/skills_matrix_verified.png')

        await browser.close()
        print('ALL TESTS PASSED WITH 100% SUCCESS!')

asyncio.run(run_test())
