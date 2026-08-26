"""
E.B.J. AI · Zero-Downtime Tunnel & Server Watchdog Supervisor
Monitora e mantiene perennemente attivi i 3 processi vitali:
1. Master Server: server.py (Porta 8088)
2. Rust Bridge: jarvis-bridge.exe (Porta 9000)
3. Cloudflare Tunnel: cloudflared.exe (https://eb.badrexpress.com)
"""
import os
import sys
import time
import subprocess
import requests
import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard"
LOG_FILE = os.path.join(BASE_DIR, "watchdog_supervisor.log")

CF_TOKEN = "eyJhIjoiYzQ4YjA0ZGViODA1NzcwM2EyODQ5ZTZmOWY5ZWVmNjkiLCJ0IjoiZjFlNjQ4YWYtMGU0Yi00YWVjLWE1N2EtZmYzZmYxZGFiZjc3IiwicyI6Ik1qbGpZemt6WXpVdFl6VXpOaTAwTXpWa0xUaG1Nell0TWpBM09UVTRNRGhrTUdFMSJ9"
CLOUDFLARED_BIN = os.path.join(BASE_DIR, "cloudflared.exe")
RUST_BRIDGE_BIN = os.path.join(os.path.dirname(BASE_DIR), "jarvis-bridge", "target", "release", "jarvis-bridge.exe")
SERVER_PY = os.path.join(BASE_DIR, "server.py")

processes = {
    "server": None,
    "rust_bridge": None,
    "cloudflared": None
}

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [WATCHDOG] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        print(line.encode('ascii', 'replace').decode('ascii'), flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

import socket

def is_port_responding(port, path="/api/ping"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        res = s.connect_ex(('127.0.0.1', port))
        s.close()
        return res == 0
    except Exception:
        return False

def is_process_alive(proc):
    if proc is None:
        return False
    return proc.poll() is None

def start_server():
    log("Avvio/Ripristino Master Server (server.py:8088)...")
    cmd = [sys.executable, SERVER_PY]
    proc = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    time.sleep(1)
    return proc

def start_rust_bridge():
    if os.path.exists(RUST_BRIDGE_BIN):
        log("Avvio/Ripristino Rust Tokio Bridge (porta 9000)...")
        proc = subprocess.Popen(
            [RUST_BRIDGE_BIN],
            cwd=os.path.dirname(RUST_BRIDGE_BIN),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return proc
    return None

def start_cloudflared():
    if os.path.exists(CLOUDFLARED_BIN):
        log("Avvio/Ripristino Cloudflare Named Tunnel (https://eb.badrexpress.com)...")
        cmd = [CLOUDFLARED_BIN, "tunnel", "run", "--token", CF_TOKEN]
        proc = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return proc
    else:
        log("ERRORE: cloudflared.exe non trovato in " + CLOUDFLARED_BIN)
        return None

def supervisor_loop():
    log("==========================================================")
    log("[SENTRY] E.B.J. ZERO-DOWNTIME SUPERVISOR DAEMON ATTIVATO")
    log("==========================================================")

    # Initial boot of any missing process
    if not is_port_responding(8088, "/"):
        processes["server"] = start_server()
    else:
        log("Master Server (8088) gia attivo e rispondente.")

    if not is_port_responding(9000, "/api/ping"):
        processes["rust_bridge"] = start_rust_bridge()
    else:
        log("Rust Bridge (9000) gia attivo e rispondente.")

    processes["cloudflared"] = start_cloudflared()

    while True:
        try:
            # 1. Check Server.py (Port 8088)
            if not is_port_responding(8088, "/"):
                log("Allarme: Master Server (8088) non risponde! Riavvio immediato...")
                if processes["server"]:
                    try: processes["server"].terminate()
                    except Exception: pass
                processes["server"] = start_server()

            # 2. Check Rust Bridge (Port 9000)
            if not is_port_responding(9000, "/api/ping"):
                if not is_process_alive(processes["rust_bridge"]):
                    log("Allarme: Rust Bridge (9000) terminato! Riavvio immediato...")
                    processes["rust_bridge"] = start_rust_bridge()

            # 3. Check Cloudflared process
            if not is_process_alive(processes["cloudflared"]):
                log("Allarme: cloudflared.exe terminato! Resurrezione immediata del Tunnel...")
                processes["cloudflared"] = start_cloudflared()

        except Exception as e:
            log(f"Eccezione ciclo supervisore: {e}")

        time.sleep(2.0)

if __name__ == "__main__":
    supervisor_loop()
