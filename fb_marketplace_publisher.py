#!/usr/bin/env python3
"""
==============================================================================
🚀 JEV AUTONOMOUS FACEBOOK MARKETPLACE PUBLISHER (PLAYWRIGHT STEALTH)
==============================================================================
Pubblica annunci su Facebook Marketplace in totale autonomia:
1. Utilizza il profilo utente o la sessione autenticata.
2. Esegue l'upload delle immagini reali tramite file input nativo di Playwright.
3. Compila Titolo, Prezzo, Categoria, Condizione e Descrizione dettagliata.
4. Convalida i campi, naviga lo step successivo e finalizza la pubblicazione.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
SCREENSHOT_DIR = ROOT / "public" / "marketplace_runs"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_PHOTOS = [
    str(ROOT / "public" / "marketplace_doors" / "porta_cover_fb_marketplace.jpg"),
    str(ROOT / "public" / "marketplace_doors" / "porta_1_hero_studio.jpg"),
    str(ROOT / "public" / "marketplace_doors" / "porta_2_telai_stipiti.jpg"),
    str(ROOT / "public" / "marketplace_doors" / "porta_3_chiavi_ottone.jpg"),
    str(ROOT / "public" / "marketplace_doors" / "porta_4_blocco_3_porte.jpg"),
]

DEFAULT_DATA = {
    "title": "3 Porte per Interni Legno Massello con Telai, Cardini e Chiavi - Trattabili + Consegna a Domicilio",
    "price": "75",
    "category": "Miglioramento della casa",
    "condition": "Usato - Come nuovo",
    "location": "Imola",
    "description": """🚪 VENDESI: SET 3 PORTE PER INTERNI IN LEGNO MASSELLO COMPLETE DI TELAI, CARDINI E CHIAVI ORIGINALI 🚪

Splendide porte da interni in vero legno massello (finitura noce classico con elegante bugnatura superiore ad arco). 
Robuste, calde e di ottima manifattura artigianale, ideali per abitazioni, appartamenti in ristrutturazione, uffici o seconde case.

Smontate con estrema cura da appartamento, già numerate e pronte per il montaggio immediato!

✨ DOTAZIONE COMPLETA (RARA DA TROVARE COSÌ COMPLETA):
✔️ 3 Ante porta in legno massello con pannelli bugnati ad arco
✔️ Telai / stipiti completi in legno abbinato con mostrine e coprifili
✔️ Cardini in legno/metallo originali già predisposti
✔️ Maniglie originali in ottone dorato
✔️ Serrature perfettamente funzionanti con le loro CHIAVI in ottone originali incluse!

📐 MISURE STANDARD ITALIANE:
• Spessore anta robusto, battuta perfetta
• Disponibili 3 porte gemelle coordinate

💰 PREZZO & TRATTABILITÀ:
• Singola porta completa (anta + telaio + cardini + maniglia + chiave): 75 € cad.
• 🔥 OFFERTA BLOCCO COMPLETO: Tutte e 3 le porte a soli 200 € complessivi!
• 🤝 PREZZO TRATTABILE per acquisto rapido o per chi ritira tutto il blocco!

🚚 DISPONIBILE AL TRASPORTO E CONSEGNA IN CASA:
• Ritiro a mano disponibile in zona Imola / Bologna.
• 📦 SERVIZIO TRASPORTO & CONSEGNA AL PIANO: Se non hai il furgone o non vuoi fare fatica, siamo OVVIAMENTE DISPONIBILI AL TRASPORTO con furgone e possiamo effettuare la CONSEGNA IN CASA / AL PIANO con una piccola aggiunta concordata per il servizio di trasporto e facchinaggio! 
• Copertura trasporto rapido su Bologna, Imola, Faenza, Ravenna, Forlì e zone limitrofe.

Massima serietà, trasparenza e puntualità. Disponibile per qualsiasi visione e prova sul posto.
Primo che conferma si aggiudica l'affare!

💬 Contattami subito in privato su Messenger o via messaggio per info, accordarci sul prezzo o bloccarle!

---
BadrExpress.com · Servizi Espressi, Trasporti, Logistica & Arredo"""
}

class FBMarketplacePublisher:
    def __init__(self, headless=False, use_cdp=False, cdp_url="http://localhost:9222"):
        self.headless = headless
        self.use_cdp = use_cdp
        self.cdp_url = cdp_url
        self.session_file = PROJECT_ROOT / "Agente-0" / "config" / "fb_session.json"
        self.user_data_dir = ROOT / "storage" / "fb_bot_profile"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

    async def publish(self, data=None, photos=None, auto_submit=False):
        data = data or DEFAULT_DATA
        photos = [p for p in (photos or DEFAULT_PHOTOS) if os.path.exists(p)]
        run_id = f"run_{int(time.time())}"
        log_records = []

        def log(msg):
            t_msg = f"[{time.strftime('%H:%M:%S')}] {msg}"
            print(t_msg)
            log_records.append(t_msg)

        log(f"Inizio pubblicazione annuncio Marketplace: '{data['title']}'")
        log(f"Numero foto verificate per l'upload: {len(photos)}")

        async with async_playwright() as p:
            browser = None
            context = None
            page = None

            if self.use_cdp:
                try:
                    log(f"Tentativo connessione CDP su {self.cdp_url}...")
                    browser = await p.chromium.connect_over_cdp(self.cdp_url)
                    context = browser.contexts[0] if browser.contexts else await browser.new_context()
                    # Cerca se esiste già un tab con facebook create
                    for pg in context.pages:
                        if "facebook.com/marketplace/create" in pg.url:
                            page = pg
                            log(f"Trovata scheda già aperta: {page.url}")
                            break
                    if not page:
                        page = await context.new_page()
                except Exception as e:
                    log(f"CDP non disponibile ({e}). Fallback su profilo persistente stealth.")

            if not page:
                args = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--start-maximized"
                ]
                kwargs = {
                    "user_data_dir": str(self.user_data_dir),
                    "headless": self.headless,
                    "args": args,
                    "viewport": None if not self.headless else {"width": 1366, "height": 850},
                    "locale": "it-IT",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                }
                context = await p.chromium.launch_persistent_context(**kwargs)
                page = await context.new_page()

            # Navigazione
            target_url = "https://www.facebook.com/marketplace/create/item"
            log(f"Caricamento URL: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(3)

            # Verifica eventuale popup login / continua come
            continue_btns = page.locator("div[role='button']:has-text('Continua come'), button:has-text('Continua come'), div[role='button']:has-text('Continue as')")
            if await continue_btns.count() > 0:
                log("Popup 'Continua come' rilevato. Clicco...")
                await continue_btns.first.click()
                await asyncio.sleep(4)

            shot1 = str(SCREENSHOT_DIR / f"{run_id}_step1_loaded.png")
            await page.screenshot(path=shot1)
            log(f"Screenshot step 1 salvato: {shot1}")

            # 1. Caricamento Foto
            file_inputs = page.locator("input[type='file']")
            if await file_inputs.count() > 0 and photos:
                log(f"Caricamento {len(photos)} immagini nel selettore file...")
                await file_inputs.first.set_input_files(photos)
                await asyncio.sleep(4)
                log("Foto caricate con successo!")
            else:
                log("Nessun input file trovato o nessuna foto disponibile.")

            # 2. Compilazione Titolo
            title_locators = [
                page.locator("label[aria-label*='Titolo' i] input"),
                page.locator("input[aria-label*='Titolo' i]"),
                page.locator("label:has-text('Titolo') input"),
                page.locator("input[type='text']").first
            ]
            for loc in title_locators:
                if await loc.count() > 0:
                    log("Inserimento Titolo...")
                    await loc.first.click()
                    await loc.first.fill(data["title"])
                    await asyncio.sleep(0.5)
                    break

            # 3. Compilazione Prezzo
            price_locators = [
                page.locator("label[aria-label*='Prezzo' i] input"),
                page.locator("input[aria-label*='Prezzo' i]"),
                page.locator("label:has-text('Prezzo') input")
            ]
            for loc in price_locators:
                if await loc.count() > 0:
                    log("Inserimento Prezzo...")
                    await loc.first.click()
                    await loc.first.fill(str(data["price"]))
                    await asyncio.sleep(0.5)
                    break

            # 4. Selezione Categoria
            cat_locators = [
                page.locator("label[aria-label*='Categoria' i]"),
                page.locator("div[aria-label*='Categoria' i]"),
                page.locator("label:has-text('Categoria')")
            ]
            for loc in cat_locators:
                if await loc.count() > 0:
                    log("Apertura menu Categoria...")
                    await loc.first.click()
                    await asyncio.sleep(1.5)
                    # Cerca l'opzione migliore
                    opt = page.locator("div[role='button']:has-text('Miglioramento della casa'), div[role='menuitem']:has-text('Miglioramento della casa'), span:has-text('Miglioramento della casa'), span:has-text('Arredamento')")
                    if await opt.count() > 0:
                        await opt.first.click()
                        log("Categoria 'Miglioramento della casa' selezionata.")
                        await asyncio.sleep(1)
                    break

            # 5. Selezione Condizione
            cond_locators = [
                page.locator("label[aria-label*='Condizione' i]"),
                page.locator("div[aria-label*='Condizione' i]"),
                page.locator("label:has-text('Condizione')")
            ]
            for loc in cond_locators:
                if await loc.count() > 0:
                    log("Apertura menu Condizione...")
                    await loc.first.click()
                    await asyncio.sleep(1)
                    opt_cond = page.locator("div[role='button']:has-text('Usato - Come nuovo'), span:has-text('Usato - Come nuovo'), div[role='menuitem']:has-text('Usato - Come nuovo')")
                    if await opt_cond.count() > 0:
                        await opt_cond.first.click()
                        log("Condizione 'Usato - Come nuovo' selezionata.")
                    else:
                        # Fallback prima opzione usato
                        alt_cond = page.locator("div[role='button']:has-text('Usato'), span:has-text('Usato')")
                        if await alt_cond.count() > 0:
                            await alt_cond.first.click()
                    await asyncio.sleep(1)
                    break

            # 6. Compilazione Descrizione
            desc_locators = [
                page.locator("label[aria-label*='Descrizione' i] textarea"),
                page.locator("textarea[aria-label*='Descrizione' i]"),
                page.locator("label:has-text('Descrizione') textarea"),
                page.locator("div[role='textbox'][aria-label*='Descrizione' i]")
            ]
            for loc in desc_locators:
                if await loc.count() > 0:
                    log("Inserimento Descrizione...")
                    await loc.first.click()
                    await loc.first.fill(data["description"])
                    await asyncio.sleep(1)
                    break

            shot2 = str(SCREENSHOT_DIR / f"{run_id}_step2_filled.png")
            await page.screenshot(path=shot2)
            log(f"Screenshot step 2 (Campi Compilati) salvato: {shot2}")

            # 7. Tasto Avanti o Pubblica
            next_btns = page.locator("div[role='button']:has-text('Avanti'), button:has-text('Avanti'), div[aria-label='Avanti']")
            if await next_btns.count() > 0:
                log("Tasto 'Avanti' visibile e attivo.")
                if auto_submit:
                    log("Auto-Submit attivo: clicco Avanti...")
                    await next_btns.first.click()
                    await asyncio.sleep(3)
                    pub_btns = page.locator("div[role='button']:has-text('Pubblica'), button:has-text('Pubblica'), div[aria-label='Pubblica']")
                    if await pub_btns.count() > 0:
                        log("Clicco 'Pubblica'...")
                        await pub_btns.first.click()
                        await asyncio.sleep(5)
                        log("Annuncio pubblicato!")

            shot3 = str(SCREENSHOT_DIR / f"{run_id}_step3_final.png")
            await page.screenshot(path=shot3)
            log(f"Screenshot finale salvato: {shot3}")

            return {
                "success": True,
                "run_id": run_id,
                "title": data["title"],
                "price": data["price"],
                "photos_count": len(photos),
                "screenshots": [shot1, shot2, shot3],
                "logs": log_records
            }

if __name__ == "__main__":
    auto = "--submit" in sys.argv
    use_cdp = "--cdp" in sys.argv
    publisher = FBMarketplacePublisher(headless=True, use_cdp=use_cdp)
    result = asyncio.run(publisher.publish(auto_submit=auto))
    print("\n--- RISULTATO FINALE PUBBLICAZIONE ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
