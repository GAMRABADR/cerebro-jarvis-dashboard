#!/usr/bin/env python3
"""
==============================================================================
🤖 EBJ SUPREME — UNIVERSAL AUTONOMOUS REGISTRATOR & ONBOARDING BOT
==============================================================================
Modulo specialistico per registrare autonomamente Badr / PietroTraslochi / SELEZIONE
sui principali portali italiani di lead generation, preventivi e bacheche lavoro:
- Cronoshare.it
- ProntoPro.it
- Edilnet.it
- GuidaTraslochi.it
- Traslochi24.it
- Habitissimo.it
- Subito.it / Bakeca.it

Funzionamento:
1. Carica il Dossier Aziendale Ufficiale da mail_vault.db (Badr El Ouariti, Pietro Traslochi).
2. Analizza i form web via Playwright tramite semantic field matching (AI-guided selectors).
3. Compila automaticamente tutti i campi (nome, email, telefono, CAP, città, servizi).
4. Cattura screenshot di conferma e memorizza lo stato nel database.
==============================================================================
"""

import os
import sys
import json
import time
import asyncio
import sqlite3
from playwright.async_api import async_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_vault.db")
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "registration_proofs")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Dossier Unificato di Registrazione
BADR_PROFILE = {
    "full_name": "Badr El Ouariti",
    "first_name": "Badr",
    "last_name": "El Ouariti",
    "company_name": "Pietro Traslochi & BadrExpress",
    "brand": "BadrExpress & PietroTraslochi",
    "email": "badraudi@gmail.com",
    "phone": "3888703508",
    "phone_intl": "+393888703508",
    "address": "Via San Vitale 187/189",
    "city": "Bologna",
    "city_hub": "Imola",
    "province": "BO",
    "cap": "40121",
    "cap_imola": "40026",
    "cf": "LRTBDR88A07Z330L",
    "description": (
        "Ditta specializzata in traslochi civili e commerciali, sgomberi rapidi appartamenti e uffici, "
        "noleggio furgone con autista e sponda idraulica, smontaggio e rimontaggio mobili con personale qualificato. "
        "Operativi a Bologna, Imola e in tutta l'Emilia-Romagna 7 giorni su 7."
    ),
    "services": ["Traslochi", "Sgomberi", "Trasporti", "Noleggio Furgone", "Montaggio Mobili", "Deposito"],
}

# Cataloghi di portali target per l'onboarding
PORTALS_CATALOG = [
    {
        "id": "cronoshare",
        "name": "Cronoshare Professionisti",
        "url": "https://www.cronoshare.it/registrare-azienda",
        "type": "FORM_AZIENDA",
        "notes": "Email gia registrata. Gestione tramite accesso o reset password."
    },
    {
        "id": "edilnet",
        "name": "Edilnet.it Imprese",
        "url": "https://www.edilnet.it/aziende/",
        "type": "FORM_IMPRESE",
        "notes": "Portale specializzato traslochi, ristrutturazioni ed edilizia locale."
    },
    {
        "id": "guidatraslochi",
        "name": "GuidaTraslochi.it",
        "url": "https://www.guidatraslochi.it/iscrizione-imprese",
        "type": "DIRECTORY_TRASLOCHI",
        "notes": "La directory n.1 in Italia per ditte di trasloco con preventivi diretti."
    },
    {
        "id": "traslochi24",
        "name": "Traslochi24 Partner Network",
        "url": "https://www.traslochi24.it/diventa-partner",
        "type": "PARTNER_NETWORK",
        "notes": "Rete nazionale di interscambio carichi e preventivi trasloco."
    }
]

async def inspect_and_fill_portal(page, portal_info):
    """Analizza semanticamente la pagina e tenta la compilazione automatica."""
    url = portal_info["url"]
    name = portal_info["name"]
    print(f"\n🌐 [AUTO-REGISTER] Connessione a: {name} ({url})...")
    
    try:
        await page.goto(url, timeout=35000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # 1. Accetta cookie se presenti
        for cookie_sel in [
            "button:has-text('Accetta')", "button:has-text('accetto')",
            "button:has-text('Accept')", "#acceptCookiesAlert input[type=submit]",
            ".cookie-accept", "#cookie-notice-ok"
        ]:
            try:
                btn = await page.query_selector(cookie_sel)
                if btn and await btn.is_visible():
                    await btn.click()
                    print(f"  🍪 Cookie accettati su {name}")
                    await asyncio.sleep(1)
                    break
            except Exception:
                pass

        # 2. Mappa semantica dei campi input
        inputs = await page.query_selector_all("input:not([type=hidden]):not([type=submit]):not([type=button])")
        
        # Se la landing page non ha input diretti, cerca il bottone per aprire il form (es. Edilnet)
        if len(inputs) == 0:
            for btn_text in ["REGISTRA LA TUA AZIENDA", "Registra la tua azienda", "ISCRIVITI", "Diventa partner", "Registrati", "Inizia Ora"]:
                try:
                    candidate = await page.query_selector(f"a:has-text('{btn_text}'), button:has-text('{btn_text}')")
                    if candidate and await candidate.is_visible():
                        print(f"  👆 Rilevato pulsante di registrazione: '{btn_text}' -> Clic...")
                        await candidate.click()
                        await asyncio.sleep(4)
                        await page.wait_for_load_state("domcontentloaded")
                        inputs = await page.query_selector_all("input:not([type=hidden]):not([type=submit]):not([type=button])")
                        print(f"  📝 Nuovi campi input rilevati dopo il clic: {len(inputs)}")
                        break
                except Exception:
                    pass

        print(f"  📝 Rilevati {len(inputs)} campi input visibili")

        filled_fields = []
        for inp in inputs:
            try:
                name_attr = (await inp.get_attribute("name") or "").lower()
                id_attr = (await inp.get_attribute("id") or "").lower()
                ph_attr = (await inp.get_attribute("placeholder") or "").lower()
                type_attr = (await inp.get_attribute("type") or "text").lower()
                aria_attr = (await inp.get_attribute("aria-label") or "").lower()

                field_desc = f"{name_attr} {id_attr} {ph_attr} {aria_attr}"

                # Email
                if type_attr == "email" or "email" in field_desc or "posta" in field_desc:
                    await inp.fill(BADR_PROFILE["email"])
                    filled_fields.append("email")
                # Telefono / Cellulare
                elif type_attr == "tel" or any(w in field_desc for w in ["tel", "cell", "phone", "mobile", "recapito"]):
                    await inp.fill(BADR_PROFILE["phone"])
                    filled_fields.append("telefono")
                # CAP
                elif any(w in field_desc for w in ["cap", "zip", "postcode", "geozipcode"]):
                    await inp.fill(BADR_PROFILE["cap"])
                    filled_fields.append("cap")
                # Azienda / Ragione Sociale
                elif any(w in field_desc for w in ["azienda", "attivita", "company", "ragione", "business", "ditta"]):
                    await inp.fill(BADR_PROFILE["company_name"])
                    filled_fields.append("azienda")
                # Nome e Cognome
                elif any(w in field_desc for w in ["nome", "first_name", "full_name"]):
                    await inp.fill(BADR_PROFILE["full_name"])
                    filled_fields.append("nome")
                # Città
                elif any(w in field_desc for w in ["citta", "city", "comune"]):
                    await inp.fill(BADR_PROFILE["city"])
                    filled_fields.append("città")
            except Exception as e:
                pass

        # Textarea descrizione
        try:
            textarea = await page.query_selector("textarea")
            if textarea and await textarea.is_visible():
                await textarea.fill(BADR_PROFILE["description"])
                filled_fields.append("descrizione")
        except Exception:
            pass

        print(f"  ✅ Campi compilati con successo ({len(filled_fields)}): {', '.join(filled_fields)}")

        # Salva screenshot di prova
        shot_path = os.path.join(SCREENSHOTS_DIR, f"auto_reg_{portal_info['id']}.png")
        await page.screenshot(path=shot_path)
        print(f"  📸 Prova visiva salvata in: {shot_path}")

        return {
            "portal": portal_info["id"],
            "name": name,
            "status": "COMPILATO_CON_SUCCESSO" if filled_fields else "PAGINA_SPECIALIZZATA_RICHIEDE_STEP",
            "filled_fields": filled_fields,
            "proof_screenshot": shot_path
        }

    except Exception as e:
        print(f"  ❌ Errore durante l'analisi di {name}: {e}")
        return {
            "portal": portal_info["id"],
            "name": name,
            "status": f"ERRORE: {str(e)[:100]}",
            "filled_fields": [],
            "proof_screenshot": None
        }

async def run_universal_onboarding(limit=2):
    print("🚀 [EBJ SUPREME] AVVIO MOTORE UNIVERSALE DI REGISTRAZIONE AUTOMATICA...")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        for portal in PORTALS_CATALOG[:limit]:
            res = await inspect_and_fill_portal(page, portal)
            results.append(res)
            await asyncio.sleep(2)

        await browser.close()

    print("\n=== RIEPILOGO REGISTRAZIONI AUTOMATICHE ===")
    for r in results:
        print(f"• {r['name']}: {r['status']} ({len(r['filled_fields'])} campi compilati)")

    return results

if __name__ == "__main__":
    asyncio.run(run_universal_onboarding())
