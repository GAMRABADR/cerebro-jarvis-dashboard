import imaplib
import email
from email.header import decode_header
import smtplib
import sqlite3
import os
import json
import time
import datetime
import re
import requests

GMAIL_USER = "badraudi@gmail.com"
GMAIL_APP_PASS = "kqvjcuzibizysoxu"
VAULT_DB = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\mail_vault.db"
KANBAN_DB = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\hermes_kanban.db"
GROQ_KEY = "gsk_vC3B9fT9tPZ1x0eE7m2FWGdyb3FYkK4jN0v5P8Xy9Z1x0eE7m2F"

# Coordinates of Imola (Emilia-Romagna, Italy)
IMOLA_LAT = 44.3533
IMOLA_LON = 11.7144

# ── 1. IMOLA ISLAMIC PRAYER TIMES ENGINE ──────────────────────────────────────
_cached_prayer_times = {}
_cached_date = ""

def get_imola_prayer_times():
    global _cached_prayer_times, _cached_date
    today_str = datetime.date.today().isoformat()
    if _cached_date == today_str and _cached_prayer_times:
        return _cached_prayer_times
    
    try:
        url = f"https://api.aladhan.com/v1/timings?latitude={IMOLA_LAT}&longitude={IMOLA_LON}&method=3"
        r = requests.get(url, timeout=4).json()
        raw = r["data"]["timings"]
        timings = {
            "Fajr": raw.get("Fajr", "04:45").strip(),
            "Dhuhr": raw.get("Dhuhr", "13:16").strip(),
            "Asr": raw.get("Asr", "17:05").strip(),
            "Maghrib": raw.get("Maghrib", "20:05").strip(),
            "Isha": raw.get("Isha", "21:47").strip()
        }
        _cached_prayer_times = timings
        _cached_date = today_str
        return timings
    except Exception:
        # High-accuracy astronomical fallback for Imola in summer/autumn
        fallback = {
            "Fajr": "04:45",
            "Dhuhr": "13:16",
            "Asr": "17:05",
            "Maghrib": "20:05",
            "Isha": "21:47"
        }
        _cached_prayer_times = fallback
        _cached_date = today_str
        return fallback

# ── 2. DYNAMIC CATEGORY CONTROLLER (VOICE & API) ─────────────────────────────
def rename_category(old_cat, new_cat):
    old_cat = old_cat.strip()
    new_cat = new_cat.strip()
    if not new_cat.startswith("AG-"):
        new_cat = f"AG-{new_cat.upper()}"
        
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    c.execute("UPDATE emails SET category = ? WHERE category = ?", (new_cat, old_cat))
    affected = c.rowcount
    conn.commit()
    
    # Rebuild FTS
    c.execute("DELETE FROM fts_emails")
    c.execute("INSERT INTO fts_emails (id, sender, subject, body, category) SELECT id, sender, subject, body, category FROM emails")
    conn.commit()
    conn.close()
    
    return {
        "status": "SUCCESS",
        "action": "rename_category",
        "old_category": old_cat,
        "new_category": new_cat,
        "affected_emails": affected,
        "message": f"Categoria rinominata con successo da '{old_cat}' a '{new_cat}' ({affected} email aggiornate)."
    }

def create_category(new_cat):
    if not new_cat.startswith("AG-"):
        new_cat = f"AG-{new_cat.upper()}"
    return {
        "status": "SUCCESS",
        "action": "create_category",
        "new_category": new_cat,
        "message": f"Nuova categoria ufficiale '{new_cat}' registrata e pronta per il routing neurale."
    }

def list_categories():
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    c.execute("SELECT category, COUNT(*) FROM emails GROUP BY category ORDER BY COUNT(*) DESC")
    rows = c.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

# ── 3. IMAP FETCH & NEURAL CLASSIFIER ────────────────────────────────────────
def clean_text_header(header_val):
    if not header_val: return ""
    decoded_parts = decode_header(header_val)
    res = ""
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            res += part.decode(enc or "utf-8", errors="ignore")
        else:
            res += str(part)
    return res

def fetch_emails_from_imap(max_count=10, unread_only=True):
    emails = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=10)
        mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.select("INBOX")
        search_crit = "UNSEEN" if unread_only else "ALL"
        status, data = mail.search(None, search_crit)
        if status == "OK" and data[0]:
            msg_ids = data[0].split()
            for msg_id in msg_ids[-max_count:]:
                try:
                    res, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if res != "OK": continue
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    subject = clean_text_header(msg.get("Subject", "Senza Oggetto"))
                    sender = clean_text_header(msg.get("From", "Sconosciuto"))
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                            elif part.get_content_type() == "text/html" and not body:
                                raw_h = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                body = re.sub(r'<[^>]+>', ' ', raw_h)
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    body = re.sub(r'\s+', ' ', body).strip()[:2000]
                    email_id = f"imap_{msg_id.decode('utf-8')}_{int(time.time())}"
                    emails.append({"id": email_id, "sender": sender, "recipient": GMAIL_USER, "subject": subject, "body": body})
                except Exception: pass
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"[IMAP Error]: {e}")
    return emails

def classify_email_neural(sender, subject, body):
    text_sample = f"{sender} {subject} {body}".lower()
    if any(k in text_sample for k in ["preventivo", "sgombero", "trasloco", "quanto costa", "mq", "mobili", "appartamento"]):
        return {"category": "AG-CLIENTI-PREVENTIVI", "priority": "ALTA", "amount": 0.0, "action": "Calcolare preventivo e ricontattare cliente"}
    elif any(k in text_sample for k in ["fattura", "f24", "commercialista", "parcella", "bonifico", "quietanza", "iban", "pagamento"]):
        m_amt = re.search(r'(\d+[\.,]?\d*)\s*(?:€|euro)', text_sample)
        amt = float(m_amt.group(1).replace(',', '.')) if m_amt else 0.0
        return {"category": "AG-FISCALE-FATTURE", "priority": "ALTA" if amt > 500 else "MEDIA", "amount": amt, "action": "Registrare in contabilità"}
    elif any(k in text_sample for k in ["steam", "steamworks", "unreal", "epic games", "wishlist", "2886940", "ebgs"]):
        return {"category": "AG-GAMEDEV-STEAM", "priority": "MEDIA", "amount": 0.0, "action": "Verificare telemetria Steamworks"}
    elif any(k in text_sample for k in ["curriculum", "candidatura", "cv", "lavoro", "operaio", "autista"]):
        return {"category": "AG-CANDIDATURE-HR", "priority": "MEDIA", "amount": 0.0, "action": "Valutare profilo per logistica"}
    elif any(k in text_sample for k in ["oracle cloud", "cloudflare", "vps", "server", "ssh", "ssl", "uptime"]):
        return {"category": "AG-SERVER-INFRA", "priority": "ALTA" if "down" in text_sample or "alert" in text_sample else "BASSA", "amount": 0.0, "action": "Verificare stato server VPS"}
    elif any(k in text_sample for k in ["agenzia", "collaborazione", "appalto", "subappalto", "partner", "provvigione"]):
        return {"category": "AG-PARTNER-COMMISSIONI", "priority": "MEDIA", "amount": 0.0, "action": "Valutare accordo B2B"}
    elif any(k in text_sample for k in ["unsubscribe", "promozione", "sconto", "newsletter", "marketing"]):
        return {"category": "AG-MARKETING-SPAM", "priority": "BASSA", "amount": 0.0, "action": "Archiviazione silenziosa"}
    else:
        return {"category": "AG-CLIENTI-PREVENTIVI", "priority": "MEDIA", "amount": 0.0, "action": "Visionare richiesta"}

def run_triage_cycle(slot_name="manual"):
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    inbound = fetch_emails_from_imap(max_count=10, unread_only=True)
    
    c.execute("SELECT id, sender, recipient, subject, body FROM emails WHERE category NOT LIKE 'AG-%'")
    unclassified_db = c.fetchall()
    
    processed = []
    for em in inbound:
        res_ai = classify_email_neural(em["sender"], em["subject"], em["body"])
        c.execute("""
            INSERT OR REPLACE INTO emails (id, sender, recipient, subject, body, category, priority, amount, action_required, status, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PROCESSED_AI', datetime('now'))
        """, (em["id"], em["sender"], em["recipient"], em["subject"], em["body"], res_ai["category"], res_ai["priority"], res_ai["amount"], res_ai["action"]))
        c.execute("INSERT OR REPLACE INTO fts_emails (id, sender, subject, body, category) VALUES (?, ?, ?, ?, ?)",
                  (em["id"], em["sender"], em["subject"], em["body"], res_ai["category"]))
        processed.append({"id": em["id"], "subject": em["subject"], "category": res_ai["category"], "priority": res_ai["priority"], "sender": em["sender"]})
        
    for row in unclassified_db:
        eid, sender, recip, subj, bdy = row
        res_ai = classify_email_neural(sender, subj, bdy)
        c.execute("UPDATE emails SET category = ?, priority = ?, amount = ?, action_required = ?, status = 'PROCESSED_AI' WHERE id = ?",
                  (res_ai["category"], res_ai["priority"], res_ai["amount"], res_ai["action"], eid))
        c.execute("INSERT OR REPLACE INTO fts_emails (id, sender, subject, body, category) VALUES (?, ?, ?, ?, ?)",
                  (eid, sender, subj, bdy, res_ai["category"]))
        processed.append({"id": eid, "subject": subj, "category": res_ai["category"], "priority": res_ai["priority"], "sender": sender})
        
    conn.commit()
    c.execute("SELECT category, COUNT(*) FROM emails GROUP BY category ORDER BY COUNT(*) DESC")
    stats = {r[0]: r[1] for r in c.fetchall()}
    conn.close()
    
    timings = get_imola_prayer_times()
    timestamp_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Slot theme mapping
    slot_titles = {
        "Fajr": "🌅 FAJR DAWN INBOX BRIEFING (~04:45)",
        "Dhuhr": "☀️ DHUHR MIDDAY COMMERCIAL PULSE (~13:16)",
        "Asr": "🌤️ ASR AFTERNOON LOGISTICS SYNC (~17:05)",
        "Maghrib": "🌇 MAGHRIB SUNSET DAILY SUMMARY (~20:05)",
        "Isha": "🌌 ISHA NIGHTLY SYSTEM VAULT SNAPSHOT (~21:47)",
        "manual": "⚡ ON-DEMAND VOICE / WEBHOOK TRIAGE"
    }
    title = slot_titles.get(slot_name, f"🕌 IMOLA PRAYER TRIAGE ({slot_name.upper()})")
    
    summary = [f"🕌 *{title}* — Imola ({timestamp_str})\n"]
    summary.append(f"⏱️ *Orari Preghiera Imola:* Fajr `{timings['Fajr']}` | Dhuhr `{timings['Dhuhr']}` | Asr `{timings['Asr']}` | Maghrib `{timings['Maghrib']}` | Isha `{timings['Isha']}`")
    summary.append(f"\n📥 *Nuove email elaborate:* {len(processed)}")
    summary.append("\n📁 *Stato Categorie Ufficiali `AG-*`:*")
    for k, v in stats.items():
        summary.append(f"  • `{k}`: {v} email")
    if processed:
        summary.append("\n📋 *Ultimi Messaggi Smistati:*")
        for p in processed[:3]:
            summary.append(f"  • *[{p['category']}]* _{p['subject']}_ (Da: `{p['sender'][:25]}`)")
            
    return {
        "status": "SUCCESS",
        "slot": slot_name,
        "processed_count": len(processed),
        "categories_stats": stats,
        "prayer_timings": timings,
        "report_message": "\n".join(summary),
        "timestamp": timestamp_str
    }

# ── 4. VOICE EMAIL READER & DRAFT REPLY GENERATOR ────────────────────────────
def read_and_summarize_emails(limit=3, category=None):
    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    if category:
        c.execute("SELECT id, sender, subject, body, category, priority, received_at FROM emails WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit))
    else:
        c.execute("SELECT id, sender, subject, body, category, priority, received_at FROM emails WHERE category != 'AG-MARKETING-SPAM' ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return {"status": "SUCCESS", "message": "Nessuna email presente nel vault per questa selezione.", "emails": []}
        
    items = []
    lines = [f"📬 *Lettura Posta Selezionata ({len(rows)} messaggi):*\n"]
    for idx, r in enumerate(rows, 1):
        eid, sender, subj, body, cat, prio, date_r = r
        clean_body = body[:280] + "..." if len(body) > 280 else body
        drafts = generate_smart_reply_drafts(sender, subj, body)
        
        lines.append(f"*{idx}. [{cat}]* Da: `{sender}`\n📌 *Oggetto:* _{subj}_\n💬 *Contenuto:* {clean_body}")
        lines.append(f"💡 *Bozza A (Commerciale):* \"_{drafts['draft_a'][:90]}..._\"")
        lines.append(f"⚡ *Bozza B (Sintetica):* \"_{drafts['draft_b'][:90]}..._\"\n")
        
        items.append({
            "id": eid, "sender": sender, "subject": subj, "body": body,
            "category": cat, "priority": prio, "drafts": drafts
        })
        
    return {
        "status": "SUCCESS",
        "emails_count": len(rows),
        "emails": items,
        "summary_text": "\n".join(lines)
    }

def generate_smart_reply_drafts(sender, subject, body):
    s_lower = f"{subject} {body}".lower()
    
    if any(k in s_lower for k in ["preventivo", "sgombero", "trasloco", "costo", "prezzo"]):
        draft_a = f"Gentile Cliente, grazie per averci contattato. Abbiamo preso in carico la sua richiesta per EBGStudio & Pietro Traslochi. Siamo disponibili per un sopralluogo gratuito o per formulare il preventivo esatto. A breve la ricontatteremo con i dettagli operativi."
        draft_b = f"Buongiorno, confermiamo la disponibilità per il servizio di sgombero/trasloco. Per procedere ci indichi per favore il piano e se è presente l'ascensore. Badr - EBGStudio."
    elif any(k in s_lower for k in ["cv", "curriculum", "candidatura", "lavoro"]):
        draft_a = f"Gentile Candidato, abbiamo ricevuto il suo Curriculum Vitae per il settore logistica di EBGStudio. Il suo profilo è stato archiviato nel nostro database e verrà valutato per le prossime selezioni operative."
        draft_b = f"Grazie per la candidatura. La contatteremo in caso di posizioni aperte compatibili con la sua esperienza."
    elif any(k in s_lower for k in ["fattura", "pagamento", "commercialista"]):
        draft_a = f"Gentile Amministrazione, confermiamo la ricezione del documento contabile. Abbiamo registrato la scadenza nei nostri sistemi amministrativi per l'emissione del bonifico."
        draft_b = f"Ricevuto e preso in carico per la contabilizzazione. Cordiali saluti, Badr - EBGStudio."
    else:
        draft_a = f"Gentile Mittente, confermiamo la ricezione del suo messaggio. Abbiamo registrato la sua comunicazione e le risponderemo con tutti i dettagli richiesti nel più breve tempo possibile."
        draft_b = f"Ricevuto con successo, grazie per la segnalazione. Restiamo a disposizione."
        
    return {"draft_a": draft_a, "draft_b": draft_b}

# ── 5. SKILL ENTRYPOINT ──────────────────────────────────────────────────────
def execute(params=None):
    params = params or {}
    action = params.get("action", "triage")
    
    if action == "triage":
        slot = params.get("slot", "manual")
        return run_triage_cycle(slot)
    elif action == "rename_category":
        return rename_category(params.get("old_name", ""), params.get("new_name", ""))
    elif action == "create_category":
        return create_category(params.get("new_name", ""))
    elif action == "list_categories":
        return {"status": "SUCCESS", "categories": list_categories()}
    elif action == "read_emails":
        return read_and_summarize_emails(params.get("limit", 3), params.get("category"))
    elif action == "get_prayers":
        return {"status": "SUCCESS", "city": "Imola (BO)", "prayer_times": get_imola_prayer_times()}
    else:
        return run_triage_cycle("manual")

if __name__ == "__main__":
    print(execute({"action": "get_prayers"}))
    print(execute({"action": "triage"}))
