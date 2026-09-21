#!/usr/bin/env python3
"""
EBJ Supreme — Brand Signature & JEV Intent Engine
Modulo centralizzato per la gestione intelligente e dinamica di:
1. Brand Context:
   - SELECTION (Autolavaggi, detergenti, chimica industriale, detailing, pulizie)
     -> Firma: "SELEZIONE — Distribuzione e Vendita Prodotti Professionali" (Ditta Italiana)
     -> In calce: "In collaborazione con BadrExpress.com" (NON firmato a nome Badr)
   - TRASLOCHI (Traslochi, sgomberi, facchinaggio, noleggio furgone con sponda)
     -> Firma: "BadrExpress.com & PietroTraslochi.com" (Referenti: Badr & Pietro)
   - EBGSTUDIO (Gaming, Unreal Engine 5.8, EBGS Survival MMO)
     -> Firma: "EBGStudio Publishing"

2. Pipeline Lead & Filtro Esiti Chiamata:
   - Esclusione automatica di lead segnati 'NON_INTERESSATO' nelle nuove ricerche di zona
   - Mappatura 'GIA_FORNITO_SELECTION' nel portafoglio clienti consolidati
   - Raggruppamento prioritario 'INTERESSATO' per ordini e campionature

3. Generazione Report di Chiusura Campagna per qualsiasi città d'Italia
"""

import os
import sys
import re
import json
import sqlite3
import datetime
from enum import Enum

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIR_PATH, "mail_vault.db")

class BrandContext(str, Enum):
    SELECTION = "SELECTION"
    TRASLOCHI = "TRASLOCHI"
    EBGSTUDIO = "EBGSTUDIO"
    NEUTRAL = "NEUTRAL"

def classify_brand_intent(text: str) -> BrandContext:
    """
    JEV Intent Classifier:
    Riconosce in modo deterministico e ultra-veloce il perimetro di business dell'utente.
    """
    if not text:
        return BrandContext.NEUTRAL

    t = text.lower()

    # Pattern per SELEZIONE (Autolavaggi & Detergenza)
    selection_keywords = [
        "autolavagg", "car wash", "carwash", "detergent", "prodotti chimic",
        "fusti", "tanich", "campionatur", "selection", "selezione", "detailing",
        "pulizie professional", "lavanderi", "schiuma attiva", "cera nanotech",
        "prodotti italiani", "forniture autolavagg"
    ]
    if any(k in t for k in selection_keywords):
        return BrandContext.SELECTION

    # Pattern per TRASLOCHI & SGOMBERI
    traslochi_keywords = [
        "trasloc", "sgomber", "badrexpress", "pietrotraslochi", "furgon",
        "sponda idraulica", "facchinagg", "cantin", "smaltiment", "appartament",
        "scatol", "pietro", "piattaforma aerea"
    ]
    if any(k in t for k in traslochi_keywords):
        return BrandContext.TRASLOCHI

    # Pattern per EBGSTUDIO / GAMING
    gaming_keywords = [
        "ebgs", "steam", "unreal engine", "gameplay", "ue5", "server rust",
        "multiplayer", "survivor mmo", "patch notes", "discord bot"
    ]
    if any(k in t for k in gaming_keywords):
        return BrandContext.EBGSTUDIO

    return BrandContext.NEUTRAL

def get_brand_signature(context: BrandContext, channel: str = "text") -> dict:
    """
    Restituisce intestazioni, firme, disclaimer e badge ufficiali
    in base al contesto di business.
    """
    if context == BrandContext.SELECTION:
        return {
            "context": "SELECTION",
            "company_name": "SELEZIONE",
            "full_title": "SELEZIONE — Distribuzione e Vendita Prodotti Professionali",
            "slogan": "LA SCELTA CHE FA LA DIFFERENZA",
            "badge": "🇮🇹 DITTA ITALIANA · PRODOTTI CHIMICI 100% ITALIANI",
            "sectors": "Autolavaggi · Lavanderie · Ristorazione · Pulizie Professionali · Igiene e Sanificanti",
            # Regola utente: NON firmare Badr, ma SELEZIONE
            "signature_signoff": "SELEZIONE — Distribuzione e Vendita Prodotti Professionali",
            "signature_sub": "Rete Forniture Industriali & Detergenza Professionale",
            "collaboration_footer": "In collaborazione con BadrExpress.com",
            "include_badr_name": False,
            "theme_primary_color": "#000000",
            "theme_accent_color": "#facc15", # Oro
            "theme_link_color": "#0284c7"
        }

    elif context == BrandContext.TRASLOCHI:
        return {
            "context": "TRASLOCHI",
            "company_name": "BadrExpress.com & PietroTraslochi.com",
            "full_title": "BadrExpress.com & PietroTraslochi.com · Traslochi & Logistica",
            "slogan": "I Tuoi Partner di Fiducia per Traslochi e Sgomberi a Bologna e in Tutta Italia",
            "badge": "SERVIZIO ESPRESSO H24 · MEZZI CON SPONDA IDRAULICA",
            "sectors": "Traslochi Privati · Sgomberi Aziendali · Smaltimento Certificato · Facchinaggio",
            # Regola utente: "Badr" senza "Ing."
            "signature_signoff": "BadrExpress.com & PietroTraslochi.com",
            "signature_sub": "Badr (+39 388 870 3508) & Pietro (+39 328 426 3554)",
            "collaboration_footer": "",
            "include_badr_name": True,
            "theme_primary_color": "#0f172a",
            "theme_accent_color": "#0ea5e9", # Azzurro
            "theme_link_color": "#16a34a"
        }

    elif context == BrandContext.EBGSTUDIO:
        return {
            "context": "EBGSTUDIO",
            "company_name": "EBGStudio",
            "full_title": "EBGStudio — Autonomous Game & Software Engineering",
            "slogan": "Creators of EBGS Survival MMO (Steam AppID 2886940)",
            "badge": "UNREAL ENGINE 5.8 · STEAMWORKS & EPIC GAMES STORE",
            "sectors": "Game Development · High-Performance Microservices · AI Robotics",
            "signature_signoff": "EBGStudio Team",
            "signature_sub": "Software & Game Publishing Division",
            "collaboration_footer": "",
            "include_badr_name": False,
            "theme_primary_color": "#090d16",
            "theme_accent_color": "#8b5cf6",
            "theme_link_color": "#38bdf8"
        }

    else:
        return {
            "context": "NEUTRAL",
            "company_name": "E.B.J. Autonomous Core",
            "full_title": "E.B.J. AI OS — Executive Management",
            "slogan": "Autonomous Business Intelligence",
            "badge": "SYSTEM 1 READY",
            "sectors": "Multi-Agent Automation",
            "signature_signoff": "E.B.J. Operations",
            "signature_sub": "Autonomous Intelligence",
            "collaboration_footer": "",
            "include_badr_name": False,
            "theme_primary_color": "#111827",
            "theme_accent_color": "#facc15",
            "theme_link_color": "#0284c7"
        }

def format_email_signature_html(context: BrandContext) -> str:
    """
    Genera il blocco firma HTML con le esatte prescrizioni del Brand.
    """
    sig = get_brand_signature(context)
    if context == BrandContext.SELECTION:
        return f"""
        <div style="margin-top: 30px; padding-top: 16px; border-top: 2px solid #facc15; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #475569; line-height: 1.5;">
            <div style="font-size: 14px; font-weight: 900; color: #000000; letter-spacing: 1px;">
                <span style="color: #ca8a04;">S</span>ELEZIONE
            </div>
            <div style="font-weight: 700; color: #334155; font-size: 11px; margin-top: 1px;">
                {sig['slogan']} · {sig['full_title']}
            </div>
            <div style="font-size: 10px; color: #15803d; font-weight: 800; margin-top: 2px;">
                {sig['badge']}
            </div>
            <div style="font-size: 10px; color: #64748b; margin-top: 2px;">
                {sig['sectors']}
            </div>
            <div style="margin-top: 10px; font-size: 10px; color: #0284c7; font-weight: 700; border-top: 1px dashed #cbd5e1; padding-top: 6px;">
                🤝 <i>{sig['collaboration_footer']}</i>
            </div>
        </div>
        """
    elif context == BrandContext.TRASLOCHI:
        return f"""
        <div style="margin-top: 30px; padding-top: 16px; border-top: 2px solid #0284c7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; font-size: 11px; color: #475569; line-height: 1.5;">
            <b style="font-size: 13px; color: #0f172a;">{sig['company_name']}</b><br>
            <span style="color: #64748b;">{sig['slogan']}</span><br>
            <div style="margin-top: 4px; font-weight: bold; color: #0284c7;">
                {sig['signature_sub']}
            </div>
            <div style="font-size: 10px; color: #94a3b8; margin-top: 3px;">
                Siti Web: <a href="https://badrexpress.com" style="color:#0284c7;">badrexpress.com</a> · <a href="https://pietrotraslochi.com" style="color:#0284c7;">pietrotraslochi.com</a>
            </div>
        </div>
        """
    else:
        return f"""
        <div style="margin-top: 20px; padding-top: 10px; border-top: 1px solid #cbd5e1; font-size: 10px; color: #64748b;">
            {sig['signature_signoff']} · {sig['slogan']}
        </div>
        """

def get_filtered_car_washes_for_campaign(city_or_zone: str = "Bologna", exclude_not_interested: bool = True):
    """
    Estrae gli autolavaggi dal database mail_vault.db applicando il filtro intelligente JEV:
    - Se exclude_not_interested=True: esclude categoricamente chi è marcato 'NON_INTERESSATO',
      in modo che la campagna commerciale proceda spedita senza ricontattare chi ha rifiutato.
    - Separa i già forniti per non risollecitarli come nuovi clienti.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
        SELECT id, name, phone, city, address, plant_type, zone, distance, whatsapp_link, notes,
               COALESCE(lead_status, 'DA_CHIAMARE') as lead_status, call_outcome, last_call_at
        FROM b2b_car_washes
        WHERE (city LIKE ? OR zone LIKE ? OR ? = 'ALL')
    """
    params = [f"%{city_or_zone}%", f"%{city_or_zone}%", city_or_zone]

    if exclude_not_interested:
        sql += " AND (lead_status IS NULL OR lead_status != 'NON_INTERESSATO')"

    sql += " ORDER BY CASE WHEN lead_status = 'INTERESSATO' THEN 1 WHEN lead_status = 'GIA_FORNITO_SELECTION' THEN 2 ELSE 3 END, id ASC"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def generate_campaign_closure_summary(city_or_zone: str = "Bologna"):
    """
    Calcola il resoconto completo della campagna per la zona indicata:
    - Quanti contattati
    - Lista degli INTERESSATI (caldi per campionatura/fusti)
    - Lista dei GIÀ FORNITI DA SELECTION FORNITURE
    - Lista dei NON INTERESSATI (archiviati e non più da chiamare)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, phone, city, address, plant_type, zone, distance, notes,
               COALESCE(lead_status, 'DA_CHIAMARE') as lead_status, call_outcome, last_call_at
        FROM b2b_car_washes
        WHERE (city LIKE ? OR zone LIKE ? OR ? = 'ALL')
        ORDER BY id ASC
    """, (f"%{city_or_zone}%", f"%{city_or_zone}%", city_or_zone))
    all_leads = [dict(r) for r in cur.fetchall()]
    conn.close()

    interested = [l for l in all_leads if l['lead_status'] == 'INTERESSATO']
    supplied = [l for l in all_leads if 'GIA_FORNITO' in (l['lead_status'] or '')]
    not_interested = [l for l in all_leads if l['lead_status'] == 'NON_INTERESSATO']
    to_call = [l for l in all_leads if not l['lead_status'] or l['lead_status'] == 'DA_CHIAMARE']

    return {
        "zone": city_or_zone,
        "total": len(all_leads),
        "count_interested": len(interested),
        "count_supplied": len(supplied),
        "count_not_interested": len(not_interested),
        "count_to_call": len(to_call),
        "interested_leads": interested,
        "supplied_leads": supplied,
        "not_interested_leads": not_interested,
        "to_call_leads": to_call,
        "generated_at": datetime.datetime.now().strftime("%d/%m/%Y ore %H:%M")
    }

if __name__ == "__main__":
    # Test di classificazione e signature
    test_queries = [
        "EBJ dammi la lista degli autolavaggi di Bologna con numeri di telefono",
        "Mandami il prospetto per i traslochi e sgomberi",
        "Come va il server del gioco EBGS su Steam?"
    ]
    print("=== TEST JEV BRAND CLASSIFIER ===")
    for q in test_queries:
        ctx = classify_brand_intent(q)
        sig = get_brand_signature(ctx)
        print(f"\nQuery: '{q}'")
        print(f"➔ Brand Context: {ctx.value}")
        print(f"➔ Intestazione: {sig['full_title']}")
        print(f"➔ Firma Ufficiale: {sig['signature_signoff']}")
        if sig['collaboration_footer']:
            print(f"➔ Postilla: {sig['collaboration_footer']}")
