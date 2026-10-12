"""
==============================================================================
🚀 EBJ SUPREME — JEV UNIVERSAL SYSTEM & APPLICATION EXECUTOR
==============================================================================
Consente ad EBJ di controllare Windows 11 in modo completo ed autonomo:
1. Gestione Applicazioni (Avvio, Focus, Chiusura di qualsiasi app o cartella)
2. Ricerca & Visualizzazione Foto / Screenshot (Schermo reale o Dashboard)
3. Invio Email Universale (SMTP Gmail, note vocali Edge-TTS, allegati multipli)
4. Telemetria di Sistema & Controllo Schermo (Screenshot, clipboard, finestre)
==============================================================================
"""

from __future__ import annotations
import os
import sys
import time
import glob
import json
import base64
import ctypes
import smtplib
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

ROOT_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT_DIR / "public"
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
VOICE_DIR = PUBLIC_DIR / "voice_dispatches"
VOICE_DIR.mkdir(parents=True, exist_ok=True)

# Credenziali Email Gmail (Google App Password)
GMAIL_USER = "badraudi@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "kqvjcuzibizysoxu")

# Mappa delle applicazioni Windows più comuni e percorsi noti
KNOWN_APPS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "chrome.exe"
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "msedge.exe"
    ],
    "explorer": ["explorer.exe"],
    "esplora risorse": ["explorer.exe"],
    "cartella": ["explorer.exe"],
    "terminal": ["wt.exe", "powershell.exe"],
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "prompt dei comandi": ["cmd.exe"],
    "blocco note": ["notepad.exe"],
    "notepad": ["notepad.exe"],
    "calcolatrice": ["calc.exe"],
    "calc": ["calc.exe"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
    "gestione attivita": ["taskmgr.exe"],
    "paint": ["mspaint.exe"],
    "foto": ["ms-photos:", "explorer.exe"],
    "photos": ["ms-photos:"],
    "unreal": [
        r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
        r"D:\UnrealEngine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
        r"D:\EBGStudioProgetti\EBGS\EBGS.uproject"
    ],
    "ue5": [
        r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
        r"D:\UnrealEngine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
        r"D:\EBGStudioProgetti\EBGS\EBGS.uproject"
    ],
    "blender": [
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
        "blender.exe"
    ],
    "vscode": [
        r"C:\Users\Admin\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "code.exe"
    ],
    "code": [
        r"C:\Users\Admin\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "code.exe"
    ],
    "telegram": [
        r"C:\Users\Admin\AppData\Roaming\Telegram Desktop\Telegram.exe",
        "telegram.exe"
    ],
    "whatsapp": [
        r"C:\Program Files\WindowsApps\WhatsApp.exe",
        "whatsapp.exe"
    ],
    "spotify": [
        r"C:\Users\Admin\AppData\Roaming\Spotify\Spotify.exe",
        "spotify.exe"
    ],
    "bambu": [
        r"C:\Program Files\Bambu Studio\bin\bambu-studio.exe",
        r"C:\Program Files\Bambu Studio\bambu-studio.exe"
    ],
    "bambu studio": [
        r"C:\Program Files\Bambu Studio\bin\bambu-studio.exe",
        r"C:\Program Files\Bambu Studio\bambu-studio.exe"
    ]
}

# Cartelle di sistema standard per Explorer
FOLDER_SHORTCUTS = {
    "download": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Downloads"),
    "downloads": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Downloads"),
    "desktop": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Desktop"),
    "documenti": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Documents"),
    "documents": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Documents"),
    "immagini": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Pictures"),
    "pictures": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Pictures"),
    "musica": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Music"),
    "video": os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Videos"),
    "progetti": r"d:\EBGStudioProgetti",
    "disco c": r"C:\\",
    "disco d": r"D:\\",
    "c:": r"C:\\",
    "d:": r"D:\\"
}

# ══════════════════════════════════════════════════════════════════════════════
# 1. GESTIONE APPLICAZIONI & FINESTRE (Win32 & Schtasks)
# ══════════════════════════════════════════════════════════════════════════════

def launch_app(app_query: str, args: Optional[str] = None) -> Dict[str, Any]:
    """
    Avvia un'applicazione o cartella Windows nella sessione grafica interattiva.
    """
    t0 = time.perf_counter()
    q = app_query.lower().strip()
    words = q.split()
    
    # 1. Controllo se è una richiesta di apertura cartella (match esatto o per parola)
    for f_key, f_path in FOLDER_SHORTCUTS.items():
        if q == f_key or q == f"apri {f_key}" or f_key in words or f"cartella {f_key}" in q:
            if os.path.exists(f_path):
                subprocess.Popen(["explorer.exe", f_path])
                lat = (time.perf_counter() - t0) * 1000.0
                return {
                    "status": "success",
                    "action": "open_folder",
                    "target": f_path,
                    "latency_ms": round(lat, 2),
                    "message": f"Cartella '{f_key}' aperta in Esplora Risorse."
                }

    # 2. Controllo se il query corrisponde a un URL web
    if q.startswith("http://") or q.startswith("https://") or q.startswith("www."):
        url = q if q.startswith("http") else f"https://{q}"
        os.startfile(url)
        lat = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "success",
            "action": "open_url",
            "target": url,
            "latency_ms": round(lat, 2),
            "message": f"Aperto URL '{url}' nel browser predefinito."
        }

    # 3. Risoluzione tramite mappa delle applicazioni conosciute
    target_exec = None
    matched_app_name = q
    for name, paths in KNOWN_APPS.items():
        if name in q or q.startswith(name):
            matched_app_name = name
            for candidate in paths:
                if os.path.exists(candidate) or not os.path.isabs(candidate):
                    target_exec = candidate
                    break
            if target_exec:
                break

    # Se non trovato nella mappa, prova come comando diretto o startfile
    if not target_exec:
        # Pulisci parole di comando
        clean_q = q.replace("apri", "").replace("avvia", "").replace("lancia", "").strip()
        target_exec = clean_q

    try:
        if target_exec.startswith("ms-"):
            os.startfile(target_exec)
        elif os.path.isabs(target_exec) and target_exec.endswith(".uproject"):
            # Progetto Unreal Engine: avvia associato
            os.startfile(target_exec)
        else:
            cmd_list = [target_exec]
            if args:
                cmd_list.extend(args.split())
            
            # Usiamo start / subprocess per non bloccare
            subprocess.Popen(cmd_list, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        lat = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "success",
            "action": "launch_app",
            "app": matched_app_name,
            "target": target_exec,
            "latency_ms": round(lat, 2),
            "message": f"Applicazione '{matched_app_name}' avviata con successo."
        }
    except Exception as e:
        lat = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "error",
            "action": "launch_app",
            "target": target_exec,
            "error": str(e),
            "latency_ms": round(lat, 2)
        }

def list_running_apps() -> List[Dict[str, Any]]:
    """
    Elenca i processi grafici e le finestre principali attive dell'utente in tempo reale (< 5ms).
    """
    import psutil
    user32 = ctypes.windll.user32
    raw_windows = []
    
    def enum_proc(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                if title and title not in ["Program Manager", "Settings", "Windows Input Experience"]:
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    raw_windows.append({"hwnd": hwnd, "title": title, "pid": pid.value})
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    
    apps = []
    seen_pids = set()
    for w in raw_windows:
        pname = "application"
        mem_mb = 0.0
        try:
            p = psutil.Process(w["pid"])
            pname = p.name()
            mem_mb = round(p.memory_info().rss / (1024 * 1024), 1)
        except Exception:
            pass
        apps.append({
            "pid": w["pid"],
            "process_name": pname,
            "title": w["title"],
            "memory_mb": mem_mb
        })
    return apps

KILL_ALIASES = {
    "calcolatrice": ["CalculatorApp.exe", "calc.exe"],
    "calc": ["CalculatorApp.exe", "calc.exe"],
    "chrome": ["chrome.exe"],
    "blocco note": ["notepad.exe"],
    "notepad": ["notepad.exe"],
    "edge": ["msedge.exe"],
    "esplora risorse": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "telegram": ["Telegram.exe"],
    "spotify": ["Spotify.exe"],
    "unreal": ["UnrealEditor.exe"],
    "blender": ["blender.exe"],
    "bambu": ["bambu-studio.exe"]
}

def kill_app(process_name_or_pid: Any) -> Dict[str, Any]:
    """
    Termina un'applicazione o processo tramite nome, alias o PID.
    """
    t0 = time.perf_counter()
    raw = str(process_name_or_pid).lower().strip()
    
    candidates = []
    if raw.isdigit():
        candidates = [raw]
    elif raw in KILL_ALIASES:
        candidates = KILL_ALIASES[raw]
    else:
        candidates = [raw if raw.endswith(".exe") else f"{raw}.exe"]
        
    outputs = []
    success = False
    last_target = candidates[0]
    
    for target in candidates:
        last_target = target
        try:
            if target.isdigit():
                res = subprocess.run(["taskkill", "/PID", target, "/F"], capture_output=True, text=True)
            else:
                res = subprocess.run(["taskkill", "/IM", target, "/F"], capture_output=True, text=True)
            if res.returncode == 0:
                success = True
                outputs.append(res.stdout.strip())
                break
            else:
                outputs.append(res.stderr.strip() or res.stdout.strip())
        except Exception as e:
            outputs.append(str(e))
            
    lat = (time.perf_counter() - t0) * 1000.0
    return {
        "status": "success" if success else "failed",
        "action": "kill_app",
        "target": last_target,
        "output": "; ".join(filter(None, outputs)),
        "latency_ms": round(lat, 2)
    }

# ══════════════════════════════════════════════════════════════════════════════
# 2. RICERCA & VISUALIZZAZIONE FOTO / SCREENSHOT
# ══════════════════════════════════════════════════════════════════════════════

def find_recent_photos(limit: int = 15) -> List[Dict[str, Any]]:
    """
    Scansiona le cartelle multimediali del sistema (Immagini, Desktop, Downloads, Screenshots)
    e restituisce le foto più recenti ordinate per data.
    """
    search_dirs = [
        str(SCREENSHOTS_DIR),
        str(ROOT_DIR / "public" / "registration_proofs"),
        str(ROOT_DIR / "public" / "marketplace_runs"),
        os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Pictures"),
        os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Desktop"),
        os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Admin"), "Downloads"),
    ]
    
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")
    all_files = []
    
    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        for ext in extensions:
            for p in glob.glob(os.path.join(sdir, ext)):
                try:
                    st = os.stat(p)
                    all_files.append({
                        "path": p,
                        "filename": os.path.basename(p),
                        "size_kb": round(st.st_size / 1024, 1),
                        "mtime": st.st_mtime,
                        "date_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
                    })
                except Exception:
                    pass

    # Ordina dal più recente al più vecchio
    all_files.sort(key=lambda x: x["mtime"], reverse=True)
    return all_files[:limit]

def show_photo(query_or_path: Optional[str] = None, open_native: bool = True) -> Dict[str, Any]:
    """
    Trova una foto (o l'ultima scattata/salvata) e la apre su schermo con il visualizzatore nativo
    di Windows, restituendo anche l'anteprima base64 per la dashboard web.
    """
    t0 = time.perf_counter()
    target_path = None
    
    if query_or_path and os.path.exists(query_or_path):
        target_path = query_or_path
    else:
        # Cerca la foto più recente o che contiene la parola chiave
        recent = find_recent_photos(limit=30)
        if query_or_path:
            q_low = query_or_path.lower()
            for r in recent:
                if q_low in r["filename"].lower() or q_low in r["path"].lower():
                    target_path = r["path"]
                    break
        if not target_path and recent:
            target_path = recent[0]["path"] # Prendi l'ultima disponibile

    if not target_path or not os.path.exists(target_path):
        return {
            "status": "not_found",
            "message": "Nessuna foto trovata nei percorsi di sistema."
        }

    # 1. Apri con il visualizzatore foto nativo di Windows
    if open_native:
        try:
            os.startfile(target_path)
        except Exception as e:
            # Fallback con explorer
            subprocess.Popen(["explorer.exe", target_path])

    # 2. Genera miniatura base64 per il visualizzatore web della dashboard
    b64_thumb = None
    try:
        with open(target_path, "rb") as f:
            raw_bytes = f.read()
            # Se è < 10MB genera preview
            if len(raw_bytes) < 10 * 1024 * 1024:
                b64_thumb = base64.b64encode(raw_bytes).decode("ascii")
    except Exception:
        pass

    lat = (time.perf_counter() - t0) * 1000.0
    return {
        "status": "success",
        "action": "show_photo",
        "path": target_path,
        "filename": os.path.basename(target_path),
        "size_kb": round(os.path.getsize(target_path) / 1024, 1),
        "has_base64_preview": bool(b64_thumb),
        "base64_preview": b64_thumb,
        "latency_ms": round(lat, 2),
        "message": f"Foto '{os.path.basename(target_path)}' aperta su schermo."
    }

def take_system_screenshot() -> Dict[str, Any]:
    """
    Scatta uno screenshot a tutto schermo della sessione Windows reale,
    lo salva in alta definizione e lo restituisce per la visione.
    """
    t0 = time.perf_counter()
    fn = f"screenshot_{int(time.time())}.png"
    out_path = str(SCREENSHOTS_DIR / fn)
    
    # Tentativo rapido con Pillow ImageGrab
    try:
        from PIL import ImageGrab
        im = ImageGrab.grab(all_screens=True)
        im.save(out_path, "PNG")
    except Exception:
        # Fallback PowerShell .NET Graphics
        ps_cmd = f"""
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
        $bitmap.Save('{out_path}')
        $graphics.Dispose()
        $bitmap.Dispose()
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)

    if os.path.exists(out_path):
        lat = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "success",
            "action": "take_screenshot",
            "path": out_path,
            "filename": fn,
            "latency_ms": round(lat, 2),
            "message": "Screenshot catturato e salvato con successo."
        }
    return {"status": "error", "message": "Impossibile catturare lo screenshot."}

# ══════════════════════════════════════════════════════════════════════════════
# 3. INVIO EMAIL UNIVERSALE (Gmail SMTP + Allegati + Note Vocali)
# ══════════════════════════════════════════════════════════════════════════════

def send_universal_email(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    voice_note_text: Optional[str] = None,
    brand: str = "EBJ"
) -> Dict[str, Any]:
    """
    Invia un'email a qualsiasi destinatario tramite il server SMTP sicuro di Google.
    Supporta allegati multipli e generazione vocale neurale MP3 incorporata.
    """
    t0 = time.perf_counter()
    recipient = to.strip()
    if recipient.lower() in ["me", "me stesso", "badr", "admin"]:
        recipient = GMAIL_USER

    msg = MIMEMultipart()
    sender_name = "EBJ Supreme AI · Workstation" if brand == "EBJ" else "SELEZIONE Detergenza Professionale"
    msg["From"] = f"{sender_name} <{GMAIL_USER}>"
    msg["To"] = recipient
    msg["Subject"] = subject

    # Se c'è una nota vocale da sintetizzare
    audio_path = None
    if voice_note_text:
        try:
            import edge_tts
            audio_fn = f"vdispatch_{int(time.time())}.mp3"
            audio_path = str(VOICE_DIR / audio_fn)
            async def _synth():
                comm = edge_tts.Communicate(voice_note_text, "it-IT-DiegoNeural", rate="+12%")
                await comm.save(audio_path)
            asyncio.run(_synth())
        except Exception as e:
            print("[JEV Executor] Errore sintesi vocale email:", e)

    # HTML elegante
    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #020813; color: #e2e8f0; padding: 24px; }}
.card {{ background: #071226; border: 1.5px solid #00f0ff; border-radius: 14px; padding: 26px; max-width: 600px; margin: 0 auto; box-shadow: 0 10px 30px rgba(0,240,255,0.2); }}
.header {{ font-size: 11px; font-weight: 800; color: #00f0ff; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 12px; }}
.content {{ font-size: 14px; line-height: 1.6; color: #f1f5f9; white-space: pre-wrap; }}
.footer {{ font-size: 11px; color: #64748b; margin-top: 24px; border-top: 1px solid #1e293b; padding-top: 14px; text-align: center; }}
</style>
</head>
<body>
<div class="card">
    <div class="header">⚡ EBJ SUPREME SYSTEM DISPATCH · BADREXPRESS</div>
    <div class="content">{body}</div>
    {f'<div style="background:rgba(0,240,255,0.08); border-left:3px solid #00f0ff; padding:10px 14px; margin-top:16px; border-radius:4px; font-size:12px; color:#38bdf8;">🎙️ <b>Nota Vocale Neurale Inclusa:</b> "{voice_note_text}"</div>' if voice_note_text else ''}
    <div class="footer">
        <b>Badr El Ouariti · EBJ AI Ecosystem</b><br>
        BadrExpress.com & PietroTraslochi.com · Workstation DESKTOP-SJR1JS8
    </div>
</div>
</body>
</html>"""

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Allegato Audio Vocale se presente
    if audio_path and os.path.exists(audio_path):
        try:
            with open(audio_path, "rb") as f:
                part = MIMEBase("audio", "mpeg")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(audio_path)}")
            msg.attach(part)
        except Exception as e:
            print("[JEV Executor] Errore allegato audio:", e)

    # Allegati file generici
    if attachments:
        for att_path in attachments:
            if os.path.exists(att_path):
                try:
                    with open(att_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(att_path)}")
                    msg.attach(part)
                except Exception as e:
                    print(f"[JEV Executor] Errore allegato {att_path}:", e)

    # Invio SMTP SSL
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=12) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
            
        lat = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "success",
            "action": "send_email",
            "recipient": recipient,
            "subject": subject,
            "has_voice_note": bool(audio_path),
            "attachments_count": len(attachments) if attachments else 0,
            "latency_ms": round(lat, 2),
            "message": f"Email inviata con successo a {recipient}!"
        }
    except Exception as e:
        lat = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "error",
            "action": "send_email",
            "recipient": recipient,
            "error": str(e),
            "latency_ms": round(lat, 2)
        }

# ══════════════════════════════════════════════════════════════════════════════
# 4. APPUNTI (CLIPBOARD) & HARDWARE
# ══════════════════════════════════════════════════════════════════════════════

def get_clipboard_text() -> str:
    """Legge il testo dagli appunti di Windows."""
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True, timeout=3)
        return res.stdout.strip()
    except Exception:
        return ""

def set_clipboard_text(text: str) -> bool:
    """Scrive un testo negli appunti di Windows."""
    try:
        p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=text)
        return p.returncode == 0
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST NATIVO AUTONOMO
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== TEST JEV SYSTEM OPS EXECUTOR ===")
    photos = find_recent_photos(limit=3)
    print(f"Foto recenti trovate: {len(photos)}")
    for p in photos:
        print(f" - {p['filename']} ({p['size_kb']} KB) in {p['path']}")
        
    running = list_running_apps()
    print(f"\nApp con finestra aperte: {len(running)}")
    for r in running[:5]:
        print(f" - [{r['pid']}] {r['process_name']}: '{r['title']}' ({r['memory_mb']} MB)")
