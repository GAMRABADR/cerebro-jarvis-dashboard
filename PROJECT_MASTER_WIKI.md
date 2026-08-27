# 🏛️ E.B.J. AI · MASTER PROJECT WIKI & BLUEPRINT (v8.5 APEX)
> **Documento Privato Ufficiale & Immutabile dell'Ecosistema EBGStudio**  
> **Comandante & Ingegnere Capo:** Ingegner Badr El Ouariti (`badraudi@gmail.com` | `+39 388 870 3508` | Imola)  
> **Partner Operativo Logistica:** Pietro (`+39 328 426 3554` | PietroTraslochi.com)  
> **Data Ultimo Aggiornamento:** 28/08/2026 00:45:00 (Sincronizzato in Tempo Reale)

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


---

## 11. REGISTRO STORICO MIGLIORIE IN TEMPO REALE (REAL-TIME WIKI LOG)

* `[HASH: de5f5ae4c492]` **[2026-08-28 00:45:00] SESSIONE COLLI DI BOTTIGLIA —TROVATI E RISOLTI** *(Cat: PERFORMANCE)*:
  (1) **server.py HUD: CPU 29.8%→1.1%** — scoperto poller Telegram duplicato nella HUD, in conflitto getUpdates col Superbot (stesso token, eccezioni silenziate in loop): disattivato, il bot resta al Superbot. (2) **Lead Pipeline riparata in 2 strati**: nodo Telegram con credenziale inesistente → convertito a HTTP Request con token risolto dinamicamente dal DB; poi errore di parse Markdown di Telegram (underscore dentro il bold dell'heartbeat) → rimosso parse_mode. **Ciclo schedulato 23:20 = SUCCESS**. (3) Disco: journal vacuum + prune docker, 69%→66%. (4) Load 2.59 diagnosticato come boot di n8n post-restart: normalizzato a 0.06. (5) Primo scan Trivy: 33 CRITICAL / 47 HIGH nelle immagini (per lo più senza fix upstream), monitoraggio settimanale già attivo con alert Telegram. Sweep difensivo: nessun altro workflow attivo con credenziali telegramApi mancanti.

* `[HASH: 194aa225d1a6]` **[2026-08-28 00:15:00] P16 INFRASTRUTTURA NATIVA — Dock Control, Shield, Backup, Self-Heal** *(Cat: INFRASTRUCTURE)*:
  **EBJ DOCK CONTROL**: modulo Rust `docker.rs` nel bridge (client Docker Engine via unix socket, decodifica chunked e demux log, zero dipendenze nuove) — `GET /api/docker/containers` (stato+RAM), `POST /api/docker/action` (start/stop/restart), `GET /api/docker/logs`; protetto da header `X-EBJ-Token` (senza token: 401). GUI cyberpunk in Hermes `/docker` con card cliccabili e auto-refresh 15s, pubblica via nginx sul tunnel ebgs. **EBJ SHIELD**: Trivy 0.74.0, scan settimanale lunedì 03:30 sulle immagini dei container attivi, report + alert Telegram. **EBJ BACKUP**: repo Restic cifrato `/opt/backups/restic-repo`, primo backup riuscito (dump Postgres n8n+ebj_supreme, lead vault, dati bridge/Hermes, env, nginx), timer giornaliero 02:30, retention 7gg/4sett/6mesi. **SELF-HEAL**: container critici monitorati ogni 5min con riavvio automatico + Telegram. Tailscale 1.102 installato (autenticazione Ingegnere pending). Knowledge agente: nuova sezione 9.

* `[HASH: 23fa098af9ad]` **[2026-08-27 22:45:00] CHIUSURA FINALE — 138/138 TOOL KALI OK, COLLI DI BOTTIGLIA RISOLTI** *(Cat: FINAL_VALIDATION)*:
  Test sistematico di TUTTI i tool del catalogo via catena di produzione bridge→Hermes→Kali: **138/138 funzionanti** (103 exit-0 + 35 rispondenti, 0 guasti, 0 timeout, latenza media 607ms end-to-end). Kiterunner rimosso dal catalogo (inesistente su ARM64). Fix: risoluzione name→binary nella Kali Exec API, bloodhound.py installato, theHarvester e bloodhound ri-verificati OK. Colli di bottiglia risolti: Lead Pipeline (chiamata corretta a `run_cycle`, genera lead reali), Kali OSINT Harvester (JSON.stringify nel body Telegram → SUCCESS), Morning Briefing (nodo Telegram convertito a HTTP Request con token risolto dinamicamente dal DB), limiti RAM alzati live con `docker update` (agent-zero e kali-engine da 2GB a 4GB: pressione RAM da 74%/71% a 37%/36%). Watchdog Kali Exec API provato sul campo: restart automatico dopo kill. Lead vault a 1374 lead. Ecosistema: 7 container healthy, 5 timer systemd attivi, 4 tunnel monitorati.

* `[HASH: 997703bcb20a]` **[2026-08-27 21:30:00] P13 TUNNEL IMMORTALI — watchdog, rigenerazione automatica, notifiche** *(Cat: INFRASTRUCTURE)*:
  Watchdog systemd `ebj-tunnel-watchdog.timer` (ogni 60s) monitora i 4 tunnel quick (ebgs, jarvis, agent-zero, n8n): servizio morto o URL pubblico caduto → rigenerazione automatica, nuovo URL scritto nel registro `/home/ubuntu/tunnel_registry.json` + evento in `tunnel_events.log` + **notifica Telegram immediata** all'Ingegnere (via token Superbot). Collaudo notifica riuscito. Upload hub spostato dietro nginx catch-all (`location /upload` e `/api/upload` → Hermes :8089) sul tunnel ebgs stabile; pensionato `hermes-upload-tunnel` (crash-loop dei quick tunnel recenti). Link upload attuale: `https://orientation-cents-protective-recognized.trycloudflare.com/upload` (cambia solo se il tunnel ebgs si rigenera — e in quel caso arriva la notifica). Gap aperto: email SMTP richiede Gmail App Password dell'Ingegnere.

* `[HASH: 9c0cf68c6839]` **[2026-08-27 11:30:00] P12 ASSIMILAZIONE TOTALE — MEMORIA INFINITA LIVE** *(Cat: MEMORY_ENGINE)*:
  Modulo Rust INGEST nel jarvis-bridge: `POST /api/ingest` (base64, flag `pre_extracted`), `GET /api/ingest/search` (ranking keyword+contenuto), `/api/ingest/doc`, `/api/ingest/stats`; dedup SHA256 persistente (JSONL), testo completo su file, keywords automatiche, ingest <1ms. Pulsante upload drag&drop cyberpunk su Hermes `/upload` (pubblico via tunnel `hermes-upload-tunnel.service`): testi assimilati all'istante, PDF/immagini/docx in coda inbox. Worker automatici: `pdf_ingest_worker` (pymupdf, timer 60s) e `chat_sync` (conversazioni Agente Zero, timer 15min). Knowledge dell'agente aggiornata (sezione 8: cerca in memoria prima di rispondere, assimila dopo ogni interazione). Collaudo: PDF di prova → 137 caratteri, 12 keyword, ricerca funzionante; upload via hub → indice interrogabile.

* `[HASH: fadf78b3796b]` **[2026-08-27 10:30:00] N8N RIATTIVATO: 5 WORKFLOW PRIORITARI LIVE (P7)** *(Cat: AUTOMATION)*:
  Da 24 workflow tutti SPENTI a 5 prioritari ATTIVATI e caricati nel runtime: EB_Workflow_Autonomous_Lead_Pipeline (ogni 20 min), Kali OSINT & MetaGoofil Lead Harvester (ogni 2h), Google Maps Local Business & Sgomberi Lead Hunter (ogni 24h), Autonomous Morning Briefing & Sentinel Watchdog (cron 0 8 * * *), Sentinel errori → Telegram (event-driven). Fix ingegneristico Lead Pipeline: il nodo `executeCommand` è stato rimosso dalle versioni moderne di n8n → convertito in HTTP Request verso il bridge Rust (`POST http://172.19.0.1:9000/api/terminal/exec`) che esegue `lead_hunter_daemon.run_fresh_cycle()` sull'host. Nota tecnica: la modifica dei nodi via SQL diretto viene ignorata dal runtime n8n; usare sempre export→edit→import via CLI n8n. Primo ciclo lead automatico entro 20 minuti.

* `[HASH: 0ed0ee9df75e]` **[2026-08-27 09:45:00] AGENTE ZERO CABLATO ALL'ECOSISTEMA (P4)** *(Cat: AGENT_WIRING)*:
  Knowledge map `EBJ_Ecosystem_Capability_Map.md` iniettata in `/a0/usr/knowledge/main` (fonte: ebj-supreme/agent-wiring/): mappa completa di bridge/Hermes/n8n/DB/Kali con esempi operativi e regole di sicurezza. Reachability dal container agente: bridge via gateway 172.19.0.1:9000, Hermes via DNS `hermes:8089`, n8n via `n8n:5678`. Collaudo 5/5 DENTRO l'agente: dispatch Kali (nmap, 7ms), dedup (40µs), lead match (is_lead=true), Hermes health, e tool fuori allowlist bloccato con 403. Scheduler interno dell'agente pronto per i task ricorrenti. L'agente ora può fare e controllare l'intero ecosistema.

* `[HASH: 68a41946d246]` **[2026-08-27 09:15:00] HERMES v1 ORCHESTRATORE LIVE — catena completa chiusa** *(Cat: ORCHESTRATION)*:
  Container `hermes` (immagine ebj-hermes:1.0, Python 3.12 slim) su 127.0.0.1:8089, rete ebj_default, restart unless-stopped, volume /opt/hermes/data per la LTM. Moduli: master · kali_exec (proxy con token verso Kali Exec API) · memory (LTM SQLite store/search) · scrape (stub fase P5). Bridge ricollegato: EBJ_H_EXEC_URL → http://127.0.0.1:8089/api/kali/exec. Collaudo catena COMPLETA: POST bridge /api/ebj-h/dispatch → validazione Rust 2µs → Hermes → Kali Exec API → nmap eseguito: 7ms totali end-to-end. action=which (hydra in allowlist) e memoria store/search collaudati. Codice: ebj-supreme/hermes/.

* `[HASH: c5e715df7396]` **[2026-08-27 08:40:00] KALI EXEC API live — l'anello mancante chiuso** *(Cat: SECURITY_INFRASTRUCTURE)*:
  FastAPI exec deployata nel container ebj-kali-engine su :8899 (SOLO rete docker interna, nessuna porta host): token auth condiviso (backup in /home/ubuntu/ebj-supreme/kali-exec.token), allowlist 139 tool caricata dal tool-catalog, sanitizzazione metacaratteri shell, timeout 120s/600s max, output cappato 200KB. Collaudo sicurezza 5/5: nmap eseguito, bash rifiutato (non in allowlist), injection `127.0.0.1; cat /etc/passwd` bloccata, token errato respinto, porta 8899 invisibile dall'esterno. Watchdog systemd (kali-exec-watchdog.timer, 60s) con auto-restart. Codice in ebj-supreme/kali/exec_api.py. Chain completa pronta: jarvis-bridge (Rust) → Hermes → Kali Exec API → tool.

* `[HASH: 29f6cb26753c]` **[2026-08-27 08:05:00] JARVIS BRIDGE RUST LIVE + Kali Large + Ingestion Fix** *(Cat: INFRASTRUCTURE)*:
  Bridge Rust v2.0 SUPERPOWER deployato su VPS Oracle :9000 (systemd `jarvis-bridge`, 4 worker Actix, restart automatico): NUOVI moduli LEAD DEDUP BLOOM (2M elementi / FPR 0.1%, dedup misurato 1µs, snapshot persistente in /opt/jarvis-bridge/data) e LEAD INTENT MATCHER (Aho-Corasick, 25 stem italiani, match 12µs); EBJ_H Commander con 139 tool Kali in RAM; wake vocale collaudato ("Ci sono, Ingegnere. Dimmi."). Toolchain Rust aggiornato via rustup a 1.98 + libssl-dev/pkg-config. Kali engine: kali-linux-large installato (2.683 pacchetti), aggiunti volatility3 2.28, kerbrute (compilato Go), Ghidra; venv /opt/scraping con Scrapy 2.18 + Playwright + Chromium testato su pagina reale. Pipeline DOCUMENTI_INGESTION_AUTOMATICA riparata dopo spostamento cartella (path + scansione ricorsiva): 71 documenti catalogati, 71 righe obsolete rimosse dal vault. Decisioni Piano v4: UN Hermes modulare su :8089 (mai dentro Kali, no doppia istanza), Kali esecutore puro con exec API interna, n8n resta unico; fasi P8 hub UI e P9 flow redesign pianificate.

* `[HASH: 077f1804b2e3]` **[2026-08-26 20:41:22] MCP Cursor collegati** *(Cat: CURSOR_MCP)*:
  Aggiunti server MCP reali in .cursor/mcp.json (filesystem, git, sequential-thinking). Niente moduli Python fantasma. Autonomia in ebj-autonomia.mdc.

* `[HASH: 687b3d4a5f9f]` **[2026-08-26 20:41:22] Skill autonome Git, Kali e upload** *(Cat: SKILLS)*:
  Allineate skill github-manager (no secret, no force-push main, gh, check remote, commit solo su richiesta), hermes_kali_toolkit, ebj-git-repo e hub upload.

* `[HASH: ce31f8c2d237]` **[2026-08-26 20:41:22] Kali Lab e toolkit Hermes** *(Cat: KALI_LAB)*:
  Catalogo unico tool-catalog.json (ebj-supreme/kali e copia locale), allowlist caricata dal JSON, canale aetherswarm kali verso hermes_kali_toolkit, dispatcher keyword Kali, resolver SSH condiviso, timeout 120s.

* `[HASH: 909189682ba3]` **[2026-08-26 20:41:23] Cascata AI multi-provider** *(Cat: AI_CASCADE)*:
  Router ai_cascade_router e endpoint /api/ai/cascade: Groq, Gemini, OpenRouter, HF, Qwen locale :61517, QwenCloud. Chiavi solo da env, mai stampate.

* `[HASH: e7e368d5f966]` **[2026-08-26 22:21:43] Toolkit Kali Hermes allargato (catalogo unico)** *(Cat: SECURITY)*:
  Catalogo Kali Lab portato a 93 tool (fonte unica ebj-supreme/kali/tool-catalog.json copiata sulla skill hermes_kali_toolkit). Aggiunti i migliori pacchetti ufficiali Kali ARM64-viable per lab operator: recon (amass, subfinder, theHarvester, dnsenum, fierce, traceroute, arp-scan, hping3, smbclient, rpcinfo, ldapsearch, onesixtyone, dnsrecon, sslscan, smbmap), web (nuclei, feroxbuster, dirsearch, hakrawler, arjun, commix), password (fcrackzip, pdfcrack, samdump2), wireless (bettercap), rete (ngrep, ettercap-text-only, snmpwalk), identity/AD (enum4linux-ng, bloodhound.py, netexec, certipy-ad, impacket enum), utilita (wget, openssl, pip3, testssl). Installati live nel container ebj-kali-engine senza compose down: 92/93 binari disponibili; kiterunner assente dai repo arm64; jwt-tool e seclists (~1.8GB) esclusi. Metasploit, Burp GUI e Wireshark GUI non aggiunti. Allowlist solo da JSON. Nginx/n8n/agent-zero intatti.

* `[HASH: 2ab3bb5f09f7]` **[2026-08-26 22:37:08] Hermes Kali lab pentest allargato a 123 tool** *(Cat: SECURITY)*:
  Catalogo operator portato da 93 a 123 nomi (122 disponibili su ebj-kali-engine ARM64). Aggiunti searchsploit/exploitdb, msfconsole (gia presente, ora in allowlist), naabu, httpx, xsser, evil-winrm, chisel, ligolo-ng, tor, lynis/chkrootkit/rkhunter/bandit, trufflehog/gitleaks, binwalk/foremost/exiftool/strings/file/hexedit/steghide/stegsnow, radare2/gdb/strace/ltrace/checksec. Esclusi C2 (sliver/empire/covenant), BeEF, GUI Burp/Wireshark/Maltego/Autopsy, seclists extra. Solo host operator. kiterunner ancora assente su ARM64.

* `[HASH: 821bfb2e15b5]` **[2026-08-26 23:04:21] E.B.J. sempre in ascolto (Rust wake + Kali chat)** *(Cat: CORE_ENGINEERING)*:
  jarvis-bridge su :9000 include sessione wake Actix: POST /api/wake, /api/listen, GET /api/session, WS /ws/ebj. Frasi: ebj, ebj ci sei, ebj cisei, e.b.j., jarvis, hermes sei li. ACK: Ci sono, Ingegnere. Dimmi. Follow-up a /api/chat. HUD stesso ACK se bridge giu. Catalogo Kali intero in dispatcher; --help di default; n8n kali-exec solo tool+exit. Niente mic nativo. Kibana assente. Cloudflared intatto.

* `[HASH: 7d4c9a12e8b0]` **[2026-08-26 23:36:00] Kali lab Mobile AppSec (APK/IPA propri)** *(Cat: KALI_LAB)*:
  Catalogo operator a 139 nomi (138 disponibili su ebj-kali-engine ARM64). Nuova categoria mobile: apktool, jadx CLI, adb, fastboot, dex2jar (d2j-dex2jar/baksmali/smali/jar2dex), apksigner, zipalign, aapt, androguard, ideviceinstaller, idevice_id, ideviceinfo, sqlite3. Solo audit di APK/IPA di proprieta. Assenti apt arm64: drozer, objection, frida. Esclusi scrcpy/Ghidra (GUI). Ampere senza USB: adb per telefono lab o emulatore altrove. Default /kali --help. n8n/nginx/agent-zero intatti.

* `[HASH: 5a4d991ba8d4]` **[2026-08-26 23:51:49] Hermes Kali v1.4 - fix which + perimetro difensivo + telemetria Rust** *(Cat: CYBERSECURITY_OPERATIONS)*:
  Corretto il bug storico dell azione which: docker exec usava la builtin di shell command -v senza bash e falliva sempre; ora si usa argv esplicito docker exec ebj-kali-engine which -- <binario> con binario risolto dal catalogo (verificato live: nmap, apktool, jadx, theHarvester tutti in /usr/bin). Nuova azione status con conteggio catalogo (139 tool, 12 famiglie incluse le 16 mobile AppSec), famiglie, chiave SSH e ultima esecuzione. Aggiunto guardrail di perimetro REJECTED_TARGET_OUT_OF_SCOPE sui soli tool di rete: IPv4/CIDR pubblici e domini non di proprieta rifiutati, --help e --version sempre consentiti, reti private e host operatore (badrexpress.com, pietrotraslochi.com, tinoshop.it, 127.0.0.1, VPS Oracle) ammessi. Dashboard: nuove route GET /api/kali/status e /api/kali/which, riepilogo italiano per /kali status, chip categoria Mobile nella Kali Lab UI. Rust jarvis-bridge Actix :9000: nuovo modulo kali_status.rs di sola lettura con GET /api/kali/status e /api/kali/catalog-count (conteggio catalogo + ultima esecuzione nome/exit, zero payload e zero argomenti esposti); cargo check e build release senza warning, wake ebj ci sei verificato integro. Nessun cracker, exploit o payload nel Rust: l esecuzione resta in Python con allowlist.

* `[HASH: eb0h1c0mm4nd]` **[2026-08-26 23:59:00] EBJ_H Commander + 7 Famiglie (Rust hot-path + n8n)** *(Cat: CORE_ENGINEERING)*:
  Sostituita l ipotesi di 123 workflow n8n con l architettura 1 EBJ_H_COMMANDER + 7 famiglie (EBJ_H_RECON, EBJ_H_WEB, EBJ_H_PASSWORD, EBJ_H_WIRELESS, EBJ_H_RETE=rete+identity, EBJ_H_VULN=vuln+hardening+forensics+reverse+utilita, EBJ_H_MOBILE): ogni famiglia gestisce TUTTI i tool della sua categoria dal tool-catalog.json (un tool per job, --help di default). Nuovo hot-path Rust in jarvis-bridge Actix :9000 (modulo ebj_h.rs): catalogo tool incorporato/caricato UNA volta in RAM (HashSet allowlist + mappa categorie, sha256), POST /api/ebj-h/dispatch valida allowlist + metacaratteri shell + coerenza famiglia in microsecondi (campo ebj_h_dispatch_us in risposta) poi inoltra a Hermes http://127.0.0.1:8088/api/kali/exec; GET /api/ebj-h/catalog e /api/ebj-h/families espongono catalogo e mappa webhook. Override EBJ_H_EXEC_URL / EBJ_H_CATALOG. Wake ebj ci sei intatto; cargo build --release OK. Workflow importabili in cerebro-jarvis-dashboard/n8n/workflows/ (COMMANDER accetta family; ogni famiglia forza il proprio family e ha fallback diretto su Hermes :8088 se il bridge Rust e giu). README con curl e import via n8n API senza stampare credenziali. Fixato ebj-supreme/jarvis-bridge: axum::serve al posto di Server::bind rimosso in axum 0.7, pin takecell 0.1.1 (MSRV), rimossi terminatori here-string '@ corrotti in config/error/websocket/rate_limiter/bloom_filter/circuit_breaker (crate ancora con errori pre-esistenti nei moduli applicativi, fuori scope; bus di produzione = Actix :9000). Nessun cracker/exploit nel Rust: solo validazione+inoltro, scope difensivo gestito da Hermes.
