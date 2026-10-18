#!/bin/bash
# ==============================================================================
#  E.B.J. SUPREME — ANDROID MOBILE HARDWARE DAEMON INSTALLER (TERMUX)
#  Compatibile: Tutti i dispositivi Android (Samsung, Xiaomi, Oppo, Pixel, ecc.)
# ==============================================================================

echo "=========================================================="
echo "⚡ INSTALLAZIONE E.B.J. ANDROID BRIDGE & HARDWARE DAEMON"
echo "   Ingegner Badr El Ouariti — EBGStudio & BadrExpress"
echo "=========================================================="
echo ""

# 1. Aggiornamento pacchetti base Termux
echo "📦 [1/5] Aggiornamento repository Termux..."
pkg update -y && pkg upgrade -y

# 2. Installazione dipendenze richieste (Python, Curl, Termux-API, Git)
echo "📦 [2/5] Installazione Python, Termux-API e Curl..."
pkg install -y python git curl termux-api

# 3. Installazione librerie Python necessarie
echo "🐍 [3/5] Installazione moduli Python (requests, websockets)..."
pip install --upgrade pip
pip install requests urllib3 websockets

# 4. Creazione cartella EBJ e download del demone
echo "📂 [4/5] Configurazione ambiente operativo EBJ..."
mkdir -p ~/ebj-mobile
cd ~/ebj-mobile

cat << 'EOF' > ~/ebj-mobile/ebj_android_daemon.py
#!/usr/bin/env python3
"""
E.B.J. Supreme — Android Mobile Hardware Node
Connessione diretta tra lo smartphone dell'Ingegner Badr e il Server EBJ Supreme.
Consente a EBJ di:
- Effettuare chiamate telefoniche reali (termux-telephony-call)
- Rilevare posizione GPS in tempo reale (termux-location)
- Leggere notifiche WhatsApp Business e SMS (termux-notification-list)
- Parlare dall'altoparlante del telefono (termux-tts-speak)
- Scattare foto con la fotocamera (termux-camera-photo)
"""

import os
import sys
import time
import json
import subprocess
import requests

SERVER_URL = os.environ.get("EBJ_SERVER_URL", "https://eb.badrexpress.com")
POLL_INTERVAL = 3.0
NODE_ID = "badr-smartphone-primary"

print(f"🚀 [EBJ Mobile Node] Connesso a {SERVER_URL}")
print(f"📱 ID Dispositivo: {NODE_ID}")

def run_termux_cmd(args):
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return res.stdout.strip()
    except Exception as e:
        return ""

def get_gps_location():
    try:
        raw = run_termux_cmd(["termux-location", "-p", "gps", "-r", "last"])
        if not raw:
            raw = run_termux_cmd(["termux-location", "-p", "network", "-r", "last"])
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None

def get_battery_status():
    try:
        raw = run_termux_cmd(["termux-battery-status"])
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return {}

def make_phone_call(number):
    clean_num = "".join(c for c in str(number) if c.isdigit() or c == "+")
    print(f"📞 Avvio chiamata verso: {clean_num}")
    run_termux_cmd(["termux-telephony-call", clean_num])
    return True

def speak_on_device(text):
    print(f"🗣️ TTS Telefono: {text}")
    run_termux_cmd(["termux-tts-speak", "-l", "it", "-r", "1.1", text])
    return True

def get_recent_notifications():
    try:
        raw = run_termux_cmd(["termux-notification-list"])
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return []

def send_heartbeat():
    loc = get_gps_location()
    batt = get_battery_status()
    notifs = get_recent_notifications()
    payload = {
        "device_id": NODE_ID,
        "timestamp": time.time(),
        "battery": batt,
        "location": loc,
        "notifications_count": len(notifs),
        "notifications": notifs,
        "status": "ONLINE"
    }
    try:
        r = requests.post(f"{SERVER_URL}/api/device/android/telemetry", json=payload, timeout=5)
        if r.ok:
            data = r.json()
            commands = data.get("pending_commands", [])
            for cmd in commands:
                exec_remote_command(cmd)
    except Exception as e:
        print(f"Heartbeat soft fail: {e}")

def exec_remote_command(cmd):
    action = cmd.get("action")
    params = cmd.get("params", {})
    print(f"⚡ [Comando Ricevuto da EBJ]: {action}")
    
    if action == "call":
        num = params.get("number")
        if num: make_phone_call(num)
    elif action == "speak":
        text = params.get("text")
        if text: speak_on_device(text)
    elif action == "vibrate":
        run_termux_cmd(["termux-vibrate", "-d", "500"])
    elif action == "photo":
        out_p = os.path.expanduser("~/ebj-mobile/latest_snap.jpg")
        run_termux_cmd(["termux-camera-photo", "-c", "0", out_p])
        if os.path.exists(out_p):
            with open(out_p, "rb") as fh:
                requests.post(f"{SERVER_URL}/api/device/android/upload-photo", files={"photo": fh}, timeout=15)

def main():
    speak_on_device("Nodo mobile E.B.J. sincronizzato e pronto, Ingegnere.")
    while True:
        try:
            send_heartbeat()
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
EOF

chmod +x ~/ebj-mobile/ebj_android_daemon.py

# 5. Creazione comando rapido 'ebj-start'
cat << 'EOF' > $PREFIX/bin/ebj-start
#!/bin/bash
termux-wake-lock
echo "🚀 Avvio Demone EBJ Mobile Hardware Node in background..."
python ~/ebj-mobile/ebj_android_daemon.py
EOF
chmod +x $PREFIX/bin/ebj-start

echo ""
echo "=========================================================="
echo "✅ INSTALLAZIONE COMPLETATA CON SUCCESSO!"
echo "   Per avviare il collegamento con EBJ, scrivi semplicemente:"
echo "   ebj-start"
echo "=========================================================="
