import os
import sys
import csv
import time
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

DASHBOARD_DIR = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard"
sys.path.append(DASHBOARD_DIR)

import ebj_lead_scraper_perfect as perfect_scraper
import server

RECIPIENT_EMAIL = "badraudi@gmail.com"
GMAIL_USER = server.GMAIL_USER
GMAIL_APP_PASS = server.GMAIL_APP_PASS

PDF_FILENAME = "SCHEDA_CLIENTI_BADREXPRESS_SELEZIONE_VERIFICATI.pdf"
CSV_FILENAME = "SCHEDA_CLIENTI_BADREXPRESS_SELEZIONE_VERIFICATI.csv"

PDF_PATH = os.path.join(DASHBOARD_DIR, "public", PDF_FILENAME)
CSV_PATH = os.path.join(DASHBOARD_DIR, "public", CSV_FILENAME)

def clean_text(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_csv(leads):
    print(f"[*] Generazione CSV in corso: {CSV_PATH}")
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "ID", "CATEGORIA", "RAGIONE_SOCIALE", "CITTA", "INDIRIZZO",
            "TELEFONO_FORMATTATO", "TIPO_LINEA", "LINK_CHIAMATA_RAPIDA",
            "LINK_WHATSAPP", "SERVIZIO_OFFERTA", "BRAND_FIRMA", "NOTE_SEDE"
        ])
        for l in leads:
            p = l.get("phone_info", {})
            cat = l.get("category", "")
            brand = "SELEZIONE Chimica" if cat == "AUTOLAVAGGI_SELEZIONE" else "BadrExpress & Pietro Traslochi"
            writer.writerow([
                l.get("id"),
                cat,
                l.get("name"),
                l.get("city"),
                l.get("notes", "").replace("Indirizzo: ", ""),
                p.get("formatted") or p.get("digits"),
                p.get("line_type"),
                p.get("tel_uri"),
                l.get("wa_link"),
                l.get("service"),
                brand,
                l.get("notes")
            ])
    print(f"[+] CSV generato con successo ({len(leads)} righe).")

def generate_pdf(leads):
    print(f"[*] Generazione PDF ReportLab in corso: {PDF_PATH}")
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    color_primary = colors.HexColor("#0284c7")   # Cyan Blue
    color_dark = colors.HexColor("#0f172a")      # Dark Slate
    color_emerald = colors.HexColor("#059669")   # Emerald Green
    color_amber = colors.HexColor("#d97706")     # Amber
    color_bg_light = colors.HexColor("#f8fafc")
    color_gray_text = colors.HexColor("#475569")

    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=color_dark
    )

    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=color_gray_text
    )

    style_badge = ParagraphStyle(
        "DocBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=color_emerald
    )

    style_sec_heading = ParagraphStyle(
        "SecHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=color_dark,
        spaceBefore=14,
        spaceAfter=6
    )

    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    style_cell_name = ParagraphStyle(
        "CellName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=color_dark
    )

    style_cell_text = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=color_gray_text
    )

    style_cell_phone = ParagraphStyle(
        "CellPhone",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=color_primary
    )

    story = []

    # 1. HEADER
    story.append(Paragraph("E.B.J. AI · SCHEDA CLIENTI & DOSSIER RECAPITI", style_title))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "<b>BadrExpress.com · PietroTraslochi.com · SELEZIONE Detergenza Professionale</b><br/>"
        "<i>Dossier Ufficiale Contatti Certificati 100% Geocodificati da Registri Pubblici ed Albi di Settore</i>",
        style_subtitle
    ))
    story.append(Spacer(1, 4 * mm))

    # Info summary box
    agencies_count = len([l for l in leads if l.get("category") == "AGENZIE_IMMOBILIARI_PARTNER"])
    carwash_count = len([l for l in leads if l.get("category") == "AUTOLAVAGGI_SELEZIONE"])
    traslochi_count = len([l for l in leads if l.get("category") == "TRASLOCHI_SGOMBERI"])

    summary_data = [
        [
            Paragraph("<b>TOTALE CONTATTI VERIFICATI</b>", style_cell_name),
            Paragraph("<b>AGENZIE IMMOBILIARI (SGOMBERI)</b>", style_cell_name),
            Paragraph("<b>AUTOLAVAGGI (CHIMICA SELEZIONE)</b>", style_cell_name),
            Paragraph("<b>LOGISTICA & TRASLOCHI</b>", style_cell_name)
        ],
        [
            Paragraph(f"<font size=12 color='#059669'><b>{len(leads)}</b></font>", style_title),
            Paragraph(f"<font size=12 color='#0284c7'><b>{agencies_count}</b></font>", style_title),
            Paragraph(f"<font size=12 color='#d97706'><b>{carwash_count}</b></font>", style_title),
            Paragraph(f"<font size=12 color='#10b981'><b>{traslochi_count}</b></font>", style_title)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[46 * mm, 46 * mm, 47 * mm, 47 * mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color_bg_light),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4 * mm))

    # Note
    story.append(Paragraph(
        "<b>CERTIFICAZIONE DI VERIDICITA':</b> Tutti i recapiti sotto riportati corrispondono a centralini fisici o cellulari aziendali ufficiali. Zero placeholder, zero simulazioni. Consultabile con chiamata 1-click su: <font color='#0284c7'><u>https://eb.badrexpress.com/leads_chiamata_rapida.html</u></font>",
        style_badge
    ))
    story.append(Spacer(1, 4 * mm))

    def make_section_table(section_leads, header_bg, category_label):
        rows = [[
            Paragraph("<b>RAGIONE SOCIALE</b>", style_table_header),
            Paragraph("<b>CITTA' & INDIRIZZO</b>", style_table_header),
            Paragraph("<b>TELEFONO PUBBLICO</b>", style_table_header),
            Paragraph("<b>PROPOSTA / NOTE</b>", style_table_header)
        ]]
        for item in section_leads:
            p = item.get("phone_info", {})
            name = clean_text(item.get("name"))
            city = clean_text(item.get("city"))
            notes = clean_text(item.get("notes", "").replace("Indirizzo: ", ""))
            phone_str = p.get("formatted") or p.get("digits") or clean_text(item.get("phone"))
            line_type = p.get("line_type", "")
            
            rows.append([
                Paragraph(name, style_cell_name),
                Paragraph(f"<b>{city}</b><br/>{notes[:65]}", style_cell_text),
                Paragraph(f"<b>{phone_str}</b><br/><font size=6 color='#64748b'>[{line_type}]</font>", style_cell_phone),
                Paragraph(clean_text(item.get("service"))[:50], style_cell_text)
            ])

        t = Table(rows, colWidths=[52 * mm, 60 * mm, 36 * mm, 38 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, color_bg_light]),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    # SECTION 1: IMMOBILIARI
    agencies = [l for l in leads if l.get("category") == "AGENZIE_IMMOBILIARI_PARTNER"]
    if agencies:
        story.append(Paragraph(f"1. AGENZIE IMMOBILIARI PARTNER — CONVENZIONI SGOMBERI & TRASLOCHI ({len(agencies)} CONTATTI)", style_sec_heading))
        story.append(make_section_table(agencies, colors.HexColor("#0284c7"), "IMMOBILIARE"))
        story.append(Spacer(1, 4 * mm))

    # SECTION 2: AUTOLAVAGGI
    carwashes = [l for l in leads if l.get("category") == "AUTOLAVAGGI_SELEZIONE"]
    if carwashes:
        story.append(Paragraph(f"2. AUTOLAVAGGI & IMPIANTI — VENDITA CHIMICA SELEZIONE ({len(carwashes)} CONTATTI)", style_sec_heading))
        story.append(make_section_table(carwashes, colors.HexColor("#d97706"), "AUTOLAVAGGIO"))
        story.append(Spacer(1, 4 * mm))

    # SECTION 3: TRASLOCHI & ALTRI
    others = [l for l in leads if l.get("category") not in ("AGENZIE_IMMOBILIARI_PARTNER", "AUTOLAVAGGI_SELEZIONE")]
    if others:
        story.append(Paragraph(f"3. DITTE TRASLOCHI & LOGISTICA ({len(others)} CONTATTI)", style_sec_heading))
        story.append(make_section_table(others, colors.HexColor("#059669"), "TRASLOCO"))

    doc.build(story)
    print(f"[+] PDF generato con successo: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")

def send_dossier_email(leads):
    print(f"[*] Invio email via SMTP SSL a {RECIPIENT_EMAIL}...")
    
    agencies_count = len([l for l in leads if l.get("category") == "AGENZIE_IMMOBILIARI_PARTNER"])
    carwash_count = len([l for l in leads if l.get("category") == "AUTOLAVAGGI_SELEZIONE"])
    traslochi_count = len([l for l in leads if l.get("category") == "TRASLOCHI_SGOMBERI"])

    subject = f"📋 SCHEDA CLIENTI COMPLETA E.B.J. · {len(leads)} Contatti Verificati 100% [PDF + CSV]"

    # HTML Body
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
        .card {{ max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }}
        .header {{ background: #020813; padding: 24px 28px; color: #ffffff; border-bottom: 2px solid #00f0ff; }}
        .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px; }}
        .header p {{ margin: 6px 0 0 0; font-size: 13px; color: #00f0ff; }}
        .content {{ padding: 24px 28px; }}
        .banner {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 14px 16px; margin-bottom: 20px; font-size: 13px; color: #065f46; }}
        .banner strong {{ color: #059669; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; text-align: center; }}
        .metric-box {{ background: #f1f5f9; padding: 14px; border-radius: 8px; border: 1px solid #cbd5e1; }}
        .metric-val {{ font-size: 22px; font-weight: 900; color: #0f172a; margin-top: 4px; }}
        .metric-lbl {{ font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }}
        .btn-call-web {{ display: inline-block; background: #10b981; color: #000000; font-weight: 800; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-size: 14px; margin: 16px 0; }}
        .lead-item {{ border-left: 3px solid #0284c7; background: #f8fafc; padding: 10px 14px; margin-bottom: 8px; border-radius: 4px; font-size: 13px; }}
        .footer {{ background: #0f172a; color: #94a3b8; padding: 18px 28px; font-size: 12px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>E.B.J. AI · SCHEDA CLIENTI COMPLETA & DOSSIER RECAPITI</h1>
          <p>BadrExpress.com · PietroTraslochi.com · SELEZIONE Detergenza Professionale</p>
        </div>
        <div class="content">
          <div class="banner">
            <strong>🛡️ 100% REGISTRI PUBBLICI UFFICIALI & RECAPITI CERTIFICATI:</strong><br/>
            Tutti i {len(leads)} contatti allegati a questa email sono stati estratti tramite geocodifica dei registri ufficiali (OpenStreetMap, Albi FIAIP, PagineGialle). Nessun dato fittizio né placeholder: tutti i numeri di telefono corrispondono a centralini o cellulari operativi.
          </div>

          <div class="metrics-grid">
            <div class="metric-box">
              <div class="metric-lbl">Totale Contatti</div>
              <div class="metric-val" style="color: #059669;">{len(leads)}</div>
            </div>
            <div class="metric-box">
              <div class="metric-lbl">Agenzie Immobiliari</div>
              <div class="metric-val" style="color: #0284c7;">{agencies_count}</div>
            </div>
            <div class="metric-box">
              <div class="metric-lbl">Autolavaggi SELEZIONE</div>
              <div class="metric-val" style="color: #d97706;">{carwash_count}</div>
            </div>
          </div>

          <p style="font-size: 14px; line-height: 1.5; color: #334155;">
            Ingegnere, trovi in allegato alla presente email:
          </p>
          <ul style="font-size: 13px; color: #334155; line-height: 1.6;">
            <li>📄 <b>{PDF_FILENAME}</b>: Dossier PDF completo impaginato e diviso per categorie, pronto per la stampa o consultazione rapida.</li>
            <li>📊 <b>{CSV_FILENAME}</b>: Foglio di calcolo compatibile Excel con tutti i campi, indirizzi, numeri formattati e link rapidi.</li>
          </ul>

          <div style="text-align: center; margin: 24px 0;">
            <a href="https://eb.badrexpress.com/leads_chiamata_rapida.html" class="btn-call-web" target="_blank">
              📞 APRI DIALER CHIAMATE RAPIDE 1-CLICK SUL CELLULARE
            </a>
          </div>

          <p style="font-size: 13px; font-weight: bold; color: #0f172a; margin-top: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;">
            ANTEPRIMA PRIMI 8 CONTATTI VERIFICATI:
          </p>
    """

    for l in leads[:8]:
        p = l.get("phone_info", {})
        cat = l.get("category", "")
        border_col = "#d97706" if cat == "AUTOLAVAGGI_SELEZIONE" else "#0284c7"
        tag_name = "AUTOLAVAGGIO" if cat == "AUTOLAVAGGI_SELEZIONE" else "IMMOBILIARE B2B"
        html_content += f"""
          <div class="lead-item" style="border-left-color: {border_col};">
            <div style="font-weight: 800; color: #0f172a; font-size: 14px;">{clean_text(l.get('name'))} · <span style="font-size:11px; color:#64748b;">{clean_text(l.get('city'))}</span></div>
            <div style="color: #475569; font-size: 12px; margin-top: 2px;">{clean_text(l.get('notes'))}</div>
            <div style="margin-top: 6px;">
              <a href="{p.get('tel_uri')}" style="background:#059669; color:#fff; text-decoration:none; padding:4px 10px; border-radius:4px; font-weight:bold; font-size:12px; display:inline-block;">📞 Chiama: {p.get('formatted')}</a>
              <a href="{l.get('wa_link')}" style="background:#25d366; color:#000; text-decoration:none; padding:4px 10px; border-radius:4px; font-weight:bold; font-size:12px; display:inline-block; margin-left:6px;">💬 WhatsApp</a>
            </div>
          </div>
        """

    html_content += f"""
        </div>
        <div class="footer">
          E.B.J. AI Master System · Ingegner Badr El Ouariti · Imola (BO)<br/>
          Server Ufficiale: <a href="https://eb.badrexpress.com/" style="color:#00f0ff;">https://eb.badrexpress.com/</a>
        </div>
      </div>
    </body>
    </html>
    """

    # Plain text fallback
    body_text = f"""E.B.J. AI · SCHEDA CLIENTI & DOSSIER RECAPITI VERIFICATI
BadrExpress.com · PietroTraslochi.com · SELEZIONE Detergenza Professionale

Ingegnere, ecco la scheda clienti completa con tutti i {len(leads)} contatti 100% verificati.
- Totale contatti: {len(leads)}
- Agenzie Immobiliari (Sgomberi & Traslochi): {agencies_count}
- Autolavaggi (Chimica SELEZIONE): {carwash_count}
- Logistica & Altri: {traslochi_count}

File allegati:
1. {PDF_FILENAME} (Dossier PDF completo stampabile)
2. {CSV_FILENAME} (Foglio Excel completo con link diretti)

Web App Dialer 1-Click:
https://eb.badrexpress.com/leads_chiamata_rapida.html
"""

    msg = MIMEMultipart("mixed")
    msg["From"] = f"E.B.J. AI · Jarvis Master <{GMAIL_USER}>"
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(html_content, "html", "utf-8"))
    msg.attach(alt_part)

    # Attach PDF
    if os.path.exists(PDF_PATH):
        with open(PDF_PATH, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=\"{PDF_FILENAME}\"")
        msg.attach(part)
        print(f"[+] Allegato PDF aggiunto ({os.path.getsize(PDF_PATH)} bytes).")

    # Attach CSV
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "rb") as f:
            part = MIMEBase("text", "csv")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=\"{CSV_FILENAME}\"")
        msg.attach(part)
        print(f"[+] Allegato CSV aggiunto ({os.path.getsize(CSV_PATH)} bytes).")

    server_smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20)
    server_smtp.login(GMAIL_USER, GMAIL_APP_PASS)
    server_smtp.sendmail(GMAIL_USER, [RECIPIENT_EMAIL], msg.as_string())
    server_smtp.quit()
    print(f"[SUCCESS] Email recapitata con successo via SMTP SSL 465 a {RECIPIENT_EMAIL}!")

def main():
    print("[1] Caricamento leads verificati...")
    leads = perfect_scraper.get_all_verified_leads(limit=500)
    print(f"[*] Totale leads caricati: {len(leads)}")

    if not leads:
        print("[!] Nessun lead trovato!")
        return

    print("\n[2] Generazione file...")
    generate_csv(leads)
    generate_pdf(leads)

    print("\n[3] Spedizione via Email...")
    send_dossier_email(leads)

    print("\n[FINITO] Operazione completata al 100%!")

if __name__ == "__main__":
    main()
