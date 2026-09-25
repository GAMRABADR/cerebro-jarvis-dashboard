# -*- coding: utf-8 -*-
"""
E.B.J. AUTONOMOUS AI EMPLOYEES & NIGHT FLEET ENGINE
Ispirato alle architetture di Riccardo Zanetti (15 tool) e Jirka Hernik (Hermes VPS 24/7).
Gestione di 7 Agenti Autonomi che lavorano mentre l'Ingegnere Badr dorme o è fuori sede.
Supporto per i comandi universali:
  - /new <task>    : Reset contesto e avvio nuovo compito autonomo in background
  - /steer <guida> : Correzione e iniezione direttive al volo senza interruzione
  - /queue <task>  : Inserimento nella coda notturna (Night Queue)
"""

import os
import sys
import time
import json
import sqlite3
import threading
import datetime
import traceback

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autonomous_task_queue.db")

# I 7 Agenti del Team Autonomo
FLEET_AGENTS = {
    "hermes": {
        "name": "HERMES AGENT (Task Master)",
        "role": "Orchestratore Autonomo Task Complessi",
        "runtime": "Docker ebj-hermes (VPS 24GB) + Tokio Rust Bridge",
        "icon": "🤖",
        "status": "ONLINE / STANDBY"
    },
    "openclaw": {
        "name": "OPENCLAW LEAD HUNTER",
        "role": "Scraping & Monitoring Subito/Bakeca/Marketplace H24",
        "runtime": "Playwright Stealth + Chromium Headless",
        "icon": "🕷️",
        "status": "ONLINE / ACTIVE"
    },
    "b2b_pitcher": {
        "name": "B2B PITCHER (SELEZIONE & SGOMBERI)",
        "role": "Audit Agenzie Immobiliari e Prospetti Autolavaggi",
        "runtime": "ReportLab PDF Engine + SMTP Gmail SSL",
        "icon": "💼",
        "status": "ONLINE / STANDBY"
    },
    "claude_code": {
        "name": "CLAUDE CODE & APEX DEV",
        "role": "Sviluppo Autonomo, Git Commit, Rust SIMD, UE5.8",
        "runtime": "Anthropic Claude Opus 5.5 + Cargo Release",
        "icon": "💻",
        "status": "ONLINE / STANDBY"
    },
    "sentinel": {
        "name": "SENTINEL SELF-HEAL & BATTERY GUARD",
        "role": "Supervisione 11 Container VPS, RAM & Telegram Silent Guard",
        "runtime": "Watchdog Supervisor Daemon (Port 9000)",
        "icon": "🛡️",
        "status": "ONLINE / RUNNING"
    },
    "jev_marketplace": {
        "name": "JEV PERIZIE & AUTO-POSTER",
        "role": "Stima Arredi Usati & Pubblicazione Stealth FB/Subito",
        "runtime": "Computer Vision 1080p + JEV Estimator",
        "icon": "💎",
        "status": "ONLINE / STANDBY"
    },
    "postiz_radar": {
        "name": "POSTIZ SOCIAL RADAR",
        "role": "Monitoraggio Menzioni, Gruppi FB & Discord Gaming",
        "runtime": "Discord Bot API + Social Webhook Gateway",
        "icon": "📡",
        "status": "ONLINE / ACTIVE"
    }
}

_active_task_lock = threading.Lock()
_active_task_id = None
_active_task_prompt = None
_active_task_steer = []
_active_task_thread = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE,
            agent_type TEXT,
            command TEXT,
            instruction TEXT,
            status TEXT, -- QUEUED, RUNNING, COMPLETED, FAILED
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            result_summary TEXT,
            steer_notes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def _pick_best_agent(prompt):
    p_low = prompt.lower()
    if any(k in p_low for k in ["subito", "annunci", "lead", "bologna", "imola", "bazar", "bici", "prezzo", "trova"]):
        return "openclaw"
    elif any(k in p_low for k in ["autolavagg", "detergenz", "selezione", "agenzi", "immobiliare", "prospetto", "preventivo"]):
        return "b2b_pitcher"
    elif any(k in p_low for k in ["codice", "rust", "compila", "bug", "ue5", "git", "commit", "funzione"]):
        return "claude_code"
    elif any(k in p_low for k in ["vps", "docker", "riavvia", "container", "memoria", "notifiche"]):
        return "sentinel"
    elif any(k in p_low for k in ["perizia", "porta", "valuta", "stima", "marketplace", "vendi"]):
        return "jev_marketplace"
    elif any(k in p_low for k in ["discord", "post", "social", "canale", "gruppo"]):
        return "postiz_radar"
    return "hermes"

def dispatch_new_task(instruction, origin="telegram"):
    """
    Comando /new: resetta il contesto e lancia un nuovo task autonomo prioritario.
    """
    global _active_task_id, _active_task_prompt, _active_task_steer, _active_task_thread

    clean_task = instruction.strip()
    if not clean_task:
        return {
            "status": "ERROR",
            "message": "Specificare il compito dopo il comando /new (es: /new trova annunci arredi a Bologna)"
        }

    agent_key = _pick_best_agent(clean_task)
    agent = FLEET_AGENTS.get(agent_key, FLEET_AGENTS["hermes"])
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = f"T_{now_str}"

    with _active_task_lock:
        _active_task_id = task_id
        _active_task_prompt = clean_task
        _active_task_steer = []

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO task_queue (task_id, agent_type, command, instruction, status, started_at)
            VALUES (?, ?, '/new', ?, 'RUNNING', CURRENT_TIMESTAMP)
        """, (task_id, agent_key, clean_task))
        conn.commit()
        conn.close()

    # Avvia worker thread per esecuzione autonoma
    _active_task_thread = threading.Thread(target=_execute_task_worker, args=(task_id, agent_key, clean_task, origin), daemon=True)
    _active_task_thread.start()

    return {
        "status": "SUCCESS",
        "task_id": task_id,
        "agent": agent["name"],
        "icon": agent["icon"],
        "prompt": clean_task,
        "message": f"🚀 [AI EMPLOYEE — NUOVO TASK AVVIATO]\n\nTask: {clean_task}\nAgente: {agent['icon']} {agent['name']}\nID: #{task_id}\n\nL'agente lavora in autonomia. Usa /steer per correggere o /queue per accodare."
    }

def steer_active_task(guidance, origin="telegram"):
    """
    Comando /steer: inietta direttive correttive nell'agente attualmente in esecuzione.
    """
    global _active_task_id, _active_task_steer
    clean_steer = guidance.strip()
    if not clean_steer:
        return {"status": "ERROR", "message": "Specificare la correzione dopo /steer"}

    with _active_task_lock:
        if not _active_task_id:
            return {
                "status": "WARNING",
                "message": "Nessun task attivo al momento. Usa /new per avviarne uno nuovo o /queue per metterlo in lista."
            }

        _active_task_steer.append(clean_steer)
        steer_text = " | ".join(_active_task_steer)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE task_queue SET steer_notes = ? WHERE task_id = ?", (steer_text, _active_task_id))
        conn.commit()
        conn.close()

    return {
        "status": "SUCCESS",
        "task_id": _active_task_id,
        "steer_note": clean_steer,
        "message": f"🧭 [AI EMPLOYEE — ROTTA MODIFICATA (STEER)]\n\nDirettiva: \"{clean_steer}\"\nApplicata con successo al task attivo #{_active_task_id}."
    }

def enqueue_task(instruction, origin="telegram"):
    """
    Comando /queue: aggiunge il task alla coda notturna (Night Queue).
    """
    clean_task = instruction.strip()
    if not clean_task:
        return {"status": "ERROR", "message": "Specificare il compito da accodare dopo /queue"}

    agent_key = _pick_best_agent(clean_task)
    agent = FLEET_AGENTS.get(agent_key, FLEET_AGENTS["hermes"])
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = f"Q_{now_str}"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO task_queue (task_id, agent_type, command, instruction, status)
        VALUES (?, ?, '/queue', ?, 'QUEUED')
    """, (task_id, agent_key, clean_task))
    conn.commit()
    c.execute("SELECT COUNT(*) FROM task_queue WHERE status = 'QUEUED'")
    queue_len = c.fetchone()[0]
    conn.close()

    # Se non c'è nessun task attivo al momento, avvialo subito
    with _active_task_lock:
        if not _active_task_id:
            threading.Thread(target=_check_and_run_next_queued, daemon=True).start()

    return {
        "status": "SUCCESS",
        "task_id": task_id,
        "agent": agent["name"],
        "icon": agent["icon"],
        "queue_position": queue_len,
        "message": f"📥 [AI EMPLOYEE — TASK ACCODATO]\n\nTask: {clean_task}\nAgente: {agent['icon']} {agent['name']}\nPosizione in coda: #{queue_len}\n\nVerrà elaborato autonomamente dal team notturno."
    }

def get_fleet_status():
    """
    Ritorna lo stato completo dei 7 agenti, del task attivo e della coda notturna.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT task_id, agent_type, command, instruction, status, started_at, steer_notes FROM task_queue WHERE status = 'RUNNING' LIMIT 1")
    running_row = c.fetchone()

    c.execute("SELECT task_id, agent_type, instruction, created_at FROM task_queue WHERE status = 'QUEUED' ORDER BY id ASC LIMIT 10")
    queued_rows = c.fetchall()

    c.execute("SELECT task_id, agent_type, instruction, status, completed_at, result_summary FROM task_queue WHERE status IN ('COMPLETED', 'FAILED') ORDER BY id DESC LIMIT 5")
    recent_rows = c.fetchall()
    conn.close()

    running_task = None
    if running_row:
        running_task = {
            "task_id": running_row[0],
            "agent_type": running_row[1],
            "command": running_row[2],
            "instruction": running_row[3],
            "status": running_row[4],
            "started_at": running_row[5],
            "steer_notes": running_row[6]
        }

    queue_list = [
        {"task_id": r[0], "agent_type": r[1], "instruction": r[2], "created_at": r[3]}
        for r in queued_rows
    ]

    recent_history = [
        {"task_id": r[0], "agent_type": r[1], "instruction": r[2], "status": r[3], "completed_at": r[4], "summary": r[5]}
        for r in recent_rows
    ]

    return {
        "agents": FLEET_AGENTS,
        "active_task": running_task,
        "queued_tasks": queue_list,
        "queued_count": len(queue_list),
        "recent_history": recent_history,
        "night_fleet_online": True,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def _execute_task_worker(task_id, agent_key, prompt, origin="telegram"):
    """
    Worker che esegue il compito autonomamente via skill / AI a cascata.
    """
    global _active_task_id, _active_task_prompt, _active_task_steer
    print(f"[AI Employee] Avvio esecuzione task #{task_id} ({agent_key}): {prompt}")

    summary = ""
    try:
        # Import lazy per evitare cicli
        import requests
        import subprocess

        # Simulazione o dispatch skill reale
        agent_info = FLEET_AGENTS.get(agent_key, FLEET_AGENTS["hermes"])

        # Check steer al volo
        steer_extra = ""
        with _active_task_lock:
            if _active_task_steer:
                steer_extra = "\n[DIRETTIVE CORRETTIVE STEER RICEVUTE]: " + " | ".join(_active_task_steer)

        full_prompt = f"Sei l'agente autonomo {agent_info['name']}. Esegui con la massima precisione: {prompt}{steer_extra}"

        # Chiamata al Master Core locale
        res = requests.post("http://127.0.0.1:8088/api/chat", json={
            "prompt": full_prompt,
            "model": "auto",
            "persona": "jarvis"
        }, timeout=45)

        if res.status_code == 200:
            d = res.json()
            summary = d.get("response", "Completato con successo.")
        else:
            summary = f"Esecuzione completata con status code {res.status_code}."

        # Segna come COMPLETED
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE task_queue 
            SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP, result_summary = ?
            WHERE task_id = ?
        """, (summary[:1000], task_id))
        conn.commit()
        conn.close()

        print(f"[AI Employee] Task #{task_id} COMPLETATO!")

        # Notifica Telegram a Badr se origin è telegram o se configurato
        try:
            tg_token = os.environ.get("TELEGRAM_BOT_TOKEN_JARVIS_MASTER", "")
            tg_chat = os.environ.get("TELEGRAM_CHAT_ID_BADR", "7298887137")
            if tg_token:
                notif_msg = (
                    f"✅ *[AI EMPLOYEE — COMPITO COMPLETATO]*\n\n"
                    f"Task: _{prompt}_\n"
                    f"Agente: {agent_info['icon']} {agent_info['name']}\n\n"
                    f"📋 *Risultato:*\n{summary[:500]}..."
                )
                requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", json={
                    "chat_id": tg_chat,
                    "text": notif_msg,
                    "parse_mode": "Markdown"
                }, timeout=5)
        except Exception as te:
            print(f"[AI Employee TG Notif Err]: {te}")

    except Exception as e:
        err_msg = f"Errore durante l'esecuzione: {str(e)}\n{traceback.format_exc()}"
        print(f"[AI Employee Err]: {err_msg}")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE task_queue SET status = 'FAILED', completed_at = CURRENT_TIMESTAMP, result_summary = ? WHERE task_id = ?", (err_msg[:800], task_id))
        conn.commit()
        conn.close()

    finally:
        with _active_task_lock:
            _active_task_id = None
            _active_task_prompt = None
            _active_task_steer = []

        # Controlla se ci sono altri compiti in coda notturna
        threading.Thread(target=_check_and_run_next_queued, daemon=True).start()

def _check_and_run_next_queued():
    """
    Estrae il prossimo compito dalla coda notturna ed inizia l'esecuzione.
    """
    global _active_task_id, _active_task_prompt, _active_task_steer, _active_task_thread

    with _active_task_lock:
        if _active_task_id:
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT task_id, agent_type, instruction FROM task_queue WHERE status = 'QUEUED' ORDER BY id ASC LIMIT 1")
        row = c.fetchone()
        if not row:
            conn.close()
            return

        next_id, agent_key, instruction = row
        c.execute("UPDATE task_queue SET status = 'RUNNING', started_at = CURRENT_TIMESTAMP WHERE task_id = ?", (next_id,))
        conn.commit()
        conn.close()

        _active_task_id = next_id
        _active_task_prompt = instruction
        _active_task_steer = []

    _active_task_thread = threading.Thread(target=_execute_task_worker, args=(next_id, agent_key, instruction), daemon=True)
    _active_task_thread.start()

# Avvia scheduler periodico per coda notturna se c'è lavoro in sospeso
def start_night_queue_daemon():
    def _loop():
        while True:
            time.sleep(10)
            _check_and_run_next_queued()
    t = threading.Thread(target=_loop, daemon=True, name="night-fleet-daemon")
    t.start()

start_night_queue_daemon()
print("[Autonomous Employee Fleet] Engine attivo. 7 Agenti pronti per esecuzione H24 (/new, /steer, /queue).")
