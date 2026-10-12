#!/usr/bin/env python3
# ==============================================================================
#  EBJ SUPREME — JEV APEX MARKETPLACE & APPRAISAL ENGINE (2026 ARCHITECTURE)
# ==============================================================================
#  Motore peritale e decisionale multimodale per Facebook Marketplace, Subito, eBay & Wallapop:
#   - Riconoscimento automatico e stima del valore a nuovo vs valore reale dell'usato
#   - 5 Gradi di conservazione certificati (Mint, Ottimo, Buono, Discreto, Revisione)
#   - Modelli di pricing: "Prezzo Affare Super Competitivo" (48-72h) vs "Valore Medio"
#   - Copywriting persuasivo ad alta conversione personalizzato per piattaforma
#   - Integrazione nativa servizio furgone & consegna al piano con BadrExpress.com
#   - Generatore link WhatsApp per trattativa diretta immediata senza intermediari
# ==============================================================================

import os
import sys
import json
import urllib.parse
from typing import Dict, Any, List, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEPRECIATION_MAP = {
    "nuovo_sigillato": {"ratio_min": 0.80, "ratio_max": 0.90, "deal_ratio": 0.75, "label": "Nuovo Sigillato / Mai Aperto"},
    "come_nuovo": {"ratio_min": 0.65, "ratio_max": 0.75, "deal_ratio": 0.55, "label": "Usato - Come Nuovo (Mint)"},
    "ottime_condizioni": {"ratio_min": 0.45, "ratio_max": 0.55, "deal_ratio": 0.40, "label": "Usato - Ottime Condizioni Generali"},
    "buone_condizioni": {"ratio_min": 0.30, "ratio_max": 0.40, "deal_ratio": 0.25, "label": "Usato - Buone Condizioni con Normali Segni"},
    "da_revisionare": {"ratio_min": 0.15, "ratio_max": 0.25, "deal_ratio": 0.12, "label": "Usato - Da Revisionare / Per Parti di Ricambio"}
}

CATEGORY_DEFAULTS = {
    "porte_infissi": {"name": "Infissi & Porte da Interno", "retail_est": 300, "kw": ["porta", "porte", "infissi", "stipiti", "telaio"]},
    "arredo_casa": {"name": "Arredamento & Mobili", "retail_est": 450, "kw": ["armadio", "tavolo", "divano", "sedia", "letto", "comodino", "libreria", "cucina"]},
    "elettrodomestici": {"name": "Grandi & Piccoli Elettrodomestici", "retail_est": 380, "kw": ["lavatrice", "frigorifero", "forno", "lavastoviglie", "microonde", "asciugatrice"]},
    "attrezzatura_lavoro": {"name": "Attrezzatura da Lavoro & Fai-da-te", "retail_est": 220, "kw": ["trapano", "compressore", "scala", "idropulitrice", "saldatrice", "banco"]},
    "mobilita_veicoli": {"name": "Biciclette, E-Bike & Mobilità", "retail_est": 250, "kw": ["bici", "bicicletta", "mountain bike", "e-bike", "monopattino", "scooter"]}
}

def detect_category(item_name: str) -> str:
    n_low = item_name.lower()
    for cat, info in CATEGORY_DEFAULTS.items():
        if any(w in n_low for w in info["kw"]):
            return cat
    return "arredo_casa"

def appraise_generic_item(
    item_name: str,
    condition: str = "ottime_condizioni",
    retail_price_new: Optional[float] = None,
    location: str = "Bologna / Imola",
    phone_contact: Optional[str] = "3489823610",
    include_delivery_upsell: bool = True
) -> Dict[str, Any]:
    """
    Perizia specialistica JEV per qualsiasi bene o arredo.
    Calcola prezzo a nuovo, stima usato, prezzo affare 48h, e genera testi multi-piattaforma.
    """
    cat_key = detect_category(item_name)
    cond_key = condition if condition in DEPRECIATION_MAP else "ottime_condizioni"
    dep = DEPRECIATION_MAP[cond_key]

    base_retail = retail_price_new if retail_price_new and retail_price_new > 0 else CATEGORY_DEFAULTS[cat_key]["retail_est"]
    
    market_used_min = round(base_retail * dep["ratio_min"])
    market_used_max = round(base_retail * dep["ratio_max"])
    deal_price = round(base_retail * dep["deal_ratio"])
    # Arrotondamento psicologico (termina con 0 o 5 se > 30)
    if deal_price > 30:
        deal_price = int(round(deal_price / 5.0) * 5)

    # Titoli ottimizzati per piattaforma (< 60 caratteri per Subito e FB)
    clean_title = f"{item_name.title()} - {dep['label'].split('(')[0].strip()}"
    if len(clean_title) > 65:
        clean_title = f"{item_name.title()} {dep['label'].split('-')[-1].strip()}"[:65]

    subito_title = f"{item_name.title()} in ottime condizioni"[:50]
    
    # Costruzione Copywriting Persuasivo Facebook Marketplace
    fb_desc = f"""✨ VENDESI: {item_name.upper()} ✨

Condizioni: {dep['label']}
Perfettamente funzionante, pronto all'uso e verificabile di persona!

📐 DETTAGLI & CARATTERISTICHE:
• Oggetto integro, solido e tenuto con estrema cura.
• Ideale per chi cerca qualità e affidabilità risparmiando notevolmente rispetto al prezzo di listino.
• Prezzo da nuovo equivalente a listino: circa € {base_retail:.0f}.

💰 PREZZO AFFARE PER REALIZZO RAPIDO:
🔥 SOLO € {deal_price:.0f} (Risparmi oltre il {round((1 - deal_price/base_retail)*100)}% rispetto al nuovo!)
Prezzo competitivo studiato per chiudere l'affare rapidamente senza inutili attese.

📍 ZONA DI RITIRO:
• Ritiro a mano comodo in zona {location}."""

    if include_delivery_upsell:
        fb_desc += f"""

🚚 NON HAI UN VEICOLO O IL TEMPO PER IL TRASPORTO?
Nessun problema! Con il nostro servizio BadrExpress.com offriamo possibilità di CONSEGNA DIRETTA A DOMICILIO con furgone su Bologna, Imola, Faenza e comuni limitrofi a tariffa concordata agevolata!"""

    fb_desc += f"""

Massima serietà, trasparenza e disponibilità per visione sul posto.
Primo che conferma si aggiudica l'affare!

💬 Contattami subito in privato per bloccarlo o richiedere informazioni!
---
BadrExpress.com · Servizi Espressi, Logistica & Arredo"""

    # Copywriting Subito.it (Pulito, privo di emoji ridondanti)
    subito_desc = f"""Vendo {item_name.lower()}, condizioni: {dep['label']}.
L'oggetto è perfettamente integro e pronto per l'utilizzo immediato.

Prezzo richiesto: € {deal_price} (valore stimato a nuovo ~€ {base_retail:.0f}).
Ritiro a mano in zona {location}. Disponibilità di trasporto dedicato su richiesta tramite furgone BadrExpress.

Per qualsiasi informazione o per concordare la visione contattare via messaggio o telefono."""

    # Link WhatsApp Diretto
    wa_msg = f"Salve, ho visto l'annuncio per '{item_name}' su Marketplace a {deal_price}€ ed è ancora disponibile?"
    wa_encoded = urllib.parse.quote(wa_msg)
    wa_link = f"https://wa.me/39{phone_contact}?text={wa_encoded}" if phone_contact else None

    return {
        "status": "SUCCESS",
        "item_name": item_name,
        "category": cat_key,
        "condition": cond_key,
        "condition_label": dep["label"],
        "valuation": {
            "retail_new_eur": base_retail,
            "market_used_range_eur": f"€ {market_used_min} - € {market_used_max}",
            "recommended_deal_price_eur": deal_price,
            "savings_percent": round((1 - deal_price/base_retail)*100)
        },
        "copywriting": {
            "fb_marketplace_title": clean_title,
            "fb_marketplace_description": fb_desc,
            "subito_title": subito_title,
            "subito_description": subito_desc
        },
        "whatsapp_deal_link": wa_link,
        "location": location,
        "delivery_upsell": include_delivery_upsell,
        "verbal_summary": f"Perizia JEV completata per '{item_name}', Badr: valore stimato a nuovo €{base_retail}, prezzo consigliato €{deal_price} per vendita rapida entro 48 ore."
    }

def appraise_wooden_doors() -> Dict[str, Any]:
    """Retrocompatibilità specialistica per il set di 3 porte in legno massello."""
    res = appraise_generic_item(
        item_name="Set 3 Porte per Interni in Legno Massello Complete",
        condition="ottime_condizioni",
        retail_price_new=900,
        location="Bologna / Imola"
    )
    res["fb_title"] = "3 Porte per Interni Legno Massello con Telai, Cardini e Chiavi"
    res["subito_title"] = "3 Porte da interno in legno massello con telaio e chiavi"
    res["price_single"] = 75
    res["price_bundle"] = 200
    res["fb_description"] = res["copywriting"]["fb_marketplace_description"]
    return res

if __name__ == "__main__":
    print("--- TEST UNIVERSAL JEV MARKETPLACE ENGINE ---")
    test1 = appraise_generic_item("Lavatrice Bosch Serie 6 8kg", "ottime_condizioni", 550)
    print("Test 1:", test1["verbal_summary"])
    print("Prezzo Affare:", test1["valuation"]["recommended_deal_price_eur"], "€")
    print("WA Link:", test1["whatsapp_deal_link"])
