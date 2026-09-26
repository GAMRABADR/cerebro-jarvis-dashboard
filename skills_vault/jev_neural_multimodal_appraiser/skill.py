import os
import sys
import json
import re

CATEGORY_RULES = {
    "porte": {
        "cat": "ARREDO_CASA_INFISSI",
        "new_unit": 320,
        "used_avg": 120,
        "deal_unit": 75,
        "bundle_discount": 0.88,
        "specs": ["Legno massello finitura classica", "Telai e stipiti coordinati", "Cardini premontati", "Maniglie e chiavi originali"]
    },
    "armadio": {
        "cat": "MOBILI_ANTICO_MASSELLO",
        "new_unit": 850,
        "used_avg": 280,
        "deal_unit": 180,
        "bundle_discount": 0.90,
        "specs": ["Struttura solida in legno", "Ripiani e aste appendiabiti inclusi", "Smontaggio curato e ferramenta inclusa"]
    },
    "tavolo": {
        "cat": "MOBILI_ANTICO_MASSELLO",
        "new_unit": 450,
        "used_avg": 160,
        "deal_unit": 95,
        "bundle_discount": 0.85,
        "specs": ["Piano in vero legno massello", "Gambe stabili senza oscillazioni", "Finitura protettiva sana"]
    },
    "elettrodomestico": {
        "cat": "ELETTRODOMESTICI",
        "new_unit": 420,
        "used_avg": 150,
        "deal_unit": 90,
        "bundle_discount": 0.90,
        "specs": ["Classe energetica verificata", "Testato e perfettamente funzionante", "Pulizia e sanificazione eseguita"]
    },
    "idropulitrice": {
        "cat": "ATTREZZATURE_LAVAGGIO_OFFICINA",
        "new_unit": 1200,
        "used_avg": 450,
        "deal_unit": 290,
        "bundle_discount": 0.85,
        "specs": ["Pompa ad alta pressione professionale", "Ugelli e tubo rinforzato inclusi", "Pressione e portata verificate"]
    },
    "default": {
        "cat": "OGGETTISTICA_E_ARREDO",
        "new_unit": 250,
        "used_avg": 90,
        "deal_unit": 50,
        "bundle_discount": 0.85,
        "specs": ["Oggetto controllato e integro", "Condizioni ottime di conservazione", "Pronto all'uso immediato"]
    }
}

def detect_category(item_name):
    low = item_name.lower()
    for k in CATEGORY_RULES:
        if k in low:
            return CATEGORY_RULES[k], k
    return CATEGORY_RULES["default"], "articolo"

def execute(params=None):
    params = params or {}
    item_name = (params.get("item_name") or params.get("query") or "Set 3 Porte per Interni Legno Massello").strip()
    qty = int(params.get("quantity", 3 if "porte" in item_name.lower() else 1))
    location = params.get("location", "Bologna / Cuneo e provincia")
    condition = params.get("condition", "Ottime condizioni generali - Smontato con cura")
    
    cat_rule, key_detected = detect_category(item_name)
    
    val_new_unit = cat_rule["new_unit"]
    val_used_unit = cat_rule["used_avg"]
    deal_unit = cat_rule["deal_unit"]
    
    val_new_total = val_new_unit * qty
    deal_total = int(deal_unit * qty * (cat_rule["bundle_discount"] if qty > 1 else 1.0))

    # Copywriting ad alta conversione per Facebook Marketplace
    fb_title = f"{qty}x {item_name.title()} [Ottime Condizioni + Trasporto Disponibile]"
    fb_desc = f"""✨ VENDESI: {item_name.upper()} ✨
Condizioni: {condition}. Robusto, sano e pronto all'uso immediato!

📦 DOTAZIONE COMPLETA:
{"".join(f"✔️ {s}\n" for s in cat_rule["specs"])}
💰 PREZZO AFFARE (VENDITA RAPIDA):
• Singolo pezzo: SOLO {deal_unit} € cad.
{f"🔥 OFFERTA BLOCCO COMPLETO ({qty} pezzi): SOLO {deal_total} € complessivi! (Risparmio oltre il 70% rispetto al nuovo)" if qty > 1 else ""}

📍 RITIRO & TRASPORTO:
• Ritiro a mano comodo su appuntamento.
🚚 NON HAI IL FURGONE?
Con il nostro servizio BadrExpress.com offriamo CONSEGNA DIRETTA A DOMICILIO con furgone su {location} e zone limitrofe a tariffa agevolata!

💬 Contattami subito in privato o su WhatsApp per informazioni o per bloccarlo prima che vada venduto!
---
BadrExpress.com · Logistica, Sgomberi & Arredo di Qualità"""

    subito_title = f"{item_name.title()} - Perfetto affare ({location.split('/')[0].strip()})"
    subito_desc = fb_desc.replace("BadrExpress.com", "PietroTraslochi.com")

    return {
        "status": "SUCCESS",
        "skill": "jev_neural_multimodal_appraiser",
        "item_name": item_name,
        "category": cat_rule["cat"],
        "quantity": qty,
        "valuation": {
            "valore_nuovo_stimato_totale": f"€ {val_new_total}",
            "valore_usato_medio_mercato": f"€ {val_used_unit * qty}",
            "prezzo_singolo_consigliato": f"€ {deal_unit}",
            "prezzo_blocco_consigliato": f"€ {deal_total}",
            "margine_competitivo_risparmio": f"{int((1 - (deal_total/val_new_total))*100)}%"
        },
        "copywriting": {
            "fb_title": fb_title,
            "fb_description": fb_desc,
            "subito_title": subito_title,
            "subito_description": subito_desc
        },
        "transport_hook": "CONSEGNA CON FURGONE BADREXPRESS.COM AL PIANO",
        "message": f"Perizia JEV completata per '{item_name}': prezzo affare consigliato {deal_total}€ ({qty} pz) con copywriting pronto per FB Marketplace e Subito."
    }
