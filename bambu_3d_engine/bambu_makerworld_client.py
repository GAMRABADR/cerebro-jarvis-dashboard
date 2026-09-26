"""
Bambu 3D Engine - Bambu Lab MakerWorld Cloud Client
Author: E.B.J. AI Supreme for Ing. Badr
Manages MakerWorld authentication, draft creation, and cloud sync using user session cookies.
"""

import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

COOKIES_VAULT = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\bambu_auth_cookies.json"
MODEL_3MF = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\public\3d_models\HTVW_281_BambuLab.3mf"
RENDERS_DIR = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\public\3d_models\renders"

def get_auth_cookies():
    if not os.path.exists(COOKIES_VAULT):
        raise FileNotFoundError(f"Vault cookies non trovato: {COOKIES_VAULT}")
        
    with open(COOKIES_VAULT, "r", encoding="utf-8") as f:
        raw_cookies = json.load(f)
        
    pw_cookies = []
    for c in raw_cookies:
        item = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".bambulab.com"),
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", True)
        }
        same_site = c.get("sameSite", "Lax")
        if same_site and same_site.lower() in ["none", "lax", "strict"]:
            item["sameSite"] = same_site.capitalize()
        pw_cookies.append(item)
        
        # Mirror for .makerworld.com domain
        if "bambulab.com" in item["domain"]:
            c2 = dict(item)
            c2["domain"] = ".makerworld.com"
            pw_cookies.append(c2)
            
    return pw_cookies

def verify_makerworld_session():
    """Verifica lo stato della sessione MakerWorld con i cookie correnti."""
    print("[*] Connessione a Bambu Lab MakerWorld con credenziali vault...")
    pw_cookies = get_auth_cookies()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900}
        )
        context.add_cookies(pw_cookies)
        page = context.new_page()
        
        try:
            page.goto("https://makerworld.com/it", timeout=25000, wait_until="domcontentloaded")
            time.sleep(3)
            
            title = page.title()
            current_url = page.url
            print(f"[+] MakerWorld aperto con successo: {title}")
            print(f"[+] URL di sessione: {current_url}")
            
            # Check for user avatar / logged in indicator
            is_logged_in = page.evaluate("""() => {
                return !!document.querySelector('.avatar, [data-testid="user-avatar"], .user-profile, a[href*="/my/"]');
            }""")
            
            screenshot_path = os.path.join(RENDERS_DIR, "makerworld_session_live.png")
            page.screenshot(path=screenshot_path)
            print(f"[+] Screenshot di sessione salvato: {screenshot_path}")
            
            browser.close()
            return {
                "success": True,
                "title": title,
                "url": current_url,
                "screenshot": screenshot_path,
                "authenticated": is_logged_in
            }
        except Exception as e:
            print(f"[!] Errore verifica sessione: {e}")
            browser.close()
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    res = verify_makerworld_session()
    print(json.dumps(res, indent=2))
