# -*- coding: utf-8 -*-
"""
ebj_lead_sanitizer.py
Motore unico di validazione telefonica AGCOM, verifica email/MX,
classificazione coerenza lead (Privati vs Agenzie Immobiliari vs Competitor/Off-Topic)
e bonifica SQLite per BadrExpress.com & PietroTraslochi.com.
"""

from __future__ import annotations

import os
import re
import socket
import sqlite3
import datetime
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")

# Prefissi provinciali italiani certificati AGCOM (numerazione fissa 0xx)
VALID_DISTRICT_PREFIXES: Tuple[str, ...] = (
    "010", "011", "0121", "0122", "0123", "0124", "0125", "0131", "0141", "0142", "0143", "0144",
    "015", "0161", "0163", "0165", "0171", "0172", "0173", "0174", "0175", "0182", "0183", "0184", "0185", "0187",
    "02",
    "030", "031", "0321", "0322", "0323", "0324", "0331", "0332", "0341", "0342", "0343", "0344", "0345", "0346",
    "035", "0362", "0363", "0364", "0365", "0371", "0372", "0373", "0374", "0375", "0376", "0381", "0382", "0383", "0384", "0385", "0386",
    "040", "041", "0421", "0422", "0423", "0424", "0425", "0426", "0427", "0428", "0429", "0431", "0432", "0433", "0434", "0435", "0438", "0439",
    "0442", "0444", "0445", "045", "0461", "0462", "0463", "0464", "0465", "0471", "0472", "0473", "0474", "0481", "049",
    "050", "051", "0521", "0522", "0523", "0524", "0525", "0532", "0533", "0534", "0535", "0536", "0541", "0542", "0543", "0544", "0545", "0546", "0547",
    "055", "0564", "0565", "0566", "0571", "0572", "0573", "0574", "0575", "0577", "0578", "0583", "0584", "0585", "0586", "0587", "0588",
    "059",
    "06",
    "070", "071", "0721", "0722", "0731", "0732", "0733", "0734", "0735", "0736", "0737", "0742", "0743", "0744", "0746", "075", "0761", "0763", "0765", "0766",
    "0771", "0773", "0774", "0775", "0776", "0781", "0782", "0783", "0784", "0785", "0789", "079",
    "080", "081", "0823", "0824", "0825", "0827", "0828", "0831", "0832", "0833", "0835", "0836", "085", "0861", "0862", "0863", "0864", "0865",
    "0871", "0872", "0873", "0874", "0875", "0881", "0882", "0883", "0884", "0885", "089",
    "090", "091", "0921", "0922", "0923", "0924", "0925", "0931", "0932", "0933", "0934", "0935", "0941", "0942", "095", "0961", "0962", "0963", "0964", "0965", "0966", "0967", "0968",
    "0971", "0972", "0973", "0974", "0975", "0981", "0982", "0983", "0984", "0985"
)

VALID_DISTRICT_PREFIXES_SORTED = sorted(VALID_DISTRICT_PREFIXES, key=len, reverse=True)

SEQUENTIAL_OR_DUMMY_PATTERNS = (
    "012345", "123456", "234567", "345678", "456789", "567890",
    "987654", "876543", "765432", "654321", "543210",
    "000000", "111111", "222222", "333333", "444444", "555555",
    "666666", "777777", "888888", "999999", "121212", "123123",
    "8899001", "5544332",
)

BAD_SUFFIXES = ("12345", "23456", "34567", "45678", "56789", "67890", "98765", "87654", "76543", "65432", "54321")
TOLL_FREE_OR_SPECIAL_PREFIXES = ("800", "803", "840", "848", "892", "894", "895", "899", "199", "166", "144", "112", "113", "115", "118")

IT_WORD_DIGITS = {
    "zero": "0", "uno": "1", "due": "2", "tre": "3", "quattro": "4",
    "cinque": "5", "sei": "6", "sette": "7", "otto": "8", "nove": "9",
}

DISPOSABLE_EMAIL_DOMAINS = {
    "tempmail.com", "guerrillamail.com", "10minutemail.com", "mailinator.com",
    "yopmail.com", "trashmail.com", "throwawaymail.com", "getairmail.com",
    "sharklasers.com", "guerrillamailblock.com", "pokemail.net", "mohmal.com",
    "fakeinbox.com", "dispostable.com", "tempail.com", "mytemp.email",
    "example.com", "example.it", "test.com", "sentry.io", "wixpress.com",
}

_PHONE_CANDIDATE_RE = re.compile(
    r"(?<!\d)(?:(?:\+|00)39[\s.\-]*)?(?:3[1-9]\d(?:[\s.\-]?\d){7,8}|0\d{1,3}(?:[\s.\-]?\d){5,8})(?!\d)"
)

_EMAIL_RE = re.compile(r"\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,12})\b")

# Competitor / off-topic / client / agency lexicons
CLIENT_DEMAND_KEYWORDS = (
    "cerco trasloco", "cerco qualcuno", "cercasi furgone", "cerco furgone",
    "cerco aiuto", "chi fa sgomber", "chi può aiutarmi", "chi puo aiutarmi",
    "devo traslocare", "devo sgomberare", "devo svuotare", "svuoto appartamento",
    "svuoto cantina", "causa trasloco", "vendo per trasloco", "regalo mobili",
    "regalo per sgombero", "ho bisogno di un trasloco", "ho bisogno di sgomber",
    "preventivo per trasloco", "preventivo per sgombero", "cerchiamo ditta",
    "libero appartamento", "sgombero urgente cantina", "piccolo trasloco da",
    "trasporto divano", "trasporto cucina", "spostare mobili",
)

COMPETITOR_OFFER_KEYWORDS = (
    "siamo una ditta", "la nostra ditta", "la nostra azienda", "offriamo traslochi",
    "offro traslochi", "offriamo servizi di trasloco", "eseguiamo traslochi",
    "eseguo sgomberi", "preventivi gratuiti dal", "preventivo gratuito in",
    "noleggio autoscala", "autoscala fino a", "traslochi nazionali ed internazionali",
    "ditta di traslochi", "azienda di traslochi", "impresa di traslochi",
    "imprese di traslochi", "migliori ditte di traslochi", "top 10 traslochi",
    "quanto costa un trasloco", "quanto costa traslocare", "guida ai costi",
    "listino prezzi traslochi", "furgoni imbottiti", "imballaggio professionale offriamo",
    "trasporti conto terzi", "facchinaggio aziendale offresi", "svuotapp",
    "dolcetraslocare", "emiliana sgomberi", "roadsavior",
)

REAL_ESTATE_KEYWORDS = (
    "immobiliare", "agenzia immobiliare", "studio immobiliare", "consulenze immobiliari",
    "intermediazioni immobiliari", "mediazione immobiliare", "compravendita",
    "tempocasa", "tecnocasa", "tecnorete", "gabetti", "re/max", "remax", "toscano",
    "engel & völkers", "engel & volkers", "grimaldi", "fondocasa", "capitalhouse",
    "stimacasa", "vendocasa", "progetto casa", "interaffari", "piramide", "stop house",
    "case e ville", "real estate", "professionecasa", "pirelli re", "gabrielli immobiliare",
)

OFF_TOPIC_KEYWORDS = (
    "autolavaggio", "autolavaggi", "car wash", "schiuma attiva", "detergenza",
    "nanotech", "pista self service", "cerchiamo personale autista", "offresi lavoro",
    "cercasi autista", "vendesi furgone usato",
)

_OWN_NUMBERS = {"3888703508", "3284263554"}
_MX_CACHE: Dict[str, bool] = {}


def deobfuscate_spoken_numbers(text: str) -> str:
    """Converte sequenze di parole numeriche italiane adiacenti in cifre senza incollare numeri distanti."""
    if not text:
        return ""
    tokens = re.split(r"(\s+|[.,;:/()\-]+)", text)
    out: List[str] = []
    run_digits: List[str] = []

    def _flush_run():
        nonlocal run_digits
        if run_digits:
            if len(run_digits) >= 6:
                out.append("".join(run_digits))
            else:
                out.extend(run_digits)
            run_digits = []

    for tok in tokens:
        low = tok.lower().strip()
        if low in IT_WORD_DIGITS:
            run_digits.append(IT_WORD_DIGITS[low])
        elif re.fullmatch(r"\d{1,4}", low) and run_digits:
            run_digits.append(low)
        elif tok.strip() == "":
            if not run_digits:
                out.append(tok)
        else:
            _flush_run()
            out.append(tok)
    _flush_run()
    return "".join(out)


def validate_italian_phone(raw: Any, strict_mobile_10: bool = True) -> Optional[Dict[str, Any]]:
    """
    Valida e normalizza rigorosamente un numero telefonico italiano AGCOM.
    Ritorna dict normalizzato (e164, formatted, tel_uri, wa_url, line_type) oppure None se fake/non valido.
    """
    if not raw:
        return None
    raw_str = deobfuscate_spoken_numbers(str(raw).strip())

    # Gestione multi-numero ("+39 051... / +39 335...")
    if any(sep in raw_str for sep in ("/", ";", "\n")) or (raw_str.count("+") > 1):
        parts = [p.strip() for p in re.split(r"[/;\n,]+|(?=\+39)", raw_str) if p.strip()]
        if len(parts) > 1:
            for part in parts:
                res = validate_italian_phone(part, strict_mobile_10=strict_mobile_10)
                if res:
                    return res
            return None

    digits = re.sub(r"\D", "", raw_str)
    if not digits:
        return None

    # Rimuovi prefisso internazionale italiano
    if digits.startswith("0039"):
        digits = digits[4:]
    elif digits.startswith("39") and len(digits) in (11, 12, 13):
        digits = digits[2:]

    # Rifiuta propri numeri aziendali per evitare auto-loop
    if digits in _OWN_NUMBERS:
        return None

    # Lunghezza valida nazionale (8..11 cifre)
    if len(digits) < 8 or len(digits) > 11:
        return None

    # Rifiuta numeri verdi / speciali / emergenza
    if digits.startswith(TOLL_FREE_OR_SPECIAL_PREFIXES):
        return None

    # Rifiuta cifre ripetute troppo uniformi o sequenze artificiali
    if len(set(digits)) <= 2:
        return None
    if re.search(r"(\d)\1{4,}", digits):  # 5+ cifre identiche consecutive (00000, 11111, ...)
        return None
    for pat in SEQUENTIAL_OR_DUMMY_PATTERNS:
        if pat in digits:
            return None
    if digits.endswith(BAD_SUFFIXES):
        return None

    if digits.startswith("3"):
        valid_mob_len = (digits.startswith("3") and len(digits) == 10) if strict_mobile_10 else (len(digits) in (9, 10))
        if not valid_mob_len:
            return None
        if digits[1] not in "123456789":
            return None
        if len(set(digits)) < 4:
            return None
        line_type = "MOBILE"
        formatted = f"+39 {digits[:3]} {digits[3:6]} {digits[6:]}"
        prefix = digits[:3]
    elif digits.startswith("0"):
        matched_pfx = None
        for pfx in VALID_DISTRICT_PREFIXES_SORTED:
            if digits.startswith(pfx):
                matched_pfx = pfx
                break
        if not matched_pfx:
            return None
        sub = digits[len(matched_pfx):]
        if len(sub) < 5 or len(sub) > 8:
            return None
        if len(set(sub)) <= 1:
            return None
        line_type = "FISSO"
        formatted = f"+39 {matched_pfx} {sub[:3]} {sub[3:]}" if len(sub) >= 6 else f"+39 {matched_pfx} {sub}"
        prefix = matched_pfx
    else:
        return None

    e164 = f"+39{digits}"
    return {
        "raw": str(raw).strip(),
        "digits": digits,
        "e164": e164,
        "formatted": formatted,
        "tel_uri": f"tel:{e164}",
        "wa_url": f"https://wa.me/39{digits}",
        "line_type": line_type,
        "prefix": prefix,
        "is_mobile": line_type == "MOBILE",
        "is_landline": line_type == "FISSO",
    }


def extract_phones_from_text(text: str, author_only: bool = False, mobile_only: bool = False) -> List[Dict[str, Any]]:
    """
    Estrae solo numeri di telefono italiani reali e validati dal testo, senza mai concatenare
    numeri separati (es. metri quadri + euro).
    """
    if not text:
        return []
    work = deobfuscate_spoken_numbers(text)

    # Rimuove P.IVA, CF, prezzi, date, CAP/mq espliciti prima del match
    work = re.sub(r"(?i)(?:p\.?\s*iva|partita\s*iva|codice\s*fiscale|c\.?\s*f\.?|rea|capitale\s*sociale)\s*[:\-]?\s*[A-Z0-9]{8,16}", " ", work)
    work = re.sub(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", " ", work)
    work = re.sub(r"\b\d{2}[-/]\d{2}[-/]\d{4}\b", " ", work)

    if author_only:
        low = work.lower()
        author_cues = ("mio ", "cell", "cellulare", "whatsapp", "wa ", "chiamatemi", "chiami", "contattatemi", "lascio", "tel", "numero", "scrivetemi", "reperibile")
        if not any(cue in low for cue in author_cues):
            return []

    seen: set = set()
    results: List[Dict[str, Any]] = []
    for m in _PHONE_CANDIDATE_RE.finditer(work):
        info = validate_italian_phone(m.group(0))
        if not info:
            continue
        if mobile_only and not info["is_mobile"]:
            continue
        if info["digits"] not in seen:
            seen.add(info["digits"])
            results.append(info)
    return results


def validate_email_address(email: str, check_dns: bool = True) -> Tuple[bool, str]:
    """Verifica sintassi, esclude indirizzi fake/asset/noreply e controlla DNS del dominio."""
    e = (email or "").strip().lower().rstrip(".,;:")
    if not e or "@" not in e:
        return False, "Email vuota o non valida"
    if any(e.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", ".pdf")):
        return False, "Asset file scambiato per email"
    if not re.match(r"^[a-zA-Z0-9._%+\-]+@([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,12})$", e):
        return False, "Formato email non conforme"
    local, domain = e.split("@", 1)
    if local in ("noreply", "no-reply", "donotreply", "mailer-daemon", "info.example", "privacy", "dpo"):
        return False, f"Casella non utile per contatti B2B ({local})"
    if domain in DISPOSABLE_EMAIL_DOMAINS or domain.endswith((".png", ".jpg", ".js", ".css", ".local")):
        return False, f"Dominio email scartato ({domain})"

    if check_dns:
        if domain in _MX_CACHE:
            ok = _MX_CACHE[domain]
            return (True, "Dominio email verificato (cache)") if ok else (False, f"Dominio email irraggiungibile ({domain})")
        ok = False
        try:
            socket.getaddrinfo(domain, 25, type=socket.SOCK_STREAM)
            ok = True
        except Exception:
            try:
                socket.gethostbyname(domain)
                ok = True
            except Exception:
                ok = False
        _MX_CACHE[domain] = ok
        if not ok:
            return False, f"Dominio email inesistente in DNS ({domain})"
    return True, "Email verificata"


def extract_emails_from_text(text: str, check_dns: bool = False) -> List[str]:
    if not text:
        return []
    found: List[str] = []
    seen: set = set()
    for m in _EMAIL_RE.finditer(text):
        cand = m.group(1).lower()
        ok, _ = validate_email_address(cand, check_dns=check_dns)
        if ok and cand not in seen:
            seen.add(cand)
            found.append(cand)
    return found


def classify_lead_coherence(
    title: str,
    text: str,
    url: str = "",
    source: str = "",
    target_mode: str = "TRASLOCHI_PRIVATI",
) -> Dict[str, Any]:
    """
    Classifica la coerenza di un annuncio/record prima dell'ingestione nel DB:
    - CLIENT_DEMAND: privato o richiesta esplicita di trasloco/sgombero
    - REAL_ESTATE_B2B: agenzia immobiliare reale per convenzione sgomberi pre-rogito
    - COMPETITOR_OFFER: ditta concorrente che offre traslochi / SEO blog / listini
    - OFF_TOPIC: autolavaggi, offerte lavoro o annunci fuori contesto
    """
    blob = f"{title or ''} {text or ''} {source or ''}".lower()
    url_low = (url or "").lower()

    # 1. Off-topic (autolavaggi o annunci non traslochi/immobiliari)
    if any(k in blob for k in OFF_TOPIC_KEYWORDS):
        return {"category": "OFF_TOPIC", "coherent": False, "reason": "Fuori target (autolavaggio o altro settore)"}

    # 2. Esclusione blog SEO / directory comparative / offerte competitor
    if any(k in url_low for k in ("/blog/", "/guida-", "quanto-costa", "cronoshare.it/prezzi", "prontopro.it/c/")):
        return {"category": "COMPETITOR_OFFER", "coherent": False, "reason": "Pagina guida prezzi/competitor"}

    is_competitor = any(k in blob for k in COMPETITOR_OFFER_KEYWORDS)
    has_piva = bool(re.search(r"(?i)(?:p\.?\s*iva|partita\s*iva)\s*[:\-]?\s*\d{11}", blob))
    is_real_estate = any(k in blob for k in REAL_ESTATE_KEYWORDS) or ("agenzie-immobiliari" in url_low) or ("immobiliare_b2b" in (source or "").lower())
    is_client = any(k in blob for k in CLIENT_DEMAND_KEYWORDS)

    # Evita falsi positivi: agenzia immobiliare non è competitor di traslochi
    if is_real_estate and not is_competitor:
        cat = "REAL_ESTATE_B2B"
        reason = "Agenzia immobiliare per convenzione sgomberi/traslochi"
    elif is_competitor or (has_piva and not is_client):
        cat = "COMPETITOR_OFFER"
        reason = "Ditta o annuncio che offre traslochi/sgomberi (concorrente)"
    elif is_client:
        cat = "CLIENT_DEMAND"
        reason = "Richiesta reale di cliente privato per trasloco o sgombero"
    else:
        cat = "AMBIGUOUS"
        reason = "Intento non chiaramente riconducibile a richiesta o agenzia immobiliare"

    if target_mode == "TRASLOCHI_PRIVATI":
        coherent = cat == "CLIENT_DEMAND"
    elif target_mode == "IMMOBILIARI_B2B":
        coherent = cat == "REAL_ESTATE_B2B"
    else:  # "TUTTI_COERENTI"
        coherent = cat in ("CLIENT_DEMAND", "REAL_ESTATE_B2B")

    return {"category": cat, "coherent": coherent, "reason": reason}


def audit_and_clean_vault_db(db_path: str = VAULT_DB, dry_run: bool = False) -> Dict[str, Any]:
    """
    Esegue una bonifica deterministica sul database lead:
    - Rimuove numeri fittizi/sequenziali/800/non-AGCOM (es. +39800444222, 3489876543, 3334567890, +3990172753176)
    - Rimuove righe off-topic (autolavaggi) o mock Facebook dalla tabella verified_leads_2026
    - Normalizza i numeri validi in formato E.164 (+39...) e aggiorna link wa.me/39...
    """
    if not os.path.exists(db_path):
        return {"status": "MISSING_DB", "db_path": db_path}

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    report: Dict[str, Any] = {
        "db_path": db_path,
        "dry_run": dry_run,
        "verified_leads_removed": [],
        "verified_leads_normalized": 0,
        "captured_leads_removed": [],
        "captured_leads_normalized": 0,
        "agencies_cleaned_phones": 0,
        "agencies_cleaned_emails": 0,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    # 1. Audit verified_leads_2026
    try:
        rows = c.execute(
            "SELECT id, client_name, phone, service_type, notes, post_url, provenance_channel FROM verified_leads_2026"
        ).fetchall()
        for rid, name, phone, srv, notes, post_url, prov in rows:
            blob = f"{name or ''} {srv or ''} {notes or ''}".lower()
            is_offtopic = any(k in blob for k in OFF_TOPIC_KEYWORDS)
            is_mock_fb = ("10892348912" in (post_url or "")) or ("8912739102" in (post_url or "")) or ("7728190291" in (post_url or ""))

            # Consenti DM_ONLY solo se reale (url non mock e non offtopic)
            ph_res = None if (str(phone or "").strip() == "DM_ONLY") else validate_italian_phone(phone, strict_mobile_10=False)

            bad_reason = None
            if is_offtopic:
                bad_reason = "off_topic_autolavaggio"
            elif is_mock_fb:
                bad_reason = "mock_facebook_seed"
            elif str(phone or "").strip() != "DM_ONLY" and not ph_res:
                bad_reason = f"invalid_phone:{phone}"

            if bad_reason:
                report["verified_leads_removed"].append({"id": rid, "name": name, "phone": phone, "reason": bad_reason})
                if not dry_run:
                    c.execute("DELETE FROM verified_leads_2026 WHERE id = ?", (rid,))
            elif ph_res and phone != ph_res["e164"]:
                if not dry_run:
                    c.execute(
                        "UPDATE verified_leads_2026 SET phone = ? WHERE id = ?",
                        (ph_res["e164"], rid),
                    )
                report["verified_leads_normalized"] += 1
    except Exception as e:
        report["verified_leads_error"] = str(e)

    # 2. Audit captured_moving_leads
    try:
        rows2 = c.execute("SELECT id, channel, title, phone, service_type, details FROM captured_moving_leads").fetchall()
        for rid, ch, title, phone, srv, details in rows2:
            blob = f"{title or ''} {srv or ''} {details or ''}".lower()
            ph_res = validate_italian_phone(phone, strict_mobile_10=False)
            bad_reason = None
            if any(k in blob for k in OFF_TOPIC_KEYWORDS):
                bad_reason = "off_topic"
            elif phone and not ph_res:
                bad_reason = f"invalid_phone:{phone}"
            if bad_reason:
                report["captured_leads_removed"].append({"id": rid, "title": title, "phone": phone, "reason": bad_reason})
                if not dry_run:
                    c.execute("DELETE FROM captured_moving_leads WHERE id = ?", (rid,))
            elif ph_res and phone != ph_res["e164"]:
                if not dry_run:
                    c.execute("UPDATE captured_moving_leads SET phone = ? WHERE id = ?", (ph_res["e164"], rid))
                report["captured_leads_normalized"] += 1
    except Exception as e:
        report["captured_leads_error"] = str(e)

    # 3. Audit b2b_real_estate_agencies (pulisce telefoni non validi o email asset senza eliminare agenzie OSM reali)
    try:
        rows3 = c.execute("SELECT id, phone, email FROM b2b_real_estate_agencies").fetchall()
        for rid, phone, email in rows3:
            if phone and not validate_italian_phone(phone, strict_mobile_10=False):
                report["agencies_cleaned_phones"] += 1
                if not dry_run:
                    c.execute("UPDATE b2b_real_estate_agencies SET phone = '' WHERE id = ?", (rid,))
            if email:
                ok_em, _ = validate_email_address(email, check_dns=False)
                if not ok_em:
                    report["agencies_cleaned_emails"] += 1
                    if not dry_run:
                        c.execute("UPDATE b2b_real_estate_agencies SET email = '' WHERE id = ?", (rid,))
    except Exception as e:
        report["agencies_error"] = str(e)

    if not dry_run:
        conn.commit()
    try:
        report["remaining_verified_leads"] = c.execute("SELECT COUNT(*) FROM verified_leads_2026").fetchone()[0]
        report["remaining_captured_leads"] = c.execute("SELECT COUNT(*) FROM captured_moving_leads").fetchone()[0]
        report["remaining_agencies"] = c.execute("SELECT COUNT(*) FROM b2b_real_estate_agencies").fetchone()[0]
    except Exception:
        pass
    conn.close()
    return report
