#!/usr/bin/env python3
# ==============================================================================
#  E.B.J. NATIVE OS & COMPUTER CONTROLLER (INSPIRED BY MARK-LV ARCHITECTURE)
# ==============================================================================
#  Controlla applicazioni, volume, media e desktop a zero latenza su Windows/Linux.
# ==============================================================================

import os
import sys
import platform
import subprocess
import time
from typing import Dict, Any, Optional

_SYSTEM = platform.system()

# Mappatura alias applicazioni comuni
_APP_MAP = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "brave": "brave",
    "vscode": "code",
    "visual studio code": "code",
    "code": "code",
    "telegram": "telegram",
    "whatsapp": "whatsapp",
    "discord": "discord",
    "spotify": "spotify",
    "terminale": "wt",
    "terminal": "wt",
    "powershell": "powershell",
    "cmd": "cmd",
    "blocco note": "notepad",
    "notepad": "notepad",
    "calcolatrice": "calc",
    "esplora risorse": "explorer",
    "explorer": "explorer",
    "paint": "mspaint"
}

APP_TARGETS = _APP_MAP

def launch_application(app_name: str) -> Dict[str, Any]:
    """Avvia un'applicazione su Windows/Linux."""
    clean_name = app_name.lower().strip()
    target_bin = _APP_MAP.get(clean_name, clean_name)

    try:
        if _SYSTEM == "Windows":
            # Usa os.startfile o shell execute
            if target_bin in ["wt", "cmd", "powershell", "calc", "notepad", "mspaint", "explorer"]:
                subprocess.Popen(target_bin, shell=True)
            else:
                try:
                    os.startfile(target_bin)
                except Exception:
                    subprocess.Popen(f"start {target_bin}", shell=True)
        elif _SYSTEM == "Linux":
            subprocess.Popen([target_bin])
        else:
            subprocess.Popen(["open", "-a", target_bin])

        return {
            "status": "SUCCESS",
            "app": clean_name,
            "target": target_bin,
            "message": f"Applicazione '{clean_name}' avviata con successo."
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "app": clean_name,
            "error": str(e)
        }

def control_system_audio(action: str) -> Dict[str, Any]:
    """Regola volume di sistema (up, down, mute)."""
    act = action.lower().strip()
    try:
        try:
            import pyautogui
            if "up" in act or "alza" in act or "piu" in act:
                for _ in range(5):
                    pyautogui.press("volumeup")
                msg = "Volume alzato."
            elif "down" in act or "abbassa" in act or "meno" in act:
                for _ in range(5):
                    pyautogui.press("volumedown")
                msg = "Volume abbassato."
            elif "mute" in act or "muto" in act or "silenzia" in act:
                pyautogui.press("volumemute")
                msg = "Audio silenziato o ripristinato."
            else:
                msg = "Azione volume non riconosciuta."
            return {"status": "SUCCESS", "action": act, "message": msg}
        except ImportError:
            # Fallback PowerShell su Windows se pyautogui non c'è
            if _SYSTEM == "Windows":
                if "up" in act:
                    subprocess.run(["powershell", "-c", "$w = New-Object -ComObject WScript.Shell; 1..5 | % { $w.SendKeys([char]175) }"], timeout=2)
                elif "down" in act:
                    subprocess.run(["powershell", "-c", "$w = New-Object -ComObject WScript.Shell; 1..5 | % { $w.SendKeys([char]174) }"], timeout=2)
                elif "mute" in act:
                    subprocess.run(["powershell", "-c", "$w = New-Object -ComObject WScript.Shell; $w.SendKeys([char]173)"], timeout=2)
                return {"status": "SUCCESS", "action": act, "message": "Volume modificato via PowerShell."}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

def take_desktop_screenshot() -> Dict[str, Any]:
    """Cattura screenshot del desktop e salva in Desktop/ebj_screenshot.png."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "ebj_screenshot.png")
    try:
        try:
            import pyautogui
            pyautogui.screenshot(desktop_path)
            return {"status": "SUCCESS", "path": desktop_path}
        except ImportError:
            # Fallback Windows PowerShell
            ps_cmd = f"Add-Type -AssemblyName System.Windows.Forms,System.Drawing; $b = New-Object Drawing.Bitmap ([Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $g = [Drawing.Graphics]::FromImage($b); $g.CopyFromScreen(0,0,0,0,$b.Size); $b.Save('{desktop_path}');"
            subprocess.run(["powershell", "-Command", ps_cmd], timeout=4)
            return {"status": "SUCCESS", "path": desktop_path}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

if __name__ == "__main__":
    print("Testing ebj_os_controller...")
    print(control_system_audio("mute"))
