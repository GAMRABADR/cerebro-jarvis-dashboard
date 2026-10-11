#!/usr/bin/env python3
"""
==============================================================================
👁️ EBJ SUPREME — JEV MULTIMODAL VISION & APPRAISAL ENGINE
==============================================================================
Motore visivo neurale per EBJ con perizia specializzata JEV:
1. Arredo & Traslochi: Riconoscimento mobili, calcolo cubatura m³ e furgone.
2. Porte & Materiali: Stima stato conservazione, tipo legno, prezzo FB Marketplace.
3. Autolavaggi: Ispezione impianti (self/portale), rilevazione chimica e pitch SELEZIONE.
4. OCR Recapiti: Estrazione automatica di numeri telefonici e P.IVA da foto.
"""

import os
import sys
import json
import base64
import re
import time
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Pesi e volumi standard JEV (in m³)
JEV_FURNITURE_M3 = {
    "armadio_6_ante": 4.0,
    "armadio_4_ante": 3.0,
    "armadio_2_ante": 2.0,
    "letto_matrimoniale": 2.2,
    "letto_singolo": 1.2,
    "materasso": 0.8,
    "divano_angolare": 3.5,
    "divano_3_posti": 2.2,
    "divano_2_posti": 1.5,
    "poltrona": 0.8,
    "tavolo_pranzo": 1.5,
    "sedia": 0.2,
    "cucina_lineare_metro": 1.2,
    "frigorifero": 1.1,
    "lavatrice": 0.5,
    "asciugatrice": 0.5,
    "comodino": 0.3,
    "comò_cassettiera": 1.0,
    "parete_attrezzata_modulo": 1.5,
    "scatolone_standard": 0.1,
    "scrivania": 1.0,
    "porta_interna": 0.3
}

def _get_api_keys():
    import server
    server._load_repo_dotenv()
    return {
        "gemini": os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"),
        "groq": os.environ.get("GROQ_API_KEY"),
        "openrouter": os.environ.get("OPENROUTER_API_KEY"),
        "qwen": os.environ.get("QWEN_API_KEY"),
    }

def analyze_image_with_jev(image_input, task_type="furniture_moving", custom_prompt=None):
    """
    Analizza un'immagine (percorso file, URL o stringa base64) usando l'intelligenza peritale JEV.
    Task supportati:
    - 'furniture_moving': stima mobili, cubatura m³ e preventivo PietroTraslochi.
    - 'doors_materials': perizia infissi, legname, valutazione Facebook Marketplace.
    - 'car_wash_audit': analisi impianto autolavaggio e prodotti chimici SELEZIONE.
    - 'ocr_contacts': estrazione numeri di telefono e insegne.
    """
    b64_data = ""
    mime_type = "image/jpeg"

    if isinstance(image_input, str):
        if image_input.startswith("data:image"):
            header, b64_data = image_input.split(",", 1)
            if "png" in header: mime_type = "image/png"
            elif "webp" in header: mime_type = "image/webp"
        elif os.path.isfile(image_input):
            with open(image_input, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            if image_input.lower().endswith(".png"): mime_type = "image/png"
            elif image_input.lower().endswith(".webp"): mime_type = "image/webp"
        else:
            b64_data = image_input

    # 1. Prova prima con Gemini se disponibile, altrimenti esegue perizia JEV euristica avanzata
    keys = _get_api_keys()
    analysis_result = None

    prompts = {
        "furniture_moving": (
            "Sei JEV, l'esperto peritale di BadrExpress e PietroTraslochi. "
            "Analizza questa foto di mobili/arredamento. "
            "Elenca con precisione ogni elemento visibile, stima il volume in metri cubi (m³) per ciascuno, "
            "il totale complessivo di cubatura, il furgone necessario (Fiat Ducato 14m³, Iveco Daily 20m³, o Camion 40m³), "
            "e consiglia il preventivo indicativo per Bologna/Emilia-Romagna in Euro. "
            "Rispondi con un JSON strutturato con chiavi: items (lista di {name, quantity, volume_m3}), total_volume_m3, "
            "recommended_vehicle, price_estimate_eur, confidence, notes."
        ),
        "doors_materials": (
            "Sei JEV, il perito d'arredo di EBJ Supreme per Facebook Marketplace e Subito.it. "
            "Analizza questa foto di porte o infissi. "
            "Valuta: tipo di legno (massello/tamburato/finitura), stato di conservazione (A/B/C), "
            "presenza di telai, stipiti, maniglie e chiavi. "
            "Fornisci: valore stimato a nuovo, prezzo medio usato su Subito.it, prezzo affare consigliato per vendita in 48h, "
            "e titolo + descrizione persuasiva per Facebook Marketplace. "
            "Rispondi con un JSON strutturato."
        ),
        "car_wash_audit": (
            "Sei JEV per SELEZIONE Detergenza e Prodotti Professionali (in collaborazione con BadrExpress). "
            "Analizza questa foto di autolavaggio (piste self, portale o impianto). "
            "Individua: tipologia impianto, condizioni, sporco stradale/calcare, e consiglia i prodotti SELEZIONE più idonei "
            "(es. Super Sgrassatore Monocomponente per cerchi/moscerini, Cera Nanotech Idrofobica, Shampoo Lucidante Schiuma Attiva). "
            "Includi la frase di pitch commerciale per il titolare. Rispondi con un JSON strutturato."
        ),
        "ocr_contacts": (
            "Sei JEV OCR. Estrai con la massima accuratezza tutti i numeri di telefono, cellulari, email, indirizzi, "
            "nomi di aziende e P.IVA visibili in questa immagine. Rispondi con JSON: {phone_numbers: [], emails: [], company_name: '', address: ''}."
        ),
        "jarvis_operator_vision": (
            "Sei J.A.R.V.I.S., il sistema d'intelligenza artificiale e interfaccia olografica dell'Ingegner Badr El Ouariti. "
            "Stai osservando il tuo operatore/creatore attraverso i sensori ottici della webcam. "
            "Analizza con tono cinematografico, brillante ed empatico degno di Tony Stark: "
            "1. Identifica chiaramente l'operatore come l'Ingegner Badr. "
            "2. Descrivi cosa vedi con precisione: la sua espressione facciale (concentrato, determinato, sorridente), postura, abbigliamento, luce della stanza e sfondo. "
            "3. Fornisci un rapido controllo telemetrico (battito simulato 72 bpm, focus 100%, biometria ottica verificata). "
            "4. Genera un messaggio vocale conciso e potente (massimo 2-3 frasi chiare per sintesi vocale Diego/JARVIS) in cui lo saluti calorosamente e confermi che lo vedi perfettamente. "
            "Rispondi SOLO con un JSON valido contenente le chiavi: "
            "{\"operator\": \"Ingegner Badr El Ouariti\", \"vocal_message\": \"...\", \"visual_description\": \"...\", \"biometrics\": {\"bpm\": 72, \"focus\": \"100%\", \"state\": \"OTTIMALE\"}, \"target_locked\": true, \"confidence\": 0.99}"
        )
    }

    prompt_to_use = custom_prompt or prompts.get(task_type, prompts["furniture_moving"])

    # Tentativo API Gemini Multimodale
    fallback_reason = None
    if keys.get("gemini") and b64_data:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={keys['gemini']}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_to_use},
                        {"inlineData": {"mimeType": mime_type, "data": b64_data}}
                    ]
                }],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000}
            }
            res = requests.post(url, json=payload, timeout=12)
            if res.status_code == 200:
                raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_json = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
                clean_json = re.sub(r"^```\s*", "", clean_json, flags=re.MULTILINE).strip()
                try:
                    analysis_result = json.loads(clean_json)
                except Exception:
                    analysis_result = {"raw_analysis": raw_text}
            else:
                fallback_reason = f"gemini_http_{res.status_code}"
        except Exception as e:
            fallback_reason = f"gemini_error: {e}"
            print(f"[JEV Vision] Gemini error: {e}")
    elif not b64_data:
        fallback_reason = "no_image_data"
    else:
        fallback_reason = "no_api_key"

    if analysis_result:
        analysis_result["engine"] = "EBJ JEV Multimodal Vision 2026"
        analysis_result["appraisal_source"] = "gemini_vision"
        analysis_result["vision_applied"] = True
    else:
        # Il template deterministico non ha letto nulla: deve dirlo al chiamante,
        # altrimenti una perizia cablata viene presa per una lettura della foto.
        analysis_result = _jev_deterministic_appraisal(task_type)
        analysis_result["engine"] = "JEV deterministic template (immagine NON analizzata)"
        analysis_result["appraisal_source"] = "deterministic_template"
        analysis_result["vision_applied"] = False
        analysis_result["fallback_reason"] = fallback_reason
        analysis_result["confidence"] = 0.0

    analysis_result["task_type"] = task_type
    analysis_result["timestamp"] = int(time.time())
    return analysis_result

def _jev_deterministic_appraisal(task_type):
    """Calcolo peritale deterministico basato sulla knowledge base di JEV."""
    if task_type == "furniture_moving":
        items = [
            {"name": "Armadio 4 ante smontato", "quantity": 1, "volume_m3": 3.0},
            {"name": "Letto matrimoniale con contenitore", "quantity": 1, "volume_m3": 2.2},
            {"name": "Divano 3 posti", "quantity": 1, "volume_m3": 2.2},
            {"name": "Tavolo con 4 sedie", "quantity": 1, "volume_m3": 2.3},
            {"name": "Elettrodomestici (Frigo + Lavatrice)", "quantity": 2, "volume_m3": 1.6},
            {"name": "Scatoloni masserizie", "quantity": 20, "volume_m3": 2.0}
        ]
        tot = sum(i["volume_m3"] for i in items)
        return {
            "items": items,
            "total_volume_m3": round(tot, 1),
            "recommended_vehicle": "1x Iveco Daily Gran Volume (20 m³)",
            "price_estimate_eur": 490.0,
            "estimated_hours": 4,
            "confidence": 0.94,
            "provider": "PietroTraslochi.com & BadrExpress.com",
            "notes": "Valutazione peritale standard appartamento bilocale Bologna."
        }
    elif task_type == "doors_materials":
        return {
            "item_name": "Set Porte Legno Massello con Finitura Noce",
            "wood_type": "Legno massello naturale stagionato con bugnatura ad arco",
            "state_of_conservation": "Ottimo (Grado A - Legno sano, smontato con cura)",
            "accessories_detected": ["Telai/Stipiti completi", "Coprifili", "Maniglie ottone", "Chiavi originali"],
            "market_valuation": {
                "estimated_price_new": "€ 320 cad.",
                "used_market_average": "€ 120 cad.",
                "quick_sale_price": "€ 75 cad. (o € 200 blocco 3 porte)"
            },
            "fb_title": "3 Porte per Interni Legno Massello con Telai e Chiavi - Bologna",
            "confidence": 0.96,
            "signature": "BadrExpress.com"
        }
    elif task_type == "car_wash_audit":
        return {
            "facility_type": "Impianto Autolavaggio Piste Self + Portale Spazzole",
            "target_issues": ["Calcare persistente su lance", "Pellicola di traffico pesante sui veicoli", "Asciugatura lenta"],
            "recommended_selezione_products": [
                {
                    "product": "SELEZIONE Monocomponente Hyper-Degreaser 25Kg",
                    "use": "Prelavaggio schiumogeno senza spugnatura",
                    "savings_per_wash": "0.18 € / lavaggio"
                },
                {
                    "product": "SELEZIONE Nanotech Hydro-Wax Effetto Seta",
                    "use": "Asciugatura istantanea senza aloni a zero residui",
                    "savings_per_wash": "0.12 € / lavaggio"
                }
            ],
            "pitch_script": "Buongiorno, siamo di SELEZIONE Distribuzione. Vi consegniamo gratuitamente 5L di prova del nostro monocomponente per testare la brillantezza sulle piste.",
            "brand": "SELEZIONE — Distribuzione e Vendita Prodotti Professionali (in collab. BadrExpress.com)"
        }
    elif task_type in ("jarvis_operator_vision", "operator_vision"):
        return {
            "operator": "Ingegner Badr El Ouariti",
            "vocal_message": "Bentornato, Ingegner Badr. Sistemi di puntamento ottico calibrati. Riconoscimento facciale attivo: ti vedo chiaramente e tutti i sistemi sono online.",
            "visual_description": "Operatore inquadrato frontalmente davanti alla postazione di comando. Condizioni di luce rilevate, parametri biometrici stabili.",
            "biometrics": {"bpm": 72, "focus": "100%", "state": "OTTIMALE"},
            "target_locked": True,
            "confidence": 0.99
        }
    else:
        # Nessun dato cablato: un OCR di fallback che restituisce un numero reale
        # verrebbe salvato come contatto estratto dalla foto.
        return {
            "phone_numbers": [],
            "emails": [],
            "company_name": "",
            "address": "",
            "notes": "OCR non eseguito: nessuna estrazione dall'immagine. Riprovare con le quote cloud disponibili."
        }

if __name__ == "__main__":
    test_result = analyze_image_with_jev("public/selezione_van_header.jpg", "furniture_moving")
    print(json.dumps(test_result, indent=2, ensure_ascii=False))
