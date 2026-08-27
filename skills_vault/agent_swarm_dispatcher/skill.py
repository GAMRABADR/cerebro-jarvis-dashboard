"""
Intelligent Multi-Agent Dispatch Router & MCP Specialization Matrix
Hermes Kali usa l'intero catalogo tool-catalog.json (allowlist), non un sottoinsieme fisso.
"""
import os
import json
import time
import re

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
        "description": "Esecuzione tool allowlist nel container kali-custom:apex (catalogo Hermes Kali).",
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

_KALI_STATIC_KW = (
    "/kali", "kali lab", "scansiona", "sicurezza", "vulnerab",
    "fail2ban", "linux comando", "penetration", "pentest",
)


def _catalog_tool_names():
    names = set()
    here = os.path.dirname(os.path.abspath(__file__))
    paths = (
        os.path.join(here, "..", "hermes_kali_toolkit", "tool-catalog.json"),
        os.path.normpath(os.path.join(here, "..", "..", "..", "ebj-supreme", "kali", "tool-catalog.json")),
    )
    for p in paths:
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    for item in data:
                        for key in ("name", "binary"):
                            val = str(item.get(key) or "").strip().lower()
                            if val:
                                names.add(val)
                break
            except Exception:
                continue
    return names


def _looks_like_kali(prompt: str) -> bool:
    p_low = prompt.lower().strip()
    if any(k in p_low for k in _KALI_STATIC_KW):
        return True
    tools = _catalog_tool_names()
    if not tools:
        return False
    if re.search(r"(?:ebj|hermes|jarvis)\s+(?:lancia|esegui|run|avvia)\s+\S+", p_low):
        return True
    first = re.split(r"\s+", p_low, maxsplit=1)[0]
    first = first.lstrip("/")
    return first in tools


def _run_kali(prompt: str):
    try:
        from skills_vault.hermes_kali_toolkit.skill import execute as kali_exec, parse_user_kali, parse_kali_cli
    except ImportError:
        return None
    params = parse_user_kali(prompt) or parse_kali_cli(prompt)
    return kali_exec(params)


def route_task_to_agent(task_prompt=""):
    t0 = time.time()
    p_low = task_prompt.lower().strip()

    if _looks_like_kali(task_prompt):
        assigned_agent = "HERMES_KALI"
        reason = "Task Kali: catalogo allowlist completo (hermes_kali_toolkit)."
    elif any(k in p_low for k in ["scrappa", "estrai", "subito", "bakeca", "aste", "annunci", "autolavaggi d'italia", "crawl", "cerca annunci"]):
        assigned_agent = "OPENCLAW_CRAWL4AI"
        reason = "Task di data mining, web scraping intensivo o monitoraggio aste su RAM-Disk."
    elif any(k in p_low for k in ["plc", "siemens", "s7-1200", "cnc", "gcode", "g-code", "unreal", "ue5", "blender", "compila c++", "script python"]):
        assigned_agent = "AGENTE_ZERO"
        reason = "Task di sviluppo codice, automazione industriale PLC/CNC o rendering 3D."
    elif any(k in p_low for k in ["flusso", "workflow", "cron notturno", "schedula", "foglio excel", "google sheets", "bot telegram"]):
        assigned_agent = "N8N_ORCHESTRATOR"
        reason = "Task di orchestrazione visiva, trigger temporizzato o automazione multi-canale."
    else:
        assigned_agent = "HERMES_MASTER"
        reason = "Task di dialogo naturale, calcolo preventivo, vision AI o strategia generale."

    agent_info = AGENT_SPECIALIZATION_MATRIX.get(assigned_agent, {})
    out = {
        "status": "SUCCESS",
        "task_prompt": task_prompt,
        "assigned_agent": assigned_agent,
        "agent_role": agent_info.get("role"),
        "routing_reason": reason,
        "available_mcp_tools": agent_info.get("assigned_mcp_skills", []),
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }
    if assigned_agent == "HERMES_KALI":
        kali = _run_kali(task_prompt)
        if kali:
            out["kali"] = kali
            out["stdout"] = kali.get("stdout") or kali.get("message") or ""
            out["exit_code"] = kali.get("exit_code")
            if kali.get("status") == "ERROR":
                out["status"] = "ERROR"
    return out


def execute(params=None):
    params = params or {}
    action = params.get("action", "route")
    if action == "matrix":
        return {
            "status": "SUCCESS",
            "matrix": AGENT_SPECIALIZATION_MATRIX
        }
    prompt = params.get("prompt") or params.get("task") or params.get("command") or ""
    return route_task_to_agent(prompt)
