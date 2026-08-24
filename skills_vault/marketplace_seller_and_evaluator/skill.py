def execute(params=None):
    params = params or {}
    item_title = params.get("item", "Articolo Usato").strip()
    condition = params.get("condition", "Ottime condizioni / Come nuovo")
    location = params.get("location", "Imola / Bologna / Milano")

    # Intelligent pricing heuristic
    i_lower = item_title.lower()
    if "playstation 5" in i_lower or "ps5" in i_lower:
        price_min, price_max, price_rec = 340, 420, 380
        category = "Console & Videogiochi"
    elif "iphone" in i_lower or "telefono" in i_lower or "smartphone" in i_lower:
        price_min, price_max, price_rec = 280, 550, 420
        category = "Telefonia & Smartphone"
    elif "lavatrice" in i_lower or "frigo" in i_lower or "elettrodomestico" in i_lower:
        price_min, price_max, price_rec = 120, 260, 180
        category = "Elettrodomestici"
    elif "mobile" in i_lower or "armadio" in i_lower or "tavolo" in i_lower:
        price_min, price_max, price_rec = 80, 220, 150
        category = "Arredamento & Casa"
    else:
        price_min, price_max, price_rec = 50, 150, 95
        category = "Varie & Collezionismo"

    ad_copy = f"""🔥 VENDESI: {item_title.upper()} — {condition.upper()} 🔥

Prezzo richiesto: € {price_rec} (Trattabile per ritiro rapido)
📍 Ritiro a mano zona: {location} (Possibilità di concordare consegna o spedizione tracciata).

✨ Caratteristiche & Dettagli:
• Condizioni: {condition}, testato e perfettamente funzionante al 100%.
• Massima serietà e disponibilità per qualsiasi prova sul posto prima dell'acquisto.
• Primo che ritira si aggiudica l'articolo!

💬 Per info o per bloccarlo subito, contattatemi in privato su Messenger o WhatsApp!"""

    return {
        "status": "SUCCESS",
        "item": item_title,
        "category": category,
        "price_range": f"€ {price_min} - € {price_max}",
        "recommended_price": f"€ {price_rec}",
        "ad_copy": ad_copy,
        "facebook_marketplace_ready": True,
        "message": f"Valutazione completata per '{item_title}': fascia di mercato stimata €{price_min}-€{price_max}. Prezzo consigliato per vendita rapida: €{price_rec}."
    }
