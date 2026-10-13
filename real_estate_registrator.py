#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
real_estate_registrator.py — Agente Autonomo per Registrazione su Portali Immobiliari Italiani & Lead Gen
Sviluppato per BadrExpress & Pietro Traslochi (Ingegnere Badr El Ouariti).

Funzionalità:
- Supporto nativo per i principali portali immobiliari italiani:
  * Immobiliare.it
  * Idealista.it
  * Casa.it
  * Wikicasa.it
  * Subito.it Imprese
  * Cronoshare.it
  * ProntoPro.it
  * Qualsiasi URL personalizzato passato in input
- Compilazione euristica dei form con il Dossier Ufficiale dell'Ingegnere Badr
- Risoluzione automatica dei cookie banner (GDPR / Iubenda / OneTrust / Didomi)
- Spunta automatica delle caselle Privacy & Termini obbligatorie
- Cattura screenshot di verifica prima e dopo l'invio
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional

# Dossier Ufficiale E.B.J.
DOSSIER = {
    "first_name": "Badr",
    "last_name": "El Ouariti",
    "full_name": "Badr El Ouariti",
    "company": "Pietro Traslochi & BadrExpress",
    "email": "badraudi@gmail.com",
    "phone": "3888703508",
    "phone_intl": "+393888703508",
    "address": "Via San Vitale 187/189",
    "city": "Bologna",
    "cap": "40121",
    "province": "BO",
    "cf": "LRTBDR88A07Z330L",
    "password": os.environ.get("PORTAL_ACCOUNT_PASSWORD", ""),
    "description": (
        "Ditta specializzata in traslochi civili e commerciali, sgomberi rapidi appartamenti e cantine, "
        "noleggio furgone con autista e sponda idraulica, smontaggio e rimontaggio mobili a regola d'arte. "
        "Disponibilità immediata 7 giorni su 7 a Bologna e provincia."
    )
}

PORTAL_PRESETS = {
    "immobiliare": {
        "name": "Immobiliare.it",
        "url": "https://www.immobiliare.it/registrazione/",
        "category": "PORTALE_IMMOBILIARE"
    },
    "idealista": {
        "name": "Idealista.it",
        "url": "https://www.idealista.it/registrati/",
        "category": "PORTALE_IMMOBILIARE"
    },
    "casa": {
        "name": "Casa.it",
        "url": "https://www.casa.it/registrati/",
        "category": "PORTALE_IMMOBILIARE"
    },
    "wikicasa": {
        "name": "Wikicasa.it",
        "url": "https://www.wikicasa.it/registrazione/",
        "category": "PORTALE_IMMOBILIARE"
    },
    "subito_imprese": {
        "name": "Subito.it Imprese",
        "url": "https://imprese.subito.it/",
        "category": "MARKETPLACE_E_IMMOBILI"
    },
    "cronoshare": {
        "name": "Cronoshare",
        "url": "https://www.cronoshare.it/registrare-azienda",
        "category": "LEAD_GEN_TRASLOCHI"
    },
    "prontopro": {
        "name": "ProntoPro",
        "url": "https://pro.prontopro.it/",
        "category": "LEAD_GEN_TRASLOCHI"
    }
}

COOKIE_SELECTORS = [
    "button:has-text('Accetta')",
    "button:has-text('Accetta tutti')",
    "button:has-text('Accetta e continua')",
    "button:has-text('Accetto')",
    "button:has-text('Consenti tutti')",
    "button:has-text('Consenti')",
    "button:has-text('Agree')",
    "button:has-text('Accept all')",
    "#onetrust-accept-btn-handler",
    ".iubenda-cs-accept-btn",
    "#didomi-notice-agree-button",
    "button[data-testid='cookie-accept-all']"
]


async def dismiss_cookies(page):
    """Chiude i banner dei cookie se presenti."""
    for sel in COOKIE_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(1000)
                return True
        except Exception:
            pass
    return False


async def auto_fill_form(page, dossier: dict = DOSSIER) -> Dict[str, Any]:
    """Compila euristicamente tutti i campi input trovati nella pagina."""
    filled_fields = {}
    
    # 1. Rileva tutti gli input visibili
    inputs = await page.locator("input:visible").all()
    
    for inp in inputs:
        try:
            itype = (await inp.get_attribute("type") or "text").lower()
            iname = (await inp.get_attribute("name") or "").lower()
            iid = (await inp.get_attribute("id") or "").lower()
            placeholder = (await inp.get_attribute("placeholder") or "").lower()
            aria = (await inp.get_attribute("aria-label") or "").lower()
            
            ctx = f"{iname} {iid} {placeholder} {aria}"
            
            if itype in ("submit", "button", "hidden", "image", "file"):
                continue
                
            if itype == "checkbox":
                # Se è una checkbox di consenso privacy o termini, la spunta
                if any(k in ctx for k in ["privacy", "termini", "condizioni", "terms", "agree", "policy", "trattamento"]):
                    is_checked = await inp.is_checked()
                    if not is_checked:
                        await inp.check()
                        filled_fields[iname or iid or "checkbox"] = "CHECKED"
                continue

            # Mappatura semantica
            val = None
            field_label = ""
            
            if itype == "email" or any(k in ctx for k in ["email", "e-mail", "mail"]):
                val = dossier["email"]
                field_label = "email"
            elif itype == "password" or "pass" in ctx:
                val = dossier["password"]
                field_label = "password"
            elif any(k in ctx for k in ["cell", "tel", "phone", "mobile", "telefono"]):
                val = dossier["phone"]
                field_label = "telefono"
            elif any(k in ctx for k in ["cap", "zip", "postal"]):
                val = dossier["cap"]
                field_label = "cap"
            elif any(k in ctx for k in ["citta", "city", "comune"]):
                val = dossier["city"]
                field_label = "citta"
            elif any(k in ctx for k in ["indirizzo", "address", "via"]):
                val = dossier["address"]
                field_label = "indirizzo"
            elif any(k in ctx for k in ["azienda", "ragione", "company", "ditta", "societa"]):
                val = dossier["company"]
                field_label = "azienda"
            elif any(k in ctx for k in ["cognome", "last_name", "surname"]):
                val = dossier["last_name"]
                field_label = "cognome"
            elif any(k in ctx for k in ["nome", "first_name", "name"]) and not any(k in ctx for k in ["utente", "user"]):
                val = dossier["first_name"]
                field_label = "nome"
            elif any(k in ctx for k in ["cf", "fiscale", "vat", "piva"]):
                val = dossier["cf"]
                field_label = "codice_fiscale"
                
            if val and field_label:
                # Controlla se il campo è già compilato
                curr_val = await inp.input_value()
                if not curr_val:
                    await inp.fill(val)
                    filled_fields[iname or iid or field_label] = val
                    await page.wait_for_timeout(150)
        except Exception:
            pass

    return filled_fields


async def register_on_portal(
    target_url: str,
    submit: bool = False,
    headless: bool = True,
    screenshots_dir: str = "screenshots"
) -> Dict[str, Any]:
    """
    Agente browser per registrarsi o pre-compilare un form su qualsiasi portale.
    """
    from playwright.async_api import async_playwright

    os.makedirs(screenshots_dir, exist_ok=True)
    t0 = time.time()
    
    # Se il target è una chiave preset (es. 'immobiliare'), usa la sua URL
    actual_url = PORTAL_PRESETS.get(target_url, {}).get("url", target_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="it-IT",
            timezone_id="Europe/Rome"
        )
        page = await context.new_page()

        # Stealth evasions contro Datadome e Cloudflare
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['it-IT', 'it', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        try:
            # 1. Navigazione
            await page.goto(actual_url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # 2. Chiusura cookie
            cookies_dismissed = await dismiss_cookies(page)

            # 3. Compilazione Automatica dei campi
            filled = await auto_fill_form(page, DOSSIER)

            # 4. Screenshot di verifica compilazione
            ts = int(time.time())
            clean_name = target_url.replace("https://", "").replace("http://", "").replace("/", "_")[:25]
            screen_pre = os.path.join(screenshots_dir, f"pre_{clean_name}_{ts}.png")
            await page.screenshot(path=screen_pre, full_page=True)

            submission_status = "READY_FOR_REVIEW"
            screen_post = None

            # 5. Invio (se esplicitamente richiesto)
            if submit:
                for submit_sel in [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:has-text('Registrati')",
                    "button:has-text('Crea account')",
                    "button:has-text('Continua')",
                    "button:has-text('Avanti')"
                ]:
                    btn = page.locator(submit_sel).first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        await page.wait_for_timeout(4000)
                        submission_status = "SUBMITTED"
                        screen_post = os.path.join(screenshots_dir, f"post_{clean_name}_{ts}.png")
                        await page.screenshot(path=screen_post, full_page=True)
                        break

            return {
                "success": True,
                "target_url": actual_url,
                "portal_identified": PORTAL_PRESETS.get(target_url, {}).get("name", "Custom Portal"),
                "cookies_dismissed": cookies_dismissed,
                "fields_filled_count": len(filled),
                "fields_details": filled,
                "submission_status": submission_status,
                "screenshot_pre_submit": screen_pre,
                "screenshot_post_submit": screen_post,
                "elapsed_seconds": round(time.time() - t0, 2)
            }

        except Exception as e:
            return {
                "success": False,
                "target_url": actual_url,
                "error": str(e),
                "elapsed_seconds": round(time.time() - t0, 2)
            }
        finally:
            await browser.close()


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.immobiliare.it/registrazione/"
    print(f"[*] Avvio Agente Registrazione su: {url}")
    res = asyncio.run(register_on_portal(url, submit=False, headless=True))
    print(res)
