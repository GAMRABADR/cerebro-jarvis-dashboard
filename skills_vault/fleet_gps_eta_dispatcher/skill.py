import os, re, urllib.parse, datetime

def calculate_eta(city="Bologna", client_name="Gentile Cliente", phone="+393888703508"):
    clean_phone = re.sub(r'[^0-9]', '', phone)
    if clean_phone.startswith("3") and len(clean_phone) == 10: clean_phone = "39" + clean_phone
    
    eta_mins = 18
    msg = (
        f"Gentile {client_name}, la squadra operativa di Pietro Traslochi è partita per il suo indirizzo a {city}.\n\n"
        f"🚚 Tempo di arrivo stimato: circa {eta_mins} minuti.\n"
        f"Furgone attrezzato con piattaforma elevatrice e operatori in avvicinamento.\n\n"
        f"Per qualsiasi necessità diretta: Tel +39 388 870 3508 (Ingegner Badr)."
    )
    wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"
    return {
        "status": "SUCCESS",
        "client": client_name,
        "city": city,
        "eta_minutes": eta_mins,
        "whatsapp_url": wa_url,
        "message": msg
    }

def execute(params=None):
    params = params or {}
    return calculate_eta(params.get("city", "Bologna"), params.get("client_name", "Cliente"), params.get("phone", "3888703508"))
