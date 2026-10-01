import os
import sys
import re
import urllib.parse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

DASHBOARD_DIR = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard"
PUBLIC_DIR = os.path.join(DASHBOARD_DIR, "public")

def clean_text(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def generate_custom_leads_pdf(leads, output_path, filter_cat="ALL", filter_city="ALL"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm
    )

    styles = getSampleStyleSheet()

    color_navy = colors.HexColor("#020813")
    color_cyan = colors.HexColor("#0284c7")
    color_emerald = colors.HexColor("#059669")
    color_amber = colors.HexColor("#d97706")
    color_bg_light = colors.HexColor("#f8fafc")
    color_gray_text = colors.HexColor("#475569")
    color_border = colors.HexColor("#cbd5e1")

    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=color_navy
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=color_gray_text
    )
    style_filter_info = ParagraphStyle(
        "FilterInfo",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=color_emerald
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )
    style_cell_name = ParagraphStyle(
        "CellName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=color_navy
    )
    style_cell_text = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=8.5,
        textColor=color_gray_text
    )
    style_cell_phone = ParagraphStyle(
        "CellPhone",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=color_emerald
    )
    style_sec_heading = ParagraphStyle(
        "SecHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=color_navy,
        spaceBefore=8,
        spaceAfter=4
    )

    story = []

    # 1. HEADER WITH LOGO AND BRANDING
    logo_path = os.path.join(PUBLIC_DIR, "ebj_supreme_logo.jpg")
    logo_img = None
    if os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=18 * mm, height=18 * mm)
        except Exception:
            logo_img = None

    header_text = [
        Paragraph("<b>BADREXPRESS.COM · PIETROTRASLOCHI.COM</b>", style_title),
        Paragraph("<i>Logistica, Traslochi Nazionali &amp; Sgomberi Pre-Rogito ad Alta Priorità</i><br/>"
                  "<b>In collaborazione con SELEZIONE — Detergenza &amp; Chimica Professionale Autolavaggi</b>", style_subtitle),
    ]

    filter_desc = f"Filtro Categoria: <b>{filter_cat}</b> · Città: <b>{filter_city}</b> · Contatti Stampati: <b>{len(leads)}</b>"
    header_text.append(Paragraph(filter_desc, style_filter_info))

    if logo_img:
        hdr_table_data = [[logo_img, header_text]]
        hdr_table = Table(hdr_table_data, colWidths=[22 * mm, 168 * mm])
        hdr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(hdr_table)
    else:
        for p in header_text:
            story.append(p)

    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=color_cyan, spaceBefore=1, spaceAfter=4))

    # Click instructions banner
    story.append(Paragraph(
        "<b>📱 SCHEDA INTERATTIVA 1-CLICK:</b> I numeri di telefono sotto riportati sono <b>cliccabili</b>. Cliccando su qualsiasi numero dal cellulare o dal PC parte direttamente la telefonata senza doverlo ricopiare. Cliccando su [WA] si apre la chat WhatsApp con messaggio pre-compilato.",
        ParagraphStyle("Notice", parent=styles["Normal"], fontName="Helvetica", fontSize=7.2, leading=9, textColor=color_gray_text)
    ))
    story.append(Spacer(1, 3 * mm))

    # Function to create table for a subset of leads
    def make_table(subset_leads, header_bg):
        rows = [[
            Paragraph("<b>RAGIONE SOCIALE</b>", style_table_header),
            Paragraph("<b>LOCALITA' &amp; INDIRIZZO</b>", style_table_header),
            Paragraph("<b>TELEFONO 1-CLICK</b>", style_table_header),
            Paragraph("<b>AZIONI RAPIDE</b>", style_table_header),
            Paragraph("<b>SERVIZIO / NOTE</b>", style_table_header)
        ]]

        for l in subset_leads:
            p = l.get("phone_info", {})
            name = clean_text(l.get("name"))
            city = clean_text(l.get("city"))
            notes = clean_text(l.get("notes", "").replace("Indirizzo: ", ""))
            tel_uri = p.get("tel_uri") or f"tel:{p.get('digits')}"
            wa_url = l.get("wa_link") or f"https://wa.me/{p.get('digits')}"
            formatted_phone = p.get("formatted") or p.get("digits") or l.get("phone")
            line_type = p.get("line_type") or "ATTIVO"

            # Clickable phone paragraph
            phone_html = f"<a href='{tel_uri}' color='#059669'><b>📞 {formatted_phone}</b></a><br/><font size=6 color='#64748b'>[{line_type}]</font>"
            actions_html = f"<a href='{wa_url}' color='#16a34a'><b>💬 [WA]</b></a>"

            rows.append([
                Paragraph(name, style_cell_name),
                Paragraph(f"<b>{city}</b><br/>{notes[:55]}", style_cell_text),
                Paragraph(phone_html, style_cell_phone),
                Paragraph(actions_html, style_cell_text),
                Paragraph(clean_text(l.get("service"))[:45], style_cell_text)
            ])

        t = Table(rows, colWidths=[46 * mm, 54 * mm, 34 * mm, 18 * mm, 38 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, color_bg_light]),
            ('GRID', (0, 0), (-1, -1), 0.35, color_border),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        return t

    # Group leads by category
    agencies = [l for l in leads if l.get("category") == "AGENZIE_IMMOBILIARI_PARTNER"]
    carwashes = [l for l in leads if l.get("category") == "AUTOLAVAGGI_SELEZIONE"]
    others = [l for l in leads if l.get("category") not in ("AGENZIE_IMMOBILIARI_PARTNER", "AUTOLAVAGGI_SELEZIONE")]

    if agencies:
        story.append(Paragraph(f"🏢 AGENZIE IMMOBILIARI PARTNER — CONVENZIONI SGOMBERI &amp; TRASLOCHI ({len(agencies)})", style_sec_heading))
        story.append(make_table(agencies, colors.HexColor("#0284c7")))
        story.append(Spacer(1, 3 * mm))

    if carwashes:
        story.append(Paragraph(f"🚗 AUTOLAVAGGI &amp; IMPIANTI — VENDITA CHIMICA SELEZIONE ({len(carwashes)})", style_sec_heading))
        story.append(make_table(carwashes, colors.HexColor("#d97706")))
        story.append(Spacer(1, 3 * mm))

    if others:
        story.append(Paragraph(f"📦 DITTE TRASLOCHI &amp; LOGISTICA ({len(others)})", style_sec_heading))
        story.append(make_table(others, colors.HexColor("#059669")))

    doc.build(story)
    return output_path
