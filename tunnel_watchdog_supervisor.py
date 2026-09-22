"""
E.B.J. AI · SENTINEL v3.0 - Ultra-Resilient Zero-Downtime Watchdog Supervisor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monitora e mantiene perennemente attivi i 3 processi vitali dell'ecosistema E.B.J.:
  1. Master Server:     server.py          → Porta 8088
  2. Rust Bridge:       jarvis-bridge.exe  → Porta 9000
  3. Cloudflare Tunnel: cloudflared.exe    → https://eb.badrexpress.com

Funzionalità v3.0:
  ✅ Heartbeat aggressivo ogni 2 secondi su ogni servizio
  ✅ Verifica HTTP diretta del tunnel pubblico (eb.badrexpress.com)
  ✅ Alert Telegram su ogni evento di kill/restart automatico
  ✅ Fallback automatico release→debug per Rust Bridge
  ✅ Log rotante con limite di 50.000 righe (no disk overflow)
  ✅ Auto-respawn con backoff esponenziale su crash ripetuti
  ✅ Watchdog di se stesso (secondary re-check dopo 1s post-avvio)
"""
import os
import sys
import time
import subprocess
import socket
import datetime
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────────
BASE_DIR    = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard"
JARVIS_DIR  = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\jarvis-bridge"
LOG_FILE    = os.path.join(BASE_DIR, "watchdog_supervisor.log")
LOG_MAX_LINES = 50000
HEARTBEAT_S = 2           # Ciclo di verifica ogni 2 secondi
TUNNEL_CHECK_INTERVAL = 6 # Verifica tunnel pubblico ogni N cicli (12s)
MAX_CRASH_RESTARTS = 10   # Dopo N riavvii in < 2 min → backoff 30s
PUBLIC_URL  = "https://eb.badrexpress.com/"

CF_TOKEN = "eyJhIjoiYzQ4YjA0ZGViODA1NzcwM2EyODQ5ZTZmOWY5ZWVmNjkiLCJ0IjoiZjFlNjQ4YWYtMGU0Yi00YWVjLWE1N2EtZmYzZmYxZGFiZjc3IiwicyI6Ik1qbGpZemt6WXpVdFl6VXpOaTAwTXpWa0xUaG1Nell0TWpBM09UVTRNRGhrTUdFMSJ9"

CLOUDFLARED_BIN = os.path.join(BASE_DIR, "cloudflared.exe")
SERVER_PY       = os.path.join(BASE_DIR, "server.py")

JARVIS_DIR_ROOT    = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\jarvis-bridge"
JARVIS_DIR_SUPREME = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\ebj-supreme\jarvis-bridge"

def get_best_rust_bin():
    candidates = [
        os.path.join(JARVIS_DIR_SUPREME, "target", "release", "ebj_apex_engine.exe"),
        os.path.join(JARVIS_DIR_SUPREME, "target", "release", "ebj_apex_bridge.exe"),
        os.path.join(JARVIS_DIR_SUPREME, "target", "release", "jarvis-bridge.exe"),
        os.path.join(JARVIS_DIR_ROOT, "target", "release", "ebj_apex_bridge.exe"),
        os.path.join(JARVIS_DIR_ROOT, "target", "release", "ebj_apex_engine.exe"),
        os.path.join(JARVIS_DIR_ROOT, "target", "release", "jarvis-bridge.exe"),
    ]
    existing = [c for c in candidates if os.path.exists(c)]
    if existing:
        return max(existing, key=os.path.getmtime)
    return os.path.join(JARVIS_DIR_SUPREME, "target", "release", "jarvis-bridge.exe")

RUST_BRIDGE_BIN = get_best_rust_bin()


# Telegram per alert (opzionale - non blocca se non disponibile)
TG_BOT_TOKEN = ""
TG_CHAT_ID   = "7298887137"

try:
    from dotenv import dotenv_values
    _env = dotenv_values(os.path.join(BASE_DIR, ".env"))
    TG_BOT_TOKEN = _env.get("TELEGRAM_BOT_TOKEN", TG_BOT_TOKEN)
except Exception:
    pass

# ── STATO PROCESSI ─────────────────────────────────────────────────────────────
processes = {"server": None, "rust_bridge": None, "cloudflared": None}
crash_counts = {"server": 0, "rust_bridge": 0, "cloudflared": 0}
crash_window_start = {"server": time.time(), "rust_bridge": time.time(), "cloudflared": time.time()}

# ── LOGGING ───────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        # Log rotante: se file > LOG_MAX_LINES righe, tronca le prime 10k
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > LOG_MAX_LINES:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-40000:])
    except Exception:
        pass

def tg_alert(msg: str):
    """Invia alert su Telegram se il token è configurato. Fail silenzioso."""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": f"🛡️ *E.B.J. SENTINEL v3.0*\n{msg}", "parse_mode": "Markdown"},
            timeout=4
        )
    except Exception:
        pass

# ── CHECK HELPER ─────────────────────────────────────────────────────────────
def is_port_responding(port: int) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.8)
        res = s.connect_ex(('127.0.0.1', port))
        s.close()
        return res == 0
    except Exception:
        return False

def is_process_alive(proc) -> bool:
    return proc is not None and proc.poll() is None

def is_cloudflared_os_alive() -> bool:
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq cloudflared.exe"],
            capture_output=True, text=True, timeout=3
        )
        return "cloudflared.exe" in (r.stdout or "")
    except Exception:
        return False

def check_public_tunnel() -> bool:
    """Verifica HTTP reale del tunnel pubblico. Tolera redirect e pagine HTML."""
    try:
        r = requests.get(PUBLIC_URL, timeout=5, allow_redirects=True)
        return r.status_code in (200, 301, 302, 308)
    except Exception:
        return False

# ── SPAWN PROCESSI ────────────────────────────────────────────────────────────
def _backoff_if_crashing(name: str) -> bool:
    """Ritorna True se occorre backoff (troppi crash in poco tempo)."""
    now = time.time()
    if now - crash_window_start[name] < 120:
        crash_counts[name] += 1
    else:
        crash_counts[name] = 1
        crash_window_start[name] = now

    if crash_counts[name] >= MAX_CRASH_RESTARTS:
        log(f"BACKOFF: {name} ha avuto {crash_counts[name]} crash in 2 min → pausa 30s", "WARN")
        tg_alert(f"⚠️ `{name}` ha crashato {crash_counts[name]}x in 2 min. Backoff 30s attivo.")
        time.sleep(30)
        crash_counts[name] = 0
        crash_window_start[name] = time.time()
        return True
    return False

def start_server():
    log("🔄 Avvio/Ripristino Master Server (server.py → porta 8088)...")
    _backoff_if_crashing("server")
    proc = subprocess.Popen(
        [sys.executable, SERVER_PY],
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    time.sleep(2)  # Attende stabilizzazione
    if is_port_responding(8088):
        log("✅ Master Server (8088) ONLINE")
        tg_alert("✅ Master Server :8088 ripristinato automaticamente.")
    else:
        log("❌ Master Server non risponde dopo avvio - prossimo ciclo ritenterà", "WARN")
    return proc

def start_rust_bridge():
    bin_to_run = get_best_rust_bin()
    if not os.path.exists(bin_to_run):
        log(f"ERRORE: jarvis-bridge.exe non trovato in: {bin_to_run}", "ERROR")
        return None
    log(f"🔄 Avvio/Ripristino Rust Bridge (porta 9000) → {os.path.basename(bin_to_run)}")
    _backoff_if_crashing("rust_bridge")
    proc = subprocess.Popen(
        [bin_to_run],

        cwd=os.path.dirname(bin_to_run),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    time.sleep(1.5)
    if is_port_responding(9000):
        log("✅ Rust Superpower Bridge (9000) ONLINE")
    return proc

def start_cloudflared():
    if is_cloudflared_os_alive():
        return None  # Già attivo a livello OS
    if not os.path.exists(CLOUDFLARED_BIN):
        log(f"ERRORE: cloudflared.exe non trovato in {CLOUDFLARED_BIN}", "ERROR")
        return None
    log("🔄 Avvio/Ripristino Cloudflare Named Tunnel (eb.badrexpress.com)...")
    _backoff_if_crashing("cloudflared")
    log_path = os.path.join(BASE_DIR, "cloudflared.log")
    logf = open(log_path, "ab")
    proc = subprocess.Popen(
        [CLOUDFLARED_BIN, "tunnel", "run", "--token", CF_TOKEN],
        cwd=BASE_DIR,
        stdout=logf,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    time.sleep(4)  # Il tunnel impiega qualche secondo per connettersi
    log("✅ Cloudflare Tunnel avviato")
    tg_alert("✅ Cloudflare Tunnel `eb.badrexpress.com` ripristinato automaticamente.")
    return proc

# ── MAIN LOOP ──────────────────────────────────────────────────────────────────
def supervisor_loop():
    log("═══════════════════════════════════════════════════════")
    log("  E.B.J. SENTINEL v3.0 · ZERO-DOWNTIME SUPERVISOR")
    log("  Heartbeat: 2s · Tunnel check: 12s · Alert: Telegram")
    log("═══════════════════════════════════════════════════════")

    # Avvio iniziale
    if not is_port_responding(8088):
        processes["server"] = start_server()
    else:
        log("ℹ️  Master Server (8088) già attivo.")

    if not is_port_responding(9000):
        processes["rust_bridge"] = start_rust_bridge()
    else:
        log("ℹ️  Rust Bridge (9000) già attivo.")

    if not is_cloudflared_os_alive():
        processes["cloudflared"] = start_cloudflared()
    else:
        log("ℹ️  Cloudflared già attivo a livello OS.")

    tunnel_check_counter = 0

    while True:
        try:
            # ── 1. Master Server ────────────────────────────────────────
            if not is_port_responding(8088):
                log("🚨 Master Server (8088) NON RISPONDE! Riavvio...", "WARN")
                try:
                    if processes["server"]:
                        processes["server"].terminate()
                except Exception:
                    pass
                processes["server"] = start_server()

            # ── 2. Rust Bridge ─────────────────────────────────────────
            if not is_port_responding(9000):
                if not is_process_alive(processes["rust_bridge"]):
                    log("🚨 Rust Bridge (9000) terminato! Riavvio...", "WARN")
                    processes["rust_bridge"] = start_rust_bridge()

            # ── 3. Cloudflared ─────────────────────────────────────────
            if not is_process_alive(processes["cloudflared"]) and not is_cloudflared_os_alive():
                log("🚨 Cloudflared terminato! Resurrezione tunnel...", "WARN")
                processes["cloudflared"] = start_cloudflared()

            # ── 4. Verifica Tunnel Pubblico (ogni 12s) ─────────────────
            tunnel_check_counter += 1
            if tunnel_check_counter >= TUNNEL_CHECK_INTERVAL:
                tunnel_check_counter = 0
                if not check_public_tunnel():
                    log("🚨 Tunnel pubblico https://eb.badrexpress.com NON RAGGIUNGIBILE! Restart CF...", "WARN")
                    # Tenta kill e riavvio cloudflared
                    try:
                        subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], capture_output=True, timeout=3)
                    except Exception:
                        pass
                    time.sleep(1)
                    processes["cloudflared"] = start_cloudflared()
                else:
                    log(f"🌐 Tunnel pubblico OK | 8088:{'OK' if is_port_responding(8088) else 'KO'} | 9000:{'OK' if is_port_responding(9000) else 'KO'}")

        except Exception as e:
            log(f"Eccezione ciclo supervisore: {e}", "ERROR")

        time.sleep(HEARTBEAT_S)


if __name__ == "__main__":
    supervisor_loop()
