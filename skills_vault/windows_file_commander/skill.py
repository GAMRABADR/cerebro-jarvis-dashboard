import os
import shutil
import glob
import time
import datetime
import subprocess
import json
import re

def get_system_time_info():
    now = datetime.datetime.now()
    return {
        "status": "SUCCESS",
        "current_time": now.strftime("%H:%M:%S"),
        "current_date": now.strftime("%A %d %B %Y"),
        "timestamp_iso": now.isoformat(),
        "timezone": "Europe/Rome (Imola, IT)",
        "human_readable": f"Signore, sono esattamente le {now.strftime('%H:%M')} di {now.strftime('%A %d %B %Y')}."
    }

def explore_directory(target_path=None, max_items=40):
    if not target_path or target_path == "workspace":
        target_path = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio"
    elif target_path.lower() in ["desktop", "scrivania"]:
        target_path = os.path.join(os.path.expanduser("~"), "Desktop")
    elif target_path.lower() in ["downloads", "download"]:
        target_path = os.path.join(os.path.expanduser("~"), "Downloads")
    elif target_path.lower() in ["documents", "documenti"]:
        target_path = os.path.join(os.path.expanduser("~"), "Documents")
    elif target_path.lower() in ["c:", "c:\\", "disco c"]:
        target_path = r"C:\\"
    elif target_path.lower() in ["d:", "d:\\", "disco d"]:
        target_path = r"D:\\"
    elif target_path.lower() in ["e:", "e:\\", "disco e", "usb"]:
        target_path = r"E:\\"
        
    if not os.path.exists(target_path):
        return {"status": "ERROR", "message": f"Percorso '{target_path}' non trovato o unità non accessibile."}
        
    entries = []
    try:
        with os.scandir(target_path) as it:
            for entry in it:
                try:
                    is_dir = entry.is_dir()
                    size_bytes = 0 if is_dir else entry.stat().st_size
                    size_str = "<DIR>" if is_dir else f"{size_bytes / (1024*1024):.2f} MB" if size_bytes > 1024*1024 else f"{size_bytes / 1024:.1f} KB"
                    mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
                    entries.append({
                        "name": entry.name,
                        "is_directory": is_dir,
                        "size": size_str,
                        "modified": mtime,
                        "path": entry.path
                    })
                except Exception:
                    pass
        entries.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
        return {
            "status": "SUCCESS",
            "directory": target_path,
            "total_items": len(entries),
            "items": entries[:max_items],
            "message": f"Esplorazione di '{target_path}' completata: {len(entries)} elementi trovati."
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def search_files_on_disk(pattern, root_dir=None, max_results=30):
    if not root_dir:
        root_dir = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio"
    elif root_dir.lower() in ["c:", "c:\\"]:
        root_dir = r"C:\\"
    elif root_dir.lower() in ["e:", "e:\\"]:
        root_dir = r"E:\\"
        
    results = []
    p_lower = pattern.lower()
    try:
        for root, dirs, files in os.walk(root_dir):
            if any(ign in root for ign in [".git", "node_modules", "Intermediate", "Binaries", "DerivedDataCache", "Saved", "$RECYCLE.BIN"]):
                continue
            for f in files:
                if p_lower in f.lower():
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        sz_str = f"{sz/(1024*1024):.2f} MB" if sz > 1024*1024 else f"{sz/1024:.1f} KB"
                        results.append({"name": f, "path": fp, "size": sz_str})
                    except Exception:
                        results.append({"name": f, "path": fp, "size": "N/A"})
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break
        return {"status": "SUCCESS", "query": pattern, "count": len(results), "results": results}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def organize_cluttered_folder(folder_path):
    if folder_path.lower() in ["downloads", "download"]:
        folder_path = os.path.join(os.path.expanduser("~"), "Downloads")
    elif folder_path.lower() in ["desktop", "scrivania"]:
        folder_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
    if not os.path.exists(folder_path):
        return {"status": "ERROR", "message": f"Cartella '{folder_path}' inesistente."}
        
    categories = {
        "01_Immagini": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico", ".psd"],
        "02_Documenti_PDF": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".txt", ".csv", ".rtf"],
        "03_Video": [".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv"],
        "04_Audio": [".mp3", ".wav", ".ogg", ".flac", ".m4a"],
        "05_Archivi_ZIP": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "06_Installer_Setup": [".exe", ".msi", ".iso", ".bat", ".cmd", ".ps1"],
        "07_Codice_Sviluppo": [".py", ".rs", ".cpp", ".h", ".json", ".js", ".html", ".css", ".uproject", ".uasset"]
    }
    
    moved_count = 0
    moved_log = []
    
    for f in os.listdir(folder_path):
        src_file = os.path.join(folder_path, f)
        if os.path.isfile(src_file):
            ext = os.path.splitext(f)[1].lower()
            dest_cat = "99_Altri_File"
            for cat_name, ext_list in categories.items():
                if ext in ext_list:
                    dest_cat = cat_name
                    break
                    
            target_dir = os.path.join(folder_path, dest_cat)
            os.makedirs(target_dir, exist_ok=True)
            dst_file = os.path.join(target_dir, f)
            try:
                if not os.path.exists(dst_file):
                    shutil.move(src_file, dst_file)
                    moved_count += 1
                    moved_log.append(f"{f} ➔ {dest_cat}/")
            except Exception as e:
                pass
                
    return {
        "status": "SUCCESS",
        "folder": folder_path,
        "files_organized": moved_count,
        "log": moved_log[:20],
        "message": f"Organizzazione completata: {moved_count} file ordinati in cartelle tematiche."
    }

def file_operations(action, src, dst=None):
    try:
        if action == "copy":
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            return {"status": "SUCCESS", "message": f"Copiato '{src}' in '{dst}' con successo."}
        elif action in ["move", "rename"]:
            shutil.move(src, dst)
            return {"status": "SUCCESS", "message": f"Spostato/Rinominato '{src}' in '{dst}' con successo."}
        elif action == "delete":
            if os.path.isdir(src):
                shutil.rmtree(src)
            else:
                os.remove(src)
            return {"status": "SUCCESS", "message": f"Eliminato '{src}' con successo."}
        elif action == "mkdir":
            os.makedirs(src, exist_ok=True)
            return {"status": "SUCCESS", "message": f"Cartella '{src}' creata con successo."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def execute(params=None):
    params = params or {}
    action = params.get("action", "explore").lower()
    
    if action in ["time", "ora", "clock"]:
        return get_system_time_info()
    elif action in ["explore", "list", "ls", "dir", "esplora"]:
        return explore_directory(params.get("path"))
    elif action in ["search", "find", "cerca"]:
        return search_files_on_disk(params.get("query", ""), params.get("path"))
    elif action in ["organize", "riordina", "pulisci"]:
        return organize_cluttered_folder(params.get("path", "downloads"))
    elif action in ["copy", "move", "rename", "delete", "mkdir"]:
        return file_operations(action, params.get("src", ""), params.get("dst"))
    else:
        return explore_directory(params.get("path"))
