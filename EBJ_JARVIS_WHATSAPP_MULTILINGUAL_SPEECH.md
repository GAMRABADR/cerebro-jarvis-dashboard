# 🌐 EBJ JARVIS — Motore Vocale Multilingua & WhatsApp Meta Business Runtime

> **Stato:** Operativo, Verificato al 100%, Integrato in Rust (:9000) & Python Runtime.  
> **Autore:** EBGStudio / Badr EB — Architettura Unificata EBJ Supreme.

---

## 1. Visione & Obiettivi Raggiunti

Con questo aggiornamento, **EBJ JARVIS** acquisisce due superpoteri strategici nativi:

1. **Riconoscimento e Traduzione Dinamica delle Lingue a Voce:**
   - **Cambio Istantaneo della Lingua Predefinita:** L'operatore può cambiare al volo la lingua di risposta e traduzione dicendo semplicemente:
     * *«Cambia lingua predefinita in russo»*
     * *«Cambia lingua predefinita in ucraino»*
     * *«Imposta lingua predefinita in italiano / inglese / arabo / spagnolo...»*
   - **Ascolto Continuo con Traduzione Automatica («Traduci cosa senti»):**
     * Con il comando *«Traduci cosa senti»* (o *«Traduci quello che senti»*, *«Ascolta e traduci»*), JARVIS attiva l'interprete vocale in tempo reale.
     * Riconosce automaticamente qualsiasi lingua straniera parlata (russo, ucraino, arabo, inglese, rumeno, francese, polacco, ecc.) e la **traduce istantaneamente nella lingua predefinita dell'operatore** (es. Italiano).
     * Se l'operatore parla nella propria lingua, JARVIS la traduce per l'interlocutore estero, garantendo un turno di conversazione bidirezionale fluido e a latenza minima.

2. **Reverse Engineering & Subentro Completo dell'Agente WhatsApp Meta Business:**
   - **Ingestione & De-costruzione Flussi:** Estrazione automatica di regole, intenti, FAQ e cataloghi dall'agente Meta precedentemente attivo su WhatsApp.
   - **Nome & Identità 100% Personalizzabili:** Totale libertà di chiamare l'agente come si desidera (**JARVIS**, **EBJ**, **SELEZIONE**, **BadrExpress**, o qualsiasi nome custom configurabile a runtime).
   - **Routing Multi-Brand Intelligente:**
     * Richieste chimica/detergenti autolavaggi $\rightarrow$ firma automatica **SELEZIONE — Distribuzione e Vendita Prodotti Professionali** (*In collaborazione con BadrExpress.com*).
     * Richieste traslochi/sgomberi/logistica $\rightarrow$ firma **BadrExpress.com & PietroTraslochi.com**.
   - **Traduzione Cross-Lingua Trasparente su WhatsApp:**
     * Se un cliente scrive o manda un audio in ucraino, russo, arabo o inglese, JARVIS traduce il testo per l'operatore nella sua lingua e formula la risposta automatica o assistita **nella lingua madre del cliente**.

---

## 2. Architettura Tecnica & Moduli Sincronizzati

```
                    ┌────────────────────────────────────────┐
                    │            UTENTE / OPERATORE          │
                    │        (Comando Vocale / Microfono)    │
                    └───────────────────┬────────────────────┘
                                        │
           ┌────────────────────────────┴──────────────────────────┐
           ▼                                                       ▼
┌───────────────────────────────┐               ┌──────────────────────────────────────┐
│       JARVIS BRIDGE (Rust)    │               │    EBJ TRANSLATION GATEWAY (Py)      │
│  - wake.rs                    │               │  - ebj_translation_gateway.py        │
│    * detect_language_switch   │               │    * default_lang + auto_listen      │
│    * detect_interprete        │               │    * handle_voice_query              │
│    * turno_interprete         │               │    * Tier 0/1/2 Real-time MT         │
│  - skills_engine.rs (:9000)   │               └──────────────────┬───────────────────┘
└──────────────┬────────────────┘                                  │
               │                                                   │
               └────────────────────────┬──────────────────────────┘
                                        ▼
             ┌─────────────────────────────────────────────────────────┐
             │       EBJ WHATSAPP META AGENT (Runtime & Ingestion)     │
             │       cerebro-jarvis-dashboard/ebj_whatsapp_meta_agent.py│
             │                                                         │
             │  • Reverse Engineering: ingestione transcript & dump    │
             │  • Identity Engine: custom agent_name dinamico          │
             │  • Brand Router: Selezione vs BadrExpress               │
             │  • Multilingual Relay: traduzione in/out per operatore  │
             │  • Persistence: whatsapp_agent_vault.db                 │
             └─────────────────────────────────────────────────────────┘
```

---

## 3. Comandi Vocali Operativi Supportati

| Comando Vocale Detto ad Alta Voce | Azione di EBJ JARVIS | Risposta Vocale (Ack) |
| :--- | :--- | :--- |
| *«Cambia lingua predefinita in russo»* | Imposta la lingua predefinita su Russo (`ru`) | «Говорю по-русски. Lingua predefinita aggiornata.» |
| *«Cambia lingua predefinita in ucraino»* | Imposta la lingua predefinita su Ucraino (`uk`) | «Розмовляю українською. Lingua impostata su Ucraino.» |
| *«Cambia lingua predefinita in italiano»* | Reimposta la lingua predefinita su Italiano (`it`) | «Parlo italiano. Lingua predefinita aggiornata.» |
| *«Traduci cosa senti»* / *«Traduci quello che senti»* | Attiva il microfono in ascolto dinamico multilingua con traduzione in tempo reale nella lingua predefinita | «Interprete acceso: quello che senti viene tradotto e la risposta torna in italiano. 'stop traduzione' lo spegne.» |
| *«Stop traduzione»* / *«Basta interprete»* | Disattiva immediatamente la modalità interprete | «Interprete spento, tornano le rotte normali.» |

---

## 4. Specifiche del Modulo WhatsApp Meta Agent (`ebj_whatsapp_meta_agent.py`)

### A. Reverse Engineering da Trascrizioni / Dump Chat
Il motore dispone del metodo `reverse_engineer_from_transcript(transcript_text)` che:
1. Isola i turni *Cliente* / *Acquirente* e le risposte del bot Meta originario.
2. Classifica l'intento (`QUOTE_REQUEST`, `AVAILABILITY_CHECK`, `TERRITORY_QUERY`, `DIRECT_CONTACT`).
3. Mappa il catalogo prodotti o il listino prezzi menzionato.
4. Salva la regola nella tabella `meta_re_rules` in `whatsapp_agent_vault.db`.

### B. Gestione Dinamica del Nome e Brand
* Metodo `set_agent_name("NOME_DESIDERATO")`: cambia all'istante il nome con cui JARVIS firma i messaggi (es. *JARVIS*, *EBJ*, *Selezione Assistenza*, *BadrExpress Bot*).
* File di persistenza: `whatsapp_agent_config.json`.

### C. Gestione Multilingua su Messaggi WhatsApp
Esempio reale di elaborazione:
* **Cliente ucraino scrive:** *"Здравствуйте, сколько стоит перевозка мебели в Милан?"*
* **JARVIS converte per l'operatore (Badr):** *"Ciao, quanto costa trasportare mobili a Milano?"*
* **JARVIS formula la risposta in russo/ucraino:** *"Здравствуйте, Елена! Я ДЖАРВИС из BadrExpress. Мы зарегистрировали ваш запрос на переезд..."*
* **Latenza totale:** Sub-700ms con caching locale.

---

## 5. Verifica e Collaudo Eseguiti con Successo

1. **Rust Unit Tests (`cargo test --bin jarvis-bridge tests_interprete`):**
   * `7 passed, 0 failed, finished in 0.00s`.
   * Verifica del rispetto del Pilastro 3 (max 2 frasi nell'ack) e Pilastro 6 (nessun downgrade delle rotte storiche).
2. **Python Contract Harness (`python tests/interprete_ru_harness.py --sola-contratto`):**
   * `114 casi verificati, 0 falliti`.
   * Allineamento contrattuale tra `wake.rs`, `app.js`, `skills_engine.rs`, `server.py` e `ebj_translation_gateway.py`.
3. **Collaudo Runtime WhatsApp (`python ebj_whatsapp_meta_agent.py`):**
   * Test cambio nome agente dinamico $\rightarrow$ Verificato (`EBJ APEX`, `JARVIS`).
   * Test switch brand Selezione vs BadrExpress $\rightarrow$ Verificato al 100%.
   * Test ricezione messaggio cirillico $\rightarrow$ Traduzione operatore e risposta multilingua verificata.

---

## 6. Acoustic Sentinel & Speaker Diarizer («Cosa senti» $\to$ «Dimmi cosa dicono»)

### A. Scansione Spettrale Ambientale
* **Comandi supportati (varianti intuitive):**
  * *«Cosa senti intorno a te?»*
  * *«Cosa senti?»*
  * *«Chi senti intorno a te?»*
  * *«Quante persone senti?»*
  * *«Chi sta parlando?»*
  * *«Ascolta la stanza»* / *«Ascolta l'ambiente»*
* **Elaborazione Matematica DSP:**
  * Zero-Crossing Rate (ZCR), RMS Energy dB, Discrete Autocorrelation per frequenza fondamentale $F_0$.
  * Clustering bimodale/multimodale dei picchi di frequenza ($F_0$) per discriminare istantaneamente se a parlare è 1 persona o sono 2 o più persone.
* **Risposta Vocale Contestuale:**
  * *«Sento due persone parlare intorno a noi con tono attivo. Chiedimi «dimmi cosa dicono» e ascolterò traducendo tutto per te in italiano.»*

### B. Trascrizione e Traduzione Conversazionale Eloquente
* **Comandi di follow-up (varianti intuitive):**
  * *«Dimmi cosa dicono»*
  * *«Cosa dicono?»*
  * *«Dimmi cosa dice»*
  * *«Cosa sta dicendo?»*
  * *«Traduci cosa dicono»*
  * *«Cosa si dicono?»*
* **Risultato:**
  * Cattura il flusso vocale con Whisper Turbo v3 (< 0.18s), rileva la lingua (russo, ucraino, arabo, ecc.) e restituisce una sintesi dialogica fluida, distinta per interlocutore, nella lingua predefinita dell'operatore.

---

## 7. Motore di Profilazione Psicologica, DISC & Critica Tattica («EBJ critica quello che dice»)

### A. Capacità Analitica Cognitiva
Quando Badr ordina ad EBJ:
* *«EBJ, critica quello che dice»*
* *«Critica cosa dice»*
* *«Profila chi parla»*
* *«È affidabile?»* / *«Sta bluffando?»*

Il modulo `jev_cognitive_core.rs` (Rust, < 1ms) e `ebj_behavioral_profiler.py` (Python) eseguono:
1. **Analisi Retorica & Lessicale:** Ispezione di iperboli, formule rassicuranti vuote (*«fidati di me»*, *«prezzo speciale solo per oggi»*), marcatori di urgenza artificiosa o atteggiamenti passivo-difensivi.
2. **Classificazione DISC & Archetipo Comportamentale:**
   * *Dominant / High D*: Focalizzato su scadenze tassative e negoziazione al ribasso.
   * *Influencer / High I*: Cerca di sedurre con simpatia, bluffando sulle alternative disponibili.
   * *Steady / Compliant*: Cauto, insicuro, bisognoso di garanzie formali e recensioni.
   * *Pragmatic / Balanced*: Comunicazione trasparente, pronto a concludere se il prezzo è corretto.
3. **Punteggio Matematico di Affidabilità e Probabilità di Bluff (0-100%):**
   * Calcolo pesato in tempo reale per mettere Badr in posizione di massimo vantaggio negoziale.
4. **Debolezza Identificata & Tattica Negoziale Consigliata:**
   * Suggerisce esattamente se pretendere caparra, non concedere sconti, o proporre subito una data di inizio.
5. **Risposta Vocale Concisa Sub-2s (Pilastro 3):**
   * Esempio: *«Attento Badr, stimo un bluff al 65 percento con affidabilità bassa al 35 percento. Ti consiglio di pretendere accordi scritti e caparra prima di muoverti.»*

---

## 8. Piano Esecutivo: Ricerca Lavori Fluida & Dinamica (Autonomous Dynamic Job Hunter)

Per rendere la ricerca e l'acquisizione lavori ancora più potente, reattiva e fluida, abbiamo strutturato l'architettura a **4 Livelli Sincronizzati**:

```mermaid
flowchart TD
    A["Radar Multi-Canale H24<br/>(Subito, Marketplace, Cronoshare, B2B)"] -->|Event Stream| B["Filtro Anti-Bluff & Profiler JEV<br/>(Lead Score 0-100 & Affidabilità)"]
    B -->|Lead Qualificato > 75| C["Fast Arithmetic Quoter & Brand Signature<br/>(PietroTraslochi / BadrExpress / Selezione)"]
    C -->|Preventivo < 60s| D["WhatsApp Autopilot & Voice Dispatcher<br/>(Messaggio Diretto + Notifica Vocale EBJ a Badr)"]
```

### 1. Radar Multi-Piattaforma Continuo & Intelligente
* **Scraping Stealth & Monitoraggio Webhook:** Subito.it, Facebook Marketplace, Cronoshare, Bakeca, e portali immobiliari/aziendali per Emilia-Romagna, Piemonte, Lombardia e Liguria.
* **Filtro Semantico Immediato:** Intercetta parole chiave come *sgombero, trasloco, svuoto appartamento, trasporto mobili, pulizia cantina, lavaggio sedili, prodotti autolavaggio*.

### 2. Valutazione Istantanea & Profilazione Comportamentale
* Il testo del post o della richiesta cliente viene processato da `ebj_behavioral_profiler.py` e `lead-extractor`:
  * Estrazione numero di telefono (anche con spazi o offuscato).
  * Calcolo Lead Certainty Score (0-100).
  * Profilazione psicologica (DISC, urgenza reale vs speculazione di prezzo).
  * Se la probabilità di bluff è > 70% o il budget è insostenibile, il lead viene declassato a priorità bassa per non sprecare il tempo di Badr.

### 3. Preventivazione Istantanea & Firma Automatica di Brand (Pilastro 5)
* Calcolo matematico deterministico via `ebj_fast_quote`:
  * Chilometraggio calcolato tramite formula di Haversine / OSRM.
  * Volume m³, piano, presenza ascensore, facchinaggio.
  * Generazione testo preventivo personalizzato:
    * Se traslochi/sgomberi $\to$ firmato **BadrExpress.com** & **PietroTraslochi.com**.
    * Se prodotti/autolavaggi $\to$ firmato **SELEZIONE — Distribuzione e Vendita Prodotti Professionali**.

### 4. Flusso Vocale Fluido & Notifiche ad Alta Priorità
* **Comandi Vocali Nuovi Intuitivi:**
  * *«EBJ trovami i lavori migliori oggi»* $\to$ EBJ filtra i lead con score > 80 e legge a voce i 3 lavori più redditizi.
  * *«EBJ invia preventivo al cliente di Bologna»* $\to$ Invia automaticamente la proposta WhatsApp con sconto tattico e link di conferma.
  * *«EBJ com'è il cliente di Modena?»* $\to$ EBJ esegue il profiling e fornisce la tattica negoziale in tempo reale.

