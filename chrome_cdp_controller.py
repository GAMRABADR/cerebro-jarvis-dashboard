# ── chrome_cdp_controller.py ──────────────────────────────────────────
#  E.B.J. AI — Chrome CDP Controller & Web Automation Suite
#  Controlla Google Chrome nativo tramite Chrome DevTools Protocol (CDP)
#  su porta 9222 con Playwright per bypassare Cloudflare, Turnstile,
#  DataDome e compilare automaticamente moduli su portali e immobiliari.
# ────────────────────────────────────────────────────────────────────────

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"

# Percorsi standard Google Chrome su Windows
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
]

DEFAULT_USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".ebj_chrome_cdp_profile")

def find_chrome_binary():
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None

def is_cdp_running():
    """Verifica se l'endpoint CDP su porta 9222 è attivo e risponde."""
    try:
        req = urllib.request.Request(f"{CDP_URL}/json/version", headers={"User-Agent": "EBJ-CDP-Checker"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return True, data
    except Exception as e:
        return False, str(e)

def launch_chrome_with_cdp(headless=False, target_url="https://eb.badrexpress.com"):
    """
    Avvia Google Chrome con Remote Debugging attivo sulla porta 9222.
    Se è già avviato, ritorna lo stato attuale.
    """
    running, info = is_cdp_running()
    if running:
        return {"status": "ALREADY_RUNNING", "cdp_url": CDP_URL, "version_info": info}

    chrome_bin = find_chrome_binary()
    if not chrome_bin:
        return {"status": "ERROR", "message": "Google Chrome non trovato nei percorsi di sistema."}

    os.makedirs(DEFAULT_USER_DATA_DIR, exist_ok=True)

    cmd = [
        chrome_bin,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={DEFAULT_USER_DATA_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        target_url
    ]
    if headless:
        cmd.append("--headless=new")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Attesa avvio CDP (max 6 secondi)
        for _ in range(12):
            time.sleep(0.5)
            up, data = is_cdp_running()
            if up:
                return {
                    "status": "LAUNCHED",
                    "pid": proc.pid,
                    "cdp_url": CDP_URL,
                    "version_info": data
                }
        return {"status": "TIMEOUT", "message": "Chrome avviato ma CDP non ha risposto entro 6 secondi."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def get_open_tabs():
    """Elenca le schede aperte nel browser Chrome tramite CDP."""
    try:
        req = urllib.request.Request(f"{CDP_URL}/json/list", headers={"User-Agent": "EBJ-CDP-Checker"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            tabs = json.loads(resp.read().decode("utf-8"))
            pages = [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "url": t.get("url"),
                    "type": t.get("type")
                }
                for t in tabs if t.get("type") == "page"
            ]
            return {"status": "SUCCESS", "count": len(pages), "tabs": pages}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def execute_cdp_action(url, js_script=None, wait_selector=None, action_type="navigate"):
    """
    Connette Playwright via CDP, naviga sull'URL indicato o inietta codice JS
    nella pagina autenticata dell'utente.
    """
    running, _ = is_cdp_running()
    if not running:
        # Tenta auto-lancio di Chrome
        launch_res = launch_chrome_with_cdp(headless=False, target_url=url)
        if launch_res.get("status") not in ["LAUNCHED", "ALREADY_RUNNING"]:
            return {"status": "ERROR", "message": f"Impossibile collegarsi a CDP: {launch_res.get('message')}"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP_URL)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            
            # Trova pagina esistente o aprine una nuova
            pages = context.pages
            page = None
            for pg in pages:
                if url in pg.url:
                    page = pg
                    break
            if not page:
                page = context.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")

            result_data = {"status": "SUCCESS", "current_url": page.url, "title": page.title()}

            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=5000)
                except Exception:
                    result_data["selector_found"] = False

            if js_script:
                eval_res = page.evaluate(js_script)
                result_data["eval_result"] = eval_res

            return result_data
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def fill_agency_portal_contact(portal_url, agency_name, custom_message=None):
    """
    Compila automaticamente il form di contatto di un'agenzia immobiliare o portale
    usando l'identità ufficiale dell'Ing. Badr e PietroTraslochi.
    """
    badr_data = {
        "name": "Badr El Ouariti",
        "company": "BadrExpress & PietroTraslochi",
        "phone": "3888703508",
        "email": "badraudi@gmail.com",
        "website": "https://badrexpress.com",
        "message": custom_message or (
            f"Gentile {agency_name},\n\n"
            f"Siamo PietroTraslochi & BadrExpress, partner specializzati a Bologna e provincia per lo sgombero rapido di appartamenti prima del rogito notarile.\n"
            f"Offriamo convenzione dedicata con sconto 15% per i vostri clienti e retrocessione provvigionale del 10% per la vostra agenzia.\n\n"
            f"Recapito diretto: 388 870 3508 - Pietro: 328 426 3554\n"
            f"Sito: https://badrexpress.com / https://pietrotraslochi.com"
        )
    }

    # Script di auto-compilazione universale euristico (ricerca campi name/email/phone/msg)
    inject_js = f"""
    (() => {{
        const data = {json.dumps(badr_data)};
        let filledCount = 0;

        function setVal(el, val) {{
            if (!el) return false;
            el.focus();
            el.value = val;
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            filledCount++;
            return true;
        }}

        // Nome
        setVal(document.querySelector('input[name*="name" i], input[name*="nome" i], input[id*="name" i], input[id*="nome" i]'), data.name);
        
        // Email
        setVal(document.querySelector('input[type="email"], input[name*="mail" i], input[id*="mail" i]'), data.email);
        
        // Telefono
        setVal(document.querySelector('input[type="tel"], input[name*="tel" i], input[name*="phone" i], input[id*="tel" i], input[id*="phone" i]'), data.phone);
        
        // Azienda
        setVal(document.querySelector('input[name*="company" i], input[name*="azienda" i], input[name*="ragione" i]'), data.company);
        
        // Messaggio
        setVal(document.querySelector('textarea, textarea[name*="msg" i], textarea[name*="messaggio" i]'), data.message);

        return {{ filled: filledCount, status: 'FIELDS_AUTOPOPULATED' }};
    }})()
    """

    return execute_cdp_action(url=portal_url, js_script=inject_js)
