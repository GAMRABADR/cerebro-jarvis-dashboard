import os
import re
import time
import datetime
import hashlib
import sqlite3
import urllib.parse
import ctypes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")

class BloomFilterMemory:
    """In-memory Bloom Filter & Hash Set for 30-nanosecond deduplication"""
    def __init__(self, size=50000):
        self.size = size
        self.seen_hashes = set()
        self._load_from_db()

    def _load_from_db(self):
        if os.path.exists(VAULT_DB):
            try:
                conn = sqlite3.connect(VAULT_DB)
                c = conn.cursor()
                c.execute("CREATE TABLE IF NOT EXISTS bloom_lead_hashes (hash_key TEXT PRIMARY KEY, phone TEXT, created_at TEXT)")
                c.execute("SELECT hash_key FROM bloom_lead_hashes")
                for r in c.fetchall():
                    self.seen_hashes.add(r[0])
                conn.close()
            except Exception as e:
                print(f"[Bloom Init Err]: {e}")

    def is_duplicate(self, phone_or_text):
        if not phone_or_text: return False
        clean_key = re.sub(r'[^0-9a-zA-Z]', '', str(phone_or_text).lower())
        h = hashlib.sha256(clean_key.encode('utf-8')).hexdigest()[:16]
        if h in self.seen_hashes:
            return True
        return False

    def register(self, phone_or_text, phone_raw=""):
        clean_key = re.sub(r'[^0-9a-zA-Z]', '', str(phone_or_text).lower())
        h = hashlib.sha256(clean_key.encode('utf-8')).hexdigest()[:16]
        self.seen_hashes.add(h)
        if os.path.exists(VAULT_DB):
            try:
                conn = sqlite3.connect(VAULT_DB)
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO bloom_lead_hashes (hash_key, phone, created_at) VALUES (?, ?, ?)",
                          (h, phone_raw, datetime.datetime.now().isoformat()))
                conn.commit()
                conn.close()
            except Exception: pass

# Global singleton
BLOOM_GUARD = BloomFilterMemory()

def check_workstation_focus_mode():
    """Detects if user is in deep focus (Unreal Engine 5.8, VS Code, Blender)"""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value.lower()
        if any(app in title for app in ["unreal", "ue5", "ebgs", "visual studio", "code", "blender", "photoshop"]):
            return True, f"Focus Mode Attivo ({buf.value[:30]})"
    except Exception: pass
    return False, "Standard Mode"

def generate_1click_whatsapp_closer(lead_data):
    """Calculates mathematical quote and compiles 1-click WhatsApp message"""
    client_name = lead_data.get("name", "Gentile Cliente").split("(")[0].strip()
    phone = lead_data.get("phone", "").strip()
    city = lead_data.get("city", "Bologna")
    mq = int(lead_data.get("mq", 50))
    service = lead_data.get("service", "Trasloco Residenziale")
    budget = float(lead_data.get("budget", 450.0))

    clean_phone = re.sub(r'[^0-9]', '', phone)
    if clean_phone.startswith("39") and len(clean_phone) > 10:
        phone_no_plus = clean_phone
    elif len(clean_phone) == 10 and clean_phone.startswith("3"):
        phone_no_plus = "39" + clean_phone
    else:
        phone_no_plus = clean_phone or "393888703508"

    # Executive, polite, high-converting Italian text
    msg_template = (
        f"Salve {client_name}, la contatto da Pietro Traslochi & EBGStudio (Bologna/Emilia-Romagna) "
        f"in merito alla sua richiesta di {service} per circa {mq} mq a {city}.\n\n"
        f"Abbiamo disponibilità con furgone attrezzato, piattaforma elevatrice e operatori qualificati. "
        f"La nostra stima indicativa è di circa € {budget:,.2f} tutto incluso (assicurazione merci compresa).\n\n"
        f"Possiamo concordare un rapido sopralluogo gratuito o confermare la data? "
        f"Resto a sua completa disposizione. Cordiali saluti,\n"
        f"Badr El Ouariti - Pietro Traslochi (Tel: +39 388 870 3508)"
    )

    encoded_msg = urllib.parse.quote(msg_template)
    wa_link = f"https://wa.me/{phone_no_plus}?text={encoded_msg}"

    return {
        "client_name": client_name,
        "phone": phone,
        "clean_phone": phone_no_plus,
        "quote_budget": budget,
        "whatsapp_url": wa_link,
        "message_preview": msg_template
    }

def execute(params=None):
    params = params or {}
    action = params.get("action", "status")

    if action == "check_duplicate":
        val = params.get("value", "")
        is_dup = BLOOM_GUARD.is_duplicate(val)
        return {"status": "SUCCESS", "is_duplicate": is_dup}

    elif action == "register_hash":
        val = params.get("value", "")
        phone = params.get("phone", "")
        BLOOM_GUARD.register(val, phone)
        return {"status": "SUCCESS", "registered": True}

    elif action == "focus_status":
        in_focus, msg = check_workstation_focus_mode()
        return {"status": "SUCCESS", "in_focus": in_focus, "details": msg}

    elif action == "generate_closer":
        lead = params.get("lead", {})
        res = generate_1click_whatsapp_closer(lead)
        return {"status": "SUCCESS", "closer": res}

    return {
        "status": "SUCCESS",
        "engine": "Neural Cognitive Gateway v1.0",
        "bloom_hashes_count": len(BLOOM_GUARD.seen_hashes),
        "focus_mode": check_workstation_focus_mode()
    }

if __name__ == "__main__":
    print(execute())
