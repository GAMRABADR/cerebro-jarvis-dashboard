#!/usr/bin/env python3
"""
==============================================================================
🎙️ EBJ SUPREME — VOICE OUTBOUND DISPATCHER & LEAD HARVESTER
==============================================================================
Consente ad EBJ di:
1. Sintetizzare messaggi vocali personalizzati ad alta fedeltà con Edge-TTS (voce it-IT-DiegoNeural).
2. Inviare messaggi vocali via Email tramite Google SMTP con allegato audio MP3 e player web.
3. Predisporre payload audio per WhatsApp Business Cloud API / Webhook.
4. Salvare i contatti e i numeri telefonici raccolti nel database verificato (mail_vault.db).
"""

import os
import sys
import json
import time
import asyncio
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VAULT_DB = str(ROOT / "mail_vault.db")
AUDIO_OUT_DIR = ROOT / "public" / "voice_dispatches"
AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)

# Credenziali SMTP Google
GMAIL_USER = "badraudi@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "kqvjcuzibizysoxu")

async def synthesize_voice_note(text: str, filename_prefix="vnote") -> str:
    """Sintetizza una nota vocale MP3 in italiano usando Edge-TTS."""
    import edge_tts
    fn = f"{filename_prefix}_{int(time.time())}.mp3"
    out_path = str(AUDIO_OUT_DIR / fn)
    communicate = edge_tts.Communicate(text, "it-IT-DiegoNeural", rate="+10%")
    await communicate.save(out_path)
    return out_path

def send_voice_email(recipient: str, subject: str, message_text: str, audio_file_path: str, brand="EBJ"):
    """Invia un'email con allegato vocale MP3 e player HTML incorporato."""
    if not os.path.exists(audio_file_path):
        return {"success": False, "error": "File audio non trovato"}

    msg = MIMEMultipart("related")
    msg["From"] = f"EBJ Supreme AI <{GMAIL_USER}>" if brand == "EBJ" else f"SELEZIONE Detergenza <{GMAIL_USER}>"
    msg["To"] = recipient
    msg["Subject"] = f"🎙️ [Nota Vocale] {subject}"

    audio_filename = os.path.basename(audio_file_path)
    audio_public_url = f"https://eb.badrexpress.com/voice_dispatches/{audio_filename}"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f8fafc; padding: 20px; }}
.card {{ background: #131b2e; border: 1px solid #00f0ff; border-radius: 12px; padding: 24px; max-width: 550px; margin: 0 auto; }}
.btn {{ display: inline-block; background: #0284c7; color: #fff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 15px; }}
.quote {{ background: #07090e; border-left: 4px solid #facc15; padding: 12px; margin: 15px 0; font-style: italic; color: #cbd5e1; }}
</style>
</head>
<body>
<div class="card">
    <div style="font-size: 11px; font-weight: bold; color: #00f0ff; text-transform: uppercase;">🎙️ Messaggio Vocale da EBJ Supreme</div>
    <h2 style="color: #fff; margin-top: 8px;">Hai ricevuto un messaggio vocale</h2>
    <div class="quote">"{message_text}"</div>
    <p style="font-size: 13px; color: #94a3b8;">Il file audio MP3 in alta definizione è allegato a questa email e può essere ascoltato anche dal link diretto qui sotto:</p>
    <a href="{audio_public_url}" class="btn">▶️ Ascolta Nota Vocale Online</a>
    <hr style="border: none; border-top: 1px solid #1e293b; margin: 20px 0;">
    <div style="font-size: 11px; color: #64748b;">
        <b>BadrExpress.com & EBJ Supreme</b> · Logistica, Assistenza Intelligente & Distribuzione
    </div>
</div>
</body>
</html>"""

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Allegato Audio
    with open(audio_file_path, "rb") as f:
        part = MIMEBase("audio", "mpeg")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={audio_filename}")
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    return {
        "success": True,
        "recipient": recipient,
        "audio_url": audio_public_url,
        "message": "Nota vocale inviata con successo via email"
    }

def harvest_lead_contact(name: str, phone: str, notes: str, source="FACEBOOK_MARKETPLACE"):
    """Salva un contatto / numero raccolto nel database unificato di EBJ."""
    try:
        conn = sqlite3.connect(VAULT_DB)
        cur = conn.cursor()
        # Inserisci nella tabella verified_leads o b2b_car_washes a seconda della sorgente
        cur.execute("""
            INSERT INTO verified_leads_2026 (nome, telefono, citta, note, stato, fonte)
            VALUES (?, ?, 'Bologna', ?, 'NUOVO_CONTATTO', ?)
        """, (name, phone, notes, source))
        conn.commit()
        lead_id = cur.lastrowid
        conn.close()
        return {"success": True, "lead_id": lead_id, "message": f"Numero {phone} salvato nel Vault"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 2:
        dest_email = sys.argv[1]
        testo = sys.argv[2]
        audio_p = asyncio.run(synthesize_voice_note(testo, "test_dispatch"))
        res = send_voice_email(dest_email, "Test Vocale EBJ", testo, audio_p)
        print(json.dumps(res, indent=2))
    else:
        print("Usage: python voice_outbound_dispatcher.py <email> <testo>")
