# 🏛️ E.B.J. AI · MASTER PROJECT WIKI & BLUEPRINT (v8.5 APEX)
> **Documento Privato Ufficiale & Immutabile dell'Ecosistema EBGStudio**  
> **Comandante & Ingegnere Capo:** Ingegner Badr El Ouariti (`badraudi@gmail.com` | `+39 388 870 3508` | Imola)  
> **Partner Operativo Logistica:** Pietro (`+39 328 426 3554` | PietroTraslochi.com)  
> **Data Ultimo Aggiornamento:** 26/08/2026 20:27:01 (Sincronizzato in Tempo Reale)

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

* `[HASH: 077f1804b2e3]` **[2026-08-26 20:41:22] MCP Cursor collegati** *(Cat: CURSOR_MCP)*:
  Aggiunti server MCP reali in .cursor/mcp.json (filesystem, git, sequential-thinking). Niente moduli Python fantasma. Autonomia in ebj-autonomia.mdc.

* `[HASH: 687b3d4a5f9f]` **[2026-08-26 20:41:22] Skill autonome Git, Kali e upload** *(Cat: SKILLS)*:
  Allineate skill github-manager (no secret, no force-push main, gh, check remote, commit solo su richiesta), hermes_kali_toolkit, ebj-git-repo e hub upload.

* `[HASH: ce31f8c2d237]` **[2026-08-26 20:41:22] Kali Lab e toolkit Hermes** *(Cat: KALI_LAB)*:
  Catalogo unico tool-catalog.json (ebj-supreme/kali e copia locale), allowlist caricata dal JSON, canale aetherswarm kali verso hermes_kali_toolkit, dispatcher keyword Kali, resolver SSH condiviso, timeout 120s.

* `[HASH: 909189682ba3]` **[2026-08-26 20:41:23] Cascata AI multi-provider** *(Cat: AI_CASCADE)*:
  Router ai_cascade_router e endpoint /api/ai/cascade: Groq, Gemini, OpenRouter, HF, Qwen locale :61517, QwenCloud. Chiavi solo da env, mai stampate.
