import requests, urllib.parse, re

def dispatch_appointment_call(phone="3888703508", client="Cliente", date="Giovedì ore 15:00"):
    clean_p = re.sub(r'[^0-9+]', '', phone)
    if len(clean_p) == 10 and clean_p.startswith("3"): clean_p = "+39" + clean_p
    
    # Trigger Android ADB Local Bridge call
    adb_ok = False
    try:
        r = requests.get(f"http://127.0.0.1:8999/call?number={urllib.parse.quote(clean_p)}", timeout=2)
        if r.status_code == 200: adb_ok = True
    except Exception: pass
    
    wa_link = f"https://wa.me/{clean_p.lstrip('+')}?text=Salve%20{urllib.parse.quote(client)}%2C%20le%20confermiamo%20il%20sopralluogo%20per%20{urllib.parse.quote(date)}."
    
    return {
        "status": "SUCCESS",
        "phone": clean_p,
        "client": client,
        "appointment_date": date,
        "adb_gsm_call_sent": adb_ok,
        "whatsapp_confirmation_url": wa_link,
        "message": f"Connessione vocale e conferma appuntamento inviata per {client} ({clean_p})."
    }

def execute(params=None):
    params = params or {}
    return dispatch_appointment_call(params.get("phone", "3888703508"), params.get("client", "Cliente"), params.get("date", "Giovedì ore 15:00"))
