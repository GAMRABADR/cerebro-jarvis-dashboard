# -*- coding: utf-8 -*-
"""
setup_multi_city_leads_engine.py
Configura e popola il database unificato per il Lead Radar Multi-Città:
- BadrExpress & Pietro Traslochi (Traslochi, Sgomberi, Depositi, Smaltimento, Scale)
- Selezione Forniture (Autolavaggi & B2B)
- Tabella Blacklist & Regole di Auto-Apprendimento
- Tabella Service Switches per il controllo rapido dei microservizi
"""

import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mail_vault.db")

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Tabella Blacklist & Regole Auto-Apprendimento
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lead_blacklist_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_type TEXT NOT NULL, -- 'PHONE', 'NAME', 'KEYWORD', 'PATTERN'
        pattern TEXT NOT NULL UNIQUE,
        reason TEXT NOT NULL, -- 'NUMERO_INESISTENTE', 'LEAD_FALSO', 'SPAM'
        source_lead_id INTEGER,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        hit_count INTEGER DEFAULT 0
    );
    """)

    # 2. Tabella Switchboard Servizi (Toggle Rapido Rust / Python)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS service_switches (
        service_key TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        enabled INTEGER DEFAULT 1,
        last_run TEXT,
        details TEXT
    );
    """)

    default_services = [
        ("radar_traslochi", "Radar Traslochi Express Multi-Città", "TRASLOCHI", 1, "Attivo su 10 città italiane"),
        ("radar_sgomberi", "Radar Sgomberi & Cantine", "SGOMBERI", 1, "Scansione appartamenti, garage e solai"),
        ("radar_depositi", "Radar Depositi & Magazzini Mobili", "DEPOSITI", 1, "Intercettazione stoccaggio temporaneo"),
        ("radar_selezione", "Radar Selezione Autolavaggi B2B", "CHIMICA", 1, "Censimento impianti e detailing"),
        ("prayer_scheduler", "Scheduler Preghiere 5x/die (Salat)", "CRON", 1, "Aggiornamenti a Fajr, Dhuhr, Asr, Maghrib, Isha"),
        ("blacklist_learner", "Filtro Blacklist & Anti-Fake", "SECURITY", 1, "Auto-apprendimento numeri inesistenti e falsi"),
        ("telegram_dispatcher", "Notifiche Telegram H24", "NOTIFY", 1, "Alert immediati per lead ad alto valore")
    ]

    for s_key, s_name, s_cat, s_en, s_det in default_services:
        cur.execute("""
        INSERT INTO service_switches (service_key, name, category, enabled, details)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(service_key) DO UPDATE SET
            name = excluded.name,
            category = excluded.category,
            details = excluded.details;
        """, (s_key, s_name, s_cat, s_en, s_det))

    # 3. Assicura colonne necessarie su verified_leads_2026
    columns = [r[1] for r in cur.execute("PRAGMA table_info(verified_leads_2026)").fetchall()]
    needed_cols = [
        ("lead_status", "TEXT DEFAULT 'DA_CHIAMARE'"),
        ("call_outcome", "TEXT"),
        ("last_call_at", "TEXT"),
        ("blacklist_flag", "INTEGER DEFAULT 0"),
        ("failure_reason", "TEXT"),
        ("notes", "TEXT"),
        ("estimated_budget", "REAL DEFAULT 0.0"),
        ("service_type", "TEXT DEFAULT 'Trasloco Completo'")
    ]
    for col_name, col_def in needed_cols:
        if col_name not in columns:
            try:
                cur.execute(f"ALTER TABLE verified_leads_2026 ADD COLUMN {col_name} {col_def}")
                print(f"Colonna aggiunta a verified_leads_2026: {col_name}")
            except Exception as e:
                print(f"Colonna {col_name} gia presente o errore: {e}")

    # 4. Popolamento Lead Multi-Città per TRASLOCHI, SGOMBERI, DEPOSITI, SMALTIMENTO
    # Copertura completa: Bologna, Milano, Roma, Torino, Firenze, Modena, Cuneo, Verona, Napoli
    sample_leads = [
        # BOLOGNA
        ("Marco Ferri", "+393384920112", "Bologna", "Trasloco Completo", "75 mq", "3", "2", 1, 950.0, "Subito.it", "DA_CHIAMARE", "Bologna (Mazzini) ➔ Casalecchio. Cucina componibile da smontare e riadattare."),
        ("Studio Legale Vanzetti", "+393478819203", "Bologna", "Trasloco Ufficio", "140 mq", "1", "4", 1, 1600.0, "Facebook", "DA_CHIAMARE", "Bologna Centro Storico ➔ San Lazzaro. 18 scrivanie, armadi archivio blindati."),
        ("Famiglia Ghedini", "+393351940228", "Bologna", "Sgombero Cantina", "25 mq", "-1", "0", 0, 380.0, "Google Local", "DA_CHIAMARE", "Bologna (Zona Saragozza). Vecchi mobili, libri, scatoloni. Smaltimento urgente."),
        ("Elena Bonfiglioli", "+393405521948", "Bologna", "Deposito Mobili", "50 mq", "2", "0", 1, 550.0, "BadrExpress.com", "DA_CHIAMARE", "Custodia mobili per 3 mesi causa ristrutturazione casa. Ritiro con scala aerea."),
        
        # MILANO
        ("Arch. Matteo Moretti", "+393491209384", "Milano", "Trasloco Completo", "110 mq", "4", "3", 1, 1450.0, "Subito.it", "DA_CHIAMARE", "Milano (Porta Romana) ➔ Milano (CityLife). Arredi design e lampadari di pregio."),
        ("Lorenzo De Luca", "+393489912044", "Milano", "Sgombero Appartamento", "85 mq", "2", "0", 1, 750.0, "Facebook", "DA_CHIAMARE", "Milano (Lambrate). Sgombero totale appartamento ereditato. Ritiro rapido in settimana."),
        ("Digital Agency Hive", "+393394857102", "Milano", "Trasloco Ufficio", "200 mq", "5", "2", 1, 2200.0, "LinkedIn B2B", "DA_CHIAMARE", "Milano (Garibaldi) ➔ Tortona. 30 postazioni PC, sala riunioni, server rack."),
        ("Simona Cattaneo", "+393476291045", "Milano", "Deposito Mobili", "40 mq", "3", "0", 1, 480.0, "PietroTraslochi.com", "DA_CHIAMARE", "Richiede box privato custodito per 6 mesi. Partenza per lavoro all'estero."),
        ("Davide Pozzi", "+393338192033", "Milano", "Smaltimento & Recupero", "30 mq", "1", "0", 1, 420.0, "Subito.it", "DA_CHIAMARE", "Milano Nord. Smaltimento arredi vecchi ufficio e certificato formulario rifiuti."),

        # ROMA
        ("Dott. Valerio Mancini", "+393318940211", "Roma", "Trasloco Completo", "130 mq", "3", "1", 1, 1550.0, "BadrExpress.com", "DA_CHIAMARE", "Roma (Prati) ➔ Roma (Eur). Servizio chiavi in mano con imballaggio completo."),
        ("Fabrizio Colasanti", "+393427189033", "Roma", "Sgombero Solaio", "45 mq", "5", "0", 0, 520.0, "Facebook Marketplace", "DA_CHIAMARE", "Roma (Monteverde). Solaio piano alto senza ascensore. Necessaria scala aerea esterna."),
        ("Carla De Angelis", "+393386712940", "Roma", "Scala Aerea Noleggio", "60 mq", "6", "0", 0, 390.0, "Google Local", "DA_CHIAMARE", "Roma (Tiburtina). Noleggio autoscala con manovratore per salita divano e armadio."),
        ("Emanuele Rinaldi", "+393459981240", "Roma", "Deposito Mobili", "70 mq", "2", "0", 1, 680.0, "Subito.it", "DA_CHIAMARE", "Roma (San Giovanni). Deposito mobili per 4 mesi in attesa di rogito nuova casa."),

        # TORINO
        ("Ing. Roberto Gallo", "+393481239840", "Torino", "Trasloco Completo", "90 mq", "2", "4", 1, 1100.0, "Subito.it", "DA_CHIAMARE", "Torino (Crocetta) ➔ Torino (San Salvario). Trasloco con montaggio cucina e librerie."),
        ("Chiara Boero", "+393398471203", "Torino", "Sgombero Garage", "35 mq", "-1", "0", 0, 350.0, "Facebook", "DA_CHIAMARE", "Torino (Santa Rita). Garage pieno di scatoloni, ferro vecchio e pneumatici."),
        ("Logistica Piemonte SRL", "+393409182374", "Torino", "Trasloco Industriale", "300 mq", "0", "0", 1, 2800.0, "B2B Rete", "DA_CHIAMARE", "Torino Sud ➔ Moncalieri. Macchinari leggeri, scaffalature industriali pesanti."),

        # FIRENZE
        ("Prof. Andrea Nencini", "+393358891244", "Firenze", "Trasloco Completo", "80 mq", "3", "2", 0, 1250.0, "BadrExpress.com", "DA_CHIAMARE", "Firenze (Campo di Marte) ➔ Sesto Fiorentino. Accesso con scala esterna in ZTL."),
        ("Letizia Bardi", "+393471092834", "Firenze", "Sgombero Cantina", "20 mq", "-1", "0", 0, 320.0, "Subito.it", "DA_CHIAMARE", "Firenze (Rifredi). Cantina umida con vecchi faldoni e mobili in legno."),
        ("Toscana Antichità", "+393389471029", "Firenze", "Trasporto Mobili Pregio", "45 mq", "1", "1", 1, 650.0, "Passaparola", "DA_CHIAMARE", "Firenze ➔ Bologna. Trasporto delicato cassettoni intarsiati e specchiere d'epoca."),

        # MODENA & REGGIO EMILIA
        ("Massimo Barbieri", "+393394781290", "Modena", "Trasloco Completo", "100 mq", "2", "2", 1, 1050.0, "Facebook", "DA_CHIAMARE", "Modena (Buon Pastore) ➔ Carpi. Appartamento 4 locali, smontaggio armadio 6 ante."),
        ("Claudio Reggiani", "+393481029348", "Reggio Emilia", "Sgombero Capannone", "120 mq", "0", "0", 1, 1400.0, "B2B Locale", "DA_CHIAMARE", "Reggio Emilia (Mancasale). Sgombero scaffali metallici e bancali in legno."),
        ("Giulia Ferrari", "+393408891204", "Modena", "Deposito Mobili", "30 mq", "1", "0", 1, 400.0, "Google Local", "DA_CHIAMARE", "Modena Est. Deposito temporaneo 2 mesi in attesa di fine lavori imbiancatura."),

        # CUNEO & PROVINCIA
        ("Giacomo Olivero", "+393478912384", "Cuneo", "Trasloco Completo", "85 mq", "2", "3", 1, 980.0, "Subito.it", "DA_CHIAMARE", "Cuneo Centro ➔ Borgo San Dalmazzo. Alloggio al secondo piano con camera e sala."),
        ("Azienda Agricola Vaudano", "+393359981204", "Alba (Cuneo)", "Sgombero Magazzino", "150 mq", "0", "0", 1, 1100.0, "Passaparola", "DA_CHIAMARE", "Alba. Sgombero cantina vinicola e vecchie botti in legno dismesse."),
        ("Paolo Dutto", "+393401928374", "Bra (Cuneo)", "Trasloco Appartamento", "70 mq", "1", "2", 1, 850.0, "Facebook", "DA_CHIAMARE", "Bra ➔ Fossano. Mobili cucina ed elettrodomestici, scala aerea richiesta."),

        # VERONA & PADOVA
        ("Federico Zanetti", "+393498871203", "Verona", "Trasloco Completo", "105 mq", "3", "1", 1, 1200.0, "BadrExpress.com", "DA_CHIAMARE", "Verona (Borgo Trento) ➔ San Bonifacio. Mobili moderni, imballaggio stoviglie."),
        ("Studio Commerciale Maran", "+393381029384", "Padova", "Sgombero Ufficio", "90 mq", "2", "0", 1, 800.0, "Subito.it", "DA_CHIAMARE", "Padova Centro. Ritiro vecchi tavoli riunioni e 50 scatoloni faldoni da macero."),

        # NAPOLI
        ("Ciro Esposito", "+393381920491", "Napoli", "Trasloco Interregionale", "95 mq", "4", "2", 1, 1850.0, "Subito.it", "DA_CHIAMARE", "Napoli (Vomero) ➔ Bologna (Murri). Trasloco completo per trasferimento famiglia."),
        ("Vincenzo De Rosa", "+393479981203", "Napoli", "Sgombero Locale", "60 mq", "0", "0", 1, 600.0, "Facebook", "DA_CHIAMARE", "Napoli (Fuorigrotta). Sgombero ex negozio abbigliamento, arredi e bancone.")
    ]

    inserted_count = 0
    for name, phone, city, service, vol, p_part, p_arr, asc, bud, src, st, nts in sample_leads:
        clean_p = phone.replace(" ", "").replace("-", "")
        # Verifica se già presente
        existing = cur.execute("SELECT id FROM verified_leads_2026 WHERE phone = ? OR (client_name = ? AND city = ?)", (clean_p, name, city)).fetchone()
        if not existing:
            cur.execute("""
            INSERT INTO verified_leads_2026 (
                client_name, phone, city, service_type, volume_mq,
                piano_partenza, piano_arrivo, ascensore, estimated_budget,
                source, verified_status, notes, lead_status, scraped_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (name, clean_p, city, service, vol, p_part, p_arr, asc, bud, src, st, nts, st))
            inserted_count += 1

    conn.commit()
    conn.close()
    print(f"Setup completato con successo! Lead inseriti/aggiornati: {inserted_count}")

if __name__ == "__main__":
    setup_db()
