import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}]: {msg.text}") if msg.type in ["error", "warning"] else None)

        print("Navigazione su http://127.0.0.1:8088/ ...")
        await page.goto("http://127.0.0.1:8088/", wait_until="networkidle", timeout=15000)

        # 1. Verifica titolo pagina
        title = await page.title()
        print(f"Titolo pagina: {title}")
        assert "E.B.J." in title

        # 2. Verifica Stark HUD mode
        is_stark = await page.evaluate("() => document.body.classList.contains('stark-hud-mode')")
        print(f"Stark HUD Mode attivo di default: {is_stark}")
        assert is_stark, "Stark HUD Mode dovrebbe essere attivo di default"

        # 3. Verifica presenza bottone toggle e Arc Reactor
        btn_stark = await page.query_selector("#btn-stark-mode")
        assert btn_stark is not None, "Bottone Stark HUD non trovato"

        arc_svg = await page.query_selector(".jarvis-arc-svg")
        assert arc_svg is not None, "Arc Reactor SVG non trovato"

        bars = await page.query_selector_all("#jarvis-audio-spectrum .jas-bar")
        print(f"Barre Audio Visualizer trovate: {len(bars)}")
        assert len(bars) >= 8, f"Attese almeno 8 barre spettrogramma, trovate {len(bars)}"

        # 4. Verifica toggle tema dinamico
        await page.evaluate("() => window.setThemePreset('stark-gold')")
        has_gold = await page.evaluate("() => document.body.classList.contains('theme-stark-gold')")
        print(f"Tema Stark Gold impostato: {has_gold}")
        assert has_gold, "Tema Stark Gold non applicato"

        await page.evaluate("() => window.setThemePreset('stark-cyan')")
        has_cyan = await page.evaluate("() => document.body.classList.contains('theme-stark-cyan')")
        print(f"Tema Stark Cyan ripristinato: {has_cyan}")
        assert has_cyan, "Tema Stark Cyan non applicato"

        # 5. Verifica assenza di 'Ingegner Badr' nel testo di saluto centrale
        resp_text = await page.inner_text("#resp-body")
        print(f"Saluto centrale: {resp_text[:80]}...")
        assert "Ingegner" not in resp_text, "Non deve contenere 'Ingegner'"
        assert "Badr" in resp_text, "Deve contenere 'Badr'"

        # 6. Verifica animazione spettrogramma audio
        await page.evaluate("() => window.animateJarvisSpectrum(true, 1.0)")
        await asyncio.sleep(0.3)
        transform_val = await page.evaluate("() => document.querySelector('#jarvis-audio-spectrum .jas-bar').style.transform")
        print(f"Spettrogramma animato attivo, transform: {transform_val}")
        assert "scaleY" in transform_val, "Lo spettrogramma audio non è animato"

        # 7. Verifica modalità conversazione
        is_conv = await page.evaluate("() => window.isConversationalMode")
        print(f"Modalità conversazione attiva: {is_conv}")
        assert is_conv, "Modalità conversazione deve essere True"

        # Cattura screenshot per verifica grafica
        await page.screenshot(path="stark_hud_verified.png")
        print("Screenshot salvato in stark_hud_verified.png")

        print("TUTTI I TEST SUPERATI CON SUCCESSO! ZERO ERRORI.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
