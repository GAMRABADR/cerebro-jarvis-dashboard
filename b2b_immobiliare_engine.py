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
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")

PHONE_BADR = "+39 388 870 3508"
PHONE_PIETRO = "+39 328 426 3554"
SITE_BADR = "https://www.badrexpress.com"
SITE_PIETRO = "https://www.pietrotraslochi.com"
EMAIL_SENDER = os.environ.get("GMAIL_USER", "badraudi@gmail.com")
EMAIL_PASS = os.environ.get("GMAIL_APP_PASSWORD", "kqvjcuzibizysoxu")

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

# ── CENSIMENTO AGENZIE VIA OVERPASS OSM (Zero Costi, Dati Veri) ───────────────
def scout_agencies_osm(city="Bologna", limit=20):
    """Interroga OpenStreetMap Overpass API per trovare agenzie immobiliari reali."""
    overpass_query = f"""
    [out:json][timeout:20];
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
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "EBJ-B2B-Scout/2.0"})
    
    agencies = []
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            elements = res_json.get("elements", [])
            conn = sqlite3.connect(VAULT_DB)
            c = conn.cursor()

            for el in elements:
                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("brand")
                if not name:
                    continue
                
                street = tags.get("addr:street", "")
                housenumber = tags.get("addr:housenumber", "")
                address = f"{street} {housenumber}".strip() if street else "Indirizzo locale"
                phone = tags.get("phone") or tags.get("contact:phone") or tags.get("mobile") or "Su richiesta"
                email = tags.get("email") or tags.get("contact:email") or ""
                website = tags.get("website") or tags.get("contact:website") or ""

                agency_obj = {
                    "agency_name": name,
                    "city": city,
                    "address": address,
                    "phone": phone,
                    "email": email,
                    "website": website,
                    "status": "SCOUTED"
                }
                agencies.append(agency_obj)

                # Salva nel DB con protezione anti-duplicati
                c.execute("""
                    INSERT INTO b2b_real_estate_agencies (agency_name, city, address, phone, email, website, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'SCOUTED')
                    ON CONFLICT(agency_name, city) DO UPDATE SET
                    phone=COALESCE(excluded.phone, phone),
                    email=COALESCE(NULLIF(excluded.email,''), email),
                    address=COALESCE(NULLIF(excluded.address,''), address)
                """, (name, city, address, phone, email, website))

            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[OSM Scout Err ({city})]: {e}")
        # Se Overpass va in timeout o rate-limit, estrai da cache SQLite
        conn = sqlite3.connect(VAULT_DB)
        c = conn.cursor()
        c.execute("SELECT agency_name, city, address, phone, email, website, status FROM b2b_real_estate_agencies WHERE city=? LIMIT ?", (city, limit))
        for row in c.fetchall():
            agencies.append({
                "agency_name": row[0],
                "city": row[1],
                "address": row[2],
                "phone": row[3],
                "email": row[4],
                "website": row[5],
                "status": row[6]
            })
        conn.close()

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
