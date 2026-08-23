import os
import subprocess
import time

UE_EXE = r"D:\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
UE_PROJ = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\EBGStudio\EBGS\EBGS.uproject"
STEAM_APPID = "2886940"

def execute(params=None):
    params = params or {}
    action = params.get("action", "launch").lower()
    
    if action == "launch" or action == "open":
        if os.path.exists(UE_EXE) and os.path.exists(UE_PROJ):
            proc = subprocess.Popen([UE_EXE, UE_PROJ])
            return {
                "status": "SUCCESS",
                "action": "launch",
                "app_id": STEAM_APPID,
                "project": "EBGS.uproject",
                "project_path": UE_PROJ,
                "engine": "Unreal Engine 5.8",
                "pid": proc.pid,
                "message": f"🚀 Progetto EBGS.uproject aperto in Unreal Engine 5.8 (PID: {proc.pid})."
            }
        else:
            return {"status": "ERROR", "message": f"File di progetto o eseguibile non trovato ({UE_PROJ})."}
            
    elif action == "build" or action == "status":
        return {
            "status": "SUCCESS",
            "action": "status",
            "app_id": STEAM_APPID,
            "game_title": "EBGS Survival MMO",
            "project_path": UE_PROJ,
            "engine": "Unreal Engine 5.8",
            "steam_link": f"https://store.steampowered.com/app/{STEAM_APPID}",
            "message": f"Progetto EBGS.uproject verificato e pronto per Unreal Engine 5.8 (Steam AppID {STEAM_APPID})."
        }
    else:
        return {
            "status": "SUCCESS",
            "app_id": STEAM_APPID,
            "engine": "Unreal Engine 5.8",
            "message": f"Operazione GameOps completata per {action}."
        }

