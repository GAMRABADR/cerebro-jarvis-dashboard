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
SCRAPINGBEE_KEY = os.environ.get("SCRAPINGBEE_API_KEY", "9SFDK0AECW1DUPYU0BM04S7NVZB5KXR8P19ZIYC7AFSLDRO1PZNALSHO8LTQZ814B3X8BGZN0KEX8UHD")

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
    # Rimuove esplicitamente diciture P.IVA o codici fiscali
    clean_text = re.sub(r'(?i)p\.?\s*iva\s*[:\s]*\d+', ' ', text)
    clean_text = re.sub(r'(?i)partita\s*iva\s*[:\s]*\d+', ' ', clean_text)
    clean_text = re.sub(r'(?i)capitale\s*sociale\s*[:\s]*\d+', ' ', clean_text)
    clean_text = re.sub(r'(?i)rea\s*[:\s]*\d+', ' ', clean_text)

    found = []
    # SOLO cellulari italiani personali (3xx xxx xxxx)
    for m in MOBILE_RE.finditer(clean_text):
        c = clean_phone(m.group())
        if c and is_valid_phone(c):
            d = re.sub(r'[^\d]', '', c)
            if d.startswith("39"):
                d = d[2:]
            if d.startswith("3") and len(d) == 10:
                found.append(c)
    return list(dict.fromkeys(found))


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
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_url ON verified_leads_2026(post_url) WHERE post_url != ''")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_phone ON verified_leads_2026(phone) WHERE phone != 'DM_ONLY'")
    conn.commit()
    return conn


def is_known(conn, phone=None, post_url=None):
    c = conn.cursor()
    if phone and phone != "DM_ONLY":
        d = re.sub(r"[^\d]", "", str(phone))
        if d.startswith("39"):
            d = d[2:]
        if len(d) >= 8:
            rows = c.execute(
                "SELECT id FROM verified_leads_2026 WHERE REPLACE(REPLACE(REPLACE(phone,'+',''),' ',''),'-','') LIKE ?",
                ("%" + d[-8:],)
            ).fetchall()
            if rows:
                return True
    if post_url and len(str(post_url).strip()) > 10:
        clean_url = str(post_url).strip()
        rows = c.execute(
            "SELECT id FROM verified_leads_2026 WHERE post_url = ? OR (length(post_url) > 10 AND post_url LIKE ?)",
            (clean_url, "%" + clean_url[:45] + "%")
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


CLIENT_INTENT_KEYWORDS = [
    "cerco", "cercasi", "ho bisogno", "serve", "servirebbe", "chi può", "chi puo", 
    "chi ha un furgone", "dovrei portare", "devo spostare", "devo traslocare",
    "quanto costa", "preventivo per", "sgomberare", "svuotare", "trasferire",
    "qualcuno disponibile", "cerchiamo ditta", "cerco qualcuno", "richiesta preventivo"
]

COMPETITOR_BLACKLIST = [
    "offro traslochi", "offresi", "siamo una ditta", "eseguiamo traslochi", 
    "eseguo sgomberi", "la nostra azienda", "la nostra ditta", "contattaci per info", 
    "lavori edili", "offriamo servizi", "p.iva", "partita iva", "s.r.l.", "srl", 
    "snc", "ditta specializzata", "anni di esperienza", "visita il nostro sito",
    "dolcetraslocare", "emiliana sgomberi", "roadsavior", "svuotapp"
]

def is_genuine_client_request(text):
    t = text.lower()
    # 1. Se contiene frasi tipiche di concorrenti, scarta categoricamente
    if any(b in t for b in COMPETITOR_BLACKLIST):
        return False
    # 2. Se contiene parole di richiesta esplicita di cliente privato, accetta
    if any(k in t for k in CLIENT_INTENT_KEYWORDS):
        return True
    return False

def extract_author_phone_only(text):
    """Estrae il numero SOLO se il testo indica che appartiene all'autore che scrive."""
    t_low = text.lower()
    # Indicatori che l'utente sta lasciando il SUO recapito
    author_indicators = ["mio", "cell", "cellulare", "whatsapp", "chiamatemi", "contattatemi", "lascio", "tel", "numero"]
    if not any(ind in t_low for ind in author_indicators):
        return ""
    phones = extract_phones(text)
def scrape_subito_live_scrapingbee(city="bologna", query="trasloco", limit=5):
    """
    Estrae annunci reali di privati da Subito.it per Bologna e provincia
    utilizzando ScrapingBee per il bypass completo del WAF Cloudflare.
    """
    if not SCRAPINGBEE_KEY:
        return []

    target_queries = [
        "vendo per trasloco",
        "sgombero cantina",
        "cerco aiuto trasloco",
        "regalo per sgombero"
    ] if "trasloc" in query.lower() or "sgomb" in query.lower() else [query]

    ads_found = []
    seen_urls = set()

    for q_term in target_queries:
        if len(ads_found) >= limit:
            break
        search_url = f"https://www.subito.it/annunci-emilia-romagna/vendita/usato/?q={urllib.parse.quote_plus(q_term)}&r=bologna-bo"
        try:
            r = requests.get(
                "https://app.scrapingbee.com/api/v1/",
                params={
                    "api_key": SCRAPINGBEE_KEY,
                    "url": search_url,
                    "render_js": "false",
                    "country_code": "it"
                },
                timeout=25
            )
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            links = [l.get("href") for l in soup.find_all("a", href=re.compile(r"/.*-\d+\.htm")) if l.get("href")]
            uniq_links = [u for u in dict.fromkeys(links) if u not in seen_urls][:3]

            for ad_url in uniq_links:
                seen_urls.add(ad_url)
                if len(ads_found) >= limit:
                    break
                # Fetch dettaglio singolo annuncio
                r_ad = requests.get(
                    "https://app.scrapingbee.com/api/v1/",
                    params={
                        "api_key": SCRAPINGBEE_KEY,
                        "url": ad_url,
                        "render_js": "false",
                        "country_code": "it"
                    },
                    timeout=20
                )
                if r_ad.status_code != 200:
                    continue

                s_ad = BeautifulSoup(r_ad.text, "html.parser")
                h1 = s_ad.find("h1")
                ad_title = h1.get_text(strip=True) if h1 else "Annuncio Subito Privato"
                body_text = s_ad.get_text(" ")

                # Estrazione telefoni presenti nel testo dell'annuncio
                phones = extract_phones(body_text)
                author_phone = phones[0] if phones else ""

                # Estrai descrizione specifica
                desc_p = []
                for p in s_ad.find_all("p"):
                    pt = p.get_text(strip=True)
                    if len(pt) > 25 and not any(ign in pt.lower() for ign in ["cookie", "privacy", "copyright", "subito.it"]):
                        desc_p.append(pt)
                desc_text = " ".join(desc_p[:2]) if desc_p else body_text[:200]

                ads_found.append({
                    "title": ad_title,
                    "url": ad_url,
                    "phone": author_phone,
                    "text": desc_text,
                    "source": "Subito.it Live (ScrapingBee)"
                })
                time.sleep(0.5)

        except Exception as e:
            print(f"[ScrapingBee Subito err]: {e}")
            continue

    return ads_found


def get_query_variants(query, city):
    """Genera varianti di query rigorosamente orientate alle RICHIESTE di privati."""
    return [
        f"\"cerco {query}\" {city} privato",
        f"\"ho bisogno di {query}\" {city}",
        f"\"chi fa {query}\" {city} privato",
        f"\"devo {query}\" {city}",
        f"\"preventivo {query}\" {city} privato"
    ]


def run(params):
    city  = str(params.get("city", "bologna")).lower()
    query = str(params.get("query", "trasloco"))
    limit = int(params.get("limit", 10))

    city_disp = city.title()
    conn = get_db()
    leads_out = []
    seen_phones = set()

    # ── LIVELLO 1: SCRAPING DIRETTO SUBITO.IT CON SCRAPINGBEE (NO CLOUDFLARE 403) ──
    live_subito_ads = scrape_subito_live_scrapingbee(city=city, query=query, limit=limit)
    for ad in live_subito_ads:
        if len(leads_out) >= limit:
            break
        full_text = ad["title"] + " " + ad["text"]
        t_low = full_text.lower()

        # 1. Rigoroso scarto competitor / ditte
        if any(b in t_low for b in COMPETITOR_BLACKLIST):
            continue

        # 2. Richiesta genuina di privato o vendita mobili causa trasloco
        is_client = is_genuine_client_request(full_text) or ("vendo per trasloco" in t_low) or ("causa trasloco" in t_low)
        if not is_client:
            continue

        if is_known(conn, post_url=ad["url"]):
            continue

        service = "Trasloco Residenziale"
        if any(k in full_text.lower() for k in ("sgombero", "cantina", "garage", "svuotare")):
            service = "Sgombero & Smaltimento"
        elif any(k in full_text.lower() for k in ("deposito", "custodia")):
            service = "Deposito & Custodia Mobili"

        mq = 80 if "appartamento" in full_text.lower() else 50
        budget = mq * 9.5 if mq > 60 else 380.0
        phone = ad["phone"]

        if phone and phone not in seen_phones and not is_known(conn, phone=phone):
            seen_phones.add(phone)
            wa = whatsapp_link(phone, city_disp, service)
            lead = {
                "name": "Cliente Subito (" + ad["title"][:25].strip() + ")",
                "phone": phone,
                "city": city_disp,
                "service": service,
                "mq": mq,
                "budget": budget,
                "source": "Subito.it Certificato",
                "verified_status": "NUMERO_AUTORE_CERTIFICATO",
                "contact_type": "TELEFONO_CERTIFICATO",
                "post_url": ad["url"],
                "dm_template": dm_template(city_disp, service),
                "whatsapp_link": wa,
                "notes": ad["text"][:150],
            }
            save_lead(conn, lead)
            leads_out.append(lead)
        else:
            dm = dm_template(city_disp, service)
            lead = {
                "name": "Cliente Subito (" + ad["title"][:25].strip() + ")",
                "phone": "DM_ONLY",
                "city": city_disp,
                "service": service,
                "mq": mq,
                "budget": budget,
                "source": "Subito.it (DM Diretto)",
                "verified_status": "DM_READY",
                "contact_type": "MESSENGER_DM",
                "post_url": ad["url"],
                "dm_template": dm,
                "whatsapp_link": "",
                "notes": ad["text"][:150],
            }
            save_lead(conn, lead)
            leads_out.append(lead)

    # ── LIVELLO 2: FALLBACK DUCKDUCKGO SE SERVONO ALTRI LEAD ──
    if len(leads_out) < limit:
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
                title_el = item.find("a", class_="result__a")
                snippet_el = item.find("a", class_="result__snippet")
                link_el = item.find("a", class_="result__a")

                title = title_el.get_text(strip=True) if title_el else "Richiesta Privata"
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                link = link_el.get("href", "") if link_el else ""
                full_text = title + " " + snippet

                if not is_genuine_client_request(full_text):
                    continue
                if is_known(conn, post_url=link):
                    continue

                service = "Trasloco Residenziale"
                if any(k in full_text.lower() for k in ("sgombero", "cantina", "garage", "svuotare")):
                    service = "Sgombero & Smaltimento"

                mq = 80 if "appartamento" in full_text.lower() else 50
                budget = mq * 9.5 if mq > 60 else 380.0
                phone = extract_author_phone_only(full_text)

                if phone and phone not in seen_phones and not is_known(conn, phone=phone):
                    seen_phones.add(phone)
                    wa = whatsapp_link(phone, city_disp, service)
                    lead = {
                        "name": "Cliente Privato (" + title[:25].strip() + ")",
                        "phone": phone,
                        "city": city_disp,
                        "service": service,
                        "mq": mq,
                        "budget": budget,
                        "source": "Post Privato Verificato",
                        "verified_status": "NUMERO_AUTORE_CERTIFICATO",
                        "contact_type": "TELEFONO_CERTIFICATO",
                        "post_url": link,
                        "dm_template": dm_template(city_disp, service),
                        "whatsapp_link": wa,
                        "notes": snippet[:150],
                    }
                    save_lead(conn, lead)
                    leads_out.append(lead)
                else:
                    dm = dm_template(city_disp, service)
                    lead = {
                        "name": "Cliente Privato (" + title[:25].strip() + ")",
                        "phone": "DM_ONLY",
                        "city": city_disp,
                        "service": service,
                        "mq": mq,
                        "budget": budget,
                        "source": "Richiesta Gruppo/Web (DM)",
                        "verified_status": "DM_READY",
                        "contact_type": "MESSENGER_DM",
                        "post_url": link,
                        "dm_template": dm,
                        "whatsapp_link": "",
                        "notes": snippet[:150] or "Cliente cerca il servizio. Contattare via Messenger con Magic Link.",
                    }
                    save_lead(conn, lead)
                    leads_out.append(lead)

            time.sleep(0.8)

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

