#!/usr/bin/env python3
"""
EBJ Supreme - SELEZIONE PROSPETTO COMMERCIALE & REPORT CHIUSURA AUTOLAVAGGI
Generatore Ufficiale Vettoriale con:
- Branding ufficiale SELEZIONE estratto dal furgone aziendale (Logo & Furgone reale)
- Firma: Rigorosamente SELEZIONE (Azienda Italiana)
- Postilla in fondo: "In collaborazione con BadrExpress.com" (NON firmato Badr)
- Numeri di telefono TUTTI cliccabili con link tel:+39... (avvio chiamata istantanea su smartphone)
- Link WhatsApp one-click diretti
- Pulsanti Esito Chiamata cliccabili direttamente nel PDF e nell'Email:
    * 🟢 INTERESSATO (Richiede campionatura / preventivo fusti)
    * 🔴 NON INTERESSATO (Rifiutato / Non idoneo -> escluso dalle future ricerche)
    * 🟡 GIÀ FORNITO DA SELECTION FORNITURE (Portafoglio clienti attivo)
- Supporto Multi-Città dinamico: Bologna, Milano, Torino, e tutta Italia
- Modalità Prospetto Chiamate vs Modalità Report Chiusura Campagna
- Spedizione PDF via Google SMTP a badraudi@gmail.com
"""

import sys
import os
import re
import json
import sqlite3
import smtplib
import datetime
import base64
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(DIR_PATH, "public")
DB_PATH = os.path.join(DIR_PATH, "mail_vault.db")
GMAIL_USER = "badraudi@gmail.com"
GMAIL_PASS = "kqvjcuzibizysoxu"
DEFAULT_RECIPIENT = "badraudi@gmail.com"

# Endpoint pubblico Cloudflare per registrazione istantanea esiti
SERVER_ENDPOINT = "https://eb.badrexpress.com/api/carwash/outcome"
COCKPIT_URL = "https://eb.badrexpress.com/selezione"

def get_car_washes(city="Bologna", filter_not_interested=True):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    if not city or city.upper() == "ALL":
        sql = """
            SELECT id, name, phone, city, address, plant_type, zone, distance, whatsapp_link, notes, 
                   COALESCE(lead_status, 'DA_CHIAMARE') as lead_status, call_outcome, last_call_at
            FROM b2b_car_washes
        """
        params = []
    else:
        sql = """
            SELECT id, name, phone, city, address, plant_type, zone, distance, whatsapp_link, notes, 
                   COALESCE(lead_status, 'DA_CHIAMARE') as lead_status, call_outcome, last_call_at
            FROM b2b_car_washes
            WHERE (city LIKE ? OR zone LIKE ?)
        """
        params = [f"%{city}%", f"%{city}%"]

    if filter_not_interested:
        clause = " (lead_status IS NULL OR lead_status != 'NON_INTERESSATO')"
        if "WHERE" in sql:
            sql += f" AND {clause}"
        else:
            sql += f" WHERE {clause}"

    sql += " ORDER BY id ASC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_base64_image(filename):
    file_path = os.path.join(DIR_PATH, filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(PUBLIC_DIR, filename)
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        except Exception:
            return ""
    return ""

def generate_selezione_html(items, city="Bologna", is_pdf_version=False):
    now_str = datetime.datetime.now().strftime("%d/%m/%Y ore %H:%M")
    logo_b64 = get_base64_image("selezione_logo_brand.jpg")
    van_b64 = get_base64_image("selezione_van_header.jpg")

    # Raggruppamento per zona
    zones = {}
    for it in items:
        z = it['zone']
        if z not in zones:
            zones[z] = []
        zones[z].append(it)

    html_zones = ""
    for z_title, z_items in zones.items():
        rows_html = ""
        for it in z_items:
            clean_digits = re.sub(r'[^0-9]', '', it['phone'])
            tel_href = f"tel:+39{clean_digits}" if not clean_digits.startswith("39") else f"tel:+{clean_digits}"
            wa_href = f"https://wa.me/39{clean_digits}" if not clean_digits.startswith("39") else f"https://wa.me/{clean_digits}"

            badge_color = "#0ea5e9"
            plant_lower = it['plant_type'].lower()
            if "mano" in plant_lower or "detailing" in plant_lower:
                badge_color = "#22c55e"
            elif "self" in plant_lower or "h24" in plant_lower:
                badge_color = "#d97706"
            elif "servito" in plant_lower:
                badge_color = "#6366f1"

            lead_id = it['id']
            status_text = it.get('lead_status', 'DA_CHIAMARE')
            status_badge = "#64748b"
            status_label = "DA CHIAMARE"
            if status_text == "INTERESSATO": 
                status_badge = "#16a34a"
                status_label = "INTERESSATO"
            elif status_text == "NON_INTERESSATO": 
                status_badge = "#dc2626"
                status_label = "NON INTERESSATO"
            elif "GIA_FORNITO" in status_text: 
                status_badge = "#ca8a04"
                status_label = "GIÀ FORNITO"

            # Pulsanti Esito Chiamata 1-Click (Funzionanti sia in PDF sia in Email)
            outcome_buttons = f"""
            <div style="margin-top: 4px; font-size: 8px; line-height: 1.2;">
                <a href="{SERVER_ENDPOINT}?id={lead_id}&outcome=INTERESSATO" target="_blank" style="display:inline-block; background:#16a34a; color:#ffffff; text-decoration:none; padding:2px 5px; border-radius:3px; font-weight:bold; margin-bottom:2px; white-space:nowrap;">+ INTERESSATO</a><br>
                <a href="{SERVER_ENDPOINT}?id={lead_id}&outcome=NON_INTERESSATO" target="_blank" style="display:inline-block; background:#dc2626; color:#ffffff; text-decoration:none; padding:2px 5px; border-radius:3px; font-weight:bold; margin-bottom:2px; white-space:nowrap;">- NON INT.</a><br>
                <a href="{SERVER_ENDPOINT}?id={lead_id}&outcome=GIA_FORNITO_SELECTION" target="_blank" style="display:inline-block; background:#ca8a04; color:#ffffff; text-decoration:none; padding:2px 5px; border-radius:3px; font-weight:bold; white-space:nowrap;">★ GIÀ FORNITO</a>
            </div>
            """

            rows_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0; page-break-inside: avoid;">
                <td style="padding: 8px 10px; font-weight: bold; color: #0f172a; vertical-align: top;">
                    {it['name']}
                    <div style="font-size: 10px; color: #64748b; font-weight: normal; margin-top: 2px;">{it['notes']}</div>
                </td>
                <td style="padding: 8px 10px; white-space: nowrap; vertical-align: top;">
                    <!-- TELEFONO CLICCABILE SUBITO PER AVVIARE CHIAMATA -->
                    <a href="{tel_href}" style="display: inline-block; background: #0284c7; color: #ffffff; text-decoration: none; padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); margin-bottom: 3px;">
                        📞 {it['phone']}
                    </a>
                    <br>
                    <a href="{wa_href}" target="_blank" style="display: inline-block; color: #16a34a; text-decoration: none; font-size: 10px; font-weight: bold; margin-left: 2px;">
                        💬 WhatsApp
                    </a>
                </td>
                <td style="padding: 8px 10px; color: #334155; font-size: 11px; vertical-align: top;">{it['address']}</td>
                <td style="padding: 8px 10px; text-align: center; vertical-align: top;">
                    <span style="display: inline-block; background: {badge_color}; color: white; padding: 3px 6px; border-radius: 3px; font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
                        {it['plant_type']}
                    </span>
                </td>
                <td style="padding: 8px 10px; font-weight: bold; color: #475569; text-align: right; white-space: nowrap; vertical-align: top;">
                    {it['distance']}
                </td>
                <td style="padding: 8px 10px; text-align: center; white-space: nowrap; vertical-align: top;">
                    <span style="display: inline-block; background: {status_badge}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold;">
                        {status_label}
                    </span>
                    {outcome_buttons}
                </td>
            </tr>
            """

        html_zones += f"""
        <div style="margin-top: 15px; margin-bottom: 12px; page-break-inside: avoid;">
            <div style="background: linear-gradient(90deg, #111827 0%, #1f2937 100%); color: #facc15; padding: 6px 12px; border-radius: 6px 6px 0 0; font-weight: 800; font-size: 11px; letter-spacing: 0.5px; border-left: 4px solid #facc15;">
                📍 {z_title}
            </div>
            <table style="width: 100%; border-collapse: collapse; background: #ffffff; border: 1px solid #cbd5e1; border-top: none; font-size: 11px;">
                <thead>
                    <tr style="background: #f8fafc; color: #64748b; text-align: left; border-bottom: 2px solid #e2e8f0; font-size: 10px; text-transform: uppercase;">
                        <th style="padding: 6px 10px;">Nome Ditta / Lavaggio</th>
                        <th style="padding: 6px 10px;">Chiamata Rapida (Click)</th>
                        <th style="padding: 6px 10px;">Località / Indirizzo</th>
                        <th style="padding: 6px 10px; text-align: center;">Tipo Impianto</th>
                        <th style="padding: 6px 10px; text-align: right;">Distanza</th>
                        <th style="padding: 6px 10px; text-align: center;">Stato / Segna Esito</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """

    logo_img_tag = f'<img src="{logo_b64}" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #facc15; object-fit: cover; background: #fff; margin-right: 12px;" alt="Logo">' if logo_b64 else ''
    van_img_tag = f'<img src="{van_b64}" style="height: 52px; border-radius: 6px; border: 1px solid #3f3f46; object-fit: cover;" alt="Furgone SELEZIONE">' if van_b64 else ''

    full_html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>SELEZIONE — Prospetto Commerciale Autolavaggi {city}</title>
        <style>
            @page {{
                size: A4 portrait;
                margin: 8mm 8mm 10mm 8mm;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: { '0' if is_pdf_version else '16px' };
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .container {{
                max-width: 960px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                overflow: hidden;
                border: 1px solid #cbd5e1;
            }}
            a {{ text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            
            <!-- HEADER BRANDIZZATO SELEZIONE DAL FURGONE UFFICIALE -->
            <div style="background: #000000; padding: 18px 22px; color: #ffffff; border-bottom: 4px solid #facc15;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center;">
                        {logo_img_tag}
                        <div>
                            <div style="font-size: 26px; font-weight: 900; letter-spacing: 2px; color: #ffffff; line-height: 1;">
                                <span style="color: #facc15;">S</span>ELEZIONE
                            </div>
                            <div style="font-size: 10px; font-weight: 700; color: #e2e8f0; letter-spacing: 1.5px; margin-top: 2px;">
                                LA SCELTA CHE FA LA DIFFERENZA
                            </div>
                            <div style="font-size: 11px; font-weight: 600; color: #facc15; margin-top: 4px; letter-spacing: 0.5px;">
                                DISTRIBUZIONE E VENDITA PRODOTTI PROFESSIONALI
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; text-align: right;">
                        {van_img_tag}
                        <div style="background: #18181b; border: 1px solid #3f3f46; border-radius: 6px; padding: 6px 12px;">
                            <div style="color: #86efac; font-size: 10px; font-weight: 800;">🇮🇹 AZIENDA ITALIANA</div>
                            <div style="color: #38bdf8; font-size: 12px; font-weight: 800;">AUTOLAVAGGI & DETAILING</div>
                            <div style="color: #facc15; font-size: 9px; font-weight: bold; margin-top: 1px;">PRODOTTI 100% ITALIANI</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KPI BOX PROSPETTO -->
            <div style="display: flex; background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 10px 22px; gap: 12px; font-size: 11px;">
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; font-size: 9px;">AREA TARGET</span>
                    <b style="color: #0f172a; font-size: 12px;">{city.upper()} & HINTERLAND</b>
                </div>
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; font-size: 9px;">IMPIANTI ATTIVI</span>
                    <b style="color: #0f172a; font-size: 12px;">{len(items)} Censiti</b>
                </div>
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; font-size: 9px;">PRODOTTI CHIMICI</span>
                    <b style="color: #0284c7; font-size: 12px;">Schiuma Attiva, Cere, Cerchi</b>
                </div>
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; font-size: 9px;">AGGIORNAMENTO</span>
                    <b style="color: #334155; font-size: 12px;">{now_str}</b>
                </div>
            </div>

            <!-- LINK ACCESSO COCKPIT MOBILE CRM -->
            <div style="background: #eff6ff; border-bottom: 1px solid #bfdbfe; padding: 8px 22px; font-size: 11px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #1e40af;">
                    📱 <b>Cockpit Interattivo Mobile:</b> Gestisci chiamate ed esiti in tempo reale su smartphone.
                </span>
                <a href="{COCKPIT_URL}" target="_blank" style="background: #0284c7; color: #fff; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px;">
                    Apri CRM Mobile ➔
                </a>
            </div>

            <!-- CORPO TABELLARE -->
            <div style="padding: 14px 20px;">
                <div style="background: #fefce8; border: 1px solid #fde047; border-left: 4px solid #eab308; padding: 8px 12px; border-radius: 4px; font-size: 11px; color: #854d0e; margin-bottom: 12px;">
                    <b>Istruzioni Rapide Operatore:</b><br>
                    1. Tocca il tasto blu con il numero per <b>avviare la chiamata telefonica istantanea</b> dallo smartphone.<br>
                    2. Al termine della chiamata, tocca subito uno dei 3 tasti esito: <b>+ INTERESSATO</b>, <b>- NON INT.</b>, oppure <b>★ GIÀ FORNITO</b> per registrare il dato direttamente nel sistema.<br>
                    <i>Nota: Chi viene marcato 'Non Interessato' verrà automaticamente escluso dai futuri prospetti per procedere spediti con tutta Italia.</i>
                </div>

                {html_zones}

                <!-- NOTE TECNICHE PRODOTTI CHIMICI -->
                <div style="margin-top: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #0284c7; border-radius: 6px; padding: 10px 14px; font-size: 10px; line-height: 1.4; color: #334155; page-break-inside: avoid;">
                    <b style="color: #0f172a; font-size: 11px;">🧪 Linea Guida Proposta Chimica SELEZIONE (Made in Italy):</b><br>
                    • <b>Piste Self & H24:</b> Fusti 25kg di detergente monocomponente ad alta schiuma e cera nanotech superidrofobica.<br>
                    • <b>Lavaggio a Mano & Detailing:</b> Sgrassatore cerchi alcalino, decontaminante ferrosi pH neutro, nero gomme a lunga durata.<br>
                    • <b>Campionatura:</b> Offrire tanica campione prova da 5kg con test di diluizione direttamente presso l'impianto del cliente.
                </div>
            </div>

            <!-- FOOTER UFFICIALE SELEZIONE (NON FIRMATO BADR - FIRMATO SELEZIONE CON COLLABORAZIONE IN CALCE) -->
            <div style="background: #000000; padding: 14px 20px; font-size: 10px; color: #94a3b8; border-top: 2px solid #facc15; text-align: center;">
                <b style="color: #ffffff; font-size: 11px;">SELEZIONE — Distribuzione e Vendita Prodotti Professionali</b><br>
                Autolavaggi · Lavanderie · Ristorazione · Pulizie Professionali · Igiene e Sanificanti<br>
                🇮🇹 <b>Azienda Italiana — Selezione e Vendita Prodotti 100% Made in Italy</b>
                <div style="margin-top: 6px; color: #facc15; font-size: 10px; font-weight: bold; border-top: 1px dashed #3f3f46; padding-top: 6px;">
                    🤝 In collaborazione con BadrExpress.com
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return full_html

def generate_closure_report_html(city="Bologna", is_pdf_version=False):
    """
    Genera il Report Riassuntivo di Chiusura Zona per SELEZIONE:
    - Evidenzia gli INTERESSATI (caldi per campionatura / preventivo fusti)
    - Elenca i GIÀ FORNITI DA SELECTION FORNITURE
    - Riassume i NON INTERESSATI esclusi per il prosieguo della campagna nazionale
    - Rigorosamente firmato SELEZIONE, con 'In collaborazione con BadrExpress.com' in calce.
    """
    now_str = datetime.datetime.now().strftime("%d/%m/%Y ore %H:%M")
    logo_b64 = get_base64_image("selezione_logo_brand.jpg")
    van_b64 = get_base64_image("selezione_van_header.jpg")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, phone, city, address, plant_type, zone, distance, notes,
               COALESCE(lead_status, 'DA_CHIAMARE') as lead_status, call_outcome, last_call_at
        FROM b2b_car_washes
        WHERE (city LIKE ? OR zone LIKE ? OR ? = 'ALL')
        ORDER BY id ASC
    """, (f"%{city}%", f"%{city}%", city))
    all_leads = [dict(r) for r in cur.fetchall()]
    conn.close()

    interested = [l for l in all_leads if l['lead_status'] == 'INTERESSATO']
    supplied = [l for l in all_leads if 'GIA_FORNITO' in (l['lead_status'] or '')]
    not_interested = [l for l in all_leads if l['lead_status'] == 'NON_INTERESSATO']
    to_call = [l for l in all_leads if not l['lead_status'] or l['lead_status'] == 'DA_CHIAMARE']

    # Righe Interessati
    rows_interested = ""
    for it in interested:
        clean_d = re.sub(r'[^0-9]', '', it['phone'])
        t_href = f"tel:+39{clean_d}" if not clean_d.startswith("39") else f"tel:+{clean_d}"
        rows_interested += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 10px; font-weight: bold; color: #166534;">{it['name']}</td>
            <td style="padding: 8px 10px;">
                <a href="{t_href}" style="color: #0284c7; font-weight: bold; text-decoration: none;">📞 {it['phone']}</a>
            </td>
            <td style="padding: 8px 10px; color: #334155;">{it['address']} ({it['zone']})</td>
            <td style="padding: 8px 10px; text-align: center;"><span style="background: #22c55e; color: #fff; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold;">{it['plant_type']}</span></td>
            <td style="padding: 8px 10px; font-size: 10px; color: #475569;">{it['notes']}</td>
        </tr>
        """
    if not rows_interested:
        rows_interested = '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #94a3b8;">Nessun autolavaggio ancora segnato come interessato in questa sessione.</td></tr>'

    # Righe Già Forniti
    rows_supplied = ""
    for it in supplied:
        clean_d = re.sub(r'[^0-9]', '', it['phone'])
        t_href = f"tel:+39{clean_d}" if not clean_d.startswith("39") else f"tel:+{clean_d}"
        rows_supplied += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 10px; font-weight: bold; color: #854d0e;">{it['name']}</td>
            <td style="padding: 8px 10px;">
                <a href="{t_href}" style="color: #0284c7; font-weight: bold; text-decoration: none;">📞 {it['phone']}</a>
            </td>
            <td style="padding: 8px 10px; color: #334155;">{it['address']} ({it['zone']})</td>
            <td style="padding: 8px 10px; text-align: center;"><span style="background: #ca8a04; color: #fff; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold;">{it['plant_type']}</span></td>
            <td style="padding: 8px 10px; font-size: 10px; color: #475569;">Cliente Attivo Selection</td>
        </tr>
        """
    if not rows_supplied:
        rows_supplied = '<tr><td colspan="5" style="padding: 12px; text-align: center; color: #94a3b8;">Nessun cliente censito precedentemente come già fornito.</td></tr>'

    logo_img_tag = f'<img src="{logo_b64}" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #facc15; object-fit: cover; background: #fff; margin-right: 12px;" alt="Logo">' if logo_b64 else ''
    van_img_tag = f'<img src="{van_b64}" style="height: 52px; border-radius: 6px; border: 1px solid #3f3f46; object-fit: cover;" alt="Furgone SELEZIONE">' if van_b64 else ''

    closure_html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>SELEZIONE — Report Chiusura Campagna {city}</title>
        <style>
            @page {{
                size: A4 portrait;
                margin: 8mm 8mm 10mm 8mm;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: { '0' if is_pdf_version else '16px' };
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .container {{
                max-width: 960px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                overflow: hidden;
                border: 1px solid #cbd5e1;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- HEADER BRANDIZZATO SELEZIONE -->
            <div style="background: #000000; padding: 18px 22px; color: #ffffff; border-bottom: 4px solid #facc15;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center;">
                        {logo_img_tag}
                        <div>
                            <div style="font-size: 24px; font-weight: 900; letter-spacing: 2px; color: #ffffff;">
                                <span style="color: #facc15;">S</span>ELEZIONE
                            </div>
                            <div style="font-size: 10px; font-weight: 700; color: #e2e8f0; letter-spacing: 1.5px; margin-top: 2px;">
                                REPORT ESECUTIVO CHIUSURA CAMPAGNA
                            </div>
                            <div style="font-size: 11px; font-weight: 600; color: #facc15; margin-top: 4px;">
                                DISTRIBUZIONE E VENDITA PRODOTTI PROFESSIONALI
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 12px; text-align: right;">
                        {van_img_tag}
                        <div style="background: #18181b; border: 1px solid #3f3f46; border-radius: 6px; padding: 6px 12px;">
                            <div style="color: #86efac; font-size: 10px; font-weight: 800;">🇮🇹 AZIENDA ITALIANA</div>
                            <div style="color: #facc15; font-size: 12px; font-weight: 800;">{city.upper()}</div>
                            <div style="color: #94a3b8; font-size: 9px; margin-top: 1px;">{now_str}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- KPI BOX ESITI -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 14px 22px; gap: 12px; text-align: center;">
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px;">
                    <div style="font-size: 20px; font-weight: 900; color: #0f172a;">{len(all_leads)}</div>
                    <div style="font-size: 10px; font-weight: bold; color: #64748b; text-transform: uppercase;">Totale Contatti</div>
                </div>
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px;">
                    <div style="font-size: 20px; font-weight: 900; color: #16a34a;">{len(interested)}</div>
                    <div style="font-size: 10px; font-weight: bold; color: #15803d; text-transform: uppercase;">🟢 Interessati (Lead Caldi)</div>
                </div>
                <div style="background: #fefce8; border: 1px solid #fef08a; border-radius: 8px; padding: 10px;">
                    <div style="font-size: 20px; font-weight: 900; color: #ca8a04;">{len(supplied)}</div>
                    <div style="font-size: 10px; font-weight: bold; color: #854d0e; text-transform: uppercase;">★ Già Forniti Selection</div>
                </div>
                <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 10px;">
                    <div style="font-size: 20px; font-weight: 900; color: #ef4444;">{len(not_interested)}</div>
                    <div style="font-size: 10px; font-weight: bold; color: #b91c1c; text-transform: uppercase;">🔴 Non Interessati (Esclusi)</div>
                </div>
            </div>

            <div style="padding: 16px 20px;">
                <!-- SEZIONE 1: INTERESSATI PER ORDINI / CAMPIONATURA -->
                <div style="margin-bottom: 20px;">
                    <div style="background: #14532d; color: #86efac; padding: 6px 12px; border-radius: 6px 6px 0 0; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;">
                        🟢 AUTOLAVAGGI INTERESSATI — PRIORITÀ CONSEGNA CAMPIONI E LISTINO FUSTI
                    </div>
                    <table style="width: 100%; border-collapse: collapse; background: #ffffff; border: 1px solid #cbd5e1; border-top: none; font-size: 11px;">
                        <thead>
                            <tr style="background: #f0fdf4; color: #166534; text-align: left; font-size: 10px; text-transform: uppercase; border-bottom: 2px solid #bbf7d0;">
                                <th style="padding: 6px 10px;">Nome Impianto</th>
                                <th style="padding: 6px 10px;">Recapito Chiamata</th>
                                <th style="padding: 6px 10px;">Indirizzo & Zona</th>
                                <th style="padding: 6px 10px; text-align: center;">Tipologia</th>
                                <th style="padding: 6px 10px;">Note Prodotto</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_interested}
                        </tbody>
                    </table>
                </div>

                <!-- SEZIONE 2: CLIENTI GIÀ FORNITI -->
                <div style="margin-bottom: 20px;">
                    <div style="background: #713f12; color: #fde047; padding: 6px 12px; border-radius: 6px 6px 0 0; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;">
                        ★ CLIENTI GIÀ FORNITI DA SELECTION FORNITURE (PORTAFOGLIO ATTIVO)
                    </div>
                    <table style="width: 100%; border-collapse: collapse; background: #ffffff; border: 1px solid #cbd5e1; border-top: none; font-size: 11px;">
                        <thead>
                            <tr style="background: #fefce8; color: #854d0e; text-align: left; font-size: 10px; text-transform: uppercase; border-bottom: 2px solid #fef08a;">
                                <th style="padding: 6px 10px;">Nome Impianto</th>
                                <th style="padding: 6px 10px;">Recapito</th>
                                <th style="padding: 6px 10px;">Indirizzo & Zona</th>
                                <th style="padding: 6px 10px; text-align: center;">Tipologia</th>
                                <th style="padding: 6px 10px;">Stato Fornitura</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_supplied}
                        </tbody>
                    </table>
                </div>

                <!-- NOTA LOGISTICA SUI NON INTERESSATI -->
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #ef4444; border-radius: 6px; padding: 10px 14px; font-size: 11px; color: #334155;">
                    <b>Regola di Gestione Esiti & Avanzamento Nazionale:</b><br>
                    I <b>{len(not_interested)} autolavaggi</b> che hanno risposto <i>"Non Interessato"</i> sono stati definitivamente archiviati in <code>mail_vault.db</code>. 
                    Nelle successive ricerche e nelle campagne commerciali sulle città confinanti, il sistema <b>li escluderà in automatico</b> per concentrare l'energia commerciale solo su contatti freschi e ricettivi in tutta Italia.
                </div>
            </div>

            <!-- FOOTER UFFICIALE SELEZIONE -->
            <div style="background: #000000; padding: 14px 20px; font-size: 10px; color: #94a3b8; border-top: 2px solid #facc15; text-align: center;">
                <b style="color: #ffffff; font-size: 11px;">SELEZIONE — Distribuzione e Vendita Prodotti Professionali</b><br>
                Autolavaggi · Lavanderie · Ristorazione · Pulizie Professionali · Igiene e Sanificanti<br>
                🇮🇹 <b>Azienda Italiana — Selezione e Vendita Prodotti 100% Made in Italy</b>
                <div style="margin-top: 6px; color: #facc15; font-size: 10px; font-weight: bold; border-top: 1px dashed #3f3f46; padding-top: 6px;">
                    🤝 In collaborazione con BadrExpress.com
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return closure_html

async def build_pdf_with_playwright(html_content, output_pdf_path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(
            path=output_pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "6mm", "bottom": "8mm", "left": "6mm", "right": "6mm"}
        )
        await browser.close()
    print(f"[PDF] PDF generato con successo in: {output_pdf_path}")

    # Copia anche nella cartella public per download web
    public_target = os.path.join(PUBLIC_DIR, os.path.basename(output_pdf_path))
    try:
        shutil.copyfile(output_pdf_path, public_target)
        print(f"[PDF] Copiato in public per accesso web: {public_target}")
    except Exception as e:
        print(f"[WARN] Impossibile copiare in public: {e}")

def send_selezione_email(recipient, subject, html_content, pdf_path=None):
    print(f"[*] Connessione a Google SMTP per invio dossier SELEZIONE...")
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"SELEZIONE Forniture <{GMAIL_USER}>"
    msg["To"] = recipient

    # Corpo HTML
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    # Allegato PDF con numeri cliccabili
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_attach = MIMEBase("application", "pdf")
            pdf_attach.set_payload(f.read())
            encoders.encode_base64(pdf_attach)
            filename = os.path.basename(pdf_path)
            pdf_attach.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(pdf_attach)
            print(f"[*] Allegato PDF {filename} incluso nel messaggio.")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=25)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, recipient, msg.as_string())
        server.quit()
        print(f"[SUCCESS] Email SELEZIONE spedita con successo a {recipient}!")
        return True
    except Exception as e:
        print(f"[ERROR] Invio email fallito: {e}")
        return False

def update_lead_outcome(lead_id, outcome):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now_ts = datetime.datetime.now().isoformat()
    cur.execute("""
        UPDATE b2b_car_washes 
        SET lead_status = ?, call_outcome = ?, last_call_at = ?
        WHERE id = ?
    """, (outcome, outcome, now_ts, lead_id))
    conn.commit()
    conn.close()
    print(f"[DB] Lead #{lead_id} aggiornato a stato: {outcome}")

if __name__ == "__main__":
    import asyncio

    # Controllo se chiamato per aggiornare esito
    if len(sys.argv) >= 3 and sys.argv[1] == "--set-outcome":
        lid = int(sys.argv[2])
        outc = sys.argv[3]
        update_lead_outcome(lid, outc)
        sys.exit(0)

    is_closure_report = "--report-chiusura" in sys.argv or "-report" in sys.argv
    args_cleaned = [a for a in sys.argv[1:] if not a.startswith("--report") and not a.startswith("-report")]

    target_city = args_cleaned[0] if len(args_cleaned) > 0 else "Bologna"
    target_email = args_cleaned[1] if len(args_cleaned) > 1 else DEFAULT_RECIPIENT

    print("=" * 70)
    print("   SELEZIONE — DISTRIBUZIONE E VENDITA PRODOTTI PROFESSIONALI   ")
    mode_label = "Report Chiusura Campagna" if is_closure_report else "Prospetto Chiamate Commerciali"
    print(f"   {mode_label} ({target_city})")
    print("=" * 70)

    if is_closure_report:
        # Generazione Report Chiusura Campagna
        email_html = generate_closure_report_html(target_city, is_pdf_version=False)
        pdf_html = generate_closure_report_html(target_city, is_pdf_version=True)
        pdf_output_path = os.path.join(DIR_PATH, f"SELEZIONE_Report_Chiusura_Autolavaggi_{target_city}.pdf")
        asyncio.run(build_pdf_with_playwright(pdf_html, pdf_output_path))
        subj = f"📊 SELEZIONE — Report Riassuntivo Chiusura Autolavaggi {target_city} (Clienti Caldi & Esiti)"
        send_selezione_email(target_email, subj, email_html, pdf_path=pdf_output_path)
    else:
        # Generazione Prospetto Chiamate Attive (escludendo i Non Interessati)
        items = get_car_washes(target_city, filter_not_interested=True)
        print(f"[*] Caricati {len(items)} autolavaggi attivi dal database per {target_city}.")

        email_html = generate_selezione_html(items, city=target_city, is_pdf_version=False)
        pdf_html = generate_selezione_html(items, city=target_city, is_pdf_version=True)
        pdf_output_path = os.path.join(DIR_PATH, f"SELEZIONE_Prospetto_Autolavaggi_{target_city}.pdf")
        asyncio.run(build_pdf_with_playwright(pdf_html, pdf_output_path))
        subj = f"📋 SELEZIONE — Prospetto Commerciale Autolavaggi {target_city} (PDF con Chiamata Diretta & Esiti)"
        send_selezione_email(target_email, subj, email_html, pdf_path=pdf_output_path)
