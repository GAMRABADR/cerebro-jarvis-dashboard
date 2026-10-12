# 🛡️ MANUALE OPERATIVO COMPLETO: GLI 8 AGENTI AUTONOMI DI E.B.J. SUPREME

> **Documento Ufficiale Architetturale & Registro Abilità per Badr**  
> *Sistemi Certificati: EBJ Supreme · JEV Core · Agente Zero · Hermes Kali · FastMCP Universe*

---

## 🏛️ ARCHITETTURA UNIFICATA (Zero-Prompt & Full Autonomy)
L'ecosistema opera secondo la filosofia **"L'Agente Giusto per la Cosa Giusta"**, ispirato dalle dimostrazioni sul campo di Riccardo Zanetti (15 tool multi-step), Jirka Herník (VPS 24/7) e zSecurity (AI Hacker Showdown - Vittoria di Agent Zero). Badr interagisce con un'unica voce e un'unica plancia (**EBJ**), mentre gli 8 agenti autonomi si scambiano task e ricevute hardware in tempo reale.

```
                    ┌───────────────────────────────┐
                    │     E.B.J. SUPREME MASTER     │
                    │   (Badr El Ouariti Cockpit)   │
                    └───────────────┬───────────────┘
                                    │
    ┌──────────────┬────────────────┼────────────────┬──────────────┐
    ▼              ▼                ▼                ▼              ▼
[HERMES]      [AGENTE 0]       [OPENCLAW]       [B2B PITCHER]   [CLAUDE CODE]
Recon/Audio   Root Takeover    Web Scraping     Preventivi/PDF  Git/C++ Dev
    ▲              ▲                ▲                ▲              ▲
    └──────────────┴────────────────┼────────────────┴──────────────┘
                                    ▼
                      [SENTINEL · JEV · POSTIZ]
                      Self-Healing & Social Radar
```

---

## 🤖 IGLI 8 AGENTI AUTONOMI E LE LORO CAPACITÀ

### 1. 🤖 HERMES AGENT (Task Master & Cognitive Director)
* **Ruolo**: Direttore cognitivo, dialogo vocale neurale, vision multimodale e perizia volumetrica.
* **Runtime**: Docker `ebj-hermes` (VPS 24GB) + Tokio Rust Bridge (latenza 30µs).
* **Tool & MCP assegnati**:
  - `mcp-gemini-vision-pro`: Analisi fotogrammi 1080p e stima visiva arredi.
  - `mcp-google-maps` & `mcp-openrouteservice`: Calcolo tragitti, pedaggi e tempi di percorrenza.
  - `mcp-elevenlabs-voice-synth` & `edge-tts`: Voce neurale italiana `it-IT-DiegoNeural` (+12%).
  - `mcp-sqlite-wal-fts5`: Memoria a lungo termine illimitata (LTM).
* **Comandi Chiave**: Dialogo naturale, *"chi sei"*, *"cosa vedi"*, *"calcola preventivo"*.

---

### 2. ⚡ AGENTE ZERO (Apex Server Takeover, Sandbox & Exploit)
* **Ruolo**: Autonomia assoluta di sistema, penetration testing e automazione industriale. Vincitore assoluto dell'**AI Hacker Showdown (zSecurity)**.
* **Runtime**: Docker Container isolato + Python Zero-Shot Terminal Loop.
* **Tool & MCP assegnati**:
  - `mcp-hexstrike-ai`: Orchestratore di 150+ tool offensivi (Nmap, Gobuster, SQLmap, Nuclei).
  - Reverse shell & Privilege escalation: exploit di workflow n8n, upload bypass e ComfyUI.
  - `mcp-snap7-siemens-plc`: Comunicazione diretta con PLC Siemens S7-1200 / TIA Portal.
  - `mcp-gcode-cnc-validator`: Validazione percorsi utensile per centri di lavoro a controllo numerico (CNC).
  - `mcp-docker-compose-manager`: Controllo totale dei container senza interruzione.
* **Comandi Chiave**: `/new prendi controllo server`, `/kali <cmd>`, `audit HexStrike`.

---

### 3. 🕷️ OPENCLAW LEAD HUNTER (Massive Scraping & Radar Lead)
* **Ruolo**: Monitoraggio continuo H24 di portali annunci e de-offuscamento contatti.
* **Runtime**: Playwright Stealth Headless su RAM-Disk tmpfs (50.000 MB/s).
* **Tool & MCP assegnati**:
  - `mcp-crawl4ai`: Estrazione rapida annunci da Subito, Bakeca, Facebook Marketplace.
  - Rust SIMD `lead-extractor`: De-offuscamento numeri di telefono anche spaziati o mascherati (`3 4 8 . 9 8...`).
  - `mcp-real-estate-auctions-spider`: Monitoraggio aste immobiliari e fallimenti (PVP).
  - `mcp-captcha-solver-bridge`: Risoluzione automatica Turnstile e reCAPTCHA.
* **Comandi Chiave**: `/new trova annunci a Bologna`, `radar lead`, `sgomberi immobiliari`.

---

### 4. 💼 B2B PITCHER (SELEZIONE & SGOMBERI)
* **Ruolo**: Generazione dossier commerciali e contatto automatico con aziende e autolavaggi.
* **Runtime**: ReportLab PDF Engine + SMTP Gmail SSL nativo.
* **Tool & MCP assegnati**:
  - `mcp-osm-places-scraper`: Censimento e geolocalizzazione autolavaggi di tutta Italia.
  - `mcp-wholesale-pricing-engine`: Listini detergenti industriali firmati **SELEZIONE**.
  - `lead_pdf_report_generator`: Generazione automatica contratti e dossier PDF vettoriali.
* **Comandi Chiave**: `autolavaggi bologna`, `invia email dossier`, `genera contratto`.

---

### 5. 💻 CLAUDE CODE & APEX DEV (UE5.8 & 3D MCP PIPELINE)
* **Ruolo**: Sviluppo software autonomo, compilazione ad alte prestazioni, Unreal Engine 5.8 e modellazione 3D procedurale con Blender 5.2 (Architettura Stefan 3D AI MCP & Skills).
* **Runtime**: Claude 3.5/Opus + Cargo Release + Unreal Build Tool (UBT) + Blender 5.2 MCP Server.
* **Tool & MCP assegnati**:
  - `mcp-blender-skills-studio`: Bridge MCP per Blender 5.2 con libreria di Skills procedurali 3D (Cassa Munizioni Survivor, Barricata Tattica, Pannelli Sci-Fi, Porta Tamburata JEV, Medkit).
  - Nanite Auto-Topology & UCX Collision: Generazione automatica di collisioni UCX, Smart UV Project e materiali PBR calibrati in centimetri Z-up per `EBGS.uproject`.
  - `mcp-cplusplus-clang-format`: Linter e architettura C++ per `EBGS.uproject` (Unreal Engine 5.8).
  - `mcp-steamworks-api`: Automazione upload build SteamPipe (AppID `2886940`).
  - `mcp-rust-aether-kernel`: Compilazione e ottimizzazione micro-bridge Rust Tokio.
  - `git-multi-sync`: Commit e push atomici con zero-prompt pre-approvato.
* **Comandi Chiave**: `/new genera cassa 3d blender`, `/new correggi bug in server.py`, `compila rust`, `pusha su github`.

---

### 6. 🛡️ SENTINEL SELF-HEAL & BATTERY GUARD
* **Ruolo**: Sentinella di sistema, auto-riparazione tunnel, container Docker e risparmio energetico.
* **Runtime**: Python Watchdog Daemon su porta 9000 e supervisor background task.
* **Tool & MCP assegnati**:
  - `tunnel_watchdog_supervisor`: Monitoraggio Cloudflare Tunnel `eb.badrexpress.com` (autoriparazione Error 1033/530).
  - `telegram_rate_guard`: Silenziamento intelligente notifiche per non scaricare la batteria del telefono di Badr.
  - `mcp-fail2ban-manager`: Blocco tentativi brute-force SSH sulla VPS.
* **Comandi Chiave**: `stato server`, `silenzia notifiche`, `report vps`.

---

### 7. 💎 JEV PERIZIE & AUTO-POSTER
* **Ruolo**: Stima del valore dell'usato e pubblicazione automatica annunci Marketplace.
* **Runtime**: Playwright Stealth Session Persistente + JEV Multi-Tone Estimator.
* **Tool & MCP assegnati**:
  - Stima a rapporti fissi (5 condizioni per 3 toni) su porte, arredi ed elettrodomestici.
  - Pubblicazione autonoma con upload foto e coordinate territoriali (Bologna, Imola, Milano).
  - Generazione link WhatsApp pre-compilati per trattativa diretta.
* **Comandi Chiave**: `perizia porte`, `pubblica su facebook`, `stima valore mobile`.

---

### 8. 📡 POSTIZ SOCIAL RADAR
* **Ruolo**: Ascolto sociale, monitoraggio menzioni, gruppi Facebook e community Discord.
* **Runtime**: Discord Bot API (`778676826481754152`) + Social Webhook Gateway.
* **Tool & MCP assegnati**:
  - `mcp-slack-discord-webhooks`: Invio patch notes e annunci per la community gamer EBGS.
  - Intercettazione richieste di trasloco e sgombero nei gruppi Facebook pubblici.
* **Comandi Chiave**: `/new ascolta gruppi fb milano`, `invia annuncio su discord`.

---

## 🕹️ COMANDI DI CONTROLLO UNIVERSALI PER BADR

| Comando | Sintassi | Azione Svolta |
| :--- | :--- | :--- |
| **Nuovo Task** | `/new <istruzione>` | Resetta il contesto precedente e avvia il task autonomo con l'agente più adatto. |
| **Rotta al Volo** | `/steer <guida>` | Inietta una correzione immediata all'agente attivo senza fermare l'esecuzione. |
| **Coda Notturna** | `/queue <istruzione>` | Inserisce il compito nella Night Queue, che verrà elaborato mentre dormi. |
| **Stato Flotta** | `/employees` o `/team` | Mostra in tempo reale lo stato degli 8 agenti e dei compiti in lavorazione. |
| **Audit HexStrike** | `audit hexstrike [ip]` | Lancia la scansione di sicurezza automatica tramite il container Kali. |
| **Blender 3D MCP** | `genera 3d [prop/porta/cassa]` | Genera asset 3D procedurale in Blender 5.2 ed esporta FBX Nanite per Unreal Engine 5.8. |

---

*Documento salvato e memorizzato nel nucleo cognitivo permanente di EBJ Supreme.*
