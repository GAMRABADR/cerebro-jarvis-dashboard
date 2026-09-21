#!/usr/bin/env python3
"""
==============================================================================
🤝 JEV & EBJ — META MARKETPLACE AUTO-RESPONDER & LEAD HARVESTER
==============================================================================
Gestisce automaticamente i messaggi in arrivo su Facebook Messenger / Marketplace:
1. Riconosce le domande tipiche degli acquirenti ("È disponibile?", "Trattabile?", "Consegni?").
2. Risponde in modo cordiale, professionale ed empatico in nome di BadrExpress.com.
3. Propone l'offerta blocco (200€) e la consegna furgonata al piano a domicilio.
4. Chiede il numero di telefono ("Lasciami il tuo WhatsApp...") e lo cattura con regex, salvandolo in automatico nel CRM di mail_vault.db!
"""

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VAULT_DB = str(ROOT / "mail_vault.db")

def generate_smart_reply(buyer_name: str, message: str) -> dict:
    """Genera la risposta persuasiva di EBJ & JEV e verifica se c'è un numero di telefono."""
    msg_clean = message.lower().strip()
    
    # 1. Regex per estrarre numeri di telefono italiani (es. 3331234567, +39 340 1234567, 051...)
    phone_match = re.search(r'(?:(?:\+|00)39[\s.-]?)?(?:3\d{2}[\s.-]?\d{6,7}|0\d{1,3}[\s.-]?\d{5,7})', message)
    captured_phone = phone_match.group(0).replace(" ", "").replace("-", "").replace(".", "") if phone_match else None

    # Se l'utente ha mandato il suo numero di telefono, salvalo subito!
    if captured_phone:
        _save_lead(buyer_name, captured_phone, f"Interessato alle 3 porte: '{message}'")
        return {
            "reply": f"Perfetto {buyer_name}! Ho registrato il tuo numero ({captured_phone}). Ti ricontatto subito su WhatsApp o telefonicamente per concordare i dettagli e l'eventuale consegna a domicilio con BadrExpress!",
            "phone_captured": captured_phone,
            "action": "LEAD_HARVESTED"
        }

    # 2. Se chiedono se è disponibile
    if any(w in msg_clean for w in ["disponibile", "disponibili", "ancora", "dispo"]):
        return {
            "reply": f"Ciao {buyer_name}! Sì, le 3 porte in legno massello sono ancora disponibili e pronte per il montaggio (complete di stipiti, cardini, maniglie e chiavi originali).\nIl prezzo è di 75€ cad. oppure 200€ per tutte e 3.\n🚚 Se non hai il furgone, siamo disponibili al trasporto con consegna direttamente in casa tua!\nIn che zona ti trovi? Se mi lasci il tuo cellulare/WhatsApp ci sentiamo al volo per organizzarci!",
            "phone_captured": None,
            "action": "AVAILABILITY_CONFIRMED"
        }

    # 3. Se chiedono del prezzo o sconto
    if any(w in msg_clean for w in ["trattabile", "prezzo", "sconto", "meno", "ultimo prezzo"]):
        return {
            "reply": f"Ciao {buyer_name}, per chi prende tutto il blocco delle 3 porte complete posso fare 200€ totali (da nuove costano oltre 300€ l'una, sono in vero massello con cardini e chiavi incluse).\nInoltre se sei vicino a Imola/Bologna posso organizzare il trasporto direttamente a casa tua con piccolo supplemento concordato!\nLasciami il tuo numero WhatsApp così ci accordiamo subito!",
            "phone_captured": None,
            "action": "PRICE_NEGOTIATED"
        }

    # 4. Se chiedono di trasporto o consegna
    if any(w in msg_clean for w in ["trasporto", "consegna", "furgone", "porti", "casa", "piano"]):
        return {
            "reply": f"Certamente {buyer_name}! Con il nostro servizio BadrExpress offriamo il trasporto dedicato con furgone e possiamo effettuare la consegna direttamente dentro casa / al piano con una piccola aggiunta concordata!\nIn quale città o via ti trovi? Lasciami il tuo recapito telefonico così calcoliamo la tariffa di consegna più economica per te!",
            "phone_captured": None,
            "action": "TRANSPORT_PROPOSED"
        }

    # Risposta generale di cortesia con richiesta contatto
    return {
        "reply": f"Ciao {buyer_name}, grazie per averci contattato! Le porte sono in ottime condizioni, complete di tutto il controtelaio e chiavi originali.\nOffriamo anche il servizio di trasporto e consegna in casa con furgone BadrExpress.\nLasciami pure il tuo numero di telefono o WhatsApp così ti invio ulteriori foto o ci accordiamo al volo!",
        "phone_captured": None,
        "action": "GENERAL_INQUIRY"
    }

def _save_lead(name: str, phone: str, notes: str):
    try:
        conn = sqlite3.connect(VAULT_DB)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS marketplace_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_name TEXT,
                phone TEXT,
                notes TEXT,
                item TEXT DEFAULT '3 Porte Legno Massello',
                status TEXT DEFAULT 'DA_RICONTAKTARE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            INSERT INTO marketplace_leads (buyer_name, phone, notes)
            VALUES (?, ?, ?)
        """, (name, phone, notes))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LEAD HARVEST ERROR]: {e}")

if __name__ == "__main__":
    test_msg = "Ciao, sono Marco, le porte sono ancora disponibili? Mio numero 3401234567"
    res = generate_smart_reply("Marco", test_msg)
    print(res["reply"])
    print(f"Telefono catturato: {res['phone_captured']}")
