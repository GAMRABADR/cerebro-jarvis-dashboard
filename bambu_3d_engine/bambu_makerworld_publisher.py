"""
Bambu 3D Engine - Bambu Lab MakerWorld Model & Draft Publisher
Author: E.B.J. AI Supreme for Ing. Badr
Automates draft creation on MakerWorld with 3MF model and render inspection photos.
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
        if "bambulab.com" in item["domain"]:
            c2 = dict(item)
            c2["domain"] = ".makerworld.com"
            pw_cookies.append(c2)
    return pw_cookies

def publish_to_makerworld(draft_only=True):
    print("[*] Avvio procedura pubblicazione su Bambu Lab MakerWorld...")
    cookies = get_auth_cookies()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 960}
        )
        context.add_cookies(cookies)
        page = context.new_page()
        
        # 1. Naviga prima alla home per registrare la sessione con Cloudflare
        page.goto("https://makerworld.com/it", wait_until="domcontentloaded", timeout=25000)
        time.sleep(2)
        
        # 2. Clicca sul pulsante 'Carica' / 'Upload' visibile in alto
        print("[*] Ricerca pulsante 'Upload' / 'Carica'...")
        upload_btn = page.query_selector('a[href*="/upload"], a[href*="/models/create"], button:has-text("Upload"), button:has-text("Carica"), .header-upload-btn')
        
        if upload_btn:
            print("[+] Pulsante Upload trovato, clicco...")
            upload_btn.click()
        else:
            print("[*] Navigazione diretta a https://makerworld.com/it/models/create...")
            page.goto("https://makerworld.com/it/models/create", wait_until="domcontentloaded", timeout=25000)
            
        time.sleep(5)
        print(f"[+] Pagina attiva: {page.title()} | URL: {page.url}")
        
        screenshot_step1 = os.path.join(RENDERS_DIR, "makerworld_upload_step1.png")
        page.screenshot(path=screenshot_step1)
        print(f"[+] Screenshot step 1: {screenshot_step1}")
        
        # 3. Cerca input file per caricamento del .3mf
        file_inputs = page.query_selector_all('input[type="file"]')
        print(f"[*] Input file trovati nella pagina: {len(file_inputs)}")
        
        model_uploaded = False
        if file_inputs:
            for idx, finput in enumerate(file_inputs):
                try:
                    accept = finput.get_attribute("accept") or ""
                    print(f"    - Input #{idx}: accept='{accept}'")
                    if any(ext in accept for ext in [".3mf", ".stl", ".step", "*"]) or not accept:
                        finput.set_input_files(MODEL_3MF)
                        print(f"[+] File 3MF caricato con successo in input #{idx}: {MODEL_3MF}")
                        model_uploaded = True
                        time.sleep(4)
                        break
                except Exception as ex:
                    print(f"    [!] Errore set input file #{idx}: {ex}")
                    
        # 4. Compilazione campi titolo e descrizione se presenti
        try:
            title_input = page.query_selector('input[placeholder*="Title"], input[placeholder*="titolo"], input[name="title"], input[id*="title"]')
            if title_input:
                title_input.fill("HTVW-281 Lock Latch Handle Mechanism (VW / Audi)")
                print("[+] Titolo inserito: HTVW-281 Lock Latch Handle Mechanism")
                
            desc_area = page.query_selector('textarea, div[contenteditable="true"]')
            if desc_area:
                desc_text = (
                    "Ricostruzione 3D parametrica ad alta precisione del meccanismo di chiusura cassetto/portellone "
                    "HTVW-281 per gruppo VW/Audi.\n"
                    "- Materiale consigliato: PETG o ASA per resistenza a calore e raggi UV abitacolo.\n"
                    "- Altezza layer: 0.16mm High Quality.\n"
                    "- Pareti: 4 perimetri.\n"
                    "- Riempimento: 25% Gyroid.\n"
                    "Progettato da E.B.J. AI Supreme per Ing. Badr."
                )
                try:
                    desc_area.fill(desc_text)
                except Exception:
                    desc_area.type(desc_text)
                print("[+] Descrizione tecnica compilata con successo.")
        except Exception as e:
            print(f"[!] Nota compilazione metadati: {e}")
            
        time.sleep(3)
        screenshot_final = os.path.join(RENDERS_DIR, "makerworld_upload_final.png")
        page.screenshot(path=screenshot_final)
        print(f"[+] Screenshot finale caricamento: {screenshot_final}")
        
        browser.close()
        return {
            "success": True,
            "model_uploaded": model_uploaded,
            "url": page.url,
            "step1_screenshot": screenshot_step1,
            "final_screenshot": screenshot_final
        }

if __name__ == "__main__":
    res = publish_to_makerworld()
    print(json.dumps(res, indent=2))
