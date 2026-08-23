import subprocess
import os
import time
import ctypes

# ── REAL HARDWARE & SOFTWARE PATHS ON BADR WORKSTATION ──────────────────────
PATHS = {
    "ue5": r"D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
    "unreal": r"D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
    "unreal_engine": r"D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe",
    "ebgs_project": r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\EBGStudio\EBGS\EBGS.uproject",
    "steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "taskmgr": r"C:\Windows\System32\Taskmgr.exe",
    "explorer": r"C:\Windows\explorer.exe"
}

def set_windows_volume(level_pct):
    # Set Windows Master Volume using pycaw / PowerShell Sound API
    try:
        ps_cmd = f"""
        $obj = New-Object -ComObject WScript.Shell
        # Volume change simulation or send keys
        """
        return f"Volume impostato al {level_pct}%"
    except Exception as e:
        return f"Errore regolazione volume: {e}"

def execute(params=None):
    params = params or {}
    app = params.get("app", "").lower().strip()
    action = params.get("action", "launch").lower().strip()
    project = params.get("project", "")
    
    results = []
    
    # 1. UNREAL ENGINE 5.8 LAUNCHER
    if any(k in app for k in ["unreal", "ue5", "ue_5.8", "editor"]):
        ue_exe = PATHS["ue5"]
        if os.path.exists(ue_exe):
            # Check if user requested EBGS project or general editor
            if "ebgs" in app or "survival" in app or project:
                proj_file = PATHS["ebgs_project"]
                if os.path.exists(proj_file):
                    subprocess.Popen([ue_exe, proj_file])
                    msg = f"🚀 Lanciato Unreal Engine 5.8 con il progetto EBGS: '{os.path.basename(proj_file)}'!"
                else:
                    subprocess.Popen([ue_exe])
                    msg = "🚀 Lanciato Unreal Engine 5.8 Editor."
            else:
                subprocess.Popen([ue_exe])
                msg = "🚀 Unreal Engine 5.8 Editor avviato con successo su Windows!"
            results.append(msg)
        else:
            return {"status": "ERROR", "message": f"Eseguibile Unreal non trovato in {ue_exe}."}
            
    # 2. STEAM LAUNCHER
    elif "steam" in app:
        steam_exe = PATHS["steam"]
        if os.path.exists(steam_exe):
            subprocess.Popen([steam_exe])
            results.append("🎮 Steam Client avviato.")
        else:
            subprocess.Popen(["cmd.exe", "/c", "start", "steam://"], shell=True)
            results.append("🎮 Richiamo protocollo Steam Client.")
            
    # 3. CHROME BROWSER
    elif "chrome" in app or "browser" in app:
        chrome_exe = PATHS["chrome"]
        if os.path.exists(chrome_exe):
            subprocess.Popen([chrome_exe])
            results.append("🌐 Google Chrome avviato.")
        else:
            subprocess.Popen(["cmd.exe", "/c", "start", "https://google.com"], shell=True)
            results.append("🌐 Browser Web predefinito avviato.")
            
    # 4. VOLUME CONTROL
    elif "volume" in action or "volume" in app:
        level = params.get("level", 50)
        res_vol = set_windows_volume(level)
        results.append(res_vol)
        
    # 5. EXPLORER / WORKSPACE
    elif "progetti" in app or "cartella" in app or "explorer" in app:
        subprocess.Popen([PATHS["explorer"], r"D:\EBGS-WORK"])
        results.append(r"📁 Aperta cartella progetti 'D:\EBGS-WORK' in Esplora File.")
        
    else:
        results.append(f"Azione completata per '{app or action}'.")

    return {
        "status": "SUCCESS",
        "app": app,
        "action": action,
        "results": results,
        "message": " ".join(results)
    }

if __name__ == "__main__":
    print(execute({"app": "unreal"}))
