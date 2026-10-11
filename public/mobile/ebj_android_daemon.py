#!/usr/bin/env python3
"""
E.B.J. Supreme — Android Mobile Hardware Node (Termux Companion)
Connessione diretta tra lo smartphone di Badr e il Server EBJ Supreme.

Capacità hardware gestite da EBJ:
1. Chiamate telefoniche native (termux-telephony-call)
2. Invio SMS nativi (termux-sms-send)
3. Invio / Apertura chat WhatsApp Business (am start intent)
4. Telemetria GPS in tempo reale (termux-location)
5. Notifiche smartphone in tempo reale (termux-notification-list)
6. Sintesi vocale altoparlante telefono (termux-tts-speak)
7. Cattura foto con fotocamera (termux-camera-photo)
"""

import os
import sys
import time
import json
import urllib.parse
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

def send_native_sms(number, text):
    clean_num = "".join(c for c in str(number) if c.isdigit() or c == "+")
    print(f"💬 Invio SMS a {clean_num}: {text}")
    run_termux_cmd(["termux-sms-send", "-n", clean_num, text])
    return True

def open_whatsapp_chat(number, text):
    clean_num = "".join(c for c in str(number) if c.isdigit())
    if clean_num.startswith("0") and len(clean_num) == 10:
        clean_num = "39" + clean_num
    elif not clean_num.startswith("39") and len(clean_num) == 10:
        clean_num = "39" + clean_num
    
    encoded_text = urllib.parse.quote(text)
    intent_url = f"whatsapp://send?phone={clean_num}&text={encoded_text}"
    print(f"🟢 Apertura WhatsApp a {clean_num}")
    run_termux_cmd(["am", "start", "-a", "android.intent.action.VIEW", "-d", intent_url])
    return True

def speak_on_device(text):
    print(f"🗣️ TTS Altoparlante: {text}")
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
        "status": "ONLINE"
    }
    try:
        r = requests.post(f"{SERVER_URL}/api/device/android/telemetry", json=payload, timeout=6)
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
    elif action == "sms":
        num = params.get("number")
        txt = params.get("text", "")
        if num and txt: send_native_sms(num, txt)
    elif action in ("whatsapp", "whatsapp_send"):
        num = params.get("number")
        txt = params.get("text", "")
        if num and txt: open_whatsapp_chat(num, txt)
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
    speak_on_device("Nodo mobile E.B.J. sincronizzato e pronto, Badr.")
    while True:
        try:
            send_heartbeat()
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
