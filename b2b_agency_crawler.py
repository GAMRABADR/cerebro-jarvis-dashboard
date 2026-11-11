#!/usr/bin/env python3
"""
EBJ Supreme - B2B Real Estate Agency Scout, Website Crawler & Enricher
Censisce agenzie immobiliari REALI da PagineGialle + siti web ufficiali + OpenStreetMap Overpass,
estrae recapiti telefonici AGCOM validati, email verificate DNS, pagine Facebook e form Contatti,
e aggiorna b2b_real_estate_agencies in mail_vault.db.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mail_vault.db")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

from ebj_lead_sanitizer import (
    validate_italian_phone,
    extract_phones_from_text,
    validate_email_address,
    extract_emails_from_text,
)

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8",
}

TARGET_CITIES = [
    ("Bologna", "BO"),
    ("Imola", "BO"),
    ("Casalecchio di Reno", "BO"),
    ("San Lazzaro di Savena", "BO"),
    ("Modena", "MO"),
    ("Ferrara", "FE"),
    ("Ravenna", "RA"),
    ("Reggio nell'Emilia", "RE"),
    ("Cuneo", "CN"),
    ("Torino", "TO"),
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
        province TEXT NOT NULL DEFAULT '',
        address TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        mobile_whatsapp TEXT DEFAULT '',
        email TEXT DEFAULT '',
        pec TEXT DEFAULT '',
        website TEXT DEFAULT '',
        facebook_url TEXT DEFAULT '',
        contact_form_url TEXT DEFAULT '',
        status TEXT DEFAULT 'VERIFICATO_LIVE',
        proposal_sent_at TEXT,
        last_response TEXT,
        contacted_date TEXT DEFAULT '',
        response_status TEXT DEFAULT 'NONE',
        partnership_tier TEXT DEFAULT 'PARTNER_PROSPECT',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(agency_name, city)
    )
    """)
    existing_cols = {r[1] for r in c.execute("PRAGMA table_info(b2b_real_estate_agencies)").fetchall()}
    for col, col_def in (
        ("facebook_url", "TEXT DEFAULT ''"),
        ("contact_form_url", "TEXT DEFAULT ''"),
        ("proposal_sent_at", "TEXT"),
        ("province", "TEXT DEFAULT ''"),
        ("mobile_whatsapp", "TEXT DEFAULT ''"),
        ("brand", "TEXT DEFAULT ''"),
        ("last_response", "TEXT"),
    ):
        if col not in existing_cols:
            try:
                c.execute(f"ALTER TABLE b2b_real_estate_agencies ADD COLUMN {col} {col_def}")
            except Exception:
                pass
    conn.commit()
    conn.close()


def clean_phone_number(raw: str) -> str:
    res = validate_italian_phone(raw, strict_mobile_10=False)
    return res["e164"] if res else ""


def crawl_agency_website(website_url: str, max_subpages: int = 3) -> Dict[str, Any]:
    """Visita homepage e sottopagine Contatti/Agenzia per estrarre email DNS-valide, cellulari, Facebook e form."""
    out: Dict[str, Any] = {
        "email": "",
        "all_emails": [],
        "phones": [],
        "mobile_whatsapp": "",
        "facebook_url": "",
        "contact_form_url": "",
    }
    if not website_url or not website_url.startswith("http"):
        return out

    visited = set()
    to_visit = [website_url]
    emails: List[str] = []
    phones: List[str] = []
    fb_urls: List[str] = []

    session = requests.Session()
    session.headers.update(HTTP_HEADERS)

    while to_visit and len(visited) < (1 + max_subpages):
        u = to_visit.pop(0)
        if u in visited:
            continue
        visited.add(u)
        try:
            r = session.get(u, timeout=7, allow_redirects=True)
            if r.status_code != 200 or "text/html" not in (r.headers.get("Content-Type") or "text/html"):
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            base_netloc = urllib.parse.urlparse(r.url).netloc

            for a in soup.select("a[href]"):
                href = (a.get("href") or "").strip()
                if href.startswith("mailto:"):
                    cand = href.replace("mailto:", "").split("?")[0].strip().lower()
                    ok, _ = validate_email_address(cand, check_dns=True)
                    if ok and cand not in emails:
                        emails.append(cand)
                elif href.startswith("tel:"):
                    ph = validate_italian_phone(href.replace("tel:", ""), strict_mobile_10=False)
                    if ph and ph["e164"] not in phones:
                        phones.append(ph["e164"])
                elif "facebook.com" in href and not any(x in href for x in ("sharer", "paginegialle", "plugins/")):
                    if href not in fb_urls:
                        fb_urls.append(href)
                elif len(to_visit) + len(visited) < (1 + max_subpages):
                    full = urllib.parse.urljoin(r.url, href)
                    parsed = urllib.parse.urlparse(full)
                    if parsed.netloc == base_netloc and any(k in parsed.path.lower() for k in ("contatt", "lavora", "chi-siamo", "agenzia", "contact")):
                        if full not in visited and full not in to_visit:
                            to_visit.append(full)

            text = soup.get_text(" ")
            for em in extract_emails_from_text(text, check_dns=True):
                if em not in emails:
                    emails.append(em)
            for ph in extract_phones_from_text(text, author_only=False, mobile_only=False):
                if ph["e164"] not in phones:
                    phones.append(ph["e164"])

            if not out["contact_form_url"] and soup.select("form input[type='email'], form textarea"):
                out["contact_form_url"] = r.url
        except Exception:
            continue

    # Prioritizza info@/agenzia@/direzione@ rispetto ad altri indirizzi
    emails.sort(key=lambda e: (0 if e.startswith(("info@", "agenzia@", "contatti@", "segreteria@")) else 1, e))
    mob = next((p for p in phones if p.startswith("+393")), "")
    out["email"] = emails[0] if emails else ""
    out["all_emails"] = emails[:5]
    out["phones"] = phones[:5]
    out["mobile_whatsapp"] = mob
    out["facebook_url"] = fb_urls[0] if fb_urls else ""
    return out


def scrape_paginegialle_agencies(
    city: str = "Bologna",
    province: str = "",
    limit: int = 15,
    crawl_websites: bool = True,
) -> List[Dict[str, Any]]:
    """
    Estrae agenzie immobiliari REALI da PagineGialle, risolve i siti web ufficiali e arricchisce
    email DNS-verificate, telefoni AGCOM, pagine Facebook e form contatti.
    """
    ensure_crm_schema()
    slug = urllib.parse.quote(re.sub(r"\s+", "-", city.strip().lower()))
    list_url = f"https://www.paginegialle.it/ricerca/agenzie-immobiliari/{slug}"
    agencies: List[Dict[str, Any]] = []

    try:
        r = requests.get(list_url, headers=HTTP_HEADERS, timeout=12)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".search-itm")[: max(1, min(limit, 25))]
    except Exception:
        return []

    from concurrent.futures import ThreadPoolExecutor

    def _process_pg_card(card) -> Optional[Dict[str, Any]]:
        title_el = card.select_one("h2")
        name = re.sub(r"\s+", " ", title_el.get_text(" ", strip=True)) if title_el else ""
        if not name:
            return None
        detail_a = card.select_one("a[href*='paginegialle.it/']")
        detail_url = detail_a.get("href", "") if detail_a else ""

        wa_phone = ""
        for a in card.select("a[href*='wa.me']"):
            ph = validate_italian_phone(a.get("href", ""), strict_mobile_10=False)
            if ph:
                wa_phone = ph["e164"]
                break

        address = ""
        addr_el = card.select_one(".search-itm__adr")
        if addr_el:
            address = re.sub(r"\s+", " ", addr_el.get_text(" ", strip=True))

        phones: List[str] = [wa_phone] if wa_phone else []
        website = ""
        email = ""
        fb_url = ""
        contact_form_url = ""

        if detail_url and detail_url.startswith("http"):
            try:
                rd = requests.get(detail_url, headers=HTTP_HEADERS, timeout=7)
                if rd.status_code == 200:
                    sd = BeautifulSoup(rd.text, "html.parser")
                    site_a = sd.select_one("a[data-tr*='sito']")
                    if not site_a:
                        for cand_a in sd.select("a[href^='http']"):
                            if "sito web" in cand_a.get_text(" ", strip=True).lower():
                                site_a = cand_a
                                break
                    if site_a:
                        cand_url = (site_a.get("href") or "").strip()
                        if cand_url.startswith("http") and "paginegialle.it" not in cand_url and "italiaonline.it" not in cand_url:
                            website = cand_url

                    for ph in extract_phones_from_text(sd.get_text(" "), author_only=False, mobile_only=False):
                        if ph["e164"] not in phones:
                            phones.append(ph["e164"])
                    for em in extract_emails_from_text(sd.get_text(" "), check_dns=True):
                        if not email:
                            email = em
            except Exception:
                pass

        if crawl_websites and website:
            site_info = crawl_agency_website(website, max_subpages=2)
            if site_info["email"]:
                email = site_info["email"]
            for p_site in site_info["phones"]:
                if p_site not in phones:
                    phones.append(p_site)
            if site_info["facebook_url"]:
                fb_url = site_info["facebook_url"]
            if site_info["contact_form_url"]:
                contact_form_url = site_info["contact_form_url"]

        primary_phone = phones[0] if phones else ""
        mobile_wa = next((p for p in phones if p.startswith("+393")), wa_phone)

        if not primary_phone and not email and not website:
            return None

        return {
            "agency_name": name,
            "city": city.title(),
            "province": province,
            "address": address or f"{city.title()}",
            "phone": primary_phone,
            "mobile_whatsapp": mobile_wa,
            "email": email,
            "website": website,
            "facebook_url": fb_url,
            "contact_form_url": contact_form_url,
            "status": "VERIFICATO_PG_LIVE",
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        for res_item in pool.map(_process_pg_card, cards):
            if res_item:
                agencies.append(res_item)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for row_obj in agencies:
        existing = c.execute(
            "SELECT id, phone, mobile_whatsapp, email, website, facebook_url, contact_form_url FROM b2b_real_estate_agencies WHERE LOWER(agency_name)=LOWER(?) AND LOWER(city)=LOWER(?)",
            (row_obj["agency_name"], row_obj["city"]),
        ).fetchone()
        if existing:
            eid, cur_ph, cur_wa, cur_em, cur_web, cur_fb, cur_cf = existing
            c.execute(
                """UPDATE b2b_real_estate_agencies
                   SET province = COALESCE(NULLIF(?, ''), province),
                       address = COALESCE(NULLIF(?, ''), address),
                       phone = COALESCE(NULLIF(?, ''), phone),
                       mobile_whatsapp = COALESCE(NULLIF(?, ''), mobile_whatsapp),
                       email = COALESCE(NULLIF(?, ''), email),
                       website = COALESCE(NULLIF(?, ''), website),
                       facebook_url = COALESCE(NULLIF(?, ''), facebook_url),
                       contact_form_url = COALESCE(NULLIF(?, ''), contact_form_url)
                   WHERE id = ?""",
                (
                    row_obj["province"], row_obj["address"],
                    row_obj["phone"], row_obj["mobile_whatsapp"], row_obj["email"],
                    row_obj["website"], row_obj["facebook_url"], row_obj["contact_form_url"],
                    eid,
                ),
            )
        else:
            c.execute(
                """INSERT INTO b2b_real_estate_agencies
                   (agency_name, city, province, address, phone, mobile_whatsapp, email, website, facebook_url, contact_form_url, status, partnership_tier, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'VERIFICATO_PG_LIVE', 'PARTNER_PROSPECT', 'Censita da PagineGialle + verifica sito ufficiale per convenzione B2B sgomberi.')""",
                (
                    row_obj["agency_name"], row_obj["city"], row_obj["province"], row_obj["address"],
                    row_obj["phone"], row_obj["mobile_whatsapp"], row_obj["email"], row_obj["website"],
                    row_obj["facebook_url"], row_obj["contact_form_url"],
                ),
            )

    conn.commit()
    conn.close()
    return agencies


def enrich_existing_agencies_from_websites(limit: int = 20) -> Dict[str, Any]:
    """Arricchisce in parallelo le agenzie già salvate che hanno un website ma email o facebook mancante."""
    from concurrent.futures import ThreadPoolExecutor

    ensure_crm_schema()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """SELECT id, agency_name, city, website, email, phone, facebook_url, contact_form_url
           FROM b2b_real_estate_agencies
           WHERE website != '' AND (email = '' OR email IS NULL OR facebook_url = '' OR facebook_url IS NULL)
           LIMIT ?""",
        (limit,),
    ).fetchall()

    def _crawl_row(r):
        rid, name, city, website, email, phone, fb, cf = r
        return rid, email, phone, fb, cf, crawl_agency_website(website, max_subpages=2)

    enriched = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for rid, email, phone, fb, cf, info in pool.map(_crawl_row, rows):
            new_email = email or info["email"]
            new_phone = phone or (info["phones"][0] if info["phones"] else "")
            new_mob = info["mobile_whatsapp"]
            new_fb = fb or info["facebook_url"]
            new_cf = cf or info["contact_form_url"]
            if (new_email != email) or (new_fb != fb) or (new_cf != cf) or (new_phone != phone):
                conn.execute(
                    """UPDATE b2b_real_estate_agencies
                       SET email=?, phone=?, mobile_whatsapp=COALESCE(NULLIF(?, ''), mobile_whatsapp),
                           facebook_url=?, contact_form_url=?
                       WHERE id=?""",
                    (new_email, new_phone, new_mob, new_fb, new_cf, rid),
                )
                enriched += 1
    conn.commit()
    conn.close()
    return {"checked": len(rows), "enriched": enriched}


def query_osm_for_city(city_name: str, province_code: str, limit: int = 35) -> list:
    query = f"""[out:json][timeout:20];
area["name"="{city_name}"]["boundary"="administrative"]->.a;
(
  node["office"="estate_agent"](area.a);
  way["office"="estate_agent"](area.a);
);
out center {limit};"""

    try:
        r = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": "EBJ-B2B-Partner-Scout/2.5 (BadrExpress & PietroTraslochi)"},
            timeout=22,
        )
        if r.status_code == 200:
            return r.json().get("elements", [])
    except Exception:
        pass
    return []


def run_b2b_scout(cities: Optional[List[Tuple[str, str]]] = None, limit_per_city: int = 12) -> Dict[str, Any]:
    ensure_crm_schema()
    targets = cities or TARGET_CITIES[:5]
    all_found: List[Dict[str, Any]] = []

    for city_name, prov in targets:
        pg_found = scrape_paginegialle_agencies(city_name, province=prov, limit=limit_per_city, crawl_websites=True)
        all_found.extend(pg_found)
        time.sleep(0.5)

    enrich_res = enrich_existing_agencies_from_websites(limit=25)
    conn = sqlite3.connect(DB_PATH)
    tot = conn.execute("SELECT COUNT(*) FROM b2b_real_estate_agencies").fetchone()[0]
    with_em = conn.execute("SELECT COUNT(*) FROM b2b_real_estate_agencies WHERE email != ''").fetchone()[0]
    with_ph = conn.execute("SELECT COUNT(*) FROM b2b_real_estate_agencies WHERE phone != ''").fetchone()[0]
    conn.close()

    return {
        "status": "SUCCESS",
        "newly_scraped": len(all_found),
        "enriched_existing": enrich_res,
        "total_agencies": tot,
        "with_verified_phone": with_ph,
        "with_verified_email": with_em,
    }


if __name__ == "__main__":
    print(json.dumps(run_b2b_scout([("Bologna", "BO"), ("Imola", "BO")], limit_per_city=10), indent=2, ensure_ascii=False))
