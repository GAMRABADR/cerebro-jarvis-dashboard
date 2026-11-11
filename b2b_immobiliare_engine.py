# ── b2b_immobiliare_engine.py ─────────────────────────────────────────────
#  E.B.J. AI — Motore Autonomo B2B Partnership Agenzie Immobiliari
#  Scouting, Generazione Proposte Personalizzate, Calcolo Sgomberi & Dispatch
# ────────────────────────────────────────────────────────────────────────────

import os
import json
import sqlite3
import datetime
import urllib.request
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))
except Exception:
    pass
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")

PHONE_BADR = "+39 388 870 3508"
PHONE_PIETRO = "+39 328 426 3554"
SITE_BADR = "https://www.badrexpress.com"
SITE_PIETRO = "https://www.pietrotraslochi.com"
EMAIL_SENDER = os.environ.get("GMAIL_USER", "badraudi@gmail.com")
EMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("GMAIL_APP_PASS") or os.environ.get("SMTP_PASS") or os.environ.get("GMAIL_PASSWORD") or ""

def init_b2b_tables():
    """Crea la tabella SQLite per tracciare le agenzie immobiliari partner."""
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS b2b_real_estate_agencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agency_name TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            status TEXT DEFAULT 'SCOUTED',
            proposal_sent_at TEXT,
            last_response TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(agency_name, city)
        )
    """)
    conn.commit()
    conn.close()

init_b2b_tables()

# ── CENSIMENTO AGENZIE LIVE (CACHE -> PAGINEGIALLE -> SITO -> OVERPASS) ───────
def scout_agencies_osm(city="Bologna", limit=20, force_refresh=False):
    """Interroga cache SQLite locale o esegue discovery reale (PagineGialle + siti ufficiali + Overpass OSM)."""
    import b2b_agency_crawler as crawler
    from ebj_lead_sanitizer import validate_italian_phone

    crawler.ensure_crm_schema()
    if not force_refresh:
        try:
            conn = sqlite3.connect(VAULT_DB)
            c = conn.cursor()
            c.execute(
                """SELECT agency_name, city, address, phone, email, website, status, facebook_url, contact_form_url
                   FROM b2b_real_estate_agencies WHERE LOWER(city)=LOWER(?) ORDER BY id DESC LIMIT ?""",
                (city, limit),
            )
            rows = c.fetchall()
            conn.close()
            if rows and len(rows) >= min(limit, 5):
                return [
                    {
                        "agency_name": r[0], "city": r[1], "address": r[2],
                        "phone": r[3], "email": r[4], "website": r[5],
                        "status": r[6], "facebook_url": r[7] or "", "contact_form_url": r[8] or "",
                    }
                    for r in rows
                ]
        except Exception:
            pass

    agencies = crawler.scrape_paginegialle_agencies(city=city, limit=limit, crawl_websites=True)
    if len(agencies) < min(limit, 5):
        overpass_query = f"""
        [out:json][timeout:15];
        area["name"="{city}"]["boundary"="administrative"]->.a;
        (
          node["office"="estate_agent"](area.a);
          way["office"="estate_agent"](area.a);
          node["shop"="estate_agent"](area.a);
        );
        out center {limit};
        """
        url = "https://overpass-api.de/api/interpreter"
        data = urllib.parse.urlencode({"data": overpass_query}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "EBJ-B2B-Scout/2.5"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                elements = json.loads(resp.read().decode("utf-8")).get("elements", [])
                conn = sqlite3.connect(VAULT_DB)
                c = conn.cursor()
                for el in elements:
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("brand")
                    if not name:
                        continue
                    street = tags.get("addr:street", "")
                    housenumber = tags.get("addr:housenumber", "")
                    address = f"{street} {housenumber}".strip() or city
                    raw_ph = tags.get("phone") or tags.get("contact:phone") or tags.get("mobile") or ""
                    ph_res = validate_italian_phone(raw_ph, strict_mobile_10=False)
                    phone = ph_res["e164"] if ph_res else ""
                    email = tags.get("email") or tags.get("contact:email") or ""
                    website = tags.get("website") or tags.get("contact:website") or ""
                    agency_obj = {
                        "agency_name": name, "city": city, "address": address,
                        "phone": phone, "email": email, "website": website,
                        "status": "VERIFICATO_OSM", "facebook_url": "", "contact_form_url": "",
                    }
                    agencies.append(agency_obj)
                    c.execute(
                        """
                        INSERT INTO b2b_real_estate_agencies (agency_name, city, address, phone, email, website, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'VERIFICATO_OSM')
                        ON CONFLICT(agency_name, city) DO UPDATE SET
                        phone=COALESCE(NULLIF(excluded.phone,''), phone),
                        email=COALESCE(NULLIF(excluded.email,''), email),
                        website=COALESCE(NULLIF(excluded.website,''), website)
                        """,
                        (name, city, address, phone, email, website),
                    )
                conn.commit()
                conn.close()
        except Exception:
            pass

    if not agencies:
        try:
            conn = sqlite3.connect(VAULT_DB)
            c = conn.cursor()
            c.execute(
                "SELECT agency_name, city, address, phone, email, website, status, facebook_url, contact_form_url FROM b2b_real_estate_agencies WHERE LOWER(city)=LOWER(?) LIMIT ?",
                (city, limit),
            )
            for row in c.fetchall():
                agencies.append({
                    "agency_name": row[0], "city": row[1], "address": row[2],
                    "phone": row[3], "email": row[4], "website": row[5],
                    "status": row[6], "facebook_url": row[7] or "", "contact_form_url": row[8] or "",
                })
            conn.close()
        except Exception:
            pass

    return agencies

# ── CALCOLATORE PREVENTIVI SGOMBERI PER AGENZIE IMMOBILIARI ──────────────────
def calculate_agency_sgombero(tipo_immobile="trilocale", piano=2, ascensore=False, smaltimento_speciale=False):
    """
    Calcola un preventivo professionale sgombero per agenzie con listino agevolato B2B.
    """
    tariffe_base = {
        "cantina": {"mq": 12, "base": 180.0, "ore_stimate": 3},
        "garage": {"mq": 18, "base": 240.0, "ore_stimate": 4},
        "soffitta": {"mq": 20, "base": 260.0, "ore_stimate": 4},
        "monolocale": {"mq": 35, "base": 380.0, "ore_stimate": 5},
        "bilocale": {"mq": 55, "base": 550.0, "ore_stimate": 7},
        "trilocale": {"mq": 80, "base": 780.0, "ore_stimate": 9},
        "quadrilocale_villa": {"mq": 120, "base": 1150.0, "ore_stimate": 12}
    }
    
    info = tariffe_base.get(tipo_immobile.lower(), tariffe_base["trilocale"])
    prezzo_base = info["base"]
    
    # Quota scale
    quota_piano = 0.0 if ascensore else max(0, piano) * 35.0
    # Smaltimento speciale (es. vernici, pneumatici, RAEE ingombranti)
    quota_smaltimento = 90.0 if smaltimento_speciale else 40.0
    
    subtotale = prezzo_base + quota_piano + quota_smaltimento
    # Sconto Convenzione Agenzia B2B: 15%
    sconto_agenzia = round(subtotale * 0.15, 2)
    prezzo_finale = round(subtotale - sconto_agenzia, 2)
    # Provvigione riconosciuta all'agenzia segnalatrice (10%)
    provvigione_partner = round(prezzo_finale * 0.10, 2)

    return {
        "tipo_immobile": tipo_immobile,
        "piano": piano,
        "ascensore": ascensore,
        "prezzo_listino": subtotale,
        "sconto_partner_b2b": sconto_agenzia,
        "prezzo_finale_agenzia": prezzo_finale,
        "provvigione_riconosciuta": provvigione_partner,
        "tempistica_garantita": "Entro 24/48 ore dalla conferma",
        "servizi_inclusi": [
            "Furgone maxi con sponda idraulica",
            "Personale qualificato con assicurazione RCT",
            "Spazzata e pulizia finale dei locali post-sgombero",
            "Conferimento a discarica autorizzata con formulario rifiuti",
            "Fatturazione regolare P.IVA"
        ],
        "contatti_rapidi": {
            "badr": PHONE_BADR,
            "pietro": PHONE_PIETRO,
            "sito": SITE_BADR
        }
    }

# ── GENERATORE COPYWRITING PERSONALIZZATO PER IMMOBILIARI ────────────────────
def compose_agency_b2b_email(agency_name, city="Bologna", contact_person="Responsabile Compravendite"):
    """
    Genera un testo persuasivo, formale, autorevole e studiato appositamente per agenzie immobiliari.
    Risolve il loro problema numero 1: liberare gli immobili prima del rogito notarile senza intoppi.
    """
    subject = f"Convenzione Sgomberi & Traslochi Pre-Rogito per {agency_name} — BadrExpress & PietroTraslochi"

    body_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
.box {{ max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }}
.head {{ background: linear-gradient(135deg, #090d16, #1e293b); color: #ffffff; padding: 28px; text-align: center; }}
.title {{ font-size: 22px; font-weight: 800; color: #00f0ff; letter-spacing: 0.5px; margin: 0; }}
.sub {{ font-size: 13px; color: #94a3b8; margin-top: 6px; }}
.body {{ padding: 28px; line-height: 1.6; font-size: 14px; }}
.badge {{ display: inline-block; background: #e0f2fe; color: #0284c7; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 11px; }}
.benefit-card {{ background: #f1f5f9; border-left: 4px solid #00f0ff; padding: 14px; border-radius: 6px; margin: 16px 0; }}
.cta-btn {{ display: inline-block; background: #0284c7; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: 700; font-size: 14px; margin-top: 12px; }}
.footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="box">
  <div class="head">
    <div class="title">🤝 CONVENZIONE B2B SGOMBERI & TRASLOCHI</div>
    <div class="sub">Servizio Espresso Pre-Rogito per {agency_name} · {city} e provincia</div>
  </div>
  <div class="body">
    <p>Gentile <strong>{contact_person}</strong> di <strong>{agency_name}</strong>,</p>

    <p>Sappiamo per esperienza diretta che uno dei momenti più delicati nella compravendita immobiliare è la <strong>consegna dell'immobile libero da mobili, cantine piene e masserizie entro la data del rogito notarile</strong>.</p>

    <p>Siamo <strong>BadrExpress & PietroTraslochi</strong>, ditta specializzata operante a <strong>{city}</strong> e in tutta la regione. Proponiamo a {agency_name} una convenzione operativa diretta studiata per togliere ogni pensiero ai Vostri agenti e ai Vostri clienti venditori/acquirenti:</p>

    <div class="benefit-card">
      <div style="font-weight: 800; color: #0f172a; margin-bottom: 6px;">💎 VANTAGGI ESCLUSIVI PER {agency_name.upper()}:</div>
      • <strong>Intervento Rapido Garantito (24-48h):</strong> Liberiamo cantine, solai, appartamenti completi e box anche con urgenza pre-rogito.<br/>
      • <strong>Sconto Convenzione 15%:</strong> Riservato a tutti i clienti presentati dalla Vostra Agenzia.<br/>
      • <strong>Provvigione Segnalazione 10%:</strong> Riconosciuta all'agenzia su ogni incarico portato a termine.<br/>
      • <strong>Pulizia Finale Post-Sgombero Inclusa:</strong> I locali vengono lasciati spazzati e pronti per la consegna delle chiavi.<br/>
      • <strong>Smaltimento a Norma con Formulario Rifiuti:</strong> Massima tutela legale contro l'abbandono abusivo.<br/>
      • <strong>Fatturazione Trasparente con P.IVA:</strong> Assicurazione RCT su tutti i trasporti e movimentazioni.
    </div>

    <p><strong>Preventivo Rapido WhatsApp:</strong> Mandateci 2 foto o un breve video dei locali su WhatsApp e Vi forniamo il preventivo esatto in <strong>meno di 30 minuti</strong>.</p>

    <div style="text-align: center; margin: 24px 0;">
      <a href="https://wa.me/393888703508?text=Salve%20Badr,%20sono%20di%20{urllib.parse.quote(agency_name)}%20da%20{urllib.parse.quote(city)}.%20Vorrei%20informazioni%20sulla%20convenzione%20sgomberi." class="cta-btn" style="background:#25D366; color:#fff;">💬 Contattaci su WhatsApp: {PHONE_BADR}</a>
    </div>

    <p style="margin-bottom: 0;">
      Disponibili per un breve caffè conoscitivo presso la Vostra sede per consegnare il listino cartaceo e presentarci di persona.
    </p>
  </div>

  <div class="footer">
    <strong>Badr El Ouariti</strong> ({PHONE_BADR}) · <strong>Pietro</strong> ({PHONE_PIETRO})<br/>
    BadrExpress & PietroTraslochi · {SITE_BADR} · {SITE_PIETRO}<br/>
    Servizi Espressi di Logistica, Sgomberi Certificati & Traslochi Civili / Commerciali
  </div>
</div>
</body>
</html>"""

    body_plain = f"""Gentile {contact_person} di {agency_name},

Siamo BadrExpress & PietroTraslochi, ditta specializzata in sgomberi e traslochi a {city} e provincia.
Le proponiamo una convenzione B2B dedicata alla Vostra agenzia per gestire in totale serenità la liberazione degli immobili prima del rogito notarile.

VANTAGGI PER {agency_name.upper()}:
- Interventi rapidi garantiti entro 24-48 ore (cantine, solai, appartamenti interi)
- Sconto del 15% sul listino per tutti i Vostri clienti
- Provvigione del 10% riconosciuta all'agenzia su ogni commessa
- Pulizia finale e spazzata dei locali post-sgombero inclusa
- Smaltimento rifiuti autorizzato con formulario di legge
- Fatturazione regolare con P.IVA e copertura assicurativa RCT

PREVENTIVI ISTANTANEI VIA WHATSAPP:
Inviateci 2 foto o un video dei locali da sgomberare al numero {PHONE_BADR} per ricevere il preventivo in meno di 30 minuti.

CONTATTI DIRETTI:
- Badr El Ouariti: {PHONE_BADR} (WhatsApp & Chiamate)
- Pietro: {PHONE_PIETRO}
- Sito Web Ufficiale: {SITE_BADR} / {SITE_PIETRO}

Restiamo a disposizione per una breve visita conoscitiva senza impegno presso la Vostra sede.

Cordiali saluti,
Badr El Ouariti & Pietro
BadrExpress.com & PietroTraslochi.com
"""

    return {
        "agency_name": agency_name,
        "city": city,
        "subject": subject,
        "body_html": body_html,
        "body_plain": body_plain,
        "phone_badr": PHONE_BADR,
        "phone_pietro": PHONE_PIETRO,
        "website": SITE_BADR
    }

# ── DISPATCH EMAIL B2B REALE VIA SMTP ────────────────────────────────────────
def send_agency_proposal_email(agency_name, to_email, city="Bologna", contact_person="Responsabile"):
    """Invia l'email formale di convenzione direttamente alla casella dell'agenzia."""
    if not to_email or "@" not in to_email:
        return {"success": False, "error": "Email agenzia non valida o assente"}

    pack = compose_agency_b2b_email(agency_name, city, contact_person)
    
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"BadrExpress & PietroTraslochi <{EMAIL_SENDER}>"
        msg["To"] = to_email
        msg["Subject"] = pack["subject"]
        msg["Reply-To"] = EMAIL_SENDER

        msg.attach(MIMEText(pack["body_plain"], "plain", "utf-8"))
        msg.attach(MIMEText(pack["body_html"], "html", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=12)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASS)
        server.sendmail(EMAIL_SENDER, [to_email], msg.as_string())
        server.quit()

        # Aggiorna lo stato nel database
        conn = sqlite3.connect(VAULT_DB)
        c = conn.cursor()
        c.execute("""
            UPDATE b2b_real_estate_agencies 
            SET status='PROPOSTA_INVIATA', proposal_sent_at=?
            WHERE agency_name=? AND city=?
        """, (datetime.datetime.now().isoformat(), agency_name, city))
        conn.commit()
        conn.close()

        return {
            "success": True, 
            "status": "INVIATA", 
            "to": to_email, 
            "agency": agency_name,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── CAMPAGNA AUTONOMA COLLABORAZIONE SGOMBERI & PORTALI IMMOBILIARI ──────────
def run_sgomberi_collaboration_campaign(city="ALL", limit=10, dry_run=False):
    """
    Seleziona le agenzie immobiliari verificate con email reale (MX/DNS confermato)
    non ancora contattate e invia la proposta di convenzione sgomberi pre-rogito & traslochi.
    """
    from ebj_lead_sanitizer import validate_email_address, validate_italian_phone
    import b2b_agency_crawler as crawler

    crawler.ensure_crm_schema()
    conn = sqlite3.connect(VAULT_DB)
    q = """SELECT id, agency_name, city, phone, email, website, facebook_url, contact_form_url, status
           FROM b2b_real_estate_agencies
           WHERE COALESCE(status, '') != 'PROPOSTA_INVIATA'"""
    params = []
    if city and city.upper() != "ALL":
        q += " AND LOWER(city) LIKE ?"
        params.append(f"%{city.lower()}%")
    q += " ORDER BY id DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()

    candidates_email = []
    candidates_wa_only = []
    seen_emails = set()
    for rid, name, cty, phone, email, web, fb, cf, st in rows:
        if "costruzioni" in (web or "").lower() or name.strip().upper() == "ICEA":
            continue
        ok_em, _ = validate_email_address(email, check_dns=True) if email else (False, "no_email")
        ph_res = validate_italian_phone(phone, strict_mobile_10=False) if phone else None
        em_low = (email or "").strip().lower()
        if ok_em and em_low not in seen_emails:
            seen_emails.add(em_low)
            candidates_email.append({
                "id": rid, "agency_name": name, "city": cty,
                "email": em_low, "phone": ph_res["e164"] if ph_res else "",
                "website": web or "", "contact_form_url": cf or "",
            })
        elif ph_res:
            msg = f"Buongiorno {name}, siamo BadrExpress & PietroTraslochi ({cty}). Proponiamo convenzione diretta sgomberi pre-rogito 24-48h con sconto 15% ai vostri clienti e 10% di segnalazione."
            candidates_wa_only.append({
                "id": rid, "agency_name": name, "city": cty,
                "phone": ph_res["e164"],
                "whatsapp_url": f"{ph_res['wa_url']}?text={urllib.parse.quote(msg)}",
                "contact_form_url": cf or "",
                "facebook_url": fb or "",
            })

    sent = []
    errors = []
    smtp_ready = bool(EMAIL_PASS)
    for item in candidates_email[:limit]:
        if dry_run or not smtp_ready:
            sent.append({**item, "dispatch": "PREVIEW_DRY_RUN" if dry_run else "SKIPPED_NO_SMTP_PASSWORD"})
            continue
        res = send_agency_proposal_email(item["agency_name"], item["email"], city=item["city"])
        if res.get("success"):
            sent.append({**item, "dispatch": "SENT_SMTP"})
        else:
            errors.append({**item, "error": res.get("error")})

    return {
        "status": "SUCCESS",
        "city": city,
        "smtp_configured": smtp_ready,
        "dry_run": dry_run,
        "email_candidates_total": len(candidates_email),
        "processed_count": len(sent),
        "sent_or_preview": sent,
        "errors": errors,
        "whatsapp_and_form_ready": candidates_wa_only[:limit],
    }


def onboard_portals_safe(portals=None, submit=False):
    """
    Tenta la pre-compilazione/iscrizione di BadrExpress & PietroTraslochi sui portali immobiliari/traslochi
    con rilevamento automatico CAPTCHA (fail-closed: mai aggirare CAPTCHA).
    """
    import asyncio
    from playwright.async_api import async_playwright
    import real_estate_registrator as reg

    targets = portals or ["immobiliare", "idealista", "casa", "wikicasa", "guidatraslochi", "traslochi24"]
    portal_urls = {k: v["url"] for k, v in reg.PORTAL_PRESETS.items()}
    try:
        import universal_portal_registrator as upr
        for p_item in getattr(upr, "PORTALS_CATALOG", []):
            portal_urls.setdefault(p_item["id"], p_item["url"])
    except Exception:
        pass

    async def _run_all():
        out = []
        for t in targets:
            actual_url = portal_urls.get(t, t)
            if not str(actual_url).startswith("http"):
                out.append({"portal": t, "url": str(actual_url), "status": "INVALID_URL"})
                continue
            async with async_playwright() as p:
                br = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                ctx = await br.new_context(locale="it-IT", viewport={"width": 1366, "height": 768})
                pg = await ctx.new_page()
                try:
                    await pg.goto(actual_url, timeout=20000, wait_until="domcontentloaded")
                    await reg.dismiss_cookies(pg)
                    html_low = (await pg.content()).lower()
                    has_captcha = any(k in html_low for k in ("g-recaptcha", "hcaptcha", "turnstile", "datadome", "captcha-delivery"))
                    filled = await reg.auto_fill_form(pg, reg.DOSSIER)
                    if has_captcha:
                        out.append({"portal": t, "url": actual_url, "status": "CAPTCHA_REQUIRED", "fields_prefilled": len(filled), "note": "Portale protetto da CAPTCHA/WAF: completare verifica manuale."})
                    else:
                        sub_st = "READY_PREFILLED"
                        if submit and filled:
                            btn = pg.locator("button[type='submit'], input[type='submit']").first
                            if await btn.count() > 0 and await btn.is_visible():
                                await btn.click()
                                await pg.wait_for_timeout(2500)
                                sub_st = "SUBMITTED_AUTO"
                        out.append({"portal": t, "url": actual_url, "status": sub_st, "fields_prefilled": len(filled)})
                except Exception as exc:
                    out.append({"portal": t, "url": actual_url, "status": "ERROR", "error": str(exc)[:120]})
                finally:
                    await br.close()
        return out

    return asyncio.run(_run_all())
