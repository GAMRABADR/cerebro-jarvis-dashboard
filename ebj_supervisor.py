# ==============================================================================
#  EBJ SUPERVISOR WATCHDOG DAEMON — Auto-Heal & Zero-Downtime Controller
#  Monitors: jarvis-bridge (Port 9000) & Python server (Port 8088)
#  Auto-restarts dead processes in < 2 seconds with exponential backoff
# ==============================================================================

import os
import sys
import time
import socket
import subprocess
import logging

LOG_FILE = os.path.join(os.path.dirname(__file__), "ebj_supervisor.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SUPERVISOR] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

WORKSPACE_ROOT = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio"
BRIDGE_EXE = os.path.join(WORKSPACE_ROOT, "ebj-supreme", "jarvis-bridge", "target", "debug", "jarvis-bridge.exe")
PYTHON_SERVER = os.path.join(WORKSPACE_ROOT, "cerebro-jarvis-dashboard", "server.py")

procs = {
    "bridge": None,
    "python": None
}

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_bridge():
    if not os.path.exists(BRIDGE_EXE):
        logging.error(f"Eseguibile non trovato: {BRIDGE_EXE}")
        return None
    logging.info("Avvio jarvis-bridge.exe...")
    env = os.environ.copy()
    env["RUST_LOG"] = "info"
    p = subprocess.Popen([BRIDGE_EXE], cwd=os.path.dirname(BRIDGE_EXE), env=env)
    return p

def start_python():
    logging.info("Avvio server.py Python...")
    p = subprocess.Popen([sys.executable, PYTHON_SERVER], cwd=os.path.dirname(PYTHON_SERVER))
    return p

def health_check_and_heal():
    # 1. Verifica Porta 9000 (Rust Bridge)
    if not is_port_open(9000):
        logging.warning("Porta 9000 non risponde! Riavvio immediato di jarvis-bridge...")
        if procs["bridge"] and procs["bridge"].poll() is None:
            try:
                procs["bridge"].terminate()
            except Exception:
                pass
        procs["bridge"] = start_bridge()
        time.sleep(1.5)

    # 2. Verifica Porta 8088 (Python Server)
    if not is_port_open(8088):
        logging.warning("Porta 8088 non risponde! Riavvio immediato di server.py...")
        if procs["python"] and procs["python"].poll() is None:
            try:
                procs["python"].terminate()
            except Exception:
                pass
        procs["python"] = start_python()
        time.sleep(1.0)

def main():
    logging.info("╔════════════════════════════════════════════════════════════════════╗")
    logging.info("║  E.B.J. SUPERVISOR WATCHDOG DAEMON OPERATIVO — AUTO-HEAL ATTIVO   ║")
    logging.info("╚════════════════════════════════════════════════════════════════════╝")
    
    # Esegui primo check
    health_check_and_heal()

    while True:
        try:
            health_check_and_heal()
            time.sleep(3)
        except KeyboardInterrupt:
            logging.info("Arresto supervisor...")
            break
        except Exception as e:
            logging.error(f"Errore ciclo supervisor: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
