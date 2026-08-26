"""
Intelligent Multi-Agent Dispatch Router & MCP Specialization Matrix
Smista automaticamente ogni richiesta all'agente specializzato più idoneo:
- 🧠 HERMES MASTER: Dialogo, Voce, Preventivi, Vision AI, Calendario, Memoria
- 🛡️ HERMES KALI: Sicurezza, Audit di Rete, Scansioni Nmap, Comandi Linux
- 🤖 AGENTE ZERO: Esecuzione Script complessi, Code Dev, PLC Siemens, CNC
- 🕷️ OPENCLAW / CRAWL4AI: Web Scraping massivo su RAM-Disk, Aste, Subito, Autolavaggi
- 🔄 N8N ORCHESTRATOR: Flussi visivi, Webhook, Notifiche Telegram, Google Sheets
"""
import os
import json
import time

AGENT_SPECIALIZATION_MATRIX = {
    "HERMES_MASTER": {
        "role": "Direttore Cognitivo, Dialogo Vocale, Vision AI & Preventivi",
        "description": "Interazione naturale con Ingegner Badr, calcolo volumetria mobili, sintesi vocale e memoria LTM.",
        "assigned_mcp_skills": [
            "mcp-gemini-vision-pro", "mcp-google-maps", "mcp-openrouteservice",
            "mcp-whatsapp-baileys-bot", "mcp-elevenlabs-voice-synth", "mcp-sqlite-wal-fts5",
            "mcp-google-calendar-sync", "mcp-smtp-mailer"
        ]
    },
    "HERMES_KALI": {
        "role": "Braccio Operativo Sicurezza, Diagnostica di Rete & Linux Native",
        "description": "Esecuzione tool a basso livello nel container Docker kalilinux/kali-custom:apex, audit sicurezza e monitoraggio porte.",
        "assigned_mcp_skills": [
            "hermes_kali_toolkit",
            "mcp-nmap-scanner", "mcp-whois-dns-prober", "mcp-fail2ban-manager",
            "mcp-ssl-cert-auditor", "mcp-wireguard-mesh", "mcp-linux-system-stats",
            "mcp-journald-log-analyzer"
        ]
    },
    "AGENTE_ZERO": {
        "role": "Autonomic Sandbox Worker, Code Dev, PLC Siemens & CNC",
        "description": "Esecuzione script autonomi, validazione codice C++ UE5.8, bridge PLC Siemens S7-1200 e percorsi utensile CNC.",
        "assigned_mcp_skills": [
            "mcp-snap7-siemens-plc", "mcp-gcode-cnc-validator", "mcp-cplusplus-clang-format",
            "mcp-unreal-remote-control", "mcp-blender-python-bridge", "mcp-docker-compose-manager"
        ]
    },
    "OPENCLAW_CRAWL4AI": {
        "role": "Massive Web Scraping & Data Mining su RAM-Disk",
        "description": "Estrazione annunci da Subito/Bakeca, monitoraggio aste giudiziarie e censimento autolavaggi su 2GB tmpfs a 50.000 MB/s.",
        "assigned_mcp_skills": [
            "mcp-crawl4ai", "mcp-real-estate-auctions-spider", "mcp-osm-places-scraper",
            "mcp-subito-bakeca-crawler", "mcp-brightdata-proxy-pool", "mcp-captcha-solver-bridge",
            "mcp-pdf-docling-extractor"
        ]
    },
    "N8N_ORCHESTRATOR": {
        "role": "Visual Workflow Bus & Event Dispatcher",
        "description": "Schedulazione temporale, webhook esterni, broadcast Telegram e aggiornamento fogli condivisi.",
        "assigned_mcp_skills": [
            "mcp-n8n-dag-orchestrator", "mcp-telegram-bot-api", "mcp-google-sheets-live",
            "mcp-redis-pubsub-bus", "mcp-cron-job-scheduler"
        ]
    }
}

def route_task_to_agent(task_prompt=""):
    t0 = time.time()
    p_low = task_prompt.lower().strip()
    
    # 1. Check KALI keywords (toolkit allowlist + audit rete)
    kali_kw = [
        "/kali", "scansiona", "nmap", "porte", "sicurezza", "vulnerab",
        "dns", "ssl", "certificato", "fail2ban", "linux comando",
        "hydra", "aircrack", "john", "hashcat", "gobuster", "nikto",
        "sqlmap", "wifite", "ffuf", "masscan", "dirb", "wfuzz",
        "whatweb", "wpscan", "tcpdump", "tshark", "kali lab",
    ]
    if any(k in p_low for k in kali_kw):
        assigned_agent = "HERMES_KALI"
        reason = "Task di sicurezza, audit di rete o tool Kali allowlist (hermes_kali_toolkit)."
    
    # 2. Check SCRAPING & OPENCLAW keywords
    elif any(k in p_low for k in ["scrappa", "estrai", "subito", "bakeca", "aste", "annunci", "autolavaggi d'italia", "crawl", "cerca annunci"]):
        assigned_agent = "OPENCLAW_CRAWL4AI"
        reason = "Task di data mining, web scraping intensivo o monitoraggio aste su RAM-Disk."
        
    # 3. Check AGENTE ZERO & INDUSTRIAL keywords
    elif any(k in p_low for k in ["plc", "siemens", "s7-1200", "cnc", "gcode", "g-code", "unreal", "ue5", "blender", "compila c++", "script python"]):
        assigned_agent = "AGENTE_ZERO"
        reason = "Task di sviluppo codice, automazione industriale PLC/CNC o rendering 3D."
        
    # 4. Check N8N keywords
    elif any(k in p_low for k in ["flusso", "workflow", "cron notturno", "schedula", "foglio excel", "google sheets", "bot telegram"]):
        assigned_agent = "N8N_ORCHESTRATOR"
        reason = "Task di orchestrazione visiva, trigger temporizzato o automazione multi-canale."
        
    # 5. Default -> HERMES MASTER (Regia Cognitiva)
    else:
        assigned_agent = "HERMES_MASTER"
        reason = "Task di dialogo naturale, calcolo preventivo, vision AI o strategia generale."
        
    agent_info = AGENT_SPECIALIZATION_MATRIX.get(assigned_agent, {})
    
    return {
        "status": "SUCCESS",
        "task_prompt": task_prompt,
        "assigned_agent": assigned_agent,
        "agent_role": agent_info.get("role"),
        "routing_reason": reason,
        "available_mcp_tools": agent_info.get("assigned_mcp_skills", []),
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

def execute(params=None):
    params = params or {}
    action = params.get("action", "route")
    if action == "matrix":
        return {
            "status": "SUCCESS",
            "matrix": AGENT_SPECIALIZATION_MATRIX
        }
    prompt = params.get("prompt") or params.get("task") or ""
    return route_task_to_agent(prompt)
