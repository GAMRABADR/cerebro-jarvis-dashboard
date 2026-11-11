"""
==============================================================================
EBJ REAL ESTATE MAILER & OUTREACH DISPATCHER
==============================================================================
Modulo autonomo per inviare email professionali personalizzate ad agenzie
immobiliari indicate da Badr o censite nel database di partnership di BadrExpress.

Supporta:
  - Invio mirato a una o più agenzie specificate per email o nome
  - Proposta commerciale di partnership per sgomberi cantine/soffitte, traslochi inquilini
  - Selezione brand (BadrExpress.com & PietroTraslochi.com)
  - Notifica istantanea all'Ingegnere Badr (badraudi@gmail.com) con riepilogo
==============================================================================
"""
from __future__ import annotations
import os
import sys
import time
from typing import Dict, Any, List, Optional
from ebj_system_ops_executor import send_universal_email

# Directory agenzie di riferimento e partner verificati
DEFAULT_AGENCIES = [
    {
        "name": "Agenzia Immobiliare Bologna Centro",
        "email": "info@immobiliarebolognacentro.it",
        "city": "Bologna",
        "contact_person": "Responsabile Acquisizioni / Locazioni"
    },
    {
        "name": "Immobiliare San Vitale",
        "email": "sanvitale@gruppocasa.it",
        "city": "Bologna",
        "contact_person": "Ufficio Gestioni"
    },
    {
        "name": "Tecnocasa Bologna San Donato",
        "email": "boca3@tecnocasa.it",
        "city": "Bologna",
        "contact_person": "Team Locazioni & Vendite"
    },
    {
        "name": "Tempocasa Bologna Mazzini",
        "email": "bolognamazzini@tempocasa.it",
        "city": "Bologna",
        "contact_person": "Ufficio Vendite"
    }
]

def build_real_estate_proposal(agency_name: str, city: str = "Bologna") -> Dict[str, str]:
    """Genera oggetto e testo email di convenzione professionale per le agenzie immobiliari."""
    subject = f"Proposta di Collaborazione Operativa Sgomberi & Traslochi · {agency_name} & BadrExpress"
    body = f"""Gentile Team di {agency_name},

Vi contattiamo per proporre una convenzione operativa diretta e dedicata alla Vostra agenzia su {city} e provincia per la gestione chiavi in mano di:

1. SGOMBERI RAPIDI CERTIFICATI: Sgombero totale di appartamenti, cantine, solai e garage pre-rogito o pre-locazione, con smaltimento ecologico autorizzato.
2. TRASLOCHI CLIENTI: Servizio dedicato per i Vostri acquirenti e inquilini con smontaggio/rimontaggio mobili, imballaggio e furgoni con sponda idraulica.
3. INTERVENTI URGENTI: Operatività garantita 7 giorni su 7 con preventivazione immediata e tariffe agevolate riservate ai Vostri clienti e proprietari.

Siamo operativi con sede in Via San Vitale 187/189 a Bologna.
Restiamo a Vostra completa disposizione per una rapida prova sul campo o per concordare una percentuale di convenzione sui lavori segnalati.

Cordiali Saluti,
Badr El Ouariti
Titolare & Responsabile Operativo
Pietro Traslochi & BadrExpress.com
Tel / WhatsApp: +39 388 870 3508
Web: https://badrexpress.com | https://pietrotraslochi.com
"""
    return {"subject": subject, "body": body}

def send_to_real_estate(
    recipient_email: str,
    agency_name: Optional[str] = None,
    city: str = "Bologna",
    custom_subject: Optional[str] = None,
    custom_body: Optional[str] = None,
    notify_badr: bool = True
) -> Dict[str, Any]:
    """Invia un'email commerciale a un'agenzia immobiliare specifica."""
    name = agency_name or "Agenzia Immobiliare"
    template = build_real_estate_proposal(name, city)
    
    subj = custom_subject or template["subject"]
    content = custom_body or template["body"]

    res = send_universal_email(
        to=recipient_email,
        subject=subj,
        body=content,
        brand="EBJ"
    )

    if notify_badr and res.get("status") == "success":
        # Invia copia/notifica riepilogativa a Badr
        notification_body = (
            f"⚡ EBJ SUPREME OUTREACH REPORT:\n\n"
            f"Email commerciale inviata con successo all'agenzia immobiliare:\n"
            f"• Nome Agenzia: {name}\n"
            f"• Destinatario: {recipient_email}\n"
            f"• Città: {city}\n"
            f"• Oggetto: {subj}\n\n"
            f"Stato invio SMTP: OK (Latenza: {res.get('latency_ms')} ms)"
        )
        send_universal_email(
            to="badraudi@gmail.com",
            subject=f"[EBJ Outreach] Email inviata a {name}",
            body=notification_body,
            brand="EBJ"
        )

    return res

def execute_real_estate_mailer(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handler per EBJ Ability Registry."""
    target_email = payload.get("email") or payload.get("recipient")
    agency_name = payload.get("agency_name") or payload.get("name")
    city = payload.get("city", "Bologna")
    query = payload.get("query", "")

    # Se non c'è email, cerca prima nel DB reale b2b_real_estate_agencies, poi fallback presets
    if not target_email:
        try:
            import sqlite3
            from ebj_lead_sanitizer import validate_email_address
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_vault.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                rows = conn.execute(
                    "SELECT agency_name, email, city FROM b2b_real_estate_agencies WHERE email != '' ORDER BY id DESC LIMIT 30"
                ).fetchall()
                conn.close()
                for r_name, r_email, r_city in rows:
                    ok_em, _ = validate_email_address(r_email, check_dns=True)
                    if ok_em and (not agency_name or agency_name.lower() in r_name.lower()):
                        target_email = r_email
                        agency_name = r_name
                        city = r_city or city
                        break
        except Exception:
            pass

    if not target_email:
        matching = [a for a in DEFAULT_AGENCIES if agency_name and agency_name.lower() in a["name"].lower()]
        if matching:
            target = matching[0]
            target_email = target["email"]
            agency_name = target["name"]
        else:
            return {
                "status": "need_recipient",
                "message": "Specificare l'indirizzo email dell'agenzia o avviare /api/b2b/crawl-and-enrich.",
                "available_presets": [a["name"] for a in DEFAULT_AGENCIES]
            }

    return send_to_real_estate(
        recipient_email=target_email,
        agency_name=agency_name,
        city=city,
        custom_subject=payload.get("subject"),
        custom_body=payload.get("body")
    )
