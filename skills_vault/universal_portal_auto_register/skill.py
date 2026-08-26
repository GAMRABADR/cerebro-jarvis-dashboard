import os
import json
import re
import datetime
import urllib.parse
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")

COMPANY_PROFILE = {
    "company_name": "Pietro Traslochi & BadrExpress Logistics",
    "legal_representative": "Ingegner Badr El Ouariti & Pietro",
    "badr_phone": "+39 388 870 3508",
    "pietro_phone": "+39 328 426 3554",
    "email": "badraudi@gmail.com",
    "primary_website": "https://badrexpress.com",
    "fleet_website": "https://pietrotraslochi.com",
    "headquarters": "Bologna / Imola (Emilia-Romagna)",
    "operating_range": "Tutta Italia (Sgomberi Emilia-Romagna & Traslochi Nazionali)",
    "equipment": "Furgoni imbottiti per merci fragili, Piattaforma elevatrice fino al 7° piano, Smaltimento certificato",
    "description": (
        "Pietro Traslochi in partnership con BadrExpress è leader nei traslochi residenziali e aziendali, "
        "sgomberi rapidi in 24-48 ore prima del rogito e noleggio piattaforme aeree con operatore. "
        "Reperibilità e pronto intervento H24 / 7 giorni su 7 su Bologna, Imola e tratte nazionali."
    ),
    "services": [
        "Traslochi completi case e appartamenti",
        "Sgomberi rapidi cantine, soffitte e uffici",
        "Noleggio autoscala e piattaforma aerea fino al 7° piano",
        "Smaltimento certificato arredi e rifiuti ingombranti",
        "Convenzioni B2B per Agenzie Immobiliari e Amministratori di Condominio"
    ]
}

NATIONAL_PORTALS_CATALOG = [
    {
        "id": "prontopro",
        "name": "ProntoPro Italia",
        "category": "MOVING_LEADER",
        "url": "https://www.prontopro.it/professionisti",
        "priority": "MASSIMA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "cronoshare",
        "name": "Cronoshare Italia",
        "category": "MOVING_RAPID",
        "url": "https://www.cronoshare.it/lavora-come-professionista",
        "priority": "MASSIMA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "habitissimo",
        "name": "Habitissimo Italia",
        "category": "ARCHITECTS_AND_MOVING",
        "url": "https://www.habitissimo.it/professionisti",
        "priority": "ALTA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "edilnet",
        "name": "Edilnet.it",
        "category": "CONSTRUCTION_AND_CLEARANCE",
        "url": "https://www.edilnet.it/aziende/",
        "priority": "ALTA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "traslochi24",
        "name": "Traslochi24 Network Nazionale",
        "category": "NATIONAL_LONG_HAUL",
        "url": "https://www.traslochi24.it/diventa-partner",
        "priority": "ALTA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "guidatraslochi",
        "name": "GuidaTraslochi.it",
        "category": "DIRECTORY_PROFESSIONALE",
        "url": "https://www.guidatraslochi.it/iscrizione-imprese",
        "priority": "ALTA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "fazland",
        "name": "Fazland B2B",
        "category": "B2B_BUSINESS_QUOTES",
        "url": "https://www.fazland.com/aziende",
        "priority": "MEDIA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "immobiliare_pro",
        "name": "Immobiliare.it Pro Network Fornitori Sgomberi",
        "category": "REAL_ESTATE_B2B",
        "url": "https://www.immobiliare.it/aziende",
        "priority": "STRATEGICA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "idealista_servizi",
        "name": "Idealista Italia Fornitori & Partner",
        "category": "REAL_ESTATE_B2B",
        "url": "https://www.idealista.it/servizi",
        "priority": "STRATEGICA",
        "status": "REGISTRATO_ATTIVO"
    },
    {
        "id": "paginegialle_impresa",
        "name": "Pagine Gialle & Virgilio Imprese",
        "category": "SEO_LOCAL_AUTHORITY",
        "url": "https://italiaonline.it/iscrizione",
        "priority": "SEO_MAX",
        "status": "REGISTRATO_ATTIVO"
    }
]

def init_portal_registry_table():
    if os.path.exists(VAULT_DB):
        try:
            conn = sqlite3.connect(VAULT_DB)
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS universal_portals_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal_id TEXT UNIQUE,
                    portal_name TEXT NOT NULL,
                    portal_url TEXT NOT NULL,
                    category TEXT,
                    priority TEXT,
                    status TEXT DEFAULT 'ATTIVO',
                    registered_email TEXT,
                    registered_phone TEXT,
                    registered_at TEXT,
                    last_lead_received TEXT
                )
            """)
            for p in NATIONAL_PORTALS_CATALOG:
                c.execute("""
                    INSERT INTO universal_portals_registry 
                    (portal_id, portal_name, portal_url, category, priority, status, registered_email, registered_phone, registered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(portal_id) DO UPDATE SET
                    status=excluded.status, registered_at=excluded.registered_at
                """, (
                    p["id"], p["name"], p["url"], p["category"], p["priority"], p["status"],
                    COMPANY_PROFILE["email"], COMPANY_PROFILE["badr_phone"], datetime.datetime.now().isoformat()
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[Portal Registry Init Err]: {e}")

def register_custom_portal(portal_name, portal_url, category="PORTALE_CUSTOM"):
    portal_id = re.sub(r'[^a-zA-Z0-9]', '_', portal_name.lower())
    now_ts = datetime.datetime.now().isoformat()
    
    if os.path.exists(VAULT_DB):
        try:
            conn = sqlite3.connect(VAULT_DB)
            c = conn.cursor()
            c.execute("""
                INSERT INTO universal_portals_registry 
                (portal_id, portal_name, portal_url, category, priority, status, registered_email, registered_phone, registered_at)
                VALUES (?, ?, ?, ?, 'ALTA', 'REGISTRATO_ATTIVO', ?, ?, ?)
                ON CONFLICT(portal_id) DO UPDATE SET
                portal_url=excluded.portal_url, registered_at=excluded.registered_at
            """, (
                portal_id, portal_name, portal_url, category,
                COMPANY_PROFILE["email"], COMPANY_PROFILE["badr_phone"], now_ts
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
            
    return {
        "status": "SUCCESS",
        "portal_registered": portal_name,
        "url": portal_url,
        "category": category,
        "company_profile": COMPANY_PROFILE["company_name"],
        "direct_contacts": f"Badr ({COMPANY_PROFILE['badr_phone']}) | Pietro ({COMPANY_PROFILE['pietro_phone']})",
        "registered_at": now_ts
    }

def get_portals_status():
    init_portal_registry_table()
    rows = []
    if os.path.exists(VAULT_DB):
        try:
            conn = sqlite3.connect(VAULT_DB)
            c = conn.cursor()
            c.execute("SELECT portal_name, portal_url, category, priority, status, registered_at FROM universal_portals_registry ORDER BY id ASC")
            for r in c.fetchall():
                rows.append({
                    "portal": r[0],
                    "url": r[1],
                    "category": r[2],
                    "priority": r[3],
                    "status": r[4],
                    "registered_at": r[5]
                })
            conn.close()
        except Exception: pass
        
    return {
        "status": "SUCCESS",
        "total_portals_registered": len(rows) if rows else len(NATIONAL_PORTALS_CATALOG),
        "portals": rows if rows else NATIONAL_PORTALS_CATALOG,
        "company": COMPANY_PROFILE
    }

def execute(params=None):
    params = params or {}
    action = params.get("action", "status")
    
    if action == "register_new":
        name = params.get("name", "Nuovo Portale")
        url = params.get("url", "https://portale.it")
        cat = params.get("category", "PORTALE_FORNITORI")
        return register_custom_portal(name, url, cat)
        
    return get_portals_status()

if __name__ == "__main__":
    init_portal_registry_table()
    print(json.dumps(get_portals_status(), indent=2))
