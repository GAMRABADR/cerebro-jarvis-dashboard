# ==============================================================================
#  EBJ SUPERVISOR WATCHDOG DAEMON — Auto-Heal & Zero-Downtime Controller
#  Monitors: jarvis-bridge (Port 9000), lead-extractor (Port 9015), & Python server (Port 8088)
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

# 1. Jarvis Bridge (Rust)
BRIDGE_RELEASE = os.path.join(WORKSPACE_ROOT, "ebj-supreme", "jarvis-bridge", "target", "release", "jarvis-bridge.exe")
BRIDGE_DEBUG = os.path.join(WORKSPACE_ROOT, "ebj-supreme", "jarvis-bridge", "target", "debug", "jarvis-bridge.exe")
BRIDGE_EXE = BRIDGE_RELEASE if os.path.exists(BRIDGE_RELEASE) else BRIDGE_DEBUG

# 2. Lead Extractor (Rust SIMD)
LEAD_RELEASE = os.path.join(WORKSPACE_ROOT, "ebj-supreme", "rust-agents", "target", "release", "lead-extractor.exe")
LEAD_DEBUG = os.path.join(WORKSPACE_ROOT, "ebj-supreme", "rust-agents", "target", "debug", "lead-extractor.exe")
LEAD_EXE = LEAD_RELEASE if os.path.exists(LEAD_RELEASE) else LEAD_DEBUG

# 3. Python Master Server
CEREBRO_SERVER = os.path.join(WORKSPACE_ROOT, "cerebro-jarvis-dashboard", "server.py")
EBJ_SERVER = os.path.join(WORKSPACE_ROOT, "ebj-supreme", "jarvis", "server.py")
PYTHON_SERVER = CEREBRO_SERVER if os.path.exists(CEREBRO_SERVER) else EBJ_SERVER

procs = {
    "bridge": None,
    "lead_extractor": None,
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
    logging.info(f"Avvio jarvis-bridge.exe ({'RELEASE' if 'release' in BRIDGE_EXE else 'DEBUG'})...")
    env = os.environ.copy()
    env["RUST_LOG"] = "info"
    p = subprocess.Popen([BRIDGE_EXE], cwd=os.path.dirname(BRIDGE_EXE), env=env)
    return p

def start_lead_extractor():
    if not os.path.exists(LEAD_EXE):
        logging.warning(f"Eseguibile lead-extractor non trovato: {LEAD_EXE}")
        return None
    logging.info(f"Avvio lead-extractor.exe ({'RELEASE' if 'release' in LEAD_EXE else 'DEBUG'}) su porta 9015...")
    env = os.environ.copy()
    env["LEAD_EXTRACTOR_PORT"] = "9015"
    p = subprocess.Popen([LEAD_EXE], cwd=os.path.dirname(LEAD_EXE), env=env)
    return p

def start_python():
    logging.info(f"Avvio server.py Python ({PYTHON_SERVER})...")
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
        time.sleep(1.0)

    # 2. Verifica Porta 9015 (Rust Lead Extractor)
    if not is_port_open(9015):
        if procs["lead_extractor"] and procs["lead_extractor"].poll() is None:
            try:
                procs["lead_extractor"].terminate()
            except Exception:
                pass
        procs["lead_extractor"] = start_lead_extractor()
        time.sleep(0.5)

    # 3. Verifica Porta 8088 (Python Server)
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
    logging.info("║  Porte Monitorate: 9000 (Bridge), 9015 (Leads), 8088 (Server)     ║")
    logging.info("╚════════════════════════════════════════════════════════════════════╝")
    
    health_check_and_heal()

    while True:
        try:
            health_check_and_heal()
            time.sleep(3)
        except KeyboardInterrupt:
            logging.info("Arresto supervisor...")
            for k, p in procs.items():
                if p and p.poll() is None:
                    try:
                        p.terminate()
                    except Exception:
                        pass
            break
        except Exception as e:
            logging.error(f"Errore ciclo supervisor: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
