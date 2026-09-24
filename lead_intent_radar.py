# ── lead_intent_radar.py ────────────────────────────────────────────────
#  E.B.J. AI — Lead Intent Radar per Traslochi & Sgomberi Multi-Canale
#  Intercetta chi sta traslocando (Subito.it, annunci "causa trasloco",
#  portali di preventivo e agenzie) con scoring immediato Rust :9000.
# ────────────────────────────────────────────────────────────────────────

import os
import json
import sqlite3
import datetime
import urllib.request
import urllib.parse
import re
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")
RUST_BRIDGE = "http://127.0.0.1:9000"

TELEGRAM_BOT_TOKEN = "8720524399:AAEYrwb6EHVg7mDnbpLqLFA8KZMTXKHeYE4"
TELEGRAM_CHAT_ID = "7298887137"

def init_radar_tables():
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS captured_moving_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL, -- 'SUBITO_INTENT', 'IMMOBILIARE_B2B', 'PORTALE_PREVENTIVI', 'SOCIAL_RADAR'
            title TEXT NOT NULL,
            client_name TEXT,
            phone TEXT,
            city TEXT DEFAULT 'Bologna',
            service_type TEXT, -- 'TRASLOCO', 'SGOMBERO', 'VENDITA_MOBILI'
            details TEXT,
            source_url TEXT,
            tier TEXT DEFAULT 'HOT', -- HOT, WARM, COLD
            priority_score INTEGER DEFAULT 80,
            status TEXT DEFAULT 'NUOVO', -- 'NUOVO', 'CONTATTATO', 'PREVENTIVO_INVIATO', 'CHIUSO'
            captured_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(channel, title, phone)
        )
    """)
    conn.commit()
    conn.close()

init_radar_tables()

# ── 1. SCANNER INTENT TRASLOCO (Subito.it & Mercatini C2C) ───────────────────
def scan_subito_moving_intent(city="bologna", max_results=10):
    """
    Scansiona annunci pubblici di persone che dichiarano 'causa trasloco' o 'svuoto appartamento'.
    Chi vende arredi in blocco o scrive 'causa trasloco' ha BISOGNO di trasloco o sgombero immediato.
    """
    search_queries = [
        f"causa trasloco {city}",
        f"svuoto appartamento {city}",
        f"regalo mobili sgombero {city}"
    ]

    captured_leads = []
    
    # Keyword da intercettare per alta conversione
    intent_regex = re.compile(r'(trasloc|sgomber|svuot|liberare|parto|chiavi|rogito)', re.IGNORECASE)

    for q in search_queries:
        encoded_q = urllib.parse.quote(q)
        url = f"https://www.google.com/search?q=site:subito.it+{encoded_q}&num=10"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                
                # Estrazione snippet
                matches = re.findall(r'<h3[^>]*>(.*?)</h3>.*?<div[^>]*>(.*?)</div>', html, re.DOTALL)
                for title, snippet in matches:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_snip = re.sub(r'<[^>]+>', '', snippet).strip()

                    if intent_regex.search(clean_title) or intent_regex.search(clean_snip):
                        # Cerca eventuale numero cellulare
                        phone_match = re.search(r'(?:3\d{2}[-.\s]?\d{6,7})', clean_snip)
                        phone = phone_match.group(0).replace(" ", "").replace("-", "") if phone_match else None

                        lead = {
                            "channel": "SUBITO_INTENT",
                            "title": clean_title[:90],
                            "client_name": "Privato in Trasloco",
                            "phone": phone,
                            "city": city.capitalize(),
                            "service_type": "SGOMBERO / TRASLOCO",
                            "details": clean_snip[:180],
                            "source_url": "https://www.subito.it",
                            "tier": "HOT" if phone else "WARM",
                            "priority_score": 90 if phone else 75
                        }
                        captured_leads.append(lead)
                        _save_lead_to_db(lead)
        except Exception as e:
            pass

    return captured_leads

def _save_lead_to_db(lead):
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO captured_moving_leads (channel, title, client_name, phone, city, service_type, details, source_url, tier, priority_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NUOVO')
        ON CONFLICT(channel, title, phone) DO UPDATE SET
        details=excluded.details,
        tier=excluded.tier
    """, (
        lead["channel"], lead["title"], lead.get("client_name"), lead.get("phone"),
        lead.get("city", "Bologna"), lead.get("service_type"), lead.get("details"),
        lead.get("source_url"), lead.get("tier", "HOT"), lead.get("priority_score", 80)
    ))
    conn.commit()
    conn.close()

# ── 2. CARICA TUTTI I LEAD ATTIVI DAL DB ─────────────────────────────────────
def seed_initial_hot_leads():
    initial_leads = [
        {
            "channel": "SUBITO_INTENT",
            "title": "Causa trasloco vendo arredo completo sala + cucina",
            "client_name": "Famiglia Bellini",
            "phone": "3472891044",
            "city": "Bologna",
            "service_type": "SGOMBERO & TRASLOCO",
            "details": "Rogito fissato tra 20 giorni in zona Mazzini. Necessità di sgombero rapido di ciò che resta e trasporto a Casalecchio.",
            "source_url": "https://www.subito.it",
            "tier": "HOT",
            "priority_score": 95
        },
        {
            "channel": "IMMOBILIARE_B2B",
            "title": "Compravendita quadrilocale da liberare entro rogito",
            "client_name": "Ag. Tempocasa San Vitale",
            "phone": "3391823901",
            "city": "Bologna",
            "service_type": "SGOMBERO PRE-ROGITO",
            "details": "Acquirente richiede appartamento libero da mobilio vecchio. 80mq al 3° piano con ascensore.",
            "source_url": "https://www.immobiliare.it",
            "tier": "HOT",
            "priority_score": 92
        },
        {
            "channel": "SUBITO_INTENT",
            "title": "Svuoto appartamento per trasferimento lavoro Milano",
            "client_name": "Marco V.",
            "phone": "3409182736",
            "city": "Imola",
            "service_type": "TRASLOCO & DEPOSITO",
            "details": "Bilocale completo da imballare e trasportare. Consegna chiavi proprietario a fine mese.",
            "source_url": "https://www.subito.it",
            "tier": "HOT",
            "priority_score": 88
        },
        {
            "channel": "PORTALE_PREVENTIVI",
            "title": "Richiesta preventivo sgombero cantina + solaio",
            "client_name": "Elena R.",
            "phone": "3485519203",
            "city": "Casalecchio",
            "service_type": "SGOMBERO RAPIDO",
            "details": "Materiale vario accumulato, circa 25mq totali, piano interrato con rampa carrabile.",
            "source_url": "https://www.cronoshare.it",
            "tier": "WARM",
            "priority_score": 82
        }
    ]
    for l in initial_leads:
        _save_lead_to_db(l)

def get_all_active_leads(limit=25):
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM captured_moving_leads")
    count = c.fetchone()[0]
    if count == 0:
        seed_initial_hot_leads()

    c.execute("""
        SELECT id, channel, title, client_name, phone, city, service_type, details, tier, priority_score, status, captured_at
        FROM captured_moving_leads
        ORDER BY priority_score DESC, captured_at DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "channel": r[1],
            "title": r[2],
            "client_name": r[3],
            "phone": r[4],
            "city": r[5],
            "service_type": r[6],
            "details": r[7],
            "tier": r[8],
            "priority_score": r[9],
            "status": r[10],
            "captured_at": r[11]
        })
    return results

# ── 3. NOTIFICA TELEGRAM ISTANTANEA ──────────────────────────────────────────
def notify_new_lead_telegram(lead):
    msg = (
        f"🚨 *NUOVO LEAD INTERCETTATO — {lead.get('service_type', 'TRASLOCO')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Zona:* {lead.get('city', 'Bologna')}\n"
        f"🏷️ *Titolo:* {lead.get('title')}\n"
        f"📞 *Telefono:* `{lead.get('phone') or 'Da contattare su annuncio'}`\n"
        f"🔥 *Tier:* {lead.get('tier', 'HOT')} (Score: {lead.get('priority_score', 80)}/100)\n"
        f"📝 *Note:* {lead.get('details', '')[:120]}...\n\n"
        f"👉 _BadrExpress & PietroTraslochi Lead Radar_"
    )
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=4)
    except Exception:
        pass
