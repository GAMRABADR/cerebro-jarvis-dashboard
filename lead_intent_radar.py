# ── lead_intent_radar.py ────────────────────────────────────────────────
#  E.B.J. AI — Lead Intent Radar per Traslochi & Sgomberi Multi-Canale
#  Intercetta chi sta traslocando (Subito.it, annunci "causa trasloco",
#  portali di preventivo e agenzie) con scoring immediato Rust :9000.
# ────────────────────────────────────────────────────────────────────────

import logging
import os
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")
RUST_BRIDGE = "http://127.0.0.1:9000"
logger = logging.getLogger(__name__)

# Le credenziali arrivano esclusivamente dall'ambiente di runtime.
# Non sono richieste per consultare il radar e non devono mai finire nel repository.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_JARVIS_MASTER", "")
TELEGRAM_CHAT_ID = os.environ.get("OWNER_CHAT_ID", "")

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

    result_limit = max(0, min(int(max_results), 100))
    if result_limit == 0:
        return captured_leads

    for q in search_queries:
        if len(captured_leads) >= result_limit:
            break
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
                            "client_name": None,
                            "phone": phone,
                            "phone_status": "unverified" if phone else "not_found",
                            "city": city.capitalize(),
                            "service_type": "SGOMBERO / TRASLOCO",
                            "details": clean_snip[:180],
                            "source_url": f"https://www.google.com/search?q={urllib.parse.quote('site:subito.it ' + q)}",
                            "tier": "WARM",
                            "priority_score": 60
                        }
                        captured_leads.append(lead)
                        _save_lead_to_db(lead)
                        if len(captured_leads) >= result_limit:
                            break
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as exc:
            logger.warning("Radar Subito: ricerca non riuscita per %r: %s", q, exc)
        except (sqlite3.Error, ValueError, TypeError):
            logger.exception("Radar Subito: errore durante l'elaborazione della ricerca %r", q)

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
def get_all_active_leads(limit=25):
    """Restituisce solo lead effettivamente salvati dalla pipeline.

    Non vengono creati lead di esempio: un radar vuoto deve mostrare chiaramente
    che non ci sono risultati, non numeri apparentemente chiamabili.
    """
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()

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
            "phone_status": "unverified" if r[4] else "not_found",
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
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=4)
        return response.ok
    except requests.RequestException:
        return False
