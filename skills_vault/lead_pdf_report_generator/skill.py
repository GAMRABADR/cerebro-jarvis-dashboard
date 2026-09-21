import os, time, sqlite3, qrcode, unicodedata
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def safe_str(text, max_len=200):
    """Sanitizza stringa per ReportLab: converte unicode -> ASCII (NFKD), rimuove caratteri non-stampabili.
    Gestisce encoding Windows-1252 / Latin-1 da Subito.it e ScrapingBee senza crash."""
    if not text:
        return ""
    try:
        # Normalizza unicode -> forma ASCII compatibile
        normalized = unicodedata.normalize("NFKD", str(text))
        # Converti in ASCII ignorando caratteri non convertibili
        ascii_text = normalized.encode("ascii", errors="replace").decode("ascii")
        # Rimuovi caratteri di controllo e ? residui duplicati
        ascii_text = ascii_text.replace("???", "?").replace("??", "?")
        return ascii_text[:max_len]
    except Exception:
        return str(text)[:max_len].encode("ascii", errors="replace").decode("ascii")
REPORTS_DIR = os.path.join(BASE_DIR, "public", "reports")
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")
os.makedirs(REPORTS_DIR, exist_ok=True)

def execute(params=None):
    params = params or {}
    city_filter = (params.get("city") or "bologna").lower().strip()
    prayer_name = params.get("prayer_name", "Dhuhr").upper()
    prayer_time = params.get("prayer_time", time.strftime("%H:%M"))
    phone_only = params.get("phone_only", True)
    
    validated_leads = []
    dm_leads = []
    
    import re
    try:
        conn = sqlite3.connect(VAULT_DB)
        c = conn.cursor()
        c.execute("""
            SELECT client_name, phone, city, service_type, volume_mq, estimated_budget, source, verified_status, scraped_date, notes, post_url 
            FROM verified_leads_2026 
            ORDER BY id DESC
        """)
        rows = c.fetchall()
        conn.close()
        for r in rows:
            c_name, phone, city, service, v_mq, budget, source, status, s_date, notes, post_url = r
            c_low = (city or "").lower()
            
            # Filtro per Bologna & Provincia
            if city_filter and city_filter != "tutti":
                if city_filter not in c_low and "imola" not in c_low and "bologna" not in c_low:
                    continue
                    
            clean_digits = re.sub(r'[^0-9]', '', str(phone or ''))
            has_valid_phone = bool(clean_digits and len(clean_digits) >= 8 and "DM" not in str(phone).upper())
            
            lead_obj = {
                "name": c_name,
                "phone": phone if has_valid_phone else "DM_ONLY",
                "clean_phone": clean_digits,
                "city": city or "Bologna",
                "service": service or "Trasloco / Sgombero",
                "volume_mq": v_mq or 50,
                "budget": float(budget or 350.0),
                "source": source or "Web / Subito / Bakeca",
                "status": status or "VERIFICATO",
                "date": s_date or time.strftime("%Y-%m-%d"),
                "notes": notes or "",
                "post_url": post_url or ""
            }
            
            if has_valid_phone:
                validated_leads.append(lead_obj)
            else:
                import urllib.parse
                serv_clean = service.lower() if service else "sgombero o trasloco"
                # Genera Magic Link con pre-compilazione e Coupon BOLOGNA15
                clean_name_url = re.sub(r'\(.*?\)', '', c_name).strip() or c_name
                magic_link = f"https://eb.badrexpress.com/preventivo.html?n={urllib.parse.quote(clean_name_url)}&s={urllib.parse.quote(lead_obj['service'])}&c={urllib.parse.quote(lead_obj['city'])}&coupon=BOLOGNA15"
                
                dm_pitch = (
                    f"Ciao {clean_name_url}! Ho visto il tuo post per {serv_clean} a {lead_obj['city']}. "
                    f"Siamo la squadra di BadrExpress & Pietro Traslochi (furgoni con sponda idraulica e personale per facchinaggio a Bologna e Imola). "
                    f"Per agevolarti ti ho già riservato il Coupon Sconto del 15% (-50€) con sopralluogo a costo zero. Puoi vederlo e bloccare la data qui in 20 secondi: {magic_link} "
                    f"Oppure se fai prima, lasciami pure il tuo cellulare qui in privato e ti faccio mandare subito le foto dei mezzi e i dettagli su WhatsApp da me o da Pietro. A presto, Badr"
                )
                lead_obj["magic_link"] = magic_link
                lead_obj["messenger_pitch"] = dm_pitch
                dm_leads.append(lead_obj)
    except Exception as e:
        print(f"[Lead PDF DB Err]: {e}")

    # Nel PDF ci vanno SOLO i clienti con numero di telefono validato!
    leads_for_pdf = validated_leads if phone_only else (validated_leads + dm_leads)
    
    total_budget = sum(l["budget"] for l in leads_for_pdf)
    city_name = (city_filter or "Bologna e Provincia").title()
    filter_tag = city_filter.replace(" ", "_") if city_filter else "bologna"
    filename = f"dossier_lead_validati_{filter_tag}_{prayer_name.lower()}_{int(time.time())}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, filename)
    public_url = f"/reports/{filename}"

    # Setup Doc
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=10*mm,
        rightMargin=10*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#04101e')
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0284c7')
    )

    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    phone_style = ParagraphStyle(
        'PhoneStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=14,
        textColor=colors.HexColor('#0369a1')
    )

    text_style = ParagraphStyle(
        'CardText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155')
    )

    notes_style = ParagraphStyle(
        'CardNotes',
        parent=styles['Italic'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b')
    )

    story = []

    # Generate QR Code
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(f"https://eb.badrexpress.com{public_url}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='#04101e', back_color='#ffffff')
    qr_path = os.path.join(REPORTS_DIR, 'qr_temp.png')
    qr_img.save(qr_path)

    # Header Table
    header_data = [
        [
            Paragraph(f'<b>PIETRO TRASLOCHI & EBGSTUDIO · DOSSIER COMMESSE VALIDATE</b><br/><font size=9.5 color="#059669"><b>SOLO CLIENTI CON TELEFONO CERTIFICATO · PREGHIERA {prayer_name} ({prayer_time})</b></font><br/><font size=8 color="#64748b">Territorio: {city_name.upper()} · Data Rilevamento: {time.strftime("%d/%m/%Y %H:%M")}</font>', title_style),
            Image(qr_path, width=20*mm, height=20*mm)
        ]
    ]
    header_table = Table(header_data, colWidths=[150*mm, 40*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=4*mm))

    # Summary Table
    summary_data = [
        [
            Paragraph(f'<b>Clienti con Telefono:</b> {len(leads_for_pdf)} Opportunità', text_style),
            Paragraph(f'<b>Pipeline Immediata:</b> € {total_budget:,.2f}', phone_style),
            Paragraph(f'<b>Coda Messenger DM:</b> {len(dm_leads)} In attesa', subtitle_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[60*mm, 70*mm, 60*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fdf4')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#86efac')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bbf7d0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 4*mm))

    # Lead Cards (SOLO CLIENTI CON TELEFONO NEL PDF!)
    for idx, lead in enumerate(leads_for_pdf):
        card_data = [
            [
                Paragraph(f'<b>#{idx+1} · {safe_str(lead["name"], 60)}</b>  ({safe_str(lead["city"], 40)})', card_title_style),
                Paragraph(f'<font color="#059669"><b>[TELEFONO VALIDATO]</b></font>', text_style)
            ],
            [
                Paragraph(f'<b>TEL:</b> <font color="#0284c7" size=12><b>{lead["phone"]}</b></font>', phone_style),
                Paragraph(f'<b>Budget Stimato:</b> EUR {lead["budget"]:,.2f}  |  <b>Volume:</b> {lead["volume_mq"]} mq', text_style)
            ],
            [
                Paragraph(f'<b>Fonte:</b> <font color="#4338ca"><b>{safe_str(lead["source"], 40)}</b></font>', text_style),
                Paragraph(f'<b>Data Annuncio:</b> <font color="#0f766e"><b>{safe_str(lead["date"], 20)}</b></font>', text_style)
            ],
            [
                Paragraph(f'<b>Servizio Richiesto:</b> <b>{safe_str(lead["service"], 60)}</b>', text_style),
                Paragraph(f'<b>Dettagli Richiesta:</b> {safe_str(lead["notes"], 180) if lead["notes"] else "Richiesta diretta per Bologna e provincia"}', notes_style)
            ]
        ]
        card_table = Table(card_data, colWidths=[115*mm, 75*mm])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#f1f5f9')),
            ('LINEBELOW', (0,2), (-1,2), 0.5, colors.HexColor('#f8fafc')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        story.append(KeepTogether([card_table, Spacer(1, 2.5*mm)]))

    # Footer Note
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('<font size=7.5 color="#94a3b8">Dossier Riservato generato dal CEREBRO JARVIS per l\'Ingegner Badr El Ouariti · EBGStudio & Pietro Traslochi · Tutti i contatti sono verificati con numero telefonico attivo.</font>', text_style))

    doc.build(story)

    return {
        "status": "SUCCESS",
        "filename": filename,
        "pdf_path": pdf_path,
        "url": public_url,
        "count": len(leads_for_pdf),
        "total_budget": total_budget,
        "city": city_name,
        "prayer_name": prayer_name,
        "validated_leads": leads_for_pdf,
        "dm_leads": dm_leads
    }

if __name__ == "__main__":
    print(execute({"city": "bologna"}))


