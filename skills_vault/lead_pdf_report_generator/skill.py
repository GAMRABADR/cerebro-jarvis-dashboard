import os, time, sqlite3, qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORTS_DIR = os.path.join(BASE_DIR, "public", "reports")
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")
os.makedirs(REPORTS_DIR, exist_ok=True)

def execute(params=None):
    params = params or {}
    city_filter = (params.get("city") or "").lower().strip()
    
    leads = []
    try:
        conn = sqlite3.connect(VAULT_DB)
        c = conn.cursor()
        c.execute("SELECT client_name, phone, city, service_type, volume_mq, estimated_budget, source, verified_status, scraped_date, notes FROM verified_leads_2026 ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        for r in rows:
            if city_filter and city_filter not in r[2].lower():
                continue
            leads.append({
                "name": r[0], "phone": r[1], "city": r[2], "service": r[3],
                "volume_mq": r[4], "budget": r[5] or 0.0, "source": r[6], "status": r[7],
                "date": r[8], "notes": r[9]
            })
    except Exception as e:
        print(f"[Lead PDF DB Err]: {e}")

    total_budget = sum(l["budget"] for l in leads)
    city_name = (city_filter or "Emilia-Romagna Metropoli").title()
    filter_tag = city_filter.replace(" ", "_") if city_filter else "emilia_romagna"
    filename = f"report_leads_{filter_tag}_{int(time.time())}.pdf"
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
            Paragraph(f'<b>PIETRO TRASLOCHI & EBGSTUDIO</b><br/><font size=9 color="#059669"><b>RADAR COMMESSE & CLIENTI VERIFICATI 2026</b></font><br/><font size=8 color="#64748b">Territorio: {city_name.upper()} · Data Generazione: {time.strftime("%d/%m/%Y %H:%M")}</font>', title_style),
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
            Paragraph(f'<b>Commesse Rilevate:</b> {len(leads)} Clienti', text_style),
            Paragraph(f'<b>Valore Totale Pipeline:</b> € {total_budget:,.2f}', phone_style),
            Paragraph('<b>Stato:</b> DISPATCH DIRETTO ATTIVO', subtitle_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[60*mm, 75*mm, 55*mm])
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

    # Lead Cards
    for idx, lead in enumerate(leads):
        card_data = [
            [
                Paragraph(f'<b>#{idx+1} · {lead["name"]}</b>  ({lead["city"]})', card_title_style),
                Paragraph(f'<font color="#059669"><b>[{lead["status"]}]</b></font>', text_style)
            ],
            [
                Paragraph(f'<b>TEL:</b> <font color="#0284c7" size=11.5><b>{lead["phone"]}</b></font>', phone_style),
                Paragraph(f'<b>Budget:</b> € {lead["budget"]:,.2f}  |  <b>Mq:</b> {lead["volume_mq"]} mq', text_style)
            ],
            [
                Paragraph(f'<b>Fonte Scraping:</b> <font color="#4338ca"><b>{lead["source"]}</b></font>', text_style),
                Paragraph(f'<b>Data Annuncio:</b> <font color="#0f766e"><b>{lead["date"]}</b></font>', text_style)
            ],
            [
                Paragraph(f'<b>Servizio:</b> {lead["service"]}', text_style),
                Paragraph(f'<b>Note:</b> {lead["notes"]}', notes_style)
            ]
        ]
        card_table = Table(card_data, colWidths=[115*mm, 75*mm])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#f1f5f9')),
            ('LINEBELOW', (0,2), (-1,2), 0.5, colors.HexColor('#f8fafc')),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        story.append(KeepTogether([card_table, Spacer(1, 2.5*mm)]))


    # Footer Note
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('<font size=7.5 color="#94a3b8">Documento Ufficiale generato dal CEREBRO JARVIS / E.B. SUPREME AI per l\'Ingegner Badr · EBGStudio & Pietro Traslochi · Tutti i diritti riservati 2026.</font>', text_style))

    doc.build(story)

    return {
        "status": "SUCCESS",
        "filename": filename,
        "pdf_path": pdf_path,
        "url": public_url,
        "count": len(leads),
        "total_budget": total_budget,
        "city": city_name
    }

if __name__ == "__main__":
    print(execute({"city": "bologna"}))


