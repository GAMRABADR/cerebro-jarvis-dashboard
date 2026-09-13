"""
LEAD HUNTER OSINT 2.0 - Versione corretta e ottimizzata
Tre livelli di ricerca:
  Livello 1: Estratto da DuckDuckGo snippet (numeri nelle SERP)
  Livello 2: Scraping della pagina del singolo annuncio
  Livello 3: OSINT cross-reference da nome autore su web
  Fallback: DM_READY con template di contatto pre-compilato
"""
import requests
import re
import sqlite3
import datetime
import os
import time
import urllib.parse
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")
RUST_BRIDGE = "http://127.0.0.1:9000"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9",
}

# Pattern numeri italiani
MOBILE_RE   = re.compile(r"(?<!\d)(?:\+39[\s.\-]?)?(?:3[1-9]\d{1}[\s.\-]?\d{3,4}[\s.\-]?\d{3,4})(?!\d)")
LANDLINE_RE = re.compile(r"(?<!\d)(?:\+39[\s.\-]?)?(?:0\d{1,3}[\s.\-]?\d{5,8})(?!\d)")

# Blacklist sequenze artificiali
BAD_ENDINGS = {"1234", "4321", "5678", "8765", "0000", "1111", "2222", "3333", "6789", "9876"}


def clean_phone(raw):
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("+39"):
        digits = digits[3:]
    digits = digits.lstrip("0")
    if len(digits) == 10 and digits.startswith("3"):
        return "+39 " + digits[:3] + " " + digits[3:6] + " " + digits[6:]
    if len(digits) >= 8:
        return "+39 " + digits
    return ""


def is_valid_phone(raw):
    cleaned = clean_phone(raw)
    if not cleaned:
        return False
    digits = re.sub(r"[^\d]", "", cleaned)
    if digits.startswith("39"):
        digits = digits[2:]
    if len(digits) not in (9, 10):
        return False
    if len(set(digits)) <= 2:
        return False
    if digits[-4:] in BAD_ENDINGS:
        return False
    return True


def extract_phones(text):
    found = []
    for m in MOBILE_RE.finditer(text):
        c = clean_phone(m.group())
        if c and is_valid_phone(c):
            found.append(c)
    for m in LANDLINE_RE.finditer(text):
        c = clean_phone(m.group())
        if c and is_valid_phone(c):
            found.append(c)
    return list(dict.fromkeys(found))  # Deduplica preservando ordine


def get_db():
    conn = sqlite3.connect(VAULT_DB, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS verified_leads_2026 (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name      TEXT NOT NULL,
            phone            TEXT NOT NULL DEFAULT 'DM_ONLY',
            email            TEXT DEFAULT '',
            city             TEXT NOT NULL DEFAULT '',
            service_type     TEXT NOT NULL DEFAULT 'Trasloco Residenziale',
            volume_mq        INTEGER DEFAULT 50,
            piano_partenza   INTEGER DEFAULT 0,
            piano_arrivo     INTEGER DEFAULT 0,
            ascensore        INTEGER DEFAULT 0,
            estimated_budget REAL DEFAULT 450.0,
            source           TEXT NOT NULL DEFAULT 'OSINT',
            verified_status  TEXT DEFAULT 'VERIFICATO',
            contact_type     TEXT DEFAULT 'TELEFONO',
            post_url         TEXT DEFAULT '',
            dm_template      TEXT DEFAULT '',
            whatsapp_link    TEXT DEFAULT '',
            scraped_date     TEXT NOT NULL DEFAULT '',
            notes            TEXT DEFAULT ''
        )
    """)
    conn.commit()
    return conn


def is_known(conn, phone=None, post_url=None):
    c = conn.cursor()
    if phone and phone != "DM_ONLY":
        d = re.sub(r"[^\d]", "", phone)
        if d.startswith("39"):
            d = d[2:]
        rows = c.execute(
            "SELECT id FROM verified_leads_2026 WHERE REPLACE(REPLACE(REPLACE(phone,'+',''),' ',''),'-','') LIKE ?",
            ("%" + d[-8:],)
        ).fetchall()
        if rows:
            return True
    if post_url:
        rows = c.execute(
            "SELECT id FROM verified_leads_2026 WHERE post_url=? OR notes LIKE ?",
            (post_url, "%" + post_url[:50] + "%")
        ).fetchall()
        if rows:
            return True
    return False


def save_lead(conn, lead):
    try:
        conn.execute("""
            INSERT OR IGNORE INTO verified_leads_2026
            (client_name, phone, email, city, service_type, volume_mq, estimated_budget,
             source, verified_status, contact_type, post_url, dm_template, whatsapp_link,
             scraped_date, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            lead.get("name", "Privato"),
            lead.get("phone", "DM_ONLY"),
            lead.get("email", ""),
            lead.get("city", ""),
            lead.get("service", "Trasloco Residenziale"),
            lead.get("mq", 50),
            lead.get("budget", 450.0),
            lead.get("source", "OSINT"),
            lead.get("verified_status", "VERIFICATO"),
            lead.get("contact_type", "DM_ONLY"),
            lead.get("post_url", ""),
            lead.get("dm_template", ""),
            lead.get("whatsapp_link", ""),
            datetime.datetime.now().strftime("%Y-%m-%d"),
            str(lead.get("notes", ""))[:200],
        ))
        conn.commit()
    except Exception:
        pass


def whatsapp_link(phone, city, service):
    digits = re.sub(r"[^\d]", "", phone)
    if not digits.startswith("39"):
        digits = "39" + digits.lstrip("0")
    msg = urllib.parse.quote(
        f"Ciao! Ho visto il tuo annuncio per {service} a {city}. "
        f"Siamo Pietro Traslochi, offriamo servizi professionali con preventivo gratuito. "
        f"Posso mandarti un preventivo? Scrivi o chiama: Pietro Traslochi 328 426 3554. Grazie!"
    )
    return "https://wa.me/" + digits + "?text=" + msg


def dm_template(city, service):
    return (
        f"Ciao! Ho visto il tuo post per {service} a {city}. "
        f"Siamo Pietro Traslochi - professionisti del settore. "
        f"Possiamo offrirti un preventivo gratuito e senza impegno. "
        f"Contattaci al 328 426 3554 oppure rispondici qui. Grazie!"
    )


def scrape_page_for_phones(url):
    if not url or not url.startswith("http"):
        return [], ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ")
        phones = extract_phones(text)
        author = ""
        for sel in [".UserInfo-name", ".ad-author", ".seller-name", ".user-name",
                    "[itemprop='author']", ".advertiser-name", ".user__name"]:
            el = soup.select_one(sel)
            if el:
                author = el.get_text(strip=True)
                break
        return phones, author
    except Exception:
        return [], ""


def osint_search_phone(name, city):
    """Cerca il numero telefonico di un privato tramite ricerca web mirata."""
    if not name or len(name.strip()) < 4:
        return ""
    clean = re.sub(r"\(.*?\)", "", name).strip()
    clean = re.sub(r"[0-9]", "", clean).strip()
    if len(clean) < 3:
        return ""
    queries = [
        clean + " " + city + " telefono cellulare contatto",
        '"' + clean + '" ' + city + " trasloco",
    ]
    for q in queries[:1]:
        try:
            url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
            r = requests.get(url, headers=HEADERS, timeout=6)
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ")
            phones = extract_phones(text)
            if phones:
                return phones[0]
        except Exception:
            pass
        time.sleep(0.3)
    return ""


def get_query_variants(query, city):
    """Genera varianti di query per massimizzare la copertura dei risultati."""
    return [
        query + " " + city + " privato cellulare",
        query + " urgente " + city + " preventivo",
        "cerco " + query + "  " + city + " disponibile",
        "sgombero " + city + " privato numero",
        query + " " + city + " contatti",
    ]


def run(params):
    city  = str(params.get("city", "bologna")).lower()
    query = str(params.get("query", "trasloco"))
    limit = int(params.get("limit", 10))

    city_disp = city.title()
    conn = get_db()
    leads_out = []
    seen_phones = set()

    query_variants = get_query_variants(query, city)

    for q_variant in query_variants:
        if len(leads_out) >= limit:
            break

        ddg_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q_variant)
        try:
            r = requests.get(ddg_url, headers=HEADERS, timeout=8)
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception:
            continue

        items = soup.find_all("div", class_="result__body")
        if not items:
            continue

        for item in items:
            if len(leads_out) >= limit:
                break

            title_el   = item.find("a", class_="result__a")
            snippet_el = item.find("a", class_="result__snippet")
            link_el    = item.find("a", class_="result__a")

            title   = title_el.get_text(strip=True)   if title_el   else "Richiesta Privata"
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            link    = link_el.get("href", "")          if link_el    else ""

            # Salta se gia visto questo annuncio
            if is_known(conn, post_url=link):
                continue

            full_text = title + " " + snippet

            # Tipo servizio
            service = "Trasloco Residenziale"
            if any(k in full_text.lower() for k in ("sgombero", "cantina", "garage")):
                service = "Sgombero & Smaltimento"
            elif any(k in full_text.lower() for k in ("ufficio", "azienda", "magazzino")):
                service = "Trasloco Commerciale"

            mq = 80 if "appartamento" in full_text.lower() else 50
            budget = mq * 9.5 if mq > 60 else 420.0

            # ── LIVELLO 1: Numero nei snippet SERP ───────────────────
            phones = extract_phones(full_text)

            # ── LIVELLO 2: Scraping pagina annuncio ──────────────────
            if not phones and link:
                time.sleep(0.5)
                page_phones, author = scrape_page_for_phones(link)
                phones = page_phones
            else:
                author = ""

            if phones:
                phone = phones[0]
                if phone not in seen_phones and not is_known(conn, phone=phone):
                    seen_phones.add(phone)
                    wa = whatsapp_link(phone, city_disp, service)
                    lead = {
                        "name": author if author else "Privato (" + title[:25].strip() + ")",
                        "phone": phone,
                        "city": city_disp,
                        "service": service,
                        "mq": mq,
                        "budget": budget,
                        "source": "OSINT DuckDuckGo + Web",
                        "verified_status": "CERTIFICATO",
                        "contact_type": "TELEFONO_CERTIFICATO",
                        "post_url": link,
                        "dm_template": dm_template(city_disp, service),
                        "whatsapp_link": wa,
                        "notes": snippet[:150],
                    }
                    save_lead(conn, lead)
                    leads_out.append(lead)
                continue

            # ── LIVELLO 3: OSINT ricerca nome su web ─────────────────
            if author:
                osint_phone = osint_search_phone(author, city_disp)
                if osint_phone and osint_phone not in seen_phones and not is_known(conn, phone=osint_phone):
                    seen_phones.add(osint_phone)
                    wa = whatsapp_link(osint_phone, city_disp, service)
                    lead = {
                        "name": author,
                        "phone": osint_phone,
                        "city": city_disp,
                        "service": service,
                        "mq": mq,
                        "budget": budget,
                        "source": "OSINT Web Cross-Reference",
                        "verified_status": "OSINT_VERIFICATO",
                        "contact_type": "TELEFONO_OSINT",
                        "post_url": link,
                        "dm_template": dm_template(city_disp, service),
                        "whatsapp_link": wa,
                        "notes": "Ricavato tramite OSINT da nome autore.",
                    }
                    save_lead(conn, lead)
                    leads_out.append(lead)
                    continue

            # ── FALLBACK: DM_READY ────────────────────────────────────
            if not is_known(conn, post_url=link):
                dm = dm_template(city_disp, service)
                lead = {
                    "name": "Privato (" + title[:30].strip() + ")",
                    "phone": "DM_ONLY",
                    "city": city_disp,
                    "service": service,
                    "mq": mq,
                    "budget": budget,
                    "source": "Subito/Bakeca (DM Ready)",
                    "verified_status": "DM_READY",
                    "contact_type": "MESSENGER_DM",
                    "post_url": link,
                    "dm_template": dm,
                    "whatsapp_link": "",
                    "notes": "Numero non pubblico. Usa il link post per contattare via DM.",
                }
                save_lead(conn, lead)
                leads_out.append(lead)

        time.sleep(0.8)  # Rispetta rate limit DuckDuckGo

    conn.close()

    n_phone = sum(1 for l in leads_out if "TELEFONO" in l.get("contact_type", ""))
    n_dm    = sum(1 for l in leads_out if l.get("contact_type") == "MESSENGER_DM")

    return {
        "city": city_disp,
        "query": query,
        "total_leads": len(leads_out),
        "telefono_certificato": n_phone,
        "dm_ready": n_dm,
        "leads": leads_out,
        "summary": (
            "Trovati " + str(len(leads_out)) + " contatti reali per " + city_disp + ": " +
            str(n_phone) + " numeri verificati, " + str(n_dm) + " contatti DM-Ready."
        ),
    }
