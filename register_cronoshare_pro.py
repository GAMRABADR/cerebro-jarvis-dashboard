import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from playwright.async_api import async_playwright

async def run():
    print("🚀 AVVIO REGISTRAZIONE CRONOSHARE PRO...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print("Navigazione su https://www.cronoshare.it/registrare-azienda ...")
        await page.goto("https://www.cronoshare.it/registrare-azienda", timeout=30000)
        await page.wait_for_load_state("networkidle")

        # Accetta cookies se presente
        try:
            cookie_btn = await page.query_selector("#acceptCookiesAlert input[type=submit], button:has-text('Accetta'), button:has-text('accetto')")
            if cookie_btn:
                await cookie_btn.click()
                print("✅ Cookie accettati")
                await asyncio.sleep(1)
        except Exception as e:
            print("Cookie check:", e)

        # Compilazione campi
        print("Compilazione dati: Pietro Traslochi & BadrExpress...")
        await page.fill("#name", "Pietro Traslochi & BadrExpress")
        await page.fill("#email", "badraudi@gmail.com")
        await page.fill("#password", "BadrExpress2026!")

        # Digitazione CAP con trigger eventi per caricare il select delle città
        await page.click("#geozipcode")
        await page.type("#geozipcode", "40121", delay=100)
        await page.dispatch_event("#geozipcode", "keyup")
        await asyncio.sleep(2)

        # Attendi che appaia la select delle località
        try:
            await page.wait_for_selector("#geolocality", timeout=5000)
            await page.select_option("#geolocality", value="2728")
            print("✅ Città selezionata: Bologna (2728)")
        except Exception as e:
            print("Selezione località fallback:", e)
            await page.evaluate('''() => {
                const container = document.getElementById('geolocalitiesContainer');
                if (container && !document.getElementById('geolocality')) {
                    container.innerHTML = '<select name="geolocality" id="geolocality" class="select txt14 col-sm-4 col-xs-12"><option value="2728" selected>Bologna</option></select>';
                }
            }''')

        await asyncio.sleep(1)

        # Submit
        print("Invio form con città selezionata...")
        submit_btn = await page.query_selector("input[type=submit][value='CONTINUA'], button:has-text('CONTINUA')")
        if submit_btn:
            await submit_btn.click()
            await asyncio.sleep(5)
            await page.wait_for_load_state("networkidle")

            screenshot_dir = r"C:\Users\Admin\.gemini\antigravity\brain\72dbc376-f271-4e04-8154-7a159d279000"
            post_path = os.path.join(screenshot_dir, "cronoshare_step3.png")
            await page.screenshot(path=post_path)
            print(f"📸 Screenshot step 3 salvato: {post_path}")
            print(f"URL attuale: {page.url}")
            print(f"Titolo pagina: {await page.title()}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
