"""
Bambu 3D Engine - Bambu Studio 1-Click Launcher
Author: E.B.J. AI Supreme for Ing. Badr
Opens native Bambu Studio (X1C / P1S / A1) with the 3MF project ready on the virtual print bed.
"""

import os
import sys
import subprocess

BAMBU_STUDIO_PATH = r"C:\Program Files\Bambu Studio\bambu-studio.exe"
DEFAULT_MODEL_3MF = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\public\3d_models\HTVW_281_BambuLab.3mf"

def launch_bambu_studio(file_path=None):
    target = file_path or DEFAULT_MODEL_3MF
    if not os.path.exists(BAMBU_STUDIO_PATH):
        return {"success": False, "error": f"Bambu Studio non trovato in {BAMBU_STUDIO_PATH}"}
    if not os.path.exists(target):
        return {"success": False, "error": f"File modello non trovato in {target}"}
        
    try:
        proc = subprocess.Popen([BAMBU_STUDIO_PATH, target], shell=False)
        print(f"[+] Bambu Studio avviato con successo! PID={proc.pid} | File={target}")
        return {
            "success": True,
            "pid": proc.pid,
            "file": target,
            "message": "Bambu Studio avviato con il modello caricato sul piatto virtuale."
        }
    except Exception as e:
        print(f"[!] Errore avvio Bambu Studio: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    launch_bambu_studio()
