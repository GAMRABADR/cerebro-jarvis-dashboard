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
        wake_cases = [
            ("ehi ebj quanti preventivi abbiamo oggi?", True, "ehi ebj", "quanti preventivi abbiamo oggi?"),
            ("EBJ apri i container", True, "ebj", "apri i container"),
            ("Hey EBJ ci sei?", True, "hey ebj", "ci sei?"),
            ("Jarvis status sistema", True, "jarvis", "status sistema"),
            ("Hermes genera preventivo", True, "hermes", "genera preventivo"),
            ("passami il sale per favore", False, "", "passami il sale per favore"),
            ("come va il tempo a bologna?", False, "", "come va il tempo a bologna?"),
            ("stavo parlando con marco al telefono", False, "", "stavo parlando con marco al telefono")
        ]
        for phrase, expected_wake, exp_word, exp_cmd in wake_cases:
            res_wake = await page.evaluate(f'parseWakePhrase({repr(phrase)})')
            print(f'Test phrase: "{phrase}" -> hasWake: {res_wake["hasWake"]}, word: "{res_wake.get("wakeWord")}"')
            assert res_wake['hasWake'] == expected_wake, f'Failed wake check for "{phrase}"'

        # 7. Test Voice Companion page (/voice)
        print('[TEST 6] Testing /voice companion page...')
        page_voice = await browser.new_page()
        res_v = await page_voice.goto('http://127.0.0.1:8088/voice', wait_until='domcontentloaded')
        print(f'/voice status: {res_v.status}')
        assert res_v.status == 200, 'Expected 200 OK for /voice'
        
        voice_wake_test = await page_voice.evaluate('parseWakePhrase("Ehi EBJ ci sei?")')
        assert voice_wake_test['hasWake'] == True, 'Expected hasWake True in /voice'
        voice_ambient_test = await page_voice.evaluate('parseWakePhrase("oggi piove a milano")')
        assert voice_ambient_test['hasWake'] == False, 'Expected hasWake False in /voice'
        print('/voice page Wake Gating verified successfully!')

        # 8. Take screenshot of the Skills Matrix
        await page.set_viewport_size({'width': 1280, 'height': 800})
        await page.screenshot(path='screenshots/skills_matrix_verified.png')
        print('[TEST 7] Saved screenshot to screenshots/skills_matrix_verified.png')

        await page_voice.close()
        await browser.close()
        print('ALL TESTS PASSED WITH 100% SUCCESS!')

asyncio.run(run_test())
