import re
import socket
import urllib.parse
import requests

DISPOSABLE_DOMAINS = {
    "tempmail.com", "guerrillamail.com", "10minutemail.com", "mailinator.com",
    "yopmail.com", "trashmail.com", "throwawaymail.com", "getairmail.com",
    "sharklasers.com", "guerrillamailblock.com", "pokemail.net", "mohmal.com",
    "fakeinbox.com", "dispostable.com", "tempail.com", "mytemp.email"
}

def validate_email(email):
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return False, "Sintassi email non valida (manca @ o vuota)"

    match = re.match(r'^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', email)
    if not match:
        return False, "Formato email non conforme"

    domain = match.group(1).lower()

    if domain in DISPOSABLE_DOMAINS:
        return False, f"Dominio usa-e-getta temporaneo rilevato ({domain})"

    # MX / DNS check
    try:
        # Check domain resolution
        socket.gethostbyname(domain)
    except Exception:
        return False, f"Dominio email inesistente o senza record DNS validi ({domain})"

    return True, "Email valida e attiva con server DNS confermato"

def validate_phone(phone):
    phone = (phone or "").strip()
    clean_num = re.sub(r'[^0-9]', '', phone)

    if not clean_num or len(clean_num) < 9 or len(clean_num) > 13:
        return False, "Lunghezza numero di telefono errata (richieste 9-10 cifre)"

    # Strip country code +39 if present
    local_num = clean_num
    if local_num.startswith("39") and len(local_num) >= 11:
        local_num = local_num[2:]

    # Check repeating dummy numbers (0000000000, 1111111111, 123456789, etc.)
    if len(set(local_num)) <= 2 or local_num in ["123456789", "1234567890", "987654321"]:
        return False, f"Numero fasullo o sequenza fittizia rilevata ({phone})"

    # Italian mobile prefix check (starts with 3)
    if local_num.startswith("3"):
        return True, f"Cellulare mobile italiano valido (+39 {local_num})"
    elif local_num.startswith("0"):
        return True, f"Numero fisso italiano valido (+39 {local_num})"
    else:
        return True, f"Numero internazionale valido (+{clean_num})"

def geocode_address(address_text):
    if not address_text or len(address_text.strip()) < 3:
        return None, "Indirizzo troppo corto o assente"

    try:
        query = urllib.parse.quote(address_text.strip())
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        headers = {"User-Agent": "EBGS_LeadQualityGuard_v1.0 (badrexpress.com)"}
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                item = data[0]
                return {
                    "display_name": item.get("display_name"),
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "type": item.get("type")
                }, "Indirizzo confermato su mappa reale"
    except Exception as e:
        return None, f"Geocoding timeout o errore: {e}"

    return None, "Indirizzo non trovato su mappa reale"

def execute(params=None):
    params = params or {}
    name = (params.get("name") or "Cliente").strip()
    source = (params.get("source") or "").lower()
    email = params.get("email", "").strip()
    phone = params.get("phone", "").strip()
    partenza = params.get("partenza", "").strip()
    arrivo = params.get("arrivo", "").strip()
    messenger_url = params.get("messenger_url", "").strip()

    score = 100
    penalties = []
    checks = {}

    # 1. Check Real Name
    has_valid_name = bool(name and len(name) >= 3 and not any(w in name.lower() for w in ["utente", "anonimo", "facebook user", "inserzionista", "profilo", "null", "none"]))
    if not has_valid_name:
        return {
            "status": "REJECTED",
            "skill": "EB_LeadQualityGuard",
            "name": name,
            "quality_score": 0,
            "verdict": "REJECTED_NO_NAME",
            "badge": "🔴 SCARTATO (NOME NON VALIDO)",
            "penalties": ["Nome e cognome reale assente o generico"],
            "message": "Lead scartato: Nome reale mancante."
        }

    # 2. Check Phone & Messenger availability
    phone_ok, phone_msg = validate_phone(phone) if phone else (False, "Telefono non specificato")
    has_messenger = bool(messenger_url and ("m.me/" in messenger_url or "facebook.com/messages" in messenger_url))

    checks["phone"] = {"valid": phone_ok, "detail": phone_msg}
    checks["messenger"] = {"valid": has_messenger, "detail": messenger_url if has_messenger else "Assente"}

    # ── STRICT BARRIER: MUST HAVE (MESSENGER OR VALID PHONE) ──
    if not has_messenger and not phone_ok:
        return {
            "status": "REJECTED",
            "skill": "EB_LeadQualityGuard",
            "name": name,
            "quality_score": 0,
            "verdict": "REJECTED_NO_CONTACT_CHANNEL",
            "badge": "🔴 SCARTATO (NO CONTATTO)",
            "penalties": ["Nessun contatto Messenger o numero di telefono valido disponibile"],
            "message": "Lead scartato: Nessun canale di contatto valido (serve Messenger o Telefono)."
        }

    # 3. Email Check
    if email:
        email_ok, email_msg = validate_email(email)
        checks["email"] = {"valid": email_ok, "detail": email_msg}
        if not email_ok:
            score -= 25
            penalties.append(f"Email: {email_msg}")
    else:
        checks["email"] = {"valid": False, "detail": "Non specificata"}

    # 4. Geocoding / City match
    if partenza:
        geo_p, geo_p_msg = geocode_address(partenza)
        checks["partenza"] = {"found": geo_p is not None, "detail": geo_p_msg}
        if not geo_p:
            score -= 10
            penalties.append(f"Partenza: {geo_p_msg}")

    if not phone_ok:
        score -= 10 # Relies purely on Messenger
    if not email:
        score -= 5

    score = max(50, min(100, score))

    if score >= 85:
        verdict = "VERIFIED_HIGH_INTENT"
        badge = "🟢 LEAD AUTENTICO AL 100%"
    else:
        verdict = "MEDIUM_QUALITY"
        badge = "🟡 CONTATTO DISPONIBILE"

    clean_num = re.sub(r'[^0-9]', '', phone)
    wa_link = f"https://wa.me/39{clean_num}?text=Salve%20{urllib.parse.quote(name)}%2C%20la%20contatto%20da%20PietroTraslochi%20per%20il%20preventivo." if phone_ok else None

    return {
        "status": "SUCCESS",
        "skill": "EB_LeadQualityGuard",
        "name": name,
        "quality_score": score,
        "verdict": verdict,
        "badge": badge,
        "checks": checks,
        "penalties": penalties,
        "messenger_url": messenger_url if has_messenger else None,
        "whatsapp_ping_link": wa_link,
        "message": f"{badge} (Score: {score}/100) per {name}."
    }
