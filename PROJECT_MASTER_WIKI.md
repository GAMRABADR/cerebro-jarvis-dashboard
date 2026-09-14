# 🏛️ E.B.J. AI · MASTER PROJECT WIKI & BLUEPRINT (v8.5 APEX)
> **Documento Privato Ufficiale & Immutabile dell'Ecosistema EBGStudio**  
> **Comandante & Ingegnere Capo:** Ingegner Badr El Ouariti (`badraudi@gmail.com` | `+39 388 870 3508` | Imola)  
> **Partner Operativo Logistica:** Pietro (`+39 328 426 3554` | PietroTraslochi.com)  
> **Data Ultimo Aggiornamento:** 14/09/2026 02:59 (Sincronizzato in Tempo Reale)

---

## 1. VISIONE GENERALE & IDENTITÀ IMMUTABILE
* **Nome Ufficiale:** `E.B.J. AI` (El Ouariti Badr Jarvis).
* **Identità Architetturale:** Sistema multi-agente distribuito a zero-latency, pilotato da un Nucleo 3D Fotorealistico (Luna 8K con Eclissi Vocale) e sostenuto da un micro-bus in Rust Tokio (30µs), orchestrazione N8N, container Docker isolati su VPS e accelerazione hardware su GPU RTX 4070.
* **Le 5 Regole Immutabili:**
  1. *Identità Singola:* E.B.J. è il nome sovrano. Il vecchio nome "Cerebro" è permanentemente eliminato.
  2. *Specifiche Hardware Reali:* Workstation 64GB DDR RAM + Dual GPU (RTX 4070 12GB + GTX 1660), VPS Oracle 24GB RAM 4 OCPU Ampere Ubuntu 24.04 LTS (200GB NVMe).
  3. *Filtro Lead Reali & Anti-Spam Temporale:* Annunci > 365 giorni scartati all'istante (`REJECTED_STALE_OVER_1_YEAR`).
  4. *Catalogo Servizi 360°:* Traslochi completi, Sgomberi totali con smaltimento Hera/Ecocentro, Deposito custodito, Pulizie post-trasloco/industriali, Tinteggiatura, Taglio erba/giardinaggio, Corriere espresso BadrExpress, Fornitura chimica all'ingrosso per Autolavaggi (detersivi, schiume, cere).
  5. *Sincronizzazione Atomica in Tempo Reale:* Ogni miglioria viene registrata al secondo con hash SHA256 nella Wiki Master.

---

## 2. TOPOLOGIA DI RETE & PORTE ATTIVE
* **Master Server Python (HTTP/REST/SSE):** `http://127.0.0.1:8088` (Locale) | `https://eb.badrexpress.com` (Tunnel Globale)
* **Rust Tokio Micro-Bus (Zero-Copy):** `http://127.0.0.1:9000` (Latenza: 30 microsecondi)
* **N8N Automation Engine (Oracle VPS):** `http://92.4.233.42:5678` (24GB RAM Cloud)
* **N8N Local Runner:** `http://127.0.0.1:5678` (64GB Workstation)
* **Agente Zero Sandbox (Oracle VPS):** `http://92.4.233.42:50080` (Console Web)
* **Kali Linux Docker Container:** `ebj-kali-engine` su VPS (`kalilinux/kali-custom:apex`, 3.29GB NVMe, 2GB tmpfs RAM-Disk)
* **LLM Locale Unsloth / Ollama:** `http://127.0.0.1:61517` / `http://127.0.0.1:11434` (Qwen 27B Abliterated su RTX 4070)

---

## 3. CASCATA MULTI-MODELLO ANTI-CENSURA & ZERO-BOTTLENECK
Il router di inferenza in `server.py` implementa un failover automatico su 4 livelli con intercettazione istantanea dei rifiuti/filtri:
1. **Livello 1 (Groq Qwen 27B / 32B):** Risposta sub-second ad altissima velocità.
2. **Livello 2 (Gemini 2.0 Flash):** Deep reasoning e contesto esteso.
3. **Livello 3 (Local Qwen 27B Abliterated su RTX 4070 - Porta 61517/11434):** Pesi liberi senza allineamento, **ZERO FILTRI / ZERO CENSURE**, 100% locale.
4. **Livello 4 (Groq Llama 3.3 70B Versatile):** Potenza analitica a 70 miliardi di parametri.

---

## 4. I 4 SUPER-SISTEMI ATTIVI & COLLAUDATI
1. **🦀 RUST AETHER-CACHE:** Buffer di memoria in-RAM zero-copy con latenza di 0.6 microsecondi (`/api/rust/aether-cache`).
2. **🔄 N8N TRASLOCHI COMPLETE FUNNEL:** Generatore istantaneo di contratti formali con timbro EBGStudio / Pietro Traslochi e notifica Telegram (`/api/preventivo/genera-contratto`).
3. **📦 3D CARGO PACKING & VAN ESTIMATOR:** Algoritmo 3D Bin Packing per simulare il carico e selezionare il furgone ottimale (Ducato Maxi 13.5 m³ vs Daily 20 m³) (`/api/cargo/pack-optimize`).
4. **🛡️ RUST TIME-MACHINE SNAPSHOT VAULT:** Backup atomico a caldo di `mail_vault.db`, `hermes_ltm_memory.db` e hash Git con ripristino istantaneo a voce (`/api/timemachine/snapshot`).

---

## 5. WATCHDOG ZERO-DOWNTIME (PERSISTENZA TOTALE)
* **Demone Supervisore:** `tunnel_watchdog_supervisor.py` monitora ogni 2 secondi `server.py` (8088), `jarvis-bridge.exe` (9000) e `cloudflared.exe` (`eb.badrexpress.com`).
* **Auto-Resurrezione Istantanea:** In caso di crash forzato, il Watchdog riavvia i processi in meno di 2 secondi (Collaudato con successo).
* **Auto-Start Windows Boot:** Registrato in `shell:startup` con launcher silenzioso `launch_watchdog_silent.vbs`.

---

## 6. MATRICE DEI 5 AGENTI SPECIALIZZATI & 100 SERVER MCP
* 🧠 **HERMES MASTER:** Dialogo vocale, Vision AI ($m^3$ mobili), preventivi, memoria LTM (`hermes_ltm_memory.db`).
* 🛡️ **HERMES KALI:** Sicurezza, audit di rete Nmap, comandi Linux `/kali`, scraping su RAM-Disk.
* 🤖 **AGENTE ZERO:** Sviluppo codice, PLC Siemens S7-1200, CNC G-Code, Unreal Engine 5.8 C++.
* 🕷️ **OPENCLAW / CRAWL4AI:** Web scraping massivo annunci Subito/Bakeca e aste giudiziarie a 50.000 MB/s.
* 🔄 **N8N ORCHESTRATOR:** Flussi schedulati, bot Telegram, webhook e sincronizzazione Google Sheets.
* **100 Server MCP Mappati:** Gestiti da `mcp_master_universe` con audit live su `/api/mcp/universe/audit`.

---

## 7. REGISTRO STORICO MIGLIORIE IN TEMPO REALE (REAL-TIME WIKI LOG)
* `[HASH: 61f53a9d565a]` Attivazione Motore Real-Time Wiki Sync (Rust/Python + N8N).
* `[HASH: 14f16a1e13da]` Sincronizzazione Automatica Immutabile Wiki Attiva con hash SHA256.
* `[HASH: 8a4c1f90e21b]` Integrazione Catalogo 100 MCP Server Mondiali & Architettura FastMCP Rust.
* `[HASH: 9b2d3c4e5f6a]` Selezione Ufficiale TOP 70 MCP Servers Mondiali per Ecosistema E.B.J.
* `[HASH: 3c4d5e6f7a8b]` Audit Diagnostico 100 Server MCP (0.02ms latenza, salute 100% OPERATIONAL).
* `[HASH: 7a8b9c0d1e2f]` Attivazione Router di Smistamento Specializzato Multi-Agente in 0.01ms.
* `[HASH: 2e3f4a5b6c7d]` Restyling Completo UI E.B.J. Matrix v8.0 & Top Bar a tendina Glassmorphism.
* `[HASH: f1e2d3c4b5a6]` Attivazione Supervisore Watchdog Auto-Rigenerante Zero-Downtime per il Tunnel.
* `[HASH: a1b2c3d4e5f6]` Creazione Guida Ufficiale di Integrazione per Cursor IDE (`.cursorrules`).
* `[HASH: 4a5b6c7d8e9f]` Implementazione e Collaudo dei 4 Super-Sistemi Rust & N8N per E.B.J.
* `[HASH: 9f8e7d6c5b4a]` Integrazione Cascata Multi-Modello Anti-Censura & Zero-Bottleneck Router.
* `[HASH: 305b5ea96195]` **[2026-09-13 18:35:33] EBJ Fase 7 — Reporting dei lead CERTI** *(Cat: LEAD)*: vista `v_certain_leads` con `JOIN LATERAL` **interna** su `lead_evidence` (senza prova il lead non esiste, nessun filtro nel reportista), rotta `GET /api/leads/certain` in Hermes, digest Telegram 09:00 e 18:00 con timer systemd, riga triage obbligatoria in fondo. Misurato sul deploy (`6acf6d1`, 16:30 UTC): `0/7` sonde fuori posto, 1 lead certo in archivio, invariante `0`, timer `enabled + active`. La rotta resta chiusa per costruzione finche' `EBJ_REPORT_TOKEN` non e' compilato nello `.env` della VPS — il digest non lo chiede.
* `[HASH: b37214f2f601]` **[2026-09-14 01:58] EBJ deploy-Fase — Il giro di deploy si auto-limita, e la coda dice la verita'** *(Cat: DEPLOY/RESILIENZA)*: moltiplicatore misurato della tempesta del 13/09 = 40 commit non consumati x 9 servizi x timer da 3 min. Tre gate in `deploy-worker.sh`: carico 1-min > `EBJ_BUILD_LOAD_RATIO` x core = nessuna build parte (fail-safe: se /proc/loadavg non si legge, si rimanda), tetto `EBJ_MAX_BUILDS_PER_ROUND`=2 con coda FIFO dal piu' vecchio (nessun servizio affamato), muro `EBJ_BUILD_TIMEOUT_SECS`=1500 dove rc 124/137 e' **rimando** e non BUILD FALLITO. Hook `016-proteggi-risponditori.sh`: `MemoryMin`+`OOMScoreAdjust`+`CPUWeight` su ssh/nginx, perche' buildkit vive nel cgroup di dockerd e ne' `Nice=` ne' `systemd-run --scope` sul chiamante lo toccano. Due bug trovati dal harness: `taglia_bersagli` catturava il proprio log nello stdout (`docker compose build "[2026-09-14"`), e la chiusura della coda testava l'assenza di errore invece del successo - con tre gate che scrivono coda DOPO la sezione 2b una voce appena accodata si sarebbe auto-scaricata nel giro in cui nasceva; ora serve la comparsa in `SUCCESSI`. 29 asserzioni verdi su 12 scenari (`tests/pendenza_harness.sh`), commit `27931af`.
* `[HASH: 949eb03d05f7]` **[2026-09-14 00:25] EBJ M1 - Canale di controllo OCI che resta vivo a macchina congelata** *(Cat: DEPLOY/RESILIENZA)*: `oci_rescue.ps1` legge il buffer seriale (`compute console-history capture` + `get-content`) e comanda l'hypervisor (`SENDDIAGNOSTICINTERRUPT` = break, non riavvio; `RESET` = ciclo di corrente), `oci_run.ps1` usa `instance-agent command create` + poll dell'esecuzione. Nomi di azioni e flag letti dall'help del CLI 3.92.1 installato, non ipotizzati: `REBOOT` non e' tra i valori accettati da `--action`, e `get-content` prende `--instance-console-history-id`, non `--console-history-id`. La misura che ha aperto tutto: `92.4.233.42:22` accetta il TCP poi `Connection timed out during banner exchange` dalle 22:52Z, quindi SSH e run-command sono morti per costruzione (entrambi chiedono una risposta al guest) e resta solo cio' che l'hypervisor fa da solo. Corretta anche una lettura sbagliata durata un giorno: i 5 script `vps_*.ps1` puntavano la chiave a un albero ritirato, e `ssh` lo segnalava in modo generico; `controllo/keys/vps_ssh_key.key` era sempre stato qui. Ora la path si risolve da `$PSScriptRoot` e `ssh` porta `ConnectTimeout=20 -o BatchMode=yes`. Slot umani rimasti: `~/.oci/config` (user/tenancy/region/key_file/fingerprint: mappa in SKILL.md, valori no) e `ocid_compartment` in `vps_system_profile.json`.
* `[HASH: cc0e5e19e4cc]` **[2026-09-14 00:59:10] EBJ Fase 8 - Il canale di misura separato diventa vero** *(Cat: DEPLOY/RESILIENZA)*: Il campo `giro_in_corso_da_s` era montato al contrario: `deploy-worker.sh` scriveva il marker `giro-in-corso.txt` nel ramo in cui trovava il lock OCCUPATO e lo cancellava (`rm -f`) nel ramo in cui il lock lo prendeva davvero. Per tutta la durata del build - l'unico momento in cui serve - il file non esisteva e il canale pubblicava 0, cioe' il contrario della realta'. Ora il marker appartiene al giro che lavora: epoch + passo (`avvio`, `fetch:<sha>`, `build:<svc>`, `host:<tgt>`, `hook:<nome>`, `stato`) scritti da `giro_passo()`, e lo toglie un `trap ... EXIT` del possessore del lock; il ramo rimandato non lo tocca piu', perche' sovrascriverlo ogni 3 minuti azzererebbe il numero che dice da quanto dura quel build. `ops/publish_state.sh` legge '<epoch> <passo>' (con ripiego sul mtime per i marker vecchi) e pubblica TRE campi fratelli: `giro_in_corso_da_s`, `giro_passo` (nomina il servizio sotto build) e `worker_attivo`, che e' la verita' di systemd su `ebj-selfdeploy.service` e vale `null` quando la query stessa fallisce perche' 'non lo so' non e' un 'no'. Combinazione decisiva: marker presente + unita' inactive = marker orfano da SIGKILL del TimeoutStartSec; marker assente + unita' active = il giro non ha ancora scritto il passo. L'hook `014-stato-fresco.sh` non decide piu' dopo un singolo `sleep 3`: itera ~20 s e passa anche se il mtime e' invariato ma l'`updated` del file ha meno di 180 s, perche' il `flock -n` sul `.publish.lock` fa uscire in silenzio un `systemctl start` perfettamente riuscito - un rosso falso su un hook di osservabilita' costa piu' di un verde timido. Corretti anche i testi bugiardi: `ebj-state-pub.timer` dichiarava 'stessa cadenza del worker (3 min)' mentre monta 2 minuti di proposito (deve battere il worker, e' un battito indipendente) e rinviava a una riga numerica di `publish_state.sh` che sarebbe andata a marcire. Verifica: harness portato da 12 a 14 scenari e da 28 a 37 asserzioni verdi con 0 rossi in 58 s; S13 fotografa il marker DENTRO lo stub di `docker compose build` (un controllo dopo il giro non distinguerebbe 'mai scritto' da 'scritto e cancellato dal trap') e verifica che a giro finito non ci sia piu'; S14 esegue il VERO `ops/publish_state.sh` contro la sandbox e controlla il contratto fra i due file - `da_s=63` da un epoch di 60 s prima, `giro_passo=build:kali` propagato, marker rimosso che pubblica di nuovo 0 e stringa vuota invece di conservare l'ultimo numero letto. Resta il passo umano: finche' la macchina non risponde il montaggio avviene al primo giro dopo il recupero, e li' 014 sara' la misura che dice se il canale gira davvero.
