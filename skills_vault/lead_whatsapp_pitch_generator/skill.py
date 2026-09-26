import re
import urllib.parse

def generate_pitch(client_name, service, city, mq=70, budget=None):
    client_name = (client_name or "Gentile Cliente").title()
    service = (service or "trasloco").lower()
    city = (city or "Bologna").title()
    
    if "sgombero" in service:
        text = (
            f"Buongiorno {client_name}, la contatto da PietroTraslochi.com in merito alla richiesta di sgombero per {city}. "
            f"Abbiamo disponibilità immediata con furgone e 2 operatori specializzati, smaltimento ecologico autorizzato incluso. "
            f"Desidera un preventivo fisso senza impegno con sopralluogo o foto su WhatsApp?"
        )
    elif "autolavaggio" in service or "chimica" in service:
        text = (
            f"Buongiorno {client_name}, la contatto da SELEZIONE — Distribuzione Prodotti Professionali (in collab. con BadrExpress.com). "
            f"Forniamo detergenti industriali ad altissima resa per piste e rulli a {city}, con consegna diretta e prova gratuita sul primo fusto. "
            f"Possiamo passarci questo venerdì per una breve dimostrazione?"
        )
    else: # Trasloco standard
        estimate = budget if budget else (mq * 8.5 if mq > 50 else 350.0)
        text = (
            f"Buongiorno {client_name}, la contatto dal centralino PietroTraslochi.com per il Suo trasloco a {city} (~{mq} mq). "
            f"La nostra stima indicativa parte da circa {int(estimate)} euro tutto compreso (assicurazione merci inclusa). "
            f"Possiamo sentirci per 2 minuti oggi o preferisce concordare l'orario via messaggio?"
        )
    return text

def execute(params=None):
    params = params or {}
    name = params.get("name", "Cliente")
    phone = params.get("phone", "")
    service = params.get("service", "trasloco")
    city = params.get("city", "Cuneo")
    mq = int(params.get("mq", 70))
    budget = params.get("budget")

    pitch_text = generate_pitch(name, service, city, mq, budget)
    
    clean_phone = re.sub(r'[^0-9]', '', str(phone))
    if clean_phone.startswith("39"):
        clean_phone = clean_phone[2:]
        
    wa_url = None
    if clean_phone:
        encoded_text = urllib.parse.quote(pitch_text)
        wa_url = f"https://wa.me/39{clean_phone}?text={encoded_text}"

    return {
        "status": "SUCCESS",
        "skill": "lead_whatsapp_pitch_generator",
        "client_name": name,
        "phone": f"+39 {clean_phone}" if clean_phone else None,
        "service": service,
        "city": city,
        "pitch_text": pitch_text,
        "whatsapp_url": wa_url,
        "message": f"Pitch generato con successo per {name} ({service} a {city})."
    }
