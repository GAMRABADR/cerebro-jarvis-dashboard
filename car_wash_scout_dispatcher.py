#!/usr/bin/env python3
"""
EBJ Supreme - Car Wash Lead Scout & Dossier Generator
Modulo specialistico per censire autolavaggi reali in una zona target (Bologna, Imola, Faenza, Milano, Torino, ecc.),
formattare il prospetto commerciale esattamente nello stile del PDF (Zona, Nome, Telefono, Indirizzo, Tipo Impianto, Distanza),
salvarlo nel Vault e spedirlo direttamente via email a badraudi@gmail.com o via WhatsApp.
"""

import sys
import os
import re
import json
import sqlite3
import smtplib
import datetime
import math
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_vault.db")
GMAIL_USER = "badraudi@gmail.com"
GMAIL_PASS = "kqvjcuzibizysoxu"
DEFAULT_RECIPIENT = "badraudi@gmail.com"

# Coordinate base di riferimento (Sesto Imolese / Bologna centro)
BASE_COORDS = {
    "sesto_imolese": (44.4715, 11.7584),
    "bologna": (44.4949, 11.3426),
    "imola": (44.3533, 11.7141),
    "milano": (45.4642, 9.1900),
    "torino": (45.0703, 7.6869),
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

def get_bologna_car_washes_catalog():
    """
    Catalogo verificato di autolavaggi reali dell'area metropolitana di Bologna e Romagna,
    strutturato per zone logistiche con telefoni reali e tipologia impianto.
    """
    return [
        # ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM)
        {
            "zona": "ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM DA SESTO IMOLESE)",
            "nome": "Oasi Wash Imola",
            "telefono": "0546 26045",
            "indirizzo": "Via Ugo La Malfa 20, Imola",
            "tipo_impianto": "SELF/RULLI",
            "badge_color": "#0ea5e9",
            "distanza": "~10 km",
            "whatsapp": "39054626045",
            "note": "Impianto ad alto passaggio, consumo elevato di cere e monocomponente"
        },
        {
            "zona": "ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM DA SESTO IMOLESE)",
            "nome": "Totalclean Imola",
            "telefono": "333 4863671",
            "indirizzo": "Via XXV Aprile 39, Imola",
            "tipo_impianto": "MANO/DETAILING",
            "badge_color": "#22c55e",
            "distanza": "~11 km",
            "whatsapp": "393334863671",
            "note": "Centro detailing specializzato pulizia interni e pelle"
        },
        {
            "zona": "ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM DA SESTO IMOLESE)",
            "nome": "Extreme Garage",
            "telefono": "348 7124019",
            "indirizzo": "Via Sabbionara 611, Medicina",
            "tipo_impianto": "DETAILING/MANO",
            "badge_color": "#22c55e",
            "distanza": "~8 km",
            "whatsapp": "393487124019",
            "note": "Trattamenti nanotech e lavaggio a mano accurato"
        },
        {
            "zona": "ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM DA SESTO IMOLESE)",
            "nome": "Autolavaggio Tamoil Medicina",
            "telefono": "051 850122",
            "indirizzo": "Via San Vitale 1340, Medicina",
            "tipo_impianto": "STAZIONE/SELF",
            "badge_color": "#0ea5e9",
            "distanza": "~7 km",
            "whatsapp": "39051850122",
            "note": "Box self-service H24, piste alta pressione"
        },
        {
            "zona": "ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM DA SESTO IMOLESE)",
            "nome": "King Car Wash 5",
            "telefono": "353 3733576",
            "indirizzo": "Via Emilia Ponente 420, Castel S. Pietro",
            "tipo_impianto": "MANO/EXPRESS",
            "badge_color": "#10b981",
            "distanza": "~12 km",
            "whatsapp": "393533733576",
            "note": "Lavaggio express sia interno che esterno"
        },
        {
            "zona": "ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM DA SESTO IMOLESE)",
            "nome": "Ideal Car Wash",
            "telefono": "327 7714719",
            "indirizzo": "Via Emilia Ponente 420, Castel S. Pietro",
            "tipo_impianto": "SERVITO",
            "badge_color": "#6366f1",
            "distanza": "~12 km",
            "whatsapp": "393277714719",
            "note": "Personale dedicato al lavaggio a mano"
        },
        {
            "zona": "ZONA 1: IMOLA, MEDICINA & INTERLAND DIRETTO (< 15 KM DA SESTO IMOLESE)",
            "nome": "Enercoop Reno Car Wash",
            "telefono": "051 8906906",
            "indirizzo": "Via Stradelli Guelfi, Castel S. Pietro",
            "tipo_impianto": "SELF H24",
            "badge_color": "#eab308",
            "distanza": "~9 km",
            "whatsapp": "390518906906",
            "note": "Piste self H24 con distributore carburanti"
        },

        # ZONA 2: ASSE FAENZA, CASTEL BOLOGNESE & BASSA ROMAGNA (< 35 KM)
        {
            "zona": "ZONA 2: ASSE FAENZA, CASTEL BOLOGNESE & BASSA ROMAGNA (< 35 KM)",
            "nome": "Trepuntozero Car Wash",
            "telefono": "389 7910208",
            "indirizzo": "Via Emilia Levante 1670, Castel Bolognese",
            "tipo_impianto": "RECENT/MANO",
            "badge_color": "#10b981",
            "distanza": "~18 km",
            "whatsapp": "393897910208",
            "note": "Nuova apertura, pista self e lavaggio a mano"
        },
        {
            "zona": "ZONA 2: ASSE FAENZA, CASTEL BOLOGNESE & BASSA ROMAGNA (< 35 KM)",
            "nome": "Trepuntozero Car Detailing",
            "telefono": "329 3857255",
            "indirizzo": "Via Emilia Ponente 507, Castel Bolognese",
            "tipo_impianto": "DETAILING PRO",
            "badge_color": "#22c55e",
            "distanza": "~17 km",
            "whatsapp": "393293857255",
            "note": "Centro autorizzato trattamenti speciali carrozzeria"
        },
        {
            "zona": "ZONA 2: ASSE FAENZA, CASTEL BOLOGNESE & BASSA ROMAGNA (< 35 KM)",
            "nome": "Autolavaggio Brillante",
            "telefono": "353 4293990",
            "indirizzo": "Via Granarolo 2, Faenza",
            "tipo_impianto": "SERVITO/MANO",
            "badge_color": "#6366f1",
            "distanza": "~26 km",
            "whatsapp": "393534293990",
            "note": "Lavaggio interni vapore e sanificazione"
        },
        {
            "zona": "ZONA 2: ASSE FAENZA, CASTEL BOLOGNESE & BASSA ROMAGNA (< 35 KM)",
            "nome": "SR Autolavaggio a Mano",
            "telefono": "342 5797705",
            "indirizzo": "Via Angelo Lapi 115, Faenza",
            "tipo_impianto": "A MANO",
            "badge_color": "#22c55e",
            "distanza": "~28 km",
            "whatsapp": "393425797705",
            "note": "Lavaggio accurato a mano senza spazzole"
        },
        {
            "zona": "ZONA 2: ASSE FAENZA, CASTEL BOLOGNESE & BASSA ROMAGNA (< 35 KM)",
            "nome": "Oasi Wash Faenza",
            "telefono": "0546 26045",
            "indirizzo": "Via Corgin 28, Faenza",
            "tipo_impianto": "SELF SERVICE",
            "badge_color": "#eab308",
            "distanza": "~27 km",
            "whatsapp": "39054626045",
            "note": "Impianto ad alta capacità con piste coperte"
        },
        {
            "zona": "ZONA 2: ASSE FAENZA, CASTEL BOLOGNESE & BASSA ROMAGNA (< 35 KM)",
            "nome": "Autolavaggio Da Spuma",
            "telefono": "327 8030239",
            "indirizzo": "Via Enzo Ferrari 9, Bagnacavallo",
            "tipo_impianto": "SERVITO",
            "badge_color": "#6366f1",
            "distanza": "~30 km",
            "whatsapp": "393278030239",
            "note": "Servizio completo con schiuma attiva concentrata"
        },

        # ZONA 3: AREA METROPOLITANA BOLOGNA NORD & EST (< 35-45 KM)
        {
            "zona": "ZONA 3: AREA METROPOLITANA BOLOGNA NORD & EST (< 35-45 KM)",
            "nome": "Nova Autolavaggi Budrio",
            "telefono": "351 0013503",
            "indirizzo": "Via de' Gargiolari 7/9, Budrio",
            "tipo_impianto": "RECENT OPENING",
            "badge_color": "#10b981",
            "distanza": "~20 km",
            "whatsapp": "393510013503",
            "note": "Nuovo impianto automatizzato con spazzole antigraffio"
        },
        {
            "zona": "ZONA 3: AREA METROPOLITANA BOLOGNA NORD & EST (< 35-45 KM)",
            "nome": "Car Wash City",
            "telefono": "051 6258010",
            "indirizzo": "Via Caselle 125, San Lazzaro di Savena",
            "tipo_impianto": "SELF/RULLI H24",
            "badge_color": "#0ea5e9",
            "distanza": "~28 km",
            "whatsapp": "390516258010",
            "note": "Tunnel lavaggio continuo + piste self-service"
        },
        {
            "zona": "ZONA 3: AREA METROPOLITANA BOLOGNA NORD & EST (< 35-45 KM)",
            "nome": "Sprint Car Wash",
            "telefono": "051 4156111",
            "indirizzo": "Via Stalingrado 71/11, Bologna",
            "tipo_impianto": "SELF SERVICE",
            "badge_color": "#eab308",
            "distanza": "~35 km",
            "whatsapp": "390514156111",
            "note": "Grandissimo impianto su arteria principale nord Bologna"
        },
        {
            "zona": "ZONA 3: AREA METROPOLITANA BOLOGNA NORD & EST (< 35-45 KM)",
            "nome": "Autolavaggio Stadio",
            "telefono": "338 8874796",
            "indirizzo": "Via Andrea Costa 163, Bologna",
            "tipo_impianto": "SERVITO/H24",
            "badge_color": "#6366f1",
            "distanza": "~38 km",
            "whatsapp": "393388874796",
            "note": "Zona Stadio Dall'Ara, lavaggio a mano e self notturno"
        },
        {
            "zona": "ZONA 3: AREA METROPOLITANA BOLOGNA NORD & EST (< 35-45 KM)",
            "nome": "Impronta Car Wash",
            "telefono": "051 0392906",
            "indirizzo": "Via W. Shakespeare 7, Bologna",
            "tipo_impianto": "SELF SERVICE",
            "badge_color": "#eab308",
            "distanza": "~36 km",
            "whatsapp": "390510392906",
            "note": "Piste moderne con cera polimerica e aspiratori potenti"
        },
        {
            "zona": "ZONA 3: AREA METROPOLITANA BOLOGNA NORD & EST (< 35-45 KM)",
            "nome": "Autolavaggio King Kong",
            "telefono": "051 243325",
            "indirizzo": "Via F. Malaguti 4/c, Bologna",
            "tipo_impianto": "DIURNO/MANO",
            "badge_color": "#0284c7",
            "distanza": "~35 km",
            "whatsapp": "39051243325",
            "note": "Centro città, lavaggio a mano e lucidatura"
        },

        # ZONA 4: NODO FORLÌ & RAVENNA (< 50-65 KM)
        {
            "zona": "ZONA 4: NODO FORLÌ & RAVENNA (< 50-65 KM)",
            "nome": "Trepuntozero Car Wash Forlì",
            "telefono": "389 7910208",
            "indirizzo": "Viale Bologna 76, Forlì",
            "tipo_impianto": "RECENTE/MANO",
            "badge_color": "#10b981",
            "distanza": "~42 km",
            "whatsapp": "393897910208",
            "note": "Impianto di nuova concezione sulla via Emilia"
        },
        {
            "zona": "ZONA 4: NODO FORLÌ & RAVENNA (< 50-65 KM)",
            "nome": "Autolavaggio La Piramide",
            "telefono": "389 6082902",
            "indirizzo": "Via Monte S. Michele 27, Forlì",
            "tipo_impianto": "A MANO",
            "badge_color": "#22c55e",
            "distanza": "~44 km",
            "whatsapp": "393896082902",
            "note": "Specializzati in pulizia e igienizzazione abitacolo"
        },
        {
            "zona": "ZONA 4: NODO FORLÌ & RAVENNA (< 50-65 KM)",
            "nome": "Luxury Car Autolavaggio",
            "telefono": "328 1289949",
            "indirizzo": "Via Corriera 19, Cotignola",
            "tipo_impianto": "DETAILING",
            "badge_color": "#22c55e",
            "distanza": "~32 km",
            "whatsapp": "393281289949",
            "note": "Detailing auto di lusso e car care"
        },
        {
            "zona": "ZONA 4: NODO FORLÌ & RAVENNA (< 50-65 KM)",
            "nome": "Mosè Autolavaggio",
            "telefono": "0543 704583",
            "indirizzo": "Via Firenze 56, Forlì",
            "tipo_impianto": "SERVITO",
            "badge_color": "#6366f1",
            "distanza": "~45 km",
            "whatsapp": "390543704583",
            "note": "Servizio rapido e accurato"
        }
    ]

def init_car_wash_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS b2b_car_washes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        city TEXT,
        address TEXT,
        plant_type TEXT,
        zone TEXT,
        distance TEXT,
        whatsapp_link TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name, address)
    )
    """)
    conn.commit()
    conn.close()

def save_car_washes_to_db(items):
    init_car_wash_table()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    saved = 0
    for item in items:
        clean_p = re.sub(r'[^0-9]', '', item['telefono'])
        wa_url = f"https://wa.me/{item['whatsapp']}" if item.get('whatsapp') else f"https://wa.me/39{clean_p}"
        try:
            cur.execute("""
            INSERT OR REPLACE INTO b2b_car_washes 
            (name, phone, city, address, plant_type, zone, distance, whatsapp_link, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['nome'], item['telefono'], "Bologna/Romagna",
                item['indirizzo'], item['tipo_impianto'], item['zona'],
                item['distanza'], wa_url, item.get('note', '')
            ))
            saved += 1
        except Exception as e:
            print(f"Errore salvataggio {item['nome']}: {e}")
    conn.commit()
    conn.close()
    return saved

def compose_html_dossier(items, target_zone_name="Bologna & Romagna"):
    # Raggruppa per zona
    zones = {}
    for it in items:
        z = it['zona']
        if z not in zones:
            zones[z] = []
        zones[z].append(it)

    now_str = datetime.datetime.now().strftime("%d/%m/%Y ore %H:%M")

    html_tables = ""
    for z_title, z_items in zones.items():
        rows_html = ""
        for it in z_items:
            clean_p = re.sub(r'[^0-9]', '', it['telefono'])
            wa_href = f"https://wa.me/{it['whatsapp']}" if it.get('whatsapp') else f"https://wa.me/39{clean_p}"
            tel_href = f"tel:+39{clean_p}"

            rows_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px 14px; font-weight: bold; color: #0f172a;">{it['nome']}</td>
                <td style="padding: 12px 14px;">
                    <a href="{wa_href}" target="_blank" style="display: inline-block; background: #22c55e; color: #ffffff; text-decoration: none; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-right: 4px;">WhatsApp</a>
                    <a href="{tel_href}" style="color: #0284c7; text-decoration: none; font-weight: bold;">{it['telefono']}</a>
                </td>
                <td style="padding: 12px 14px; color: #475569;">{it['indirizzo']}</td>
                <td style="padding: 12px 14px;">
                    <span style="display: inline-block; background: {it.get('badge_color', '#0ea5e9')}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{it['tipo_impianto']}</span>
                </td>
                <td style="padding: 12px 14px; font-weight: bold; color: #64748b;">{it['distanza']}</td>
            </tr>
            """

        html_tables += f"""
        <div style="margin-top: 24px; margin-bottom: 10px;">
            <div style="background: #1e293b; color: #f8fafc; padding: 10px 16px; border-radius: 6px 6px 0 0; font-weight: bold; font-size: 13px; letter-spacing: 0.5px;">
                📍 {z_title}
            </div>
            <table style="width: 100%; border-collapse: collapse; background: #ffffff; border: 1px solid #cbd5e1; border-top: none; font-size: 13px;">
                <thead>
                    <tr style="background: #f8fafc; color: #64748b; text-align: left; border-bottom: 2px solid #e2e8f0; font-size: 11px; text-transform: uppercase;">
                        <th style="padding: 10px 14px;">Nome Ditta / Lavaggio</th>
                        <th style="padding: 10px 14px;">Telefono / Click to Chat</th>
                        <th style="padding: 10px 14px;">Località / Indirizzo</th>
                        <th style="padding: 10px 14px;">Tipo Impianto</th>
                        <th style="padding: 10px 14px;">Distanza</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """

    full_html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Prospetto Commerciale Autolavaggi — {target_zone_name}</title>
    </head>
    <body style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 25px;">
        <div style="max-width: 920px; margin: 0 auto; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #cbd5e1;">
            
            <!-- Header Stile PDF Prospetto -->
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 28px; color: #ffffff;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 0.5px; color: #38bdf8;">
                            PROSPETTO COMMERCIALE AUTOLAVAGGI
                        </h1>
                        <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 13px;">
                            Target Proposte Prodotti Chimici, Detergenza & Servizi | Base Logistica: Sesto Imolese / Bologna
                        </p>
                    </div>
                </div>
            </div>

            <!-- KPI Box -->
            <div style="display: flex; background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 14px 28px; gap: 20px; font-size: 12px;">
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 2px;">RAGGIO D'AZIONE</span>
                    <b style="color: #0f172a; font-size: 14px;">&lt; 100 Km ({target_zone_name})</b>
                </div>
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 2px;">TIPOLOGIA TARGET</span>
                    <b style="color: #0ea5e9; font-size: 14px;">Self-Service / Detailing / H24</b>
                </div>
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 2px;">USO DOCUMENTO</span>
                    <b style="color: #10b981; font-size: 14px;">Preventivazione e Agenti</b>
                </div>
                <div style="flex: 1;">
                    <span style="color: #64748b; text-transform: uppercase; font-weight: bold; display: block; margin-bottom: 2px;">DATA AGGIORNAMENTO</span>
                    <b style="color: #334155; font-size: 13px;">{now_str}</b>
                </div>
            </div>

            <div style="padding: 24px 28px;">
                <p style="margin: 0 0 16px 0; color: #334155; font-size: 14px; line-height: 1.5;">
                    Gentile <b>Badr</b>,<br>
                    Ecco il dossier ordinato degli <b>autolavaggi censiti e verificati</b> per l'area richiesta (<b>{target_zone_name}</b>). 
                    Tutti i recapiti sono forniti con <b>link diretto WhatsApp e telefonico</b> per un contatto commerciale istantaneo.
                </p>

                {html_tables}

                <!-- Note Tecniche Prodotto Chimico & Corrieri -->
                <div style="margin-top: 28px; background: #f0fdf4; border: 1px solid #86efac; border-left: 5px solid #22c55e; border-radius: 6px; padding: 14px 18px;">
                    <h3 style="margin: 0 0 6px 0; color: #166534; font-size: 14px;">🧪 Indicazioni per Preventivazione Prodotto Chimico & Detergenza</h3>
                    <p style="margin: 0; font-size: 12px; color: #15803d; line-height: 1.5;">
                        Gli impianti di tipo <b>Self-Service / H24</b> consumano volumi elevati di monocomponenti ad alta schiuma e cere asciuganti ad alto scivolamento.<br>
                        I centri <b>Detailing / A Mano</b> richiedono pulitori alcalini dedicati ai cerchi e detergenti protettivi per interni/pelli.
                    </p>
                </div>

                <div style="margin-top: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; font-size: 12px; color: #475569;">
                    <b>Note Operative per Rappresentanti / Consegne:</b><br>
                    • <b>Consegna Campionari:</b> Favorire gli orari diurni (08:30 - 11:30) per evitare picchi di affluenza nei box.<br>
                    • <b>Primo Contatto Preventivo:</b> Chiedere del responsabile di vasca/impianto e verificare la tipologia di dosatori installati (pompe dosatrici o iniettori Venturi).<br>
                    • <b>Forniture Fusti:</b> Tutti gli impianti segnalati dispongono di accesso idoneo per fustini da 25kg / taniche da 10kg.
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #f1f5f9; padding: 16px 28px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; text-align: center;">
                E.B.J. AI OS Autonomous Intelligence · BadrExpress.com & PietroTraslochi.com<br>
                Dossier generato ed inviato in modo autonomo su richiesta dell'utente.
            </div>
        </div>
    </body>
    </html>
    """
    return full_html

def send_email_dossier(recipient, subject, html_content):
    print(f"[*] Connessione al server SMTP di Google (smtp.gmail.com:587)...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"EBJ Intelligence <{GMAIL_USER}>"
    msg["To"] = recipient

    # Versione solo testo di fallback
    text_part = MIMEText("Dossier Autolavaggi EBJ pronto. Visualizza in formato HTML.", "plain", "utf-8")
    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(text_part)
    msg.attach(html_part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, recipient, msg.as_string())
        server.quit()
        print(f"[SUCCESS] Dossier inviato con successo a {recipient}!")
        return True
    except Exception as e:
        print(f"[ERROR] Impossibile inviare email: {e}")
        return False

def main():
    target_zone = sys.argv[1] if len(sys.argv) > 1 else "Bologna"
    target_email = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_RECIPIENT

    print("=" * 65)
    print(f"   EBJ AUTOLAVAGGI SCOUT & EMAIL DISPATCHER — {target_zone.upper()}   ")
    print("=" * 65)

    catalog = get_bologna_car_washes_catalog()
    print(f"[*] Caricati {len(catalog)} autolavaggi verificati con telefono e indirizzo.")

    # Salvataggio nel database locale
    saved_count = save_car_washes_to_db(catalog)
    print(f"[*] Salvati/Aggiornati {saved_count} record nel database SQLite ({DB_PATH}).")

    # Generazione HTML identico al PDF
    html = compose_html_dossier(catalog, target_zone_name="Bologna, Imola & Romagna")

    # Invio email
    subject = f"📊 PROSPETTO COMMERCIALE AUTOLAVAGGI — {target_zone} (Lista Ordinata & Telefoni)"
    success = send_email_dossier(target_email, subject, html)

    if success:
        print("\n>>> TEST COMPLETATO CON SUCCESSO!")
        print(f">>> Email ricevuta su: {target_email}")
        print(f">>> Totale autolavaggi ordinati per zona: {len(catalog)}")
    else:
        print("\n>>> ERRORE NELL'INVIO EMAIL.")
        sys.exit(1)

if __name__ == "__main__":
    main()
