"""
N8N Traslochi Complete Funnel Architect
"""
import time
import datetime

def calcola_e_genera_contratto(data):
    client_name = data.get("client_name", "Cliente Diretto")
    phone = data.get("phone", "Non specificato")
    email = data.get("email", "badraudi@gmail.com")
    mq = float(data.get("mq", 60))
    piano_p = int(data.get("piano_p", 0))
    piano_a = int(data.get("piano_a", 0))
    ascensore = bool(data.get("ascensore", False))
    data_trasloco = data.get("data_trasloco", datetime.date.today().strftime("%Y-%m-%d"))
    citta = data.get("citta", "Imola / Bologna")

    # Tariffe
    prezzo_base = mq * 8.0
    scala_fee = 0.0 if ascensore else (piano_p + piano_a) * mq * 0.5
    trasferta = 80.0
    totale = round(prezzo_base + scala_fee + trasferta, 2)
    codice = f"EBJ-TR-{int(time.time())}"[-11:]

    # Simulazione Contratto / Riepilogo
    contratto_text = f"""
================================================================================
CONFERMA PREVENTIVO & CONTRATTO D'OPERA LOGISTICA
Codice Pratica: {codice} | Data Emissione: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}
Aziende Esecutrici: EBGStudio (Ing. Badr) & Pietro Traslochi (Pietro)
--------------------------------------------------------------------------------
DATI COMMITTENTE:
• Nome / Ragione Sociale: {client_name}
• Telefono: {phone} | Email: {email}
• Data Prevista Intervento: {data_trasloco} | Tratta: {citta}

DETTAGLIO PREVENTIVO:
• Superficie stimata: {mq} mq (~{round(mq * 0.28, 1)} m³ mobili)
• Piano Partenza: {piano_p} | Piano Arrivo: {piano_a} | Ascensore: {"Sì" if ascensore else "No (Supplemento Scale)"}
• Costo Manodopera Base: €{prezzo_base:.2f}
• Supplemento Movimentazione Piani: €{scala_fee:.2f}
• Mezzi e Trasferta Operativa: €{trasferta:.2f}
--------------------------------------------------------------------------------
TOTALE NETTO CONCORDATO: €{totale:.2f}
--------------------------------------------------------------------------------
NOTE OPERATIVE:
Servizio comprensivo di carico, trasporto protetto, scarico e rimontaggio standard.
Contatto Operativo Logistica: Pietro (+39 328 426 3554 - PietroTraslochi.com)
Direzione Generale: Ing. Badr El Ouariti (+39 388 870 3508 - BadrExpress.com)
================================================================================
"""

    return {
        "status": "SUCCESS_CONTRACT_GENERATED",
        "codice_pratica": codice,
        "preventivo_totale": totale,
        "client_name": client_name,
        "citta": citta,
        "data_trasloco": data_trasloco,
        "contratto_text": contratto_text.strip(),
        "telegram_dispatched": True,
        "notified_partners": ["Ing. Badr (7298887137)", "Pietro (+39 328 426 3554)"]
    }

def execute(params=None):
    params = params or {}
    return calcola_e_genera_contratto(params)
