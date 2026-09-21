#!/usr/bin/env python3
"""
EBJ Supreme - Email Dispatcher Lead Bologna
Spedisce il dossier completo dei lead verificati di Bologna e provincia a badraudi@gmail.com,
con tabella contatti, link WhatsApp diretti e dettagli economici.
"""

import sys
import os
import re
import json
import sqlite3
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_vault.db")
GMAIL_USER = "badraudi@gmail.com"
GMAIL_PASS = "kqvjcuzibizysoxu"
RECIPIENT = "badraudi@gmail.com"

def get_verified_leads():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, client_name, phone, city, service_type, volume_mq, estimated_budget, source, notes, scraped_date, whatsapp_link
        FROM verified_leads_2026
        WHERE verified_status = 'VERIFICATO'
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def dispatch_email():
    print("=" * 65)
    print("   DISPATCH EMAIL LEAD BOLOGNA — BADREXPRESS & PIETROTRASLOCHI   ")
    print("=" * 65)

    leads = get_verified_leads()
    print(f"[*] Trovati {len(leads)} lead verificati nel Vault.")

    now_str = datetime.datetime.now().strftime("%d/%m/%Y ore %H:%M")
    total_budget = sum(row[6] for row in leads)

    val_rows_html = ""
    for idx, row in enumerate(leads):
        lead_id, name, phone, city, service, volume, budget, source, notes, date, wa_link = row
        clean_num = re.sub(r'[^0-9]', '', phone)
        wa_url = wa_link if wa_link else f"https://wa.me/{clean_num}"

        val_rows_html += f"""
        <tr style="border-bottom: 1px solid #e2e8f0; background: {('#f8fafc' if idx % 2 == 0 else '#ffffff')};">
            <td style="padding: 12px; font-weight: bold; color: #0f172a;">#{lead_id} {name}</td>
            <td style="padding: 12px; color: #0284c7; font-size: 14px; font-weight: bold;">
                <a href="{wa_url}" target="_blank" style="display: inline-block; background: #22c55e; color: #ffffff; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">
                    💬 WhatsApp {phone}
                </a>
            </td>
            <td style="padding: 12px; color: #334155;"><b>{city}</b><br><small style="color: #64748b;">{service} ({volume} mq)</small></td>
            <td style="padding: 12px; font-weight: bold; color: #059669; font-size: 15px;">€ {budget:,.2f}</td>
            <td style="padding: 12px; font-size: 12px; color: #475569;">
                <b>{source}</b><br>
                <span style="font-size: 11px; color: #64748b;">{notes[:100]}...</span>
            </td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background-color: #0b1320; padding: 25px; color: #e2e8f0; margin: 0;">
        <div style="max-width: 850px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.3); color: #1e293b;">
            <!-- Header Stark Arc Reactor Style -->
            <div style="background: linear-gradient(135deg, #04101e 0%, #0f2744 100%); padding: 24px; color: #ffffff; border-bottom: 4px solid #00f0ff;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h1 style="margin: 0; font-size: 22px; color: #ffffff; letter-spacing: 1px;">🎯 E.B.J. SUPREME · DOSSIER COMMESSE BOLOGNA</h1>
                        <p style="margin: 6px 0 0 0; font-size: 13px; color: #38bdf8;">Persone Reali & Recapiti Verificati al 100% · Data Invio: {now_str}</p>
                    </div>
                    <div style="background: rgba(0, 240, 255, 0.15); border: 1px solid #00f0ff; border-radius: 8px; padding: 8px 14px; text-align: right;">
                        <span style="display: block; font-size: 11px; color: #94a3b8; text-transform: uppercase;">Pipeline Bologna</span>
                        <span style="font-size: 18px; font-weight: bold; color: #00f0ff;">€ {total_budget:,.2f}</span>
                    </div>
                </div>
            </div>

            <div style="padding: 24px;">
                <!-- Box Certificazione -->
                <div style="background: #f0fdf4; border: 1px solid #86efac; border-left: 5px solid #22c55e; border-radius: 6px; padding: 14px 18px; margin-bottom: 22px;">
                    <h3 style="margin: 0 0 6px 0; color: #166534; font-size: 15px;">🛡️ Audit Anti-Competitor & Recapiti Certificati</h3>
                    <p style="margin: 0; font-size: 13px; color: #15803d; line-height: 1.5;">
                        Tutti i lead sottostanti sono stati filtrati escludendo tassativamente ditte di trasloco, cooperative e titolari di P.IVA.
                        I numeri di telefono sono cellulari italiani validati in formato E.164 con link diretto click-to-chat.
                    </p>
                </div>

                <!-- Tabella Lead -->
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 13px;">
                    <thead>
                        <tr style="background: #f1f5f9; color: #475569; text-align: left; border-bottom: 2px solid #cbd5e1;">
                            <th style="padding: 10px;">Cliente</th>
                            <th style="padding: 10px;">Azione Diretta</th>
                            <th style="padding: 10px;">Zona & Lavoro</th>
                            <th style="padding: 10px;">Budget</th>
                            <th style="padding: 10px;">Dettagli Richiesta</th>
                        </tr>
                    </thead>
                    <tbody>
                        {val_rows_html}
                    </tbody>
                </table>

                <!-- Info Operative -->
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; font-size: 13px; color: #475569;">
                    <b>Squadra Operativa Assegnata:</b> Badr (+39 388 870 3508) & Pietro (+39 328 426 3554)<br>
                    <b>Mezzo Disponibile:</b> Furgone gran volume con sponda idraulica e montascale per scale strette centro storico.
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #f1f5f9; padding: 16px 24px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; text-align: center;">
                BadrExpress.com & PietroTraslochi.com · E.B.J. AI OS Autonomous Intelligence<br>
                Questo messaggio è stato generato e trasmesso in modo autonomo dall'agente.
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = f"EBJ Lead Radar <{GMAIL_USER}>"
    msg['To'] = RECIPIENT
    msg['Subject'] = f"🎯 [LEAD BOLOGNA] {len(leads)} Commesse Verificate · Totale € {total_budget:,.2f} ({now_str})"
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    # Genera anche allegato PDF rapido se possibile
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Dossier_Lead_Bologna_Oggi.pdf")
    try:
        # Usa il binario Rust per generare il PDF se disponibile
        rust_mcp = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\ebj-supreme\jarvis-bridge\target\release\ebj-mcp-server.exe"
        if os.path.exists(rust_mcp):
            import subprocess
            proc = subprocess.Popen([rust_mcp], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            rpc_call = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "ebj_generate_pdf",
                    "arguments": {
                        "output_path": pdf_path,
                        "title": f"Dossier Lead Bologna - {len(leads)} Clienti",
                        "client_name": "Badr & Pietro",
                        "total_amount": float(total_budget),
                        "notes": "Commesse verificate Bologna e provincia con recapito certo."
                    }
                }
            }
            proc.stdin.write(json.dumps(rpc_call) + "\n")
            proc.stdin.flush()
            proc.terminate()
            proc.wait(timeout=2)

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=Dossier_Lead_Bologna_Oggi.pdf")
            msg.attach(part)
            print(f"  [+] Allegato PDF generato con successo: {pdf_path}")
    except Exception as e_pdf:
        print(f"  [!] Nota PDF: {e_pdf}")

    try:
        print(f"[*] Connessione a smtp.gmail.com:465 in corso...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, [RECIPIENT], msg.as_string())
        print(f"[SUCCESS] Email con i lead di Bologna inviata con successo a {RECIPIENT}!")
        return True
    except Exception as e_mail:
        print(f"[ERROR] Invio email fallito: {e_mail}")
        return False

if __name__ == "__main__":
    dispatch_email()
