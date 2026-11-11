#!/bin/bash
# ==============================================================================
#  E.B.J. SUPREME — ANDROID FULL HARDWARE DAEMON & LAST-GASP BEACON (TERMUX)
#  Compatibile: Tutti gli smartphone Android (Termux + Termux:API)
# ==============================================================================

echo "=========================================================="
echo "⚡ INSTALLAZIONE E.B.J. ANDROID FULL HARDWARE NODE v2.0"
echo "   Ingegner Badr El Ouariti — EBGStudio & BadrExpress"
echo "=========================================================="

echo "📦 [1/4] Aggiornamento pacchetti Termux & API..."
pkg update -y && pkg upgrade -y
pkg install -y python git curl termux-api

echo "🐍 [2/4] Installazione moduli Python..."
pip install --upgrade pip
pip install requests urllib3

echo "📂 [3/4] Configurazione Demone & Telemetria di Fabbrica..."
mkdir -p ~/ebj-mobile
cat << 'EOF' > ~/ebj-mobile/ebj_android_daemon.py
#!/usr/bin/env python3
"""
E.B.J. Supreme — Android Full Hardware Control, Factory Telemetry & Last-Gasp Beacon.
Funzioni supportate:
- Dati di fabbrica reali (Modello, Produttore, Android OS, Operatore SIM, Device Code)
- Last-Gasp Pre-Shutdown (<= 5% batteria): invia GPS + Wi-Fi BSSID + Celle + Foto prima dello spegnimento
- Modalita Smarrito / Squilla al Massimo Volume + Torcia + Vibrazione + Voce Diego Neural
- Chiamate telefoniche, SMS, WhatsApp, Appunti, Torcia, Foto, GPS on-demand
"""

import os
import sys
import time
import json
import base64
import urllib.parse
import subprocess
import requests

SERVER_URL = os.environ.get("EBJ_SERVER_URL", "https://eb.badrexpress.com").rstrip("/")
NODE_ID = os.environ.get("EBJ_DEVICE_ID", "badr-smartphone-primary")
POLL_INTERVAL = 4.0
GPS_INTERVAL = 60.0

HEADERS = {"Content-Type": "application/json"}
if os.environ.get("EBJ_CF_CLIENT_ID") and os.environ.get("EBJ_CF_CLIENT_SECRET"):
    HEADERS["CF-Access-Client-Id"] = os.environ["EBJ_CF_CLIENT_ID"]
    HEADERS["CF-Access-Client-Secret"] = os.environ["EBJ_CF_CLIENT_SECRET"]

_LAST_GPS_TS = 0.0
_LAST_GPS_DATA = {}
_LAST_GASP_SENT = False
_LOST_MODE = False
_FACTORY_CACHE = {}

def run_cmd(args, timeout=15):
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return res.stdout.strip()
    except Exception:
        return ""

def collect_factory_specs():
    global _FACTORY_CACHE
    if _FACTORY_CACHE:
        return _FACTORY_CACHE
    manufacturer = run_cmd(["getprop", "ro.product.manufacturer"])
    model = run_cmd(["getprop", "ro.product.model"])
    device_code = run_cmd(["getprop", "ro.product.device"])
    android_ver = run_cmd(["getprop", "ro.build.version.release"])
    serial = run_cmd(["getprop", "ro.serialno"])
    if not serial:
        serial = run_cmd(["settings", "get", "secure", "android_id"])
    tel_raw = run_cmd(["termux-telephony-deviceinfo"])
    carrier = ""
    net_type = ""
    if tel_raw:
        try:
            td = json.loads(tel_raw)
            carrier = td.get("network_operator_name") or td.get("sim_operator_name") or ""
            net_type = td.get("network_type") or ""
        except Exception:
            pass
    _FACTORY_CACHE = {
        "manufacturer": manufacturer,
        "model": model,
        "device_code": device_code,
        "android_version": android_ver,
        "serial_or_id": serial,
        "carrier": carrier,
        "network_type": net_type,
    }
    return _FACTORY_CACHE

def get_gps_location(force=False):
    global _LAST_GPS_TS, _LAST_GPS_DATA
    now = time.time()
    if not force and _LAST_GPS_DATA and (now - _LAST_GPS_TS) < GPS_INTERVAL:
        return _LAST_GPS_DATA
    for provider in ("gps", "network"):
        raw = run_cmd(["termux-location", "-p", provider, "-r", "last"], timeout=12)
        if raw:
            try:
                loc = json.loads(raw)
                if loc.get("latitude"):
                    _LAST_GPS_TS = now
                    _LAST_GPS_DATA = loc
                    return loc
            except Exception:
                pass
    return _LAST_GPS_DATA

def get_battery_status():
    raw = run_cmd(["termux-battery-status"])
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {}

def get_wifi_info():
    raw = run_cmd(["termux-wifi-connectioninfo"])
    if raw:
        try:
            d = json.loads(raw)
            return {"ssid": d.get("ssid", ""), "bssid": d.get("bssid", ""), "ip": d.get("ip", "")}
        except Exception:
            pass
    return {}

def get_cell_info():
    raw = run_cmd(["termux-telephony-cellinfo"])
    if raw:
        try:
            d = json.loads(raw)
            if isinstance(d, list):
                return d[:4]
        except Exception:
            pass
    return []

def speak_jarvis(text):
    try:
        r = requests.post(
            f"{SERVER_URL}/api/tts",
            headers=HEADERS,
            json={"text": text, "persona": "jarvis"},
            timeout=6,
        )
        if r.ok:
            b64 = r.json().get("audio_base64", "")
            if b64:
                mp3_p = os.path.expanduser("~/ebj-mobile/voice_tmp.mp3")
                with open(mp3_p, "wb") as wf:
                    wf.write(base64.b64decode(b64))
                run_cmd(["termux-media-player", "play", mp3_p], timeout=20)
                return
    except Exception:
        pass
    run_cmd(["termux-tts-speak", "-l", "it", "-r", "1.05", text])

def capture_and_upload_photo(cam_id="0"):
    out_p = os.path.expanduser("~/ebj-mobile/latest_snap.jpg")
    run_cmd(["termux-camera-photo", "-c", str(cam_id), out_p], timeout=12)
    if os.path.exists(out_p):
        try:
            with open(out_p, "rb") as rf:
                b64 = base64.b64encode(rf.read()).decode("utf-8")
            requests.post(
                f"{SERVER_URL}/api/device/android/upload-photo",
                headers=HEADERS,
                json={"photo_base64": b64},
                timeout=12,
            )
        except Exception:
            pass

def exec_remote_command(cmd):
    global _LOST_MODE
    action = cmd.get("action")
    params = cmd.get("params", {}) or {}
    print(f"⚡ [EBJ CMD]: {action}")

    if action == "call":
        num = "".join(c for c in str(params.get("number", "")) if c.isdigit() or c == "+")
        if num:
            run_cmd(["termux-telephony-call", num])
    elif action == "sms":
        num = "".join(c for c in str(params.get("number", "")) if c.isdigit() or c == "+")
        msg = params.get("text", "")
        if num and msg:
            run_cmd(["termux-sms-send", "-n", num, msg])
    elif action == "whatsapp":
        num = "".join(c for c in str(params.get("number", "")) if c.isdigit())
        msg = urllib.parse.quote(params.get("text", ""))
        if num:
            run_cmd(["termux-open-url", f"https://wa.me/{num}?text={msg}"])
    elif action == "speak":
        if params.get("text"):
            speak_jarvis(params["text"])
    elif action == "vibrate":
        run_cmd(["termux-vibrate", "-d", str(params.get("ms", 700))])
    elif action == "torch":
        state = "on" if params.get("on", True) else "off"
        run_cmd(["termux-torch", state])
    elif action == "clipboard":
        if params.get("text"):
            run_cmd(["termux-clipboard-set", str(params["text"])])
    elif action == "photo":
        capture_and_upload_photo(params.get("camera", "0"))
    elif action == "locate":
        get_gps_location(force=True)
    elif action == "factory_sync":
        global _FACTORY_CACHE
        _FACTORY_CACHE = {}
        collect_factory_specs()
    elif action in ("lost_mode_on", "ring_alarm"):
        _LOST_MODE = True
        run_cmd(["termux-volume", "music", "15"])
        run_cmd(["termux-torch", "on"])
        run_cmd(["termux-vibrate", "-d", "1000"])
        speak_jarvis("Attenzione! Modalità smarrito E B J attiva. Dispositivo localizzato.")
        get_gps_location(force=True)
        capture_and_upload_photo("1")
        run_cmd(["termux-torch", "off"])
    elif action == "lost_mode_off":
        _LOST_MODE = False
        run_cmd(["termux-torch", "off"])

def send_heartbeat():
    global _LAST_GASP_SENT, _LOST_MODE
    batt = get_battery_status()
    pct = int(batt.get("percentage", -1)) if batt.get("percentage") is not None else -1
    b_stat = str(batt.get("status", "")).upper()

    is_last_gasp = False
    if 0 <= pct <= 5 and "DISCHARG" in b_stat and not _LAST_GASP_SENT:
        is_last_gasp = True
        _LAST_GASP_SENT = True
    elif pct > 10:
        _LAST_GASP_SENT = False

    loc = get_gps_location(force=(is_last_gasp or _LOST_MODE))
    wifi = get_wifi_info()
    cell = get_cell_info() if (is_last_gasp or _LOST_MODE) else []
    fac = collect_factory_specs()

    if is_last_gasp:
        capture_and_upload_photo("0")

    payload = {
        "device_id": NODE_ID,
        "timestamp": time.time(),
        "battery": batt,
        "location": loc,
        "factory": fac,
        "wifi": wifi,
        "cell_info": cell,
        "last_gasp": is_last_gasp,
        "status": "ONLINE",
    }
    try:
        r = requests.post(f"{SERVER_URL}/api/device/android/telemetry", headers=HEADERS, json=payload, timeout=6)
        if r.ok:
            data = r.json()
            _LOST_MODE = bool(data.get("lost_mode", False))
            for cmd in data.get("pending_commands", []):
                exec_remote_command(cmd)
    except Exception as e:
        print(f"[Heartbeat warn]: {e}")

def main():
    collect_factory_specs()
    speak_jarvis("Nodo hardware Android E B J sincronizzato con telemetria di fabbrica e localizzazione d emergenza, signore.")
    while True:
        try:
            send_heartbeat()
        except Exception as e:
            print(f"[Loop err]: {e}")
        time.sleep(2.0 if _LOST_MODE else POLL_INTERVAL)

if __name__ == "__main__":
    main()
EOF

chmod +x ~/ebj-mobile/ebj_android_daemon.py

cat << 'EOF' > $PREFIX/bin/ebj-start
#!/bin/bash
termux-wake-lock
echo "🚀 Avvio Demone EBJ Android Full Node..."
python ~/ebj-mobile/ebj_android_daemon.py
EOF
chmod +x $PREFIX/bin/ebj-start

echo "✅ INSTALLAZIONE COMPLETATA! Esegui: ebj-start"
