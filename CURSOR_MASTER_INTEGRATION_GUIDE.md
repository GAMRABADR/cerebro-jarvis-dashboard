# 🧠 CURSOR MASTER INTEGRATION & ECOSYSTEM ARCHITECTURE GUIDE
> **File Ufficiale di Istruzioni per Cursor IDE & Agentic Coding**  
> **Identità Agente:** `E.B.J. AI` (El Ouariti Badr Jarvis) · **Versione:** `v8.5 APEX`  
> **Proprietario & Comandante:** Ingegner Badr El Ouariti (`badraudi@gmail.com` | `+39 388 870 3508` | Imola)  
> **Partner Logistico:** Pietro (`+39 328 426 3554` | PietroTraslochi.com)

---

## ⚡ 1. REGOLE IMMUTABILI PER CURSOR (DA RISPETTARE SEMPRE)

1. **IDENTITÀ AGENTE:** L'agente si chiama esclusivamente **`E.B.J.`** (*El Ouariti Badr Jarvis*). Non reintrodurre mai il vecchio nome *Cerebro*.
2. **HARDWARE REALE (NON DEGRADARE MAI LE SPECIFICHE):**
   * **Workstation Locale (Imola):** **64 GB RAM DDR**, CPU 8 Core / 16 Thread, **Dual GPU: NVIDIA GeForce RTX 4070 (12GB VRAM) + GTX 1660**.
   * **Oracle Cloud VPS (`92.4.233.42`):** **24 GB RAM (Ampere A1 4 OCPU)**, Ubuntu 24.04 LTS, 200GB NVMe SSD.
3. **FILTRO LEAD REALI (ANTI-SPAM TEMPORALE):**
   * Tutti i lead/annunci con data più vecchia di **365 giorni** vengono scartati all'istante (`REJECTED_STALE_OVER_1_YEAR`).
4. **CATALOGO SERVIZI A 360°:**
   * Traslochi, Sgomberi con smaltimento autorizzato, Deposito custodito, Pulizie, Tinteggiatura, Giardinaggio, BadrExpress, Fornitura chimica B2B per Autolavaggi.
5. **AGGIORNAMENTO WIKI IN TEMPO REALE:**
   * Sincronizzare ogni modifica con `skills_vault.wiki_realtime_syncer.skill.sync_wiki_improvement`.

---

## 🌐 2. TOPOLOGIA DI RETE & PORTE ATTIVE

• Master Dashboard Server:    http://127.0.0.1:8088        (Python HTTP + REST API)
• Public Worldwide Tunnel:   https://eb.badrexpress.com   (Cloudflare Named Tunnel)
• Rust Tokio Event Bus:      http://127.0.0.1:9000        (Rust jarvis-bridge, 30µs)
• N8N Workflow Cloud (VPS):  http://92.4.233.42:5678      (Automazione & Webhook)
• Agente Zero Sandbox (VPS): http://92.4.233.42:50080     (Esecuzione script autonomi)
• Kali Linux Docker (VPS):   ebj-kali-engine              (Immagine: kali-custom:apex)
• LLM Locale Qwen 27B:       http://127.0.0.1:61517       (Unsloth GPU RTX 4070 Abliterated)

---

## 🔌 3. ENDPOINT REST DISPONIBILI PER CURSOR

• POST /api/chat                      ➔ Dialogo con E.B.J. con cascata anti-censura su 4 livelli
• POST /api/preventivo/calcola        ➔ Calcolo preventivi trasloco (€8/mq + piano + trasferta)
• POST /api/preventivo/genera-contratto ➔ Generazione contratto formale con timbro EBGStudio / Pietro
• POST /api/vision/stima-mobili       ➔ Stima volumetrica arredi (m³) da foto con Vision AI
• POST /api/cargo/pack-optimize       ➔ Algoritmo 3D Bin Packing (Ducato Maxi vs Daily 35q)
• POST /api/rust/aether-cache         ➔ Buffer in-RAM zero-copy Rust (0.6µs latenza)
• POST /api/timemachine/snapshot      ➔ Creazione snapshot atomico codice, SQLite WAL e Git
• POST /api/agents/dispatch           ➔ Smistamento compiti ai 5 agenti specializzati (0.01ms)
• POST /api/mcp/universe/audit        ➔ Diagnostica globale dei 100 Server MCP
• POST /api/wiki/sync-improvement     ➔ Registrazione atomica nuove feature con hash SHA256

---

## 🛠️ 4. COME UTILIZZARE ED ESTENDERE LE SKILL (skills_vault/)

Ogni skill in `skills_vault/<nome_skill>/` contiene:
1. `manifest.json` (metadati e schema I/O)
2. `skill.py` con entrypoint: `def execute(params): ...`

---

## 🛡️ 5. WATCHDOG ZERO-DOWNTIME & MULTI-MODEL CASCADING

• **Watchdog Daemon:** `tunnel_watchdog_supervisor.py` auto-resuscita `server.py`, `jarvis-bridge.exe` e `cloudflared.exe` in < 2s.
• **Cascata Anti-Censura:** Livello 1 (Groq Qwen 27B) ➔ Livello 2 (Gemini 2.0 Flash) ➔ Livello 3 (Local Qwen 27B Abliterated su RTX 4070 - 0 Filtri) ➔ Livello 4 (Groq Llama 3.3 70B).
