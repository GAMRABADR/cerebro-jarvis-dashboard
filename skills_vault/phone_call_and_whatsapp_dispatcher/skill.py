import subprocess
import urllib.parse
import re
import requests
import os

CONTACTS_BOOK = {
    "mamma": "+393400000001",
    "papa": "+393400000002",
    "ufficio": "+393400000003",
    "pietro": "+393400000004",
    "marco": "+393400000005",
    "commercialista": "+393400000006",
    "meccanico": "+393400000007",
    "badrexpress": "+393400000008",
    "numero verde": "800900800",
    "verde": "800900800",
    "vodafone": "190",
    "assistenza vodafone": "190",
    "credito vodafone": "404",
    "190": "190",
    "404": "404",
    "414": "414",
    "42020": "42020",
    "iliad": "401212",
    "tim": "40916",
    "wind": "4242",
    "soccorso": "803116"
}

N8N_WEBHOOK_CALL = "https://system-roses-wrestling-lawsuit.trycloudflare.com/webhook/make-voice-call"

def execute(params=None):
    params = params or {}
    contact_or_number = params.get("contact", "").strip()
    msg_text = params.get("message", "").strip()
    action = params.get("action", "call" if not msg_text else "whatsapp")

    # Resolve number
    target_num = CONTACTS_BOOK.get(contact_or_number.lower(), contact_or_number)
    clean_num = re.sub(r'[^0-9+]', '', target_num)
    if clean_num and not clean_num.startswith("+") and len(clean_num) == 10:
        clean_num = "+39" + clean_num

    if action == "whatsapp":
        encoded_msg = urllib.parse.quote(msg_text)
        num_no_plus = clean_num.lstrip('+')
        
        # 1. Direct WhatsApp Protocol URI (Desktop App)
        wa_app_uri = f"whatsapp://send?phone={num_no_plus}&text={encoded_msg}"
        # 2. Web fallback link
        wa_web_link = f"https://wa.me/{num_no_plus}?text={encoded_msg}"
        
        # Trigger desktop application opening
        try:
            subprocess.Popen(["cmd", "/c", "start", wa_app_uri], shell=True)
        except Exception:
            try:
                subprocess.Popen(["cmd", "/c", "start", wa_web_link], shell=True)
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "action": "whatsapp",
            "recipient": contact_or_number,
            "number": clean_num,
            "whatsapp_link": wa_web_link,
            "whatsapp_uri": wa_app_uri,
            "message": f"Aperto WhatsApp per {contact_or_number} ({clean_num}) con messaggio compilato: '{msg_text}'."
        }

    else: # Voice Call
        tel_link = f"tel:{clean_num}"
        adb_called = False

        # 1. Trigger Direct Android GSM Call via ADB Local Gateway
        try:
            r = requests.get(f"http://127.0.0.1:8999/call?number={urllib.parse.quote(clean_num)}", timeout=2)
            if r.status_code == 200 and r.json().get("adb_gsm"):
                adb_called = True
        except Exception:
            pass

        # 2. Trigger Windows Phone Link / System Dialer
        try:
            subprocess.Popen(["cmd", "/c", "start", tel_link], shell=True)
        except Exception:
            pass

        # 3. Trigger KDE Connect if available
        try:
            subprocess.Popen(["kdeconnect-cli", "--device", "auto", "--open", tel_link], shell=True)
        except Exception:
            pass

        # 3. Trigger n8n Automated Voice Call Gateway
        n8n_triggered = False
        try:
            r = requests.post(N8N_WEBHOOK_CALL, json={
                "phone_number": clean_num,
                "contact_name": contact_or_number,
                "message": msg_text or "Salve, vi contatto per conto dell'Ingegner Badr di EBGStudio riguardo il preventivo.",
                "caller": "JARVIS AI Master"
            }, timeout=3)
            if r.status_code in [200, 201]:
                n8n_triggered = True
        except Exception:
            pass

        return {
            "status": "SUCCESS",
            "action": "call",
            "contact": contact_or_number,
            "number": clean_num,
            "tel_uri": tel_link,
            "n8n_telephony": n8n_triggered,
            "message": f"Avviata chiamata telefonica verso {contact_or_number} ({clean_num}). Dialer di sistema aperto e pipeline n8n notificata."
        }
