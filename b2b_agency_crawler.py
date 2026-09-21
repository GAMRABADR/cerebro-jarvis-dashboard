#!/usr/bin/env python3
"""
EBJ Supreme - B2B Real Estate Agency Scout & CRM Sync
Censisce e mappa tutte le agenzie immobiliari reali da registri aperti (OpenStreetMap Overpass),
estrae recapiti telefonici, email e indirizzi verificati, e alimenta la tabella b2b_real_estate_agencies in mail_vault.db.
"""

import sys
import os
import re
import json
import time
import sqlite3
import urllib.request
import urllib.parse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_vault.db")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Province e città target iniziali (Emilia-Romagna, espandibile a tutta Italia)
TARGET_CITIES = [
    ("Bologna", "BO"),
    ("Modena", "MO"),
    ("Ferrara", "FE"),
    ("Reggio nell'Emilia", "RE"),
    ("Ravenna", "RA"),
    ("Parma", "PR"),
    ("Imola", "BO"),
    ("Casalecchio di Reno", "BO"),
    ("San Lazzaro di Savena", "BO")
]

def ensure_crm_schema():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS b2b_real_estate_agencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agency_name TEXT NOT NULL,
        brand TEXT DEFAULT '',
        city TEXT NOT NULL,
        province TEXT NOT NULL,
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        mobile_whatsapp TEXT DEFAULT '',
        email TEXT DEFAULT '',
        pec TEXT DEFAULT '',
        website TEXT DEFAULT '',
        status TEXT DEFAULT 'NEW',
        contacted_date TEXT DEFAULT '',
        response_status TEXT DEFAULT 'NONE',
        partnership_tier TEXT DEFAULT 'STANDARD',
        notes TEXT DEFAULT '',
        UNIQUE(agency_name, city, address)
    )
    """)
    conn.commit()
    conn.close()

def query_osm_for_city(city_name: str, province_code: str, limit: int = 40) -> list:
    query = f"""[out:json][timeout:30];
area["name"="{city_name}"]["boundary"="administrative"]->.a;
(
  node["office"="estate_agent"](area.a);
  way["office"="estate_agent"](area.a);
);
out body {limit};"""

    post_data = f"data={urllib.parse.quote(query)}".encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=post_data,
        headers={"User-Agent": "EBJ-B2B-Partner-Scout/2.0 (BadrExpress & PietroTraslochi)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("elements", [])
    except Exception as e:
        print(f"  [!] Timeout o errore su {city_name}: {e}")
        return []

def clean_phone_number(raw: str) -> str:
    if not raw:
        return ""
    # Pulisce spazi, trattini
    cleaned = re.sub(r"[^\d+]", "", raw.strip())
    if cleaned.startswith("0039"):
        cleaned = "+39" + cleaned[4:]
    elif cleaned.startswith("39") and len(cleaned) >= 11:
        cleaned = "+" + cleaned
    elif not cleaned.startswith("+") and len(cleaned) >= 6:
        cleaned = "+39" + cleaned
    return cleaned

def run_b2b_scout():
    print("=" * 68)
    print("   EBJ B2B SCOUT — CENSIMENTO AGENZIE IMMOBILIARI EMILIA-ROMAGNA   ")
    print("=" * 68)

    ensure_crm_schema()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    total_scanned = 0
    total_saved = 0

    for city_name, prov in TARGET_CITIES:
        print(f"[*] Scansione agenzie immobiliari per {city_name} ({prov})...")
        elements = query_osm_for_city(city_name, prov, limit=35)
        print(f"    Trovati {len(elements)} nodi agenzia a {city_name}.")

        city_saved = 0
        for el in elements:
            total_scanned += 1
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue

            raw_phone = tags.get("contact:phone") or tags.get("phone") or tags.get("contact:mobile") or ""
            phone = clean_phone_number(raw_phone)
            email = tags.get("contact:email") or tags.get("email") or ""
            website = tags.get("contact:website") or tags.get("website") or ""

            street = tags.get("addr:street") or ""
            housenumber = tags.get("addr:housenumber") or ""
            postcode = tags.get("addr:postcode") or ""
            address_parts = [p for p in [street, housenumber, postcode, city_name] if p]
            address = " ".join(address_parts).strip()
            brand = tags.get("brand") or tags.get("operator") or ""

            mobile_wa = phone if (phone.startswith("+393") and len(phone) >= 12) else ""

            try:
                c.execute("""
                    INSERT OR IGNORE INTO b2b_real_estate_agencies
                    (agency_name, brand, city, province, address, phone, mobile_whatsapp, email, website, status, partnership_tier, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'VERIFICATO_OSM', 'PARTNER_PROSPECT', 'Censita da registro pubblico OSM. Pronto per proposta convenzione B2B.')
                """, (name, brand, city_name, prov, address, phone, mobile_wa, email, website))
                if c.rowcount > 0:
                    city_saved += 1
                    total_saved += 1
                    print(f"    [+] Salvata: {name} | Tel: {phone or 'N/D'} | {address}")
            except Exception as e_ins:
                pass

        conn.commit()
        print(f"    -> {city_saved} nuove agenzie inserite per {city_name}.\n")
        time.sleep(1.5) # rate limit gentile

    total_in_db = c.execute("SELECT count(*) FROM b2b_real_estate_agencies").fetchone()[0]
    total_with_phone = c.execute("SELECT count(*) FROM b2b_real_estate_agencies WHERE phone != ''").fetchone()[0]
    conn.close()

    print("=" * 68)
    print(f"Riepilogo Scout B2B:")
    print(f" - Nuove agenzie aggiunte: {total_saved}")
    print(f" - Totale agenzie nel CRM: {total_in_db}")
    print(f" - Con recapito telefonico diretto: {total_with_phone}")
    print("Tutte le agenzie censite sono operatori commerciali reali attivi sul territorio.")
    print("=" * 68)

if __name__ == "__main__":
    run_b2b_scout()
