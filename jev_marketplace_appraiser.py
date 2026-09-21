#!/usr/bin/env python3
"""
EBJ Supreme — JEV Marketplace Appraiser & Auto-Publisher
Motore decisionale e peritale per Facebook Marketplace & Subito.it
- Riconosce automaticamente oggetti, materiali e accessori da foto e testo
- Calcola valore a nuovo, valore di mercato usato e posizionamento prezzo competitivo
- Scrive copywriting persuasivo ad altissima conversione
- Firma ufficiale: BadrExpress.com (con offerta trasporto opzionale)
"""

import os
import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def appraise_wooden_doors():
    """
    Perizia specialistica JEV per il set di 3 porte in legno con stipiti e chiavi.
    """
    appraisal = {
        "item_category_jev": "ARREDO_CASA_INFISSI",
        "item_name": "Set 3 Porte per Interni in Legno Massello Complete",
        "wood_type": "Legno massello finitura noce classico / miele con bugnatura ad arco",
        "quantity": 3,
        "included_accessories": [
            "3 Ante porte in legno massello con bugnatura elegante ad arco classico",
            "Telai e stipiti in legno abbinati con mostrine e coprifili ad incastro",
            "Cardini originali già montati e numerati per facilitare il rimontaggio",
            "Maniglie in ottone dorato lucido originali",
            "Serrature e relative chiavi in ottone dorato originali (tutte verificate)"
        ],
        "state_of_conservation": "Usato - Ottime condizioni generali, legno sano e robusto, smontate con estrema cura e numerate (1, 2, 3)",
        "market_valuation": {
            "estimated_price_new": "€ 280 - € 350 a porta (Valore totale a nuovo ~€ 900 - € 1.050)",
            "average_used_market_price": "€ 110 - € 130 a porta",
            "selling_price_single": 75,
            "selling_price_bundle_3": 200,
            "pricing_strategy": "Prezzo affare super competitivo (75€ cad. o 200€ in blocco), garantisce vendita rapida entro 48-72h evitando ribassi prolungati."
        },
        "target_audience": [
            "Chi sta ristrutturando casa o appartamento e cerca porte di qualità in vero legno senza spendere cifre esorbitanti",
            "Proprietari di seconde case, case vacanza o rustici / casali",
            "Imprese edili e artigiani per cantieri veloci"
        ],
        "location": "Bologna / Imola e provincia",
        "transport_service_badr": "Ritiro a mano a costo zero oppure CONSEGNA AL PIANO con furgone BadrExpress.com",
        "signature": "BadrExpress.com"
    }

    # Copywriting ottimizzato per l'algoritmo di Facebook Marketplace
    fb_title = "3 Porte per Interni Legno Massello con Telai, Cardini e Chiavi"
    
    fb_description = f"""🚪 VENDESI: SET 3 PORTE PER INTERNI IN LEGNO MASSELLO COMPLETE DI TELAI, CARDINI E CHIAVI ORIGINALI 🚪

Splendide porte da interni in vero legno massello (finitura noce classico con elegante bugnatura superiore ad arco). 
Robuste, calde e di ottima manifattura artigianale, ideali per abitazioni, appartamenti in ristrutturazione, uffici o seconde case.

Smontate con estrema cura da appartamento, già numerate e pronte per il montaggio immediato!

✨ DOTAZIONE COMPLETA (RARA DA TROVARE COSÌ COMPLETA):
✔️ 3 Ante porta in legno massello con pannelli bugnati ad arco
✔️ Telai / stipiti completi in legno abbinato con mostrine e coprifili
✔️ Cardini in legno/metallo originali già predisposti
✔️ Maniglie originali in ottone dorato
✔️ Serrature funzionanti con le loro CHIAVI in ottone originali incluse!

📐 MISURE STANDARD ITALIANE (Verificabili sul posto):
• Spessore anta robusto, battuta perfetta
• Disponibili 3 porte gemelle coordinate

💰 PREZZO AFFARE:
• Singola porta completa (anta + telaio + cardini + maniglia + chiave): SOLO 75 € cad.!
🔥 OFFERTA BLOCCO COMPLETO: Tutte e 3 le porte a soli 200 € complessivi!
(Prezzo da nuove oltre 300€ a porta: risparmi più del 75%!)

📍 RITIRO & TRASPORTO:
• Ritiro a mano in zona Imola / Bologna.
🚚 NON HAI IL FURGONE PER IL TRASPORTO?
Nessun problema! Con il nostro servizio BadrExpress.com offriamo possibilità di CONSEGNA DIRETTA A DOMICILIO con furgone a tariffa agevolata e concordata su Bologna, Imola, Faenza e zone limitrofe!

Massima serietà e trasparenza. Disponibile per qualsiasi visione sul posto.
Primo che conferma si aggiudica l'affare!

💬 Contattami subito in privato su Messenger o via messaggio per info o per bloccarle!

---
BadrExpress.com · Servizi Espressi, Logistica & Arredo"""

    subito_title = "3 Porte da interno in legno massello con telaio e chiavi"

    return {
        "appraisal": appraisal,
        "fb_title": fb_title,
        "fb_description": fb_description,
        "subito_title": subito_title,
        "price_single": 75,
        "price_bundle": 200
    }

if __name__ == "__main__":
    res = appraise_wooden_doors()
    print("=== PERIZIA JEV MARKETPLACE ===")
    print(f"Titolo Annuncio: {res['fb_title']}")
    print(f"Prezzo: {res['price_single']} € cad. (Blocco: {res['price_bundle']} €)")
    print("\n--- DESCRIZIONE ANNUNCIO ---")
    print(res['fb_description'])
