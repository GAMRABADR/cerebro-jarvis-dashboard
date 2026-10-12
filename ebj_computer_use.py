"""
==============================================================================
⚡ EBJ SUPREME — NATIVE WORKSTATION COMPUTER USE & OS CONTROLLER
==============================================================================
Consente ad EBJ di entrare nel PC di Badr (Windows 11 DESKTOP-SJR1JS8),
visualizzare lo schermo in tempo reale, controllare mouse e tastiera con
latenza sub-millisecondo via Win32 ctypes, gestire finestre ed eseguire comandi.
==============================================================================
"""

from __future__ import annotations
import os
import sys
import time
import json
import base64
import ctypes
import subprocess
from io import BytesIO
from ctypes import windll, byref, c_int, c_long, Structure, sizeof, POINTER, c_short
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

# ── STRUTTURE WIN32 ──────────────────────────────────────────────────────────

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class RECT(Structure):
    _fields_ = [("left", c_long), ("top", c_long), ("right", c_long), ("bottom", c_long)]

# Costanti mouse Win32
MOUSEEVENTF_MOVE        = 0x0001
MOUSEEVENTF_LEFTDOWN    = 0x0002
MOUSEEVENTF_LEFTUP      = 0x0004
MOUSEEVENTF_RIGHTDOWN   = 0x0008
MOUSEEVENTF_RIGHTUP     = 0x0010
MOUSEEVENTF_MIDDLEDOWN  = 0x0020
MOUSEEVENTF_MIDDLEUP    = 0x0040
MOUSEEVENTF_WHEEL       = 0x0800
MOUSEEVENTF_ABSOLUTE    = 0x8000

# Costanti tastiera Win32
KEYEVENTF_EXTENDEDKEY   = 0x0001
KEYEVENTF_KEYUP         = 0x0002
KEYEVENTF_UNICODE       = 0x0004
KEYEVENTF_SCANCODE      = 0x0008

# Mappa Virtual Key (VK)
VK_MAP = {
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "space": 0x20,
    "backspace": 0x08,
    "delete": 0x2E,
    "del": 0x2E,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "win": 0x5B,
    "windows": 0x5B,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B
}

user32 = windll.user32
gdi32 = windll.gdi32

# ── 1. CATTURA SCHERMO ULTRA-VELOCE (GDI RAM BUFFER) ─────────────────────────

def capture_screen_pil() -> Image.Image:
    """Cattura lo schermo intero in RAM tramite GDI BitBlt nativo (< 10ms)."""
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    
    # Copia bit dello schermo nel DC in memoria
    gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, 0x00CC0020) # SRCCOPY
    
    # Estrazione pixel bitmap
    class BITMAPINFOHEADER(Structure):
        _fields_ = [
            ("biSize", c_int), ("biWidth", c_int), ("biHeight", c_int),
            ("biPlanes", c_short), ("biBitCount", c_short),
            ("biCompression", c_int), ("biSizeImage", c_int),
            ("biXPelsPerMeter", c_int), ("biYPelsPerMeter", c_int),
            ("biClrUsed", c_int), ("biClrImportant", c_int)
        ]
        
    bmi = BITMAPINFOHEADER()
    bmi.biSize = sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # Top-down bitmap
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    
    buf_size = w * h * 4
    buf = ctypes.create_string_buffer(buf_size)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, byref(bmi), 0)
    
    # Rilascio risorse GDI
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    gdi32.DeleteObject(hbmp)
    
    # Converti raw BGRA in Pillow Image
    im = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1)
    return im.convert("RGB")

def get_screen_snapshot(max_width: int = 1280, quality: int = 75) -> Dict[str, Any]:
    """
    Restituisce snapshot compresso in Base64 JPEG con metadati di risoluzione
    per la trasmissione immediata al web cockpit o vision LLM.
    """
    t0 = time.perf_counter()
    im = capture_screen_pil()
    orig_w, orig_h = im.size
    
    if orig_w > max_width:
        ratio = max_width / float(orig_w)
        new_h = int(orig_h * ratio)
        im_scaled = im.resize((max_width, new_h), Image.Resampling.BILINEAR)
    else:
        im_scaled = im
        
    bio = BytesIO()
    im_scaled.save(bio, format="JPEG", quality=quality)
    b64 = base64.b64encode(bio.getvalue()).decode("ascii")
    
    lat = (time.perf_counter() - t0) * 1000.0
    return {
        "status": "success",
        "width": orig_w,
        "height": orig_h,
        "scaled_width": im_scaled.width,
        "scaled_height": im_scaled.height,
        "jpeg_base64": b64,
        "latency_ms": round(lat, 2)
    }

# ── 2. CONTROLLO MOUSE WIN32 NATIVO ──────────────────────────────────────────

def get_mouse_position() -> Tuple[int, int]:
    """Restituisce le coordinate attuali del mouse (x, y)."""
    pt = POINT()
    user32.GetCursorPos(byref(pt))
    return int(pt.x), int(pt.y)

def mouse_move(x: int, y: int) -> Dict[str, Any]:
    """Sposta il cursore del mouse su (x, y) all'istante."""
    user32.SetCursorPos(int(x), int(y))
    return {"status": "success", "action": "mouse_move", "x": x, "y": y}

def mouse_click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", double: bool = False) -> Dict[str, Any]:
    """Esegue un click singolo o doppio con il tasto specificato."""
    if x is not None and y is not None:
        mouse_move(x, y)
        time.sleep(0.015)
    
    btn = button.lower().strip()
    if btn == "right":
        down_flag, up_flag = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    elif btn == "middle":
        down_flag, up_flag = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
    else:
        down_flag, up_flag = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
        
    user32.mouse_event(down_flag, 0, 0, 0, 0)
    time.sleep(0.02)
    user32.mouse_event(up_flag, 0, 0, 0, 0)
    
    if double:
        time.sleep(0.06)
        user32.mouse_event(down_flag, 0, 0, 0, 0)
        time.sleep(0.02)
        user32.mouse_event(up_flag, 0, 0, 0, 0)
        
    curr_x, curr_y = get_mouse_position()
    return {"status": "success", "action": "mouse_click", "button": btn, "double": double, "x": curr_x, "y": curr_y}

def mouse_drag(x1: int, y1: int, x2: int, y2: int) -> Dict[str, Any]:
    """Trascina da (x1, y1) a (x2, y2)."""
    mouse_move(x1, y1)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    
    # Movimento a passi per simulare drag naturale
    steps = 10
    for i in range(1, steps + 1):
        cx = int(x1 + (x2 - x1) * (i / steps))
        cy = int(y1 + (y2 - y1) * (i / steps))
        mouse_move(cx, cy)
        time.sleep(0.01)
        
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    return {"status": "success", "action": "mouse_drag", "from": [x1, y1], "to": [x2, y2]}

def mouse_scroll(clicks: int = 3, direction: str = "down") -> Dict[str, Any]:
    """Fa scorrere la rotella del mouse verso l'alto o verso il basso."""
    amount = -120 * abs(clicks) if direction.lower() == "down" else 120 * abs(clicks)
    user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, amount, 0)
    return {"status": "success", "action": "mouse_scroll", "clicks": clicks, "direction": direction}

# ── 3. CONTROLLO TASTIERA & DIGITAZIONE UNICODE ───────────────────────────────

def keyboard_type(text: str, interval: float = 0.01) -> Dict[str, Any]:
    """
    Digita testo arbitrario inclusi caratteri speciali e accentati via SendInput Unicode.
    """
    class KEYBDINPUT(Structure):
        _fields_ = [
            ("wVk", c_short), ("wScan", c_short),
            ("dwFlags", c_int), ("time", c_int),
            ("dwExtraInfo", ctypes.c_void_p)
        ]
        
    class INPUT(Structure):
        class _INPUT_UNION(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _anonymous_ = ("u",)
        _fields_ = [("type", c_int), ("u", _INPUT_UNION)]

    INPUT_KEYBOARD = 1
    
    for ch in text:
        code = ord(ch)
        # Tasto premuto
        inp_down = INPUT(type=INPUT_KEYBOARD)
        inp_down.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=None)
        
        # Tasto rilasciato
        inp_up = INPUT(type=INPUT_KEYBOARD)
        inp_up.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)
        
        user32.SendInput(1, byref(inp_down), sizeof(INPUT))
        time.sleep(0.005)
        user32.SendInput(1, byref(inp_up), sizeof(INPUT))
        if interval > 0:
            time.sleep(interval)
            
    return {"status": "success", "action": "keyboard_type", "length": len(text)}

def keyboard_hotkey(*keys) -> Dict[str, Any]:
    """
    Esegue scorciatoie da tastiera (es: 'win', 'd' per mostrare il desktop, 'ctrl', 'c', 'alt', 'tab').
    """
    vk_codes = []
    for k in keys:
        kl = str(k).lower().strip()
        if kl in VK_MAP:
            vk_codes.append(VK_MAP[kl])
        elif len(kl) == 1:
            # Carattere singolo: ottieni virtual key
            vk = user32.VkKeyScanW(ord(kl)) & 0xFF
            vk_codes.append(vk)
            
    # Premi tutti i tasti in sequenza
    for vk in vk_codes:
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.01)
        
    time.sleep(0.04)
    # Rilascia tutti i tasti in ordine inverso
    for vk in reversed(vk_codes):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.01)
        
    return {"status": "success", "action": "keyboard_hotkey", "keys": list(keys)}

# ── 4. GESTIONE FINESTRE & STATO WORKSTATION ─────────────────────────────────

def show_desktop() -> Dict[str, Any]:
    """Minimizza tutto e mostra il desktop (Win+D)."""
    return keyboard_hotkey("win", "d")

def get_active_window() -> Dict[str, Any]:
    """Restituisce il titolo e le coordinate della finestra attualmente attiva."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return {"title": "Nessuna", "hwnd": 0}
        
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    
    rect = RECT()
    user32.GetWindowRect(hwnd, byref(rect))
    
    pid = c_long()
    user32.GetWindowThreadProcessId(hwnd, byref(pid))
    
    return {
        "hwnd": hwnd,
        "title": buff.value.strip(),
        "pid": pid.value,
        "rect": {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}
    }

def focus_window_by_title(partial_title: str) -> Dict[str, Any]:
    """Porta in primo piano una finestra cercandone il titolo parziale."""
    target_hwnd = None
    target_title = None
    q = partial_title.lower()
    
    def enum_proc(hwnd, lparam):
        nonlocal target_hwnd, target_title
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                if q in title.lower():
                    target_hwnd = hwnd
                    target_title = title
                    return False
        return True
        
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
    
    if target_hwnd:
        # Ripristina se minimizzata (SW_RESTORE = 9) e imposta foreground
        user32.ShowWindow(target_hwnd, 9)
        user32.SetForegroundWindow(target_hwnd)
        return {"status": "success", "action": "focus_window", "title": target_title, "hwnd": target_hwnd}
    return {"status": "not_found", "action": "focus_window", "query": partial_title}

def get_workstation_status() -> Dict[str, Any]:
    """Restituisce lo stato globale di controllo della Workstation."""
    import psutil
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    mx, my = get_mouse_position()
    active_win = get_active_window()
    
    # Info risorse
    cpu_percent = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    
    return {
        "status": "connected",
        "computer_name": os.environ.get("COMPUTERNAME", "DESKTOP-SJR1JS8"),
        "user_name": os.environ.get("USERNAME", "Admin"),
        "resolution": f"{w}x{h}",
        "width": w,
        "height": h,
        "mouse": {"x": mx, "y": my},
        "active_window": active_win,
        "cpu_percent": cpu_percent,
        "ram_used_gb": round((ram.total - ram.available) / (1024**3), 2),
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "ram_percent": ram.percent,
        "control_ready": True
    }

# ── 5. RUNTIME DI CONTROLLO UNIFICATO & DISPATCHER AZIONI ────────────────────

def execute_computer_use(action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Dispatcher principale per qualsiasi azione del Computer Use di EBJ.
    """
    params = params or {}
    act = action.lower().strip()
    
    if act in ("status", "connect", "get_status"):
        res = get_workstation_status()
        res["spoken_response"] = f"Workstation {res['computer_name']} agganciata, Badr. Schermo {res['resolution']}, CPU al {res['cpu_percent']}% e controllo input pronto."
        return res
        
    elif act in ("snapshot", "screenshot", "screen"):
        max_w = params.get("max_width", 1280)
        quality = params.get("quality", 75)
        return get_screen_snapshot(max_width=max_w, quality=quality)
        
    elif act == "move":
        return mouse_move(params.get("x", 0), params.get("y", 0))
        
    elif act in ("click", "mouse_click"):
        x = params.get("x")
        y = params.get("y")
        btn = params.get("button", "left")
        dbl = params.get("double", False)
        return mouse_click(x=x, y=y, button=btn, double=dbl)
        
    elif act == "drag":
        return mouse_drag(params.get("x1", 0), params.get("y1", 0), params.get("x2", 0), params.get("y2", 0))
        
    elif act == "scroll":
        return mouse_scroll(clicks=params.get("clicks", 3), direction=params.get("direction", "down"))
        
    elif act in ("type", "write"):
        return keyboard_type(params.get("text", ""))
        
    elif act == "hotkey":
        keys = params.get("keys", ["win", "d"])
        return keyboard_hotkey(*keys)
        
    elif act in ("show_desktop", "desktop"):
        res = show_desktop()
        res["spoken_response"] = "Mostro subito il Desktop della workstation, Badr."
        return res
        
    elif act == "focus":
        return focus_window_by_title(params.get("title", ""))
        
    elif act == "open_app":
        from ebj_system_ops_executor import launch_app
        return launch_app(params.get("app", ""), args=params.get("args"))
        
    elif act in ("shell", "terminal", "command"):
        cmd = params.get("command", "dir")
        try:
            p = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=12)
            return {
                "status": "success",
                "action": "shell",
                "command": cmd,
                "stdout": p.stdout[-2000:] if p.stdout else "",
                "stderr": p.stderr[-500:] if p.stderr else ""
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
            
    else:
        return {"status": "unknown_action", "action": act}

if __name__ == "__main__":
    print("=== TEST EBJ COMPUTER USE ENGINE ===")
    status = get_workstation_status()
    print("Status:", json.dumps(status, indent=2))
    snap = get_screen_snapshot(max_width=640)
    print(f"Snapshot JPEG base64 len: {len(snap['jpeg_base64'])} (Latency: {snap['latency_ms']} ms)")
