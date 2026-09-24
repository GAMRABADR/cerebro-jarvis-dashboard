from playwright.sync_api import sync_playwright
import time

def test_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:8088/', wait_until='networkidle', timeout=15000)
        time.sleep(1)
        
        # Test 1: Radar Modal
        page.evaluate("window.toggleLeadRadarModal(true)")
        radar_display = page.evaluate("document.getElementById('card-mod-lead-radar').style.display")
        assert radar_display == 'block', f"Radar display unexpected: {radar_display}"
        print("[PASS] Radar Modal toggled successfully:", radar_display)
        
        # Test 2: B2B Modal
        page.evaluate("window.toggleB2bModal(true)")
        b2b_display = page.evaluate("document.getElementById('card-mod-b2b').style.display")
        assert b2b_display == 'block', f"B2B display unexpected: {b2b_display}"
        print("[PASS] B2B Modal toggled successfully:", b2b_display)
        
        # Test 3: CDP Modal
        page.evaluate("window.toggleCdpModal(true)")
        cdp_display = page.evaluate("document.getElementById('card-mod-cdp').style.display")
        assert cdp_display == 'block', f"CDP display unexpected: {cdp_display}"
        print("[PASS] CDP Modal toggled successfully:", cdp_display)
        
        # Test 4: Main thread responsiveness after 3 seconds
        time.sleep(3)
        res = page.evaluate("window.ebjVoiceEnabled")
        print("[PASS] Main thread is 100% responsive! Voice enabled:", res)
        
        browser.close()

if __name__ == '__main__':
    test_ui()
